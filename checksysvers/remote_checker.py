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
This module defines methods to check the operating system version of remote systems.
The following methods will connect to remote systems via SSH and execute commands to retrieve the OS version.
The credentials and connection details will be recovered from environment variables or ssh configuration files.
The list of devices will be recovered from infrahub inventory if available.
"""

import os
import subprocess
import logging

try:
    import httpx
except ImportError:
    httpx = None

try:
    import infrahub
except ImportError:
    infrahub = None

logger = logging.getLogger(__name__)


class RemoteSysVersChecker:
    """
    This class defines methods to check the operating system version of remote systems.
    """

    def __init__(self):
        self.device = None
        self.username = os.getenv('SSH_USERNAME')
        self.password = os.getenv('SSH_PASSWORD')
        self.port = os.getenv('SSH_PORT', 22)
        logger.debug(f'Initialized RemoteSysVersChecker with username: {self.username}, port: {self.port}')

    def recover_device_list(self):
        """
        To recover the device list we will use the infrahub GraphQL API if available.
        If we don't manage to recover device list from the api we will use infrahub python sdk if available.
        """
        devices = []
        infrahub_token = os.getenv('INFRAHUB_API_TOKEN')
        # First try to recover device list using GraphQL API
        if infrahub_token and httpx:
            try:
                url = os.getenv('INFRAHUB_URL', 'https://infrahub.example.com/graphql')
                query = """
                query {
                  InfraDevice {
                    edges {
                      node {
                        id
                        name {
                          value
                        }
                      }
                    }
                  }
                }
                """
                response = httpx.post(url, json={'query': query}, headers={'Authorization': f'Bearer {infrahub_token}'})
                response.raise_for_status()
                data = response.json()
                devices = [edge['node'] for edge in data['data']['InfraDevice']['edges']]
                logger.info(f'Recovered {len(devices)} devices from Infrahub GraphQL API.')
            except Exception as e:
                logger.error(f'Error recovering devices from Infrahub GraphQL API: {e}')
            return devices
        # Second try to recover device list using infrahub python sdk
        elif infrahub:
            try:
                client = infrahub.Client()
                devices = client.devices.list()
                logger.info(f'Recovered {len(devices)} devices from Infrahub SDK.')
            except Exception as e:
                logger.error(f'Error recovering devices from Infrahub SDK: {e}')
            return devices
        else:
            logger.warning('INFRAHUB_API_TOKEN not set or httpx not available. Cannot recover devices list.')
            return devices

    def remote_check_version(self, device, device_type):
        """
        Check the operating system version of a remote device based on its type.
        """
        try:
            if device_type.lower() == 'cisco':
                command = 'show version'
            elif device_type.lower() == 'juniper':
                command = 'show version'
            elif device_type.lower() == 'ubiquiti':
                command = 'cat /etc/version'
            elif device_type.lower() == 'linux':
                command = 'cat /etc/os-release | grep PRETTY_NAME'
            elif device_type.lower() == 'windows':
                command = 'systeminfo | findstr /B /C:"OS Name" /C:"OS Version"'
            elif device_type.lower() == 'macos':
                command = 'sw_vers'
            else:
                logger.warning(f'Unsupported device type: {device_type}')
                return None

            ssh_command = f'ssh -p {self.port} {self.username}@{device} "{command}"'
            output = subprocess.check_output(ssh_command, shell=True).decode()

            logger.info(f'Remote {device_type} Version on {device}: {output.strip()}')
            return output.strip()
        except Exception as e:
            logger.error(f'Error checking remote {device_type} version on {device}: {e}')
            return None
