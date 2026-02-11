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
        choices=['cisco', 'juniper', 'ubiquiti', 'linux', 'windows', 'macos'],
        help='Device type for remote check'
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
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

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

        checker = RemoteSysVersChecker()
        version = checker.remote_check_version(args.remote, args.device_type)
        if version:
            print(f"Remote System Version ({args.remote}): {version}")
        else:
            print(f"Failed to determine remote system version for {args.remote}.")
            sys.exit(1)

    if args.list_devices:
        checker = RemoteSysVersChecker()
        devices = checker.recover_device_list()
        if devices:
            print(f"Found {len(devices)} devices:")
            for device in devices:
                print(f"  - {device}")
        else:
            print("No devices found or unable to connect to Infrahub.")


if __name__ == '__main__':
    main()
