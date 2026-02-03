# B2B Payment & Subscription Setup Guide

## Overview

This guide covers the implementation of B2B subscription management for MercuraClone using **Paddle** as the Merchant of Record. Paddle handles all payment processing, tax compliance (VAT/Sales Tax), and international trade requirements automatically.

## Why Paddle?

- **Merchant of Record**: Paddle handles all tax compliance (VAT, Sales Tax) automatically
- **International Trade**: Excellent support for US/EU transactions
- **No Stripe Dependency**: World-class alternative to Stripe
- **B2B Focused**: Built for subscription-based SaaS businesses
- **Automatic Tax Handling**: Critical for selling to European businesses

## Architecture

### Backend Components

1. **Models** (`app/models_billing.py`)
   - `SubscriptionPlan`: Defines pricing tiers
   - `Subscription`: User subscription records
   - `Invoice`: Billing history
   - `PaymentMethod`: Stored payment methods
   - `SeatAssignment`: Per-seat licensing
   - `UsageRecord`: Usage tracking

2. **Service** (`app/services/paddle_service.py`)
   - Paddle API integration
   - Checkout session creation
   - Subscription management
   - Webhook verification
   - Invoice retrieval

3. **Routes** (`app/routes/billing.py`)
   - `/billing/plans` - List subscription plans
   - `/billing/subscription` - Get/update subscription
   - `/billing/checkout/create-session` - Start checkout
   - `/billing/invoices` - Invoice management
   - `/billing/seats` - Seat assignment
   - `/billing/webhooks/paddle` - Webhook handler

### Frontend Components

1. **AccountBilling Page** (`frontend/src/pages/AccountBilling.tsx`)
   - Overview dashboard
   - Plan selection & upgrade
   - Invoice history
   - Team seat management
   - Usage statistics

2. **API Client** (`frontend/src/services/api.ts`)
   - `billingApi` - All billing endpoints

## Setup Instructions

### 1. Create Paddle Account

1. Sign up at [Paddle](https://vendors.paddle.com/)
2. Complete vendor verification
3. Enable Sandbox mode for testing

### 2. Configure Paddle Products

Create three subscription products in Paddle dashboard:

**Basic Plan**
- Name: "Basic"
- Price: $150/month per seat
- Billing: Monthly recurring
- Max seats: 10

**Professional Plan**
- Name: "Professional"
- Price: $250/month per seat
- Billing: Monthly recurring
- Max seats: 50

**Enterprise Plan**
- Name: "Enterprise"
- Price: $400/month per seat
- Billing: Monthly recurring
- Max seats: Unlimited

### 3. Environment Configuration

Add to your `.env` file:

```bash
# Paddle Configuration
PADDLE_VENDOR_ID=your-vendor-id
PADDLE_VENDOR_AUTH_CODE=your-auth-code
PADDLE_PUBLIC_KEY=your-public-key
PADDLE_WEBHOOK_SECRET=your-webhook-secret
PADDLE_SANDBOX=true  # Set to false for production

# Product IDs from Paddle dashboard
PADDLE_PLAN_BASIC_MONTHLY=prod_basic_123
PADDLE_PLAN_PRO_MONTHLY=prod_pro_456
PADDLE_PLAN_ENTERPRISE_MONTHLY=prod_ent_789
```

### 4. Database Setup

Run the SQL schema to create billing tables:

```sql
-- Run the BILLING_SCHEMA from app/models_billing.py
-- This creates:
-- - subscription_plans
-- - subscriptions
-- - invoices
-- - payment_methods
-- - billing_addresses
-- - seat_assignments
-- - usage_records
```

### 5. Configure Webhooks

In Paddle dashboard, set up webhook URL:

```
https://yourdomain.com/billing/webhooks/paddle
```

Enable these events:
- `subscription_created`
- `subscription_updated`
- `subscription_cancelled`
- `subscription_payment_succeeded`
- `subscription_payment_failed`

## Usage Flow

### Customer Subscription Flow

1. **Browse Plans**
   - Customer visits `/account/billing`
   - Views available plans and pricing

2. **Select Plan**
   - Clicks "Select Plan" button
   - Frontend calls `billingApi.createCheckoutSession()`

3. **Paddle Checkout**
   - Redirects to Paddle hosted checkout
   - Customer enters payment details
   - Paddle handles tax calculation

4. **Webhook Processing**
   - Paddle sends `subscription_created` webhook
   - Backend creates subscription record
   - Customer redirected to success page

5. **Active Subscription**
   - Customer can manage seats
   - View invoices
   - Update payment method
   - Cancel subscription

### Seat Management

```typescript
// Add a seat
await billingApi.updateSubscription({ seats: 5 });

// Assign seat to sales rep
await billingApi.assignSeat('rep@company.com', 'John Doe');

// Deactivate seat
await billingApi.deactivateSeat(seatId);
```

### Invoice Access

```typescript
// List all invoices
const invoices = await billingApi.getInvoices();

// Get specific invoice
const invoice = await billingApi.getInvoice(invoiceId);
```

## Pricing Model

### Per-Seat Pricing

- **Basic**: $150/month per sales rep
- **Professional**: $250/month per sales rep
- **Enterprise**: $400/month per sales rep

### Example Calculations

**Scenario 1**: 3 sales reps on Professional plan
- Cost: 3 × $250 = **$750/month**

**Scenario 2**: 10 sales reps on Basic plan
- Cost: 10 × $150 = **$1,500/month**

**Scenario 3**: 25 sales reps on Enterprise plan
- Cost: 25 × $400 = **$10,000/month**

## Tax Compliance

Paddle automatically handles:

- **US Sales Tax**: State-by-state compliance
- **EU VAT**: Reverse charge mechanism for B2B
- **VAT MOSS**: EU VAT reporting
- **Tax Invoices**: Compliant invoices with tax breakdown

### EU B2B Transactions

For EU business customers (like Sanitär-Heinze):

1. Customer provides VAT number during checkout
2. Paddle validates VAT number via VIES
3. Reverse charge applied (0% VAT)
4. Invoice shows "Reverse Charge" notation
5. Customer handles VAT in their country

## Alternative Payment Providers

If you prefer alternatives to Paddle:

### Adyen
- **Pros**: Enterprise-grade, global coverage
- **Cons**: More complex setup, higher minimums
- **Best for**: Large enterprises

### PayPal Braintree
- **Pros**: Easy setup, familiar brand
- **Cons**: Manual tax compliance
- **Best for**: US-focused businesses

### Chargebee
- **Pros**: Subscription management focus
- **Cons**: Requires separate payment gateway
- **Best for**: Complex billing scenarios

## Testing

### Sandbox Testing

1. Use Paddle Sandbox mode
2. Test card: `4242 4242 4242 4242`
3. Test webhooks with Paddle webhook tester

### Test Scenarios

```bash
# Test subscription creation
curl -X POST http://localhost:8000/billing/checkout/create-session \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "prod_basic_123",
    "seats": 2,
    "billing_interval": "monthly",
    "success_url": "http://localhost:3000/success",
    "cancel_url": "http://localhost:3000/cancel"
  }'

# Test webhook
curl -X POST http://localhost:8000/billing/webhooks/paddle \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "alert_name=subscription_created&subscription_id=123"
```

## Production Deployment

### Pre-Launch Checklist

- [ ] Paddle account verified
- [ ] Production products created
- [ ] Webhook URL configured
- [ ] SSL certificate installed
- [ ] Environment variables set
- [ ] Database schema deployed
- [ ] Tax settings reviewed
- [ ] Test transactions completed

### Go-Live Steps

1. Switch `PADDLE_SANDBOX=false`
2. Update product IDs to production
3. Test with real payment method
4. Monitor webhook logs
5. Verify invoice generation

## Monitoring & Analytics

### Key Metrics to Track

- Monthly Recurring Revenue (MRR)
- Customer Lifetime Value (LTV)
- Churn Rate
- Seat Utilization
- Average Revenue Per User (ARPU)

### Dashboard Queries

```sql
-- Current MRR
SELECT SUM(total_amount) as mrr
FROM subscriptions
WHERE status = 'active';

-- Seat utilization
SELECT 
  s.seats as total_seats,
  COUNT(sa.id) as assigned_seats,
  (COUNT(sa.id)::float / s.seats * 100) as utilization_pct
FROM subscriptions s
LEFT JOIN seat_assignments sa ON s.id = sa.subscription_id AND sa.is_active = true
WHERE s.status = 'active'
GROUP BY s.id;
```

## Support & Resources

- **Paddle Documentation**: https://developer.paddle.com/
- **Paddle Support**: support@paddle.com
- **Tax Compliance Guide**: https://paddle.com/resources/tax-compliance
- **API Reference**: https://developer.paddle.com/api-reference

## Troubleshooting

### Common Issues

**Issue**: Webhook signature verification fails
- **Solution**: Check `PADDLE_WEBHOOK_SECRET` matches Paddle dashboard

**Issue**: Checkout redirect fails
- **Solution**: Verify success/cancel URLs are absolute URLs

**Issue**: Tax not calculated correctly
- **Solution**: Ensure customer address is complete

**Issue**: Subscription not created after payment
- **Solution**: Check webhook logs, verify database connection

## Next Steps

1. **Implement Trial Period**: Add 14-day free trial
2. **Usage-Based Billing**: Track quote generation, email processing
3. **Annual Plans**: Add yearly billing with discount
4. **Custom Plans**: Enterprise custom pricing
5. **Referral Program**: Affiliate tracking with Paddle

## Security Considerations

- Always verify webhook signatures
- Use HTTPS for all payment flows
- Store minimal payment data
- Implement rate limiting on billing endpoints
- Log all subscription changes
- Regular security audits

---

**Last Updated**: 2026-02-02
**Version**: 1.0.0
