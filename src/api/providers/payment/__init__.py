"""
Payment Provider Module

Handles production license purchases through Stripe integration
following PAP (Provider-Architect-Pattern) compliance.
"""

from .payment_provider import PaymentProvider, create_payment_provider

__all__ = ["PaymentProvider", "create_payment_provider"]