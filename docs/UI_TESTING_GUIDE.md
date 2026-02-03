# OpenMercura - UI Testing Guide
## For Manual Testing via Web Interface

---

## 🚀 START THE SERVER

### Step 1: Open PowerShell

### Step 2: Navigate to project
```powershell
cd C:\Users\graha\MercuraClone
```

### Step 3: Set environment variables
```powershell
$env:OPENROUTER_API_KEY="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"
$env:KNOWLEDGE_BASE_ENABLED="true"
```

### Step 4: Start the server
```powershell
C:\Python38\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**You should see:**
```
INFO:     Started server process
INFO:     Waiting for application startup
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Open the app

**Backend API:** http://localhost:8000/docs (Swagger UI for testing)

**Frontend:** http://localhost:5173 (if you run `npm run dev` in frontend folder)

---

## 🧪 FEATURES TO TEST

### 1. SMART QUOTE EXTRACTION

**What to test:**
- Pasting RFQ text and extracting structured data
- Creating quotes from extracted data

**How to test:**

**Via Swagger UI:**
1. Go to http://localhost:8000/docs
2. Find `POST /extract/`
3. Click "Try it out"
4. Enter this test text:
```
Subject: RFQ for Construction Materials

Hi, I need a quote for the following:
- 500 cubic yards concrete, 3000 PSI
- 200 pieces rebar #4, 20-foot lengths
- 1000 pieces 2x4x8 lumber

Delivery to: 123 Main St, Cleveland, OH
Need by: March 15th

Thanks,
John Smith
ABC Construction
john@abc.com
```
5. Set `source_type` to "email"
6. Click "Execute"

**Expected result:**
- `success: true`
- `customer_name: "John Smith"` or "ABC Construction"
- `line_items` array with 3 items
- `confidence` score (0.0-1.0)

**Test 2: Create Quote**
1. Find `POST /extract/create-quote`
2. Use same text
3. Click "Execute"
4. **Expected:** Returns a quote object with items

---

### 2. KNOWLEDGE BASE QUERIES

**What to test:**
- Asking questions about NITRA cylinders (already in KB)
- Getting accurate answers with sources

**How to test:**

**Via Swagger UI:**

**Test 1: Check KB Status**
1. Find `GET /knowledge/status`
2. Click "Try it out" → "Execute"
3. **Expected:** 
   - `enabled: true`
   - `available: true`
   - `document_count: 581` (NITRA cylinders)

**Test 2: Quick Ask**
1. Find `POST /knowledge/ask`
2. Click "Try it out"
3. Enter question: `What is the pressure rating for NITRA cylinders?`
4. Click "Execute"
5. **Expected:**
   - `answer` contains "250 PSI" or similar
   - `confidence` > 0.4
   - `has_sources: true`

**Test 3: Detailed Query**
1. Find `POST /knowledge/query`
2. Enter: `What bore sizes do NITRA cylinders come in?`
3. Set `use_ai: true`
4. **Expected:**
   - Answer lists bore sizes: 7/16", 9/16", 3/4", etc.
   - `sources` array shows where info came from
   - `query_time_ms` shows speed

**Test 4: Pricing Question**
1. Question: `How much is a 7/16 inch bore cylinder?`
2. **Expected:** Price around $19-23

---

### 3. UPLOAD NEW DOCUMENT

**What to test:**
- Uploading AutomationDirect catalog (57MB)
- Page-by-page processing works
- Querying uploaded document

**How to test:**

**Via Swagger UI:**

**Test 1: Upload PDF**
1. Find `POST /knowledge/ingest`
2. Click "Try it out"
3. For `file`: Click "Choose File"
4. Select: `test_materials/AutomationDirect-Summary.pdf`
5. Set `doc_type`: `catalog`
6. Click "Execute"
7. **Expected:**
   - `success: true`
   - `pages_processed`: 27+
   - `chunks_created`: 100+ (depends on content)
   - Watch server logs for progress every 10 pages

**Test 2: Query Uploaded Doc**
1. Wait for upload to complete
2. Find `POST /knowledge/query`
3. Question: `What products does AutomationDirect sell?`
4. **Expected:** Lists PLCs, VFDs, motors, etc.

**Test 3: Phone Number Query**
1. Question: `What is AutomationDirect's phone number?`
2. **Expected:** "1-800-633-0405"

---

### 4. CAMERA CAPTURE (OCR)

**What to test:**
- Uploading image of RFQ
- OCR extraction

**How to test:**

**Prerequisites:** Install Tesseract OCR
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to `C:\Program Files\Tesseract-OCR`
3. Add to PATH

**Test via Swagger UI:**
1. Find `POST /extract/`
2. Instead of text, use `file` parameter
3. Upload an image of text (screenshot or photo)
4. **Expected:** Extracted text in response

**Note:** Without Tesseract installed, this will return error "OCR not available"

---

### 5. QUICKBOOKS (If Configured)

**What to test:**
- Connection status
- OAuth flow (requires QB credentials)

**How to test:**

1. Find `GET /quickbooks/status`
2. Click "Try it out" → "Execute"
3. **Expected:** `connected: false` (unless you've connected)

**Note:** Full QuickBooks testing requires:
- QB_CLIENT_ID and QB_CLIENT_SECRET set
- OAuth callback configured

---

### 6. CUSTOMER INTELLIGENCE

**What to test:**
- Health scores
- Customer insights

**How to test:**

1. First create some quotes via Smart Quote
2. Find `GET /intelligence/customers`
3. Click "Execute"
4. **Expected:** List of customers with health scores

---

### 7. BUSINESS IMPACT

**What to test:**
- Time savings calculations
- ROI metrics

**How to test:**

1. Create several quotes first
2. Find `GET /impact/dashboard`
3. Click "Execute"
4. **Expected:**
   - `time_saved_hours`
   - `roi_percentage`
   - `quotes_created`

---

## 📊 TEST CHECKLIST

### Smart Quote
- [ ] Text extraction works
- [ ] Customer name extracted
- [ ] Items/quantities extracted
- [ ] Quote creation works
- [ ] Confidence score > 0.5

### Knowledge Base
- [ ] KB status shows 581 documents
- [ ] Query "NITRA pressure rating" → 250 PSI
- [ ] Query "bore sizes" → list of sizes
- [ ] Upload AutomationDirect PDF succeeds
- [ ] Query uploaded doc works

### Camera/OCR
- [ ] Image upload accepts file
- [ ] OCR extracts text (if Tesseract installed)

### QuickBooks
- [ ] Status endpoint works
- [ ] (Optional) OAuth flow works

### Intelligence
- [ ] Customer health scores display
- [ ] Business impact metrics show

---

## 🐛 TROUBLESHOOTING

**Server won't start:**
```powershell
# Check errors
C:\Python38\python.exe -c "from app.main import app"

# Check dependencies
C:\Python38\python.exe -c "import chromadb; import sentence_transformers; print('OK')"
```

**KB queries fail:**
- Check KB enabled: `GET /knowledge/status`
- Verify documents ingested

**Smart Quote returns low confidence:**
- Try more detailed RFQ text
- Check OpenRouter key is set

**OCR not working:**
- Install Tesseract OCR
- Add to system PATH
- Restart server

---

## 🎯 QUICK TEST SEQUENCE

1. **Start server** (see section above)
2. **Open Swagger:** http://localhost:8000/docs
3. **Test Smart Quote:** POST /extract/ with sample RFQ
4. **Test KB Query:** POST /knowledge/ask with "What pressure rating for NITRA cylinders?"
5. **Test Upload:** POST /knowledge/ingest with AutomationDirect PDF
6. **Test New Query:** Ask about uploaded document

---

## 📁 TEST FILES LOCATION

```
C:\Users\graha\MercuraClone\test_materials\
├── Battery.pdf (4 pages)
├── AutomationDirect-Summary.pdf (57MB catalog)
├── NPC-Nitra-Pneumatic-Cylinders.pdf (already in KB)
└── product_docs\
    ├── ball_valves.txt
    ├── pipe_fittings.txt
    └── pricing_sheet_acme.txt
```

---

## ✨ WHAT SUCCESS LOOKS LIKE

**Smart Quote:**
```json
{
  "success": true,
  "confidence": 0.85,
  "structured_data": {
    "customer_name": "ABC Construction",
    "line_items": [
      {"item_name": "Concrete", "quantity": 500},
      {"item_name": "Rebar #4", "quantity": 200}
    ]
  }
}
```

**KB Query:**
```json
{
  "answer": "NITRA cylinders have a pressure rating of 250 PSI",
  "confidence": 0.92,
  "sources": [
    {"source": "NPC-Nitra-Pneumatic-Cylinders.pdf", "page": 5}
  ]
}
```

---

**Ready to test! Start the server and open http://localhost:8000/docs**
