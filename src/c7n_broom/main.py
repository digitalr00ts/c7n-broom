""" Main module for c7n_broom """
import logging
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import partial
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, Set, Union

from vyper import Vyper

import c7n_broom
from c7n_broom import C7nCfg
from c7n_broom.actions.report import get_data_map
from c7n_broom.data import count


_LOGGER = logging.getLogger(__name__)


def _trun(action: c7n_broom.actions, jobs: Sequence[C7nCfg]):
    """ Multi-threaded actions """
    _LOGGER.debug("Processing %s %s jobs.", len(jobs), action.__class__.__name__)
    with ThreadPoolExecutor() as executor:
        executor.map(action, jobs)


def _account_batch_run(action: c7n_broom.actions, jobs: Mapping[str, C7nCfg]):
    """
    Multiprocess actions batched by account
    to get around caching sessions issue
    """
    _LOGGER.debug("Processing %s jobs for %s.", action.__class__.__name__, jobs.keys())
    exec_ = partial(_trun, action)
    with ProcessPoolExecutor() as executor:
        executor.map(exec_, jobs.values())


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
        self.jobs = deque(
            c7n_broom.config.create.c7nconfigs(
                self.settings,
                skip_unauthed=self.skip_unauthed,
                skip_auth_check=not self.auth_check,
            )
        )

    def _get_job_settings(self, attrib, jobs=None) -> Set[Any]:
        if jobs is None:
            jobs = self.jobs
        return {getattr(cfg_, attrib) for cfg_ in jobs}

    def _filter_by_attrib(self, attribute: str, attribute_val: str):
        return filter(lambda job_: getattr(job_, attribute, False) == attribute_val, self.jobs)

    def _asdict_by_attrib(self, attribute: str):
        rtn = defaultdict(deque)
        _ = [rtn[str(getattr(job_, attribute))].append(job_) for job_ in self.jobs]
        return rtn

    def _run(self, action):
        jobmap = self._asdict_by_attrib("account_id")
        return _account_batch_run(action, jobmap) if len(jobmap) > 1 else _trun(action, self.jobs)

    def get_account_jobs(self, account: str, use_profile: bool = True) -> Iterator[C7nCfg]:
        """ Get an iterator of only jobs for an account """
        attrib = "profile" if use_profile else "account_id"
        return self._filter_by_attrib(attribute=attrib, attribute_val=account)

    def query(self, telemetry=False):
        """ Run without actions. Dryrun true. """
        action = partial(
            c7n_broom.actions.query, data_dir=self.data_dir, telemetry_disabled=not telemetry,
        )
        return self._run(action)

    def execute(self, telemetry=False):
        """ Run actions. Dryrun false. """
        action = partial(
            c7n_broom.actions.execute, data_dir=self.data_dir, telemetry_disabled=not telemetry,
        )
        return self._run(action)

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
            lambda job_: (job_.get_str, func(get_data_map(job_, data_path=self.data_dir)),),
            self.jobs,
        )
        return dict(data)
