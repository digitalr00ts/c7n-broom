""" c7n Broom top level """
import logging as _logging

import pkg_resources

from c7n_broom.config import C7nCfg
from c7n_broom.main import Sweeper

from . import actions, config, data


try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    __version__ = ""


__all__ = ["C7nCfg", "Sweeper"]

_logging.getLogger(__name__).addHandler(_logging.NullHandler())
_logging.getLogger("custodian").setLevel(_logging.INFO)
_logging.getLogger("botocore").setLevel(_logging.ERROR)
_logging.getLogger("urllib3").setLevel(_logging.ERROR)
_logging.getLogger("s3transfer").setLevel(_logging.ERROR)
_logging.getLogger("urllib3").setLevel(_logging.ERROR)
_logging.getLogger("vyper").setLevel(_logging.ERROR)
