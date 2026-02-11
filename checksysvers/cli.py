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
Command-line interface for CheckSysVers.
"""

import argparse
import logging
import sys
import getpass
import os
from .local_checker import LocalSysVersChecker
from .remote_checker import RemoteSysVersChecker


def setup_logging(verbose=False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Check operating system versions across different platforms.'
    )

    parser.add_argument(
        '--local',
        action='store_true',
        help='Check local system version'
    )

    parser.add_argument(
        '--remote',
        metavar='DEVICE',
        type=str,
        help='Check remote device version (requires device hostname/IP)'
    )

    parser.add_argument(
        '--device-type',
        type=str,
        choices=['cisco', 'juniper', 'ubiquiti', 'linux', 'windows', 'macos', 'auto'],
        help='Device type for remote check (use "auto" to automatically detect)'
    )

    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='List devices from Infrahub inventory'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--prompt-credentials',
        action='store_true',
        help='Prompt for credentials interactively instead of using environment variables'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Prompt for credentials if requested
    ssh_username = None
    ssh_password = None
    infrahub_token = None

    if args.prompt_credentials:
        if args.remote or args.list_devices:
            print("=== Credential Prompt ===")

        if args.remote:
            ssh_username = input("SSH Username: ")
            ssh_password = getpass.getpass("SSH Password: ")

        if args.list_devices:
            if not infrahub_token:
                infrahub_token = getpass.getpass("Infrahub API Token: ")

    # If no arguments provided, default to local check
    if not any([args.local, args.remote, args.list_devices]):
        args.local = True

    if args.local:
        checker = LocalSysVersChecker()
        version = checker.local_check_version()
        if version:
            print(f"Local System Version: {version}")
        else:
            print("Failed to determine local system version.")
            sys.exit(1)

    if args.remote:
        if not args.device_type:
            print("Error: --device-type is required for remote checks.")
            sys.exit(1)

        # If credentials weren't prompted and aren't in environment, prompt now
        if not ssh_username:
            ssh_username = os.getenv('SSH_USERNAME')
            if not ssh_username:
                ssh_username = input(f"SSH Username for {args.remote}: ")

        if not ssh_password:
            ssh_password = os.getenv('SSH_PASSWORD')
            if not ssh_password:
                ssh_password = getpass.getpass(f"SSH Password for {ssh_username}@{args.remote}: ")

        checker = RemoteSysVersChecker(username=ssh_username, password=ssh_password)
        version = checker.remote_check_version(args.remote, args.device_type)
        if version:
            print(f"Remote System Version ({args.remote}): {version}")
        else:
            print(f"Failed to determine remote system version for {args.remote}.")
            sys.exit(1)

    if args.list_devices:
        checker = RemoteSysVersChecker(infrahub_token=infrahub_token)
        devices = checker.recover_device_list()
        if devices:
            print(f"Found {len(devices)} devices:")
            for device in devices:
                device_name = None
                os_version = None

                # Extract device name and OS version from the structure
                if isinstance(device, dict):
                    # Handle GraphQL API format: {'id': '...', 'name': {'value': '...'}, 'osversion': {'node': {'name': {'value': '...'}}}}
                    if 'name' in device and isinstance(device['name'], dict) and 'value' in device['name']:
                        device_name = device['name']['value']
                    elif 'name' in device:
                        device_name = device['name']
                    else:
                        device_name = str(device)

                    # Extract OS version from relationship structure
                    if 'osversion' in device and device['osversion']:
                        if isinstance(device['osversion'], dict) and 'node' in device['osversion']:
                            node = device['osversion']['node']
                            if node and isinstance(node, dict) and 'name' in node:
                                if isinstance(node['name'], dict) and 'value' in node['name']:
                                    os_version = node['name']['value']
                                else:
                                    os_version = node['name']
                    # Fallback to direct os_version field
                    elif 'os_version' in device and isinstance(device['os_version'], dict) and 'value' in device['os_version']:
                        os_version = device['os_version']['value']
                    elif 'os_version' in device:
                        os_version = device['os_version']
                else:
                    # Handle SDK object with attributes
                    device_name = getattr(device, 'name', str(device))
                    os_version = getattr(device, 'os_version', None)
                    if not os_version:
                        osversion_rel = getattr(device, 'osversion', None)
                        if osversion_rel:
                            os_version = getattr(osversion_rel, 'name', None)

                # Format output with OS version if available
                if os_version:
                    print(f"  - {device_name:<50} | OS: {os_version}")
                else:
                    print(f"  - {device_name}")
        else:
            print("No devices found or unable to connect to Infrahub.")


if __name__ == '__main__':
    main()
