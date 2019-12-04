""" Main of c7n_broom.config.main """
import itertools
import logging
from typing import Any, Dict, Optional, Union

import boto_remora.aws
from vyper import Vyper

from c7n_broom.config.create.policies import get_policy_files
from c7n_broom.config.main import C7nConfig

_LOGGER = logging.getLogger(__name__)


def account_c7nconfigs(
    name: str,
    account_settings: Union[Vyper, Dict[str, Any]],
    global_settings: Optional[Union[Vyper, Dict[str, Any]]] = None,
    skip_regions: bool = False,
):
    """ Create c7n config per policy for account. """
    _LOGGER.info("Creating c7n configs for %s", name)
    policies = get_policy_files(
        account_settings.get("policies") if account_settings else dict(),
        global_settings.get("policies") if global_settings else dict(),
    )
    # TODO: remove skip regions in favor of setting regions in broom config
    regions = boto_remora.aws.Ec2(name).available_regions if not skip_regions else list()
    _LOGGER.debug("Creating policies: %s %s", name, policies)
    # TODO: remove hardcoded disabling metrics and move to broom config
    return map(
        lambda policy_name: C7nConfig(
            name,
            configs=(policy_name,),
            regions=regions,
            # resource_type=_get_policy_resource(policy_name),
            metrics_enabled=False,
        ),
        policies,
    )


def _authed_accounts_data(accounts, skip_unauthed: bool):
    def is_authed(profile, region="us-east-1") -> bool:
        return (
            boto_remora.aws.Sts(profile, region_name=region).is_session_region_accessible
            if boto_remora.aws.AwsBase().is_profile_available(profile)
            else False
        )

    accounts_authed_data = dict(filter(lambda account: is_authed(account[0]), accounts.items()))
    accounts_not_authed = set(accounts.keys()).difference(accounts_authed_data.keys())
    if accounts_not_authed:
        msg = f"Not all accounts can access the AWS API {accounts_not_authed}."
        if skip_unauthed:
            _LOGGER.warning(msg)
        else:
            raise RuntimeError(msg)
    return accounts_authed_data


def c7nconfigs(
    config: Union[Vyper, Dict[str, Any]],
    skip_unauthed: bool = False,
    skip_auth_check: bool = False,
):
    """ Create c7n configs for every policy and account """
    global_settings = config.get("global")
    accounts = config.get("accounts")
    if (
        accounts is not None
        and len(accounts) == 1
        and isinstance(accounts.get("ALL"), bool)
        and accounts.get("ALL") is True
    ):
        import botocore  # pylint: disable=import-outside-toplevel

        accounts = {profile: None for profile in botocore.session.Session().available_profiles}
    if not skip_auth_check:
        accounts = _authed_accounts_data(accounts, skip_unauthed)

    if not accounts:
        _LOGGER.critical("No accounts in config.")
    return itertools.chain.from_iterable(
        map(
            lambda account_name: account_c7nconfigs(
                account_name,
                accounts.get(account_name),
                global_settings,
                skip_regions=skip_auth_check,
            ),
            accounts.keys(),
        )
    )
