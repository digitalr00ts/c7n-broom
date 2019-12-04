""" Generate reports """

import dataclasses
import json
import logging
from collections import UserDict
from dataclasses import asdict
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import jmespath
from tabulate import tabulate

from c7n_broom.actions.helper import account_profile_policy_str
from c7n_broom.util import ExtendedEnum


_LOGGER = logging.getLogger(__name__)


class ResourceKeyDict(UserDict):  # pylint: disable=too-many-ancestors
    """ Custom dict for ResourceKey """

    def __str__(self) -> str:
        """ Formatted to be passed into jmespath """
        return ", ".join(map(lambda item: f"{item[0]}: {item[1]}", self.items()))


@dataclasses.dataclass(eq=True, frozen=True)
class ResourceKey:
    """ Data structure for descriptions of resources used in report generation """

    name: str
    id: str  # pylint: disable=invalid-name
    size: str
    # date: str
    region: str = "region"
    tags: str = "Tags"
    extras: Tuple[Tuple[str, str], ...] = dataclasses.field(default_factory=tuple)

    @property
    def data(self) -> ResourceKeyDict:
        """ Return an "expanded" version of the resource key """
        rtn_data = asdict(self)
        rtn_data.update(rtn_data.pop("extras"))
        return ResourceKeyDict(rtn_data)


class ResourceKeys(ExtendedEnum):
    """ Descriptions of resources used in report generation """

    ami = ResourceKey(
        id="ImageId",
        name="Name",
        size="X",
        # date="CreationDate",
        # extras=(("BlockDeviceMappings", "BlockDeviceMappings"),)
    )
    ebs = ResourceKey(
        id="VolumeId",
        name="X",
        size="Size",
        # date="CreateTime",
    )
    ebs_snapshot = ResourceKey(
        id="SnapshotId",
        name="VolumeId",
        size="VolumeSize",
        # date="StartTime",
    )
    ec2 = ResourceKey(
        id="InstanceId",
        name="ImageId",
        size="InstanceType",
        # date="LaunchTime",
    )
    rds = ResourceKey(
        id="DBInstanceArn",
        name="DBInstanceIdentifier",
        size="AllocatedStorage",
        # date="InstanceCreateTime",
    )
    rds_cluster_snapshot = ResourceKey(
        id="DBClusterSnapshotArn",
        name="DBClusterSnapshotIdentifier",
        size="AllocatedStorage",
        # date="SnapshotCreateTime",
    )
    rds_snapshot = ResourceKey(
        id="DBSnapshotArn",
        name="DBSnapshotIdentifier",
        size="AllocatedStorage",
        # date="SnapshotCreateTime",
    )
    test = ResourceKey(
        id="key",
        name="label",
        size="",
        # date="datetime",
        extras=(("Key", "keyname"),),
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


def get_data_map(c7n_config, data_path="data") -> Dict[str, Any]:
    """ Queries data for resource key """
    resource_key = _get_resourcekey(c7n_config.resource_type.replace("-", "_"))
    datafile = (
        Path(data_path).joinpath(account_profile_policy_str(c7n_config)).with_suffix(".json")
    )
    expression = jmespath.compile(f"[].{{{resource_key.data}}}")
    if datafile.is_file():
        rawdata = expression.search(json.loads(datafile.read_bytes()))
    else:
        _LOGGER.error("File not found %s", datafile)
        rawdata = dict()
    for item in rawdata:
        if item.get("tags"):
            item["tags"] = dict((tag["Key"], tag["Value"]) for tag in item["tags"])
    return rawdata


def get_table(c7n_config, fmt="simple", data_path="data") -> str:
    """ Generate table str """
    return tabulate(
        get_data_map(c7n_config, data_path), headers="keys", showindex=True, tablefmt=fmt
    )


def write(c7n_config, fmt="md", data_path="data", output_path="reports") -> Optional[PathLike]:
    """ Write report file """
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
