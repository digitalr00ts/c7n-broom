""" main package for c7n_broom.actions """
import json
import logging
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import c7n.commands

from c7n_broom.actions.helper import account_profile_policy_str
from c7n_broom.config import C7nCfg


_LOGGING = logging.getLogger(__name__)


def run(
    c7n_config: C7nCfg,
    data_dir: PathLike = "data",
    dryrun: bool = True,
    telemetry_disabled: bool = True,
    report_minutes=5,
    regions_override: Optional[Iterator] = None,
):  # pylint: disable = too-many-arguments
    """

    c7n_config:
    telemetry_disabled Sometimes we just want to query w/ sending data
    report_minutes:
    regions_override: For debugging

    """
    MINUTES_IN_DAY = 1440  # pylint: disable=invalid-name
    profile_policies_str = account_profile_policy_str(c7n_config)

    Path(data_dir).mkdir(parents=True, exist_ok=True)

    _LOGGING.info("STARTING %s", profile_policies_str)
    print(f"STARTING: {profile_policies_str}")

    c7n_config.dryrun = dryrun
    c7n_config.no_default_fields = True
    if regions_override:
        c7n_config.regions = regions_override
    if telemetry_disabled:
        c7n_config.metrics = None
        c7n_config.metrics_enabled = False

    c7n.commands.run(c7n_config.c7n)  # pylint: disable=no-value-for-parameter

    report_settings = c7n_config.c7n
    report_settings.days = report_minutes / MINUTES_IN_DAY
    datafile = Path(data_dir).joinpath(profile_policies_str).with_suffix(".json")
    with datafile.open(mode="wt") as data_fd:
        report_settings.raw = data_fd
        c7n.commands.report(report_settings)  # pylint: disable=no-value-for-parameter

    print(f"COMPLETED: {profile_policies_str}")
    logging.info("COMPLETED %s", profile_policies_str)
    logging.debug("Data file writen %s", datafile)
    return datafile


def query(
    c7n_config: C7nCfg,
    data_dir: PathLike = Path("data").joinpath("query"),
    telemetry_disabled: bool = True,
):
    """ Run without actions. Dryrun true. """
    run(
        c7n_config, data_dir=data_dir, telemetry_disabled=telemetry_disabled, dryrun=True,
    )


def execute(
    c7n_config: C7nCfg,
    data_dir: PathLike = Path("data").joinpath("query"),
    telemetry_disabled: bool = True,
):
    """ Run actions. Dryrun false. """
    run(
        c7n_config, data_dir=data_dir, telemetry_disabled=telemetry_disabled, dryrun=False,
    )


def read_data(
    c7n_config: C7nCfg, data_dir: PathLike = Path("data").joinpath("query"),
) -> Optional[Dict[str, Any]]:
    """
        Return data from query data.
        Return None if data dne
        """
    datafile = Path(data_dir).joinpath(c7n_config.get_str).with_suffix(".json")
    return json.loads(datafile.read_bytes())
