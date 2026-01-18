# Product Definition Reference (PDR): Mercura

**Status:** Live (YC W25)
**Vertical:** B2B SaaS / Industrial AI
**Focus:** Construction Supply Chain Automation
**Core Function:** Automated RFQ-to-Quote Processing

---

## 1. Executive Summary
Mercura is an AI-powered automation platform designed for distributors and manufacturers in the construction, HVAC, plumbing, and electrical industries. It automates the manual "RFQ-to-Quote" process by analyzing unstructured customer requests (emails, PDFs, blueprints) and instantly drafting accurate, inventory-matched quotes directly inside the company’s ERP system.

**Mission:** To bring AI to the backbone of the economy, enabling industrial sales teams to process quotes in minutes rather than days.

---

## 2. Problem Statement: The "Unstructured Data" Bottleneck
Contractors send Requests for Quotes (RFQs) in non-standard formats—scanned PDF blueprints, messy Excel sheets, or forwarded email chains—creating significant friction for distributors.

* **Manual Labor:** Inside sales reps spend 70%+ of their time manually transcribing data.
* **Slow Turnaround:** Quoting takes days, resulting in lost bids (contractors buy from the fastest responder).
* **Human Error:** Mismatching part numbers leads to costly returns and logistics errors.
* **Catalog Complexity:** Finding exact equivalents for competitor part numbers relies heavily on tribal knowledge.

---

## 3. User Personas

| Persona | Role | Core Pain Point | Product Goal |
| :--- | :--- | :--- | :--- |
| **Inside Sales Rep** | Processes incoming RFQs. | Buried in data entry; hates manual lookups. | Wants "One-click" quoting to focus on selling. |
| **Sales Manager** | Oversees team performance. | Low visibility into lost bids & team efficiency. | Wants higher quote volume & faster turnaround. |
| **IT / ERP Admin** | Manages backend systems. | Fears data corruption & integration fatigue. | Needs secure, seamless ERP data injection. |

---

## 4. Solution Architecture & User Journey
Mercura acts as an intelligent layer between customer communication and the distributor's ERP.

### Step 1: Ingestion ("Reading")
* **Input:** Accepts PDFs, Excel files, Word docs, Email bodies, and Blueprints.
* **Action:** OCR and LLMs analyze documents to identify purchasing intent.

### Step 2: Extraction & Structuring
* **Logic:** Identifies line items, quantities, units of measure, and delivery dates.
* **Normalization:** Converts messy text (e.g., "100 ft of 1/2 inch copper pipe") into structured data.

### Step 3: Intelligent Matching ("The Brain")
* **Catalog Mapping:** Maps requested items to the distributor's specific **SKU/Part Number**.
* **Cross-Referencing:** Finds functional equivalents for competitor part numbers.
* **Validation:** Checks stock levels and flags special procurement items.

### Step 4: ERP Injection
* **Output:** Creates a draft quote in the ERP (SAP, Oracle, NetSuite, Epicor).
* **Review:** Sales rep reviews the draft, approves matches, and sends the quote.

---

## 5. Functional Requirements

### Core Modules
* **Smart Ingestion Engine:** Capable of handling multi-page PDFs with mixed tables/text.
* **Semantic Search:** Understands industry jargon (e.g., "sheetrock" = "drywall").
* **Competitor Cross-Reference Database:** Internal library linking competitor SKUs to user inventory.
* **One-Click ERP Sync:** Bi-directional sync for real-time pricing and stock checks.
* **Profitability Guardrails:** AI suggestions to swap low-margin items for high-margin alternatives.

---

## 6. Success Metrics (KPIs)
* **Turnaround Time:** Reduction from **2 days → <15 minutes**.
* **Volume per Rep:** Increase quote volume by **2-3x**.
* **Line Item Accuracy:** >90% of AI-matched SKUs require no human correction.
* **Win Rate:** Lift in closed deals attributed to speed-to-quote.

---

## 7. Competitive Differentiation
* **Vertical-Specific LLMs:** Fine-tuned on industrial catalogs to distinguish precise technical differences (e.g., thread pitch, voltage).
* **Founder DNA:** Combination of deep AI expertise (Google X) and 100+ years of family history in the plumbing/construction trade.
* **Profit Optimization:** actively suggests substitutions to improve distributor margins.