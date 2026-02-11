#!/usr/bin/env python3
# -*- coding:utf-8 -*-
########################################################################################################################
# This file is a part of Jeyriku.net.
#
# Created: 11.02.2026
# Author: Jeremie Rouzet
#
# Copyright (c) 2026 Jeyriku.net
########################################################################################################################
"""
CheckSysVers - A Python package to check operating system versions across different platforms.

This package provides tools to check OS versions for:
- Local systems: Linux, Windows, macOS, Cisco, Juniper, Ubiquiti
- Remote systems: via SSH connection
"""

__version__ = "0.1.0"
__author__ = "Jeremie Rouzet"
__email__ = "jeremie@jeyriku.net"

from .local_checker import LocalSysVersChecker
from .remote_checker import RemoteSysVersChecker

__all__ = ['LocalSysVersChecker', 'RemoteSysVersChecker']
