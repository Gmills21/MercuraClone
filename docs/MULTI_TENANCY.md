# 🏢 Multi-Tenancy & Team Management System

## Overview

This document describes the complete multi-tenancy, authentication, and team management system for OpenMercura.

---

## 🎯 Key Features

### ✅ What You Now Have

1. **Organization Management**
   - Multi-company support
   - Per-organization subscriptions
   - Company settings and branding
   - Trial and active status tracking

2. **Team Management**
   - Invite team members via email
   - Role-based access (Owner, Admin, Manager, Sales Rep, Viewer)
   - Seat management (subscription-based)
   - Member activity tracking

3. **Authentication & Security**
   - Persistent sessions (survives server restart)
   - "Remember me" functionality
   - Password reset flow
   - Session management (view/revoke sessions)
   - Password change with verification

4. **Data Isolation**
   - Every table has `organization_id`
   - Automatic filtering by organization
   - No data leakage between companies
   - User attribution with `user_id` fields

---

## 📐 Architecture

### Organization Hierarchy

```
Organization
  ├── Subscription (seats, billing)
  ├── Settings (branding, features)
  ├── Members (team)
  │   ├── Owner (full control)
  │   ├── Admin (manage team)
  │   ├── Manager (approve quotes)
  │   └── Sales Rep (create quotes)
  ├── Data (isolated per org)
  │   ├── Customers
  │   ├── Products
  │   ├── Quotes
  │   ├── Documents
  │   └── Competitors
  └── Invitations (pending)
```

### Database Tables

#### Core Tables
- `organizations` - Company/org records
- `organization_members` - User-org relationships
- `organization_invitations` - Pending invites
- `users` - User accounts

#### Session & Security
- `sessions` - Persistent auth tokens
- `password_reset_tokens` - Password reset flow

#### Data Tables (all have `organization_id`)
- `customers`
- `products`
- `quotes`
- `documents`
- `competitors`
- `extractions`

---

## 🚀 Getting Started

### 1. Run the Migration

**CRITICAL FIRST STEP**: Add `organization_id` to existing tables

```bash
python scripts/migrate_add_organization_id.py
```

This adds data isolation columns to all tables. **Required for security!**

### 2. API Endpoints

#### Organization Management

```http
# Create organization (signup)
POST /organizations/create
{
  "name": "Acme Corp",
  "slug": "acme",
  "owner_email": "john@acme.com",
  "owner_name": "John Doe",
  "owner_password": "SecurePass123!"
}

# Get current organization
GET /organizations/me
Authorization: Bearer {token}

# Update organization
PATCH /organizations/{org_id}
{
  "name": "Acme Corporation",
  "settings": {...}
}
```

#### Team Invitations

```http
# Invite team member
POST /organizations/{org_id}/invite
{
  "email": "jane@acme.com",
  "role": "sales_rep",
  "send_email": true
}

# Get invitation details (public)
GET /organizations/invitations/{token}

# Accept invitation (public)
POST /organizations/invitations/accept
{
  "token": "...",
  "user_name": "Jane Smith",
  "password": "SecurePass123!"
}

# List team members
GET /organizations/{org_id}/members

# Remove member
DELETE /organizations/{org_id}/members/{user_id}

# Update member role
PATCH /organizations/{org_id}/members/{user_id}/role
```

#### Password Management

```http
# Forgot password
POST /organizations/auth/forgot-password
{
  "email": "user@example.com"
}

# Reset password (from email link)
POST /organizations/auth/reset-password
{
  "token": "...",
  "new_password": "NewSecurePass123!"
}

# Change password (authenticated)
POST /organizations/auth/change-password
Authorization: Bearer {token}
{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

#### Session Management

```http
# List all sessions
GET /organizations/auth/sessions
Authorization: Bearer {token}

# Revoke all sessions (except current)
POST /organizations/auth/sessions/revoke-all
{
  "keep_current": true
}
```

---

## 🔒 Security Features

### Data Isolation

Every query **MUST** filter by `organization_id`:

```python
# ❌ WRONG - data leakage!
cursor.execute("SELECT * FROM customers")

# ✅ CORRECT - organization isolated
cursor.execute("""
    SELECT * FROM customers 
    WHERE organization_id = ?
""", (org_id,))
```

### Session Security

- Tokens stored in database (persistent)
- Automatic expiration (24h default, 30d with "remember me")
- User agent and IP tracking
- Revoke all sessions on password change

### Password Security

- PBKDF2 hashing with salt (100,000 iterations)
- Reset tokens expire in 1 hour
- One-time use reset tokens
- All sessions revoked on password change

---

## 👥 User Roles

### Permission Hierarchy

```
Viewer < Sales Rep < Manager < Admin < Owner
  ↓        ↓          ↓         ↓        ↓
 View     Create    Approve   Manage   Full
         Quotes     Quotes     Team   Control
```

### Role Capabilities

| Feature | Viewer | Sales Rep | Manager | Admin | Owner |
|---------|--------|-----------|---------|-------|-------|
| View quotes | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create quotes | ❌ | ✅ | ✅ | ✅ | ✅ |
| Approve quotes | ❌ | ❌ | ✅ | ✅ | ✅ |
| Manage team | ❌ | ❌ | ❌ | ✅ | ✅ |
| Billing | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete org | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 📝 Example Flows

### Signup Flow

1. User fills signup form
2. POST `/organizations/create` with org details
3. System creates:
   - Organization record
   - User account (owner role)
   - Organization membership
   - Session token
4. Returns `access_token` for immediate login

### Invite Flow

1. Admin invites user via email
2. POST `/organizations/{org_id}/invite`
3. System:
   - Creates invitation record
   - Generates secure token
   - (TODO: Sends email with link)
4. User clicks link, lands on accept page
5. GET `/organizations/invitations/{token}` to show org name
6. User enters name/password
7. POST `/organizations/invitations/accept`
8. System:
   - Creates user account
   - Adds to organization
   - Marks invitation accepted
   - Returns access token

### Password Reset Flow

1. User clicks "Forgot Password"
2. POST `/organizations/auth/forgot-password`
3. System creates reset token (TODO: sends email)
4. User clicks link with token
5. POST `/organizations/auth/reset-password`
6. Password updated, all sessions revoked
7. User logs in with new password

---

## 🛠️ Implementation Checklist

### Phase 1: Database & Core (✅ DONE)
- [x] Organization models
- [x] Session persistence
- [x] Password reset
- [x] Database migration
- [x] API routes
- [x] Data isolation columns

### Phase 2: Integration (🚧 TODO)
- [ ] Update all queries to filter by `organization_id`
- [ ] Add middleware to inject organization context
- [ ] Link subscriptions to organizations
- [ ] Enforce seat limits
- [ ] Update frontend to use new APIs

### Phase 3: Email & UX (🚧 TODO)
- [ ] Email service integration
- [ ] Invitation email templates
- [ ] Password reset email templates
- [ ] Frontend signup flow
- [ ] Frontend team management page
- [ ] Frontend session management page

### Phase 4: Advanced (📅 LATER)
- [ ] SSO integration (OAuth, SAML)
- [ ] 2FA/MFA
- [ ] Audit logs
- [ ] API tokens
- [ ] Custom permissions

---

## ⚠️ Breaking Changes

### Migration Required

All existing data will have `organization_id = 'default'`. You must:

1. Run migration script
2. Update all database queries
3. Update API calls to handle organization context

### API Changes

**OLD (insecure):**
```python
# Anyone can see any customer
GET /customers
```

**NEW (secure):**
```python
# Only see customers in your organization
GET /customers
Authorization: Bearer {token}
# Token contains organization_id
```

---

## 📊 Testing

### Test Organization Creation

```bash
curl -X POST http://localhost:8000/organizations/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Corp",
    "slug": "testcorp",
    "owner_email": "test@test.com",
    "owner_name": "Test User",
    "owner_password": "Test123!"
  }'
```

### Test Invitation

```bash
# Create invitation
curl -X POST http://localhost:8000/organizations/{org_id}/invite \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "role": "sales_rep"
  }'

# Check invitation
curl http://localhost:8000/organizations/invitations/{token}
```

---

## 🐛 Troubleshooting

### "No organization found" error

- User may not be a member of any organization
- Check `organization_members` table
- Verify `company_id` in users table matches org `id`

### Data not showing up

- Likely filtering by wrong `organization_id`
- Check session organization context
- Verify data has correct `organization_id`

### Sessions not persisting

- Check `sessions` table exists
- Verify database migration ran
- Check token is being sent in `Authorization` header

---

## 📚 Related Files

```
app/
├── models_organization.py       # Organization models
├── organization_service.py      # Organization business logic
├── auth_enhanced.py             # Sessions, password reset
├── routes/
│   └── organizations.py         # Organization API routes
└── database_sqlite.py           # Updated with new tables

scripts/
└── migrate_add_organization_id.py  # Critical migration

.planning/
└── auth_and_multi_tenancy_audit.md  # Full audit report
```

---

## 🎓 Best Practices

1. **Always filter by organization**
   ```python
   WHERE organization_id = ?
   ```

2. **Use middleware for organization context**
   ```python
   @router.get("/customers")
   async def list_customers(org_id: str = Depends(get_current_org)):
       # org_id automatically injected
   ```

3. **Check seat limits before inviting**
   ```python
   if org.seats_used >= org.seats_total:
       raise HTTPException(400, "No seats available")
   ```

4. **Revoke sessions on security events**
   ```python
   # On password change
   SessionService.revoke_all_sessions(user_id)
   ```

5. **Validate organization ownership**
   ```python
   # Before sensitive operations
   if current_user.id != org.owner_user_id:
       raise HTTPException(403, "Only owner can do this")
   ```

---

## 📞 Support

For issues or questions about the multi-tenancy system:

1. Check `.planning/auth_and_multi_tenancy_audit.md` for detailed architecture
2. Review this README for implementation details
3. Check database schema in `database_sqlite.py`
4. Test with provided curl examples

---

**Status:** ✅ Core infrastructure complete, ready for integration and frontend implementation
