""" Generate reports """

import dataclasses
import json
import logging
from collections import UserDict
from dataclasses import asdict
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import jmespath
from boto_remora.pricing import AWSResourceKeys
from tabulate import tabulate

from c7n_broom.actions.helper import account_profile_policy_str
from c7n_broom.util import ExtendedEnum


_LOGGER = logging.getLogger(__name__)


def _cap_1letter(string: str) -> str:
    return string[0].capitalize() + string[1:]


class ResourceKeyDict(UserDict):  # pylint: disable=too-many-ancestors
    """ Custom dict for ResourceKey """

    def __str__(self) -> str:
        """ Formatted to be passed into jmespath """
        return ", ".join(map(lambda item: f"{item[0]}: {item[1]}", self.items()))


@dataclasses.dataclass(eq=True, frozen=True)
class ResourceKey:
    """ Data structure for descriptions of resources used in report generation """

    id: str  # pylint: disable=invalid-name
    name: str = "SKIP"
    type: str = "SKIP"
    size: str = "SKIP"
    region: str = "region"
    date: str = "SKIP"
    tags: str = "Tags"
    extras: Tuple[Tuple[str, str], ...] = dataclasses.field(default_factory=tuple)

    @property
    def data(self) -> ResourceKeyDict:
        """ Return an "expanded" version of the resource key """
        rtn_data = dict(filter(lambda item_: item_[1] != "SKIP", asdict(self).items()))
        rtn_data.update(rtn_data.pop("extras"))
        return ResourceKeyDict(rtn_data)


class ResourceKeys(ExtendedEnum):
    """ Descriptions of resources used in report generation """

    ami = ResourceKey(
        id="ImageId",
        name="Name",
        date="CreationDate",
        # extras=(("BlockDeviceMappings", "BlockDeviceMappings"),)
    )
    ebs = ResourceKey(
        id="VolumeId",
        type=_cap_1letter(AWSResourceKeys.EBS.value.key),
        size="Size",
        date="CreateTime",
    )
    ebs_snapshot = ResourceKey(
        id="SnapshotId", name="VolumeId", size="VolumeSize", date="StartTime",
    )
    ec2 = ResourceKey(
        id="InstanceId",
        type=_cap_1letter(AWSResourceKeys.EC2.value.key),
        name="ImageId",
        date="LaunchTime",
    )
    rds = ResourceKey(
        id="DBInstanceArn",
        name="DBInstanceIdentifier",
        size="AllocatedStorage",
        date="InstanceCreateTime",
    )
    rds_cluster_snapshot = ResourceKey(
        id="DBClusterSnapshotArn",
        name="DBClusterSnapshotIdentifier",
        size="AllocatedStorage",
        date="SnapshotCreateTime",
    )
    rds_snapshot = ResourceKey(
        id="DBSnapshotArn",
        name="DBSnapshotIdentifier",
        size="AllocatedStorage",
        date="SnapshotCreateTime",
    )
    test = ResourceKey(
        id="key",
        name="label",
        size="",
        # date="datetime",
        # extras=(("Key", "keyname"),),
    )


@dataclasses.dataclass(frozen=True, eq=True)
class FileFormat:
    """ File extensions and formats for writing reports """

    html = "html"
    md = "github"  # pylint: disable=invalid-name
    txt = "simple"
    rst = "rst"


def _get_resourcekey(resource_type) -> ResourceKey:
    key = getattr(ResourceKeys, resource_type, None)
    if not key:
        raise RuntimeError(f"Not defined {resource_type}")
    return key.value


def get_data_map(c7n_config, data_path="data") -> Sequence[Dict[str, Any]]:
    """ Queries data for resource key """
    resource_key = _get_resourcekey(c7n_config.resource_type.replace("-", "_"))
    datafile = (
        Path(data_path).joinpath(account_profile_policy_str(c7n_config)).with_suffix(".json")
    )
    expression = jmespath.compile(f"[].{{{resource_key.data}}}")
    if not datafile.is_file():
        _LOGGER.error("File not found %s", datafile)
        return list()

    rawdata = expression.search(json.loads(datafile.read_bytes()))
    for item in rawdata:
        item["tags"] = (
            dict((tag["Key"], tag["Value"]) for tag in item["tags"])
            if item.get("tags")
            else dict()
        )

    return sorted(rawdata, key=lambda item_: item_["date"])


def get_table(c7n_config, fmt: str = "simple", data_path: str = "data") -> str:
    """ Generate table str """
    data = get_data_map(c7n_config, data_path)
    return tabulate(data, headers="keys", showindex=True, tablefmt=fmt)


def write(
    c7n_config, fmt: str = "md", data_path: str = "data", output_path: PathLike = "reports"
) -> Optional[PathLike]:
    """ Write report file """
    Path(output_path).mkdir(parents=True, exist_ok=True)
    reportfile = (
        Path(output_path).joinpath(account_profile_policy_str(c7n_config)).with_suffix(f".{fmt}")
    )
    _LOGGER.debug("Preparing to write %s", reportfile)
    filefmt = getattr(FileFormat, fmt)
    table = get_table(c7n_config, fmt=filefmt, data_path=data_path)
    if table:
        reportfile.write_text(get_table(c7n_config, fmt=filefmt, data_path=data_path))
    else:
        _LOGGER.debug("No data to write %s", reportfile)
        reportfile = None
    return reportfile
