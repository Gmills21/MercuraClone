# Custom Domain Setup Guide

This guide explains how to set up custom domains for OpenMercura, allowing your customers to access the app through their own branded domain (e.g., `crm.arkatos.com`).

---

## Overview

The custom domain feature enables:

- **White-label experience** - Customers access Mercura through their own domain
- **Automatic SSL** - HTTPS certificates provisioned automatically
- **DNS verification** - Ownership verified via TXT records
- **Multi-tenant routing** - Requests routed to correct organization based on domain

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  User Browser   │────▶│  Cloudflare/    │────▶│  Render.com     │
│                 │     │  DNS Provider   │     │  (Your App)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                              ┌─────────────────────────┘
                              ▼
                        ┌─────────────────┐
                        │ Custom Domain   │
                        │ Middleware      │
                        └─────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌─────────────┐         ┌─────────────┐
            │ Main App    │         │ Custom Dom  │
            │ Domain      │         │ Resolution  │
            └─────────────┘         └─────────────┘
```

---

## Prerequisites

### 1. For Render.com Deployment

Your `render.yaml` should include custom domain configuration:

```yaml
services:
  - type: web
    name: mercura-api
    # ... other config
    envVars:
      - key: APP_URL
        value: https://yourapp.onrender.com  # Your main domain
```

### 2. DNS Provider Access

Customers need access to their DNS provider (Cloudflare, GoDaddy, Namecheap, etc.) to add records.

### 3. Optional: Cloudflare for SSL

For the best experience, we recommend Cloudflare as the DNS provider because:
- Free SSL/TLS certificates
- Automatic HTTPS redirects
- DDoS protection
- Fast global CDN

---

## Customer Setup Flow

### Step 1: Register Domain in Mercura

1. Go to **Settings** → **Custom Domain**
2. Enter domain (e.g., `crm.arkatos.com`)
3. Click **Register Domain**

### Step 2: Add DNS Records

The system generates required DNS records:

```
Type:    CNAME
Name:    crm
Value:   yourapp.onrender.com
TTL:     3600

Type:    TXT
Name:    _mercura
Value:   mercura-verify=<random-token>
TTL:     3600
```

#### Cloudflare Example:

1. Log into Cloudflare dashboard
2. Select your domain (e.g., `arkatos.com`)
3. Go to **DNS** → **Records**
4. Click **Add Record**
5. Add the CNAME and TXT records shown above

#### GoDaddy Example:

1. Log into GoDaddy
2. Go to **My Products** → **DNS** (next to your domain)
3. Click **Add** under Records
4. Select Type "CNAME"
5. Enter Name: `crm`, Value: `yourapp.onrender.com`
6. Repeat for TXT record

### Step 3: Verify Domain

1. Wait 5-30 minutes for DNS propagation
2. Click **Verify Domain** in Mercura
3. If successful, SSL certificate is provisioned automatically
4. Domain becomes active!

---

## Deployment Configuration

### For Render.com

#### Option 1: Using Render's Built-in Custom Domains (Recommended)

1. In Render dashboard, go to your web service
2. Click **Settings** → **Custom Domains**
3. Add `crm.arkatos.com`
4. Render provides SSL automatically
5. In Mercura, the domain verification still works via TXT record

#### Option 2: Using Cloudflare Proxy (Advanced)

1. Set up Cloudflare as DNS provider
2. Add CNAME record with **orange cloud** (proxied)
3. Cloudflare handles SSL automatically
4. Mercura sees requests from Cloudflare IPs

### For Other Platforms (AWS, DigitalOcean, etc.)

1. Configure load balancer or reverse proxy to handle custom domains
2. Ensure the `Host` header is passed to the backend
3. SSL termination can happen at the load balancer
4. The middleware will resolve domains correctly

---

## Environment Variables

Add these to your deployment:

```bash
# Your main app URL
APP_URL=https://yourapp.onrender.com

# For local development
APP_URL=http://localhost:8000
```

---

## Database Schema

The custom domain feature uses two tables:

### `custom_domains` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | UUID primary key |
| `organization_id` | TEXT | FK to organizations |
| `domain` | TEXT | Custom domain (unique) |
| `status` | TEXT | pending/verified/active/failed |
| `verification_token` | TEXT | Random token for DNS verification |
| `dns_records` | TEXT | JSON array of required records |
| `ssl_status` | TEXT | SSL provisioning status |
| `created_at` | TEXT | Timestamp |
| `verified_at` | TEXT | Verification timestamp |

### `organizations` Table

Already has a `domain` column for the default slug-based domain.

---

## API Endpoints

### Get Domain Status
```
GET /custom-domains/status
Authorization: Bearer <token>

Response:
{
  "has_custom_domain": true,
  "domain": "crm.arkatos.com",
  "status": "active",
  "ssl_status": "active",
  "dns_records": [...],
  "is_active": true
}
```

### Register Domain
```
POST /custom-domains/register
Authorization: Bearer <token>
{
  "domain": "crm.arkatos.com"
}

Response:
{
  "success": true,
  "domain": {...},
  "dns_records": [...],
  "instructions": "..."
}
```

### Verify Domain
```
POST /custom-domains/verify
Authorization: Bearer <token>

Response:
{
  "success": true,
  "status": "verified",
  "message": "Domain verified successfully",
  "next_step": "SSL certificate will be provisioned..."
}
```

### Remove Domain
```
POST /custom-domains/remove
Authorization: Bearer <token>
```

---

## Middleware Behavior

The `CustomDomainMiddleware` runs on every request:

1. Extracts `Host` header from request
2. If host matches `APP_URL`, continues normally
3. If different, looks up in `custom_domains` table
4. If found and active, sets `request.state.custom_domain_org`
5. Downstream routes can access org via `get_custom_domain_org(request)`

---

## Troubleshooting

### "Domain verification failed"

- DNS propagation can take up to 24 hours
- Check TXT record is correctly formatted: `mercura-verify=<token>`
- Use `dig _mercura.yourdomain.com TXT` to verify

### "SSL certificate not provisioned"

- For Render: Ensure custom domain is added in Render dashboard
- For Cloudflare: Enable proxy (orange cloud) for automatic SSL
- May take 10-15 minutes after verification

### "Domain already registered"

- Each domain can only be registered to one organization
- Contact support to transfer domain ownership

### DNS Record Examples

**Apex domain (arkatos.com):**
```
Type:  ALIAS or ANAME
Name:  @
Value: yourapp.onrender.com
```

**Subdomain (crm.arkatos.com):**
```
Type:  CNAME
Name:  crm
Value: yourapp.onrender.com
```

---

## Security Considerations

1. **Verification Required** - Domains must be verified via TXT record before use
2. **Unique Domains** - Each domain can only be registered once
3. **SSL Enforcement** - Only active SSL domains are used for routing
4. **Reserved Subdomains** - Block reserved names (www, mail, api, etc.)

---

## For arkatos.com Specifically

To set up `crm.arkatos.com`:

1. **In Mercura Dashboard:**
   - Go to Settings → Custom Domain
   - Enter: `crm.arkatos.com`
   - Click Register

2. **In Cloudflare (arkatos.com DNS):**
   ```
   Type:  CNAME
   Name:  crm
   Value: your-render-app.onrender.com
   Proxy: Enabled (orange cloud)
   
   Type:  TXT
   Name:  _mercura
   Value: mercura-verify=<token-from-dashboard>
   ```

3. **Back in Mercura:**
   - Click "Verify Domain"
   - Wait for SSL provisioning (automatic with Cloudflare proxy)
   - Done!

---

## Support

For custom domain issues:
- Check DNS propagation: https://whatsmydns.net
- Verify records: `dig yourdomain.com ANY`
- Contact: support@openmercura.com
