""" Main module for c7n_broom """
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import partial
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, Optional, Sequence, Union

from vyper import Vyper

import c7n_broom
from c7n_broom import C7nConfig


_LOGGER = logging.getLogger(__name__)


@dataclass()
class Sweeper:
    """ Lets sweep up the cloud """

    settings: Optional[Union[Vyper, Dict[str, Any]]] = None
    config_file: Union[PathLike, str] = field(default="config", repr=False)
    data_dir: PathLike = Path("data").joinpath("query")
    report_dir: PathLike = Path("data").joinpath("report")
    jobs: Union[Sequence[C7nConfig], Generator[C7nConfig]] = field(init=False, repr=False)

    def __post_init__(self):
        if not self.settings:
            self.settings = c7n_broom.config.get_config(filename=str(self.config_file))
        broom_settings = self.settings.get("broom") if self.settings.get("broom") else dict()
        for attrib in ("data_dir", "report_dir"):
            if broom_settings.get(attrib):
                setattr(self, attrib, broom_settings.get(attrib))
        self.jobs = tuple(c7n_broom.config.create.c7nconfigs(self.settings))

    def _get_by_attrib(self, attribute: str, attribute_val: str):
        return filter(lambda job_: getattr(job_, attribute, False) == attribute_val, self.jobs)

    def _asdict_by_attrib(self, attribute: str):
        rtn_jobs = defaultdict(list)
        for job_ in self.jobs:
            rtn_jobs[str(getattr(job_, attribute))].append(job_)
        return rtn_jobs

    @property
    def jobs_by_profile(self) -> Dict[str, Sequence[C7nConfig]]:
        """ Return a dict of jobs by profile name """
        return self._asdict_by_attrib("profile")

    @property
    def jobs_by_policies(self) -> Dict[str, Sequence[C7nConfig]]:
        """ Return a dict of jobs by policy name """
        return self._asdict_by_attrib("configs")

    def get_account_jobs(self, account: str, use_profile: bool = True) -> Iterator[C7nConfig]:
        """ Get an iterator of only jobs for an account """
        attrib = "profile" if use_profile else "account_id"
        return self._get_by_attrib(attribute=attrib, attribute_val=account)

    @staticmethod
    def _exec(action, jobs):
        filelist = list()
        for profile_, jobs_ in jobs.items():
            _LOGGER.info("Executing for %s", profile_)
            with ThreadPoolExecutor() as executor:
                future_data = tuple(executor.map(action, jobs_))
            _LOGGER.debug("%s data files written.", len(future_data))
            filelist.extend(future_data)
        return filelist

    def query(self, telemetry=False, batch="profile"):
        """ Run without actions. Dryrun true. """
        jobs = getattr(self, "jobs_by_".join(batch))
        action = partial(
            c7n_broom.actions.query, data_dir=self.data_dir, telemetry_disabled=not telemetry,
        )
        return self._exec(action, jobs)

    def clean(self, telemetry=False, batch="profile"):
        """ Run actions. Dryrun false. """
        jobs = getattr(self, "jobs_by_".join(batch))
        action = partial(
            c7n_broom.actions.clean, data_dir=self.data_dir, telemetry_disabled=not telemetry,
        )
        return self._exec(action, jobs)

    def gen_reports(self, fmt="md"):
        """ Generate reports. Markdown by default. """
        writer = partial(
            c7n_broom.actions.write_report,
            fmt=fmt,
            data_path=self.data_dir,
            output_path=self.report_dir,
        )
        filelist = tuple(map(str, filter(None, map(writer, self.jobs))))
        _LOGGER.debug("%s report file written", len(filelist))
        return filelist

    def gen_html(self, html_dir: PathLike = "public"):
        """ Generate HTML report """
        report_dir_tmp = self.report_dir
        self.report_dir = html_dir
        filelist = self.gen_reports("html")
        self.report_dir = report_dir_tmp
        return filelist
