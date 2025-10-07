"""
Payment Provider for Production License Purchase System

This provider handles Stripe payment processing for license purchases
following PAP (Provider-Architect-Pattern) compliance.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from ..core.base_provider import BaseProvider

# Import Stripe SDK when available
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False


class PaymentProvider(BaseProvider):
    """Payment provider for Stripe integration and license purchase processing"""
    
    def __init__(self):
        super().__init__("payment")
        self.stripe_api_key = None
        self.stripe_webhook_secret = None
        self._initialize_stripe_config()
    
    def _initialize_stripe_config(self):
        """Initialize Stripe configuration from environment variables"""
        try:
            self.stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
            self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
            
            if STRIPE_AVAILABLE and self.stripe_api_key:
                stripe.api_key = self.stripe_api_key
                self.config["stripe_configured"] = True
            else:
                self.config["stripe_configured"] = False
                
        except Exception as e:
            self.config["stripe_configured"] = False
            self._last_error = {"error": f"Stripe configuration failed: {str(e)}"}
    
    async def authenticate(self, **kwargs) -> Dict[str, Any]:
        """Authenticate with Stripe API"""
        try:
            if not STRIPE_AVAILABLE:
                return {
                    "success": False,
                    "error": "Stripe SDK not installed",
                    "authenticated": False
                }
            
            if not self.stripe_api_key:
                return {
                    "success": False,
                    "error": "Stripe API key not configured",
                    "authenticated": False
                }
            
            # Test Stripe connection
            try:
                stripe.Account.retrieve()
                return {
                    "success": True,
                    "authenticated": True,
                    "provider": "stripe",
                    "timestamp": datetime.now().isoformat()
                }
            except stripe.error.AuthenticationError as e:
                return {
                    "success": False,
                    "error": f"Stripe authentication failed: {str(e)}",
                    "authenticated": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Authentication error: {str(e)}",
                "authenticated": False
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get payment provider status"""
        return {
            "provider": "payment",
            "stripe_sdk_available": STRIPE_AVAILABLE,
            "stripe_configured": self.config.get("stripe_configured", False),
            "api_key_present": bool(self.stripe_api_key),
            "webhook_secret_present": bool(self.stripe_webhook_secret),
            "health_status": self._health_status,
            "error_count": self._error_count,
            "last_error": self._last_error
        }
    
    async def create_payment_intent(self, 
                                  amount: int, 
                                  currency: str, 
                                  tier: str,
                                  user_email: str,
                                  metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a Stripe payment intent for license purchase"""
        
        async def _create_intent():
            if not STRIPE_AVAILABLE:
                raise Exception("Stripe SDK not available")
                
            if not self.config.get("stripe_configured", False):
                raise Exception("Stripe not properly configured")
            
            payment_metadata = {
                "license_tier": tier,
                "user_email": user_email,
                "purchase_type": "license",
                "created_at": datetime.now().isoformat()
            }
            
            if metadata:
                payment_metadata.update(metadata)
            
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=payment_metadata,
                receipt_email=user_email,
                description=f"WarpCore {tier.title()} License"
            )
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "tier": tier,
                "user_email": user_email,
                "created": datetime.now().isoformat()
            }
        
        # Execute with resilience features
        return await self.execute_with_resilience(
            _create_intent,
            fallback_result={
                "success": False,
                "error": "Payment system temporarily unavailable",
                "status": "system_error"
            }
        )
    
    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm and validate payment completion"""
        
        async def _confirm_payment():
            if not STRIPE_AVAILABLE:
                raise Exception("Stripe SDK not available")
                
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "payment_method": intent.payment_method,
                "metadata": intent.metadata,
                "confirmed": intent.status == "succeeded",
                "timestamp": datetime.now().isoformat()
            }
        
        return await self.execute_with_resilience(
            _confirm_payment,
            fallback_result={
                "success": False,
                "error": "Payment confirmation temporarily unavailable",
                "confirmed": False
            }
        )
    
    async def process_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """Process Stripe webhook events"""
        
        async def _process_webhook():
            if not STRIPE_AVAILABLE:
                raise Exception("Stripe SDK not available")
                
            if not self.stripe_webhook_secret:
                raise Exception("Stripe webhook secret not configured")
            
            try:
                event = stripe.Webhook.construct_event(
                    payload, 
                    signature, 
                    self.stripe_webhook_secret
                )
            except ValueError as e:
                raise Exception(f"Invalid payload: {str(e)}")
            except stripe.error.SignatureVerificationError as e:
                raise Exception(f"Invalid signature: {str(e)}")
            
            # Handle specific event types
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                return {
                    "success": True,
                    "event_type": "payment_succeeded",
                    "payment_intent_id": payment_intent['id'],
                    "metadata": payment_intent.get('metadata', {}),
                    "amount": payment_intent['amount'],
                    "currency": payment_intent['currency'],
                    "processed": True
                }
            
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                return {
                    "success": True,
                    "event_type": "payment_failed",
                    "payment_intent_id": payment_intent['id'],
                    "failure_reason": payment_intent.get('last_payment_error', {}).get('message', 'Unknown'),
                    "metadata": payment_intent.get('metadata', {}),
                    "processed": True
                }
            
            else:
                return {
                    "success": True,
                    "event_type": event['type'],
                    "processed": False,
                    "message": f"Event type {event['type']} not handled"
                }
        
        return await self.execute_with_resilience(
            _process_webhook,
            fallback_result={
                "success": False,
                "error": "Webhook processing temporarily unavailable",
                "processed": False
            }
        )
    
    async def get_payment_history(self, user_email: str, limit: int = 10) -> Dict[str, Any]:
        """Retrieve payment history for a user"""
        
        async def _get_history():
            if not STRIPE_AVAILABLE:
                raise Exception("Stripe SDK not available")
            
            # Search for payment intents by user email
            intents = stripe.PaymentIntent.list(
                limit=limit,
                expand=['data.charges']
            )
            
            user_payments = []
            for intent in intents.data:
                if intent.metadata and intent.metadata.get('user_email') == user_email:
                    user_payments.append({
                        "payment_intent_id": intent.id,
                        "amount": intent.amount,
                        "currency": intent.currency,
                        "status": intent.status,
                        "tier": intent.metadata.get('license_tier', 'unknown'),
                        "created": datetime.fromtimestamp(intent.created).isoformat(),
                        "description": intent.description
                    })
            
            return {
                "success": True,
                "user_email": user_email,
                "payment_count": len(user_payments),
                "payments": user_payments,
                "retrieved": datetime.now().isoformat()
            }
        
        return await self.execute_with_resilience(
            _get_history,
            fallback_result={
                "success": False,
                "error": "Payment history temporarily unavailable",
                "payments": []
            }
        )
    
    def get_env_vars(self) -> Dict[str, str]:
        """Get payment provider environment variables"""
        return {
            "STRIPE_SECRET_KEY": self.stripe_api_key or "",
            "STRIPE_WEBHOOK_SECRET": self.stripe_webhook_secret or ""
        }


# Factory function for provider registry
async def create_payment_provider() -> PaymentProvider:
    """Create and initialize payment provider"""
    provider = PaymentProvider()
    await provider.authenticate()
    return provider