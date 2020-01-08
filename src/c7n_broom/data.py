""" Process pricing information """
import itertools
import logging
from typing import Any, Dict, Sequence


_LOGGER = logging.getLogger(__name__)


def groupby(datamap: Sequence[Dict[str, Any]], attribute: str) -> Dict[str, Any]:
    """ Group query data by attribute """

    def sort_key(item_):
        _LOGGER.debug("SORT KEY: %s", item_)
        return item_[attribute]

    return {
        key_: tuple(val_)
        for key_, val_ in itertools.groupby(sorted(datamap, key=sort_key), key=sort_key)
    }


def groupby_region1st(datamap: Sequence[Dict[str, Any]], attribute: str) -> Dict[str, Any]:
    """ Group query data by region then attribute """
    return dict(
        map(
            lambda item_: (item_[0], groupby(item_[1], attribute)),
            dict(groupby(datamap, "region")).items(),
        )
    )


def countby(datamap: Sequence[Dict[str, Any]], attribute: str):
    """ Counts items by attribute """
    return map(
        lambda item_: (item_[0], sum(1 for _ in item_[1])),
        dict(groupby(datamap, attribute=attribute)).items(),
    )


def countby_region1st(datamap: Sequence[Dict[str, Any]], attribute: str):
    """ Counts items by attribute grouped by region """
    return map(
        lambda data_: (data_[0], dict(countby(data_[1], attribute))),
        dict(groupby(datamap, attribute="region")).items(),
    )


def count(datamap: Sequence[Dict[str, Any]]):
    """ Counts items by region and by type if type exists """
    if datamap and datamap[0].get("type"):
        countby_region1st(datamap, attribute="type")
    return countby(datamap, attribute="region")
