# Authentication & Multi-Tenancy Architecture Audit

## Date: 2026-02-02
## Status: NEEDS ENHANCEMENT

---

## ✅ WHAT YOU HAVE

### 1. **Authentication System** (`app/auth.py`)
- ✅ Password hashing with PBKDF2 + Salt
- ✅ Token-based authentication (32-byte secure tokens)
- ✅ Token expiration (30 days)
- ✅ User login/logout
- ✅ Role-based access control (admin, manager, sales_rep, viewer)
- ✅ Default admin user (admin@openmercura.local / admin123)

### 2. **API Routes** (`app/routes/auth.py`)
- ✅ POST /auth/login - User login
- ✅ POST /auth/logout - User logout
- ✅ GET /auth/me - Get current user info
- ✅ POST /auth/users - Create new user (admin/manager only)
- ✅ GET /auth/users - List users in company (admin/manager only)
- ✅ Bearer token authentication dependency

### 3. **Database Schema** (`app/database_sqlite.py`)
- ✅ Users table with:
  - id, email, name, password_hash
  - role, company_id (for multi-tenancy!)
  - created_at, last_login, is_active
- ✅ Default admin user seeded

### 4. **Multi-Tenancy Foundation**
- ✅ `company_id` field in users table
- ✅ `list_users()` filters by company_id
- ✅ Role hierarchy (viewer < sales_rep < manager < admin)

### 5. **Billing/Subscription Models** (`app/models_billing.py`)
- ✅ Subscription plans (per-seat pricing)
- ✅ Subscription status tracking
- ✅ Invoice management
- ✅ Payment methods
- ✅ Seat assignments
- ✅ Billing address
- ✅ Usage tracking

### 6. **Billing Routes** (`app/routes/billing.py`)
- ✅ GET /billing/plans
- ✅ POST /billing/checkout/create-session
- ✅ GET /billing/subscription
- ✅ POST /billing/subscription/update
- ✅ POST /billing/subscription/cancel
- ✅ GET /billing/invoices
- ✅ GET /billing/seats
- ✅ POST /billing/seats/assign
- ✅ POST /billing/seats/{seat_id}/deactivate
- ✅ GET /billing/usage
- ✅ POST /billing/webhooks/paddle

### 7. **Onboarding** (`app/onboarding_service.py`)
- ✅ Onboarding checklist
- ✅ Contextual tips
- ✅ Simplified mode for new users
- ✅ Progress tracking

---

## ❌ WHAT'S MISSING

### 1. **Organization/Company Management**
- ❌ No `organizations` table - only `company_id` string field
- ❌ No company/organization model
- ❌ No company settings (name, domain, branding, etc.)
- ❌ No company-level subscription management
- ❌ No company creation flow during signup

### 2. **Team Management**
- ❌ No team invitation system
- ❌ No pending invitations tracking
- ❌ No email verification
- ❌ No invite tokens/links
- ❌ No team member management UI backend

### 3. **Data Isolation**
- ❌ No company_id filtering in most database queries!
  - Customers table has no company_id
  - Products table has no company_id
  - Quotes table has no company_id
  - Documents table has no company_id
  - Competitors table has no company_id
- ❌ **CRITICAL SECURITY ISSUE**: All data shared across companies!

### 4. **Session Management**
- ❌ Token store is in-memory (lost on restart)
- ❌ No persistent session storage
- ❌ No "Remember Me" functionality
- ❌ No device/session management
- ❌ No ability to view/revoke active sessions

### 5. **Password Management**
- ❌ No password reset flow
- ❌ No forgot password
- ❌ No password strength requirements
- ❌ No password change endpoint
- ❌ No account recovery

### 6. **Advanced Security**
- ❌ No 2FA/MFA support
- ❌ No SSO integration
- ❌ No audit logs
- ❌ No login attempt tracking
- ❌ No account lockout after failed attempts
- ❌ No IP whitelist/blacklist

### 7. **User Management**
- ❌ No user profile updates
- ❌ No user deactivation/deletion
- ❌ No user role changes
- ❌ No user activity tracking
- ❌ No last seen/online status

### 8. **Registration Flow**
- ❌ No public signup endpoint
- ❌ No email verification
- ❌ No terms of service acceptance tracking
- ❌ No company registration (only user creation)

### 9. **Billing Integration Gaps**
- ❌ Subscription not tied to company_id
- ❌ Seat assignments not creating user accounts
- ❌ No automatic seat/user sync
- ❌ No seat limit enforcement

### 10. **API Token Management**
- ❌ No API keys for programmatic access
- ❌ No refresh tokens
- ❌ No token revocation list

---

## 🚨 CRITICAL ISSUES (FIX IMMEDIATELY)

### Issue #1: Data Leakage Between Companies
**Problem**: All tables except `users` lack `company_id` filtering
**Impact**: Company A can see Company B's customers, products, quotes, etc.
**Fix**: Add `company_id` to all tables and filter ALL queries

### Issue #2: Session Loss on Restart
**Problem**: Token store is in-memory
**Impact**: All users logged out when server restarts
**Fix**: Store tokens in SQLite database

### Issue #3: No Organization Model
**Problem**: Using string company_id without actual company/org table
**Impact**: Can't store company settings, subscription, or metadata
**Fix**: Create organizations table and link users to it

---

## 📋 IMPLEMENTATION PRIORITY

### **Phase 1: Critical Security (DO NOW)**
1. Create `organizations` table
2. Add `organization_id` to all data tables
3. Implement data isolation middleware
4. Move token storage to database
5. Add company-level RLS (Row Level Security)

### **Phase 2: Core Multi-Tenancy (WEEK 1)**
1. Company signup flow
2. Company settings management
3. Team invitation system
4. User role management within org
5. Subscription linked to organization

### **Phase 3: User Experience (WEEK 2)**
1. Password reset flow
2. Email verification
3. Remember me functionality
4. Session management page
5. Profile management

### **Phase 4: Enterprise Features (WEEK 3-4)**
1. SSO integration (OAuth, SAML)
2. 2FA/MFA
3. Audit logs
4. Advanced permissions
5. API token management

---

## 🎯 RECOMMENDED IMMEDIATE ACTIONS

1. **Create organization infrastructure**
   - Organizations table
   - Organization service
   - Organization API routes

2. **Fix data isolation**
   - Add organization_id to all tables
   - Create middleware to inject organization context
   - Modify all queries to filter by organization_id

3. **Persistent sessions**
   - Create sessions table in SQLite
   - Migrate in-memory tokens to database
   - Add session management endpoints

4. **Team management**
   - Invitation table
   - Invite flow (generate token, send email)
   - Accept invitation endpoint
   - Team member list/management

5. **Password recovery**
   - Password reset tokens table
   - Forgot password endpoint
   - Reset password endpoint
   - Email templates

---

## 📊 COMPLETENESS SCORE

| Category | Score | Status |
|----------|-------|--------|
| **Authentication** | 75% | ⚠️ Missing password reset, 2FA |
| **Authorization** | 60% | ⚠️ Has roles, missing fine-grained permissions |
| **Multi-Tenancy** | 30% | 🚨 CRITICAL: No data isolation |
| **Session Management** | 40% | 🚨 In-memory only, no persistence |
| **User Management** | 50% | ⚠️ Basic CRUD, missing profile/settings |
| **Team Management** | 10% | 🚨 No invitations, no team features |
| **Security** | 40% | 🚨 No 2FA, SSO, audit logs |
| **Billing Integration** | 70% | ✅ Good foundation, needs org linkage |

**OVERALL: 47%** - Needs substantial work for production B2B SaaS

---

## 🏗️ ARCHITECTURE GAPS

### Current Architecture:
```
User → company_id (string) → No actual company object
```

### Required Architecture:
```
Organization
  ├── Subscription
  ├── BillingAddress
  ├── Users (team members)
  │   ├── User (admin)
  │   ├── User (manager)
  │   └── User (sales_rep)
  ├── Customers (isolated per org)
  ├── Products (isolated per org)
  ├── Quotes (isolated per org)
  └── Documents (isolated per org)
```

---

## 📝 NEXT STEPS

Run the implementation script to add:
1. Organizations table and service
2. Data isolation middleware
3. Session persistence
4. Team invitation system
5. Password reset flow
6. Company signup flow
