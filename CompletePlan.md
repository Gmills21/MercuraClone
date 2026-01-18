# Complete Plan: Ship a Usable Mercura Product Fast (Closing the Competitor Gap Pragmatically)

## 0) What “Usable” Means (North-Star Demo)

In one sitting, a distributor can:
1. Forward a messy RFQ email (PDF/images/Excel) to our inbound address.
2. See extracted line items appear in the dashboard in minutes.
3. Review suggested product matches from their catalog (or leave unmatched).
4. Generate a draft quote (web + Excel/PDF export) and send it to the customer.

This gets us to “saleable” without the heaviest competitor pieces (full ERP injection, real-time inventory, margin optimization).

---

## 1) Product Positioning for Fast Sales

### Primary Wedge (what we sell first)
“Email-In → Draft Quote + Spreadsheet Out” for industrial/construction distributors.
- Faster than manual quoting.
- Structured outputs that plug into existing workflows even without ERP integration.

### Non-goals for the first saleable product
- Full ERP quote injection (SAP/Oracle/NetSuite/Epicor).
- Bi-directional stock/pricing sync.
- Sophisticated semantic SKU matching (vector search / embeddings).
- Automated profitability substitutions and margin guardrails.

---

## 2) Current Strengths to Lean On (Already in the Repo)

We already have:
- Inbound email webhooks + attachment handling + Gemini extraction + Supabase storage.
- Data query endpoints + exports (CSV/Excel/Google Sheets).
- A basic web UI (customers/products/quotes) and DB tables for quotes, customers, quote_items.

The fastest path is to connect these into a single workflow rather than inventing new systems.

---

## 3) The Gap (What the Competitor Has That We’ll Defer or “Lite”)

### Competitor “big rocks”
1. SKU mapping + competitor cross-reference + validation.
2. ERP injection + stock/pricing sync.
3. Profit optimization suggestions.

### Our strategy
- Build “Lite” versions that unlock real user value:
  - Assisted matching (suggestions + human approval) instead of perfect automation.
  - Exportable quote formats (Excel/PDF/CSV + email send) instead of ERP injection.
  - Simple rules/alerts (price variance, missing SKU) instead of full profitability AI.

---

## 4) MVP Scope (Ship Fast, Broad Utility)

### MVP User Journey (end-to-end)
1. Inbound email received.
2. Attachments extracted into normalized line items.
3. A “Draft Quote” is automatically created from the extracted items.
4. User opens the Draft Quote review screen:
   - Accept/edit each extracted line item.
   - Optional: select a matched catalog item (or leave unmatched).
   - Optional: edit unit price/qty/description.
5. Click “Generate Quote”:
   - Quote saved + downloadable Excel/PDF generated.
   - Optional: email quote back to requester (simple outbound email).

### What we will support in MVP inputs
- PDF + image attachments (already supported).
- Plain email body (already supported).
- Excel attachments: support via a simple approach:
  - If we can read it reliably with Pandas, extract table(s) to text and send to Gemini.
  - If not, treat as a binary attachment and prompt Gemini with best-effort instructions.

### What we will support in MVP outputs
- Quote view in web UI.
- Excel export (high value for users).
- Optional: PDF export (nice-to-have, can be Phase 1.5).
- Optional: email quote out (Phase 1.5).

---

## 5) Phased Roadmap (Fastest Path to Saleable)

### Phase 1 (Days 1–7): Connect Ingestion → Draft Quote
**Goal:** Every processed inbound email becomes a reviewable Draft Quote.

Deliverables:
- Create/extend DB flow so inbound email processing can create a Quote + QuoteItems.
- Add a “Processed Emails” and “Draft Quotes from Emails” view in the UI.
- Add a single review screen that shows:
  - Extracted items (item_name/description/qty/unit/total/confidence)
  - Editable fields
  - “Approve and Save Draft Quote”

Exit criteria:
- Forward an RFQ PDF → see a draft quote with line items within minutes.
- User can edit line items and save.

What we defer:
- Matching, PDF output, email send-back.

---

### Phase 2 (Days 8–14): Assisted Matching (No Vector Search)
**Goal:** Make drafts “usable” by linking line items to the user’s catalog with suggestions.

Deliverables:
- Catalog import:
  - Upload CSV/XLSX (or paste) to populate the catalogs table.
- Suggestion engine (lite):
  - Match extracted line items against catalog by:
    - SKU exact/substring match (if line contains token resembling SKU).
    - Normalized token overlap on item name.
    - Simple heuristics (remove punctuation, case-fold, strip units).
  - Return top N suggestions with a score.
- Review screen enhancements:
  - Suggested catalog matches dropdown.
  - “Set all best matches” button.
  - Highlight items with low confidence or no match.

Exit criteria:
- For a seeded catalog, most common line items get a reasonable suggestion.
- A user can finish a usable quote without manual product hunting.

What we defer:
- Competitor cross-reference automation.
- Inventory validation.

---

### Phase 3 (Weeks 3–4): Quote Outputs + Basic Workflow Automation
**Goal:** Make “sendable quotes” a one-click outcome.

Deliverables:
- Quote export formats:
  - Excel template formatting (consistent columns, totals, customer details).
  - PDF generation (if feasible; otherwise keep Excel as primary).
- Outbound email send:
  - Send the exported quote to the requester or selected customer email.
  - Add simple email templates.
- Audit trail:
  - Quote status transitions (draft → sent).
  - Link quote back to inbound email for traceability.

Exit criteria:
- A user can produce a customer-ready file and email it from Mercura.

---

### Phase 4 (Weeks 5–8): “Lite” Versions of the Competitor’s Biggest Differentiators
**Goal:** Capture “ERP-like” value without ERP integrations.

Deliverables:
- Competitor cross-reference (manual-first):
  - Import a mapping file (competitor_sku → our_sku).
  - Apply mapping during suggestion.
- Validation rules:
  - Flag big variances vs expected_price.
  - Flag missing pricing.
  - Flag unusually high quantities.
- Simple margin guardrails (manual inputs):
  - Store cost and price in catalog; show margin %; warn if below threshold.

Exit criteria:
- More quotes require less judgment; errors get flagged early.

What we still defer:
- True ERP injection and real-time inventory.

---

### Phase 5 (Later): ERP Integrations (Only After Strong Pull)
**Goal:** If customers demand it and we have repeatable patterns, build ERP adapters.

Approach:
- Start with “file-based integration” (export that ERPs can import) before APIs.
- Add 1 ERP integration at a time with a tight scope:
  - Create quote draft, not full lifecycle automation.

---

## 6) Engineering Workstreams (How We Build It Fast)

### A) Data Model & Traceability
Add/ensure:
- inbound_email_id on quotes (or metadata link) so every quote ties back to an email.
- quote_items store:
  - original extracted text fields
  - selected catalog product_id (optional)
  - confidence + match score (optional)

### B) Pipeline Orchestration
Update inbound processing so it can:
- Extract items
- Persist them
- Create a draft quote automatically
- Mark success/failure clearly for UI visibility

### C) Matching (Lite, deterministic, no embeddings)
Implement:
- Normalization functions (lowercase, strip punctuation, remove stopwords/units)
- Scoring:
  - exact SKU hit > partial SKU > name token overlap
- Return top N results

### D) UI (Single “Review” Screen)
Build the UI around one primary workflow:
- Inbox/Email list → Open → Review items → Save draft → Export/Send

### E) Reliability & Cost Controls
Ship with:
- Clear failure modes (partial extraction, attachment errors)
- Idempotency (avoid creating duplicate quotes for the same email)
- Quota limits (already exists at user level)

---

## 7) Milestones & Timeline (Aggressive, Sale-Focused)

### Next 48 hours
- Make inbound email processing create a Draft Quote automatically.
- Add a basic UI page to review that quote and edit items.
- Ensure Excel export works for that quote.

### End of Week 1
- “Forward email → draft quote visible + editable + exportable.”
- Demo-ready for customer calls.

### End of Week 2
- Catalog import + assisted matching suggestions.
- Demo: “Forward RFQ → mostly matched draft quote.”

### End of Week 4
- Email sending + stronger exports + quote lifecycle.
- Usable daily by a small team.

---

## 8) What We Will Say “No” To (So We Ship)

Until we have strong customer pull, we will not:
- Build ERP connectors.
- Build vector search / embeddings matching.
- Build profit optimization AI.
- Build deep analytics dashboards beyond “processed emails + quotes list.”

---

## 9) Risks & Mitigations

### Risk: Extraction quality varies by document type
Mitigation:
- Add a “human review required” first-class workflow.
- Keep outputs editable and fast to correct.
- Track confidence and highlight low-confidence rows.

### Risk: Matching without embeddings isn’t “smart enough”
Mitigation:
- Prioritize importable catalogs and manual overrides.
- Make it easy to select a product and remember that choice.
- Add “cross-reference import” before heavy ML.

### Risk: Users want ERP integration immediately
Mitigation:
- Offer file-based exports + email send as the bridge.
- Only build ERP adapters after 2–3 customers request the same ERP path.

---

## 10) Success Metrics (Early Sales Reality)

For a pilot customer:
- Time-to-first-quote: under 10 minutes from setup.
- RFQ → draft quote: under 5 minutes median.
- “Usable draft rate”: % of drafts that require only light edits (target 60%+ early).
- “Send rate”: % of drafts exported/sent (target 30%+ in first week of use).

---

## 11) Definition of Done (Saleable v1)

We can confidently sell v1 when:
- At least 1 customer can process real RFQs daily.
- They can export/send quotes without leaving Mercura.
- The system is stable enough to trust (clear errors, minimal retries, no data loss).

