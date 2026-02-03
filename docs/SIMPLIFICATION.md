# Simplification & Onboarding
## Reducing Friction for New Users

---

## Problem We Solved

**Before:**
- 6 stats on dashboard (overwhelming)
- Empty pages with "No data" messages
- All features visible at once (confusing)
- No guidance for new users

**After:**
- 4 key stats only
- Empty pages with clear next steps
- Progressive feature disclosure
- Guided 5-step onboarding

---

## 1. Getting Started Checklist

### What It Is:
A progressive checklist that guides new users through their first experience.

### Where It Appears:
At the top of the Today View dashboard.

### The 5 Steps:
```
┌─────────────────────────────────────────────────────────┐
│ Getting Started                              [Dismiss] │
│ 1 of 5 completed                                       │
│ [████████░░░░░░░░░░] 20%                               │
├─────────────────────────────────────────────────────────┤
│ Recommended next:                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Create Your First Quote                             │ │
│ │ Try Smart Quote with a sample RFQ or paste a real one│ │
│ │                                         [Create →]  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ View all steps →                                        │
└─────────────────────────────────────────────────────────┘
```

### Steps:
1. **Create Your First Quote** - Try Smart Quote
2. **Add a Customer** - Build your customer base
3. **Check Customer Intelligence** - See AI insights
4. **Connect QuickBooks (Optional)** - Sync data
5. **View Business Impact** - See ROI

### Behavior:
- Shows until 3+ steps completed
- Can be dismissed anytime
- Progress bar shows completion
- Next step highlighted in orange
- Completed steps marked with checkmark

---

## 2. Progressive Disclosure (Simplified Mode)

### What It Is:
New users see only essential features. Advanced features unlock after 10 quotes.

### Simplified Mode Shows:
- ✅ Today View (simplified)
- ✅ Smart Quote
- ✅ Basic Quotes
- ✅ Customers
- ✅ Alerts
- ✅ Camera Capture
- ✅ Business Impact

### Hidden Until 10 Quotes:
- 🔒 Customer Intelligence
- 🔒 Competitor Analysis
- 🔒 Advanced Analytics

### Auto-Progression:
```
After 10 quotes created:
┌─────────────────────────────────────────┐
│ 🎉 You've unlocked Advanced Mode!       │
│                                         │
│ New features available:                 │
│ • Customer Intelligence                 │
│ • Competitor Analysis                   │
│ • Advanced Analytics                    │
│                                         │
│ [Explore New Features]                  │
└─────────────────────────────────────────┘
```

---

## 3. Contextual Empty States

### Problem:
Blank pages with "No data" confuse new users.

### Solution:
Every empty page now shows clear next steps.

### Examples:

#### No Quotes Yet:
```
┌─────────────────────────────────────────┐
│ 📄 No Quotes Yet                        │
│                                         │
│ Start by adding a customer, then create │
│ your first quote                        │
│                                         │
│ [Add Your First Customer]               │
│                                         │
│ Quotes help you track opportunities and │
│ close deals faster                      │
└─────────────────────────────────────────┘
```

#### No Customers Yet:
```
┌─────────────────────────────────────────┐
│ 👥 No Customers Yet                     │
│                                         │
│ Add your first customer to get started  │
│                                         │
│ [Add First Customer]                    │
│ [Import from QuickBooks]                │
│                                         │
│ Customers are the foundation of your    │
│ sales workflow                          │
└─────────────────────────────────────────┘
```

#### No Intelligence Data:
```
┌─────────────────────────────────────────┐
│ 📊 Intelligence Needs Data              │
│                                         │
│ Create a few quotes first to see        │
│ customer insights                       │
│                                         │
│ [Create a Quote]                        │
│                                         │
│ After 2-3 quotes per customer, we'll    │
│ show health scores and predictions      │
└─────────────────────────────────────────┘
```

---

## 4. Simplified Stats Row

### Before (6 stats):
```
[Pending] [Follow-ups] [New RFQs] [Expiring] [Low Stock] [Win Rate]
```

### After (4 stats):
```
[Pending Quotes] [Follow-ups] [New RFQs] [Win Rate]
```

### Removed:
- Expiring Quotes (still in alerts)
- Low Stock (still accessible in products)

### Why:
- Less overwhelming for new users
- Focus on what matters most
- Advanced metrics in respective pages

---

## 5. Quick Tips

### What:
After completing onboarding, rotating tips appear.

### Example:
```
┌─────────────────────────────────────────┐
│ 💡 Quick Tip                            │
│                                         │
│ Smart Quote is Your Superpower          │
│ Paste any RFQ email and AI extracts the │
│ items automatically. Saves 16 minutes.  │
│                                         │
│ [Next tip →]                            │
└─────────────────────────────────────────┘
```

### Tips Rotate Through:
1. Smart Quote saves 16 minutes
2. Check alerts daily for urgent items
3. Health scores above 80 are excellent
4. Track your impact for ROI proof

---

## Implementation

### Backend:

**onboarding_service.py:**
- Track checklist progress
- Simplified vs Advanced mode logic
- Auto-switch after 10 quotes

**empty_states_service.py:**
- Contextual empty state content
- Different states per page
- Clear CTAs

**Routes:**
- `GET /onboarding/checklist` - Get progress
- `POST /onboarding/complete/{step}` - Mark done
- `GET /onboarding/empty-state/{page}` - Get empty state

### Frontend:

**GettingStarted.tsx:**
- Collapsible checklist
- Progress bar
- Next step highlight
- Dismissible

**TodayView.tsx:**
- Shows GettingStarted at top
- Simplified 4-stat layout
- Quick tips after onboarding

---

## User Flow

### New User:
```
1. Sign up
2. See Today View with Getting Started checklist
3. Complete step 1: Create first quote
4. Progress bar updates
5. Continue through 5 steps
6. Checklist auto-hides after 3 steps
7. Quick tips appear instead
8. After 10 quotes → Unlock Advanced Mode
```

### Returning User:
```
1. Log in
2. See Today View (no checklist)
3. See priority tasks
4. Access all features
```

---

## Success Metrics

| Metric | Target | How to Track |
|--------|--------|--------------|
| Checklist completion rate | >70% | API logs |
| Time to first quote | <5 min | Analytics |
| Feature discovery | All users find Smart Quote | Heatmaps |
| Support tickets | Reduced 40% | Ticket volume |

---

## The Pitch

> *"We don't throw 20 features at new users on day one. We guide them through the essentials first. Create a quote, add a customer, see the value. Advanced features unlock as they grow. It's like having a personal onboarding coach."*

---

*Simplification makes OpenMercura approachable for new users while still powerful for power users.*
