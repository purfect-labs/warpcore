#!/usr/bin/env python3
"""
WARPCORE License Server - Self-Contained Remote Licensing System
Runs on separate IP/port for testing and production remote licensing
"""

from .license_server_main import LicenseServerApp

__all__ = ['LicenseServerApp']