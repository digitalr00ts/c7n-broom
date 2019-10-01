"""
Helper functions
"""

import json
import logging
import pathlib

from typing import Dict, FrozenSet, Iterable, List

import boto3
import botocore.exceptions
import jmespath

from pkg_resources import resource_filename


_LOGGER = logging.getLogger(__name__)


def get_region_names(partition: str = "aws") -> Dict[str, str]:
    """
    Maps AWS region names to human friendly names.

    Parameters
    ----------
    partition : str, optional
        AWS partions: aws, aws-cn, aws-us-gov, aws-iso, aws-iso-b (default "aws")

    Returns
    -------
    Dict[str, str]
        A map of region names to their human friend names.
    """
    endpoints_file = pathlib.Path(resource_filename("botocore", "data/endpoints.json"))

    with endpoints_file.open("r") as fid:
        jmes_search = f"partitions[?partition == '{partition}'].regions"
        region_data = jmespath.search(jmes_search, json.load(fid))

    region_data = (
        {k: v["description"] for k, v in region_data[0].items()}
        if len(region_data) == 1
        else dict()
    )

    return region_data


def get_regions_accessible(
    regions: Iterable = get_region_names(), session=boto3.Session()
) -> FrozenSet[str]:
    """
    Obtains accessible regions.

    Parameters
    ----------
    regions : Iterable, optional
        [description] (default lambda:list(get_region_names().keys()))

    Returns
    -------
    Tuple[str]
        AWS Regions
    """
    ret_regions: List[str] = list()

    for region in regions:
        client = session.client("sts", region_name=region)
        try:
            client.get_caller_identity()
        except botocore.exceptions.ClientError:
            _LOGGER.debug("Unable to access region %s.", region)
        else:
            ret_regions.append(region)

    if not ret_regions:
        _LOGGER.error(
            "Access to all regions failed. Credentials may be invalid or there is a network issue."
        )

    return frozenset(ret_regions)
