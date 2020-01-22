#!/usr/bin/env python3
""" Use setup.cfg to configure setuptools. """
from pkg_resources import VersionConflict, require
from setuptools import setup


SETUPTOOLS_VER = "38.6.0"

try:
    require("setuptools>=" + SETUPTOOLS_VER)
except VersionConflict as err:
    import logging
    import sys

    logging.critical(err)
    sys.exit(f"Setuptools <={SETUPTOOLS_VER} is required.")

setup(use_scm_version=True)
