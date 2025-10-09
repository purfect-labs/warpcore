#!/usr/bin/env python3
"""
WARPCORE Agency Template System
Static config-driven template system that bypasses command constraints
"""

from .template_engine import TemplateEngine
from .static_executor import StaticExecutor
from .config_manager import StaticConfigManager

__all__ = [
    'TemplateEngine',
    'StaticExecutor', 
    'StaticConfigManager'
]