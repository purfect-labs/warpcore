# WarpCore API Documentation

## License Management API

WarpCore provides a comprehensive REST API for license management, purchase, and validation.

### Base URL
```
http://localhost:8000/api
```

### Authentication
All license operations require proper authentication. Some endpoints are rate-limited for security.

---

## License Status

### GET /license/status
Get current license information and status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "active",
    "license_type": "premium",
    "user_email": "user@company.com",
    "expires": "2025-12-31T23:59:59Z",
    "days_remaining": 365,
    "features": ["advanced_analytics", "multi_environment", "priority_support"]
  }
}
```

---

## License Purchase

### POST /license/purchase
Initiate a license purchase through Stripe integration.

**Request Body:**
```json
{
  "tier": "premium",
  "user_email": "user@company.com",
  "billing_info": {
    "name": "John Doe",
    "company": "Acme Corp"
  }
}
```

**Response:**
```json
{
  "success": true,
  "purchase_initiated": true,
  "payment_intent_id": "pi_1234567890abcdef",
  "client_secret": "pi_1234567890abcdef_secret_xyz",
  "tier": "premium",
  "amount": 299.00,
  "currency": "usd",
  "user_email": "user@company.com",
  "next_steps": {
    "complete_payment": "Use client_secret to complete payment on frontend",
    "webhook_confirmation": "License will be generated upon successful payment"
  }
}
```

### POST /license/purchase/complete
Complete license purchase after successful payment.

**Request Body:**
```json
{
  "payment_intent_id": "pi_1234567890abcdef"
}
```

**Response:**
```json
{
  "success": true,
  "purchase_completed": true,
  "license_key": "PRD-PREMIUM-ABC123XYZ789",
  "tier": "premium",
  "user_email": "user@company.com",
  "email_sent": true,
  "expires_at": "2025-12-31T23:59:59Z",
  "features": ["advanced_analytics", "multi_environment", "priority_support"]
}
```

### GET /license/purchase/status/{payment_intent_id}
Get purchase status by payment intent ID.

**Response:**
```json
{
  "success": true,
  "payment_intent_id": "pi_1234567890abcdef",
  "payment_status": "succeeded",
  "payment_confirmed": true,
  "amount": 299.00,
  "currency": "usd"
}
```

---

## License Activation

### POST /license/activate
Activate a license key.

**Request Body:**
```json
{
  "license_key": "PRD-PREMIUM-ABC123XYZ789",
  "user_email": "user@company.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "License activated successfully",
  "license_type": "premium",
  "expires_at": "2025-12-31T23:59:59Z",
  "features": ["advanced_analytics", "multi_environment", "priority_support"],
  "hardware_bound": true
}
```

---

## License Validation

### POST /license/validate
Validate a license key without activating it.

**Request Body:**
```json
{
  "license_key": "PRD-PREMIUM-ABC123XYZ789"
}
```

**Response:**
```json
{
  "valid": true,
  "license_type": "premium",
  "features": ["advanced_analytics", "multi_environment", "priority_support"],
  "expires_at": "2025-12-31T23:59:59Z",
  "hardware_binding_required": true
}
```

---

## Trial Licenses

### POST /license/generate-trial
Generate a trial license (7-day default).

**Request Body:**
```json
{
  "user_email": "user@company.com",
  "days": 7
}
```

**Response:**
```json
{
  "success": true,
  "license_key": "TRL-STANDARD-DEF456GHI012",
  "license_type": "trial",
  "expires_at": "2025-01-14T23:59:59Z",
  "days": 7,
  "features": ["basic_cloud", "monitoring", "standard_support"]
}
```

---

## License Deactivation

### POST /license/deactivate
Deactivate current license.

**Response:**
```json
{
  "success": true,
  "message": "License deactivated successfully",
  "previous_status": "active"
}
```

---

## Subscription Information

### GET /license/subscription
Get subscription and feature information.

**Response:**
```json
{
  "success": true,
  "data": {
    "subscription_type": "Premium License",
    "features_available": ["advanced_analytics", "multi_environment", "priority_support"],
    "features_active": ["advanced_analytics", "multi_environment", "priority_support"],
    "billing_status": "active",
    "renewal_date": "2025-12-31",
    "support_level": "priority"
  }
}
```

---

## Webhooks

### POST /webhooks/stripe
Stripe webhook endpoint for payment processing.

This endpoint handles Stripe webhook events automatically:
- `payment_intent.succeeded` - Completes license purchase
- `payment_intent.payment_failed` - Handles payment failures
- Other Stripe events are logged but not processed

**Headers Required:**
- `stripe-signature` - Stripe webhook signature for verification

---

## License Tiers & Pricing

| Tier | Price | Features |
|------|-------|----------|
| Basic | $29 | Core functionality, kubectl access, basic cloud operations |
| Standard | $99 | Full cloud integrations, monitoring, support |
| Premium | $299 | Advanced analytics, multi-environment, enterprise features |
| Enterprise | $999 | All features, dedicated support, SLA, custom integrations |

---

## Error Responses

All endpoints return errors in the following format:

```json
{
  "success": false,
  "error": "Error description",
  "error_code": "LICENSE_INVALID",
  "timestamp": "2025-01-07T19:00:00Z"
}
```

### Common Error Codes
- `LICENSE_INVALID` - License key is invalid or expired
- `PAYMENT_REQUIRED` - Payment is required for this feature
- `STRIPE_ERROR` - Payment processing error
- `VALIDATION_ERROR` - Request validation failed
- `RATE_LIMITED` - Too many requests

---

## Integration Examples

### JavaScript Frontend Integration
```javascript
// Purchase license
const purchaseResponse = await fetch('/api/license/purchase', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tier: 'premium',
    user_email: 'user@company.com'
  })
});

const purchase = await purchaseResponse.json();

// Use Stripe client_secret to complete payment
// Then check completion status
const statusResponse = await fetch(`/api/license/purchase/status/${purchase.payment_intent_id}`);
```

### cURL Examples
```bash
# Check license status
curl -X GET http://localhost:8000/api/license/status

# Purchase license
curl -X POST http://localhost:8000/api/license/purchase \
  -H "Content-Type: application/json" \
  -d '{"tier": "premium", "user_email": "user@company.com"}'

# Activate license
curl -X POST http://localhost:8000/api/license/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "PRD-PREMIUM-ABC123", "user_email": "user@company.com"}'
```

This API provides a complete license management system with Stripe integration, hardware binding, and comprehensive feature gating capabilities.