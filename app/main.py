"""
Main FastAPI application for OpenMercura.
Uses ONLY free tools: SQLite, OpenRouter, local ChromaDB.
"""

from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.csrf import CSRFMiddleware
from loguru import logger
import sys

# Observability & Telemetry
from app.utils.observability import (
    setup_structured_logging,
    sentry_manager,
    RequestTracingMiddleware,
)

# Configure structured logging (JSON for production, human-readable for dev)
setup_structured_logging()

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
from app.routes import billing
from app.routes import organizations
from app.routes import data
from app.routes import ai_service
from app.routes import projects
from app.routes import email_ingestion
from app.routes import copilot
from app.routes import pdf
from app.routes import email as email_routes
from app.routes import import_csv
from app.routes import password_reset
from app.routes import team_invitations
from app.routes import backups
from app.routes import monitoring
from app.routes import settings as settings_routes
from app.routes import custom_domains

# Custom domain middleware
from app.middleware.custom_domain import CustomDomainMiddleware

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="OpenMercura - Free CRM with AI-powered data capture, competitor analysis, and RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - restrict in production
import os
allow_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
if settings.app_env == "production" and allow_origins == ["*"]:
    # In production, default to same-origin only if not explicitly configured
    logger.warning("CORS_ALLOW_ORIGINS not set in production. Defaulting to same-origin.")
    allow_origins = [settings.app_url]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-User-ID", "X-Organization-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

# Add custom domain middleware (must be early in stack)
app.add_middleware(CustomDomainMiddleware)

# Add global error handler (catches all unhandled exceptions)
# Must be added after CORS but before other middleware
app.add_middleware(ErrorHandlerMiddleware)

# Add request tracing middleware (adds request IDs, timing, logging)
app.add_middleware(RequestTracingMiddleware)

# Add CSRF protection middleware
# Exempts auth endpoints, webhooks, and public quote access
app.add_middleware(
    CSRFMiddleware,
    exempt_paths=[
        "/auth/login",
        "/auth/register", 
        "/auth/logout",
        "/auth/refresh",
        "/webhooks/",
        "/quotes/token/",
        "/quotes/public/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/monitoring/",
        "/health",
    ],
    token_expiry_hours=24
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    default_limit=60,      # 60 requests per minute
    default_window=60,     # 1 minute window
    auth_limit=10,         # 10 auth requests per minute (stricter)
    auth_window=60
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
app.include_router(billing.router)  # B2B subscription management
app.include_router(organizations.router)  # Organization/team management
app.include_router(data.router)  # Data/emails endpoints
app.include_router(ai_service.router)  # AI service management
app.include_router(projects.router)  # Industrial Projects grouping
app.include_router(email_ingestion.router)
app.include_router(copilot.router)  # AI Copilot - Industrial Subject Matter Expert
app.include_router(pdf.router)  # PDF generation
app.include_router(email_routes.router)  # Email sending
app.include_router(settings_routes.router)  # Organization settings (email config)
app.include_router(import_csv.router)  # CSV import
app.include_router(password_reset.router)  # Password reset
app.include_router(team_invitations.router)  # Team invitations
app.include_router(backups.router)  # Database backups
app.include_router(monitoring.router)  # System monitoring
app.include_router(custom_domains.router)  # Custom domain management

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
    from app.ai_provider_service import get_ai_service
    from app.services.monitoring_service import monitoring_service
    
    # Get comprehensive health check
    health = monitoring_service.check_health()
    
    ai_service = get_ai_service()
    stats = ai_service.get_stats()
    
    return {
        "status": health["status"],
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": health["uptime_seconds"],
        "database": "sqlite",
        "checks": health["checks"],
        "ai_service": {
            "status": "configured" if stats["keys"] else "not_configured",
            "total_keys": len(stats["keys"]),
            "gemini_keys": len([k for k in stats["keys"] if k["provider"] == "gemini"]),
            "openrouter_keys": len([k for k in stats["keys"] if k["provider"] == "openrouter"]),
            "success_rate": stats["success_rate"]
        },
        "features": {
            "rate_limiting": True,
            "backups": True,
            "monitoring": True
        }
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.app_env}")
    
    # Security checks
    if settings.app_env == "production":
        if settings.debug:
            logger.warning("SECURITY: Debug mode is enabled in production!")
        if not settings.secret_key or len(settings.secret_key) < 32:
            logger.warning("SECURITY: SECRET_KEY is not set or too short!")
        if os.getenv("ADMIN_PASSWORD"):
            admin_pwd = os.getenv("ADMIN_PASSWORD")
            if len(admin_pwd) < 12:
                logger.warning("SECURITY: ADMIN_PASSWORD is less than 12 characters!")
    
    # Initialize database (SQLite or PostgreSQL)
    from app.database import IS_SQLALCHEMY, init_database, get_database_status
    db_status = get_database_status()
    logger.info(f"Database: {db_status['database_url_masked']} (SQLAlchemy: {db_status['is_sqlalchemy']})")
    init_database()
    
    # Check AI configuration
    from app.ai_provider_service import get_ai_service
    ai_service = get_ai_service()
    stats = ai_service.get_stats()
    
    if stats["keys"]:
        gemini_count = len([k for k in stats["keys"] if k["provider"] == "gemini"])
        openrouter_count = len([k for k in stats["keys"] if k["provider"] == "openrouter"])
        logger.info(f"MultiProviderAIService configured: {gemini_count} Gemini keys, {openrouter_count} OpenRouter keys")
    else:
        logger.warning("No AI API keys configured - AI features will be disabled")
    
    # Initialize RAG service asynchronously (non-blocking)
    import asyncio
    from app.rag_service import get_rag_service
    
    async def init_rag_async():
        """Initialize RAG service in background to avoid blocking startup."""
        try:
            logger.info("Starting RAG service initialization in background...")
            rag_service = get_rag_service()
            if rag_service.is_available():
                logger.info("RAG service initialized successfully (ChromaDB + sentence-transformers)")
            else:
                logger.warning("RAG service not available - install chromadb and sentence-transformers for RAG features")
        except Exception as e:
            logger.error(f"RAG service initialization failed: {e}")
    
    # Start RAG initialization in background (non-blocking)
    asyncio.create_task(init_rag_async())
    
    # Setup scheduled tasks (backups, monitoring, cleanup)
    from app.scheduled_tasks import setup_scheduled_tasks
    setup_scheduled_tasks()
    logger.info("Scheduled tasks initialized (backups, monitoring, cleanup)")
    
    # Print success message (required by instructions)
    print("=" * 50)
    print("Project OpenMercura Ready.")
    print("=" * 50)
    logger.info("Project OpenMercura Ready.")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    from app.scheduled_tasks import shutdown_scheduled_tasks
    shutdown_scheduled_tasks()
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
