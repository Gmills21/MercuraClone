# Test Materials for OpenMercura

This folder contains real-world sample materials for testing the OpenMercura CRM features.

## Folder Structure

```
test_materials/
├── REAL_TEST_MATERIALS.md    # Overview of all test materials
├── product_docs/             # Sample product documentation
│   ├── ball_valves.txt      # Technical specs (from Wikipedia/open sources)
│   ├── pipe_fittings.txt    # Technical specs (from Wikipedia/open sources)
│   └── pricing_sheet_acme.txt  # Example distributor pricing sheet
```

## How to Use

### 1. Smart Quote Extraction Testing

**Test Files:** `REAL_TEST_MATERIALS.md` (Examples A through G)

Copy and paste the RFQ email examples into the Smart Quote feature:
```
1. Go to /quotes/new
2. Paste example email text
3. Click "Extract Quote"
4. Verify customer name, items, quantities extracted
```

**What to Test:**
- Customer name extraction
- Line item parsing (product, quantity, specs)
- Delivery location detection
- Deadline identification
- Contact info extraction

### 2. Knowledge Base Testing

**Test Files:** `product_docs/*.txt`

Upload these to the Knowledge Base:
```
1. Go to /knowledge
2. Click "Add Document"
3. Upload ball_valves.txt as "spec_sheet"
4. Upload pricing_sheet_acme.txt as "pricing"
5. Upload pipe_fittings.txt as "catalog"
6. Ask questions like:
   - "What is the price of a 2-inch stainless steel ball valve?"
   - "What are the pressure ratings for ball valves?"
   - "What's the difference between schedule 40 and schedule 80?"
```

**What to Test:**
- Document ingestion
- Natural language queries
- Source attribution
- Confidence scoring
- Multiple document types

### 3. Camera Capture Testing

**Test Method:**
1. Print RFQ examples from REAL_TEST_MATERIALS.md
2. Take photo with phone
3. Upload via Camera Capture feature
4. Verify OCR + AI extraction works

**Or:** Take screenshot of email and upload image

### 4. Customer Intelligence Testing

**Test Method:**
1. Create multiple quotes using test materials
2. Assign to different test customers
3. Check Intelligence Dashboard for:
   - Health scores
   - Win rate calculations
   - Activity patterns

## Real vs. Synthetic Data

| Source | Type | Status |
|--------|------|--------|
| mails.ai/blog | RFQ Templates | Real (publicly available) |
| instantly.ai | RFQ Templates | Real (publicly available) |
| responsive.io | RFQ Structure | Real (procurement site) |
| Wikipedia | Product Specs | Real (open license) |
| Compiled | Pricing Sheet | Realistic (based on industry patterns) |

## Missing Materials (Could Not Find Online)

**Product Catalogs:**
- Major distributors (McMaster-Carr, Grainger) only provide PDFs or protected web catalogs
- Cannot extract text via web fetch
- **Solution:** Download PDFs directly from manufacturer websites and use OCR

**Spec Sheets:**
- Manufacturer datasheets are typically PDFs
- **Solution:** Contact local distributors for sample PDFs

## Adding Your Own Test Materials

1. **RFQ Emails:** Save actual emails from your customers (with permission)
2. **Product Docs:** Ask suppliers for sample catalogs
3. **Pricing Sheets:** Use your own distributor pricing
4. **Spec Sheets:** Download from manufacturer websites

## Recommended Additional Testing

### Real Documents to Obtain:
1. **McMaster-Carr catalog** (download PDF, OCR it)
2. **Local distributor price list** (ask your suppliers)
3. **Manufacturer spec sheets** (download from Velan, Crane, etc.)
4. **Actual customer RFQs** (with customer permission)

### Create These for Edge Case Testing:
1. **Handwritten RFQ** (for camera capture testing)
2. **Damaged/poor quality scan** (test OCR limits)
3. **Multi-page RFQ** (test pagination handling)
4. **RFQ with tables** (test table extraction)
5. **Non-English RFQ** (if supporting international)

## Validation Checklist

### Smart Quote Extraction:
- [ ] Extracts customer name correctly
- [ ] Identifies all line items
- [ ] Parses quantities accurately
- [ ] Detects delivery location
- [ ] Identifies deadline/date
- [ ] Extracts contact information
- [ ] Handles various formats

### Knowledge Base:
- [ ] Documents ingest without error
- [ ] Queries return relevant answers
- [ ] Sources are properly cited
- [ ] Confidence scores are reasonable
- [ ] Handles multiple document types
- [ ] Gracefully handles disabled state

### Camera Capture:
- [ ] OCR reads printed text
- [ ] OCR reads computer screenshots
- [ ] AI extracts structured data
- [ ] Handles different lighting
- [ ] Handles different angles

---

**Last Updated:** 2026-01-31
**Status:** Ready for testing
