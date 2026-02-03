# Today View Dashboard
## Your Daily Command Center

---

## Overview

**Today View** is the main dashboard that greets users when they open OpenMercura. It shows exactly what needs attention right now - no fluff, just actionable intelligence.

---

## Design Philosophy

### "What do I need to do RIGHT NOW?"

Unlike generic dashboards that show everything, Today View prioritizes:
1. **Urgent tasks** (RFQs to process, follow-ups needed)
2. **Time-sensitive items** (expiring quotes, pending approvals)
3. **Quick actions** (create quote, add customer, etc.)
4. **Motivation** (progress toward goals, insights)

---

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Good morning, Reg                    [Create Quote]        │
│  Friday, January 31, 2026                                   │
├─────────────────────────────────────────────────────────────┤
│  [Pending] [Follow-ups] [New RFQs] [Expiring] [Stock] [Win] │
├───────────────────────────────┬─────────────────────────────┤
│                               │                             │
│  PRIORITY TASKS               │  QUICK ACTIONS              │
│  ┌─────────────────────────┐  │  [Create Smart Quote]       │
│  │ 5 New RFQ Emails        │  │  [Add Customer]             │
│  │ Process Now →           │  │  [Add Product]              │
│  ├─────────────────────────┤  │  [QuickBooks Sync]          │
│  │ 3 Quotes Need Follow-up │  ├─────────────────────────────┤
│  │ View Quotes →           │  │  TODAY'S INSIGHT            │
│  ├─────────────────────────┤  │  You have 12 pending...     │
│  │ 2 Quotes Expiring Soon  │  ├─────────────────────────────┤
│  │ Review →                │  │  THIS WEEK'S GOALS          │
│  └─────────────────────────┘  │  Quotes: 12/20 ████████░░   │
│                               │  Value: $45K/$100K ████░░░  │
│  FOLLOW-UPS NEEDED            │  Win Rate: 64%/70% ███████░ │
│  ┌─────────────────────────┐  ├─────────────────────────────┤
│  │ ACME Corp    $12,500    │  │  THIS MONTH                 │
│  │ 5 days → [Follow Up]    │  │  Quotes: 47                 │
│  ├─────────────────────────┤  │  Value: $284,500            │
│  │ Beta Inc     $8,750     │  │  New Customers: 8           │
│  │ 4 days → [Follow Up]    │  └─────────────────────────────┘
│  └─────────────────────────┘                               │
│                                                             │
│  RECENT ACTIVITY                                            │
│  • Quote Created - ACME Corp - $12,500 - 2h ago            │
│  • RFQ Received - New request - 3h ago                     │
│  • Quote Sent - Beta Inc - $8,750 - 5h ago                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Smart Greeting
- Time-aware: "Good morning", "Good afternoon", "Good evening"
- Personalized with user's name
- Shows current date prominently

### 2. Stats Row (6 Key Metrics)
| Metric | Icon | Shows |
|--------|------|-------|
| **Pending Quotes** | FileText | Count + total value |
| **Follow-ups** | Clock | Quotes >3 days old |
| **New RFQs** | Mail | Unprocessed emails |
| **Expiring** | AlertCircle | Quotes >14 days old |
| **Low Stock** | Package | Inventory alerts |
| **Win Rate** | TrendingUp | Monthly performance |

**Visual indicators:**
- Red = Urgent (>0)
- Amber = Attention needed
- Gray = Normal

### 3. Priority Tasks
Automatically surfaces what needs action:
- **New RFQ Emails** → Link to inbox
- **Follow-ups Needed** → Link to quotes
- **Expiring Quotes** → Link to review

Empty state: "All caught up!" with checkmark

### 4. Follow-ups List
Shows specific quotes needing follow-up:
- Customer name + avatar
- Quote amount
- Days since sent
- Quick action buttons: "View Quote" | "Follow Up"

### 5. Recent Activity
Chronological feed of:
- Quotes created/sent
- RFQs received
- Customer additions

### 6. Quick Actions
One-click access to common tasks:
- Create Smart Quote (highlighted)
- Add Customer
- Add Product
- QuickBooks Sync

### 7. Today's Insight
Contextual intelligence:
> "You have 12 pending quotes worth $156,000. Following up on quotes >3 days old could increase your win rate by 23%."

### 8. This Week's Goals
Progress bars for:
- Quotes sent (target: 20)
- Quote value (target: $100K)
- Win rate (target: 70%)

### 9. This Month Summary
Quick stats:
- Total quotes sent
- Total value
- Average response time
- New customers

---

## Intelligence Features

### Automatic Prioritization
Tasks are ordered by urgency:
1. **High**: New RFQs (revenue opportunity)
2. **High**: Follow-ups (at-risk deals)
3. **Medium**: Expiring quotes (time-sensitive)

### Smart Follow-up Detection
Automatically flags quotes needing attention:
```typescript
// Quotes sent >3 days ago with no response
const needsFollowUp = 
  quote.status === 'sent' && 
  daysSinceSent > 3;
```

### Expiring Quote Alerts
Flags quotes approaching expiration:
```typescript
// Quotes sent >14 days ago
const expiring = 
  quote.status === 'sent' && 
  daysSinceSent > 14;
```

### Time-Aware Greetings
```typescript
if (hour < 12) "Good morning"
else if (hour < 17) "Good afternoon"
else "Good evening"
```

---

## Implementation

### File: `TodayView.tsx`
- **Lines**: ~550
- **Components**: Single comprehensive component
- **Data loading**: Parallel API calls
- **Real-time**: Refreshes on mount

### Data Sources
```typescript
const [quotesRes, customersRes, emailsRes] = await Promise.all([
  quotesApi.list(100),      // For pending/follow-ups
  customersApi.list(100),   // For stats
  emailsApi.list('pending', 50),  // For new RFQs
]);
```

### Calculated Stats
```typescript
{
  pendingQuotes: quotes.filter(q => q.status === 'draft' || q.status === 'sent').length,
  pendingValue: quotes.reduce((sum, q) => sum + q.total, 0),
  followUpsNeeded: quotes.filter(q => daysSinceSent > 3).length,
  newEmails: emails.length,
  expiringQuotes: quotes.filter(q => daysSinceSent > 14).length
}
```

---

## User Flows

### Morning Routine
1. Open OpenMercura
2. See greeting + today's date
3. Check Priority Tasks
4. Process new RFQs first
5. Handle follow-ups
6. Create new quotes

### End of Day
1. Check stats row
2. Review progress toward weekly goals
3. Ensure no urgent tasks remain
4. Plan tomorrow's follow-ups

---

## Future Enhancements

### Phase 2:
- [ ] **Calendar integration** (show today's meetings)
- [ ] **Weather widget** (if relevant for site visits)
- [ ] **Task reminders** (user-created todos)
- [ ] **Notifications panel** (alerts, mentions)

### Phase 3:
- [ ] **AI suggestions** ("You usually call ACME on Fridays")
- [ ] **Pipeline view** (visual funnel of quotes)
- [ ] **Revenue forecast** (based on pending quotes)
- [ ] **Competitor alerts** ("Competitor X dropped prices")

### Phase 4:
- [ ] **Personalization** (reorder widgets based on usage)
- [ ] **Custom goals** (user-defined targets)
- [ ] **Team view** (manager dashboard)
- [ ] **Mobile optimization** (today view for phone)

---

## Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| **Task Completion** | >80% | Are users acting on priorities? |
| **Quote Creation** | +30% | Is dashboard driving action? |
| **Follow-up Rate** | >60% | Are at-risk deals being saved? |
| **Time to First Action** | <30s | Is layout intuitive? |

---

## The Pitch

> *"Don't open a spreadsheet. Don't check your email. Just open OpenMercura and know exactly what to do today. It's like having a sales assistant who never sleeps."*

---

*This is the command center of OpenMercura. Everything else is just a detail view.*
