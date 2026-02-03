# Testing Instructions for OpenMercura

## Server Status: STARTING

### API Key Configured: ✅
OpenRouter API key set for AI features

---

## How to Test

### 1. Start the Server (if not already running)

In PowerShell:
```powershell
cd C:\Users\graha\MercuraClone
$env:OPENROUTER_API_KEY="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"
$env:KNOWLEDGE_BASE_ENABLED="true"
C:\Python38\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 2. Access the Application

Once server starts:
- **Frontend:** http://localhost:5173 (if running separately)
- **API Docs:** http://localhost:8000/docs
- **API Base:** http://localhost:8000

---

## Features to Test

### ✅ SMART QUOTE

**Test 1: Text Extraction**
```
POST http://localhost:8000/extract/
Content-Type: multipart/form-data

text: Subject: RFQ for 50 office chairs
      Need quote for 50 chairs, delivery to 123 Main St
      Contact: john@example.com

source_type: email
```

**Expected:** Extracts customer, items, quantities

**Test 2: Create Quote from Text**
```
POST http://localhost:8000/extract/create-quote

text: [paste RFQ email]
customer_id: [optional]
```

---

### ✅ KNOWLEDGE BASE

**Test 1: Check Status**
```
GET http://localhost:8000/knowledge/status
```

**Test 2: Upload Document**
```
POST http://localhost:8000/knowledge/ingest
Content-Type: multipart/form-data

file: [select PDF - AutomationDirect-Summary.pdf]
doc_type: catalog
supplier: AutomationDirect
```

**Test 3: Query**
```
POST http://localhost:8000/knowledge/query

question: What is the pressure rating for NITRA cylinders?
use_ai: true
```

**Test 4: Quick Ask**
```
POST http://localhost:8000/knowledge/ask

question: What bore sizes do NITRA cylinders have?
```

---

### ✅ CAMERA CAPTURE (if OCR installed)

**Test:**
```
POST http://localhost:8000/extract/
Content-Type: multipart/form-data

file: [upload photo of RFQ]
```

**Note:** Requires pytesseract + Tesseract OCR installed

---

### ✅ QUICKBOOKS (if configured)

**Test:**
```
GET http://localhost:8000/quickbooks/status
```

---

## Test Materials Available

| File | Location | Use For |
|------|----------|---------|
| Battery.pdf | test_materials/ | KB upload test |
| AutomationDirect-Summary.pdf | test_materials/ | Large PDF test (57MB) |
| NPC-Nitra-Pneumatic-Cylinders.pdf | .openclaw/ | Already in KB |
| ball_valves.txt | test_materials/product_docs/ | Text upload |
| pricing_sheet_acme.txt | test_materials/product_docs/ | Pricing query |

---

## API Testing with curl

### Example 1: Extract RFQ
```bash
curl -X POST http://localhost:8000/extract/ \
  -F "text=Need quote for 25 ball valves, 2 inch, stainless steel" \
  -F "source_type=email"
```

### Example 2: Query KB
```bash
curl -X POST http://localhost:8000/knowledge/ask \
  -F "question=What pressure rating for NITRA cylinders?"
```

### Example 3: Upload PDF
```bash
curl -X POST http://localhost:8000/knowledge/ingest \
  -F "file=@test_materials/Battery.pdf" \
  -F "doc_type=manual"
```

---

## Expected AI Behavior

With OpenRouter API key set:
- Smart Quote uses AI for better extraction
- KB queries get AI-synthesized answers
- Confidence scores should be higher
- Responses more natural/conversational

---

## Troubleshooting

**If server won't start:**
```powershell
# Check dependencies
C:\Python38\python.exe -c "import chromadb; import sentence_transformers; print('OK')"

# Check API key
$env:OPENROUTER_API_KEY
```

**If KB queries fail:**
- Check KB enabled: `GET /knowledge/status`
- Verify documents ingested

**If Smart Quote fails:**
- Check API key is set
- Test with simple text first

---

## Quick Test Sequence

1. Start server (see above)
2. Open http://localhost:8000/docs
3. Try `/extract/` with sample RFQ text
4. Try `/knowledge/status` to check KB
5. Try `/knowledge/ask` with question
6. Upload a PDF via `/knowledge/ingest`
7. Query the uploaded document

---

**Server Ready for Testing!**
