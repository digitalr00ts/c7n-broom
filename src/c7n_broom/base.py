"""
Base module
"""

import dataclasses
import logging
import os
import pathlib

from typing import Iterable, List, Optional, Set, Tuple, Union

# import boto3
import c7n.commands
import c7n.config


import c7n_broom.util


_LOGGER = logging.getLogger(__name__)
REGION_MAP = c7n_broom.util.get_region_names()


@dataclasses.dataclass(eq=False)
class C7nConfig(dict):
    """Configuration for c7n."""

    profile: str = os.environ.get("AWS_PROFILE", "")
    configs: List[str] = dataclasses.field(default_factory=list)
    dryrun: bool = True

    output_dir: str = ""
    regions: Iterable[Union[List[str], Set[str], Tuple[str, ...]]] = dataclasses.field(
        default_factory=set, compare=False
    )
    metrics: Optional[str] = "aws://master?region=us-east-1"
    policy_filter: Optional[str] = None
    resource_type: Optional[str] = None

    cache_period: int = 15
    cache: Optional[str] = None

    # Report
    format: str = "simple"
    days: float = 1
    no_default_fields: bool = False
    field: List[str] = dataclasses.field(default_factory=list)
    raw: Optional[pathlib.Path] = None

    region: str = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    metrics_enabled: bool = True
    debug: bool = False
    # verbose: bool = True

    # IDK, but c7n will throw errors w/o it.
    vars: Optional[List] = None

    # account_id: Optional[str] = field(default=None)
    # assume_role: Optional[str] = field(default=None)
    # external_id: Optional[str] = field(default=None)
    # log_group: Optional[str] = field(default=None)
    # authorization_file: Optional[str] = field(default=None)
    # tracer: str = field(default="default")

    # data: Dict[str, Any] = dataclasses.field(default_factory=dict, init=False)

    def __post_init__(self):
        if not self.profile:
            raise TypeError("Profile must be set.")

        for k, v in c7n.config.Config.empty().items():
            if k not in dataclasses.asdict(self).keys():
                _LOGGER.debug("Adding missing attribute {}:{}.", k, v)
                setattr(self, k, v)

        c7n_home = pathlib.Path.home().joinpath(".cache/c7n").joinpath(self.profile)
        self.regions = set(self.regions)

        if not self.cache:
            self.cache = str(c7n_home.joinpath("cloud-custodian.cache"))

        if not self.output_dir:
            self.output_dir = str(c7n_home.joinpath("output"))
            # self.output_dir = str(f"s3://c7n-{self.profile}/jupyter")

        if not self.configs:
            _LOGGER.warning("No configuration files set.")


# @dataclasses.dataclass(eq=False)
# class Settings:
#     """ c7n Broom Settings"""

#     config: C7nConfig

#     session: boto3.Session = dataclasses.field(init=False)

#     def __post_init__(self):

#         self.session = boto3.Session(
#             region_name=self.config.region, profile_name=self.config.profile
#         )

#         if bool(not self.config.regions):
#             self.config.regions = util.regions_accessible(session=self.session)
