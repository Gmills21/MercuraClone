# 🧪 Mercura API Testing Guide

Your service is now live! Here's how to test everything.

## 🔍 Step 1: Find Your Service URL

**If deployed on Railway:**
- Go to Railway dashboard → Your service → Settings → Domains
- Your URL will be: `https://your-service-name.up.railway.app` (or your custom domain)

**If deployed on Render:**
- Go to Render dashboard → Your service
- Your URL will be: `https://your-service-name.onrender.com` (or your custom domain)

**Replace `YOUR_URL` in all commands below with your actual URL!**

---

## ✅ Step 2: Basic Health Checks

### Test 1: Health Endpoint
```bash
curl https://YOUR_URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### Test 2: Root Endpoint
```bash
curl https://YOUR_URL/
```

**Expected Response:**
```json
{
  "name": "Mercura",
  "version": "1.0.0",
  "status": "running",
  "environment": "production",
  "email_provider": "sendgrid",
  "docs": "/docs"
}
```

### Test 3: API Documentation (Browser)
Open in your browser:
```
https://YOUR_URL/docs
```

You should see the FastAPI interactive documentation (Swagger UI) with all available endpoints.

### Test 4: Webhook Health
```bash
curl https://YOUR_URL/webhooks/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "provider": "sendgrid",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

---

## 📊 Step 3: Test Data Endpoints

### Test 5: Get Statistics
```bash
curl https://YOUR_URL/data/stats
```

**Expected Response:**
```json
{
  "period_days": 30,
  "total_emails": 0,
  "processed_emails": 0,
  "failed_emails": 0,
  "success_rate": 0,
  "total_line_items": 0,
  "average_confidence": 0,
  "items_per_email": 0
}
```

*(Will show 0s until you process some emails)*

### Test 6: Get Emails List
```bash
curl https://YOUR_URL/data/emails
```

**Expected Response:**
```json
{
  "emails": [],
  "count": 0,
  "limit": 50,
  "offset": 0
}
```

### Test 7: Get Line Items
```bash
curl https://YOUR_URL/data/line-items
```

**Expected Response:**
```json
{
  "line_items": [],
  "count": 0,
  "limit": 100
}
```

---

## 📤 Step 4: Test Export Endpoints

### Test 8: Export to CSV (Empty - No Data Yet)
```bash
curl -X POST https://YOUR_URL/export/csv \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected:** CSV file download (may be empty if no data)

### Test 9: Export to Excel (Empty - No Data Yet)
```bash
curl -X POST https://YOUR_URL/export/excel \
  -H "Content-Type: application/json" \
  -d '{}' \
  --output test-export.xlsx
```

**Expected:** Excel file download

### Test 10: Export History
```bash
curl https://YOUR_URL/export/history
```

---

## 📧 Step 5: Set Up Database & Test Webhooks

### First: Initialize Database

Before webhooks can work, you need to:
1. **Create a user in your Supabase database**

Go to Supabase Dashboard → SQL Editor and run:

```sql
-- Insert a test user (replace with your email)
INSERT INTO users (email, is_active, email_quota_per_day)
VALUES ('your-email@example.com', true, 100)
ON CONFLICT (email) DO UPDATE SET is_active = true;
```

**Important:** Replace `your-email@example.com` with the email address you'll use to send test emails!

### Test 11: Check if User Exists (via API)
You can verify your user exists by checking the emails endpoint - if emails are processed, the user exists.

---

## 🎯 Step 6: Test End-to-End Email Processing

### Option A: Using SendGrid (If Configured)

1. **Send a test email** to your inbound address (e.g., `test@inbound.yourdomain.com`)
2. **Include an attachment** (PDF, PNG, or JPG) with invoice/receipt data
3. **Check the webhook was called:**
   ```bash
   # Check if email was processed
   curl https://YOUR_URL/data/emails
   ```

### Option B: Manual Webhook Test (Advanced)

You can manually test the webhook endpoint using curl, but you'll need to:
- Generate proper webhook signatures
- Format the request correctly

**Easier approach:** Use the FastAPI docs at `/docs` to test endpoints interactively!

---

## 🌐 Step 7: Interactive API Testing

### Use FastAPI Docs (Easiest Method!)

1. **Open:** `https://YOUR_URL/docs`
2. **Click on any endpoint** to expand it
3. **Click "Try it out"**
4. **Fill in parameters** (if needed)
5. **Click "Execute"**
6. **See the response** below

This is the easiest way to test all endpoints without writing curl commands!

---

## 🔍 Step 8: Verify Everything Works

### Checklist:

- [ ] ✅ Health endpoint returns `{"status": "healthy"}`
- [ ] ✅ Root endpoint shows API info
- [ ] ✅ `/docs` page loads and shows all endpoints
- [ ] ✅ Statistics endpoint returns data (even if zeros)
- [ ] ✅ Data endpoints return empty arrays (no data yet)
- [ ] ✅ Export endpoints respond (may return empty files)
- [ ] ✅ Database has at least one user created
- [ ] ✅ Environment variables are all set (check logs)

---

## 🐛 Troubleshooting

### If endpoints return errors:

1. **Check deployment logs:**
   - Railway: Dashboard → Service → Logs
   - Render: Dashboard → Service → Logs

2. **Common issues:**
   - **500 errors:** Check if environment variables are set
   - **404 errors:** Check the URL is correct
   - **Database errors:** Verify Supabase connection strings
   - **Webhook errors:** Check email provider configuration

3. **Check environment variables:**
   ```bash
   # The app logs missing variables at startup
   # Check your deployment logs for warnings
   ```

---

## 📝 Next Steps

Once basic testing works:

1. **Set up email webhooks** (SendGrid or Mailgun)
2. **Send a test email** with invoice/receipt attachment
3. **Verify data extraction** via `/data/emails` and `/data/line-items`
4. **Test exports** with real data
5. **Monitor logs** for any issues

---

## 🎉 Quick Test Script

Save this as `test-api.sh` and run it:

```bash
#!/bin/bash

# Replace with your URL
URL="https://YOUR_URL"

echo "Testing Mercura API..."
echo ""

echo "1. Health Check:"
curl -s "$URL/health" | jq .
echo ""

echo "2. Root Endpoint:"
curl -s "$URL/" | jq .
echo ""

echo "3. Statistics:"
curl -s "$URL/data/stats" | jq .
echo ""

echo "4. Emails:"
curl -s "$URL/data/emails" | jq .
echo ""

echo "5. Line Items:"
curl -s "$URL/data/line-items" | jq .
echo ""

echo "✅ Basic tests complete!"
echo "Visit $URL/docs for interactive testing"
```

**To run:**
```bash
chmod +x test-api.sh
./test-api.sh
```

*(Requires `jq` for JSON formatting - install with `brew install jq` on Mac or `apt-get install jq` on Linux)*

---

**Happy Testing! 🚀**
