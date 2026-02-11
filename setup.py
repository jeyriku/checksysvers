#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Setup script for checksysvers package.
This file provides backward compatibility with older Python packaging tools.
Modern installations should use pyproject.toml with pip >= 21.3
"""

from setuptools import setup

# Read version from package
try:
    from checksysvers import __version__
    version = __version__
except ImportError:
    version = "0.1.0"

setup(
    name="checksysvers",
    version=version,
    use_scm_version=False,
)
