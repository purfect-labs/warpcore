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
        """Get template context with complete license data integration"""
        # Update feature gates with license status (same as API layer)
        if license_status:
            feature_gate_manager.update_license_status_sync(license_status)
        
        # Get feature context from shared Data layer
        feature_context = feature_gate_manager.generate_feature_context()
        
        # Generate current tier info from license status
        current_tier_info = self._generate_current_tier_info(license_status)
        
        # Generate upgrade options from FeatureGateManager tier definitions
        upgrade_options = self._generate_upgrade_options(license_status)
        
        # Add Web layer specific context
        context = {
            "app_name": "WARPCORE",
            "version": "3.0.0",
            "architecture": "Provider-Abstraction-Pattern",
            "license_status": license_status or {
                "status": "inactive",
                "license_type": "free",
                "user_email": None,
                "expires_at": None,
                "features": []
            },
            "current_tier_info": current_tier_info,
            "upgrade_options": upgrade_options,
            "providers": ["gcp", "license"],
            "note": "Production template manager with real license data integration"
        }
        
        # Merge with shared feature context from Data layer
        context.update(feature_context)
        return context
    
    def _generate_current_tier_info(self, license_status: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate current tier information from license status"""
        if not license_status or license_status.get('status') != 'active':
            # Update feature gate manager first to get correct basic features
            feature_gate_manager.update_license_status_sync(None)
            return {
                'name': 'Free',
                'tier': 'free',
                'feature_count': len(feature_gate_manager.get_available_features()),
                'icon': '🆓',
                'description': 'Basic features only'
            }
        
        license_type = license_status.get('license_type', 'free')
        # Feature gate manager is already updated with license status in get_template_context
        available_features = feature_gate_manager.get_available_features()
        
        tier_info = {
            'free': {'name': 'Free', 'icon': '🆓', 'description': 'Basic features'},
            'trial': {'name': 'Trial', 'icon': '🎁', 'description': 'Professional features for trial period'},
            'professional': {'name': 'Professional', 'icon': '⚡', 'description': 'Full professional features'},
            'enterprise': {'name': 'Enterprise', 'icon': '🏢', 'description': 'Enterprise-grade features'}
        }.get(license_type, {'name': 'Unknown', 'icon': '❓', 'description': 'Unknown tier'})
        
        tier_info.update({
            'tier': license_type,
            'feature_count': len(available_features),
            'features': available_features
        })
        
        return tier_info
    
    def _generate_upgrade_options(self, license_status: Optional[Dict[str, Any]]) -> list:
        """Generate upgrade options from FeatureGateManager tier definitions"""
        current_tier = 'free'
        if license_status and license_status.get('status') == 'active':
            current_tier = license_status.get('license_type', 'free')
        
        # Define tier hierarchy and pricing
        tier_hierarchy = ['free', 'trial', 'professional', 'enterprise']
        current_index = tier_hierarchy.index(current_tier) if current_tier in tier_hierarchy else 0
        
        upgrade_options = []
        tier_configs = {
            'trial': {
                'name': 'Professional Trial',
                'icon': '🎁',
                'price': 'Free for 14 days',
                'features': self._get_tier_features('trial')
            },
            'professional': {
                'name': 'Professional',
                'icon': '⚡',
                'price': '$99/month',
                'features': self._get_tier_features('professional')
            },
            'enterprise': {
                'name': 'Enterprise',
                'icon': '🏢',
                'price': 'Contact Sales',
                'features': self._get_tier_features('enterprise')
            }
        }
        
        # Only show upgrade options for higher tiers
        for i, tier in enumerate(tier_hierarchy):
            if i > current_index and tier in tier_configs:
                config = tier_configs[tier]
                upgrade_options.append({
                    'tier': tier,
                    'name': config['name'],
                    'icon': config['icon'],
                    'price': config['price'],
                    'features': config['features'],
                    'feature_count': len(config['features'])
                })
        
        return upgrade_options
    
    def _get_tier_features(self, tier: str) -> list:
        """Get features for a specific tier without changing current state"""
        # Map tier names to feature gate manager tiers
        tier_mapping = {
            'free': ['core_k8s', 'basic_terminal', 'system_status'],
            'trial': ['core_k8s', 'basic_terminal', 'system_status', 'kiali_connect', 'aws_sso', 'gcp_auth', 'live_logs'],
            'professional': ['core_k8s', 'basic_terminal', 'system_status', 'kiali_connect', 'aws_sso', 'gcp_auth', 'live_logs', 
                           'kiali_dashboard', 'rds_connect', 'ci_cd_ops', 'advanced_monitoring'],
            'enterprise': ['all']  # All features
        }
        
        if tier == 'enterprise':
            # Return all available feature names
            from ..data.feature_gates import FEATURE_DEFINITIONS
            return list(FEATURE_DEFINITIONS.keys())
        
        return tier_mapping.get(tier, tier_mapping['free'])
    
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