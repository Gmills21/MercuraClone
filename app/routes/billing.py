"""
Billing and Subscription API routes.
Handles subscription management, checkout, and Paddle webhooks.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import Optional, List
import logging
from datetime import datetime, timedelta
import json

from app.models_billing import (
    SubscriptionPlan, Subscription, Invoice, PaymentMethod,
    BillingAddress, SeatAssignment, UsageRecord,
    CreateSubscriptionRequest, UpdateSubscriptionRequest,
    CheckoutSessionRequest, CheckoutSessionResponse,
    BillingPortalRequest, BillingPortalResponse,
    SubscriptionStatus, BillingInterval
)
from app.services.paddle_service import paddle_service
from app.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# ==================== SUBSCRIPTION PLANS ====================

@router.get("/plans", response_model=List[SubscriptionPlan])
async def list_subscription_plans():
    """List all available subscription plans."""
    # For now, return hardcoded plans
    # In production, fetch from database
    plans = [
        SubscriptionPlan(
            id="plan_basic",
            name="Basic",
            description="Perfect for small teams",
            price_per_seat=150.00,
            billing_interval=BillingInterval.MONTHLY,
            paddle_plan_id=os.getenv("PADDLE_PLAN_BASIC_MONTHLY"),
            features=[
                "Unlimited quotes",
                "Email integration",
                "Basic analytics",
                "Standard support"
            ],
            max_seats=10
        ),
        SubscriptionPlan(
            id="plan_professional",
            name="Professional",
            description="For growing businesses",
            price_per_seat=250.00,
            billing_interval=BillingInterval.MONTHLY,
            paddle_plan_id=os.getenv("PADDLE_PLAN_PRO_MONTHLY"),
            features=[
                "Everything in Basic",
                "Advanced analytics",
                "QuickBooks integration",
                "Priority support",
                "Custom branding"
            ],
            max_seats=50
        ),
        SubscriptionPlan(
            id="plan_enterprise",
            name="Enterprise",
            description="For large organizations",
            price_per_seat=400.00,
            billing_interval=BillingInterval.MONTHLY,
            paddle_plan_id=os.getenv("PADDLE_PLAN_ENTERPRISE_MONTHLY"),
            features=[
                "Everything in Professional",
                "Dedicated account manager",
                "Custom integrations",
                "SLA guarantee",
                "Advanced security"
            ],
            max_seats=None  # Unlimited
        )
    ]
    return plans


# ==================== CHECKOUT ====================

@router.post("/checkout/create-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a Paddle checkout session for subscription.
    """
    try:
        # Get user details (in production, fetch from database)
        user_email = "user@example.com"  # Replace with actual user email
        user_name = "Test User"  # Replace with actual user name
        
        # Create checkout session
        session = await paddle_service.create_checkout_session(
            plan_id=request.plan_id,
            seats=request.seats,
            customer_email=user_email,
            customer_name=user_name,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": user_id,
                "seats": request.seats,
                "billing_interval": request.billing_interval
            }
        )
        
        return CheckoutSessionResponse(
            checkout_url=session["checkout_url"],
            session_id=session["session_id"]
        )
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SUBSCRIPTIONS ====================

@router.get("/subscription", response_model=Optional[Subscription])
async def get_current_subscription(user_id: str = Depends(get_current_user_id)):
    """Get current user's subscription."""
    # In production, fetch from database
    # For now, return mock data
    return Subscription(
        id="sub_123",
        user_id=user_id,
        plan_id="plan_professional",
        paddle_subscription_id="paddle_sub_123",
        status=SubscriptionStatus.ACTIVE,
        seats=3,
        price_per_seat=250.00,
        total_amount=750.00,
        billing_interval=BillingInterval.MONTHLY,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30)
    )


@router.post("/subscription/update")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Update current subscription (seats, plan, etc.)."""
    try:
        # Get current subscription from database
        # subscription = await db.get_subscription_by_user(user_id)
        
        # For now, use mock data
        paddle_subscription_id = "paddle_sub_123"
        
        # Update in Paddle
        success = await paddle_service.update_subscription(
            subscription_id=paddle_subscription_id,
            quantity=request.seats,
            plan_id=request.plan_id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update subscription")
        
        # Update in database
        # await db.update_subscription(subscription_id, request)
        
        return {"success": True, "message": "Subscription updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription/cancel")
async def cancel_subscription(
    cancel_at_period_end: bool = True,
    user_id: str = Depends(get_current_user_id)
):
    """Cancel current subscription."""
    try:
        # Get current subscription
        paddle_subscription_id = "paddle_sub_123"
        
        if cancel_at_period_end:
            # Cancel at end of billing period
            success = await paddle_service.update_subscription(
                subscription_id=paddle_subscription_id,
                pause=True
            )
        else:
            # Cancel immediately
            success = await paddle_service.cancel_subscription(paddle_subscription_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel subscription")
        
        return {"success": True, "message": "Subscription canceled successfully"}
        
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INVOICES ====================

@router.get("/invoices", response_model=List[Invoice])
async def list_invoices(user_id: str = Depends(get_current_user_id)):
    """List all invoices for current user."""
    # In production, fetch from database
    return []


@router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific invoice."""
    # In production, fetch from database
    raise HTTPException(status_code=404, detail="Invoice not found")


# ==================== BILLING PORTAL ====================

@router.post("/portal/create-session", response_model=BillingPortalResponse)
async def create_billing_portal_session(
    request: BillingPortalRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a billing portal session.
    Note: Paddle doesn't have a hosted portal, so we return our custom billing page.
    """
    portal_url = await paddle_service.create_billing_portal_session(
        customer_id=user_id,
        return_url=request.return_url
    )
    
    return BillingPortalResponse(portal_url=portal_url or request.return_url)


# ==================== SEAT MANAGEMENT ====================

@router.get("/seats", response_model=List[SeatAssignment])
async def list_seat_assignments(user_id: str = Depends(get_current_user_id)):
    """List all seat assignments for current subscription."""
    # In production, fetch from database
    return []


@router.post("/seats/assign")
async def assign_seat(
    sales_rep_email: str,
    sales_rep_name: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Assign a seat to a sales rep."""
    # In production, create seat assignment in database
    return {"success": True, "message": "Seat assigned successfully"}


@router.post("/seats/{seat_id}/deactivate")
async def deactivate_seat(seat_id: str, user_id: str = Depends(get_current_user_id)):
    """Deactivate a seat assignment."""
    # In production, deactivate in database
    return {"success": True, "message": "Seat deactivated successfully"}


# ==================== USAGE TRACKING ====================

@router.get("/usage")
async def get_usage_stats(user_id: str = Depends(get_current_user_id)):
    """Get usage statistics for current billing period."""
    # In production, fetch from database
    return {
        "quotes_generated": 45,
        "emails_processed": 120,
        "seats_used": 3,
        "seats_total": 5,
        "period_start": datetime.utcnow().isoformat(),
        "period_end": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }


# ==================== WEBHOOKS ====================

@router.post("/webhooks/paddle")
async def paddle_webhook(request: Request):
    """
    Handle Paddle webhook events.
    """
    try:
        # Get raw body
        body = await request.body()
        payload = await request.form()
        payload_dict = dict(payload)
        
        # Verify signature
        signature = payload_dict.get("p_signature", "")
        if not paddle_service.verify_webhook(payload_dict, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Process webhook
        event_data = await paddle_service.process_webhook(payload_dict)
        
        # Handle different event types
        alert_name = event_data["type"]
        
        if alert_name == "subscription_created":
            # Create subscription in database
            logger.info(f"Subscription created: {event_data['subscription_id']}")
            
        elif alert_name == "subscription_updated":
            # Update subscription in database
            logger.info(f"Subscription updated: {event_data['subscription_id']}")
            
        elif alert_name == "subscription_cancelled":
            # Mark subscription as canceled
            logger.info(f"Subscription cancelled: {event_data['subscription_id']}")
            
        elif alert_name == "subscription_payment_succeeded":
            # Create invoice record
            logger.info(f"Payment succeeded: {event_data['subscription_id']}")
            
        elif alert_name == "subscription_payment_failed":
            # Handle failed payment
            logger.warning(f"Payment failed: {event_data['subscription_id']}")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error processing Paddle webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


import os
