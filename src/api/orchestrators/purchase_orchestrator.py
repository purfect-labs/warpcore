"""
Purchase Orchestrator for Production License Purchase Flow

Orchestrates the complete license purchase workflow following PAP architecture:
- Payment processing through Stripe provider
- License generation through license provider  
- Email delivery through notification system
- Purchase history tracking
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .core.base_orchestrator import BaseOrchestrator


class PurchaseOrchestrator(BaseOrchestrator):
    """Orchestrates the complete license purchase workflow with PAP compliance"""
    
    def __init__(self, provider_registry, notification_system=None):
        super().__init__("purchase")
        self.provider_registry = provider_registry
        self.notification_system = notification_system
        
    async def initiate_license_purchase(self, 
                                       tier: str, 
                                       user_email: str, 
                                       billing_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Initiate license purchase workflow
        
        Steps:
        1. Validate purchase request
        2. Calculate pricing
        3. Create payment intent via Stripe provider
        4. Return client secret for payment completion
        """
        try:
            # Validate purchase request
            validation = await self._validate_purchase_request(tier, user_email)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"],
                    "step": "validation"
                }
            
            # Calculate pricing for tier
            pricing = await self._calculate_tier_pricing(tier)
            if not pricing["success"]:
                return {
                    "success": False,
                    "error": f"Pricing calculation failed: {pricing['error']}",
                    "step": "pricing"
                }
            
            # Get payment provider
            payment_provider = await self.provider_registry.get_payment_provider()
            if not payment_provider:
                return {
                    "success": False,
                    "error": "Payment system temporarily unavailable",
                    "step": "payment_provider"
                }
            
            # Create payment intent
            payment_result = await payment_provider.create_payment_intent(
                amount=pricing["amount_cents"],
                currency=pricing["currency"],
                tier=tier,
                user_email=user_email,
                metadata={
                    "purchase_id": str(uuid.uuid4()),
                    "initiated_at": datetime.now().isoformat()
                }
            )
            
            if not payment_result["success"]:
                return {
                    "success": False,
                    "error": f"Payment initialization failed: {payment_result.get('error', 'Unknown error')}",
                    "step": "payment_intent"
                }
            
            return {
                "success": True,
                "purchase_initiated": True,
                "payment_intent_id": payment_result["payment_intent_id"],
                "client_secret": payment_result["client_secret"],
                "tier": tier,
                "amount": pricing["amount_dollars"],
                "currency": pricing["currency"],
                "user_email": user_email,
                "next_steps": {
                    "complete_payment": "Use client_secret to complete payment on frontend",
                    "webhook_confirmation": "License will be generated upon successful payment"
                },
                "initiated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Purchase initiation failed: {str(e)}",
                "step": "orchestration_error"
            }
    
    async def complete_license_purchase(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Complete license purchase after successful payment
        
        Steps:
        1. Confirm payment with Stripe
        2. Generate license key
        3. Send license via email
        4. Record purchase history
        """
        try:
            # Get payment provider
            payment_provider = await self.provider_registry.get_payment_provider()
            if not payment_provider:
                return {
                    "success": False,
                    "error": "Payment system unavailable for confirmation",
                    "step": "payment_provider"
                }
            
            # Confirm payment
            payment_confirmation = await payment_provider.confirm_payment(payment_intent_id)
            if not payment_confirmation["success"] or not payment_confirmation["confirmed"]:
                return {
                    "success": False,
                    "error": f"Payment not confirmed: {payment_confirmation.get('error', 'Payment failed')}",
                    "step": "payment_confirmation"
                }
            
            # Extract payment metadata
            metadata = payment_confirmation.get("metadata", {})
            tier = metadata.get("license_tier", "standard")
            user_email = metadata.get("user_email")
            
            if not user_email:
                return {
                    "success": False,
                    "error": "User email not found in payment metadata",
                    "step": "metadata_extraction"
                }
            
            # Generate license key
            license_result = await self._generate_license_key(tier, user_email, payment_intent_id)
            if not license_result["success"]:
                return {
                    "success": False,
                    "error": f"License generation failed: {license_result['error']}",
                    "step": "license_generation"
                }
            
            # Send license via email
            email_result = await self._send_license_email(
                user_email, 
                license_result["license_key"], 
                tier,
                payment_confirmation["amount"] / 100,  # Convert cents to dollars
                payment_confirmation["currency"]
            )
            
            # Record purchase in history (don't fail if this fails)
            await self._record_purchase_history(payment_intent_id, license_result, payment_confirmation)
            
            return {
                "success": True,
                "purchase_completed": True,
                "license_key": license_result["license_key"],
                "tier": tier,
                "user_email": user_email,
                "payment_intent_id": payment_intent_id,
                "email_sent": email_result["success"],
                "email_details": email_result.get("details", "Email sending failed"),
                "expires_at": license_result["expires_at"],
                "features": license_result["features"],
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Purchase completion failed: {str(e)}",
                "step": "orchestration_error"
            }
    
    async def _validate_purchase_request(self, tier: str, user_email: str) -> Dict[str, Any]:
        """Validate purchase request parameters"""
        valid_tiers = ["basic", "standard", "premium", "enterprise"]
        
        if tier not in valid_tiers:
            return {
                "valid": False,
                "error": f"Invalid tier '{tier}'. Valid tiers: {', '.join(valid_tiers)}"
            }
        
        if not user_email or "@" not in user_email:
            return {
                "valid": False,
                "error": "Valid email address is required"
            }
        
        return {"valid": True}
    
    async def _calculate_tier_pricing(self, tier: str) -> Dict[str, Any]:
        """Calculate pricing for license tier"""
        try:
            # Production pricing configuration
            tier_pricing = {
                "basic": {"dollars": 29.00, "features": ["core", "api", "basic_support"]},
                "standard": {"dollars": 99.00, "features": ["core", "api", "web", "monitoring", "support"]},
                "premium": {"dollars": 299.00, "features": ["core", "api", "web", "monitoring", "analytics", "priority_support"]},
                "enterprise": {"dollars": 999.00, "features": ["all_features", "dedicated_support", "sla", "custom_integrations"]}
            }
            
            if tier not in tier_pricing:
                return {
                    "success": False,
                    "error": f"Pricing not configured for tier: {tier}"
                }
            
            pricing_info = tier_pricing[tier]
            
            return {
                "success": True,
                "tier": tier,
                "amount_dollars": pricing_info["dollars"],
                "amount_cents": int(pricing_info["dollars"] * 100),
                "currency": "usd",
                "features": pricing_info["features"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Pricing calculation error: {str(e)}"
            }
    
    async def _generate_license_key(self, tier: str, user_email: str, payment_reference: str) -> Dict[str, Any]:
        """Generate license key through license provider"""
        try:
            license_provider = await self.provider_registry.get_license_provider()
            if not license_provider:
                return {
                    "success": False,
                    "error": "License provider not available"
                }
            
            # Calculate expiration (1 year from now)
            expires_at = (datetime.now() + timedelta(days=365)).isoformat()
            
            # Generate license through provider
            license_result = await license_provider.generate_license(
                tier=tier,
                user_email=user_email,
                expires_at=expires_at,
                payment_reference=payment_reference,
                hardware_binding=True
            )
            
            return license_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"License generation error: {str(e)}"
            }
    
    async def _send_license_email(self, user_email: str, license_key: str, tier: str, amount: float, currency: str) -> Dict[str, Any]:
        """Send license key via email"""
        try:
            if not self.notification_system:
                return {
                    "success": False,
                    "details": "Email system not configured"
                }
            
            email_content = {
                "to": user_email,
                "subject": f"Your WarpCore {tier.title()} License Key",
                "template": "license_purchase_success",
                "variables": {
                    "license_key": license_key,
                    "tier": tier.title(),
                    "amount": f"${amount:.2f}",
                    "currency": currency.upper(),
                    "expires_at": (datetime.now() + timedelta(days=365)).strftime("%B %d, %Y"),
                    "activation_instructions": "Use the license key in your WarpCore application to activate your features."
                }
            }
            
            email_result = await self.notification_system.send_email(email_content)
            return email_result
            
        except Exception as e:
            return {
                "success": False,
                "details": f"Email sending failed: {str(e)}"
            }
    
    async def _record_purchase_history(self, payment_intent_id: str, license_result: Dict[str, Any], payment_confirmation: Dict[str, Any]) -> Dict[str, Any]:
        """Record purchase in history database"""
        try:
            # This would integrate with your database provider
            # For now, log the purchase details
            purchase_record = {
                "payment_intent_id": payment_intent_id,
                "license_key": license_result.get("license_key"),
                "tier": license_result.get("tier"),
                "user_email": payment_confirmation.get("metadata", {}).get("user_email"),
                "amount": payment_confirmation.get("amount"),
                "currency": payment_confirmation.get("currency"),
                "payment_status": payment_confirmation.get("status"),
                "license_expires_at": license_result.get("expires_at"),
                "purchased_at": datetime.now().isoformat()
            }
            
            # Log purchase (in production, save to database)
            print(f"Purchase recorded: {json.dumps(purchase_record, indent=2)}")
            
            return {"success": True, "recorded": True}
            
        except Exception as e:
            print(f"Failed to record purchase history: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_purchase_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """Get status of a purchase by payment intent ID"""
        try:
            payment_provider = await self.provider_registry.get_payment_provider()
            if not payment_provider:
                return {
                    "success": False,
                    "error": "Payment system unavailable"
                }
            
            payment_status = await payment_provider.confirm_payment(payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": payment_intent_id,
                "payment_status": payment_status.get("status", "unknown"),
                "payment_confirmed": payment_status.get("confirmed", False),
                "amount": payment_status.get("amount", 0) / 100 if payment_status.get("amount") else 0,
                "currency": payment_status.get("currency", "usd"),
                "metadata": payment_status.get("metadata", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Status check failed: {str(e)}"
            }


# Factory function for orchestrator registry
async def create_purchase_orchestrator(provider_registry, notification_system=None) -> PurchaseOrchestrator:
    """Create and initialize purchase orchestrator"""
    return PurchaseOrchestrator(provider_registry, notification_system)