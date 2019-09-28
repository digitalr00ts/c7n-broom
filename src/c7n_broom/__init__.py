""" c7n Broom top level """
import logging

import pkg_resources

from .base import C7nConfig, REGION_MAP


try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    __version__ = ""

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["C7nConfig"]
