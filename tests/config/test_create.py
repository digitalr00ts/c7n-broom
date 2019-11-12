""" Testing c7n_broom.config.create """
# pylint: disable=protected-access,missing-function-docstring
from pathlib import Path

import pytest

from tests.config._data.contants import (
    DICT_OF_KEYS_DATA,
    EXPECTED_POLICIES_DATA,
    MERGE_POLICY_DATA,
)

import c7n_broom


@pytest.fixture(scope="module")
def configs(request):
    vconfig = request.config.cache.get("vconfig", None)
    c7nconfigs = request.config.cache.get("c7nconfigs", None)
    if not vconfig:
        data_path = Path(__file__).parent.joinpath("_data")
        vconfig = c7n_broom.config.get_config("config", path=data_path)
        c7nconfigs = list(c7n_broom.config.create.c7nconfigs(vconfig))
    return vconfig, c7nconfigs


@pytest.mark.parametrize(
    "data", [pytest.param(value, id=id_) for id_, value in DICT_OF_KEYS_DATA.items()]
)
def test_010_create_dictset(data):
    keys = ["Key1", "Key2"]
    rtn = c7n_broom.config.create.main._create_dictset(data, keys)
    assert sorted(list(rtn.keys())) == sorted(keys)


@pytest.mark.parametrize(
    "data", [pytest.param(value, id=id_) for id_, value in MERGE_POLICY_DATA.items()]
)
def test_020_merge_policies(data):
    policies = c7n_broom.config.create.main._merge_policies(
        data.get("account"), data.get("defaults")
    )
    assert policies == data["EXPECTED"]


@pytest.mark.parametrize(
    "name,policies",
    [
        pytest.param(name, policies, id=name)
        for name, policies in EXPECTED_POLICIES_DATA.items()
    ],
)
def test_100_c7nconfigs(
    configs, name, policies
):  # pylint: disable=redefined-outer-name
    _, c7nconfigs = configs
    c7n_configs = list(filter(lambda c7nconfig: c7nconfig.profile == name, c7nconfigs))
    assert len(c7n_configs) == len(policies)
