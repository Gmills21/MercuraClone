# Customer Intelligence
## Simple, Actionable Insights for Sales Teams

---

## Design Philosophy

**"No data science degree required."**

Customer Intelligence transforms raw quote data into clear, actionable guidance that anyone can understand and act on.

### Key Principles:
1. **Plain English** - No jargon, no complexity
2. **Clear Actions** - Every insight tells you what to do
3. **Visual Simplicity** - Color-coded, easy to scan
4. **Context** - Explains *why* the insight matters

---

## Health Score (0-100)

A single number that tells you relationship strength at a glance.

```
╔══════════════════════════════════════╗
║           [84]  Excellent            ║
║                                      ║
║ This customer buys consistently.     ║
║ Prioritize their requests.           ║
╚══════════════════════════════════════╝
```

### Score Guide:
| Score | Color | Label | Meaning | Action |
|-------|-------|-------|---------|--------|
| **80-100** | 🟢 Green | Excellent | They trust you, buy often | Prioritize them |
| **60-79** | 🔵 Blue | Good | Solid relationship | Keep nurturing |
| **40-59** | 🟠 Amber | At Risk | Engagement dropping | Reach out soon |
| **0-39** | 🔴 Red | Needs Work | Relationship struggling | Schedule call |

### How It's Calculated:
```
Base Score: 50
+ Win Rate (up to 40 points)
+ Recent Activity (up to 10 points)
= Final Score (0-100)
```

---

## Customer Categories

Automatically groups customers based on behavior:

### 🌟 VIP Customers
**Criteria:** 70%+ win rate + recent activity

**What to do:**
- Prioritize their RFQs
- Offer them best pricing
- Check in regularly
- Ask for referrals

**Why it matters:** These are your best customers. Keep them happy.

---

### ✅ Active Customers
**Criteria:** Regular quote activity

**What to do:**
- Maintain relationship
- Watch for expansion opportunities
- Keep response times fast

**Why it matters:** Steady revenue stream. Don't get complacent.

---

### ⚠️ At Risk
**Criteria:** No quotes in 90+ days

**What to do:**
- Schedule check-in call immediately
- Ask if they're buying elsewhere
- Offer competitive pricing
- Address any service issues

**Why it matters:** You're about to lose them. Act now.

---

### ✨ New Customers
**Criteria:** No quotes yet

**What to do:**
- Send competitive first quote
- Follow up within 24 hours
- Make great first impression

**Why it matters:** First quote sets the tone for the relationship.

---

## Insights (The "What You Should Know" Section)

Each insight includes:
1. **Title** - What the insight is
2. **Description** - Why it matters
3. **Metric** - The number behind it
4. **Action** - What to do about it

### Example Insights:

#### 1. "VIP Customer - High Win Rate"
```
They accept 85% of your quotes. They trust your pricing and service.

Metric: 85% Win Rate
Action: [View Quote History]
```

**What to do:** Treat them like VIPs. Fast responses, best prices.

---

#### 2. "Price Sensitivity Detected"
```
Only 25% of quotes accepted. They may be shopping around for better prices.

Metric: 25% Win Rate
Action: [Review Competitor Pricing]
```

**What to do:** Check what competitors charge. Adjust pricing if needed.

---

#### 3. "Quote Gap - Customer Gone Quiet"
```
No quotes requested in 127 days. They might be buying elsewhere.

Metric: 127 Days Since Last Quote
Action: [Send Check-in Email]
```

**What to do:** Call them. Ask if they still need your products.

---

#### 4. "Fast Decision Maker"
```
They typically decide in 2 days. Quick turnarounds are their style.

Metric: 2 Days Avg Decision Time
Action: [Send Competitive Quote]
```

**What to do:** Be fast. They don't wait around.

---

## Predictions (What Might Happen Next)

Simple forecasts with confidence levels:

### Example Predictions:

#### "Order Expected Soon"
```
Prediction: Within 5 days
Confidence: Medium
Explanation: Based on their pattern of ordering every 30 days.
```

**What to do:** Be ready with inventory. Reach out proactively.

---

#### "Overdue for Next Order"
```
Prediction: Expected 12 days ago
Confidence: Medium
Explanation: They typically order every 30 days.
```

**What to do:** Call today. Find out if something's wrong.

---

#### "Likely to Accept Next Quote"
```
Prediction: High Probability
Confidence: High
Explanation: They've accepted 80% of quotes historically.
```

**What to do:** Send quote confidently. They're likely to buy.

---

## Dashboard Overview

### Top Section: Summary Cards
```
┌──────────┬──────────┬──────────┬──────────┐
│  Total   │   VIP    │  Active  │ At Risk  │
│    47    │    8     │   28     │    6     │
│ Customers│ High win │ Regular  │ 90+ days │
│          │   rate   │ quotes   │  quiet   │
└──────────┴──────────┴──────────┴──────────┘
```

### Middle Section: Recommended Actions
Shows only the most important actions based on current state:

```
┌─────────────────────────────────────────┐
│ ⚠️  6 Customers At Risk                 │
│                                         │
│ They haven't requested a quote in 90+   │
│ days. Reach out before you lose them.   │
│                                         │
│ [View At-Risk]                          │
└─────────────────────────────────────────┘
```

### Bottom Section: Customer Lists
Grouped by category (VIP, At Risk, Active, New)

Click any customer to see their full intelligence profile.

---

## Individual Customer Page

### Layout:
```
┌──────────────────────────────────────────────────┐
│  ACME Corp                          [Quote]      │
│  📧 acme@corp.com 🏢 ACME Industries             │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  Health Score: 84 (Excellent)      │
│  │    84    │  This customer buys consistently.  │
│  │  ━━━━━━  │  Prioritize their requests.       │
│  └──────────┘                                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  WHAT YOU SHOULD KNOW                            │
│  ┌────────────────────────────────────────────┐  │
│  │ 🔴 High Impact                              │  │
│  │ VIP Customer - High Win Rate                │  │
│  │ They accept 85% of your quotes...           │  │
│  │ Metric: 85% Win Rate                        │  │
│  │ [View Quote History]                        │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │ 🟡 Medium                                   │  │
│  │ 2 Quotes Need Follow-up                     │  │
│  │ $24,500 in pending quotes...                │  │
│  │ Metric: $24,500 Pending Value               │  │
│  │ [Follow Up Now]                             │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  WHAT MIGHT HAPPEN NEXT                          │
│  ┌────────────────────────────────────────────┐  │
│  │ Order Expected Soon                         │  │
│  │ Within 5 days • Medium confidence             │  │
│  │ Based on their pattern of ordering...       │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  BY THE NUMBERS         QUICK ACTIONS            │
│  Total Quotes: 12       [View Quote History]     │
│  Win Rate: 85%          [Contact Details]        │
│  Average: $4,200        [Create New Quote]       │
│  Lifetime: $45,600                               │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## Key Metrics Explained

### Win Rate
```
Quotes Accepted ÷ Total Quotes × 100

Example: 8 accepted ÷ 12 total = 67% win rate
```

**What it tells you:**
- **70%+**: They like your pricing
- **30-70%**: Room for improvement
- **<30%**: Price sensitive or shopping around

---

### Average Quote Value
```
Total Value of All Quotes ÷ Number of Quotes

Example: $50,400 ÷ 12 = $4,200 average
```

**What it tells you:** Typical deal size. Helps forecast revenue.

---

### Lifetime Value
```
Sum of All Accepted Quotes

Example: 8 accepted × $5,700 avg = $45,600 lifetime
```

**What it tells you:** Total revenue from this customer. Worth investing in the relationship.

---

### Days Since Last Quote
```
Today - Date of Last Quote

Example: 45 days since last quote
```

**What it tells you:**
- **<30 days**: Active relationship
- **30-90 days**: Normal gap
- **>90 days**: At risk

---

## User Flow

### Daily Check:
1. Open Intelligence Dashboard
2. Check "Recommended Actions"
3. Review At Risk customers
4. Click into individual customers for details

### Weekly Review:
1. Check VIP customers - any new ones?
2. Review win rate trends
3. Follow up on At Risk list
4. Reach out to New customers

### Before Creating Quote:
1. Check customer's intelligence page
2. Note their win rate (price accordingly)
3. Check their average order size
4. Review any pending follow-ups

---

## Business Value

### Before Customer Intelligence:
- ❌ Guess which customers need attention
- ❌ Miss at-risk customers until too late
- ❌ No visibility into win rates
- ❌ Treat all customers the same

### After Customer Intelligence:
- ✅ Clear priority list every day
- ✅ Catch at-risk customers early
- ✅ Price based on history
- ✅ VIP treatment for best customers

---

## Metrics to Track

| Metric | Target | Why |
|--------|--------|-----|
| **At Risk Recovery** | >40% | Save struggling relationships |
| **VIP Retention** | >95% | Keep best customers |
| **New Customer Conversion** | >60% | First quote success |
| **Insight Action Rate** | >50% | Are insights useful? |

---

## Implementation Status

✅ **COMPLETE:**
- Health score algorithm (0-100)
- Customer categorization (VIP/Active/At Risk/New)
- Actionable insights with clear explanations
- Simple predictions with confidence levels
- Dashboard overview with recommendations
- Individual customer intelligence pages
- Plain language throughout

⚠️ **FUTURE:**
- Email digest of weekly insights
- Competitor pricing impact on health score
- Industry benchmarks ("Your 65% win rate vs industry 58%")
- AI-powered recommendations

---

## The Pitch

> *"You don't need to be a data scientist to understand your customers. Our intelligence tells you in plain English: who needs attention, who's your best customer, and what to do next. It's like having a sales coach who knows your entire history."*

---

*Customer Intelligence makes data actionable. No charts to interpret. Just clear guidance on what to do.*
