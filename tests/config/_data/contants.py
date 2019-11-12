from c7n_broom.config import PolicyKeys


EXPECTED_POLICIES_DATA = [
    ("account_included", {"account_included_policy", "default_included_policy"}),
    ("default_exclude", {"account_included_policy", "default_included_policy"}),
    ("exclude_all", set()),
    (
        "account_included_none_exclude",
        {"account_included_policy", "default_included_policy"},
    ),
    ("account_none_exclude_default", set()),
    ("none", {"default_included_policy"}),
    ("none_policies", {"default_included_policy"}),
    ("empty_policies", {"default_included_policy"}),
]
EXPECTED_POLICIES_DATA = {
    "account_included": {"account_included_policy", "default_included_policy"},
    "default_exclude": {"account_included_policy", "default_included_policy"},
    "exclude_all": set(),
    "account_included_none_exclude": {
        "account_included_policy",
        "default_included_policy",
    },
    "account_none_exclude_default": set(),
    "none": {"default_included_policy"},
    "none_policies": {"default_included_policy"},
    "empty_policies": {"default_included_policy"},
}
DICT_OF_KEYS_DATA = {
    "Good Data": {"Key1": ["Value1A", "Value1B"], "Key2": ["Value2A"],},
    "Key with Empty List": {"Key1": [], "Key2": ["Value2A"],},
    "Key Value None": {"Key1": ["Value1A", "Value1B"], "Key2": None,},
    "Extra Key": {
        "Key1": ["Value1A", "Value1B"],
        "Key2": ["Value2A"],
        "ExtraKey": ["ExtraValueA"],
    },
    "Missing Key": {"Key2": ["Value2A"],},
    "No Expected Keys": {"ExtraKey": ["Value2A"],},
    "Empty Dict": {},
    "None": None,
}
POLICY_KEYS = (
    PolicyKeys.INCLUDE.value,
    PolicyKeys.EXCLUDE.value,
)
MERGE_POLICY_DATA = {
    "Defaults Only": {
        "defaults": {
            POLICY_KEYS[0]: ["default-included-policy"],
            POLICY_KEYS[1]: ["default-excluded-policy"],
        },
        "EXPECTED": {"default-included-policy"},
    },
    "Account Only": {
        "account": {
            POLICY_KEYS[0]: ["account-included-policy"],
            POLICY_KEYS[1]: ["account-excluded-policy"],
        },
        "EXPECTED": {"account-included-policy"},
    },
    "Account + Defaults w/ no Overlap": {
        "account": {
            POLICY_KEYS[0]: ["account-included-policy"],
            POLICY_KEYS[1]: ["account-excluded-policy"],
        },
        "defaults": {
            POLICY_KEYS[0]: ["default-included-policy"],
            POLICY_KEYS[1]: ["default-excluded-policy"],
        },
        "EXPECTED": {"account-included-policy", "default-included-policy"},
    },
    "Exclude Account": {
        "account": {POLICY_KEYS[0]: ["account-included-policy"],},
        "defaults": {
            POLICY_KEYS[0]: ["default-included-policy"],
            POLICY_KEYS[1]: ["account-included-policy"],
        },
        "EXPECTED": {"default-included-policy"},
    },
    "Exclude Defaults": {
        "account": {
            POLICY_KEYS[0]: ["account-included-policy"],
            POLICY_KEYS[1]: ["default-included-policy"],
        },
        "defaults": {
            POLICY_KEYS[0]: ["default-included-policy"],
            POLICY_KEYS[1]: ["default-excluded-policy"],
        },
        "EXPECTED": {"account-included-policy"},
    },
}
