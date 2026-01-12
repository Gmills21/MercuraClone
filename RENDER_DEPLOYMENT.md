# 🚀 Render Deployment Guide for Mercura

This guide will walk you through deploying Mercura to Render and getting everything configured.

---

## ✅ Pre-Deployment Checklist

Before deploying to Render, make sure you have:

- [ ] A Render account (sign up at [render.com](https://render.com) - free tier available)
- [ ] Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
- [ ] Supabase project created and configured
- [ ] Google Cloud account with Gemini API enabled
- [ ] SendGrid or Mailgun account set up

---

## 📋 Step 1: Push Code to Git Repository

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Mercura application"
   ```

2. **Push to GitHub/GitLab/Bitbucket**:
   ```bash
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

---

## 🌐 Step 2: Deploy to Render

### Option A: Using render.yaml (Recommended)

1. **Log in to Render Dashboard**: [dashboard.render.com](https://dashboard.render.com)

2. **Create New Blueprint**:
   - Click "New +" → "Blueprint"
   - Connect your Git repository
   - Render will automatically detect `render.yaml` and use it

3. **Review Configuration**:
   - Render will parse `render.yaml` and show you the services to create
   - Review the settings and click "Apply"

### Option B: Manual Service Creation

1. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your Git repository

2. **Configure Service**:
   - **Name**: `mercura-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Start with `Starter` (can upgrade later)

3. **Click "Create Web Service"**

---

## 🔐 Step 3: Configure Environment Variables

In the Render Dashboard, go to your service → **Environment** tab and add these variables:

### Required Variables:

```bash
# Application
APP_NAME=Mercura
APP_ENV=production
DEBUG=False
SECRET_KEY=<generate-a-random-secret-key>
HOST=0.0.0.0

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Gemini AI
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-1.5-flash

# Email Provider
EMAIL_PROVIDER=sendgrid  # or mailgun

# SendGrid (if using)
SENDGRID_WEBHOOK_SECRET=your-webhook-secret
SENDGRID_INBOUND_DOMAIN=inbound.yourdomain.com

# Mailgun (if using)
MAILGUN_API_KEY=your-api-key
MAILGUN_WEBHOOK_SECRET=your-webhook-secret
MAILGUN_DOMAIN=mg.yourdomain.com
```

### Optional Variables (have defaults):

```bash
LOG_LEVEL=INFO
MAX_EXPORT_ROWS=10000
MAX_ATTACHMENT_SIZE_MB=25
CONFIDENCE_THRESHOLD=0.7
```

### 🔑 Generate SECRET_KEY:

Use one of these methods:
- Online: [randomkeygen.com](https://randomkeygen.com/)
- Python: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- OpenSSL: `openssl rand -hex 32`

---

## 🗄️ Step 4: Initialize Supabase Database

1. **Go to Supabase Dashboard**: [app.supabase.com](https://app.supabase.com)

2. **Open SQL Editor**

3. **Run the Schema**:
   - Copy the SQL from `app/models.py` (SUPABASE_SCHEMA variable)
   - Or run the init script locally to generate `database_schema.sql`
   - Paste and execute in Supabase SQL Editor

4. **Verify Tables Created**:
   - Check that these tables exist:
     - `users`
     - `inbound_emails`
     - `line_items`
     - `catalogs`

---

## 🌍 Step 5: Configure Custom Domain (Optional)

1. **In Render Dashboard**:
   - Go to your service → **Settings** → **Custom Domains**
   - Click "Add Custom Domain"
   - Enter your domain (e.g., `api.yourdomain.com`)

2. **Configure DNS**:
   - Add a CNAME record pointing to your Render service
   - Example: `api.yourdomain.com` → `mercura-api.onrender.com`

3. **SSL Certificate**:
   - Render automatically provisions SSL certificates via Let's Encrypt
   - Wait 5-10 minutes for SSL to be activated

---

## 📧 Step 6: Configure Email Provider Webhook

### If Using SendGrid:

1. **Go to SendGrid Dashboard** → Settings → Inbound Parse

2. **Add Hostname**:
   - Hostname: `inbound.yourdomain.com` (or your chosen subdomain)
   - Destination URL: `https://your-render-url.onrender.com/webhooks/inbound-email`
   - Click "Add"

3. **Configure DNS**:
   - Add MX record: `inbound.yourdomain.com` → `mx.sendgrid.net` (priority 10)

4. **Update Environment Variables**:
   - In Render, set `SENDGRID_WEBHOOK_SECRET` from SendGrid settings

### If Using Mailgun:

1. **Go to Mailgun Dashboard** → Sending → Routes

2. **Create Route**:
   - Expression: `match_recipient(".*@inbound.yourdomain.com")`
   - Action: Forward to `https://your-render-url.onrender.com/webhooks/inbound-email`
   - Click "Create Route"

3. **Configure DNS** (if using custom domain):
   - Add MX records as provided by Mailgun
   - Add TXT record for domain verification

4. **Update Environment Variables**:
   - In Render, set `MAILGUN_API_KEY` and `MAILGUN_WEBHOOK_SECRET`

---

## ✅ Step 7: Verify Deployment

1. **Check Health Endpoint**:
   ```bash
   curl https://your-service-name.onrender.com/health
   ```
   Should return: `{"status": "healthy", "timestamp": "..."}`

2. **Check Root Endpoint**:
   ```bash
   curl https://your-service-name.onrender.com/
   ```
   Should return API information

3. **Check API Documentation**:
   - Visit: `https://your-service-name.onrender.com/docs`
   - You should see FastAPI interactive documentation

---

## 🧪 Step 8: Test the System

### Test Health Check:
```bash
curl https://your-service-name.onrender.com/health
```

### Test Email Webhook (SendGrid):
```bash
curl -X POST https://your-service-name.onrender.com/webhooks/inbound-email \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Send a Test Email:
1. Send an email to `test@inbound.yourdomain.com`
2. Check Render logs for processing
3. Check Supabase to see if data was stored

---

## 📊 Step 9: Monitor Your Deployment

### View Logs:
1. In Render Dashboard → Your Service → **Logs** tab
2. Real-time logs will appear here
3. Look for any errors or warnings

### Check Metrics:
- Render provides basic metrics:
  - CPU usage
  - Memory usage
  - Response times
  - Request counts

### Set Up Alerts (Optional):
- Render can send email alerts for service failures
- Configure in Settings → Alerts

---

## 🔧 Step 10: Troubleshooting

### Common Issues:

#### 1. **Application Won't Start**
   - **Check**: Environment variables are set correctly
   - **Check**: Logs for specific error messages
   - **Verify**: All required variables are present

#### 2. **Database Connection Errors**
   - **Verify**: Supabase URL and keys are correct
   - **Check**: Supabase project is active
   - **Verify**: Network connectivity (Render should have internet access)

#### 3. **Webhook Not Receiving Emails**
   - **Check**: Webhook URL is correct in email provider settings
   - **Verify**: DNS records are configured correctly
   - **Test**: Webhook endpoint is publicly accessible

#### 4. **Port Issues**
   - Render automatically provides `$PORT` environment variable
   - The app is configured to use this automatically
   - Don't hardcode port numbers

#### 5. **Build Failures**
   - **Check**: `requirements.txt` is correct
   - **Verify**: All dependencies are listed
   - **Check**: Python version compatibility

---

## 🚀 Step 11: Production Optimization

### Upgrade Plan (When Ready):
1. In Render Dashboard → Settings → Plan
2. Upgrade from `Starter` to `Standard` or `Pro` for:
   - More RAM and CPU
   - Better performance
   - Higher request limits

### Enable Auto-Deploy:
- By default, Render auto-deploys on git push
- Configure in Settings → Auto-Deploy

### Set Up Environment-Specific Variables:
- Consider using Render's environment groups
- Separate staging and production environments

---

## 📝 Step 12: Create Your First User

After deployment, create a user in Supabase:

```sql
-- Execute in Supabase SQL Editor
INSERT INTO users (email, company_name, is_active, email_quota_per_day)
VALUES ('user@example.com', 'Example Corp', true, 1000);
```

---

## 🎯 Next Steps After Deployment

1. **Test Full Workflow**:
   - Send test email with attachment
   - Verify data extraction
   - Check export functionality

2. **Monitor Performance**:
   - Watch logs for first few days
   - Monitor API usage (Gemini quotas)
   - Track database growth

3. **Set Up Backups**:
   - Configure Supabase backups
   - Set up log retention

4. **Security Hardening**:
   - Review CORS settings
   - Enable rate limiting
   - Set up API authentication (if needed)

5. **Documentation**:
   - Document your webhook URLs
   - Create user guide
   - Document API endpoints

---

## 📞 Support Resources

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Render Status**: [status.render.com](https://status.render.com)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)
- **Gemini API Docs**: [ai.google.dev](https://ai.google.dev)

---

## ✅ Deployment Checklist

Use this checklist to ensure everything is set up:

- [ ] Code pushed to Git repository
- [ ] Service created in Render
- [ ] All environment variables configured
- [ ] Supabase database initialized
- [ ] Email provider webhook configured
- [ ] DNS records configured (if using custom domain)
- [ ] Health endpoint responding
- [ ] API docs accessible
- [ ] Test email sent and processed
- [ ] Logs are being generated
- [ ] First user created in database
- [ ] Monitoring set up

---

## 🎉 You're Live!

Once all steps are complete, your Mercura application is deployed and ready to process emails!

**Your Render URL**: `https://your-service-name.onrender.com`
**API Docs**: `https://your-service-name.onrender.com/docs`
**Health Check**: `https://your-service-name.onrender.com/health`

---

**Deployment Date**: _________________
**Deployed By**: _________________
**Render Service URL**: _________________
**Status**: ⬜ In Progress  ⬜ Complete  ⬜ Live

---

*Happy deploying! 🚀*
