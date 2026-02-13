"""
AI Copilot API Routes
Provides endpoints for the Industrial Subject Matter Expert feature
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.copilot_service import copilot_service
from app.middleware.organization import get_current_user_and_org
from app.posthog_utils import capture_event

router = APIRouter(prefix="/copilot", tags=["copilot"])


class CommandRequest(BaseModel):
    command: str
    quote_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class CommandResponse(BaseModel):
    success: bool
    action: Optional[str] = None
    message: str
    changes: Optional[Dict[str, Any]] = None
    alternatives: Optional[list] = None
    suggestions: Optional[list] = None
    confidence: Optional[float] = None
    sources: Optional[list] = None


@router.post("/command", response_model=CommandResponse)
async def process_command(
    request: CommandRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Process a natural language command from the Copilot command bar.
    
    Examples:
    - "Change Sanpress to Mapress stainless steel"
    - "Find alternatives for item 3"
    - "What's the lead time on XT-400 valves?"
    - "Show me similar past quotes"
    - "Optimize for better margins"
    """
    user_id, org_id = user_org
    
    try:
        result = await copilot_service.process_command(
            command=request.command,
            quote_id=request.quote_id,
            context=request.context
        )
        
        # Track copilot usage
        capture_event(
            distinct_id=user_id,
            event_name="copilot_command",
            properties={
                "command": request.command[:50],
                "action": result.get("action"),
                "success": result.get("success"),
                "quote_id": request.quote_id,
                "organization_id": org_id
            },
            groups={"organization": org_id}
        )
        
        return CommandResponse(**result)
        
    except Exception as e:
        capture_event(
            distinct_id=user_id,
            event_name="copilot_error",
            properties={
                "error": str(e),
                "command": request.command[:50]
            }
        )
        raise HTTPException(status_code=500, detail=f"Copilot error: {str(e)}")


@router.get("/analyze/{quote_id}")
async def analyze_quote(
    quote_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get a comprehensive analysis of a quote with recommendations.
    """
    user_id, org_id = user_org
    
    try:
        result = await copilot_service.analyze_quote(quote_id)
        
        capture_event(
            distinct_id=user_id,
            event_name="copilot_analyze_quote",
            properties={
                "quote_id": quote_id,
                "organization_id": org_id
            },
            groups={"organization": org_id}
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/suggestions/{quote_id}")
async def get_suggestions(
    quote_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get context-aware command suggestions for a quote.
    """
    user_id, org_id = user_org
    
    # Analyze quote to generate contextual suggestions
    analysis = await copilot_service.analyze_quote(quote_id)
    
    suggestions = []
    
    if analysis.get("success"):
        summary = analysis.get("summary", {})
        
        # Add suggestions based on quote state
        if summary.get("low_margin_items", 0) > 0:
            suggestions.append({
                "command": "Optimize for better margins",
                "description": f"Fix {summary['low_margin_items']} low-margin items",
                "icon": "trending-up"
            })
        
        if summary.get("match_rate", 100) < 80:
            suggestions.append({
                "command": "Match items to catalog",
                "description": f"Only {summary['match_rate']}% items matched",
                "icon": "link"
            })
        
        # Always add these general suggestions
        suggestions.extend([
            {
                "command": "Show similar past quotes",
                "description": "Find historical pricing",
                "icon": "history"
            },
            {
                "command": "Find alternatives for item 1",
                "description": "See similar products",
                "icon": "repeat"
            }
        ])
    
    return {
        "quote_id": quote_id,
        "suggestions": suggestions[:4]
    }


@router.post("/apply-change")
async def apply_change(
    quote_id: str,
    change: Dict[str, Any],
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Apply a copilot-suggested change to a quote.
    """
    user_id, org_id = user_org
    
    from app.database_sqlite import update_quote, get_quote_with_items
    
    try:
        # Get current quote
        quote = get_quote_with_items(quote_id, organization_id=org_id)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Apply the change based on type
        action = change.get("action")
        
        if action == "replace_product":
            changes = change.get("changes", {})
            item_index = changes.get("item_index")
            new_item = changes.get("new_item")
            
            if item_index is None or not new_item:
                raise HTTPException(status_code=400, detail="Invalid change data")
            
            # Update the item
            items = quote.get("items", [])
            if 0 <= item_index < len(items):
                items[item_index].update({
                    "product_id": new_item.get("product_id"),
                    "product_name": new_item.get("product_name"),
                    "sku": new_item.get("sku"),
                    "description": new_item.get("description"),
                    "unit_price": new_item.get("unit_price"),
                    "total_price": new_item.get("unit_price", 0) * items[item_index].get("quantity", 1),
                    "metadata": {
                        **items[item_index].get("metadata", {}),
                        "copilot_replaced": True,
                        "replaced_at": "2024-01-01T00:00:00Z"
                    }
                })
                
                # Recalculate totals
                subtotal = sum(item.get("total_price", 0) for item in items)
                tax_rate = quote.get("tax_rate", 0)
                tax_amount = subtotal * (tax_rate / 100)
                total = subtotal + tax_amount
                
                # Save quote
                update_quote(quote_id, {
                    "subtotal": subtotal,
                    "tax_amount": tax_amount,
                    "total": total,
                    "updated_at": "2024-01-01T00:00:00Z"
                }, organization_id=org_id)
                
                capture_event(
                    distinct_id=user_id,
                    event_name="copilot_change_applied",
                    properties={
                        "action": action,
                        "quote_id": quote_id,
                        "organization_id": org_id
                    }
                )
                
                return {
                    "success": True,
                    "message": "Change applied successfully",
                    "quote": get_quote_with_items(quote_id, organization_id=org_id)
                }
        
        raise HTTPException(status_code=400, detail="Unsupported action type")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply change: {str(e)}")


@router.get("/health")
async def copilot_health():
    """Check copilot service health."""
    return {
        "status": "healthy",
        "service": "copilot",
        "version": "1.0.0",
        "features": [
            "natural_language_commands",
            "product_search",
            "quote_analysis",
            "margin_optimization",
            "history_search"
        ]
    }
