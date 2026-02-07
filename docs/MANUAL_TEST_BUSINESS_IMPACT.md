# Manual Test Guide: Business Impact (ROI) - Test 4

## Quick Start

**URL**: http://localhost:5173  
**Test Duration**: ~3 minutes  
**Expected Grade**: A

---

## Step-by-Step Test Instructions

### 1. Navigate to Business Impact Tab
- Open http://localhost:5173 in your browser
- Look for "Business Impact" or "ROI" in the sidebar navigation
- Click to navigate to the Business Impact page

### 2. Input Test Data

Enter the following values in the ROI Calculator:

| Field | Value | Notes |
|-------|-------|-------|
| **Annual Requests** | `1000` | RFQs per year |
| **Team Size** | `3` | Number of employees |
| **Manual Processing Time** | `60` | Minutes per quote (1 hour) |
| **Avg Quote Value** | `400` | Dollar amount |

### 3. Verify Calculated Results

The calculator should display (within ~1 second):

#### ✅ Potential Savings Card (Dark Background)
- **Expected Value**: **$18,300**
- **Location**: Left card in the output section
- **Visual Check**: 
  - Dark background (slate-900)
  - White text
  - Yellow lightning icon
  - Shows "966.7 hours saved annually" below

#### ✅ Revenue Upside Card (Light Background)
- **Expected Value**: **$1,500**
- **Location**: Right card in the output section
- **Visual Check**:
  - White background
  - Dark text
  - Green trending-up icon
  - Shows "Projected pipeline lift" below

---

## Grade A Checklist

### Calculations (25 points)
- [ ] Potential Savings = **$18,300** (exact match)
- [ ] Revenue Upside = **$1,500** (exact match)
- [ ] Currency symbol is **$** (not €)
- [ ] Hours saved shows **966.7 hours**

### UI/UX (25 points)
- [ ] Layout uses **Bento Grid** (two-column design)
- [ ] Input fields have **icons** (Clock, Users, DollarSign)
- [ ] Cards have **rounded corners** (not blocky)
- [ ] **Hover effects** work (cards scale up slightly)
- [ ] Real-time updates (change input → see "Updating..." → results change)

### Visuals (25 points)
- [ ] **High contrast** between dark and light cards
- [ ] Typography is **clean and modern** (not default browser font)
- [ ] Colors are **not pure black/white** (uses slate-900, slate-50)
- [ ] **Micro-animations** present (smooth transitions)
- [ ] "The Velocity Advantage" box at bottom is styled well

### Trust Signals (25 points)
- [ ] "Live Metrics" badge visible in header
- [ ] Separate **Performance Dashboard** section below calculator
- [ ] Shows actual data (Time Saved, Quotes, Win Rate, Revenue)
- [ ] Contextual explanation provided ("The Velocity Advantage")

---

## Common Issues & Fixes

### Issue: Results don't match expected values
**Fix**: Ensure you entered `60` minutes (not `1` hour) in the Manual Processing Time field

### Issue: Currency shows € instead of $
**Fix**: This should not happen - the code has been updated. If you see this, report it immediately.

### Issue: Calculator doesn't update in real-time
**Fix**: Check browser console for errors. The API endpoint `/impact/simulate` should be responding.

### Issue: UI looks "blocky" or basic
**Fix**: Ensure Tailwind CSS is loaded. Check that the page doesn't have console errors.

---

## Grading Rubric Reference

| Grade | Criteria |
|-------|----------|
| **A** | ✅ Calculations match benchmarks<br>✅ Golden Stack UI (Tailwind + Shadcn patterns)<br>✅ Apple-esque design (rounded, shadowed, premium)<br>✅ Both metrics displayed prominently |
| **B** | ✅ Math correct but lacks Revenue Upside<br>⚠️ UI is functional but "vibe-coded" (blocky)<br>⚠️ Displays data but doesn't "sell" the vision |
| **C** | ⚠️ Results are static or hard-coded<br>❌ Navigation cluttered<br>❌ Just a list of numbers without hierarchy |
| **F** | ❌ Backend error in business_impact_service.py<br>❌ Displays raw JSON<br>❌ No trust signals |

---

## Expected Visual Appearance

### Header Section
```
┌─────────────────────────────────────────────────────────┐
│ Business Impact & ROI              [🟢 Live Metrics]    │
│ Validate the value of high-velocity quoting.            │
└─────────────────────────────────────────────────────────┘
```

### ROI Calculator Section
```
┌─────────────────────────────────────────────────────────┐
│ 🧮 ROI Calculator                                       │
│                                                          │
│ ┌──────────────┬──────────────────────────────────────┐ │
│ │  INPUTS      │  OUTPUTS                             │ │
│ │              │                                       │ │
│ │ Annual Req.  │  ┌──────────┐  ┌──────────┐         │ │
│ │ [1000     ]  │  │ ⚡ $18,300│  │ 📈 $1,500│         │ │
│ │              │  │ Savings  │  │ Revenue  │         │ │
│ │ Team Size    │  └──────────┘  └──────────┘         │ │
│ │ [3        ]  │                                       │ │
│ │              │  The Velocity Advantage               │ │
│ │ Manual Time  │  By automating 1,000 requests...     │ │
│ │ [60       ]  │                                       │ │
│ │              │                                       │ │
│ │ Avg Value    │                                       │ │
│ │ [$400     ]  │                                       │ │
│ └──────────────┴──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Performance Dashboard Section
```
┌─────────────────────────────────────────────────────────┐
│ Performance Dashboard          Based on your actual usage│
│                                                          │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │
│ │ ⏱ 0h │ │ 📄 0 │ │ 🎯 0%│ │ 💼 $0│                   │
│ │ Time │ │Quote │ │ Win  │ │Revenu│                   │
│ └──────┘ └──────┘ └──────┘ └──────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## Test Result Recording

**Test Date**: _______________  
**Tester**: _______________

### Results
- [ ] **Calculations**: PASS / FAIL
- [ ] **UI/UX**: PASS / FAIL
- [ ] **Visuals**: PASS / FAIL
- [ ] **Trust Signals**: PASS / FAIL

### Overall Grade: _____ (A / B / C / F)

### Notes:
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

---

## Next Steps After Testing

### If Grade A ✅
- Document success in test log
- Take screenshots for portfolio
- Move to next test (Test 5 or other)

### If Below Grade A ⚠️
- Review the specific failing criteria
- Check the detailed report: `docs/TEST_4_BUSINESS_IMPACT_REPORT.md`
- Verify API is running: `http://localhost:8000/docs`
- Check browser console for errors

---

## Support

**Backend Service**: `app/business_impact_service.py`  
**Frontend Component**: `frontend/src/pages/BusinessImpact.tsx`  
**API Routes**: `app/routes/impact.py`  
**Detailed Report**: `docs/TEST_4_BUSINESS_IMPACT_REPORT.md`

**Test Verification Script**: Run `python test_roi_calculation.py` to verify backend calculations
