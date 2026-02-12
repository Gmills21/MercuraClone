# 🚀 Mercura Landing Page - Architecture & Implementation Plan

> **Project:** Mercura Landing Page  
> **Version:** 1.0  
> **Created:** 2026-02-07  
> **Status:** Planning Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Visual Identity & Design System](#visual-identity--design-system)
3. [Page Architecture](#page-architecture)
4. [Section Blueprints](#section-blueprints)
5. [Component Inventory](#component-inventory)
6. [Technical Implementation](#technical-implementation)
7. [File Structure](#file-structure)
8. [Implementation Phases](#implementation-phases)
9. [Dependencies & Assets](#dependencies--assets)

---

## Executive Summary

### The Mission
Build a **high-conversion, Silicon Valley-grade landing page** that positions Mercura as the AI-powered quoting solution for industrial distributors. The design must convey:

- **Engineering Precision** → Technical grid patterns, clean typography
- **Enterprise Trust** → Security badges, compliance logos, case studies
- **Human Touch** → Founder story, industry roots ("115 years in plumbing and electrical")

### Target Transformation
| Before State | After State |
|--------------|-------------|
| Sales reps buried in manual paperwork | Reps closing deals, AI handling quotes |
| Hours spent searching through specs | Instant AI-powered product matching |
| Deals lost to slow turnaround | "Quote in minutes, not days" |
| Knowledge locked in senior staff | AI preserves institutional expertise |

### Primary Conversion Goal
**"Get a Demo"** - Single, clear CTA throughout the page

---

## Visual Identity & Design System

### The "Linear.app" Aesthetic
We leverage the existing design system in `index.css` which already implements:

```
✓ Technical Grid Pattern (.tech-grid)
✓ Soft/Diffused Shadows (.shadow-soft, .shadow-soft-lg)
✓ Minimal Borders (1px at 5% opacity)
✓ Bento Grid Cards (.bento-card)
✓ Hover Lift Effects (.hover-lift)
✓ Glass Morphism (.glass)
✓ Inter Font with tracking-tight headings
```

### Color Palette (Already Configured)

| Token | Value | Usage |
|-------|-------|-------|
| `--primary` | Orange-600 `hsl(24,95%,53%)` | CTAs, accents |
| `--foreground` | Slate-950 | Headings, body text |
| `--background` | Off-white `hsl(210,40%,98%)` | Page background |
| `--muted` | Slate (`hsl(215,16%,47%)`) | Secondary text |
| `--border` | 5% opacity | Card borders |

### Typography Scale (Landing Page Specific)

```css
/* Hero */
.hero-headline     { @apply text-5xl md:text-7xl font-bold tracking-tight; }
.hero-subheadline  { @apply text-xl md:text-2xl text-muted-foreground; }

/* Section Headers */
.section-headline  { @apply text-3xl md:text-5xl font-bold tracking-tight; }
.section-subline   { @apply text-lg md:text-xl text-muted-foreground max-w-2xl; }

/* Body */
.body-large        { @apply text-lg leading-relaxed; }
.body-small        { @apply text-sm text-muted-foreground; }
```

### Spacing System

```css
/* Generous Whitespace (2x padding as per refactor) */
--section-py: 96px;    /* py-24 */
--section-px: 120px;   /* px-30 (max-w-7xl centered) */
--content-gap: 64px;   /* gap-16 */
--card-padding: 32px;  /* p-8 */
```

---

## Page Architecture

### Section Flow (10 Sections)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. HEADER (Sticky)                                              │
│     Logo | Navigation | "Get a Demo" CTA                         │
├─────────────────────────────────────────────────────────────────┤
│  2. HERO SECTION                                                 │
│     Headline + Sub + CTAs + Dashboard Mockup                     │
├─────────────────────────────────────────────────────────────────┤
│  3. TRUST LAYER (Logo Cloud)                                     │
│     "40+ customers trust Mercura" + Industry Logos               │
├─────────────────────────────────────────────────────────────────┤
│  4. PROBLEM SECTION                                              │
│     "Sales Reps Should Sell, Not Search"                         │
│     Frustrated rep visual + Data source icons                    │
├─────────────────────────────────────────────────────────────────┤
│  5. HOW IT WORKS (3 Steps)                                       │
│     Receive → Match → Send to ERP                                │
├─────────────────────────────────────────────────────────────────┤
│  6. FEATURE BENTO GRID                                           │
│     Specs AI | Voice Agents | Email Requests | Integrations      │
├─────────────────────────────────────────────────────────────────┤
│  7. ROI CALCULATOR (Interactive)                                 │
│     Inputs: Requests, Employees, Time → Output: Savings          │
├─────────────────────────────────────────────────────────────────┤
│  8. FOUNDER STORY                                                │
│     "From the Industry, For the Industry"                        │
├─────────────────────────────────────────────────────────────────┤
│  9. CASE STUDY (Sanitär-Heinze)                                  │
│     Quote + Stats + Photo                                        │
├─────────────────────────────────────────────────────────────────┤
│ 10. FOOTER CTA + COMPLIANCE                                      │
│     "Save 16 hours. Per rep, per week." + Badges                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section Blueprints

### 1. Header (Sticky Navigation)

```tsx
<header class="fixed top-0 left-0 right-0 z-50 glass">
  <nav class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
    <Logo />
    <NavLinks: [Product, Pricing, Customers, Company] />
    <CTAButton: "Get a Demo" />
  </nav>
</header>
```

**Behavior:** Transparent on load → Glass effect on scroll (backdrop-blur)

---

### 2. Hero Section

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│           Silicon Valley technology,                            │
│        for the backbone of our economy                          │
│                                                                 │
│    Automate your inside sales processes with AI that            │
│    understands customer requests, matches products,             │
│    and wins more business.                                      │
│                                                                 │
│    [ Get a Demo ]   [ See How It Works → ]                      │
│                                                                 │
│    ┌─────────────────────────────────────────────────────┐      │
│    │                                                     │      │
│    │           [Dashboard Mockup Screenshot]             │      │
│    │               "Requests Overview"                   │      │
│    │                                                     │      │
│    └─────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                         ↓ tech-grid background
```

**Component Props:**
- `headline`: "Silicon Valley technology, for the backbone of our economy"
- `subheadline`: "Automate your inside sales processes..."
- `primaryCta`: { text: "Get a Demo", href: "/demo" }
- `secondaryCta`: { text: "See How It Works", href: "#how-it-works" }
- `mockupSrc`: "/images/dashboard-mockup.png"

---

### 3. Trust Layer (Logo Cloud)

```tsx
<section class="py-16 border-y border-minimal">
  <div class="max-w-7xl mx-auto text-center">
    <p class="text-muted-foreground mb-8">
      40+ industrial distributors trust Mercura
    </p>
    <div class="flex flex-wrap justify-center items-center gap-12 grayscale opacity-70">
      {logos.map(logo => <img src={logo} alt={name} class="h-8" />)}
    </div>
  </div>
</section>
```

**Logo Sources (Monochrome):**
- HVAC distributors
- Plumbing suppliers
- Electrical wholesalers
- Manufacturing partners

---

### 4. Problem Section

**Headline:** "Sales Reps Should Sell, Not Search"

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ┌────────────────────┐                                          │
│  │                    │     Your best salespeople are            │
│  │  [Frustrated Rep   │     buried in manual paperwork.          │
│  │   Illustration]    │                                          │
│  │                    │     Instead of closing deals, they're    │
│  │        ↓           │     searching through hundreds of        │
│  │   ┌───────────┐    │     pages of specifications.             │
│  │   │PDFs│Excel │    │                                          │
│  │   │Email│GAEB │    │     Every hour wasted on admin is        │
│  │   └───────────┘    │     an hour not spent selling.           │
│  └────────────────────┘                                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Visual Elements:**
- Illustration of frustrated sales rep at desk
- Connected icons: PDF, Excel, Email, GAEB file icons
- Animated lines connecting data sources to rep

---

### 5. How It Works (3 Steps)

```
                    How Mercura Transforms Your Workflow
                    ────────────────────────────────────

    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │       📨         │    │       🎯         │    │       ⚡         │
    │                  │ →  │                  │ →  │                  │
    │  Receive Request │    │  Smart Product   │    │  Send to ERP     │
    │                  │    │    Matching      │    │    Instantly     │
    │  AI understands  │    │  AI finds spec-  │    │  Generate an     │
    │  customer        │    │  compliant       │    │  accurate quote  │
    │  requests from   │    │  products and    │    │  ready in        │
    │  any source      │    │  prioritizes     │    │  minutes, not    │
    │  instantly.      │    │  highest-margin  │    │  hours or days.  │
    │                  │    │  options.        │    │                  │
    └──────────────────┘    └──────────────────┘    └──────────────────┘
                              bento-card styling
```

**Animation:** Steps animate in sequentially on scroll (staggered fade-in)

---

### 6. Feature Bento Grid

```
┌───────────────────────────────────────────────────────────────────────┐
│                        Powerful Features                               │
│                                                                        │
│   ┌──────────────────────────┐  ┌──────────────────────────────────┐  │
│   │  📋 SPECIFICATIONS AI    │  │  🎙️ AI VOICE AGENTS             │  │
│   │                          │  │                                  │  │
│   │  Reads complex technical │  │  Intelligent assistants that     │  │
│   │  specs and tender texts  │  │  handle inquiries and provide    │  │
│   │  automatically.          │  │  real-time quotes via phone.     │  │
│   │                          │  │                                  │  │
│   │  [Spec preview visual]   │  │  [Voice wave animation]          │  │
│   └──────────────────────────┘  └──────────────────────────────────┘  │
│                                                                        │
│   ┌──────────────────────────┐  ┌──────────────────────────────────┐  │
│   │  ✉️ EMAIL AUTOMATION     │  │  🔗 ENTERPRISE INTEGRATIONS      │  │
│   │                          │  │                                  │  │
│   │  Turn inbox requests     │  │  Enterprise-ready connections    │  │
│   │  directly into CRM/ERP   │  │  to SAP, Oracle, QuickBooks.     │  │
│   │  entries automatically.  │  │                                  │  │
│   │                          │  │  [Integration logos stack]       │  │
│   │  [Email to CRM visual]   │  │                                  │  │
│   └──────────────────────────┘  └──────────────────────────────────┘  │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

**Grid Layout:** 2x2 on desktop, 1-column stack on mobile

---

### 7. ROI Calculator (Interactive)

**Integration:** Connects to `business_impact_service.py` → `calculate_roi_simulation()`

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                    Calculate Your Potential Savings                       │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐     │
│   │                                                                │     │
│   │   Annual Quote Requests          [  1,000  ] ─────────●───    │     │
│   │                                                                │     │
│   │   Number of Sales Reps           [    3    ] ───●──────────   │     │
│   │                                                                │     │
│   │   Current Processing Time        [  60 min ] ────────●────    │     │
│   │                                                                │     │
│   └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐     │
│   │         💰 POTENTIAL SAVINGS          📈 REVENUE UPSIDE        │     │
│   │                                                                │     │
│   │            $23,400                        $156,000             │     │
│   │            per year                       potential            │     │
│   │                                                                │     │
│   │         ⏱️ 16 hours saved per rep, per week                    │     │
│   └────────────────────────────────────────────────────────────────┘     │
│                            bento-card styling                            │
│                                                                          │
│                    [ Get Your Custom Analysis → ]                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Calculation Formula (from BusinessImpactService):**
```python
HOURLY_LABOR_COST = 50.0
MANUAL_QUOTE_TIME_MINS = 18
SMART_QUOTE_TIME_MINS = 4

time_saved = requests_per_year * (manual_time_mins - SMART_QUOTE_TIME_MINS)
labor_savings = (time_saved / 60) * HOURLY_LABOR_COST
```

---

### 8. Founder Story Section

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                From the Industry, For the Industry                    │
│                                                                      │
│    ┌──────────────────┐                                              │
│    │                  │   "We're not just technologists.             │
│    │  [Founder Photo] │                                              │
│    │                  │    Our family has 115 years in plumbing      │
│    │                  │    and electrical distribution.              │
│    └──────────────────┘                                              │
│                            We built Mercura because we've seen       │
│                            firsthand how much time gets wasted       │
│                            on quoting.                               │
│                                                                      │
│                            Combined with engineering experience      │
│                            from Google, we created an AI that's      │
│                            not just smart—it's a Subject Matter      │
│                            Expert coworker built for hard-working    │
│                            people in the trades."                    │
│                                                                      │
│                            — [Founder Name], CEO & Co-Founder        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 9. Case Study Section

**Company:** Sanitär-Heinze (or similar industrial distributor)

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│         "Mercura allows us to significantly increase                  │
│          productivity in the quotation department."                   │
│                                                                      │
│    ┌────────────┐  ┌─────────────────────────────────────────────┐   │
│    │            │  │                                             │   │
│    │ [Customer  │  │   📈 30% more quotes processed              │   │
│    │  Photo]    │  │                                             │   │
│    │            │  │   ⏱️ 75% faster turnaround time              │   │
│    │            │  │                                             │   │
│    └────────────┘  │   💡 "Finding qualified staff is hard.      │   │
│                    │      AI ensures that technical knowledge    │   │
│    — Maria Schmidt │      is never lost."                        │   │
│    Head of Sales   │                                             │   │
│    Sanitär-Heinze  └─────────────────────────────────────────────┘   │
│                                                                      │
│                        [ Read Full Case Study → ]                    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 10. Footer CTA + Compliance

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│              Save 16 hours. Per rep, per week.                        │
│                                                                      │
│                      [ Get a Demo ]                                   │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   🔐 SOC 2 Type II    🇪🇺 GDPR Compliant    🏆 Y Combinator S24      │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   [Logo]           Product          Company          Legal           │
│   Mercura          Features         About            Privacy         │
│                    Pricing          Careers          Terms           │
│                    Integrations     Blog             Security        │
│                    Documentation    Contact          DPA             │
│                                                                      │
│   © 2026 Mercura Inc. All rights reserved.                           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Inventory

### New Components to Build

| Component | Path | Priority | Description |
|-----------|------|----------|-------------|
| `LandingPage.tsx` | `/pages/` | P0 | Main landing page container |
| `LandingHeader.tsx` | `/components/landing/` | P0 | Sticky navigation header |
| `HeroSection.tsx` | `/components/landing/` | P0 | Hero with headline + mockup |
| `LogoCloud.tsx` | `/components/landing/` | P1 | Monochrome trust logos |
| `ProblemSection.tsx` | `/components/landing/` | P1 | Problem narrative |
| `HowItWorks.tsx` | `/components/landing/` | P0 | 3-step diagram |
| `FeatureBento.tsx` | `/components/landing/` | P0 | 2x2 feature grid |
| `ROICalculator.tsx` | `/components/landing/` | P0 | Interactive calculator |
| `FounderStory.tsx` | `/components/landing/` | P2 | Founder narrative section |
| `CaseStudy.tsx` | `/components/landing/` | P1 | Customer testimonial |
| `LandingFooter.tsx` | `/components/landing/` | P0 | Footer with CTAs + badges |

### Reusable UI Components (Existing)

| Component | Usage |
|-----------|-------|
| `Button` | CTAs throughout |
| `Card` | Feature cards, calculator |
| `Badge` | Trust badges, feature labels |

---

## Technical Implementation

### Routing Setup

```tsx
// App.tsx - Add landing page route
import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'

function App() {
  return (
    <Routes>
      {/* Public landing page - no auth */}
      <Route path="/" element={<LandingPage />} />
      
      {/* Authenticated app routes */}
      <Route path="/app/*" element={<Layout />}>
        <Route path="dashboard" element={<Dashboard />} />
        {/* ... existing routes ... */}
      </Route>
    </Routes>
  )
}
```

### ROI Calculator API Integration

```tsx
// services/roiApi.ts
export async function calculateROI(params: {
  requestsPerYear: number
  employees: number
  manualTimeMins: number
  avgValue?: number
}) {
  const response = await fetch('/api/business-impact/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      requests_per_year: params.requestsPerYear,
      employees: params.employees,
      manual_time_mins: params.manualTimeMins,
      avg_value: params.avgValue || 2500
    })
  })
  return response.json()
}
```

### Animation Library

```bash
npm install framer-motion
```

Usage for section reveals:
```tsx
import { motion } from 'framer-motion'

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
}

<motion.section
  initial="hidden"
  whileInView="visible"
  viewport={{ once: true }}
  variants={fadeInUp}
>
  {/* Section content */}
</motion.section>
```

---

## File Structure

```
frontend/src/
├── pages/
│   └── LandingPage.tsx           # Main landing page
│
├── components/
│   ├── landing/                   # Landing-specific components
│   │   ├── index.ts               # Barrel export
│   │   ├── LandingHeader.tsx
│   │   ├── HeroSection.tsx
│   │   ├── LogoCloud.tsx
│   │   ├── ProblemSection.tsx
│   │   ├── HowItWorks.tsx
│   │   ├── FeatureBento.tsx
│   │   ├── ROICalculator.tsx
│   │   ├── FounderStory.tsx
│   │   ├── CaseStudy.tsx
│   │   └── LandingFooter.tsx
│   │
│   └── ui/                        # Existing Shadcn components
│
├── assets/
│   └── images/
│       ├── logo-dark.svg
│       ├── dashboard-mockup.png
│       ├── customer-logos/
│       │   ├── logo-1.svg
│       │   ├── logo-2.svg
│       │   └── ...
│       └── integrations/
│           ├── sap.svg
│           ├── oracle.svg
│           └── quickbooks.svg
│
└── styles/
    └── landing.css                # Landing-specific styles
```

---

## Implementation Phases

### Phase 1: Foundation (Day 1)
- [ ] Create `/pages/LandingPage.tsx` container
- [ ] Add route to `App.tsx` (public, no auth)
- [ ] Build `LandingHeader.tsx` with sticky glass effect
- [ ] Build `HeroSection.tsx` with headline + mockup slot
- [ ] Create `landing.css` with section spacing

### Phase 2: Trust & Problem (Day 2)
- [ ] Build `LogoCloud.tsx` with placeholder logos
- [ ] Build `ProblemSection.tsx` with visual metaphor
- [ ] Build `HowItWorks.tsx` 3-step flow

### Phase 3: Features & Value (Day 3)
- [ ] Build `FeatureBento.tsx` 2x2 grid
- [ ] Build `ROICalculator.tsx` with sliders
- [ ] Connect to `business_impact_service.py` endpoint

### Phase 4: Story & Proof (Day 4)
- [ ] Build `FounderStory.tsx`
- [ ] Build `CaseStudy.tsx` with testimonial
- [ ] Build `LandingFooter.tsx` with badges

### Phase 5: Polish (Day 5)
- [ ] Add Framer Motion scroll animations
- [ ] Mobile responsive testing
- [ ] Performance optimization (lazy load images)
- [ ] SEO metadata (title, description, OG tags)
- [ ] Accessibility audit (ARIA labels, contrast)

---

## Dependencies & Assets

### NPM Packages to Install

```bash
npm install framer-motion    # Scroll animations
npm install lucide-react     # Icons (already installed)
```

### Assets Needed

| Asset | Type | Source | Priority |
|-------|------|--------|----------|
| Dashboard Mockup | PNG | Screenshot from app | P0 |
| Customer Logos | SVG | Request from customers | P1 |
| Founder Photo | JPG | Provided | P2 |
| Integration Logos | SVG | Official brand kits | P1 |
| Trust Badges | SVG | SOC2/GDPR/YC | P1 |

### Environment Variables

```env
# .env.local (frontend)
VITE_API_URL=http://localhost:8000
VITE_DEMO_CALENDLY_URL=https://calendly.com/mercura/demo
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to First Meaningful Paint | < 1.5s |
| Lighthouse Performance Score | > 90 |
| Lighthouse Accessibility Score | > 95 |
| Mobile Responsiveness | 100% sections work |
| CTA Visibility | "Get a Demo" visible above fold |

---

## Next Steps

1. **Approve this architecture** - Review and sign off on section structure
2. **Gather assets** - Dashboard screenshot, customer logos, founder photo
3. **Begin Phase 1** - Create foundation components
4. **Iterate on copy** - Refine headlines and body text

---

*This document is the source of truth for the Mercura landing page development. Update as implementation progresses.*
