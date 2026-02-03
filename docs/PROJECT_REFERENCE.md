# Project Reference: "Auto-Ingest Lite" (MVP)

## 1. The Core Mission
To build a lightweight, automated pipeline that receives unstructured data (emails, messy PDFs, handwritten notes) and instantly converts it into structured spreadsheets (CSV/Excel).

**Primary Goal:** Reduce manual data entry time by 90% for construction/industrial companies.
**Value Prop:** Speed (30-second turnaround), "Fat Finger" elimination (zero typos), and removing the "context switching" tax for office managers.

## 2. Current Phase: "The Sales-Ready MVP"
We are currently building the Lite Version.
- **Focus:** Immediate utility. Prove we can read "messy" handwriting.
- **Constraint:** NO Vector Search or complex SKU matching yet. We rely 100% on the AI's "common sense" to read and categorize data.
- **Architecture Strategy:** Simple, stateless, and low-cost.

## 3. The Tech Stack (Non-Negotiable)
Agents must strictly adhere to these components:
- **Ingestion:** SendGrid Inbound Parse or Mailgun Routes (Receives Email → POSTs JSON to server).
- **Intelligence:** Google Gemini 1.5 Flash (API).
  - Why: Lowest cost, massive context window, and native multimodal (vision) capabilities for reading images/PDFs.
- **Database:** Supabase (PostgreSQL).
  - Tables: inbound_emails, extracted_data, users.
- **Processing & Output:** Python (Backend) + Pandas (Data transformation/Export).
- **Output Format:** Downloadable CSV/Excel link or Google Sheets sync.

## 4. System Architecture Flow
1. **Trigger:** User sends/forwards an email (with body text or attachment) to bot@domain.com.
2. **Parse:** Email provider converts email to JSON and hits our Webhook.
3. **Extract:** Python server sends the raw text + image bytes to Gemini 1.5 Flash.
4. **Prompt Logic:** "Extract items, quantity, price. If handwriting is unclear, infer from context. Categorize generic items (e.g., 'hammer' → 'Tools')."
5. **Store:** Clean JSON is saved to Supabase extracted_data table.
6. **Deliver:** System generates a CSV/Excel file using Pandas and emails it back to the user (or updates their Google Sheet).

## 5. Decision-Making Guidelines for Agents
When generating code or answering questions, Agents must follow these rules:
- **Rule 1 (The "Lite" Rule):** Do not suggest pgvector, embeddings, or RAG (Retrieval-Augmented Generation) unless explicitly asked. We are reading data, not matching SKUs (yet).
- **Rule 2 (The "Messy" Rule):** Always assume inputs will be dirty. Code must handle "None" values, weird date formats, and spelling errors gracefully.
- **Rule 3 (Cost Efficiency):** Prioritize Gemini 1.5 Flash over Pro. We need speed and low cost, not deep reasoning.
- **Rule 4 (Formatting):** The final output (Excel) is the "product." It must be formatted perfectly (currency columns as numbers, dates as ISO).

## 6. The "Future State" (For Context Only)
Eventually, this project will evolve into an Enterprise ERP connector that uses Vector Search to match "red hammer" to specific Internal SKU codes. However, we are NOT building this yet.

---

**IMPORTANT FOR ALL AGENTS:**
- This file is a mandatory reference for all future code generation, analysis, and Q&A.
- Agents must review and adhere to these guidelines before making any changes or answering any questions about this project.
- If you are an AI agent, you must check this file every time you analyze, answer, or implement code for this project.
