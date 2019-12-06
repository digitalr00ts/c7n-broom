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
            name, configs=(policy_name,), regions=regions, metrics_enabled=False,
        ),
        policies,
    )


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

    if not skip_auth_check and accounts:
        authed_profiles = boto_remora.aws.helper.get_authed_profiles(accounts.keys())
        unauthed_profiles = set(accounts).difference(authed_profiles)
        msg = f"Not all accounts can access the AWS API {unauthed_profiles}."
        if skip_unauthed:
            if unauthed_profiles:
                _LOGGER.info(msg)
            accounts = dict(
                filter(lambda account_: account_ in authed_profiles, accounts.keys())
            )
        elif unauthed_profiles:
            raise RuntimeError(msg)

    if not accounts:
        _LOGGER.critical("No accounts to create c7n configs.")

    return itertools.chain.from_iterable(
        map(
            lambda kv_: account_c7nconfigs(
                kv_[0], kv_[1], global_settings, skip_regions=skip_auth_check,
            ),
            accounts.items(),
        )
    )
