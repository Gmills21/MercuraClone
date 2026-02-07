# Visual Reference: Business Impact ROI Calculator

## What You Should See in the Browser

### Page Header
```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║  Business Impact & ROI                    🟢 Live Metrics         ║
║  Validate the value of high-velocity quoting.                     ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

---

### ROI Calculator Section

#### Input Panel (Left Side - Light Gray Background)
```
┌─────────────────────────────────┐
│  Annual Requests                │
│  ┌───────────────────────────┐  │
│  │ 1000              RFQs/yr │  │
│  └───────────────────────────┘  │
│                                 │
│  Team Size                      │
│  ┌───────────────────────────┐  │
│  │ 👥 3          Employees   │  │
│  └───────────────────────────┘  │
│                                 │
│  Manual Processing Time         │
│  ┌───────────────────────────┐  │
│  │ ⏱️ 60        Mins/Quote   │  │
│  └───────────────────────────┘  │
│                                 │
│  Avg Quote Value                │
│  ┌───────────────────────────┐  │
│  │ 💲 400                    │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### Output Panel (Right Side - White Background)
```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌─────────────────────┐  ┌─────────────────────┐      │
│  │ ⚡ Potential Savings │  │ 📈 Revenue Upside   │      │
│  │                     │  │                     │      │
│  │     $18,300         │  │      $1,500         │      │
│  │                     │  │                     │      │
│  │ Based on 966.7 hrs  │  │ Projected pipeline  │      │
│  │ saved annually      │  │ lift from velocity  │      │
│  └─────────────────────┘  └─────────────────────┘      │
│  [DARK BACKGROUND]        [LIGHT BACKGROUND]           │
│  [WHITE TEXT]             [DARK TEXT]                  │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ 🎯 The Velocity Advantage                      │    │
│  │                                                 │    │
│  │ By automating 1,000 requests, you reclaim      │    │
│  │ 966.7 hours of skilled labor. In a high-       │    │
│  │ velocity sales culture, this translates        │    │
│  │ directly to market dominance.                  │    │
│  └────────────────────────────────────────────────┘    │
│  [ORANGE BACKGROUND]                                    │
└──────────────────────────────────────────────────────────┘
```

---

### Performance Dashboard (Below Calculator)
```
╔════════════════════════════════════════════════════════════════════╗
║  Performance Dashboard              Based on your actual usage     ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         ║
║  │ ⏱️ Time  │  │ 📄 Quotes│  │ 🎯 Win   │  │ 💼 Revenue│         ║
║  │  Saved   │  │          │  │  Rate    │  │          │         ║
║  │          │  │          │  │          │  │          │         ║
║  │   0h     │  │    0     │  │   0%     │  │   $0     │         ║
║  └──────────┘  └──────────┘  └──────────┘  └──────────┘         ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## Color Scheme Reference

### Primary Colors
- **Background**: `#f8fafc` (Slate-50) - Not pure white
- **Dark Cards**: `#0f172a` (Slate-900) - Not pure black
- **Accent**: `#f97316` (Orange-600) - Brand color
- **Success**: `#10b981` (Emerald-500) - Positive metrics

### Text Colors
- **Headings**: `#0f172a` (Slate-900)
- **Body**: `#64748b` (Slate-500)
- **Labels**: `#475569` (Slate-600)

### Interactive States
- **Focus Ring**: Orange-500 with 2px width
- **Hover**: Scale to 105% over 300ms
- **Border**: Slate-200 (subtle, not harsh)

---

## Typography Reference

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 
             'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 
             'Helvetica Neue', sans-serif;
```

### Sizes
- **Page Title**: 30px (text-3xl), Bold, Tight tracking
- **Section Headings**: 24px (text-2xl), Bold
- **Big Numbers**: 36px (text-4xl), Bold, Tight tracking
- **Labels**: 14px (text-sm), Semibold
- **Body**: 16px (text-base), Regular

---

## Visual Characteristics to Verify

### ✅ Premium Design Elements
- [ ] **Rounded Corners**: All cards have 16px border radius (rounded-2xl)
- [ ] **Shadows**: Subtle, layered shadows (not harsh drop shadows)
- [ ] **Spacing**: Generous padding (p-6, p-8) - not cramped
- [ ] **Icons**: Lucide icons with consistent sizing (20-24px)
- [ ] **Transitions**: Smooth 300ms animations on hover

### ✅ Layout Quality
- [ ] **Responsive**: Two columns on desktop, stacks on mobile
- [ ] **Alignment**: Everything properly aligned (no jagged edges)
- [ ] **Hierarchy**: Clear visual hierarchy (big numbers stand out)
- [ ] **Whitespace**: Breathing room between elements

### ✅ Interactive Feedback
- [ ] **Input Focus**: Orange ring appears when clicking input fields
- [ ] **Hover Effects**: Cards scale up slightly on hover
- [ ] **Real-time Updates**: "Updating..." appears when changing inputs
- [ ] **Smooth Transitions**: No jarring jumps or flashes

---

## Comparison: Grade A vs Grade C

### Grade A (What You Should See)
```
┌─────────────────────────────────────────────────┐
│ 🧮 ROI Calculator                               │
│                                                 │
│ ┌──────────┬────────────────────────────────┐  │
│ │  INPUTS  │  OUTPUTS                       │  │
│ │          │                                 │  │
│ │  Clean   │  ┏━━━━━━━━┓  ┌────────┐       │  │
│ │  Modern  │  ┃ $18,300┃  │ $1,500 │       │  │
│ │  Icons   │  ┗━━━━━━━━┛  └────────┘       │  │
│ │  Spacing │  Dark Card    Light Card       │  │
│ └──────────┴────────────────────────────────┘  │
│                                                 │
│ Smooth animations, premium feel                │
└─────────────────────────────────────────────────┘
```

### Grade C (What to Avoid)
```
┌─────────────────────────────────────────────────┐
│ Business Impact                                 │
│                                                 │
│ Requests: [1000]                                │
│ Employees: [3]                                  │
│ Time: [60]                                      │
│ Value: [400]                                    │
│                                                 │
│ Savings: 18300                                  │
│ Upside: 1500                                    │
│                                                 │
│ Blocky, no visual hierarchy, plain numbers     │
└─────────────────────────────────────────────────┘
```

---

## Screenshot Checklist

When taking screenshots for documentation, capture:

1. **Full Calculator View**: Showing both input and output panels
2. **Hover State**: Card with scale-up animation
3. **Focus State**: Input field with orange ring
4. **Mobile View**: Responsive layout on narrow screen
5. **Performance Dashboard**: Bottom section with actual metrics

---

## Browser Compatibility

Tested and verified on:
- ✅ Chrome/Edge (Chromium-based)
- ✅ Firefox
- ✅ Safari

**Minimum Screen Width**: 320px (mobile)  
**Optimal Screen Width**: 1024px+ (desktop)

---

## Accessibility Features

- [ ] **Keyboard Navigation**: Tab through all inputs
- [ ] **Focus Indicators**: Visible focus rings
- [ ] **Labels**: All inputs have descriptive labels
- [ ] **Color Contrast**: WCAG AA compliant (4.5:1 minimum)
- [ ] **Semantic HTML**: Proper heading hierarchy

---

## Performance Expectations

- **Initial Load**: < 1 second
- **Calculation Update**: < 500ms (debounced)
- **Animation Duration**: 300ms (smooth, not sluggish)
- **API Response**: < 200ms (local server)

---

## Common Visual Issues & Fixes

### Issue: Cards look "blocky"
**Cause**: Border radius not applied  
**Check**: Should have `rounded-2xl` class (16px radius)

### Issue: Colors look harsh
**Cause**: Using pure black (#000) or pure white (#fff)  
**Check**: Should use Slate-900 and Slate-50

### Issue: No hover effects
**Cause**: Tailwind not loaded or CSS conflict  
**Check**: Browser console for errors

### Issue: Layout broken on mobile
**Cause**: Responsive classes not working  
**Check**: Viewport meta tag present in HTML

---

## Final Visual Quality Check

Before marking as Grade A, verify:

1. **First Impression**: Does it look premium and professional?
2. **Typography**: Clean, modern, not default browser font?
3. **Colors**: Harmonious palette, not jarring?
4. **Spacing**: Generous whitespace, not cramped?
5. **Animations**: Smooth and subtle, not distracting?
6. **Hierarchy**: Big numbers stand out, labels are secondary?
7. **Consistency**: All elements follow same design language?

If you can answer "YES" to all 7 questions → **Grade A** ✅

---

**Last Updated**: February 3, 2026  
**Reference**: `frontend/src/pages/BusinessImpact.tsx`  
**Design System**: Tailwind CSS + Custom Components
