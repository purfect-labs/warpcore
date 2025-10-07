#!/usr/bin/env python3
"""
WARPCORE License Routes Module
HTTP endpoints for license management following PAP pattern
Routes → Controllers → Orchestrators → Providers
"""

from .license_routes import setup_license_routes


def setup_all_license_routes(app, controller_registry):
    """Setup all license-related routes"""
    setup_license_routes(app, controller_registry)
    print("📋 WARP LICENSE: Routes organized by capability")
    print("   - Status: /api/license/status")
    print("   - Activation: /api/license/activate")
    print("   - Management: /api/license/*")


__all__ = [
    'setup_all_license_routes',
    'setup_license_routes'
]