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
async def analyze_competitor(request: CompetitorAnalyzeRequest):
    """
    Analyze a competitor website.
    Scrapes the site and uses AI to extract insights.
    """
    scraper = CompetitorScraper()
    deepseek = get_deepseek_service()
    
    # Scrape the website
    scraped = await scraper.scrape(request.url)
    
    if not scraped.get("success"):
        # Save error state
        competitor_data = {
            "id": str(uuid.uuid4()),
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
async def analyze_competitors_batch(request: CompetitorBatchRequest):
    """Analyze multiple competitor websites."""
    scraper = CompetitorScraper()
    deepseek = get_deepseek_service()
    
    results = []
    
    for url in request.urls:
        # Check if already analyzed
        existing = get_competitor_by_url(url)
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
async def list_competitors_endpoint():
    """List all analyzed competitors."""
    competitors = list_competitors()
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
async def get_competitor(competitor_id: str):
    """Get competitor by ID."""
    competitors = list_competitors()
    for c in competitors:
        if c["id"] == competitor_id:
            return c
    raise HTTPException(status_code=404, detail="Competitor not found")


@router.post("/compare")
async def compare_with_products():
    """
    Compare competitors with our products.
    Returns price/feature comparisons where SKUs are mapped.
    """
    from app.database_sqlite import list_products, list_competitors
    
    products = list_products()
    competitors = list_competitors()
    
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
