"""
Main FastAPI application for Mercura.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import webhooks, export, data, quotes, customers, products
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

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Automated Email-to-Data Pipeline - Extract structured data from emails and attachments",
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
app.include_router(webhooks.router)
app.include_router(export.router)
app.include_router(data.router)
app.include_router(quotes.router)
app.include_router(customers.router)
app.include_router(products.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app_env,
        "email_provider": settings.email_provider,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Email Provider: {settings.email_provider}")
    
    # Validate required settings
    is_valid, missing_fields = settings.validate_required_settings()
    if not is_valid:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_fields)}. "
            "Some features may not work correctly. Please set these in your deployment environment."
        )
    else:
        logger.info("All required environment variables are set")
    
    # Validate email provider configuration
    if not settings.validate_email_provider():
        logger.warning(
            f"Email provider '{settings.email_provider}' is not properly configured. "
            "Webhooks may not work correctly."
        )


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
