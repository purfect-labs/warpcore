#!/usr/bin/env python3
"""
WARPCORE License Workflow Integration Tests - Production Implementation
Integration tests for complete license workflows across PAP architecture
Tests end-to-end flows with real components working together
"""

import pytest
import asyncio
import json
import tempfile
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import components for integration testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.providers.license.license_provider import LicenseProvider
from api.controllers.license_controller import LicenseController  
from api.orchestrators.license.license_orchestrator import LicenseOrchestrator
from api.middleware.license_security_middleware import LicenseSecurityMiddleware
from api.validators.license_security_validator import LicenseSecurityValidator


class TestLicenseWorkflowIntegration:
    """Integration tests for complete license workflows"""
    
    @pytest.fixture
    async def license_components(self):
        """Set up integrated license components for testing"""
        with patch('data.config.license.license_config.get_license_config') as mock_config:
            # Mock configuration
            config = Mock()
            config.get_audit_file.return_value = "/tmp/integration_test_audit.log"
            config.is_production_mode.return_value = True
            config.get_provider_config.return_value = {
                "fernet_encryption": True,
                "hardware_fingerprinting": True,
                "production_mode": True
            }
            config.get_watermark_config.return_value = {
                "controller": "", "orchestrator": "", "error": ""
            }
            config.should_broadcast_events.return_value = False
            config.get_trial_duration.return_value = 7
            config.get_max_trial_duration.return_value = 30
            config.get_available_features.return_value = ["production", "security", "audit", "core", "api"]
            config.get_security_features.return_value = ["production", "security", "audit"]
            config.get_required_security_features.return_value = ["production", "security"]
            mock_config.return_value = config
            
            # Create components
            provider = LicenseProvider()
            controller = LicenseController()
            orchestrator = LicenseOrchestrator()
            middleware = LicenseSecurityMiddleware()
            validator = LicenseSecurityValidator()
            
            # Wire components together
            mock_registry = Mock()
            mock_registry.get_provider.return_value = provider
            
            orchestrator.set_provider_registry(mock_registry)
            controller.orchestrator = orchestrator
            controller._orchestrator_wired = True
            
            return {
                "provider": provider,
                "controller": controller,
                "orchestrator": orchestrator,
                "middleware": middleware,
                "validator": validator,
                "config": config
            }
    
    @pytest.mark.asyncio
    async def test_complete_secure_license_generation_flow(self, license_components):
        """Test complete secure license generation workflow"""
        components = await license_components
        controller = components["controller"]
        middleware = components["middleware"]
        validator = components["validator"]
        
        # Step 1: Security middleware validation
        request_context = {
            "client_ip": "192.168.1.100",
            "operation": "generate_secure_license",
            "user_email": "integration@production.com",
            "user_name": "Integration Test User"
        }
        
        security_result = await middleware.process_request(request_context)
        assert security_result["success"] == True
        assert security_result["security_validated"] == True
        
        # Step 2: Controller processes secure license generation
        license_result = await controller.generate_secure_license(
            user_email="integration@production.com",
            user_name="Integration Test User",
            days=30,
            features=["production", "security"],
            hardware_binding=True
        )
        
        assert license_result["success"] == True
        assert "license_key" in license_result
        assert license_result["hardware_binding"] == True
        
        # Step 3: Validate the generated license with security validator
        license_key = license_result["license_key"]
        provider = components["provider"]
        
        # First get license data
        validation_result = await provider._validate_license_key(license_key)
        assert validation_result["valid"] == True
        
        license_data = validation_result["license_info"]
        
        # Security validation
        security_validation = await validator.validate_license_security(license_data, license_key)
        assert security_validation["overall_valid"] == True
        assert security_validation["security_level"] in ["production", "staging"]
    
    @pytest.mark.asyncio
    async def test_license_activation_workflow(self, license_components):
        """Test complete license activation workflow"""
        components = await license_components
        controller = components["controller"]
        middleware = components["middleware"]
        
        # Generate a license first
        license_result = await controller.generate_secure_license(
            user_email="activation@test.com",
            user_name="Activation Test",
            days=30,
            features=["production"],
            hardware_binding=True
        )
        
        assert license_result["success"] == True
        license_key = license_result["license_key"]
        
        # Step 1: Security middleware check for activation
        activation_context = {
            "client_ip": "192.168.1.101",
            "operation": "activate_license", 
            "license_key": license_key
        }
        
        security_result = await middleware.process_request(activation_context)
        assert security_result["success"] == True
        
        # Step 2: Controller activation
        activation_result = await controller.activate_license(license_key, "activation@test.com")
        assert activation_result["success"] == True
    
    @pytest.mark.asyncio
    async def test_license_validation_workflow(self, license_components):
        """Test complete license validation workflow"""
        components = await license_components
        controller = components["controller"]
        validator = components["validator"]
        provider = components["provider"]
        
        # Generate a license
        license_result = await controller.generate_secure_license(
            user_email="validation@test.com",
            user_name="Validation Test",
            days=30,
            features=["production", "security", "audit"],
            hardware_binding=True
        )
        
        license_key = license_result["license_key"]
        
        # Validate through controller
        controller_validation = await controller.validate_license_key(license_key)
        assert controller_validation["valid"] == True
        
        # Get detailed license data for security validation
        provider_validation = await provider._validate_license_key(license_key)
        license_data = provider_validation["license_info"]
        
        # Comprehensive security validation
        security_validation = await validator.validate_license_security(license_data, license_key)
        
        assert security_validation["overall_valid"] == True
        assert security_validation["compliance_score"] > 70
        assert "production" in license_data.get("features", [])
    
    @pytest.mark.asyncio
    async def test_security_middleware_rate_limiting_integration(self, license_components):
        """Test security middleware rate limiting in realistic scenario"""
        components = await license_components
        middleware = components["middleware"]
        controller = components["controller"]
        
        client_ip = "192.168.1.200"
        
        # Make multiple requests under the limit
        successful_requests = 0
        for i in range(25):  # Under 30 request limit
            request_context = {
                "client_ip": client_ip,
                "operation": "generate_license",
                "user_email": f"test{i}@ratelimit.com"
            }
            
            security_result = await middleware.process_request(request_context)
            if security_result["success"]:
                successful_requests += 1
        
        assert successful_requests >= 20  # Most should succeed
        
        # Push over the limit
        for i in range(10):
            request_context = {
                "client_ip": client_ip,
                "operation": "generate_license",
                "user_email": f"test{i+30}@ratelimit.com"
            }
            await middleware.process_request(request_context)
        
        # Next request should be rate limited
        request_context = {
            "client_ip": client_ip,
            "operation": "generate_license", 
            "user_email": "final@ratelimit.com"
        }
        
        security_result = await middleware.process_request(request_context)
        assert security_result["success"] == False
        assert "rate limit" in security_result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_hardware_binding_across_components(self, license_components):
        """Test hardware binding functionality across all components"""
        components = await license_components
        provider = components["provider"]
        validator = components["validator"]
        
        # Generate license with hardware binding
        license_result = await provider.generate_secure_license(
            user_email="hardware@binding.com",
            user_name="Hardware Test",
            days=30,
            features=["production"],
            hardware_binding=True
        )
        
        assert license_result["success"] == True
        assert license_result["hardware_binding"] == True
        
        # Validate the license
        license_key = license_result["license_key"]
        validation_result = await provider._validate_license_key(license_key)
        assert validation_result["valid"] == True
        
        license_data = validation_result["license_info"]
        assert "hardware_signature" in license_data
        
        # Security validation should pass hardware binding checks
        security_validation = await validator.validate_license_security(license_data, license_key)
        hardware_validation = security_validation["validations"]["hardware_binding"]
        assert hardware_validation["signature_present"] == True
        assert hardware_validation["binding_strength"] > 0
    
    @pytest.mark.asyncio 
    async def test_tamper_detection_integration(self, license_components):
        """Test tamper detection across components"""
        components = await license_components
        provider = components["provider"]
        validator = components["validator"]
        
        # Generate secure license
        license_result = await provider.generate_secure_license(
            user_email="tamper@detection.com",
            user_name="Tamper Test",
            days=30,
            features=["production", "security"],
            hardware_binding=True
        )
        
        license_key = license_result["license_key"]
        
        # Get license data
        validation_result = await provider._validate_license_key(license_key)
        license_data = validation_result["license_info"]
        
        # Should pass tamper detection
        tamper_result = provider._detect_tampering(license_data)
        assert tamper_result.get("tampered", False) == False
        
        # Security validator should also detect no tampering
        security_validation = await validator.validate_license_security(license_data, license_key)
        tamper_validation = security_validation["validations"]["tampering"]
        assert tamper_validation["valid"] == True
        assert tamper_validation["tamper_score"] > 0
    
    @pytest.mark.asyncio
    async def test_compliance_validation_integration(self, license_components):
        """Test compliance validation across security standards"""
        components = await license_components
        provider = components["provider"]
        validator = components["validator"]
        
        # Generate production-compliant license
        license_result = await provider.generate_secure_license(
            user_email="compliance@production.com",
            user_name="Compliance Test",
            days=90,  # Within limits
            features=["production", "security", "audit"],  # Compliant features
            hardware_binding=True
        )
        
        license_key = license_result["license_key"]
        validation_result = await provider._validate_license_key(license_key)
        license_data = validation_result["license_info"]
        
        # Security validation should show high compliance
        security_validation = await validator.validate_license_security(license_data, license_key)
        
        assert security_validation["compliance_score"] >= 80
        compliance_checks = security_validation["validations"]["compliance"]["checks"]
        assert compliance_checks.get("security_features", False) == True
        assert compliance_checks.get("license_type_compliance", False) == True
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, license_components):
        """Test error handling across integrated components"""
        components = await license_components
        middleware = components["middleware"]
        controller = components["controller"]
        
        # Test invalid email handling
        invalid_context = {
            "client_ip": "192.168.1.300",
            "operation": "generate_license",
            "user_email": "invalid-email-format"  # No @ symbol
        }
        
        security_result = await middleware.process_request(invalid_context)
        assert security_result["success"] == False
        assert "security" in security_result["error"]
        
        # Test missing required fields
        incomplete_context = {
            "client_ip": "192.168.1.301", 
            "operation": "generate_license"
            # Missing user_email
        }
        
        security_result = await middleware.process_request(incomplete_context)
        assert security_result["success"] == False
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, license_components):
        """Test system performance under realistic load"""
        components = await license_components
        controller = components["controller"]
        
        start_time = time.time()
        
        # Generate multiple licenses concurrently
        tasks = []
        for i in range(10):  # Moderate load test
            task = controller.generate_secure_license(
                user_email=f"perf{i}@load.test",
                user_name=f"Performance Test {i}",
                days=30,
                features=["production"],
                hardware_binding=True
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify all succeeded
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful_results) == 10
        
        # Performance check - should complete within reasonable time
        assert duration < 30  # 30 seconds for 10 concurrent operations
        
        # Verify all licenses are unique
        license_keys = [r["license_key"] for r in successful_results]
        assert len(set(license_keys)) == 10  # All unique


class TestLicenseSystemResilience:
    """Test system resilience and error recovery"""
    
    @pytest.fixture
    async def resilient_components(self):
        """Set up components for resilience testing"""
        with patch('data.config.license.license_config.get_license_config') as mock_config:
            config = Mock()
            config.get_audit_file.return_value = "/tmp/resilience_test_audit.log"
            config.is_production_mode.return_value = True
            config.get_provider_config.return_value = {"fernet_encryption": True}
            mock_config.return_value = config
            
            provider = LicenseProvider()
            middleware = LicenseSecurityMiddleware()
            
            return {"provider": provider, "middleware": middleware}
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, resilient_components):
        """Test graceful degradation when components fail"""
        components = await resilient_components
        middleware = components["middleware"]
        
        # Test with filesystem issues (audit log)
        with patch('builtins.open', side_effect=PermissionError):
            # Should still process request despite logging failure
            request_context = {
                "client_ip": "192.168.1.400",
                "operation": "validate_license",
                "license_key": "test_key_for_degradation_test"
            }
            
            result = await middleware.process_request(request_context)
            # Should not fail completely due to logging issues
            assert "success" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, resilient_components):
        """Test handling of concurrent requests"""
        components = await resilient_components
        middleware = components["middleware"]
        
        # Create many concurrent requests from different IPs
        tasks = []
        for i in range(50):
            request_context = {
                "client_ip": f"192.168.1.{i+100}",
                "operation": "validate_license",
                "license_key": f"test_key_{i}"
            }
            task = middleware.process_request(request_context)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most should succeed (some may be rate limited)
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful_results) >= 40  # At least 80% success rate


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-k", "integration"])