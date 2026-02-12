# Landing Page Component Specifications

> **Reference:** LANDING_PAGE_ARCHITECTURE.md  
> **Purpose:** Detailed component implementation specs

---

## Component: `LandingHeader`

### File: `frontend/src/components/landing/LandingHeader.tsx`

```tsx
interface LandingHeaderProps {
  transparent?: boolean  // Initial transparent state
}

const navLinks = [
  { label: 'Product', href: '#features' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'Customers', href: '#case-study' },
  { label: 'Company', href: '#founder' },
]
```

### Visual States

| State | Background | Border | Shadow |
|-------|------------|--------|--------|
| Top of page | `transparent` | none | none |
| Scrolled (>80px) | `glass` effect | `border-minimal` | `shadow-soft` |

### Implementation Notes

- Use `useEffect` with `scroll` listener to toggle glass effect
- Logo links to `/` (landing) or `/app/dashboard` if authenticated
- "Get a Demo" button always visible, uses `primary` color
- Mobile: Hamburger menu with slide-in drawer

---

## Component: `HeroSection`

### File: `frontend/src/components/landing/HeroSection.tsx`

```tsx
interface HeroSectionProps {
  headline: string
  subheadline: string
  primaryCta: { text: string; href: string }
  secondaryCta?: { text: string; href: string }
  mockupSrc: string
  mockupAlt: string
}
```

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  section: min-h-screen pt-24 tech-grid                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  container: max-w-7xl mx-auto px-6                    │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  text-center: max-w-4xl mx-auto                 │  │  │
│  │  │                                                 │  │  │
│  │  │  <h1> hero-headline (text-5xl→7xl)              │  │  │
│  │  │  <p>  hero-subheadline (text-xl→2xl, muted)     │  │  │
│  │  │                                                 │  │  │
│  │  │  <div> flex gap-4 justify-center mt-8           │  │  │
│  │  │    [Primary CTA Button]                         │  │  │
│  │  │    [Secondary CTA Link →]                       │  │  │
│  │  │  </div>                                         │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  mockup-container: mt-16 relative               │  │  │
│  │  │                                                 │  │  │
│  │  │  <div> shadow-2xl rounded-xl overflow-hidden    │  │  │
│  │  │    border-minimal                               │  │  │
│  │  │    <img src={mockupSrc} />                      │  │  │
│  │  │  </div>                                         │  │  │
│  │  │                                                 │  │  │
│  │  │  <!-- Glow effect behind mockup -->             │  │  │
│  │  │  <div> absolute -z-10 blur-3xl                  │  │  │
│  │  │    bg-primary/20                                │  │  │
│  │  │  </div>                                         │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Content Options

**Option A (Default):**
```
Silicon Valley technology,
for the backbone of our economy
```

**Option B (Problem-focused):**
```
Stop losing deals to
manual quote handling
```

---

## Component: `LogoCloud`

### File: `frontend/src/components/landing/LogoCloud.tsx`

```tsx
interface LogoCloudProps {
  headline?: string  // Default: "40+ customers trust Mercura"
  logos: Array<{
    src: string
    alt: string
    width?: number
  }>
}
```

### Styling

```css
.logo-cloud-item {
  @apply grayscale opacity-60 hover:opacity-100 hover:grayscale-0;
  @apply transition-all duration-300;
  height: 32px;
  width: auto;
}
```

### Animation

- Logos fade in sequentially on scroll (stagger: 100ms)
- Consider infinite scroll marquee for many logos

---

## Component: `ProblemSection`

### File: `frontend/src/components/landing/ProblemSection.tsx`

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  section: py-24 bg-slate-50                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  grid: md:grid-cols-2 gap-16 items-center             │  │
│  │                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────────────────┐ │  │
│  │  │  Visual Column  │  │  Text Column                │ │  │
│  │  │                 │  │                             │ │  │
│  │  │  [Illustration] │  │  <Badge>The Problem</Badge> │ │  │
│  │  │                 │  │  <h2>Sales Reps Should      │ │  │
│  │  │  Connected to:  │  │      Sell, Not Search</h2>  │ │  │
│  │  │  📄 PDFs        │  │                             │ │  │
│  │  │  📊 Excel       │  │  <p>Your best salespeople   │ │  │
│  │  │  ✉️ Email       │  │  are buried in manual       │ │  │
│  │  │  📋 GAEB        │  │  paperwork...</p>           │ │  │
│  │  │                 │  │                             │ │  │
│  │  └─────────────────┘  └─────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Icons for Data Sources

```tsx
import { FileText, Table, Mail, FileSpreadsheet } from 'lucide-react'

const dataSources = [
  { icon: FileText, label: 'PDF Specs' },
  { icon: Table, label: 'Excel Files' },
  { icon: Mail, label: 'Email Requests' },
  { icon: FileSpreadsheet, label: 'GAEB Standards' },
]
```

---

## Component: `HowItWorks`

### File: `frontend/src/components/landing/HowItWorks.tsx`

```tsx
interface Step {
  number: number
  icon: React.ReactNode
  title: string
  description: string
}

const steps: Step[] = [
  {
    number: 1,
    icon: <Inbox className="w-8 h-8" />,
    title: 'Receive Request',
    description: 'AI understands customer requests from multiple sources instantly.'
  },
  {
    number: 2,
    icon: <Target className="w-8 h-8" />,
    title: 'Smart Product Matching',
    description: 'AI finds spec-compliant products and prioritizes highest-margin options.'
  },
  {
    number: 3,
    icon: <Zap className="w-8 h-8" />,
    title: 'Send to ERP Instantly',
    description: 'Generate an accurate, professional quote ready in minutes, not hours.'
  },
]
```

### Layout

```
desktop: flex-row with connecting lines between steps
mobile: flex-col with vertical line connecting steps
```

### Animation

- Steps fade in sequentially on scroll
- Connecting line "draws" between steps

---

## Component: `FeatureBento`

### File: `frontend/src/components/landing/FeatureBento.tsx`

```tsx
interface FeatureCard {
  icon: React.ReactNode
  title: string
  description: string
  visual?: React.ReactNode  // Optional illustration/animation
  className?: string        // For spanning columns
}

const features: FeatureCard[] = [
  {
    icon: <FileSearch />,
    title: 'Specifications AI',
    description: 'Reads complex technical specs and tender texts automatically.',
    className: 'md:col-span-1'
  },
  {
    icon: <Mic />,
    title: 'AI Voice Agents',
    description: 'Intelligent assistants that handle customer inquiries via phone.',
    className: 'md:col-span-1'
  },
  {
    icon: <Mail />,
    title: 'E-mail Automation',
    description: 'Turn inbox requests directly into CRM/ERP entries.',
    className: 'md:col-span-1'
  },
  {
    icon: <Puzzle />,
    title: 'Enterprise Integrations',
    description: 'Enterprise-ready connections to SAP, Oracle, QuickBooks.',
    className: 'md:col-span-1'
  },
]
```

### Grid Layout

```css
.feature-bento-grid {
  @apply grid gap-6;
  grid-template-columns: repeat(2, 1fr);
}

@media (max-width: 768px) {
  .feature-bento-grid {
    grid-template-columns: 1fr;
  }
}
```

### Card Styling

Uses existing `.bento-card` class from `index.css`:
- Hover lift effect
- Soft shadow
- Minimal border (1px, 5% opacity)

---

## Component: `ROICalculator`

### File: `frontend/src/components/landing/ROICalculator.tsx`

### State Management

```tsx
interface ROIState {
  requestsPerYear: number    // Default: 1000, Range: 100-10000
  employees: number          // Default: 3, Range: 1-50
  manualTimeMins: number     // Default: 60, Range: 15-180
}

interface ROIResult {
  laborSavings: number       // $ saved per year
  revenueUpside: number      // $ potential revenue
  hoursPerWeek: number       // Hours saved per rep
  additionalQuotes: number   // Extra quotes processed
}
```

### API Integration

```tsx
// Connect to backend
const calculateROI = async (state: ROIState): Promise<ROIResult> => {
  const response = await fetch('/api/business-impact/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      requests_per_year: state.requestsPerYear,
      employees: state.employees,
      manual_time_mins: state.manualTimeMins,
      avg_value: 2500  // Default quote value
    })
  })
  return response.json()
}
```

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  section: py-24 bg-slate-900 text-white                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Header: text-center mb-12                             │  │
│  │  <Badge variant="secondary">ROI Calculator</Badge>     │  │
│  │  <h2>Calculate Your Potential Savings</h2>             │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────┐  ┌─────────────────────────────┐  │
│  │  Inputs Panel        │  │  Results Panel              │  │
│  │  bento-card-dark     │  │  bento-card-dark            │  │
│  │                      │  │                             │  │
│  │  Annual Requests     │  │     💰 $23,400              │  │
│  │  [====●======]       │  │     Labor Savings           │  │
│  │  1,000               │  │                             │  │
│  │                      │  │     📈 $156,000             │  │
│  │  Sales Reps          │  │     Revenue Upside          │  │
│  │  [===●=======]       │  │                             │  │
│  │  3                   │  │     ⏱️ 16 hours/week        │  │
│  │                      │  │     Per Rep Saved           │  │
│  │  Minutes per Quote   │  │                             │  │
│  │  [========●==]       │  │                             │  │
│  │  60 min              │  │                             │  │
│  └──────────────────────┘  └─────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  CTA: center                                           │  │
│  │  [ Get Your Custom Analysis → ]                        │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Animation

- Results animate with counting effect when values change
- Use `react-spring` or CSS counter animation

---

## Component: `FounderStory`

### File: `frontend/src/components/landing/FounderStory.tsx`

```tsx
interface FounderStoryProps {
  quote: string
  founderName: string
  founderTitle: string
  founderImage?: string
  stats?: Array<{ value: string; label: string }>
}
```

### Content

```tsx
const founderContent = {
  quote: `We're not just technologists. Our family has 115 years in plumbing 
          and electrical distribution. We built Mercura because we've seen 
          firsthand how much time gets wasted on quoting.

          Combined with engineering experience from Google, we created an AI 
          that's not just smart—it's a Subject Matter Expert coworker built 
          for hard-working people in the trades.`,
  founderName: '[Founder Name]',
  founderTitle: 'CEO & Co-Founder',
  stats: [
    { value: '115', label: 'Years in the trades' },
    { value: '→', label: 'Google engineering' },
    { value: '🎯', label: 'Built for you' },
  ]
}
```

---

## Component: `CaseStudy`

### File: `frontend/src/components/landing/CaseStudy.tsx`

```tsx
interface CaseStudyProps {
  quote: string
  author: {
    name: string
    title: string
    company: string
    image?: string
    logo?: string
  }
  stats: Array<{
    value: string
    label: string
    icon?: React.ReactNode
  }>
  ctaText?: string
  ctaHref?: string
}
```

### Example Data

```tsx
const sanitarHeinzeCaseStudy = {
  quote: "Mercura allows us to significantly increase productivity in the quotation department.",
  author: {
    name: 'Maria Schmidt',
    title: 'Head of Sales',
    company: 'Sanitär-Heinze',
    logo: '/logos/sanitar-heinze.svg'
  },
  stats: [
    { value: '30%', label: 'More quotes processed', icon: <TrendingUp /> },
    { value: '75%', label: 'Faster turnaround', icon: <Clock /> },
    { value: '0', label: 'Knowledge lost', icon: <Brain /> },
  ]
}
```

---

## Component: `LandingFooter`

### File: `frontend/src/components/landing/LandingFooter.tsx`

### Structure

```tsx
const footerLinks = {
  product: [
    { label: 'Features', href: '#features' },
    { label: 'Pricing', href: '/pricing' },
    { label: 'Integrations', href: '/integrations' },
    { label: 'Documentation', href: '/docs' },
  ],
  company: [
    { label: 'About', href: '/about' },
    { label: 'Careers', href: '/careers' },
    { label: 'Blog', href: '/blog' },
    { label: 'Contact', href: '/contact' },
  ],
  legal: [
    { label: 'Privacy', href: '/privacy' },
    { label: 'Terms', href: '/terms' },
    { label: 'Security', href: '/security' },
    { label: 'DPA', href: '/dpa' },
  ],
}

const trustBadges = [
  { icon: <Shield />, label: 'SOC 2 Type II' },
  { icon: <ShieldCheck />, label: 'GDPR Compliant' },
  { icon: <Award />, label: 'Y Combinator S24' },
]
```

---

## CSS Utility Classes to Add

### File: `frontend/src/styles/landing.css`

```css
/* Landing Page Typography */
.hero-headline {
  @apply text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight;
  @apply bg-clip-text text-transparent;
  @apply bg-gradient-to-r from-slate-900 to-slate-700;
}

.hero-subheadline {
  @apply text-xl md:text-2xl text-slate-600 max-w-2xl mx-auto;
  @apply leading-relaxed;
}

.section-headline {
  @apply text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight;
  @apply text-slate-900;
}

.section-subheadline {
  @apply text-lg md:text-xl text-slate-600 max-w-2xl;
}

/* Landing Page Sections */
.landing-section {
  @apply py-20 md:py-28 lg:py-32;
}

.landing-section-alt {
  @apply py-20 md:py-28 lg:py-32 bg-slate-50;
}

.landing-section-dark {
  @apply py-20 md:py-28 lg:py-32 bg-slate-900 text-white;
}

/* CTA Button Variants */
.cta-primary {
  @apply inline-flex items-center justify-center;
  @apply px-8 py-4 rounded-xl;
  @apply bg-orange-500 hover:bg-orange-600;
  @apply text-white font-semibold;
  @apply shadow-lg shadow-orange-500/25;
  @apply transition-all duration-200;
  @apply hover:-translate-y-0.5;
}

.cta-secondary {
  @apply inline-flex items-center gap-2;
  @apply text-slate-600 hover:text-slate-900;
  @apply font-medium;
  @apply transition-colors;
}

/* Stat Counter Animation */
@keyframes countUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.stat-value {
  @apply text-4xl md:text-5xl font-bold;
  animation: countUp 0.5s ease-out;
}
```

---

## Import Order

```tsx
// LandingPage.tsx
import { LandingHeader } from '@/components/landing/LandingHeader'
import { HeroSection } from '@/components/landing/HeroSection'
import { LogoCloud } from '@/components/landing/LogoCloud'
import { ProblemSection } from '@/components/landing/ProblemSection'
import { HowItWorks } from '@/components/landing/HowItWorks'
import { FeatureBento } from '@/components/landing/FeatureBento'
import { ROICalculator } from '@/components/landing/ROICalculator'
import { FounderStory } from '@/components/landing/FounderStory'
import { CaseStudy } from '@/components/landing/CaseStudy'
import { LandingFooter } from '@/components/landing/LandingFooter'

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      <LandingHeader />
      <HeroSection {...heroProps} />
      <LogoCloud {...logoProps} />
      <ProblemSection />
      <HowItWorks />
      <FeatureBento />
      <ROICalculator />
      <FounderStory {...founderProps} />
      <CaseStudy {...caseStudyProps} />
      <LandingFooter />
    </main>
  )
}
```

---

*End of Component Specifications*
