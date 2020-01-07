""" Process pricing information """
import itertools
import logging
from typing import Any, Dict, Sequence


_LOGGER = logging.getLogger(__name__)


def group_by(
    datamap: Sequence[Dict[str, Any]], attribute: str, region_first: bool = False
) -> Dict[str, Any]:
    """ Group query data by attribute """

    def sort_key(item_):
        _LOGGER.debug("SORT KEY: %s", item_)
        return item_[attribute]

    if not region_first:
        return {
            key_: tuple(val_)
            for key_, val_ in itertools.groupby(sorted(datamap, key=sort_key), key=sort_key)
        }

    return dict(
        map(lambda item_: (item_[0], group_by(item_[1], attribute)), group_by(datamap, "region"))
    )


def count_by(datamap: Sequence[Dict[str, Any]], attribute: str, region_first: bool = False):
    """ Counts items by attribute """
    if not region_first:
        return map(
            lambda item_: (item_[0], sum(1 for _ in item_[1])),
            dict(group_by(datamap, attribute=attribute, region_first=False)).items(),
        )

    return map(
        lambda data_: (data_[0], count_by(data_[1], attribute, region_first=False)),
        dict(group_by(datamap, attribute="region", region_first=False)).items(),
    )


def group_by_size(datamap, region_first: bool = True):
    """ Group query results by size """
    return group_by(datamap, attribute="size", region_first=region_first)


def count_by_size(datamap, region_first: bool = True):
    """ Counts items by size """
    return count_by(datamap, attribute="size", region_first=region_first)


def count_by_region(datamap: Sequence[Dict[str, Any]], and_by_size: bool = False):
    kwargs = {"attribute": "region", "region_first": False}
    if and_by_size and datamap and any(map(lambda item_: item_.get("size", None), datamap)):
        kwargs = {"attribute": "size", "region_first": True}
    return count_by(datamap, **kwargs)
