""" Main module for c7n_broom """
import logging
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from functools import partial
from itertools import chain
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Sequence, Union

from vyper import Vyper

import c7n_broom
from c7n_broom import C7nCfg
from c7n_broom.actions.report import get_data_map
from c7n_broom.data import count


_LOGGER = logging.getLogger(__name__)


@dataclass()
class Sweeper:
    """ Lets sweep up the cloud """

    settings: Optional[Union[Vyper, Dict[str, Any]]] = None
    config_file: Union[PathLike, str] = field(default="config", repr=False)
    data_dir: PathLike = Path("data").joinpath("query")
    report_dir: PathLike = Path("data").joinpath("reports")
    skip_unauthed: bool = False
    auth_check: bool = True
    jobs: Sequence[C7nCfg] = field(init=False, repr=False)

    def __post_init__(self):
        if not self.settings:
            self.settings = c7n_broom.config.get_config(filename=str(self.config_file))
        broom_settings = self.settings.get("broom") if self.settings.get("broom") else dict()
        for attrib in ("data_dir", "report_dir", "auth_check", "skip_unauthed"):
            if broom_settings.get(attrib):
                setattr(self, attrib, broom_settings.get(attrib))
        self.jobs = tuple(
            c7n_broom.config.create.c7nconfigs(
                self.settings,
                skip_unauthed=self.skip_unauthed,
                skip_auth_check=not self.auth_check,
            )
        )

    def _filter_by_attrib(self, attribute: str, attribute_val: str):
        return filter(lambda job_: getattr(job_, attribute, False) == attribute_val, self.jobs)

    def _asdict_by_attrib(self, attribute: str):
        rtn = defaultdict(deque)
        for job_ in self.jobs:
            rtn[str(getattr(job_, attribute))].append(job_)
        return rtn

    @property
    def jobs_by_profile(self) -> Dict[str, Sequence[C7nCfg]]:
        """ Return a dict of jobs by profile name """
        return self._asdict_by_attrib("profile")

    @property
    def jobs_by_policies(self) -> Dict[str, Sequence[C7nCfg]]:
        """ Return a dict of jobs by policy name """
        return self._asdict_by_attrib("configs")

    def get_account_jobs(self, account: str, use_profile: bool = True) -> Iterator[C7nCfg]:
        """ Get an iterator of only jobs for an account """
        attrib = "profile" if use_profile else "account_id"
        return self._filter_by_attrib(attribute=attrib, attribute_val=account)

    def _exec(self, action, jobs, batch=None):
        if batch:
            jobsby = getattr(self, "jobs_by_" + batch)
            filelist = map(lambda jobs_: self._exec(action, jobs_[1], batch=None), jobsby.items())
            return chain.from_iterable(filelist)

        _LOGGER.debug("Processing %s %s jobs.", len(jobs), action)
        with ProcessPoolExecutor() as executor:
            future_data = executor.map(action, jobs)
        # _LOGGER.debug("%s data files written.", len(future_data))
        return future_data

    def query(self, telemetry=False, batch=None):
        """ Run without actions. Dryrun true. """
        action = partial(
            c7n_broom.actions.query, data_dir=self.data_dir, telemetry_disabled=not telemetry,
        )
        return deque(self._exec(action, self.jobs, batch))

    def execute(self, telemetry=False, batch=None):
        """ Run actions. Dryrun false. """
        action = partial(
            c7n_broom.actions.execute, data_dir=self.data_dir, telemetry_disabled=not telemetry,
        )
        return deque(self._exec(action, self.jobs, batch))

    def gen_reports(self, fmt="md", report_dir=None):
        """ Generate reports. Markdown by default. """
        if not report_dir:
            report_dir = self.report_dir
        writer = partial(
            c7n_broom.actions.write_report,
            fmt=fmt,
            data_path=self.data_dir,
            output_path=report_dir,
        )
        filelist = deque(map(str, filter(None, map(writer, self.jobs))))
        _LOGGER.info("%s report file written", len(filelist))
        return filelist

    def gen_html(self, html_dir: PathLike = "public"):
        """ Generate HTML report """
        return self.gen_reports("html", report_dir=html_dir)

    def counts(self, grouped=False):
        """ Return count of resources from all jobs """
        func = count if grouped else len
        data = map(
            lambda job_: (job_.get_str, func(get_data_map(job_, data_path=self.data_dir))),
            self.jobs,
        )
        return dict(data)
