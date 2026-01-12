# 🚀 Mercura Deployment Checklist

Use this checklist to deploy your Email-to-Spreadsheet automation system.

---

## 📋 Pre-Deployment Setup

### 1. Service Accounts Setup

#### Supabase
- [ ] Create Supabase account at [supabase.com](https://supabase.com)
- [ ] Create new project
- [ ] Copy Project URL from Settings → API
- [ ] Copy `anon` key from Settings → API
- [ ] Copy `service_role` key from Settings → API
- [ ] Navigate to SQL Editor
- [ ] Execute the SQL schema from `app/models.py` (SUPABASE_SCHEMA)
- [ ] Verify tables created: `users`, `inbound_emails`, `line_items`, `catalogs`

#### Google Cloud (Gemini)
- [ ] Create Google Cloud account
- [ ] Create new project or select existing
- [ ] Enable Gemini API (AI Studio)
- [ ] Generate API key
- [ ] Set up billing (Gemini 1.5 Flash pricing)
- [ ] Test API key with sample request

#### Email Provider (Choose One)

**Option A: SendGrid**
- [ ] Create SendGrid account
- [ ] Verify domain ownership
- [ ] Configure DNS MX records to point to SendGrid
- [ ] Navigate to Settings → Inbound Parse
- [ ] Add hostname (e.g., `inbound.yourdomain.com`)
- [ ] Set destination URL: `https://your-server.com/webhooks/inbound-email`
- [ ] Enable spam check
- [ ] Copy webhook verification key

**Option B: Mailgun**
- [ ] Create Mailgun account
- [ ] Add and verify domain
- [ ] Configure DNS records (MX, TXT, CNAME)
- [ ] Navigate to Receiving → Routes
- [ ] Create new route
- [ ] Set expression: `match_recipient(".*@inbound.yourdomain.com")`
- [ ] Set action: Forward to `https://your-server.com/webhooks/inbound-email`
- [ ] Copy webhook signing key

#### Google Sheets (Optional)
- [ ] Go to Google Cloud Console
- [ ] Enable Google Sheets API
- [ ] Create service account
- [ ] Download JSON credentials
- [ ] Save to `credentials/google-sheets-credentials.json`
- [ ] Share target Google Sheets with service account email

---

## 💻 Local Development Setup

### 2. Environment Configuration

```bash
# Navigate to project directory
cd "c:\Users\graha\Mercura Clone"

# Copy environment template
copy .env.example .env

# Edit .env file
notepad .env
```

**Fill in these values in `.env`:**

```env
# Application
APP_NAME=Mercura
APP_ENV=development
DEBUG=True
SECRET_KEY=<generate-random-secret-key>

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Gemini
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

### 3. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Run database initialization script
python scripts/init_db.py

# This generates database_schema.sql
# Copy the SQL content and execute in Supabase SQL Editor
```

### 5. Test the System

```bash
# Test Gemini extraction
python tests/test_extraction.py

# Expected output:
# ✅ Success: True
# ✅ Confidence: 0.85+
# ✅ Items Extracted: 3+
```

### 6. Run Development Server

```bash
# Start FastAPI server
uvicorn app.main:app --reload

# Server should start at http://localhost:8000
# Visit http://localhost:8000/docs for API documentation
```

### 7. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status": "healthy", ...}

# API info
curl http://localhost:8000/

# Expected: {"name": "Mercura", "status": "running", ...}
```

---

## 🌐 Production Deployment

### 8. Server Setup

**Choose a hosting platform:**
- [ ] AWS EC2 / Lightsail
- [ ] Google Cloud Run
- [ ] DigitalOcean Droplet
- [ ] Heroku
- [ ] Railway
- [ ] Render

**Server requirements:**
- Python 3.9+
- 1GB RAM minimum (2GB recommended)
- 10GB storage
- HTTPS/SSL certificate
- Public IP address

### 9. Deploy Application

**Option A: Docker (Recommended)**

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t mercura .
docker run -p 8000:8000 --env-file .env mercura
```

**Option B: Direct Deployment**

```bash
# SSH into server
ssh user@your-server.com

# Clone repository
git clone <your-repo-url>
cd mercura

# Install dependencies
pip install -r requirements.txt

# Copy .env file
nano .env  # paste your configuration

# Run with production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Option C: Process Manager (PM2/Supervisor)**

```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name mercura

# Save PM2 configuration
pm2 save
pm2 startup
```

### 10. Configure Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 11. Enable HTTPS (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 12. Update Email Provider Webhook

- [ ] Update webhook URL to production domain
- [ ] Test webhook delivery
- [ ] Verify signature verification works

---

## ✅ Post-Deployment Verification

### 13. Smoke Tests

```bash
# Test health endpoint
curl https://your-domain.com/health

# Test webhook endpoint (should return 401 without signature)
curl -X POST https://your-domain.com/webhooks/inbound-email

# View API documentation
# Visit: https://your-domain.com/docs
```

### 14. Send Test Email

```bash
# Send email to your configured address
# To: test@inbound.yourdomain.com
# Subject: Test Invoice
# Body: Test message
# Attachment: sample invoice PDF
```

### 15. Verify Processing

```bash
# Check emails endpoint
curl https://your-domain.com/data/emails

# Check statistics
curl https://your-domain.com/data/stats
```

### 16. Test Export

```bash
# Export CSV
curl -X POST https://your-domain.com/export/csv \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z"
  }' \
  --output test_export.csv

# Verify CSV file created
```

---

## 🔒 Security Hardening

### 17. Security Checklist

- [ ] Change `SECRET_KEY` to random value
- [ ] Set `DEBUG=False` in production
- [ ] Enable HTTPS only
- [ ] Configure CORS properly (restrict origins)
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Implement API key authentication
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Set up backup strategy for database

### 18. Monitoring Setup

**Logging:**
- [ ] Verify logs are being written to `logs/mercura.log`
- [ ] Set up log rotation
- [ ] Configure log aggregation (optional: Datadog, Sentry)

**Alerts:**
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Configure email alerts for errors
- [ ] Monitor Gemini API quota usage
- [ ] Track database storage usage

**Metrics:**
- [ ] Track emails processed per day
- [ ] Monitor average extraction time
- [ ] Track confidence score trends
- [ ] Monitor error rates

---

## 📊 Create First User

### 19. Add User to Database

```sql
-- Execute in Supabase SQL Editor
INSERT INTO users (email, company_name, is_active, email_quota_per_day)
VALUES ('user@example.com', 'Example Corp', true, 1000);
```

**Or use API (future feature):**
```bash
curl -X POST https://your-domain.com/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "company_name": "Example Corp"
  }'
```

---

## 🎯 Go Live Checklist

### 20. Final Verification

- [ ] All environment variables set correctly
- [ ] Database schema executed successfully
- [ ] Gemini API key working
- [ ] Email provider webhook configured
- [ ] HTTPS enabled
- [ ] Test email processed successfully
- [ ] Export functionality working
- [ ] Logs being written
- [ ] Monitoring alerts configured
- [ ] Documentation accessible
- [ ] Backup strategy in place

### 21. User Communication

- [ ] Prepare user guide
- [ ] Document email forwarding address
- [ ] Explain export process
- [ ] Provide support contact
- [ ] Share API documentation link

---

## 📈 Scaling Considerations

### When to Scale

**Indicators:**
- Processing > 1000 emails/day
- Response time > 10 seconds
- CPU usage > 80%
- Memory usage > 80%

**Scaling Options:**
1. **Vertical Scaling:** Increase server resources
2. **Horizontal Scaling:** Add more server instances
3. **Queue System:** Add Redis/Celery for async processing
4. **CDN:** Use CloudFlare for static assets
5. **Database:** Upgrade Supabase plan or use read replicas

---

## 🆘 Troubleshooting

### Common Issues

**Webhook not receiving emails:**
- Check MX records: `nslookup -type=MX inbound.yourdomain.com`
- Verify webhook URL is publicly accessible
- Check webhook signature verification
- Review email provider logs

**Gemini API errors:**
- Verify API key is valid
- Check quota limits
- Ensure billing is enabled
- Review API error messages

**Database connection issues:**
- Verify Supabase credentials
- Check network connectivity
- Review Supabase project status
- Check connection pool limits

**Export failures:**
- Verify data exists in database
- Check file permissions
- Review export logs
- Ensure sufficient disk space

---

## 📞 Support Resources

- **API Documentation:** `https://your-domain.com/docs`
- **Logs:** `logs/mercura.log`
- **Supabase Dashboard:** `https://app.supabase.com`
- **Gemini API Console:** `https://ai.google.dev`
- **Email Provider Dashboard:** SendGrid/Mailgun

---

## ✨ Success Criteria

Your deployment is successful when:

✅ Emails are automatically processed
✅ Data is extracted with >85% confidence
✅ Exports generate correctly
✅ System uptime > 99%
✅ Processing time < 10 seconds
✅ No data loss
✅ Users can access their data

---

## 🎉 You're Ready to Launch!

Once all checklist items are complete, your Mercura Email-to-Data Pipeline is live and ready to process emails!

**Next Steps:**
1. Monitor initial email processing
2. Gather user feedback
3. Optimize based on usage patterns
4. Plan Phase 2 features

---

**Deployment Date:** _________________

**Deployed By:** _________________

**Production URL:** _________________

**Status:** ⬜ In Progress  ⬜ Complete  ⬜ Live

---

*Good luck with your deployment! 🚀*
