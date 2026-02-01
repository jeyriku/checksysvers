#!/usr/bin/env python3
# -*- coding:utf-8 -*-
########################################################################################################################
# This file is a part of Jeyriku.net.
#
# Created: 01.02.2026 17:14:56
# Author: Jeremie Rouzet
#
# Last Modified: 01.02.2026 18:09:54
# Modified By: Jeremie Rouzet
#
# Copyright (c) 2026 Jeyriku.net
########################################################################################################################
'''
This scripts checks the operating system version and prints it to the console
for different kind of systems such as Linux, Windows, macOS, Cisco, Juniper, Ubiquiti
'''

import platform
import subprocess
import logging
import os
import httpx
import infrahub


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LocalSysVersChecker:
    '''
    This class defines methods to check the local operating system version of various systems.
    '''
    def __init__(self):
        self.system = platform.system()
        logger.debug(f'Detected system: {self.system}')

    def local_check_linux(self):
        '''
        Check Linux operating system version.
        '''
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
        '''
        Check Windows operating system version.
        '''
        try:
            version = platform.platform()
            logger.info(f'Windows Version: {version}')
            return version
        except Exception as e:
            logger.error(f'Error checking Windows version: {e}')
            return None

    def local_check_macos(self):
        '''
        Check macOS operating system version.
        '''
        try:
            version = platform.mac_ver()[0]
            logger.info(f'macOS Version: {version}')
            return version
        except Exception as e:
            logger.error(f'Error checking macOS version: {e}')
            return None

    def local_check_cisco(self):
        '''
        Check Cisco operating system version.
        '''
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
        '''
        Check Juniper operating system version.
        '''
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
        '''
        Check Ubiquiti operating system version.
        '''
        try:
            output = subprocess.check_output(['cat', '/etc/version'], shell=True).decode().strip()
            logger.info(f'Ubiquiti Version: {output}')
            return output
        except Exception as e:
            logger.error(f'Error checking Ubiquiti version: {e}')
            return None

    def local_check_version(self):
        '''
        Check the operating system version based on the detected system.
        '''
        if self.system == 'Linux':
            return self.local_check_linux()
        elif self.system == 'Windows':
            return self.local_check_windows()
        elif self.system == 'Darwin':
            return self.check_macos()
        else:
            logger.warning('Unsupported system for version check.')
            return None


class RemoteSysVersChecker:
    '''
    This class defines methods to check the operating system version of remote systems.
    The following methods will connect to remote systems via SSH and execute commands to retrieve the OS version.
    The credentials and connection details will be recovered from environment variables or ssh configuration files.
    The list of devices will be recovered from infrahub invetory if available.
    '''

    def __init__(self):
        self.device = None
        self.username = os.getenv('SSH_USERNAME')
        self.password = os.getenv('SSH_PASSWORD')
        self.port = os.getenv('SSH_PORT', 22)
        logger.debug(f'Initialized RemoteSysVersChecker with username: {self.username}, port: {self.port}')

    def recover_device_list(self):
        '''
        To recover the device list we will use the infrahub GraphQL API if available.
        If we don't manage to recover device list from the api we will use infrahub python sdk if available.
        '''
        devices = []
        infrahub_token = os.getenv('INFRAHUB_API_TOKEN')
        # First try to recover device list using GraphQL API
        if infrahub_token:
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
        elif 'infrahub' in globals():
            try:
                client = infrahub.Client()
                devices = client.devices.list()
                logger.info(f'Recovered {len(devices)} devices from Infrahub SDK.')
            except Exception as e:
                logger.error(f'Error recovering devices from Infrahub SDK: {e}')
            return devices
        else:
            logger.warning('INFRAHUB_API_TOKEN not set. Cannot recover devices list.')


    def remote_check_version(self, device, device_type):
        '''
        Check the operating system version of a remote device based on its type.
        '''
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


if __name__ == '__main__':
    local_checker = LocalSysVersChecker()
    local_checker.local_check_version()
    remote_checker = RemoteSysVersChecker()
    remote_checker.remote_check_version()
