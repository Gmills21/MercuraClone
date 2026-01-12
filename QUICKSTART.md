# Mercura - Automated Email-to-Data Pipeline

A production-ready system for extracting structured data from emails and attachments.

## Quick Start Guide

### 1. Prerequisites

- Python 3.9 or higher
- Supabase account ([supabase.com](https://supabase.com))
- Google Cloud account with Gemini API access
- SendGrid or Mailgun account

### 2. Installation

```bash
# Clone or navigate to the project directory
cd "c:\Users\graha\Mercura Clone"

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
copy .env.example .env

# Edit .env with your credentials
notepad .env
```

**Required Environment Variables:**

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Gemini
GEMINI_API_KEY=your-gemini-api-key

# Email Provider (choose one)
EMAIL_PROVIDER=sendgrid  # or mailgun

# SendGrid
SENDGRID_WEBHOOK_SECRET=your-webhook-secret
SENDGRID_INBOUND_DOMAIN=inbound.yourdomain.com

# OR Mailgun
MAILGUN_API_KEY=your-api-key
MAILGUN_WEBHOOK_SECRET=your-webhook-secret
MAILGUN_DOMAIN=mg.yourdomain.com
```

### 4. Database Setup

```bash
# Generate database schema file
python scripts/init_db.py

# This creates database_schema.sql
# Execute this SQL in your Supabase Dashboard > SQL Editor
```

### 5. Run the Application

```bash
# Development mode
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 6. Test the System

```bash
# Test Gemini extraction
python tests/test_extraction.py
```

### 7. Configure Email Provider

#### For SendGrid:

1. Go to SendGrid Dashboard > Settings > Inbound Parse
2. Add your domain and point MX records to SendGrid
3. Set webhook URL to: `https://your-domain.com/webhooks/inbound-email`
4. Copy the webhook verification key to `.env`

#### For Mailgun:

1. Go to Mailgun Dashboard > Receiving > Routes
2. Create a new route
3. Set action to forward to: `https://your-domain.com/webhooks/inbound-email`
4. Copy the webhook signing key to `.env`

## API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key Endpoints

### Webhooks
- `POST /webhooks/inbound-email` - Receive emails from SendGrid/Mailgun

### Data Queries
- `GET /data/emails` - List all emails
- `GET /data/emails/{id}` - Get email details with line items
- `GET /data/line-items` - Query line items
- `GET /data/stats` - Get processing statistics

### Exports
- `POST /export/csv` - Export to CSV
- `POST /export/excel` - Export to Excel
- `POST /export/google-sheets` - Sync to Google Sheets

## Usage Example

### 1. Send an Email

Forward an invoice to your configured email address:
```
To: invoices@inbound.yourdomain.com
Subject: Invoice from Acme Corp
Attachment: invoice.pdf
```

### 2. Check Processing Status

```bash
curl http://localhost:8000/data/emails
```

### 3. Export Data

```bash
curl -X POST http://localhost:8000/export/csv \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z"
  }' \
  --output export.csv
```

## Project Structure

```
mercura/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models.py            # Data models & DB schema
│   ├── database.py          # Supabase client
│   ├── routes/
│   │   ├── webhooks.py      # Email webhook handlers
│   │   ├── data.py          # Data query endpoints
│   │   └── export.py        # Export endpoints
│   └── services/
│       ├── gemini_service.py    # AI extraction
│       └── export_service.py    # Data export
├── scripts/
│   └── init_db.py           # Database initialization
├── tests/
│   └── test_extraction.py   # Unit tests
├── requirements.txt
├── .env.example
└── README.md
```

## Features

✅ **Email Processing**
- SendGrid & Mailgun support
- Webhook signature verification
- Attachment handling (PDF, PNG, JPG)

✅ **AI Extraction**
- Gemini 1.5 Flash integration
- Support for invoices, purchase orders, catalogs
- Confidence scoring

✅ **Data Storage**
- Supabase PostgreSQL
- Row-level security
- Efficient indexing

✅ **Export Options**
- CSV with formatting
- Excel with styling
- Google Sheets sync

✅ **API Features**
- RESTful endpoints
- Interactive documentation
- CORS support

## Troubleshooting

### Database Connection Issues
```bash
# Verify Supabase credentials
python -c "from app.database import db; print('Connected!')"
```

### Gemini API Errors
```bash
# Test Gemini connection
python tests/test_extraction.py
```

### Webhook Not Receiving Emails
1. Check MX records are configured correctly
2. Verify webhook URL is publicly accessible
3. Check webhook signature verification
4. Review logs: `tail -f logs/mercura.log`

## Next Steps

1. **Add Authentication**: Implement API key authentication
2. **Rate Limiting**: Add request throttling
3. **Monitoring**: Set up error tracking (Sentry)
4. **Catalog Validation**: Compare extracted data against master catalog
5. **Web Dashboard**: Build frontend UI for data management

## Support

For issues or questions:
- Check the logs in `logs/mercura.log`
- Review API docs at `/docs`
- Ensure all environment variables are set correctly

## License

MIT License - See LICENSE file for details
