# 🆓 Free Deployment Options for Mercura

Since you already have a custom domain, here are the best free/low-cost deployment options that support **full functionality**:

---

## 🥇 **Railway** (RECOMMENDED - Best Choice)

**Cost:** $5/month credit = **Effectively FREE** for low usage

### Why Railway is Best:
- ✅ **No timeout limits** - Perfect for Gemini API calls (can take 10-30+ seconds)
- ✅ **Custom domain support** - Free (connect your existing domain)
- ✅ **HTTPS included** - Automatic SSL certificates
- ✅ **Persistent file storage** - Required for `temp/exports` directory
- ✅ **Auto-deploy from Git** - Push to GitHub, auto-deploys
- ✅ **FastAPI optimized** - Great Python/FastAPI support
- ✅ **512MB RAM, 1GB disk** - Sufficient for your app

### Setup Steps:

1. **Sign up:** [railway.app](https://railway.app) (GitHub login)
2. **Create New Project** → Deploy from GitHub repo
3. **Set Environment Variables:**
   - All variables from `.env` file
   - Add via Railway dashboard → Variables tab
4. **Configure Domain:**
   - Settings → Domains → Add custom domain
   - Update DNS records (provided by Railway)
5. **Deploy:**
   - Railway auto-detects Python/FastAPI
   - Uses `requirements.txt` automatically
   - Builds and deploys in ~2-3 minutes

### Railway Configuration:

Railway will auto-detect your FastAPI app. Optionally create `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Note:** Railway provides `$PORT` automatically, but you can also use port 8000.

### Important Notes:
- ⚠️ Requires credit card (not charged if under $5/month)
- ⚠️ Sleeps after 30 days inactivity (wakes on next request)
- ✅ Perfect for production use with your custom domain

---

## 🥈 **Render** (Free Tier Option)

**Cost:** **FREE** (750 hours/month)

### Pros:
- ✅ **Custom domain support** - Free
- ✅ **HTTPS included** - Automatic
- ✅ **Auto-deploy from Git** - GitHub integration
- ✅ **Persistent disk** - 1GB storage
- ✅ **Simple setup** - Web-based dashboard

### Cons:
- ⚠️ **30-second timeout** - May be tight for some Gemini API calls
- ⚠️ **Sleeps after 15 min inactivity** - Adds ~30 second wake-up delay
- ⚠️ **512MB RAM** - Lower than Railway

### Setup Steps:

1. **Sign up:** [render.com](https://render.com) (GitHub login)
2. **Create New Web Service** → Connect GitHub repo
3. **Configuration:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3
4. **Set Environment Variables:**
   - Add all variables from `.env` in dashboard
5. **Configure Domain:**
   - Settings → Custom Domains → Add
   - Update DNS (provided by Render)

### Important Notes:
- ⚠️ Free tier spins down after 15 min inactivity
- ⚠️ First request after sleep takes ~30 seconds
- ✅ Good for low-traffic production use

---

## 🥉 **Fly.io** (Advanced Option)

**Cost:** **FREE** (3 shared VMs)

### Pros:
- ✅ **No timeout limits** - Good for long-running requests
- ✅ **Custom domain support** - Free
- ✅ **HTTPS included** - Automatic
- ✅ **FastAPI optimized** - Great Python support

### Cons:
- ⚠️ **More complex setup** - Requires Dockerfile
- ⚠️ **Free tier storage is ephemeral** - Files may be lost
- ⚠️ **Requires CLI installation** - Command-line tool needed

### Setup Steps:

1. **Install Fly CLI:**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Sign up:** [fly.io](https://fly.io) → `fly auth signup`

3. **Initialize project:**
   ```bash
   fly launch
   ```

4. **Create Dockerfile** (required):
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

5. **Set secrets:**
   ```bash
   fly secrets set SUPABASE_URL=xxx SUPABASE_KEY=xxx ...
   ```

6. **Deploy:**
   ```bash
   fly deploy
   ```

---

## ❌ **Vercel** (NOT Recommended)

**Why Vercel won't work:**

- ❌ **10-second timeout** - Your Gemini API calls take longer
- ❌ **No persistent file storage** - Your app writes to `temp/exports`
- ❌ **Serverless functions only** - Not designed for FastAPI apps
- ❌ **Stateless architecture** - Files are ephemeral

**Vercel is great for:** Next.js, static sites, serverless APIs  
**Vercel is NOT for:** FastAPI apps with file processing, long-running tasks

---

## 📋 Quick Comparison

| Feature | Railway | Render | Fly.io | Vercel |
|---------|---------|--------|--------|--------|
| **Cost** | $5 credit (free) | FREE | FREE | FREE |
| **Timeout** | Unlimited | 30s | Unlimited | 10s ❌ |
| **File Storage** | Persistent ✅ | Persistent ✅ | Ephemeral ⚠️ | None ❌ |
| **Custom Domain** | Free ✅ | Free ✅ | Free ✅ | Free ✅ |
| **HTTPS** | Auto ✅ | Auto ✅ | Auto ✅ | Auto ✅ |
| **Setup Difficulty** | Easy ⭐ | Easy ⭐ | Medium ⭐⭐ | Easy ⭐ |
| **Sleep Policy** | 30 days | 15 min | Never | Never |
| **Best For** | Production ✅ | Low traffic | Advanced users | Static sites ❌ |

---

## 🎯 **Recommendation: Railway**

**Why Railway wins:**
1. ✅ No timeout limits (critical for Gemini API)
2. ✅ Persistent file storage (needed for exports)
3. ✅ Simple setup (GitHub → Deploy)
4. ✅ Custom domain support (you already have one)
5. ✅ Effectively free ($5 credit covers low usage)

**Perfect for your use case:** Email processing, file exports, long-running AI calls

---

## 🚀 **Quick Start: Deploy to Railway in 10 Minutes**

1. **Push code to GitHub** (if not already)
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Sign up at Railway:** [railway.app](https://railway.app)
   - Click "Login" → "GitHub" → Authorize

3. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your Mercura repository

4. **Add Environment Variables:**
   - Click on your service → "Variables" tab
   - Add all variables from your `.env` file:
     - `SUPABASE_URL`
     - `SUPABASE_KEY`
     - `SUPABASE_SERVICE_KEY`
     - `GEMINI_API_KEY`
     - `EMAIL_PROVIDER`
     - `SENDGRID_WEBHOOK_SECRET` (or Mailgun equivalent)
     - `SECRET_KEY`
     - `APP_ENV=production`
     - `DEBUG=False`
     - `HOST=0.0.0.0`
     - `PORT=8000`
     - All other required variables

5. **Configure Domain:**
   - Settings → Domains → "Add Custom Domain"
   - Enter your domain (e.g., `api.yourdomain.com`)
   - Railway provides DNS records to add at your registrar
   - Add CNAME record in your DNS settings
   - Wait 5-10 minutes for DNS propagation
   - HTTPS certificate is automatic!

6. **Update Webhook URLs:**
   - SendGrid: Settings → Inbound Parse → Update destination URL
   - Mailgun: Receiving → Routes → Update forward URL
   - New URL: `https://yourdomain.com/webhooks/inbound-email`

7. **Test:**
   ```bash
   # Health check
   curl https://yourdomain.com/health
   
   # API docs
   # Visit: https://yourdomain.com/docs
   ```

8. **Done!** ✅ Your app is live with full functionality!

---

## 💡 **Tips for Free Tier Success**

### Keep Costs Low:
- Railway: Stay under $5/month (easy for low traffic)
- Render: Stay under 750 hours/month (plenty for 24/7)
- Monitor usage in dashboard

### Optimize for Free Tier:
- Use Supabase free tier (500MB database, 2GB bandwidth)
- Use Gemini 1.5 Flash (very cheap, $0.075 per 1M tokens)
- Limit export file sizes if needed
- Set up log rotation

### Scale When Needed:
- Railway: Pay-as-you-go ($5 credit → actual usage)
- Render: Upgrade to Starter ($7/month) for always-on
- Both support scaling up easily

---

## 🆘 **Troubleshooting**

### Railway:
- **Build fails:** Check `requirements.txt` is correct
- **App crashes:** Check logs in Railway dashboard
- **Domain not working:** Verify DNS records (may take up to 48 hours)
- **File storage:** Check `temp/exports` directory exists

### Render:
- **Timeout errors:** Gemini calls taking >30 seconds (upgrade or use Railway)
- **Sleep delays:** First request after 15 min inactivity is slow (normal)
- **Disk full:** Free tier has 1GB limit (check export file sizes)

---

## ✅ **Final Checklist**

Before going live:

- [ ] Code pushed to GitHub
- [ ] Railway/Render account created
- [ ] All environment variables set
- [ ] Custom domain configured
- [ ] DNS records updated (may take 5-48 hours)
- [ ] HTTPS certificate active (automatic)
- [ ] Webhook URLs updated in SendGrid/Mailgun
- [ ] Test endpoint: `curl https://yourdomain.com/health`
- [ ] Test webhook: Send test email
- [ ] Test export: Generate CSV/Excel file
- [ ] Monitor logs for errors

---

**🎉 You're ready to deploy! Railway is the best choice for your FastAPI app with full functionality on a free/low-cost tier.**
