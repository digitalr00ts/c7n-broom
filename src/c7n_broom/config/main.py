""" Main of c7n_broom.config """
import dataclasses
import itertools
import logging
import os
import pathlib
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import c7n.config
import yaml
from vyper import Vyper


_LOGGER = logging.getLogger(__name__)


def get_config(filename: str = "config", path: PathLike = Path(".")):
    """ Read in config file """
    config = Vyper(filename)
    config.set_default("defaults", dict())
    config.add_config_path(Path(path))
    config.read_in_config()
    return config


# def create_c7nconfigs_old(accounts):
#     """ Create c7n config objects per account per policy """
#
#     class PolicyKeys(ExtendedEnum):
#         INCLUDE = "include"
#         EXCLUDE = "exclude"
#
#     def create_policy_dict(data) -> Dict[str, Set[str]]:
#         """ Creates a dict of policies of POLICY_KEYS """
#         # Ensures that policies returns as set even when None
#         rtn_policy_list_as_set = (
#             lambda data, key: set(data.get(key)) if (data and data.get(key)) else set()
#         )
#         return {key: rtn_policy_list_as_set(data, key) for key in PolicyKeys.values()}
#
#     def create_config_per_policy(account):
#         _LOGGER.debug("Creating c7n config objects for account [%s]", account["name"])
#
#         def policies() -> Set[str]:
#             """ Combine the includes and excludes policies from defaults and the account """
#             account_policies = create_policy_dict(account.get("policies"))
#             policies_sets = {
#                 policy_key: account_policies[policy_key].union(
#                     default_policies[policy_key]
#                 )
#                 for policy_key in PolicyKeys.values()
#             }
#
#             return policies_sets[PolicyKeys.INCLUDE.value].difference(
#                 policies_sets[PolicyKeys.EXCLUDE.value]
#             )
#
#         return map(
#             lambda policy: C7nConfig(account["name"], configs=[policy]), policies()
#         )
#
#     default_policies = create_policy_dict(config.get("defaults.policies"))
#
#     return itertools.chain.from_iterable(
#         map(lambda account: create_config_per_policy(account), accounts)
#     )
@dataclasses.dataclass()
class C7nConfig(c7n.config.Config):  # pylint: disable=too-many-instance-attributes
    """Configuration for c7n."""

    profile: str = os.environ.get("AWS_PROFILE", "")
    configs: Iterable[str] = dataclasses.field(default_factory=list)
    dryrun: bool = True

    output_dir: str = ""
    regions: Iterable[str] = dataclasses.field(default_factory=set, compare=False)
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

    account_id: Optional[str] = dataclasses.field(default=None)
    assume_role: Optional[str] = dataclasses.field(default=None)
    external_id: Optional[str] = dataclasses.field(default=None)
    log_group: Optional[str] = dataclasses.field(default=None)
    authorization_file: Optional[str] = dataclasses.field(default=None)
    tracer: str = dataclasses.field(default="default")

    # IDK, but c7n will throw errors w/o it.
    vars: Optional[List] = None

    def __post_init__(self):
        if not self.profile:
            raise TypeError("Profile must be set.")

        for k, v in c7n.config.Config.empty().items():
            if k not in dataclasses.asdict(self).keys():
                _LOGGER.debug("Adding missing attribute %s:%s.", k, v)
                setattr(self, k, v)

        c7n_home = pathlib.Path.home().joinpath(".cache/c7n").joinpath(self.profile)
        self.regions = set(self.regions)

        if not self.cache:
            self.cache = str(c7n_home.joinpath("cloud-custodian.cache"))

        if not self.output_dir:
            self.output_dir = str(c7n_home.joinpath("output"))

        if not self.configs:
            _LOGGER.warning("No configuration files set.")
        else:
            if not self.resource_type:
                self.resource_type = self.get_policy_resource()

    def get_config_data(self) -> Iterable[Dict[str, Any]]:
        """ Returns iterable of dict for all files in self.config """

        def get_policy_data(policy_file) -> Dict[str, Any]:
            policy_file = Path(policy_file)
            return yaml.safe_load(policy_file.read_bytes()) if policy_file.is_file() else dict()

        return map(get_policy_data, self.configs)

    def get_policy_data(self) -> Iterable[Dict[str, Any]]:
        """ Returns iterable of policies across all policies in configs """

        def policy_data(data_):
            return data_.get("policies")

        return itertools.chain.from_iterable(
            map(policy_data, filter(policy_data, self.get_config_data()))
        )

    def get_policy_resource(self) -> Optional[str]:
        """
        Returns resource type if the resources are the same across the policies in the policy file.
        Otherwise returns None
        """

        policy_resources = set(
            map(lambda policy_item: policy_item.get("resource"), self.get_policy_data())
        )
        rtn = policy_resources.pop() if len(policy_resources) == 1 else None
        if not rtn:
            _LOGGER.warning("%s resource types found.", len(policy_resources))
        return rtn
