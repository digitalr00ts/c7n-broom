""" Helper functions for c7n_broom.actions """
from pathlib import Path


def account_profile_policy_str(c7n_config):
    """
    Returns a string for the c7n_config.
    Used for creating files names.
    """
    profile_policies_str = " - ".join(
        [
            c7n_config.profile,
            ", ".join(map(lambda policy: Path(policy).stem, c7n_config.configs)),
        ]
    )
    return profile_policies_str
