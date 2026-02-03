"""
Competitor Analysis API routes.
Uses free web scraping + DeepSeek analysis.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from app.competitor_scraper import CompetitorScraper, scrape_multiple
from app.deepseek_service import get_deepseek_service
from app.database_sqlite import save_competitor, get_competitor_by_url, list_competitors
from fastapi import Depends
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/competitors", tags=["competitors"])


class CompetitorAnalyzeRequest(BaseModel):
    url: str


class CompetitorBatchRequest(BaseModel):
    urls: List[str]


class CompetitorResponse(BaseModel):
    id: str
    url: str
    name: str
    title: Optional[str]
    description: Optional[str]
    keywords: List[str]
    pricing: Optional[str]
    features: List[str]
    last_updated: str
    error: Optional[str] = None


@router.post("/analyze")
async def analyze_competitor(
    request: CompetitorAnalyzeRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Analyze a competitor website.
    Scrapes the site and uses AI to extract insights.
    """
    scraper = CompetitorScraper()
    deepseek = get_deepseek_service()
    user_id, org_id = user_org
    
    # Scrape the website
    scraped = await scraper.scrape(request.url)
    
    if not scraped.get("success"):
        # Save error state
        competitor_data = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "url": request.url,
            "name": "Unknown",
            "error": scraped.get("error", "Unknown error"),
            "last_updated": datetime.utcnow().isoformat()
        }
        save_competitor(competitor_data)
        raise HTTPException(status_code=400, detail=scraped.get("error", "Scraping failed"))
    
    # Analyze with DeepSeek
    analysis = await deepseek.analyze_competitor(request.url, scraped)
    
    if "error" in analysis:
        raise HTTPException(status_code=500, detail=analysis["error"])
    
    # Save to database
    competitor_data = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "url": request.url,
        "name": analysis.get("name", "Unknown"),
        "title": scraped.get("title"),
        "description": analysis.get("description"),
        "keywords": scraped.get("keywords", []),
        "pricing": analysis.get("pricing"),
        "features": analysis.get("features", []),
        "last_updated": datetime.utcnow().isoformat()
    }
    
    save_competitor(competitor_data)
    
    return competitor_data


@router.post("/analyze-batch")
async def analyze_competitors_batch(
    request: CompetitorBatchRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Analyze multiple competitor websites."""
    user_id, org_id = user_org
    scraper = CompetitorScraper()
    deepseek = get_deepseek_service()
    
    results = []
    
    for url in request.urls:
        # Check if already analyzed
        existing = get_competitor_by_url(url, organization_id=org_id)
        if existing and not existing.get("error"):
            results.append(existing)
            continue
        
        # Scrape
        scraped = await scraper.scrape(url)
        if not scraped.get("success"):
            results.append({
                "url": url,
                "error": scraped.get("error"),
                "success": False
            })
            continue
        
        # Analyze
        analysis = await deepseek.analyze_competitor(url, scraped)
        
        competitor_data = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "url": url,
            "name": analysis.get("name", "Unknown"),
            "title": scraped.get("title"),
            "description": analysis.get("description"),
            "keywords": scraped.get("keywords", []),
            "pricing": analysis.get("pricing"),
            "features": analysis.get("features", []),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        save_competitor(competitor_data)
        results.append(competitor_data)
    
    return {"results": results, "count": len(results)}


@router.get("/", response_model=List[CompetitorResponse])
async def list_competitors_endpoint(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """List all analyzed competitors."""
    user_id, org_id = user_org
    competitors = list_competitors(organization_id=org_id)
    return [
        CompetitorResponse(
            id=c["id"],
            url=c["url"],
            name=c["name"],
            title=c.get("title"),
            description=c.get("description"),
            keywords=c.get("keywords", []),
            pricing=c.get("pricing"),
            features=c.get("features", []),
            last_updated=c["last_updated"],
            error=c.get("error")
        )
        for c in competitors
    ]


@router.get("/{competitor_id}")
async def get_competitor(
    competitor_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get competitor by ID."""
    user_id, org_id = user_org
    competitors = list_competitors(organization_id=org_id)
    for c in competitors:
        if c["id"] == competitor_id:
            return c
    raise HTTPException(status_code=404, detail="Competitor not found")


@router.post("/compare")
async def compare_with_products(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Compare competitors with our products.
    Returns price/feature comparisons where SKUs are mapped.
    """
    user_id, org_id = user_org
    from app.database_sqlite import list_products, list_competitors
    
    products = list_products(organization_id=org_id)
    competitors = list_competitors(organization_id=org_id)
    
    comparisons = []
    
    for product in products:
        comp_sku = product.get("competitor_sku")
        if comp_sku:
            # Find competitor that mentions this SKU in their data
            matched_competitor = None
            for comp in competitors:
                # Check if SKU appears in any competitor data field
                comp_text = f"{comp.get('name', '')} {comp.get('description', '')} {' '.join(comp.get('features', []))}"
                if comp_sku.lower() in comp_text.lower():
                    matched_competitor = comp
                    break
            
            comparisons.append({
                "product": product,
                "competitor_sku": comp_sku,
                "competitor": matched_competitor,
                "our_price": product["price"],
                "competitor_url": matched_competitor["url"] if matched_competitor else None,
                "status": "matched" if matched_competitor else "sku_mapped_no_competitor_data"
            })
    
    return {
        "comparisons": comparisons,
        "total_mapped": len(comparisons),
        "total_products": len(products),
        "total_competitors": len(competitors)
    }
