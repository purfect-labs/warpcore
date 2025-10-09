#!/usr/bin/env python3
"""
WARPCORE Franchise-Agnostic Polymorphic Schema System
Simple, elegant, universal schema management for all franchises
"""

from .universal_schema import (
    UniversalAgentSchema,
    EnvironmentContext,
    FranchiseSchemaManager,
    enhance_agents,
    enhance_all_franchises
)

__all__ = [
    'UniversalAgentSchema',
    'EnvironmentContext',
    'FranchiseSchemaManager',
    'enhance_agents',
    'enhance_all_franchises'
]
