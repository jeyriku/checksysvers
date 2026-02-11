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
    from infrahub_sdk import InfrahubClientSync, Config
except ImportError:
    InfrahubClientSync = None
    Config = None

try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False
    ConnectHandler = None
    NetmikoAuthenticationException = None
    NetmikoTimeoutException = None

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    paramiko = None

logger = logging.getLogger(__name__)


class RemoteSysVersChecker:
    """
    This class defines methods to check the operating system version of remote systems.
    """

    def __init__(self, username=None, password=None, infrahub_token=None):
        self.device = None
        self.username = username or os.getenv('SSH_USERNAME')
        self.password = password or os.getenv('SSH_PASSWORD')
        self.port = os.getenv('SSH_PORT', 22)
        self.infrahub_token = infrahub_token  # Store for later use
        logger.debug(f'Initialized RemoteSysVersChecker with username: {self.username}, port: {self.port}')

    def recover_device_list(self):
        """
        To recover the device list we will use the infrahub GraphQL API if available.
        If we don't manage to recover device list from the api we will use infrahub python sdk if available.
        """
        devices = []
        # Use provided token or fallback to environment variable
        infrahub_token = self.infrahub_token or os.getenv('INFRAHUB_API_TOKEN')
        tls_insecure = os.getenv('INFRAHUB_TLS_INSECURE', 'false').lower() == 'true'
        device_schema = os.getenv('INFRAHUB_DEVICE_SCHEMA', 'JeylanDevice')  # Default to JeylanDevice

        # First try to recover device list using GraphQL API
        if infrahub_token and httpx:
            try:
                url = os.getenv('INFRAHUB_URL', 'https://infrahub.example.com')
                # Add /graphql if not already in the URL
                if not url.endswith('/graphql'):
                    url = f"{url}/graphql"
                query = f"""
                query {{
                  {device_schema} {{
                    edges {{
                      node {{
                        id
                        name {{
                          value
                        }}
                        osversion {{
                          node {{
                            name {{
                              value
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """
                # Configure SSL verification
                verify = not tls_insecure
                if tls_insecure:
                    logger.warning('TLS verification is disabled (INFRAHUB_TLS_INSECURE=true)')

                # Use a client context to properly handle SSL verification
                with httpx.Client(verify=verify) as client:
                    response = client.post(url, json={'query': query}, headers={'X-INFRAHUB-KEY': infrahub_token})
                    response.raise_for_status()
                    data = response.json()
                    devices = [edge['node'] for edge in data['data'][device_schema]['edges']]
                    logger.info(f'Recovered {len(devices)} devices from Infrahub GraphQL API.')
                    return devices
            except Exception as e:
                logger.error(f'Error recovering devices from Infrahub GraphQL API: {e}')
                # Don't return yet, try SDK as fallback

        # Second try to recover device list using infrahub python sdk
        if InfrahubClientSync and infrahub_token:
            try:
                infrahub_url = os.getenv('INFRAHUB_URL', 'https://infrahub.example.com')
                config = Config(api_token=infrahub_token, tls_insecure=tls_insecure)
                if tls_insecure:
                    logger.warning('TLS verification is disabled for SDK (INFRAHUB_TLS_INSECURE=true)')
                client = InfrahubClientSync(address=infrahub_url, config=config)
                devices = client.all(device_schema)
                logger.info(f'Recovered {len(devices)} devices from Infrahub SDK.')
                return devices
            except Exception as e:
                logger.error(f'Error recovering devices from Infrahub SDK: {e}')

        if not devices:
            logger.warning('INFRAHUB_API_TOKEN not set or unable to connect to Infrahub.')

        return devices

    def remote_check_version(self, device, device_type):
        """
        Check the operating system version of a remote device based on its type.
        Uses paramiko for network devices (handles both shell and CLI access),
        otherwise falls back to netmiko or subprocess.
        """
        # Auto-detect mode: try multiple device types
        if device_type.lower() == 'auto':
            if NETMIKO_AVAILABLE and self.password:
                return self._try_auto_detect_device_type(device)
            else:
                logger.error('Auto-detection requires netmiko and password authentication')
                return None

        # For Juniper, prefer paramiko over netmiko because:
        # - Root users land in a shell and need 'cli -c' wrapper
        # - Non-root users land directly in CLI
        # - Paramiko can handle both cases more reliably
        if device_type.lower() == 'juniper' and PARAMIKO_AVAILABLE and self.password:
            logger.debug('Using paramiko for Juniper (handles both shell and CLI access)')
            return self._remote_check_juniper_with_paramiko(device)

        # For Cisco, also prefer paramiko because some devices land in shell
        # - Some IOS-XE devices land in bash shell and need /usr/bin/cli wrapper
        # - Standard IOS devices land directly in CLI
        if device_type.lower() == 'cisco' and PARAMIKO_AVAILABLE and self.password:
            logger.debug('Using paramiko for Cisco (handles both shell and CLI access)')
            return self._remote_check_cisco_with_paramiko(device)

        # Prefer netmiko if available and password is provided
        if NETMIKO_AVAILABLE and self.password:
            result = self._remote_check_with_netmiko(device, device_type)
            return result
        else:
            # Fallback to subprocess method
            if not NETMIKO_AVAILABLE:
                logger.info('netmiko not available, using subprocess method')
            if not self.password:
                logger.info('No password provided, trying SSH key authentication')
            return self._remote_check_with_subprocess(device, device_type)

    def _try_auto_detect_device_type(self, device):
        """
        Try to automatically detect the device type by attempting connections with different device types.
        """
        device_types_to_try = [
            ('cisco_ios', 'Cisco IOS'),
            ('juniper', 'Juniper JunOS'),
            ('cisco_xe', 'Cisco IOS-XE'),
            ('cisco_nxos', 'Cisco NX-OS'),
        ]

        logger.info(f'Auto-detecting device type for {device}...')

        for netmiko_type, friendly_name in device_types_to_try:
            try:
                logger.debug(f'Trying {friendly_name} ({netmiko_type})...')

                connection_params = {
                    'device_type': netmiko_type,
                    'host': device,
                    'username': self.username,
                    'password': self.password,
                    'port': self.port,
                    'timeout': 10,  # Shorter timeout for auto-detection
                }

                with ConnectHandler(**connection_params) as net_connect:
                    output = net_connect.send_command('show version', read_timeout=15)

                    if output and output.strip():
                        logger.info(f'Successfully detected device type: {friendly_name}')
                        logger.info(f'Remote Version on {device}: {output.strip()[:200]}...')
                        return output.strip()

            except NetmikoAuthenticationException as e:
                logger.error(f'Authentication failed for {device}: {e}')
                return None  # Auth failure is fatal, don't try other types
            except Exception as e:
                logger.debug(f'{friendly_name} failed: {e}')
                continue

        logger.error(f'Failed to auto-detect device type for {device}. Tried: {[name for _, name in device_types_to_try]}')
        return None

    def _remote_check_cisco_with_paramiko(self, device):
        """
        Check Cisco device version using paramiko.
        Handles both cases:
        - Direct CLI access (standard IOS/IOS-XE)
        - Shell access (some IOS-XE devices) where we need to use '/usr/bin/cli' or 'vtysh'
        """
        if not PARAMIKO_AVAILABLE:
            logger.error('paramiko not available')
            return None

        try:
            logger.debug(f'Connecting to {device} using paramiko')

            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect
            ssh.connect(
                hostname=device,
                port=int(self.port),
                username=self.username,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )

            # Try multiple methods - Cisco behaves differently based on device/user
            commands_to_try = [
                'show version',  # Direct CLI (standard IOS/IOS-XE)
                '/usr/bin/cli "show version"',  # IOS-XE with shell access
                'vtysh -c "show version"',  # For devices using vtysh (FRRouting/Quagga)
            ]

            output = None
            for command in commands_to_try:
                try:
                    logger.debug(f'Trying command: {command}')
                    stdin, stdout, stderr = ssh.exec_command(command, timeout=30)

                    cmd_output = stdout.read().decode('utf-8', errors='ignore')
                    cmd_error = stderr.read().decode('utf-8', errors='ignore')

                    # Check if we got valid output (contains version info)
                    if cmd_output and cmd_output.strip() and 'not found' not in cmd_output.lower():
                        output = cmd_output.strip()
                        logger.debug(f'Command "{command}" succeeded')
                        break
                    else:
                        logger.debug(f'Command "{command}" failed or returned no data: {cmd_error[:100] if cmd_error else "no error"}')
                except Exception as cmd_error:
                    logger.debug(f'Command "{command}" raised exception: {cmd_error}')
                    continue

            ssh.close()

            if output:
                logger.info(f'Remote Cisco Version on {device}: {output[:200]}...')
                return output
            else:
                logger.error(f'All Cisco commands failed on {device}')
                return None

        except paramiko.AuthenticationException as e:
            logger.error(f'Authentication failed for {device}: {e}')
            return None
        except paramiko.SSHException as e:
            logger.error(f'SSH error connecting to {device}: {e}')
            return None
        except Exception as e:
            logger.error(f'Error checking Cisco version on {device} with paramiko: {e}')
            return None

    def _remote_check_juniper_with_paramiko(self, device):
        """
        Check Juniper device version using paramiko (fallback when netmiko fails).
        Handles both cases:
        - Direct CLI access (non-root users)
        - Shell access (root user) where we need to use 'cli -c'
        """
        if not PARAMIKO_AVAILABLE:
            logger.error('paramiko not available')
            return None

        try:
            logger.debug(f'Connecting to {device} using paramiko')

            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect
            ssh.connect(
                hostname=device,
                port=int(self.port),
                username=self.username,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )

            # Try multiple methods - Juniper behaves differently based on user account
            commands_to_try = [
                'show version',  # Direct CLI (non-root users land directly in CLI)
                'cli -c "show version"',  # Shell (root lands in shell, needs cli wrapper)
            ]

            output = None
            for command in commands_to_try:
                try:
                    logger.debug(f'Trying command: {command}')
                    stdin, stdout, stderr = ssh.exec_command(command, timeout=30)

                    cmd_output = stdout.read().decode('utf-8', errors='ignore')
                    cmd_error = stderr.read().decode('utf-8', errors='ignore')

                    # Check if we got valid output (contains version info)
                    if cmd_output and cmd_output.strip() and 'not found' not in cmd_output.lower():
                        output = cmd_output.strip()
                        logger.debug(f'Command "{command}" succeeded')
                        break
                    else:
                        logger.debug(f'Command "{command}" failed or returned no data: {cmd_error[:100] if cmd_error else "no error"}')
                except Exception as cmd_error:
                    logger.debug(f'Command "{command}" raised exception: {cmd_error}')
                    continue

            ssh.close()

            if output:
                logger.info(f'Remote Juniper Version on {device}: {output[:200]}...')
                return output
            else:
                logger.error(f'All Juniper commands failed on {device}')
                return None

        except paramiko.AuthenticationException as e:
            logger.error(f'Authentication failed for {device}: {e}')
            return None
        except paramiko.SSHException as e:
            logger.error(f'SSH error connecting to {device}: {e}')
            return None
        except Exception as e:
            logger.error(f'Error checking Juniper version on {device} with paramiko: {e}')
            return None

    def _remote_check_with_netmiko(self, device, device_type):
        """
        Check remote device version using netmiko (preferred for network devices).
        """
        try:
            # Map device types to netmiko device types
            netmiko_device_types = {
                'cisco': 'cisco_ios',
                'juniper': 'juniper_junos',  # Changed from 'juniper' to 'juniper_junos'
            }

            device_type_netmiko = netmiko_device_types.get(device_type.lower(), 'cisco_ios')
            logger.debug(f'Connecting to {device} using netmiko with device_type={device_type_netmiko}')

            # Create connection parameters
            connection_params = {
                'device_type': device_type_netmiko,
                'host': device,
                'username': self.username,
                'password': self.password,
                'port': self.port,
                'timeout': 30,  # Increased timeout
                'session_timeout': 60,  # Add session timeout
            }

            # Connect to the device
            with ConnectHandler(**connection_params) as net_connect:
                # Send the show version command
                output = net_connect.send_command('show version')

                if output and output.strip():
                    logger.info(f'Remote {device_type} Version on {device}: {output.strip()[:200]}...')
                    return output.strip()
                else:
                    logger.warning(f'No output received from {device}')
                    return None

        except NetmikoAuthenticationException as e:
            logger.error(f'Authentication failed for {device}: {e}')
            return None
        except NetmikoTimeoutException as e:
            logger.error(f'Connection timeout to {device}: {e}')
            return None
        except Exception as e:
            error_msg = str(e)
            logger.error(f'Error checking remote {device_type} version on {device}: {error_msg}')

            # Suggest trying auto-detection or other device types
            if 'Pattern not detected' in error_msg or 'not recognized' in error_msg:
                if device_type.lower() == 'cisco':
                    logger.info('Hint: If this is not a Cisco device, try --device-type juniper or --device-type auto')
                elif device_type.lower() == 'juniper':
                    logger.info('Hint: If this is not a Juniper device, try --device-type cisco or --device-type auto')
                else:
                    logger.info('Hint: Try --device-type auto to automatically detect the device type')
            return None

    def _remote_check_with_subprocess(self, device, device_type):
        """
        Check remote device version using subprocess (fallback method).
        """
        try:
            if device_type.lower() == 'cisco':
                # For Cisco devices, try multiple methods as some land in a shell
                commands = [
                    'show version',  # Direct CLI access
                    '/usr/bin/cli "show version"',  # IOS-XE with shell access
                    'vtysh -c "show version"',  # For devices using vtysh
                ]
            elif device_type.lower() == 'juniper':
                # For Juniper devices, different behavior based on user account:
                # - Non-root users: land directly in CLI → use 'show version'
                # - Root user: lands in shell → needs 'cli -c "show version"'
                commands = [
                    'show version',  # Direct CLI access (non-root users)
                    'cli -c "show version"',  # Shell to CLI (root user)
                    'cli show version',  # Alternative syntax
                ]
            elif device_type.lower() == 'ubiquiti':
                commands = ['cat /etc/version']
            elif device_type.lower() == 'linux':
                commands = ['cat /etc/os-release | grep PRETTY_NAME']
            elif device_type.lower() == 'windows':
                commands = ['systeminfo | findstr /B /C:"OS Name" /C:"OS Version"']
            elif device_type.lower() == 'macos':
                commands = ['sw_vers']
            else:
                logger.warning(f'Unsupported device type: {device_type}')
                return None

            # Check if sshpass is available and password is provided
            use_sshpass = self.password and self._is_sshpass_available()

            # Try each command until one succeeds
            last_error = None
            for command in commands if isinstance(commands, list) else [commands]:
                try:
                    if use_sshpass:
                        # Use sshpass to provide password
                        ssh_command = f'sshpass -p "{self.password}" ssh -p {self.port} -o StrictHostKeyChecking=no {self.username}@{device} "{command}"'
                    else:
                        # Assume SSH key authentication
                        ssh_command = f'ssh -p {self.port} -o StrictHostKeyChecking=no {self.username}@{device} "{command}"'

                    logger.debug(f'Trying command: ssh -p {self.port} {self.username}@{device} "{command}"')
                    output = subprocess.check_output(ssh_command, shell=True, stderr=subprocess.STDOUT).decode()

                    # Check if output contains meaningful data
                    if output.strip() and 'command not found' not in output.lower():
                        logger.info(f'Remote {device_type} Version on {device}: {output.strip()[:200]}...')  # Log first 200 chars
                        return output.strip()
                    else:
                        logger.debug(f'Command "{command}" did not return valid output, trying next...')
                        last_error = f'Command "{command}" returned empty or invalid output'
                except subprocess.CalledProcessError as e:
                    logger.debug(f'Command "{command}" failed: {e}')
                    last_error = e
                    continue

            # If we get here, all commands failed
            if last_error:
                logger.error(f'Error checking remote {device_type} version on {device}: All commands failed. Last error: {last_error}')
            return None
        except Exception as e:
            logger.error(f'Error checking remote {device_type} version on {device}: {e}')
            return None

    def _is_sshpass_available(self):
        """Check if sshpass is available on the system."""
        try:
            subprocess.run(['which', 'sshpass'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            logger.warning('sshpass not found. SSH key authentication will be used.')
            return False
