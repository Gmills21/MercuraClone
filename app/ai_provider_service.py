"""
Multi-Provider AI Service for OpenMercura
Manages multiple Gemini and OpenRouter API keys with intelligent rotation and fallback.
Uses API keys from OpenClaw configuration.

Includes production-grade error handling:
- Retry logic with exponential backoff
- Circuit breaker pattern for failing providers
- User-friendly error messages
- Graceful degradation
"""

import os
import json
import random
import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import httpx
from loguru import logger

from app.errors import (
    ai_service_unavailable, ai_rate_limited, ai_extraction_failed,
    AppError, ErrorCategory, ErrorSeverity
)
from app.utils.resilience import (
    with_retry, RetryConfig, CircuitBreaker, CircuitBreakerOpen,
    with_timeout, TimeoutError, get_degradation_manager
)


class ProviderType(Enum):
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


@dataclass
class APIKey:
    """Represents a single API key with usage tracking."""
    key: str
    provider: ProviderType
    name: str
    is_active: bool = True
    last_used: Optional[datetime] = None
    request_count: int = 0
    error_count: int = 0
    rate_limit_reset: Optional[datetime] = None


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    base_url: str
    default_model: str
    available_models: List[str]
    timeout_seconds: float = 30.0  # Reduced from 60s for faster failover
    max_retries: int = 2


# Provider configurations
GEMINI_CONFIG = ProviderConfig(
    base_url="https://generativelanguage.googleapis.com/v1beta",
    default_model="gemini-2.5-flash",
    available_models=[
        "gemini-2.5-flash",
        "gemini-3-flash-preview",
    ]
)

OPENROUTER_CONFIG = ProviderConfig(
    base_url="https://openrouter.ai/api/v1",
    default_model="deepseek/deepseek-r1",
    available_models=[
        "deepseek/deepseek-r1",
        "google/gemini-2.5-pro",
        "anthropic/claude-sonnet-4-5",
        "anthropic/claude-opus-4-5",
        "meta-llama/llama-3.3-70b-instruct",
    ]
)


class MultiProviderAIService:
    """
    Multi-provider AI service with production-grade resilience.
    
    Features:
    - Automatic API key rotation for load balancing
    - Intelligent fallback between providers
    - Rate limit tracking and backoff
    - Usage statistics per key
    - Circuit breaker pattern for failing services
    - Exponential backoff retry logic
    - Graceful degradation when all providers fail
    """
    
    def __init__(self):
        self.keys: List[APIKey] = []
        self.current_key_index = 0
        self._load_keys_from_env()
        
        # Circuit breakers for each provider
        self.circuit_breakers = {
            ProviderType.GEMINI: CircuitBreaker("gemini"),
            ProviderType.OPENROUTER: CircuitBreaker("openrouter")
        }
        
        # Statistics
        self.total_requests = 0
        self.failed_requests = 0
        self.last_provider_used: Optional[ProviderType] = None
        
        # Degradation tracking
        self._degradation_manager = get_degradation_manager()
        
        # Retry configuration for AI calls
        self.retry_config = RetryConfig(
            max_attempts=2,  # 2 attempts per provider
            base_delay=1.0,
            max_delay=10.0,
            jitter=True,
            retryable_exceptions=[
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.NetworkError,
                RateLimitError,
                ServiceUnavailableError
            ]
        )
        
        logger.info(f"MultiProviderAIService initialized with {len(self.keys)} API keys")
        logger.info(f"  - Gemini keys: {len([k for k in self.keys if k.provider == ProviderType.GEMINI])}")
        logger.info(f"  - OpenRouter keys: {len([k for k in self.keys if k.provider == ProviderType.OPENROUTER])}")
    
    def _load_keys_from_env(self):
        """Load all API keys from environment variables."""
        # Load Gemini keys (GEMINI_API_KEY and GEMINI_API_KEY_1 through _9)
        gemini_keys = []
        
        # Primary key
        primary_gemini = os.getenv("GEMINI_API_KEY", "")
        if primary_gemini:
            gemini_keys.append(("primary", primary_gemini))
        
        # Additional keys
        for i in range(1, 10):
            key = os.getenv(f"GEMINI_API_KEY_{i}", "")
            if key:
                gemini_keys.append((f"key_{i}", key))
        
        for name, key in gemini_keys:
            self.keys.append(APIKey(
                key=key,
                provider=ProviderType.GEMINI,
                name=f"gemini:{name}"
            ))
        
        # Load OpenRouter keys (OPENROUTER_API_KEY_1 through _9)
        for i in range(1, 10):
            key = os.getenv(f"OPENROUTER_API_KEY_{i}", "")
            if key:
                self.keys.append(APIKey(
                    key=key,
                    provider=ProviderType.OPENROUTER,
                    name=f"openrouter:key_{i}"
                ))
        
        # Shuffle keys for load balancing
        random.shuffle(self.keys)
    
    def _get_next_key(self, preferred_provider: Optional[ProviderType] = None) -> Optional[APIKey]:
        """Get the next available API key using round-robin with provider preference."""
        if not self.keys:
            return None
        
        # Filter active keys not under rate limit
        now = datetime.now()
        available_keys = [
            k for k in self.keys 
            if k.is_active and (k.rate_limit_reset is None or k.rate_limit_reset < now)
        ]
        
        if not available_keys:
            logger.warning("All API keys are rate limited or inactive")
            return None
        
        # Prefer specific provider if requested
        if preferred_provider:
            provider_keys = [k for k in available_keys if k.provider == preferred_provider]
            if provider_keys:
                # Round-robin within provider
                key = provider_keys[self.current_key_index % len(provider_keys)]
                self.current_key_index += 1
                return key
        
        # Fall back to any available key
        key = available_keys[self.current_key_index % len(available_keys)]
        self.current_key_index += 1
        return key
    
    def _get_provider_config(self, provider: ProviderType) -> ProviderConfig:
        """Get configuration for a provider."""
        if provider == ProviderType.GEMINI:
            return GEMINI_CONFIG
        return OPENROUTER_CONFIG
    
    def _get_headers(self, api_key: APIKey) -> Dict[str, str]:
        """Get headers for API request."""
        headers = {
            "Content-Type": "application/json",
        }
        
        if api_key.provider == ProviderType.GEMINI:
            # Gemini uses key in URL, not header
            pass
        elif api_key.provider == ProviderType.OPENROUTER:
            headers["Authorization"] = f"Bearer {api_key.key}"
            headers["HTTP-Referer"] = "https://openmercura.local"
            headers["X-Title"] = "OpenMercura"
        
        return headers
    
    async def _call_gemini(
        self,
        api_key: APIKey,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """Call Gemini API with timeout and error handling."""
        config = self._get_provider_config(ProviderType.GEMINI)
        
        # Convert OpenAI-style messages to Gemini format
        system_parts = []
        user_parts = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_parts.append({"text": msg["content"]})
            elif msg["role"] == "user":
                user_parts.append({"text": msg["content"]})
        
        # Build Gemini request body
        contents = []
        if user_parts:
            contents.append({"role": "user", "parts": user_parts})
        
        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or 2048,
            }
        }
        
        if system_parts:
            body["systemInstruction"] = {"parts": system_parts}
        
        url = f"{config.base_url}/models/{model}:generateContent?key={api_key.key}"
        
        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            try:
                response = await client.post(
                    url,
                    headers=self._get_headers(api_key),
                    json=body
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    reset_time = datetime.now() + timedelta(minutes=1)
                    api_key.rate_limit_reset = reset_time
                    raise RateLimitError(f"Gemini rate limited until {reset_time}")
                
                # Handle service unavailable
                if response.status_code >= 500:
                    raise ServiceUnavailableError(f"Gemini returned {response.status_code}")
                
                response.raise_for_status()
                data = response.json()
                
                # Check for blocked content
                if data.get("promptFeedback", {}).get("blockReason"):
                    raise ContentBlockedError(
                        f"Content blocked: {data['promptFeedback']['blockReason']}"
                    )
                
                # Convert Gemini response to OpenAI-like format
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    
                    return {
                        "choices": [{
                            "message": {"content": text, "role": "assistant"},
                            "finish_reason": "stop"
                        }],
                        "model": model,
                        "provider": "gemini"
                    }
                
                raise ValueError(f"No candidates in Gemini response: {data}")
                
            except httpx.TimeoutException:
                raise TimeoutError(f"Gemini request timed out after {config.timeout_seconds}s")
            except httpx.ConnectError as e:
                raise ServiceUnavailableError(f"Cannot connect to Gemini: {e}")
    
    async def _call_openrouter(
        self,
        api_key: APIKey,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """Call OpenRouter API with timeout and error handling."""
        config = self._get_provider_config(ProviderType.OPENROUTER)
        
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            body["max_tokens"] = max_tokens
        
        url = f"{config.base_url}/chat/completions"
        
        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            try:
                response = await client.post(
                    url,
                    headers=self._get_headers(api_key),
                    json=body
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    reset_time = datetime.now() + timedelta(minutes=1)
                    api_key.rate_limit_reset = reset_time
                    raise RateLimitError(f"OpenRouter rate limited until {reset_time}")
                
                # Handle service unavailable
                if response.status_code >= 500:
                    raise ServiceUnavailableError(f"OpenRouter returned {response.status_code}")
                
                response.raise_for_status()
                data = response.json()
                data["provider"] = "openrouter"
                return data
                
            except httpx.TimeoutException:
                raise TimeoutError(f"OpenRouter request timed out after {config.timeout_seconds}s")
            except httpx.ConnectError as e:
                raise ServiceUnavailableError(f"Cannot connect to OpenRouter: {e}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        preferred_provider: Optional[ProviderType] = None,
        fallback_providers: bool = True
    ) -> Dict[str, Any]:
        """
        Send a chat completion request with full resilience patterns.
        
        Features:
        - Circuit breaker protection
        - Retry with exponential backoff per provider
        - Automatic failover between providers
        - Graceful degradation when all fail
        """
        self.total_requests += 1
        
        # Build provider preference order
        providers_to_try = []
        if preferred_provider:
            providers_to_try.append(preferred_provider)
        if fallback_providers:
            for provider in ProviderType:
                if provider not in providers_to_try:
                    providers_to_try.append(provider)
        
        last_error = None
        errors_by_provider = {}
        
        for provider in providers_to_try:
            config = self._get_provider_config(provider)
            model_to_use = model or config.default_model
            
            # Check circuit breaker
            breaker = self.circuit_breakers[provider]
            if breaker.is_open:
                logger.warning(f"Circuit breaker open for {provider.value}, skipping")
                errors_by_provider[provider.value] = "circuit_breaker_open"
                continue
            
            # Try with retry logic
            for attempt in range(self.retry_config.max_attempts):
                api_key = self._get_next_key(provider)
                if not api_key:
                    logger.warning(f"No available keys for {provider.value}")
                    errors_by_provider[provider.value] = "no_keys_available"
                    break
                
                try:
                    logger.debug(f"Trying {api_key.name} with {model_to_use} (attempt {attempt + 1})")
                    
                    if provider == ProviderType.GEMINI:
                        result = await self._call_gemini(
                            api_key, messages, model_to_use, temperature, max_tokens
                        )
                    else:
                        result = await self._call_openrouter(
                            api_key, messages, model_to_use, temperature, max_tokens
                        )
                    
                    # Success - update stats
                    api_key.last_used = datetime.now()
                    api_key.request_count += 1
                    self.last_provider_used = provider
                    breaker.record_success()
                    
                    # Clear degradation flag if it was set
                    self._degradation_manager.restore("ai_service")
                    
                    logger.info(f"Success with {api_key.name} using {model_to_use}")
                    return result
                    
                except RateLimitError as e:
                    logger.warning(f"Rate limit hit for {api_key.name}: {e}")
                    api_key.error_count += 1
                    last_error = e
                    errors_by_provider[provider.value] = f"rate_limited:{api_key.name}"
                    
                    # Don't retry immediately on rate limit, try next key
                    await asyncio.sleep(self.retry_config.calculate_delay(attempt))
                    
                except (TimeoutError, ServiceUnavailableError) as e:
                    logger.warning(f"Transient error with {api_key.name}: {e}")
                    api_key.error_count += 1
                    last_error = e
                    errors_by_provider[provider.value] = f"{type(e).__name__}:{api_key.name}"
                    
                    # Calculate backoff delay
                    delay = self.retry_config.calculate_delay(attempt)
                    if attempt < self.retry_config.max_attempts - 1:
                        logger.info(f"Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"Unexpected error with {api_key.name}: {e}")
                    api_key.error_count += 1
                    last_error = e
                    errors_by_provider[provider.value] = f"unexpected:{type(e).__name__}"
                    breaker.record_failure()
                    # Don't retry on unexpected errors
                    break
            
            # If we exhausted retries for this provider, record failure
            if last_error:
                breaker.record_failure()
        
        # All providers failed
        self.failed_requests += 1
        
        # Mark service as degraded
        self._degradation_manager.mark_degraded(
            "ai_service",
            f"All AI providers failed: {errors_by_provider}",
            fallback_available=True
        )
        
        # Return structured error - this will be caught by error handler
        error = ai_service_unavailable(
            detail=f"Errors by provider: {errors_by_provider}"
        )
        
        # Return error dict for backward compatibility
        return {
            "error": error.message,
            "error_code": error.code,
            "errors_by_provider": errors_by_provider,
            "choices": None,
            "retryable": True,
            "retry_after": 30
        }
    
    async def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: Optional[str] = None,
        temperature: float = 0.1,
        preferred_provider: Optional[ProviderType] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data with error handling.
        
        Returns user-friendly errors for extraction failures.
        """
        system_prompt = f"""You are a data extraction assistant. Extract structured information from the provided text.

Output Format: Return ONLY valid JSON matching this schema:
{json.dumps(schema, indent=2)}

{instructions or ''}

Important: Return ONLY the JSON object, no markdown formatting, no explanations."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract data from this text:\n\n{text}"},
        ]
        
        result = await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=2048,
            preferred_provider=preferred_provider,
            fallback_providers=True
        )
        
        if "error" in result:
            # Propagate error with context
            return {
                "success": False,
                "error": result["error"],
                "error_code": result.get("error_code", "AI_SERVICE_ERROR"),
                "retryable": result.get("retryable", True),
                "retry_after": result.get("retry_after", 30)
            }
        
        try:
            content = result["choices"][0]["message"]["content"]
            # Clean up potential markdown formatting
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            parsed = json.loads(content)
            return {
                "success": True, 
                "data": parsed,
                "provider": result.get("provider"),
                "model": result.get("model")
            }
            
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse extraction result: {e}")
            error = ai_extraction_failed("parse the extracted data")
            return {
                "success": False,
                "error": error.message,
                "error_code": error.code,
                "retryable": True,
                "suggested_action": error.suggested_action
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all API keys."""
        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": 1 - (self.failed_requests / max(1, self.total_requests)),
            "last_provider_used": self.last_provider_used.value if self.last_provider_used else None,
            "circuit_breakers": {
                name: breaker.get_status()
                for name, breaker in self.circuit_breakers.items()
            },
            "keys": [
                {
                    "name": k.name,
                    "provider": k.provider.value,
                    "is_active": k.is_active,
                    "request_count": k.request_count,
                    "error_count": k.error_count,
                    "last_used": k.last_used.isoformat() if k.last_used else None,
                    "rate_limited_until": k.rate_limit_reset.isoformat() if k.rate_limit_reset else None
                }
                for k in self.keys
            ]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers."""
        results = {}
        
        for provider in ProviderType:
            config = self._get_provider_config(provider)
            key = self._get_next_key(provider)
            breaker = self.circuit_breakers[provider]
            
            if breaker.is_open:
                results[provider.value] = {
                    "status": "circuit_open",
                    "available": False,
                    "retry_after": breaker.config.recovery_timeout
                }
                continue
            
            if not key:
                results[provider.value] = {"status": "no_keys", "available": False}
                continue
            
            try:
                # Quick health check with timeout
                messages = [{"role": "user", "content": "Hi"}]
                
                if provider == ProviderType.GEMINI:
                    await with_timeout(
                        self._call_gemini(key, messages, config.default_model, 0.1, 10),
                        timeout_seconds=10.0
                    )
                else:
                    await with_timeout(
                        self._call_openrouter(key, messages, config.default_model, 0.1, 10),
                        timeout_seconds=10.0
                    )
                
                results[provider.value] = {"status": "healthy", "available": True}
                breaker.record_success()
                
            except TimeoutError:
                results[provider.value] = {"status": "timeout", "available": False}
                breaker.record_failure()
            except Exception as e:
                results[provider.value] = {"status": f"error: {str(e)[:50]}", "available": False}
                breaker.record_failure()
        
        return results


# Custom exceptions for the AI service
class RateLimitError(Exception):
    """Raised when an API key hits rate limits."""
    pass


class ServiceUnavailableError(Exception):
    """Raised when service returns 5xx errors."""
    pass


class ContentBlockedError(Exception):
    """Raised when content is blocked by the provider."""
    pass


# Singleton instance
_ai_service: Optional[MultiProviderAIService] = None


def get_ai_service() -> MultiProviderAIService:
    """Get or create the AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = MultiProviderAIService()
    return _ai_service


# Convenience functions for common operations
async def chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    preferred_provider: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for chat completion."""
    service = get_ai_service()
    provider = None
    if preferred_provider:
        try:
            provider = ProviderType(preferred_provider.lower())
        except ValueError:
            pass
    
    return await service.chat_completion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
        preferred_provider=provider
    )


async def extract_structured_data(
    text: str,
    schema: Dict[str, Any],
    instructions: Optional[str] = None,
    preferred_provider: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for structured data extraction."""
    service = get_ai_service()
    provider = None
    if preferred_provider:
        try:
            provider = ProviderType(preferred_provider.lower())
        except ValueError:
            pass
    
    return await service.extract_structured_data(
        text=text,
        schema=schema,
        instructions=instructions,
        preferred_provider=provider
    )
