#!/usr/bin/env python3
"""
WARPCORE Template Manager - Web Layer
Manages Jinja2 templates following Provider-Abstraction-Pattern
Feature gates from Data layer - same config as API layer
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from ..data.feature_gates import feature_gate_manager


class WARPCORETemplateManager:
    """Template manager for WARPCORE Web layer - PAP compliant"""
    
    def __init__(self, template_dir: Optional[Path] = None):
        # Default to web/templates directory
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
            
        self.template_dir = template_dir
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add global functions
        self.env.globals['has_feature'] = self._has_feature
    
    def _has_feature(self, feature_name: str) -> bool:
        """Check if a feature is available - Jinja2 global function"""
        return feature_gate_manager.has_feature(feature_name)
    
    def get_template_context(self, license_status=None) -> Dict[str, Any]:
        """Get template context with shared Data layer feature gates"""
        # Update feature gates with license status (same as API layer)
        if license_status:
            feature_gate_manager.update_license_status_sync(license_status)
        
        # Get feature context from shared Data layer
        feature_context = feature_gate_manager.generate_feature_context()
        
        # Add Web layer specific context
        context = {
            "app_name": "WARPCORE",
            "version": "3.0.0",
            "architecture": "Provider-Abstraction-Pattern",
            "license_status": license_status or {
                "status": "active",
                "type": "production",
                "user_name": "Licensed User"
            },
            "providers": ["gcp", "license"],
            "note": "Production template manager - feature gates from data layer"
        }
        
        # Merge with shared feature context from Data layer
        context.update(feature_context)
        return context
    
    def render_template(self, template_name: str, **context) -> str:
        """Render a template with context"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            return f"<!-- Template error: {template_name} - {str(e)} -->"
    
    def render_component(self, component_path: str, **context) -> str:
        """Render a component template"""
        try:
            template = self.env.get_template(f"components/{component_path}")
            return template.render(**context)
        except Exception as e:
            return f"<!-- Component error: {component_path} - {str(e)} -->"


# Global template manager instance
template_manager = WARPCORETemplateManager()

# Convenience alias for backward compatibility
TemplateManager = WARPCORETemplateManager