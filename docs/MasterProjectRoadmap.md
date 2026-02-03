# Master Project Roadmap: Mercura - AI-Driven Quote Automation Platform

**Version:** 1.0  
**Last Updated:** January 29, 2026  
**Status:** Active Development  

---

## Executive Summary

Mercura is an AI-powered quote automation platform that transforms the competitive landscape for industrial distributors by enabling "First-to-Quote" advantage through semantic matching and automated workflows. Our platform unifies a high-velocity Browser Extension for data capture with a precision Web Dashboard for review and management, all powered by Gemini AI semantic matching rather than costly ERP integrations.

**Core Value Proposition:** Replicate Mercura's high-performance quoting without enterprise ERP costs by perfecting AI-driven parsing of "dirty" email data and technical PDFs, prioritizing velocity and scale over rigid regulatory precision.

**Strategic Focus:** US market emphasis on speed-to-quote, leveraging semantic search and self-learning AI to match products without live ERP connections.

---

## Architecture Diagram (Text-Based)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Browser        │     │   FastAPI       │     │   Gemini AI     │
│  Extension      │────▶│   Backend       │────▶│   Service       │
│  (Capture)      │     │   (Processing)  │     │  (Semantic      │
│                 │     │                 │     │   Matching)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │ Forward RFQ Email     │ Extract & Structure  │ Match Products
         │ (PDF/Excel/Email)     │ Data via AI          │ via Vector Search
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Dashboard │     │   Supabase      │     │   Export        │
│   (Review &     │◀────│   Database      │────▶│   Formats       │
│    Management)  │     │   (Storage)     │     │  (Excel/PDF)    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │ Human Review &        │ Persist Quotes &     │ Send to Customer
         │ Approval              │ Line Items           │ or ERP Import
```

**Data Flow Description:**
1. **Capture Phase:** Browser Extension detects and forwards RFQ emails with attachments to API
2. **Processing Phase:** FastAPI receives webhooks, extracts data using Gemini AI
3. **Matching Phase:** Semantic search matches extracted items against catalog using vector embeddings
4. **Review Phase:** Web Dashboard presents draft quotes for human validation and approval
5. **Output Phase:** Generate formatted quotes (Excel/PDF) or export for ERP systems

---

## MVP Feature Set

### What We Keep (Core AI-Driven Capabilities)
- **AI Specs Parsing:** Gemini-powered extraction from messy PDFs, Excel files, and email bodies
- **Email Automation:** Inbound webhook processing for seamless RFQ ingestion
- **Semantic Matching:** Vector-based product matching without direct ERP hooks
- **Competitor Mapping:** Manual upload of competitor SKU cross-references for improved accuracy
- **Draft Quote Generation:** Automated creation of reviewable quotes from extracted data
- **Web Dashboard:** Human-in-the-loop review interface for quote validation
- **Export Formats:** Excel and PDF generation for customer delivery

### What We Drop (Enterprise Dependencies)
- Direct SAP/Oracle/NetSuite ERP integrations (replaced with file-based exports)
- Real-time inventory synchronization
- Bi-directional stock/pricing sync
- Sophisticated profitability optimization AI
- Full lifecycle ERP quote injection

---

## Performance Workarounds

### Semantic Search Without ERP Connections
**Challenge:** Competitors rely on deep OData-based ERP integrations for pricing and inventory. We cannot replicate these costly methods.

**Solution:** AI-driven Semantic Matching using gemini_service.py with the following workarounds:

1. **Vector Database Matching:**
   - Store product catalog as high-dimensional embeddings in Supabase Vector
   - Use Gemini to generate embeddings for incoming RFQ items
   - Perform cosine similarity search for product matches
   - Confidence scoring based on semantic similarity rather than exact database lookups

2. **Self-Learning AI Patterns:**
   - Track user approval/rejection of AI suggestions
   - Implement feedback loop to improve future matching accuracy
   - Build "industry lexicon" understanding (e.g., "12V" ↔ "12 Volt")
   - Progressive confidence thresholds (start at 60%, increase with successful matches)

3. **Competitor Cross-Reference Layer:**
   - Allow manual upload of competitor SKU mappings via CompetitorMapping.tsx
   - Prioritize exact SKU matches before falling back to semantic search
   - Support bulk import of mapping files (CSV/Excel)

4. **Validation Rules Without Live Data:**
   - Flag price variances against catalog expected prices
   - Alert on unusually high quantities or missing SKUs
   - Margin guardrails based on stored cost/price data
   - Simple heuristics for data quality (e.g., negative prices, missing descriptions)

5. **File-Based ERP Bridge:**
   - Generate tab-separated values for easy ERP import
   - Support specialized export formats for common ERP systems
   - Email delivery of formatted quotes as interim solution

---

## Consolidated Roadmap (Three Distinct Phases)

### Phase 1: Foundation - Unified Capture & Processing (Weeks 1-4)
**Goal:** Establish end-to-end workflow from email capture to draft quote generation.

**Deliverables:**
- Browser Extension integration with chrome/content.js for RFQ detection
- Webhook processing in app/routes/webhooks.py for inbound emails
- Gemini AI extraction pipeline in services/gemini_service.py
- Basic quote creation in app/routes/quotes.py
- Draft quote review UI in frontend/src/pages/QuoteReview.tsx
- Competitor mapping upload via CompetitorMapping.tsx

**Success Metrics:**
- Email-to-draft-quote: <5 minutes average processing time
- Extraction accuracy: >80% confidence on structured data
- User can review and edit draft quotes in web dashboard

**Milestones:**
- Week 1: Extension forwarding functional
- Week 2: AI extraction working on sample RFQs
- Week 3: Draft quotes auto-generated
- Week 4: Basic review workflow complete

### Phase 2: Intelligence - Semantic Matching & Validation (Weeks 5-8)
**Goal:** Implement AI-driven product matching and quality validation.

**Deliverables:**
- Vector database setup in Supabase for semantic search
- Multi-layered matching engine (Competitor X-Ref → Exact SKU → Fuzzy Match → Semantic)
- Confidence scoring and suggestion ranking
- Validation rules (price variance, margin alerts, quantity flags)
- Enhanced review UI with bulk approval features
- Performance monitoring and feedback collection

**Success Metrics:**
- Matching accuracy: >70% of items matched without manual intervention
- False positive rate: <10% on AI suggestions
- User time-to-quote: <10 minutes from RFQ receipt

**Milestones:**
- Week 5: Basic semantic matching functional
- Week 6: Competitor mapping integration
- Week 7: Validation rules implemented
- Week 8: Performance optimization complete

### Phase 3: Scale & Automation - Enterprise Features (Weeks 9-12)
**Goal:** Add advanced automation and enterprise-ready features.

**Deliverables:**
- Automated UOM (Unit of Measure) conversion
- Bulk processing for multiple RFQs
- Advanced export formats (specialized ERP imports)
- Email automation for quote delivery
- Audit trails and quote lifecycle management
- Performance analytics dashboard
- Self-learning improvements based on user feedback

**Success Metrics:**
- Processing capacity: 100+ RFQs per day
- Automation rate: >80% of quotes require minimal human intervention
- Customer adoption: First paying pilot users

**Milestones:**
- Week 9: Bulk operations and UOM handling
- Week 10: Advanced exports and email integration
- Week 11: Analytics and monitoring
- Week 12: Pilot deployment and feedback collection

---

## Implementation Details

### Key Interfaces/Types

```typescript
// Data flow interfaces
interface EmailInput {
  sender: string;
  subject: string;
  body: string;
  attachments: Attachment[];
}

interface Attachment {
  filename: string;
  contentType: string;
  data: Buffer;
}

interface ExtractedQuote {
  lineItems: LineItem[];
  metadata: QuoteMetadata;
  confidence: number;
}

interface LineItem {
  itemName: string;
  sku?: string;
  description?: string;
  quantity: number;
  unitPrice?: number;
  totalPrice?: number;
  matchedProduct?: ProductMatch;
}

interface ProductMatch {
  catalogId: string;
  confidence: number;
  matchType: 'exact' | 'fuzzy' | 'semantic';
}

interface QuoteMetadata {
  documentType: 'rfq' | 'invoice' | 'catalog';
  customer: string;
  date: Date;
  totalAmount?: number;
}
```

### Design Patterns

- **Pipeline Pattern:** Sequential processing from capture → extraction → matching → review
- **Observer Pattern:** Event-driven updates between extension and web dashboard
- **Factory Pattern:** Different extraction strategies for various document types
- **Strategy Pattern:** Pluggable matching algorithms (exact, fuzzy, semantic)

### SOLID Principles Adherence

- **Single Responsibility:** Each service handles one concern (extraction, matching, export)
- **Open-Closed:** New matching strategies can be added without modifying existing code
- **Liskov Substitution:** All matching implementations conform to same interface
- **Interface Segregation:** Separate interfaces for different workflow stages
- **Dependency Inversion:** High-level modules depend on abstractions, not concretions

### Technology Stack Alignment

- **Frontend:** React/TypeScript for extension and dashboard
- **Backend:** FastAPI/Python for API and processing
- **AI:** Google Gemini 1.5 Flash for extraction and embeddings
- **Database:** Supabase PostgreSQL with Vector extension
- **Storage:** Supabase for data persistence and file handling

---

## Risk Mitigation & Success Metrics

### Key Risks
- **Extraction Quality:** AI accuracy varies by document type
  - Mitigation: Human review workflow, confidence thresholds, progressive improvement
- **Matching Performance:** Semantic search may be slow or inaccurate initially
  - Mitigation: Hybrid approach (exact matches first), user feedback loops
- **User Adoption:** Distributors accustomed to manual processes
  - Mitigation: Focus on time savings, easy-to-use interface, quick wins

### Success Metrics
- **Time-to-First-Quote:** <10 minutes from RFQ receipt
- **Automation Rate:** >70% of line items matched automatically
- **User Satisfaction:** >80% of users report time savings vs. manual quoting
- **Accuracy:** >90% extraction confidence, <5% error rate in final quotes

---

## Future Considerations

### Phase 4+ (Post-MVP)
- Direct ERP API integrations (only after proven demand)
- Advanced profitability AI and margin optimization
- Multi-tenant enterprise features
- Mobile app for field sales teams
- Integration with CRM systems (Salesforce, HubSpot)

### Market Expansion
- European market adaptation (regulatory compliance focus)
- Additional verticals beyond industrial distribution
- International language support for global RFQs

---

**Document Owner:** Product Architecture Team  
**Next Review:** March 1, 2026  
**Approval Required:** Executive Team Sign-off
