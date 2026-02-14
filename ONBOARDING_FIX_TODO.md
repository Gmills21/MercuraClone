# MercuraClone Onboarding Fix TODO

## Backend Changes

### 1. Auth Routes (app/routes/auth.py)
- [x] Add /register endpoint for self-service signup
- [x] Create organization on registration
- [x] Return auth token on successful registration
- [x] No admin approval required (self-service)

### 2. Auth Module (app/auth.py)
- [x] Add register_user function
- [x] Handle organization creation
- [x] Hash passwords properly

### 3. Models (app/models.py / app/models_organization.py)
- [x] Ensure organization model supports auto-creation
- [x] Add onboarding flags to user/organization

## Frontend Changes

### 1. API Service (frontend/src/services/api.ts)
- [x] Add authApi with login, register, logout
- [x] Add token management
- [x] Remove hardcoded TEST_USER_ID
- [x] Add auth token interceptor

### 2. Auth Context (frontend/src/contexts/AuthContext.tsx)
- [x] Create auth context for managing auth state
- [x] Handle token storage
- [x] Provide login/logout/register methods

### 3. Landing Page Fixes
- [x] HeroSection.tsx - Remove "SOC 2 Certified", "Backed by Y Combinator"
- [x] HeroSection.tsx - Remove "16hrs saved/week" or make realistic
- [x] LogoCloud.tsx - Remove "SOC 2 Type II" badge
- [x] LogoCloud.tsx - Remove "Y Combinator" badge
- [x] ROICalculator.tsx - Remove "98% retention" claim
- [x] Update CTAs to point to signup flow

### 4. Onboarding Wizard (frontend/src/components/onboarding/)
- [x] Create OnboardingWizard.tsx
- [x] Step 1: Upload Product Catalog (CSV/Excel)
- [x] Step 2: Connect QuickBooks (optional skip)
- [x] Step 3: Upload Sample RFQ/Email
- [x] Add progress indicator
- [x] Add skip options for each step

### 5. Demo Data Feature
- [x] Add "Try with demo data" button to TodayView empty state
- [x] Create demo data service
- [x] Add API endpoint for loading demo data
- [x] Make demo data realistic (industrial distribution)

### 6. Empty States
- [x] Make TodayView empty state actionable
- [x] Add clear CTAs for first-time users
- [x] Guide to upload first RFQ

### 7. Quick Start Guide
- [x] Add contextual tooltips
- [x] First-run highlights on dashboard
- [x] Helpful hints in key areas

## Database Changes
- [x] Add demo_data_loaded flag to organization
- [x] Add onboarding_completed flag
- [x] Add onboarding_step tracking

## Testing
- [x] Test registration flow end-to-end
- [x] Test onboarding wizard
- [x] Test demo data loading
- [x] Verify all false claims removed
