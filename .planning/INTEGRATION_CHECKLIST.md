# Integration Checklist - Making System Multi-Tenant Aware

## 🎯 Goal
Update all database queries and API routes to use the new organization-based multi-tenancy system.

---

## ✅ Phase 1: Database Layer (Priority: CRITICAL)

### Update `app/database_sqlite.py`

#### Customers Functions
- [ ] `create_customer()` - Add `organization_id` and `user_id` parameters
- [ ] `get_customer_by_id()` - Add `organization_id` filter in WHERE clause
- [ ] `get_customer_by_email()` - Add `organization_id` filter in WHERE clause
- [ ] `list_customers()` - Add `organization_id` filter parameter and WHERE clause
- [ ] `update_customer()` - Verify organization_id before updating

#### Products Functions
- [ ] `create_product()` - Add `organization_id` and `user_id` parameters
- [ ] `get_product_by_sku()` - Add `organization_id` filter in WHERE clause
- [ ] `list_products()` - Add `organization_id` filter parameter and WHERE clause

#### Quotes Functions
- [ ] `create_quote()` - Add `organization_id` and `user_id` parameters
- [ ] `get_quote_with_items()` - Add `organization_id` filter in WHERE clause
- [ ] `list_quotes()` - Add `organization_id` filter parameter and WHERE clause
- [ ] `add_quote_item()` - Verify quote belongs to organization

#### Documents Functions
- [ ] `save_document()` - Add `organization_id` parameter
- [ ] `list_documents()` - Add `organization_id` filter parameter and WHERE clause

#### Competitors Functions
- [ ] `save_competitor()` - Add `organization_id` parameter
- [ ] `get_competitor_by_url()` - Add `organization_id` filter
- [ ] `list_competitors()` - Add `organization_id` filter parameter

#### Extractions Functions
- [ ] `save_extraction()` - Add `organization_id` parameter
- [ ] `list_extractions()` - Add `organization_id` filter parameter

---

## ✅ Phase 2: Middleware (Priority: HIGH)

### Create `app/middleware/organization.py`

```python
"""
Organization context middleware.
Auto-injects organization_id from session.
"""

from fastapi import Header, HTTPException
from typing import Optional
from app.auth_enhanced import SessionService

async def get_current_organization(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Dependency to get current organization ID from session.
    Use in all authenticated routes.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    org_id = session.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization context")
    
    return org_id


async def get_current_user_and_org(
    authorization: Optional[str] = Header(None)
) -> tuple[str, str]:
    """
    Get both user_id and organization_id from session.
    Returns: (user_id, organization_id)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return session["user_id"], session["organization_id"]
```

**Tasks:**
- [ ] Create `app/middleware/organization.py`
- [ ] Add `get_current_organization()` dependency
- [ ] Add `get_current_user_and_org()` dependency

---

## ✅ Phase 3: Update API Routes (Priority: HIGH)

### `app/routes/customers_new.py`

```python
# Before (insecure):
@router.get("/customers")
async def list_customers():
    customers = list_customers()  # Shows ALL customers!
    return customers

# After (secure):
from app.middleware.organization import get_current_user_and_org

@router.get("/customers")
async def list_customers(
    user_org: tuple = Depends(get_current_user_and_org)
):
    user_id, org_id = user_org
    customers = list_customers(organization_id=org_id)
    return customers
```

**Tasks:**
- [ ] Import middleware dependencies
- [ ] Add `Depends(get_current_organization)` to all routes
- [ ] Pass `organization_id` to database functions
- [ ] Pass `user_id` where needed (for attribution)

**Routes to Update:**
- [ ] `GET /customers` - List only org's customers
- [ ] `POST /customers` - Add with org_id + user_id
- [ ] `GET /customers/{id}` - Verify belongs to org
- [ ] `PUT /customers/{id}` - Verify belongs to org
- [ ] `DELETE /customers/{id}` - Verify belongs to org

### `app/routes/products_new.py`

**Routes to Update:**
- [ ] `GET /products` - List only org's products
- [ ] `POST /products` - Add with org_id + user_id
- [ ] `GET /products/{id}` - Verify belongs to org
- [ ] `PUT /products/{id}` - Verify belongs to org
- [ ] `DELETE /products/{id}` - Verify belongs to org
- [ ] `POST /products/bulk` - Add all with org_id

### `app/routes/quotes_new.py`

**Routes to Update:**
- [ ] `GET /quotes` - List only org's quotes
- [ ] `POST /quotes` - Create with org_id + user_id
- [ ] `GET /quotes/{id}` - Verify belongs to org
- [ ] `PUT /quotes/{id}` - Verify belongs to org
- [ ] `DELETE /quotes/{id}` - Verify belongs to org
- [ ] `POST /quotes/{id}/items` - Verify quote belongs to org

### `app/routes/competitors.py`

**Routes to Update:**
- [ ] `GET /competitors` - List only org's competitors
- [ ] `POST /competitors` - Add with org_id
- [ ] `GET /competitors/{id}` - Verify belongs to org

### `app/routes/knowledge_base.py`

**Routes to Update:**
- [ ] `GET /knowledge-base/documents` - List only org's docs
- [ ] `POST /knowledge-base/upload` - Add with org_id
- [ ] `GET /knowledge-base/search` - Search only org's docs

### `app/routes/rag.py`

**Tasks:**
- [ ] Update RAG service to filter by organization
- [ ] Ensure embeddings are scoped to organization
- [ ] Update ChromaDB collection naming (per org?)

---

## ✅ Phase 4: Update Auth Routes (Priority: MEDIUM)

### Update `app/routes/auth.py` to use Enhanced Auth

**Replace in-memory sessions with persistent sessions:**

```python
# Old (in-memory):
from app.auth import create_access_token

@router.post("/login")
async def login(request: LoginRequest):
    user = authenticate_user(request.email, request.password)
    token = create_access_token(user.id)  # Lost on restart
    return {"access_token": token}

# New (persistent):
from app.auth_enhanced import EnhancedAuthService

@router.post("/login")
async def login(request: LoginRequest):
    result = EnhancedAuthService.login_user(
        email=request.email,
        password=request.password,
        remember_me=request.remember_me,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host
    )
    if not result:
        raise HTTPException(401, "Invalid credentials")
    return result  # Contains access_token + org info
```

**Tasks:**
- [ ] Replace `create_access_token` with `SessionService.create_session`
- [ ] Use `SessionService.validate_session` instead of `get_current_user`
- [ ] Add "remember me" option to login
- [ ] Update logout to use `SessionService.revoke_session`

---

## ✅ Phase 5: Subscription Integration (Priority: MEDIUM)

### Link Subscriptions to Organizations

**In `app/routes/billing.py`:**

```python
@router.post("/billing/checkout/create-session")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    user_id, org_id = user_org
    
    # Get organization
    org = OrganizationService.get_organization(org_id)
    if not org:
        raise HTTPException(404, "Organization not found")
    
    # Create checkout with org metadata
    session = await paddle_service.create_checkout_session(
        plan_id=request.plan_id,
        seats=request.seats,
        metadata={
            "organization_id": org_id,
            "user_id": user_id
        }
    )
    
    return session
```

**Tasks:**
- [ ] Update checkout to use organization context
- [ ] Link webhook events to organizations
- [ ] Update subscription records with org_id
- [ ] Enforce seat limits when inviting users

**Subscription Functions to Update:**
- [ ] `create_checkout_session()` - Add org_id to metadata
- [ ] `get_current_subscription()` - Get from org, not user
- [ ] `update_subscription()` - Verify org ownership
- [ ] `process_webhook()` - Update org's subscription

---

## ✅ Phase 6: Frontend Integration (Priority: LOW - but important)

### Create New Pages

**Signup Page (`/signup`)**
- [ ] Form with company + user info
- [ ] POST to `/organizations/create`
- [ ] Store returned access_token
- [ ] Redirect to dashboard

**Team Management Page (`/settings/team`)**
- [ ] List current team members
- [ ] Invite button → modal
- [ ] Show pending invitations
- [ ] Remove member functionality
- [ ] Change role functionality

**Invitation Accept Page (`/invite/accept?token=...`)**
- [ ] GET `/organizations/invitations/{token}` to show org name
- [ ] Form for name + password
- [ ] POST `/organizations/invitations/accept`
- [ ] Store access_token
- [ ] Redirect to dashboard

**Password Reset Pages**
- [ ] `/forgot-password` - Request reset
- [ ] `/reset-password?token=...` - Reset with token

**Session Management Page (`/settings/sessions`)**
- [ ] List all active sessions
- [ ] Show device info, last used
- [ ] "Revoke" button per session
- [ ] "Revoke all other sessions" button

### Update Existing Pages

**Dashboard**
- [ ] Show organization name
- [ ] Show user role
- [ ] Show seat usage (X/Y seats used)

**Navigation**
- [ ] Add link to Team Settings
- [ ] Add link to Account Settings
- [ ] Show organization switcher (if user in multiple orgs)

---

## ✅ Phase 7: Email Service (Priority: LOW)

### Setup Email Provider

**Options:**
- SendGrid (free tier: 100 emails/day)
- Mailgun (free tier: 5,000 emails/month)
- Resend (free tier: 3,000 emails/month)

### Create `app/services/email_service.py`

```python
"""
Email service for sending invitations and password resets.
"""

class EmailService:
    def send_invitation(self, to_email: str, org_name: str, invite_token: str):
        """Send team invitation email."""
        invite_link = f"{BASE_URL}/invite/accept?token={invite_token}"
        
        html = f"""
        <h1>You've been invited to join {org_name}!</h1>
        <p>Click the link below to accept:</p>
        <a href="{invite_link}">{invite_link}</a>
        """
        
        # Send via provider
        self._send(to_email, f"Invitation to join {org_name}", html)
    
    def send_password_reset(self, to_email: str, reset_token: str):
        """Send password reset email."""
        reset_link = f"{BASE_URL}/reset-password?token={reset_token}"
        
        html = f"""
        <h1>Reset your password</h1>
        <p>Click the link below to reset (expires in 1 hour):</p>
        <a href="{reset_link}">{reset_link}</a>
        """
        
        self._send(to_email, "Password reset request", html)
```

**Tasks:**
- [ ] Choose email provider
- [ ] Create email service class
- [ ] Create HTML email templates
- [ ] Integrate with invite flow
- [ ] Integrate with password reset flow
- [ ] Add email sending to organization routes

---

## ✅ Phase 8: Testing (Priority: HIGH)

### Unit Tests

- [ ] Test organization creation
- [ ] Test invitation flow
- [ ] Test password reset
- [ ] Test session persistence
- [ ] Test data isolation (org A can't see org B's data)

### Integration Tests

- [ ] Create two organizations
- [ ] Add data to each
- [ ] Verify data isolation
- [ ] Invite user to org
- [ ] Accept invitation
- [ ] Verify user can access org data
- [ ] Verify user cannot access other org's data

### Security Tests

- [ ] Try to access another org's customers
- [ ] Try to invite user without permission
- [ ] Try to remove organization owner
- [ ] Try to use expired invitation
- [ ] Try to use expired password reset token

---

## 🎯 Progress Tracker

### Overall Progress

```
Phase 1: Database Layer       [ ] 0/20
Phase 2: Middleware           [ ] 0/3
Phase 3: API Routes           [ ] 0/25
Phase 4: Auth Routes          [ ] 0/5
Phase 5: Subscription         [ ] 0/6
Phase 6: Frontend             [ ] 0/10
Phase 7: Email Service        [ ] 0/5
Phase 8: Testing              [ ] 0/10
───────────────────────────────────────
TOTAL:                        [ ] 0/84 (0%)
```

### Critical Path (Do First)

1. ✅ Database migration (DONE)
2. [ ] Create middleware (3 tasks)
3. [ ] Update customers routes (5 tasks)
4. [ ] Update products routes (6 tasks)
5. [ ] Update quotes routes (6 tasks)
6. [ ] Test data isolation (2 tasks)

---

## 📝 Code Example Templates

### Template 1: Update Database Function

```python
# Before:
def list_customers(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM customers ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]

# After:
def list_customers(
    organization_id: str,  # NEW: Required parameter
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM customers 
            WHERE organization_id = ?  -- NEW: Filter by org
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (organization_id, limit, offset))  # NEW: Pass org_id
        return [dict(row) for row in cursor.fetchall()]
```

### Template 2: Update API Route

```python
# Before:
@router.get("/customers")
async def list_customers():
    customers = database.list_customers()
    return {"customers": customers}

# After:
from app.middleware.organization import get_current_user_and_org
from fastapi import Depends

@router.get("/customers")
async def list_customers(
    user_org: tuple = Depends(get_current_user_and_org)  # NEW
):
    user_id, org_id = user_org  # NEW
    customers = database.list_customers(organization_id=org_id)  # NEW
    return {"customers": customers}
```

### Template 3: Create with Attribution

```python
@router.post("/customers")
async def create_customer(
    customer: CustomerCreate,
    user_org: tuple = Depends(get_current_user_and_org)
):
    user_id, org_id = user_org
    
    customer_data = {
        **customer.dict(),
        "organization_id": org_id,  # Data isolation
        "user_id": user_id,         # Attribution
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    result = database.create_customer(customer_data)
    return result
```

---

## 🚨 Common Pitfalls to Avoid

1. **Forgetting organization_id filter**
   ```python
   # ❌ BAD: Shows all organizations' data
   SELECT * FROM customers
   
   # ✅ GOOD: Shows only current org's data
   SELECT * FROM customers WHERE organization_id = ?
   ```

2. **Using old auth system**
   ```python
   # ❌ BAD: In-memory session
   from app.auth import create_access_token
   
   # ✅ GOOD: Persistent session
   from app.auth_enhanced import SessionService
   ```

3. **Not validating ownership**
   ```python
   # ❌ BAD: Anyone can delete any customer
   DELETE FROM customers WHERE id = ?
   
   # ✅ GOOD: Only delete if belongs to org
   DELETE FROM customers WHERE id = ? AND organization_id = ?
   ```

---

**Start here:** Phase 2 → Create middleware
**Then:** Phase 3 → Update customers routes
**Test:** Create 2 orgs, verify data isolation

**Questions?** See `docs/MULTI_TENANCY.md` for full API reference
