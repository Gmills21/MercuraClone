# Multi-Tenancy Architecture - Quick Reference

## 🏗️ Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        USER REQUEST                          │
│            (with Authorization: Bearer token)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    SESSION VALIDATION                        │
│  sessions table: token → user_id + organization_id          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ORGANIZATION CONTEXT                        │
│     Get organization_id from validated session              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE QUERY                            │
│  SELECT * FROM customers WHERE organization_id = ?          │
│                     ↑↑↑ CRITICAL ↑↑↑                        │
│         (prevents data leakage between companies)           │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 User Journey Flows

### Signup Flow (Company Creation)

```
1. Landing Page
   ↓
2. Signup Form
   • Company Name
   • Company Slug (subdomain)
   • Your Name
   • Email
   • Password
   ↓
3. POST /organizations/create
   ↓
4. Backend Creates:
   ├─ Organization record
   ├─ User account (owner role)
   ├─ Organization membership
   └─ Session token
   ↓
5. Returns access_token
   ↓
6. Dashboard (logged in)
```

### Invite Team Member Flow

```
1. Team Page
   ↓
2. Click "Invite Member"
   ↓
3. Enter email + role
   ↓
4. POST /organizations/{org_id}/invite
   ↓
5. Backend Creates:
   ├─ Invitation record
   ├─ Secure token
   └─ (TODO) Sends email
   ↓
6. User clicks invite link
   ↓
7. Accept Page
   • Shows: "Join Acme Corp"
   • Enter: Name + Password
   ↓
8. POST /organizations/invitations/accept
   ↓
9. Backend Creates:
   ├─ User account
   ├─ Organization membership
   └─ Session token
   ↓
10. Dashboard (logged in as team member)
```

### Password Reset Flow

```
1. Login Page
   ↓
2. Click "Forgot Password"
   ↓
3. Enter email
   ↓
4. POST /auth/forgot-password
   ↓
5. Backend Creates:
   ├─ Reset token (1hr expiry)
   └─ (TODO) Sends email
   ↓
6. User clicks reset link
   ↓
7. Reset Page
   • Enter new password
   ↓
8. POST /auth/reset-password
   ↓
9. Backend:
   ├─ Updates password
   ├─ Marks token as used
   └─ Revokes all sessions
   ↓
10. Login Page
    "Password reset! Please login"
```

## 📊 Database Schema

```
┌──────────────────┐         ┌──────────────────┐
│  organizations   │◄────┬───│      users       │
├──────────────────┤     │   ├──────────────────┤
│ id (PK)          │     │   │ id (PK)          │
│ name             │     │   │ email (UNIQUE)   │
│ slug (UNIQUE)    │     │   │ name             │
│ owner_user_id  ──┼─────┘   │ password_hash    │
│ subscription_id  │         │ role             │
│ status           │         │ company_id (FK)  │
│ seats_total      │         │ created_at       │
│ seats_used       │         │ is_active        │
└──────────────────┘         └──────────────────┘
         ▲                            │
         │                            │
         │    ┌───────────────────────┘
         │    │
         │    ▼
┌──────────────────────────────┐
│   organization_members       │
├──────────────────────────────┤
│ id (PK)                      │
│ organization_id (FK) ────────┤
│ user_id (FK)                 │
│ role (owner/admin/etc)       │
│ is_active                    │
│ joined_at                    │
└──────────────────────────────┘
         ▲
         │
┌──────────────────────────────┐       ┌──────────────────┐
│ organization_invitations     │       │    sessions      │
├──────────────────────────────┤       ├──────────────────┤
│ id (PK)                      │       │ id (PK)          │
│ organization_id (FK) ────────┤       │ user_id (FK)     │
│ email                        │       │ token (UNIQUE)   │
│ role                         │       │ organization_id  │
│ token (UNIQUE)               │       │ created_at       │
│ status (pending/accepted)    │       │ expires_at       │
│ expires_at                   │       │ is_active        │
└──────────────────────────────┘       └──────────────────┘

┌──────────────────┐         ┌──────────────────┐
│    customers     │         │     products     │
├──────────────────┤         ├──────────────────┤
│ id (PK)          │         │ id (PK)          │
│ organization_id  │◄───┐    │ organization_id  │◄───┐
│ user_id          │    │    │ user_id          │    │
│ name             │    │    │ sku              │    │
│ email            │    │    │ name             │    │
└──────────────────┘    │    └──────────────────┘    │
                        │                             │
                   ┌────┴─────────────┐               │
                   │  DATA ISOLATION  │───────────────┘
                   │  (prevents data  │
                   │   leakage)       │
                   └──────────────────┘
```

## 🔑 Key Security Concepts

### 1. Organization Isolation

**Before (Insecure):**
```sql
-- Anyone can see anyone's customers!
SELECT * FROM customers
```

**After (Secure):**
```sql
-- Only see YOUR organization's customers
SELECT * FROM customers 
WHERE organization_id = 'org-123'
```

### 2. Session Management

**Before (Lost on restart):**
```python
# In-memory dictionary
_active_tokens = {
    "abc123": {"user_id": "user-1"}
}
# ❌ Lost when server restarts
```

**After (Persistent):**
```sql
-- Stored in database
INSERT INTO sessions (token, user_id, organization_id, ...)
-- ✅ Survives server restarts
```

### 3. Team Membership

**Before (No teams):**
```
User(id, email, company_id="default")
# Everyone in same "default" company
```

**After (Real teams):**
```
Organization(id, name, owner_user_id)
  ├─ OrganizationMember(user_id, org_id, role="owner")
  ├─ OrganizationMember(user_id, org_id, role="admin")
  └─ OrganizationMember(user_id, org_id, role="sales_rep")
```

## 🚦 Role Hierarchy

```
┌─────────────────────────────────────────┐
│                  OWNER                  │ ← Full control
│  • All admin powers                     │
│  • Delete organization                  │
│  • Transfer ownership                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│                  ADMIN                  │ ← Team management
│  • All manager powers                   │
│  • Manage team (invite/remove)          │
│  • Billing & subscription               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│                 MANAGER                 │ ← Quote approval
│  • All sales_rep powers                 │
│  • Approve quotes                       │
│  • View all team data                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│               SALES_REP                 │ ← Daily work
│  • Create quotes                        │
│  • Manage own customers                 │
│  • View own data                        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│                 VIEWER                  │ ← Read-only
│  • View quotes                          │
│  • View customers                       │
│  • No create/edit                       │
└─────────────────────────────────────────┘
```

## 📝 API Quick Reference

```
ORGANIZATION MANAGEMENT
=======================
POST   /organizations/create              Create org + owner
GET    /organizations/me                  Current organization
GET    /organizations/{id}                Get org details
PATCH  /organizations/{id}                Update org

TEAM MANAGEMENT
===============
GET    /organizations/{id}/members        List team
POST   /organizations/{id}/invite         Invite member
DELETE /organizations/{id}/members/{uid}  Remove member
PATCH  /organizations/{id}/members/{uid}/role  Change role

INVITATIONS
===========
GET    /organizations/invitations/{token}  View invitation
POST   /organizations/invitations/accept   Accept + create account

PASSWORD MANAGEMENT
===================
POST   /organizations/auth/forgot-password     Request reset
POST   /organizations/auth/reset-password      Reset with token
POST   /organizations/auth/change-password     Change (authenticated)

SESSION MANAGEMENT
==================
GET    /organizations/auth/sessions            List all sessions
POST   /organizations/auth/sessions/revoke-all Logout everywhere
```

## ⚡ Implementation Priority

```
PHASE 1: Core (✅ DONE)
├─ Organizations table
├─ Team invitations
├─ Session persistence
├─ Password reset
└─ Database migration

PHASE 2: Integration (🚧 NEXT)
├─ Update all queries (organization_id filter)
├─ Add middleware (auto org context)
├─ Link subscriptions to orgs
└─ Enforce seat limits

PHASE 3: Frontend (📅 UPCOMING)
├─ Signup page
├─ Team management UI
├─ Invitation accept page
└─ Password reset UI

PHASE 4: Email (📅 UPCOMING)
├─ Email service setup
├─ Invitation emails
├─ Password reset emails
└─ Welcome emails

PHASE 5: Advanced (📅 LATER)
├─ SSO integration
├─ 2FA/MFA
├─ Audit logs
└─ API tokens
```

---

**Quick Start:**
1. Read `.planning/MULTI_TENANCY_SUMMARY.md`
2. Review `docs/MULTI_TENANCY.md`
3. Update queries to filter by `organization_id`
4. Build frontend flows

**Critical Reminder:**
Every data query MUST filter by `organization_id`:
```python
WHERE organization_id = ?
```
This prevents Company A from seeing Company B's data!
