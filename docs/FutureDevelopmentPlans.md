# Mercura: The Ultimate Product Guide & Roadmap

This document serves as the definitive guide to Mercura’s current capabilities and our path toward becoming the "AI Backbone" for industrial distributors. It synthesizes our recent foundational work with the long-term vision of capturing the full value of a competitor's ERP-integrated suite.

---

## 1. The State of Mercura: The "80% Utility" Milestone
We have successfully implemented the core utility loop that solves the primary pain point for industrial sales teams: **The Unstructured Data Bottleneck.**

### **The "One-Click" Workflow**
1. **Inbound Ingestion:** Forward a messy RFQ (PDF, Excel, Image, or Email) to Mercura.
2. **AI Extraction:** Gemini-powered extraction structures line items, quantities, and descriptions in minutes.
3. **Assisted Matching:** A multi-layered suggestion engine identifies the best catalog match.
4. **Human-in-the-Loop Review:** A streamlined UI for verifying extractions and applying matches.
5. **Instant Output:** Generate ERP-ready data, formatted Excel quotes, or send directly via email.

---

## 2. Core Functionality Breakdown

### **A. Smart Ingestion & Extraction**
*   **Multi-Format Support:** Handles PDFs, XLSX, CSV, and inline email text.
*   **Confidence Scoring:** Every extracted field is assigned a confidence score, highlighting items that need manual review.
*   **Idempotency:** Built-in protection against duplicate processing for the same email.

### **B. The Multi-Layered Matching Engine**
We don't just search for text; we use a prioritized hierarchy to find the right product:
1.  **Competitor X-Ref (Priority 1):** Checks the user-defined `competitor_maps` table for direct SKU cross-references.
2.  **Exact SKU Match (Priority 2):** Scans the catalog for identical SKU strings.
3.  **Keyword/Fuzzy Match (Priority 3):** Uses substring and token overlap for high-confidence keyword hits.
4.  **Semantic Vector Search (Priority 4):** Fallback for low-confidence matches using **Gemini Embeddings** and **Supabase Vector**. This understands "Industry Lexicon" (e.g., matching "12V" to "12 Volt").

### **C. The Review & Workflow UI**
*   **Margin Guardrails:** Real-time margin calculation with visual alerts for low-profit items (<15%).
*   **Validation Hints:** Flags price variances, missing SKUs, or unusually high quantities.
*   **Copy for ERP:** A one-click "Copy for ERP" button that formats the quote as tab-separated values for instant pasting into legacy ERP systems (SAP, Epicor, etc.).
*   **Auto-Match:** Bulk apply all high-confidence suggestions (>60%) in one click.

### **D. Outputs & Traceability**
*   **Formatted Excel Export:** Professional quotes ready for customer delivery.
*   **One-Click Email Send:** Integrated SendGrid service to reply to the original requester with the quote attached.
*   **Full Traceability:** Every quote is linked back to its source `inbound_email_id` for auditing.

---

## 3. Advanced Features: "The Industry Lexicon"
Our **Phase 4** implementation introduced true semantic intelligence:
*   **Vector Database:** We use Supabase Vector to store high-dimensional embeddings of your entire catalog.
*   **Synonym Recognition:** Automatically understands that "1/2 inch copper pipe" and "0.5in Cu Tubing" are likely the same product.
*   **Bulk Mapping UI:** A dedicated management screen (`/mappings`) for users to upload and refine their own competitor-to-internal SKU relationships.

---

## 4. The Roadmap to 100%: Future Developments

### **Phase 5: ERP Integrations (The "Deep" Layer)**
*   **File-Based Injection:** Create specialized export formats (JSON/XML) tailored for specific ERP import utilities.
*   **Direct API Adapters:** If demand persists, build bi-directional sync for real-time inventory and direct quote injection into SAP/Oracle/NetSuite.

### **Phase 6: Advanced AI & Profitability**
*   **Automated UOM Conversion:** Intelligent conversion between "Boxes", "Each", "Feet", and "Pallets" during extraction and matching.
*   **Profitability Substitutions:** Automatically suggest higher-margin alternatives for low-margin items in the catalog.
*   **Price Optimization:** AI-driven suggestions to adjust pricing based on historical win rates and market data.

### **Technical Infrastructure Goals**
*   **Migration System:** Implement Alembic for robust database schema versioning.
*   **Enhanced Human-Review:** A dashboard view dedicated to "Review Required" items across all quotes.
*   **Multi-Tenant Settings:** Move hardcoded thresholds (margin alerts, price variance) into user-configurable settings.

---

## 5. Summary of Built-in "Competitive Killers"
| Feature | Competitor Approach | Mercura "Lite" Approach | Status |
| :--- | :--- | :--- | :--- |
| **Matching** | Expensive ML Models | Multi-Layered (X-Ref + Vector) | **Implemented** |
| **ERP Sync** | High-Cost Custom Dev | "Copy for ERP" + Excel | **Implemented** |
| **Guardrails** | Complex Analytics | Margin Alerts + Validation Hints | **Implemented** |
| **Mapping** | Tribal Knowledge | Bulk Mapping UI | **Implemented** |

---
*Last Updated: 2026-01-18*
