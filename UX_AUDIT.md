# OpenMercura CRM UX Audit

## Core User Workflow
The primary job: **Turn RFQs (Requests for Quote) into sent quotes as fast as possible with maximum accuracy.**

Main flow: Dashboard → Smart Quote (upload/paste RFQ) → AI Extraction → Review → Send

---

## 🔍 1. DON'T MAKE ME THINK (Steve Krug)

### Critical Issues (Every Extra Click = Friction)

| Issue | Severity | Description |
|-------|----------|-------------|
| **No "Quick Quote" from Dashboard** | HIGH | The "Create New Quote" button works, but the dashboard stats (Pending RFQs, Follow-ups) aren't clickable. Users must hunt for the next action. |
| **Customer Selection Confusion** | HIGH | SmartQuote.tsx shows customer dropdown BEFORE file upload. But user flow is: get RFQ → extract → see who it's from. Current flow forces customer selection blind. |
| **"Edit Input" button in Review** | MEDIUM | After extraction, users see "Edit Input" which takes them BACK to the input page. Better: inline editing of extracted items. |
| **Inbox status ambiguity** | MEDIUM | Emails list shows status badges but no clear "action required" indicator. Users must decode colors (emerald = processed, but what next?) |
| **Multiple "Add" buttons** | MEDIUM | Sidebar has Customers, Projects, Products under "Inventory" but the primary action "Create Quote" is buried in top nav. |

### Specific Cognitive Load Points:

**Smart Quote Page (Step 1):**
```
Current: Select Customer → Upload File → Extract
Better: Upload File → AI Extracts → AI Suggests Customer → Confirm
```
The current flow makes users KNOW the customer before extraction. But the AI can extract customer info FROM the RFQ. This is backward.

**Review Page (Step 2):**
- Two-column layout is good (source | extraction)
- BUT: "Add Custom Item" is at bottom of list, requiring scroll
- Pricing insights show alerts/opportunities but the "Apply" action is small text

**Navigation Confusion:**
- "Quotes & RFQs" in sidebar - are these the same thing?
- "Inbox" vs "Emails" - which has RFQs?
- "Knowledge" vs "Cross Reference" - unclear distinction

---

## 💼 2. JOBS TO BE DONE (Clayton Christensen)

### The Core Job:
> "When I receive an RFQ, I want to turn it into a professional quote quickly so I can win the business before competitors respond."

### Feature/Job Alignment Analysis:

| Feature | Serves Core Job? | Verdict |
|---------|-----------------|---------|
| **Smart Quote with AI extraction** | YES - Directly accelerates quote creation | ✅ KEEP |
| **Side-by-side review** | YES - Catches errors before sending | ✅ KEEP |
| **Customer suggestions from AI** | YES - Reduces data entry | ✅ KEEP |
| **Project grouping** | MAYBE - Depends on user segment | ⚠️ DEFER |
| **QuickBooks Integration** | NO - This is post-job (accounting) | ⚠️ SECONDARY |
| **Knowledge Base** | NO - This is lookup, not quote creation | ⚠️ DEFER |
| **Cross Reference** | MAYBE - Only if SKU mismatch is common | ⚠️ DEFER |
| **Security page** | NO - This is admin/config | ⚠️ HIDE |
| **Analytics/Intelligence** | MAYBE - Nice to have, not core | ⚠️ DEFER |

### Business Decision Recommendations:

**REMOVE or DEFER for MVP:**
1. **"Knowledge" menu item** - Not part of core quote workflow
2. **"Cross Reference"** - Advanced feature, add later
3. **"Security" in main nav** - Move to user menu dropdown
4. **Project grouping** in quote creation - Adds complexity; most RFQs are one-off

**REORDER Navigation by Job Frequency:**
```
Current: Dashboard | Quotes & RFQs | Inbox | Inventory... | Tools...

Better: Dashboard | New Quote [CTA] | Inbox (RFQs) | Quotes | Customers
```

**The "Inbox" naming issue:**
- Users receive RFQs via email
- "Inbox" should probably be "RFQs" or "Quote Requests"
- "Emails" is too generic

---

## 🎨 3. REFACTORING UI (Wathan & Schoger)

### Visual Hierarchy Issues:

| Issue | Location | Fix |
|-------|----------|-----|
| **Competing CTAs** | TodayView - "Create New Quote" gradient button vs stats cards | Make stats cards clickable; reduce visual weight of secondary actions |
| **Too many borders** | Sidebar - every item has border on active state | Use background color alone for active state |
| **Inconsistent card shadows** | TodayView uses `shadow-[0_2px_20px_rgba(0,0,0,0.04)]` but Quotes uses flat | Standardize: subtle shadow on all cards or none |
| **Font weight inconsistency** | Some headings use `tracking-tighter`, some don't | Pick one style for page titles |
| **Badge overload** | QuoteReview has 5+ different badge styles | Consolidate: status (outlined), confidence (filled), alert (colored) |

### Spacing & Layout:

**Dashboard (TodayView.tsx):**
- Bento grid is visually interesting but:
  - The "Priorities" black card draws too much attention (should be secondary)
  - The stats cards at top (Pipeline Value) should be more prominent
  - The "AI Priorities" section wastes space when empty ("All caught up!")

**Smart Quote Page:**
- Good: Clear step indicator (Input → Review → Sending)
- Bad: Three input sections stacked (Customer, Project, Upload) with equal visual weight
- Better: Single clear drop zone, secondary options collapsed

**Emails Page:**
- Dark theme cards on dark background = low contrast
- Status stepper icons are too small (w-8 h-8)
- The progress steps don't clearly indicate "what do I do now?"

### Color & Contrast:

| Element | Issue |
|---------|-------|
| `text-gray-400` on sidebar labels | Too light for readability, use `text-gray-500` minimum |
| `bg-zinc-900` priorities card | Doesn't match the orange/white brand palette |
| Status badges in Emails | `emerald-400` on dark bg passes, but `slate-500` is too muted |
| Empty states | Gray icons on gray bg (`text-gray-300`) = looks disabled |

### Typography:

- **Inconsistent font sizes**: Page titles range from `text-2xl` to `text-4xl`
- **Inconsistent letter spacing**: Some use `tracking-tight`, some `tracking-tighter`, some default
- **Monospace for IDs**: Good! But inconsistent application

---

## 📋 Prioritized Fix List

### P0 (Fix Immediately - Blocking Core Job) ✅ COMPLETED

1. ✅ **Flip Smart Quote flow**: Upload/Input FIRST, then AI suggests customer
   - *Implemented: Document upload is now the hero section, customer/project/assignee are in a collapsed "Advanced Options" section*
   
2. ✅ **Make Dashboard stats clickable**: Pending RFQs → Inbox, Follow-ups → Quotes filtered
   - *Already implemented: Both stat cards navigate to their respective pages*
   
3. ✅ **Rename "Inbox" to "RFQ Inbox"** - clear intent
   - *Implemented: Sidebar now shows "RFQ Inbox" instead of "Inbox"*
   
4. ✅ **Hide Knowledge, Cross Reference from main nav** - add to "More" dropdown
   - *Implemented: Knowledge Base, Cross Reference, and Security are now in a collapsible "More" menu*
   - *Also fixed: Sidebar labels now use `text-gray-500` for better readability*
   - *Also fixed: Removed border from active sidebar items (using bg color only)*

### P1 (High Impact - Reduce Friction) ✅ COMPLETED

5. ✅ **Add empty state action**: When no quotes, show "Upload your first RFQ" with file drop zone
   - *Implemented: Quotes.tsx now shows a hero empty state with drag-drop styled link to Smart Quote*
   
6. ✅ **Consolidate badge styles** - max 3 variants
   - *Implemented: Added consolidated badge classes in index.css: `.badge-status-*` (outlined), `.badge-confidence-*` (filled), `.badge-alert-*` (colored)*
   
7. ✅ **Move Security to user menu** - reduce nav clutter
   - *Implemented: Security removed from "More" menu, now accessible via user dropdown in bottom-left corner*
   
8. ✅ **Fix sidebar active state** - remove border, use bg color only
   - *Already implemented in P0: SidebarItem uses `bg-orange-50` without border for active state*

### P2 (Polish - Trust & Professionalism) ✅ COMPLETED

9. ✅ **Standardize shadows** - all cards `shadow-sm` or `shadow-md`
   - *Implemented: TodayView cards now use consistent `shadow-sm` styling*
   
10. ✅ **Darken sidebar labels** - `text-gray-500` minimum
    - *Already implemented in P0: Sidebar section labels use `text-gray-500`*
    
11. ✅ **Remove zinc-900 card** - use white/orange theme consistently
    - *Implemented: AI Priorities card in TodayView now uses `bg-gradient-to-br from-orange-50 to-amber-50` with white task cards*
    
12. ✅ **Add inline editing** - don't make users go "back" to edit
    - *Already implemented: SmartQuote review has inline editing for name, SKU, quantity, and price fields*
    - *QuoteReview also has inline editing in the table view*

### P3 (Optimization) ✅ COMPLETED

13. ✅ **Animate progress** - The stepper in Emails should animate between states
    - *Implemented: ProgressStepper now has smooth CSS transitions, larger icons (w-10 h-10), loading bar animation, and "Ready to Quote!" indicator*
    
14. ✅ **Keyboard shortcuts** - `/` for search, `n` for new quote
    - *Implemented: Layout.tsx now has global keyboard listeners. `/` opens a command palette, `n` navigates to `/quotes/new`. Search bar in header shows shortcut hint.*
    
15. ✅ **Persistent preview** - Keep source document visible during all of review
    - *Already implemented: SmartQuote review step has permanent split-screen with source on left, extracted data on right*


---

## 💡 One Big Business Decision

**Should you REMOVE the manual quote creation entirely?**

Current state: Users can create quotes via:
- Smart Quote (AI extraction) ← This is the differentiator
- Manual entry (implied through Customers/Products) ← Commodity feature

**JTBD Argument**: Users aren't hiring you for "another form to fill out." They're hiring you to "convert RFQs fast." 

**Recommendation**: Make Smart Quote the ONLY path. If extraction fails, let them edit the extracted text inline rather than switching to "manual mode." This:
- Reduces code complexity
- Forces the AI to improve
- Creates consistent UX
- Differentiates from every other CRM

---

*Audit completed: 2026-02-06*
