""" Main of c7n_broom.config.main """
import itertools
import logging

from typing import Any, Dict, Iterable, Optional, Set, Union

import boto_remora.aws

from vyper import Vyper

from c7n_broom.config.main import C7nConfig
from c7n_broom.util import ExtendedEnum


_LOGGER = logging.getLogger(__name__)


class PolicyKeys(ExtendedEnum):
    """ Types of policies """

    INCLUDE = "include"
    EXCLUDE = "exclude"


def _create_dictset(
    data: Dict[str, Iterable[str]], keys: Iterable[str]
) -> Dict[str, Set[str]]:
    """ Returns dict of sets for keys in data """
    return {
        key: set(data.get(key) if (data and data.get(key)) else set()) for key in keys
    }


def _merge_policies(
    account_policies, default_policies, keys=frozenset(PolicyKeys.values())
) -> Set[str]:
    """ Combine account and default included and excluded policies. """
    account_policies_ = _create_dictset(account_policies, keys)
    default_policies_ = _create_dictset(default_policies, keys)

    policies_sets = {
        policy_key: account_policies_[policy_key].union(default_policies_[policy_key])
        for policy_key in keys
    }

    return policies_sets[
        PolicyKeys.INCLUDE.value  # pylint: disable=no-member
    ].difference(
        policies_sets[PolicyKeys.EXCLUDE.value]  # pylint: disable=no-member
    )


def account_c7nconfigs(
    name: str,
    account_settings: Union[Vyper, Dict[str, Any]],
    global_settings: Optional[Union[Vyper, Dict[str, Any]]] = None,
):
    """ Create c7n config per policy for account. """
    policies = _merge_policies(
        account_settings.get("policies") if account_settings else dict(),
        global_settings.get("policies") if global_settings else dict(),
    )
    regions = boto_remora.aws.Ec2(name).available_regions
    _LOGGER.debug("Creating policies: %s %s", name, policies)
    return map(
        lambda policy: C7nConfig(name, configs=[policy], regions=regions), policies
    )


def _authed_accounts_data(config, skip_unauthed: bool):
    def is_authed(profile, region="us-east-1") -> bool:
        return (
            boto_remora.aws.Sts(
                profile, region_name=region
            ).is_default_region_accessible()
            if boto_remora.aws.AwsBase().is_profile_available(profile)
            else False
        )

    accounts_authed_data = dict(
        filter(lambda account: is_authed(account[0]), config.get("accounts").items())
    )
    accounts_not_authed = set(config.get("accounts").keys()).difference(
        accounts_authed_data.keys()
    )
    if accounts_not_authed:
        msg = f"Not all accounts can access the AWS API {accounts_not_authed}."
        if skip_unauthed:
            logging.warning(msg)
        else:
            raise RuntimeError(msg)
    return accounts_authed_data


def c7nconfigs(config, skip_unauthed: bool = False, skip_auth_check: bool = False):
    """ Create c7n configs for every policy and account """

    accounts = (
        _authed_accounts_data(config, skip_unauthed)
        if not skip_auth_check
        else config.get("accounts")
    )
    global_settings = config.get("global")

    if not accounts:
        _LOGGER.critical("No accounts in config.")
    return itertools.chain.from_iterable(
        map(
            lambda account_name: account_c7nconfigs(
                account_name, accounts.get(account_name), global_settings
            ),
            accounts.keys(),
        )
    )
