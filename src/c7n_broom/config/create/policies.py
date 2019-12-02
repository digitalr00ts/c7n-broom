""" Policy package for c7n_broom.config """
import logging
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Set, Union

from c7n_broom.util import ExtendedEnum
from vyper import Vyper


_LOGGER = logging.getLogger(__name__)


class PolicyKeys(ExtendedEnum):
    """ Types of policies """

    INCLUDE = "include"
    EXCLUDE = "exclude"


def _create_dictset(data: Dict[str, Iterable[str]], keys: Iterable[str]) -> Dict[str, Set[str]]:
    """ Returns dict of sets for keys in data """
    return {key: set(data.get(key) if (data and data.get(key)) else set()) for key in keys}


def filter_policies(
    account_policies, default_policies, keys=frozenset(PolicyKeys.values())
) -> Iterator[str]:
    """ Combine account and default included and excluded policies. """
    account_policies_ = _create_dictset(account_policies, keys)
    default_policies_ = _create_dictset(default_policies, keys)

    policies_sets = {
        policy_key: account_policies_[policy_key].union(default_policies_[policy_key])
        for policy_key in keys
    }

    return filter(
        lambda policy: policy
        not in policies_sets[PolicyKeys.EXCLUDE.value],  # pylint: disable=no-member
        policies_sets[PolicyKeys.INCLUDE.value],  # pylint: disable=no-member
    )


def get_policy_files(
    account_settings: Union[Vyper, Dict[str, Any]],
    global_settings: Optional[Union[Vyper, Dict[str, Any]]] = None,
    path: Optional[Union[PathLike, str]] = None,
    file_suffix="yml",
) -> Iterator[PathLike]:
    """ Returns an iterator of paths to policy files. """
    policy_names = filter_policies(account_settings, global_settings)
    path = Path(
        path if path else global_settings.get("path") if global_settings.get("path") else ""
    )
    _LOGGER.debug('Looking for policies in "%s".', path)

    return map(
        lambda policy: policy.with_suffix(f".{file_suffix}"), map(path.joinpath, policy_names),
    )
