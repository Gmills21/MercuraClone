"""
Billing and Subscription API Routes - Production Ready
Handles subscription management, checkout, and Paddle webhooks with database persistence.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import Optional, List
import logging
from datetime import datetime, timedelta
import json

from app.config import settings
from app.services.billing_service import billing_service
from app.services.paddle_service import paddle_service
from app.middleware.organization import get_current_user_and_org
from app.database_sqlite import (
    get_subscription, create_subscription, update_subscription,
    list_invoices, get_invoice, list_seat_assignments,
    create_seat_assignment, deactivate_seat, save_cancellation_feedback,
)
from app.models_billing import (
    SubscriptionPlan, Subscription, Invoice,
    BillingInterval, CheckoutSessionRequest, UpdateSubscriptionRequest,
    CancelSubscriptionRequest, BillingPortalRequest, AssignSeatRequest,
    CheckoutSessionResponse, BillingPortalResponse,
)
from app.errors import internal_error
from app.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# ==================== SUBSCRIPTION PLANS ====================

@router.get("/plans", response_model=List[SubscriptionPlan])
async def list_subscription_plans():
    """List all available subscription plans."""
    plans = [
        SubscriptionPlan(
            id="plan_basic",
            name="Basic",
            description="Perfect for small teams",
            price_per_seat=150.00,
            billing_interval=BillingInterval.MONTHLY,
            paddle_plan_id=settings.paddle_plan_basic or "",
            features=[
                "Unlimited quotes",
                "Email integration",
                "Basic analytics",
                "Standard support",
                "Up to 10 seats"
            ],
            max_seats=10
        ),
        SubscriptionPlan(
            id="plan_professional",
            name="Professional",
            description="For growing businesses",
            price_per_seat=250.00,
            billing_interval=BillingInterval.MONTHLY,
            paddle_plan_id=settings.paddle_plan_pro or "",
            features=[
                "Everything in Basic",
                "Advanced analytics",
                "QuickBooks integration",
                "Priority support",
                "Custom branding",
                "Up to 50 seats"
            ],
            max_seats=50
        ),
        SubscriptionPlan(
            id="plan_enterprise",
            name="Enterprise",
            description="For large organizations",
            price_per_seat=400.00,
            billing_interval=BillingInterval.MONTHLY,
            paddle_plan_id=settings.paddle_plan_enterprise or "",
            features=[
                "Everything in Professional",
                "Dedicated account manager",
                "Custom integrations",
                "SLA guarantee",
                "Advanced security",
                "Unlimited seats"
            ],
            max_seats=None
        )
    ]
    return plans


# ==================== CHECKOUT ====================

@router.post("/checkout/create-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    user_org: tuple = Depends(require_admin)
):
    """
    Create a Paddle checkout session for subscription.
    """
    user_id, org_id = user_org
    
    # Check if billing is configured
    if not paddle_service.enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Billing service unavailable",
                "message": "Subscription billing is not yet enabled. Please contact support to upgrade your account.",
                "code": "BILLING_NOT_CONFIGURED",
                "contact_email": "support@mercura.ai"
            }
        )
    
    try:
        # Get user's email from request or fallback
        user_email = request.customer_email or "user@example.com"
        user_name = request.customer_name or "User"
        
        # Map plan_id to Paddle plan ID
        plan_id_map = {
            "plan_basic": settings.paddle_plan_basic,
            "plan_professional": settings.paddle_plan_pro,
            "plan_enterprise": settings.paddle_plan_enterprise,
        }
        
        paddle_plan_id = plan_id_map.get(request.plan_id, settings.paddle_plan_pro)
        
        if not paddle_plan_id:
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "Plan configuration error",
                    "message": "The selected plan is not available. Please try another plan or contact support.",
                    "code": "PLAN_NOT_CONFIGURED"
                }
            )
        
        # Create checkout session
        session = await paddle_service.create_checkout_session(
            plan_id=paddle_plan_id,
            seats=request.seats,
            customer_email=user_email,
            customer_name=user_name,
            success_url=request.success_url or f"{settings.app_url}/account/billing?success=true",
            cancel_url=request.cancel_url or f"{settings.app_url}/account/billing?canceled=true",
            metadata={
                "organization_id": org_id,
                "user_id": user_id,
                "plan_id": request.plan_id,
                "seats": request.seats
            }
        )
        
        return {
            "checkout_url": session["checkout_url"],
            "session_id": session["session_id"]
        }
        
    except ValueError as e:
        # Paddle service not configured
        logger.error(f"Billing not configured: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Billing service unavailable",
                "message": "Subscription billing is temporarily unavailable. Please contact support.",
                "code": "BILLING_NOT_CONFIGURED"
            }
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Checkout error",
                "message": "Unable to create checkout session. Please try again or contact support.",
                "code": "CHECKOUT_ERROR"
            }
        )


# ==================== SUBSCRIPTIONS ====================

@router.get("/subscription")
async def get_current_subscription(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get current organization's subscription."""
    user_id, org_id = user_org
    
    subscription = get_subscription(org_id)
    
    if not subscription:
        # Return trial/default state
        return {
            "id": None,
            "organization_id": org_id,
            "plan_id": "trial",
            "plan_name": "Free Trial",
            "status": "trial",
            "seats_total": 1,
            "seats_used": 0,
            "price_per_seat": 0,
            "total_amount": 0,
            "billing_interval": "monthly",
            "trial_ends_at": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "is_trial": True
        }
    
    # Add seat count
    seats = list_seat_assignments(org_id, active_only=True)
    subscription["seats_used"] = len(seats)
    
    return subscription



@router.post("/subscription/update")
async def update_subscription_endpoint(
    request: UpdateSubscriptionRequest,
    user_org: tuple = Depends(require_admin)
):
    """Update subscription (seats only - plan changes require new checkout)."""
    user_id, org_id = user_org
    
    subscription = get_subscription(org_id)
    if not subscription or not subscription.get("paddle_subscription_id"):
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    try:
        # Validate seats
        if request.seats is None or request.seats < 1:
             raise HTTPException(status_code=400, detail="Invalid seat count")
        
        new_seats = request.seats
        
        # Update safely via service
        result = await billing_service.update_subscription_safely(org_id, new_seats)
        
        # Return updated subscription
        updated_sub = get_subscription(org_id)
        return {"success": True, "subscription": updated_sub}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to update subscription with billing provider: {str(e)}"
        )


@router.post("/subscription/cancel")
async def cancel_subscription(
    body: Optional[CancelSubscriptionRequest] = None,
    user_org: tuple = Depends(require_admin)
):
    """Cancel current subscription (self-service). Optional exit survey reason/feedback."""
    user_id, org_id = user_org
    
    subscription = get_subscription(org_id)
    if not subscription or not subscription.get("paddle_subscription_id"):
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    cancel_at_period_end = True
    reason = None
    feedback = None
    if body:
        cancel_at_period_end = body.cancel_at_period_end
        reason = body.reason
        feedback = body.feedback
    
    try:
        # Store exit survey before canceling (so we learn why they left)
        save_cancellation_feedback(
            organization_id=org_id,
            subscription_id=subscription["id"],
            reason=reason,
            feedback_text=feedback,
        )
        # Cancel safely via service
        result = await billing_service.cancel_subscription_safely(
            organization_id=org_id,
            cancel_at_period_end=cancel_at_period_end
        )
        
        return {
            "success": True,
            "message": "Subscription canceled" + (" at end of period" if cancel_at_period_end else " immediately")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to cancel subscription with billing provider: {str(e)}"
        )


# ==================== INVOICES ====================

@router.get("/invoices")
async def list_invoices_endpoint(
    user_org: tuple = Depends(require_admin),
    limit: int = 50
):
    """List all invoices for current organization."""
    user_id, org_id = user_org
    
    invoices = list_invoices(org_id, limit=limit)
    return {"invoices": invoices, "count": len(invoices)}


@router.get("/invoices/{invoice_id}")
async def get_invoice_endpoint(
    invoice_id: str,
    user_org: tuple = Depends(require_admin)
):
    """Get a specific invoice."""
    user_id, org_id = user_org
    
    invoice = get_invoice(invoice_id, org_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice


# ==================== BILLING PORTAL ====================

@router.post("/portal/create-session", response_model=BillingPortalResponse)
async def create_billing_portal_session(
    request: BillingPortalRequest,
    user_org: tuple = Depends(require_admin)
):
    """
    Create a billing portal session.
    Returns URL to our custom billing page since Paddle doesn't have hosted portal.
    """
    user_id, org_id = user_org
    
    subscription = get_subscription(org_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Return our billing page URL
    return_url = request.return_url or "/account/billing"
    return {"portal_url": return_url}


# ==================== SEAT MANAGEMENT ====================

@router.get("/seats")
async def list_seat_assignments_endpoint(
    user_org: tuple = Depends(require_admin)
):
    """List all seat assignments for current organization."""
    user_id, org_id = user_org
    
    seats = list_seat_assignments(org_id, active_only=True)
    return {"seats": seats, "count": len(seats)}


@router.post("/seats/assign")
async def assign_seat(
    request: AssignSeatRequest,
    user_org: tuple = Depends(require_admin)
):
    """Assign a seat to a team member."""
    user_id, org_id = user_org
    
    email = request.sales_rep_email
    name = request.sales_rep_name
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    result = billing_service.assign_seat(org_id, email, name)
    
    if not result:
        raise HTTPException(status_code=400, detail="Failed to assign seat - may be at seat limit")
    
    return {"success": True, "seat": result}


@router.post("/seats/{seat_id}/deactivate")
async def deactivate_seat_endpoint(
    seat_id: str,
    user_org: tuple = Depends(require_admin)
):
    """Deactivate a seat assignment."""
    user_id, org_id = user_org
    
    success = deactivate_seat(seat_id, org_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Seat not found")
    
    return {"success": True, "message": "Seat deactivated"}


# ==================== USAGE TRACKING ====================

@router.get("/usage")
async def get_usage_stats(
    user_org: tuple = Depends(require_admin)
):
    """Get usage statistics for current billing period."""
    user_id, org_id = user_org
    
    subscription = get_subscription(org_id)
    seats = list_seat_assignments(org_id, active_only=True)
    
    # In production, calculate actual usage from database
    return {
        "quotes_generated": 0,  # Would query from database
        "emails_processed": 0,  # Would query from database
        "seats_used": len(seats),
        "seats_total": subscription.get("seats_total", 1) if subscription else 1,
        "period_start": subscription.get("current_period_start") if subscription else datetime.utcnow().isoformat(),
        "period_end": subscription.get("current_period_end") if subscription else (datetime.utcnow() + timedelta(days=30)).isoformat()
    }


# ==================== WEBHOOKS ====================

@router.post("/webhooks/paddle")
async def paddle_webhook(request: Request):
    """
    Handle Paddle webhook events.
    This endpoint receives all webhook events from Paddle.
    """
    try:
        # Parse form data (Paddle sends form-encoded)
        form_data = await request.form()
        payload = dict(form_data)
        
        # Get signature
        signature = payload.get("p_signature", "")
        
        # Verify signature
        if not billing_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Log webhook for debugging
        logger.info(f"Received Paddle webhook: {payload.get('alert_name')}")
        
        # Process the webhook
        result = billing_service.process_webhook(payload)
        
        return {"success": True, "processed": result["type"]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Paddle webhook: {e}")
        # Return 200 to prevent Paddle from retrying (we logged the error)
        return {"success": False, "error": "Internal server error processing webhook"}


# ==================== BILLING STATUS ====================

@router.get("/status")
async def billing_status(user_org: tuple = Depends(get_current_user_and_org)):
    """
    Get billing status for the current organization.
    Returns subscription state, billing config, and portal availability.
    """
    user_id, org_id = user_org

    subscription = get_subscription(org_id)
    is_configured = bool(
        settings.paddle_vendor_id and settings.paddle_api_key and settings.paddle_plan_pro
    )

    if not subscription:
        return {
            "enabled": is_configured,
            "status": "trial",
            "plan_id": "trial",
            "plan_name": "Free Trial",
            "subscription": None,
            "sandbox": settings.paddle_sandbox,
        }

    return {
        "enabled": is_configured,
        "status": subscription.get("status", "active"),
        "plan_id": subscription.get("plan_id"),
        "plan_name": subscription.get("plan_name"),
        "subscription": {
            "id": subscription.get("id"),
            "organization_id": subscription.get("organization_id"),
            "seats_total": subscription.get("seats_total"),
            "seats_used": subscription.get("seats_used"),
            "current_period_end": subscription.get("current_period_end"),
        },
        "sandbox": settings.paddle_sandbox,
    }


# Configuration check endpoint
@router.get("/config")
async def billing_config(user_org: tuple = Depends(require_admin)):
    """Get billing configuration status."""
    is_configured = bool(
        settings.paddle_vendor_id and 
        settings.paddle_api_key and 
        settings.paddle_plan_pro
    )
    
    return {
        "enabled": is_configured,
        "sandbox": settings.paddle_sandbox,
        "message": None if is_configured else "Billing is not configured. Please contact support.",
        "status": "ready" if is_configured else "incomplete"
    }


# Health check endpoint
@router.get("/health")
async def billing_health(user_org: tuple = Depends(require_admin)):
    """Check billing service health."""
    return {
        "paddle_configured": bool(settings.paddle_vendor_id and settings.paddle_api_key),
        "webhook_secret_configured": bool(settings.paddle_webhook_secret),
        "sandbox": settings.paddle_sandbox
    }


# Middleware check for billing enabled
def require_billing_configured():
    """Check if billing is properly configured."""
    if not paddle_service.enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Billing service unavailable",
                "message": "Billing is not configured. Please contact support to enable subscription billing.",
                "code": "BILLING_NOT_CONFIGURED"
            }
        )
