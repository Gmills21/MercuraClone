"""
AI Service Management Routes
Provides endpoints for monitoring and managing the multi-provider AI service
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.ai_provider_service import get_ai_service, ProviderType
from app.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Service"])


class AIStatsResponse(BaseModel):
    total_requests: int
    failed_requests: int
    success_rate: float
    last_provider_used: Optional[str]
    keys: List[Dict[str, Any]]


class HealthCheckResponse(BaseModel):
    gemini: Dict[str, Any]
    openrouter: Dict[str, Any]


class TestRequest(BaseModel):
    message: str = "Hello, this is a test message."
    preferred_provider: Optional[str] = None
    temperature: float = 0.7


class TestResponse(BaseModel):
    success: bool
    response: Optional[str]
    provider: Optional[str]
    model: Optional[str]
    error: Optional[str]


@router.get("/stats", response_model=AIStatsResponse)
async def get_ai_stats(current_user: dict = Depends(get_current_user)):
    """Get AI service usage statistics."""
    service = get_ai_service()
    stats = service.get_stats()
    
    return AIStatsResponse(
        total_requests=stats["total_requests"],
        failed_requests=stats["failed_requests"],
        success_rate=stats["success_rate"],
        last_provider_used=stats["last_provider_used"],
        keys=stats["keys"]
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(current_user: dict = Depends(get_current_user)):
    """Check health of all AI providers."""
    service = get_ai_service()
    health = await service.health_check()
    
    return HealthCheckResponse(
        gemini=health.get("gemini", {"status": "unknown", "available": False}),
        openrouter=health.get("openrouter", {"status": "unknown", "available": False})
    )


@router.post("/test", response_model=TestResponse)
async def test_ai_service(
    request: TestRequest,
    current_user: dict = Depends(get_current_user)
):
    """Test the AI service with a simple message."""
    service = get_ai_service()
    
    messages = [
        {"role": "user", "content": request.message}
    ]
    
    preferred = None
    if request.preferred_provider:
        try:
            preferred = ProviderType(request.preferred_provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider: {request.preferred_provider}. Use 'gemini' or 'openrouter'."
            )
    
    result = await service.chat_completion(
        messages=messages,
        temperature=request.temperature,
        preferred_provider=preferred,
        fallback_providers=True
    )
    
    if "error" in result:
        return TestResponse(
            success=False,
            response=None,
            provider=result.get("provider"),
            model=result.get("model"),
            error=result["error"]
        )
    
    try:
        content = result["choices"][0]["message"]["content"]
        return TestResponse(
            success=True,
            response=content,
            provider=result.get("provider"),
            model=result.get("model"),
            error=None
        )
    except (KeyError, IndexError) as e:
        return TestResponse(
            success=False,
            response=None,
            provider=result.get("provider"),
            model=result.get("model"),
            error=f"Failed to parse response: {str(e)}"
        )


@router.get("/providers")
async def list_providers(current_user: dict = Depends(get_current_user)):
    """List available AI providers and their configurations."""
    from app.ai_provider_service import GEMINI_CONFIG, OPENROUTER_CONFIG
    
    return {
        "providers": [
            {
                "name": "gemini",
                "type": "google",
                "default_model": GEMINI_CONFIG.default_model,
                "available_models": GEMINI_CONFIG.available_models,
                "base_url": GEMINI_CONFIG.base_url
            },
            {
                "name": "openrouter",
                "type": "openrouter",
                "default_model": OPENROUTER_CONFIG.default_model,
                "available_models": OPENROUTER_CONFIG.available_models,
                "base_url": OPENROUTER_CONFIG.base_url
            }
        ]
    }