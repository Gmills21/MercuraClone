"""
Main FastAPI application for OpenMercura.
Uses ONLY free tools: SQLite, OpenRouter, local ChromaDB.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.config import settings
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)
logger.add(
    settings.log_file,
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)

# Import integrations (auto-registers providers)
from app.integrations import ERPRegistry
from app.integrations.quickbooks import QuickBooksProvider

# Import new routes (free tier versions)
from app.routes import customers_new as customers
from app.routes import products_new as products
from app.routes import quotes_new as quotes
from app.routes import extractions
from app.routes import competitors
from app.routes import rag
from app.routes import auth
from app.routes import analytics
from app.routes import templates
from app.routes import portal
from app.routes import erp_export
from app.routes import quickbooks
from app.routes import alerts
from app.routes import intelligence
from app.routes import image_extract
from app.routes import impact
from app.routes import onboarding
from app.routes import extraction_unified
from app.routes import knowledge_base

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="OpenMercura - Free CRM with AI-powered data capture, competitor analysis, and RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(quotes.router)
app.include_router(extractions.router)  # Legacy - keep for compatibility
app.include_router(extraction_unified.router)  # New unified extraction
app.include_router(competitors.router)
app.include_router(rag.router)
app.include_router(analytics.router)
app.include_router(templates.router)
app.include_router(portal.router)
app.include_router(erp_export.router)
app.include_router(quickbooks.router)  # Legacy - redirects to integrations
app.include_router(alerts.router)
app.include_router(intelligence.router)
app.include_router(image_extract.router)  # Legacy - redirects to unified
app.include_router(impact.router)
app.include_router(onboarding.router)
app.include_router(knowledge_base.router)  # Optional feature

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
assets_path = os.path.join(frontend_path, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    logger.info(f"Serving frontend from {frontend_path}")
else:
    logger.warning(f"Frontend assets not found at {assets_path}")


@app.get("/")
async def root():
    """Serve the frontend dashboard."""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    # Fallback to API info if frontend not built
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app_env,
        "docs": "/docs",
        "message": "Frontend not built. Run 'npm run build' in frontend/ directory.",
        "features": {
            "crm": True,
            "quotes": True,
            "competitor_analysis": True,
            "rag": "available" if settings.openrouter_api_key else "needs_api_key",
            "multi_user": True,
            "analytics": True,
            "industry_templates": True,
            "customer_portal": True,
            "erp_export": True,
            "quickbooks": bool(settings.quickbooks_client_id),
            "knowledge_base": "optional - enable with KNOWLEDGE_BASE_ENABLED=true"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "sqlite",
        "ai_provider": "openrouter" if settings.openrouter_api_key else "not_configured"
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.app_env}")
    
    # Check AI configuration
    if settings.openrouter_api_key:
        logger.info("OpenRouter API configured")
    else:
        logger.warning("OpenRouter API key not set - AI features will be disabled")
    
    # Initialize RAG service
    from app.rag_service import get_rag_service
    rag_service = get_rag_service()
    if rag_service.is_available():
        logger.info("RAG service initialized (ChromaDB + sentence-transformers)")
    else:
        logger.warning("RAG service not available - install chromadb and sentence-transformers for RAG features")
    
    # Print success message (required by instructions)
    print("=" * 50)
    print("Project OpenMercura Ready.")
    print("=" * 50)
    logger.info("Project OpenMercura Ready.")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
