#!/usr/bin/env python3
# -*- coding:utf-8 -*-
########################################################################################################################
# This file is a part of Jeyriku.net.
#
# Created: 01.02.2026 17:14:56
# Author: Jeremie Rouzet
#
# Last Modified: 11.02.2026
# Modified By: Jeremie Rouzet
#
# Copyright (c) 2026 Jeyriku.net
########################################################################################################################
"""
This module defines methods to check the local operating system version of various systems.
"""

import platform
import subprocess
import logging

logger = logging.getLogger(__name__)


class LocalSysVersChecker:
    """
    This class defines methods to check the local operating system version of various systems.
    """
    def __init__(self):
        self.system = platform.system()
        logger.debug(f'Detected system: {self.system}')

    def local_check_linux(self):
        """
        Check Linux operating system version.
        """
        try:
            with open('/etc/os-release') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('PRETTY_NAME'):
                        version = line.split('=')[1].strip().strip('"')
                        logger.info(f'Linux Version: {version}')
                        return version
        except Exception as e:
            logger.error(f'Error checking Linux version: {e}')
            return None

    def local_check_windows(self):
        """
        Check Windows operating system version.
        """
        try:
            version = platform.platform()
            logger.info(f'Windows Version: {version}')
            return version
        except Exception as e:
            logger.error(f'Error checking Windows version: {e}')
            return None

    def local_check_macos(self):
        """
        Check macOS operating system version.
        """
        try:
            version = platform.mac_ver()[0]
            logger.info(f'macOS Version: {version}')
            return version
        except Exception as e:
            logger.error(f'Error checking macOS version: {e}')
            return None

    def local_check_cisco(self):
        """
        Check Cisco operating system version.
        """
        try:
            output = subprocess.check_output(['show', 'version'], shell=True).decode()
            for line in output.splitlines():
                if 'Cisco IOS Software' in line:
                    logger.info(f'Cisco Version: {line.strip()}')
                    return line.strip()
        except Exception as e:
            logger.error(f'Error checking Cisco version: {e}')
            return None

    def local_check_juniper(self):
        """
        Check Juniper operating system version.
        """
        try:
            output = subprocess.check_output(['show', 'version'], shell=True).decode()
            for line in output.splitlines():
                if 'JUNOS Software Release' in line:
                    logger.info(f'Juniper Version: {line.strip()}')
                    return line.strip()
        except Exception as e:
            logger.error(f'Error checking Juniper version: {e}')
            return None

    def local_check_ubiquiti(self):
        """
        Check Ubiquiti operating system version.
        """
        try:
            output = subprocess.check_output(['cat', '/etc/version'], shell=True).decode().strip()
            logger.info(f'Ubiquiti Version: {output}')
            return output
        except Exception as e:
            logger.error(f'Error checking Ubiquiti version: {e}')
            return None

    def local_check_version(self):
        """
        Check the operating system version based on the detected system.
        """
        if self.system == 'Linux':
            return self.local_check_linux()
        elif self.system == 'Windows':
            return self.local_check_windows()
        elif self.system == 'Darwin':
            return self.local_check_macos()
        else:
            logger.warning('Unsupported system for version check.')
            return None
