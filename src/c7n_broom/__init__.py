""" c7n Broom top level """
import logging

import pkg_resources

from .base import REGION_MAP, C7nConfig

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    __version__ = ""


__all__ = ["C7nConfig"]

logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.getLogger(__name__).setLevel(logging.DEBUG)
logging.getLogger("custodian").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("s3transfer").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
