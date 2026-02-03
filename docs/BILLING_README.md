# B2B Payment & Subscription Implementation

## 🎯 Overview

This implementation provides a complete B2B subscription management system using **Paddle** as the Merchant of Record. It handles:

- ✅ Per-seat pricing ($150-$400/month per sales rep)
- ✅ Automatic tax compliance (VAT/Sales Tax)
- ✅ International trade (US/EU)
- ✅ Subscription management
- ✅ Invoice generation
- ✅ Team seat assignments
- ✅ Usage tracking

## 📁 Files Created

### Backend
- `app/models_billing.py` - Data models for subscriptions, invoices, seats
- `app/services/paddle_service.py` - Paddle API integration
- `app/routes/billing.py` - Billing API endpoints
- `scripts/init_billing.py` - Database initialization script

### Frontend
- `frontend/src/pages/AccountBilling.tsx` - Billing dashboard UI
- Updated `frontend/src/services/api.ts` - Added billingApi

### Documentation
- `docs/BILLING_SETUP.md` - Comprehensive setup guide
- `.env.example` - Updated with Paddle configuration

### Configuration
- Updated `app/main.py` - Registered billing routes

## 🚀 Quick Start

### 1. Install Dependencies

No additional dependencies needed! Uses existing packages.

### 2. Configure Environment

Add to `.env`:

```bash
# Paddle Configuration
PADDLE_VENDOR_ID=your-vendor-id
PADDLE_VENDOR_AUTH_CODE=your-auth-code
PADDLE_PUBLIC_KEY=your-public-key
PADDLE_WEBHOOK_SECRET=your-webhook-secret
PADDLE_SANDBOX=true

# Product IDs
PADDLE_PLAN_BASIC_MONTHLY=prod_basic_123
PADDLE_PLAN_PRO_MONTHLY=prod_pro_456
PADDLE_PLAN_ENTERPRISE_MONTHLY=prod_ent_789
```

### 3. Initialize Database

```bash
# Run the billing schema in Supabase SQL editor
# Copy from app/models_billing.py -> BILLING_SCHEMA

# Then run initialization script
python scripts/init_billing.py
```

### 4. Access Billing Dashboard

Navigate to: `http://localhost:3000/account/billing`

## 💰 Pricing Tiers

### Basic - $150/seat/month
- Unlimited quotes
- Email integration
- Basic analytics
- Standard support
- Max 10 seats

### Professional - $250/seat/month
- Everything in Basic
- Advanced analytics
- QuickBooks integration
- Priority support
- Custom branding
- Max 50 seats

### Enterprise - $400/seat/month
- Everything in Professional
- Dedicated account manager
- Custom integrations
- SLA guarantee
- Advanced security
- Unlimited seats

## 🔧 API Endpoints

### Subscription Management
```
GET    /billing/plans                    - List subscription plans
GET    /billing/subscription             - Get current subscription
POST   /billing/subscription/update      - Update subscription
POST   /billing/subscription/cancel      - Cancel subscription
```

### Checkout
```
POST   /billing/checkout/create-session  - Create Paddle checkout
POST   /billing/portal/create-session    - Create billing portal session
```

### Invoices
```
GET    /billing/invoices                 - List all invoices
GET    /billing/invoices/:id             - Get specific invoice
```

### Seat Management
```
GET    /billing/seats                    - List seat assignments
POST   /billing/seats/assign             - Assign seat to sales rep
POST   /billing/seats/:id/deactivate     - Deactivate seat
```

### Usage & Analytics
```
GET    /billing/usage                    - Get usage statistics
```

### Webhooks
```
POST   /billing/webhooks/paddle          - Paddle webhook handler
```

## 🎨 Frontend Features

### Overview Tab
- Current plan display
- Monthly cost breakdown
- Active seats count
- Next billing date
- Usage statistics
- Seat management controls

### Plans Tab
- All available plans
- Feature comparison
- Upgrade/downgrade buttons
- Current plan highlighting

### Invoices Tab
- Invoice history
- Download PDF invoices
- Payment status
- Date filtering

### Seats Tab
- Team member list
- Seat assignment
- Seat deactivation
- Utilization metrics

## 🔐 Security Features

- ✅ Webhook signature verification
- ✅ HTTPS required for payments
- ✅ Minimal payment data storage
- ✅ Rate limiting on billing endpoints
- ✅ Audit logging for subscription changes

## 🌍 International Support

### Tax Compliance
- **US**: Automatic sales tax calculation
- **EU**: VAT handling with reverse charge for B2B
- **UK**: VAT compliance
- **Canada**: GST/HST support

### Currency Support
- USD (primary)
- EUR
- GBP
- CAD

### Example: EU B2B Transaction
```
Customer: Sanitär-Heinze GmbH (Germany)
VAT Number: DE123456789
Transaction: 5 seats × €250 = €1,250
VAT: 0% (Reverse Charge)
Invoice: Shows "Reverse Charge - Customer to account for VAT"
```

## 📊 Usage Tracking

Track key metrics:
- Quotes generated
- Emails processed
- Seats utilized
- API calls made

```typescript
const usage = await billingApi.getUsage();
console.log(usage);
// {
//   quotes_generated: 45,
//   emails_processed: 120,
//   seats_used: 3,
//   seats_total: 5
// }
```

## 🔄 Webhook Events

Handled events:
- `subscription_created` - New subscription
- `subscription_updated` - Seat/plan changes
- `subscription_cancelled` - Cancellation
- `subscription_payment_succeeded` - Successful payment
- `subscription_payment_failed` - Failed payment

## 🧪 Testing

### Sandbox Mode
```bash
# Enable sandbox in .env
PADDLE_SANDBOX=true

# Use test card
Card: 4242 4242 4242 4242
Expiry: Any future date
CVV: Any 3 digits
```

### Test Scenarios
1. Create subscription
2. Upgrade plan
3. Add/remove seats
4. Cancel subscription
5. Failed payment handling
6. Webhook processing

## 📈 Analytics Queries

### Monthly Recurring Revenue
```sql
SELECT SUM(total_amount) as mrr
FROM subscriptions
WHERE status = 'active';
```

### Seat Utilization
```sql
SELECT 
  AVG(assigned::float / total * 100) as avg_utilization
FROM (
  SELECT 
    s.seats as total,
    COUNT(sa.id) as assigned
  FROM subscriptions s
  LEFT JOIN seat_assignments sa ON s.id = sa.subscription_id
  WHERE s.status = 'active' AND sa.is_active = true
  GROUP BY s.id, s.seats
) stats;
```

### Churn Rate
```sql
SELECT 
  COUNT(*) FILTER (WHERE canceled_at IS NOT NULL) * 100.0 / COUNT(*) as churn_rate
FROM subscriptions
WHERE created_at >= NOW() - INTERVAL '30 days';
```

## 🚨 Troubleshooting

### Issue: Checkout redirect fails
**Solution**: Ensure success/cancel URLs are absolute
```typescript
success_url: `${window.location.origin}/account/billing?success=true`
```

### Issue: Webhook signature invalid
**Solution**: Verify webhook secret matches Paddle dashboard

### Issue: Tax not calculated
**Solution**: Ensure customer address is complete

## 📚 Additional Resources

- [Paddle Documentation](https://developer.paddle.com/)
- [Tax Compliance Guide](docs/BILLING_SETUP.md)
- [API Reference](http://localhost:8000/docs)

## 🎯 Next Steps

1. **Trial Period**: Implement 14-day free trial
2. **Annual Billing**: Add yearly plans with discount
3. **Usage-Based**: Implement metered billing
4. **Referrals**: Add affiliate program
5. **Dunning**: Handle failed payments
6. **Reporting**: Advanced analytics dashboard

## 📞 Support

For billing issues:
- Check logs: `tail -f server.log`
- Review webhooks in Paddle dashboard
- Test in sandbox mode first
- Contact Paddle support for payment issues

---

**Implementation Date**: 2026-02-02  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
