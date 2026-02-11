#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Tests for the checksysvers package.
"""

import pytest
from checksysvers import LocalSysVersChecker, RemoteSysVersChecker


class TestLocalSysVersChecker:
    """Tests for LocalSysVersChecker class."""

    def test_init(self):
        """Test LocalSysVersChecker initialization."""
        checker = LocalSysVersChecker()
        assert checker.system is not None
        assert isinstance(checker.system, str)

    def test_local_check_version(self):
        """Test local_check_version method."""
        checker = LocalSysVersChecker()
        version = checker.local_check_version()
        # Version might be None on unsupported systems, but should return something
        assert version is not None or checker.system not in ['Linux', 'Windows', 'Darwin']


class TestRemoteSysVersChecker:
    """Tests for RemoteSysVersChecker class."""

    def test_init(self):
        """Test RemoteSysVersChecker initialization."""
        checker = RemoteSysVersChecker()
        assert checker.device is None
        assert hasattr(checker, 'username')
        assert hasattr(checker, 'password')
        assert hasattr(checker, 'port')

    def test_recover_device_list_no_token(self):
        """Test recover_device_list without token."""
        checker = RemoteSysVersChecker()
        devices = checker.recover_device_list()
        assert isinstance(devices, list)


if __name__ == '__main__':
    pytest.main([__file__])
