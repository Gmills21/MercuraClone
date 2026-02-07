# OpenMercura Multi-Provider AI Service

## Overview

OpenMercura now uses a **Multi-Provider AI Service** that intelligently manages multiple Gemini and OpenRouter API keys with automatic rotation, load balancing, and intelligent fallback.

## Features

- **Multiple API Key Support**: Load up to 9 Gemini keys and 9 OpenRouter keys
- **Intelligent Rotation**: Automatic round-robin load balancing across all available keys
- **Smart Fallback**: If one provider fails, automatically tries the other
- **Rate Limit Handling**: Tracks rate limits and temporarily excludes exhausted keys
- **Usage Statistics**: Per-key tracking of requests, errors, and success rates
- **Health Monitoring**: Built-in health check endpoint for all providers

## Configuration

### 1. Set Up Environment Variables

Copy the example file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Gemini API Keys (Primary + up to 9 additional)
GEMINI_API_KEY=AIzaSy...
GEMINI_API_KEY_1=AIzaSy...
GEMINI_API_KEY_2=AIzaSy...
# ... up to GEMINI_API_KEY_9

# OpenRouter API Keys (up to 9 keys)
OPENROUTER_API_KEY_1=sk-or-v1-...
OPENROUTER_API_KEY_2=sk-or-v1-...
# ... up to OPENROUTER_API_KEY_9
```

### 2. API Key Sources

**Gemini API Keys**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

**OpenRouter API Keys**: Get from [OpenRouter](https://openrouter.ai/keys)

## API Endpoints

### Health Check
```
GET /ai/health
```
Check the status of all AI providers.

**Response:**
```json
{
  "gemini": {"status": "healthy", "available": true},
  "openrouter": {"status": "healthy", "available": true}
}
```

### Usage Statistics
```
GET /ai/stats
```
Get detailed usage statistics for all API keys.

**Response:**
```json
{
  "total_requests": 150,
  "failed_requests": 2,
  "success_rate": 0.9867,
  "last_provider_used": "gemini",
  "keys": [
    {
      "name": "gemini:key_1",
      "provider": "gemini",
      "request_count": 50,
      "error_count": 0,
      "is_active": true
    },
    {
      "name": "openrouter:key_1",
      "provider": "openrouter",
      "request_count": 100,
      "error_count": 2,
      "is_active": true
    }
  ]
}
```

### Test AI Service
```
POST /ai/test
```
Test the AI service with a simple message.

**Request:**
```json
{
  "message": "Hello, how are you?",
  "preferred_provider": "gemini",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "response": "I'm doing well, thank you for asking!",
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "error": null
}
```

### List Providers
```
GET /ai/providers
```
List available providers and their configurations.

## Supported Models

### Gemini (Google)
- `gemini-2.5-flash` (default)
- `gemini-3-flash-preview`

### OpenRouter
- `deepseek/deepseek-r1` (default)
- `google/gemini-2.5-pro`
- `anthropic/claude-sonnet-4-5`
- `anthropic/claude-opus-4-5`
- `meta-llama/llama-3.3-70b-instruct`

## How It Works

### Provider Selection

1. **Automatic Selection**: If no provider is specified, the service tries both in random order
2. **Preferred Provider**: Specify `preferred_provider: "gemini"` or `"openrouter"` to prioritize
3. **Fallback**: If the preferred provider fails, automatically tries the other

### Key Rotation

Keys are shuffled on initialization and used in round-robin fashion:
- Distributes load evenly across all keys
- Prevents hitting rate limits on individual keys
- Automatically excludes rate-limited keys for 1 minute

### Error Handling

- **Rate Limit (429)**: Key is marked as rate-limited and excluded for 1 minute
- **Auth Error (401/403)**: Key is marked as inactive
- **Other Errors**: Tries next key, then falls back to other provider

## Usage in Code

### Basic Chat Completion

```python
from app.ai_provider_service import chat_completion

result = await chat_completion(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7
)

if "error" not in result:
    print(result["choices"][0]["message"]["content"])
```

### Structured Data Extraction

```python
from app.ai_provider_service import extract_structured_data

schema = {
    "name": "string",
    "email": "string",
    "items": [{"name": "string", "qty": "number"}]
}

result = await extract_structured_data(
    text="Quote request from Acme Corp...",
    schema=schema,
    preferred_provider="gemini"
)

if result["success"]:
    data = result["data"]
```

### Using the Service Directly

```python
from app.ai_provider_service import get_ai_service, ProviderType

service = get_ai_service()

# Chat with preferred provider
result = await service.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    preferred_provider=ProviderType.GEMINI
)

# Get stats
stats = service.get_stats()

# Health check
health = await service.health_check()
```

## Monitoring

### View Logs

```bash
# View AI service logs
tail -f logs/mercura.log | grep -i "ai\|provider\|gemini\|openrouter"
```

### Health Dashboard

Access the health check at `/ai/health` to see provider status.

### Statistics Dashboard

Access usage stats at `/ai/stats` to see:
- Total requests and success rate
- Per-key usage statistics
- Error counts and rate limit status

## Troubleshooting

### No API Keys Configured

**Error:** `No AI API keys configured or all providers failed`

**Solution:**
1. Check that `.env` file exists and has API keys
2. Verify keys are valid by testing with `POST /ai/test`
3. Check logs for specific key errors

### Rate Limiting

**Error:** `Rate limit hit for gemini:key_1`

**Solution:**
- This is normal - the service will rotate to another key
- Add more API keys to increase your total rate limit
- Wait 1 minute for rate-limited keys to reset

### Provider Unavailable

**Error:** `gemini status: error`

**Solution:**
1. Check `/ai/health` to see which provider is down
2. The service will automatically fallback to the other provider
3. Check provider status pages:
   - Gemini: https://status.cloud.google.com/
   - OpenRouter: https://status.openrouter.ai/

## Migration from Old Service

The old `DeepSeekService` and direct API calls are now deprecated. The following are automatically routed through `MultiProviderAIService`:

- `get_deepseek_service()` - Returns backward-compatible wrapper
- `extraction_engine` - Uses multi-provider service internally
- `image_extraction_service` - Uses multi-provider service internally

No code changes required for existing functionality.

## Performance Tips

1. **Add Multiple Keys**: More keys = higher effective rate limit
2. **Use Preferred Provider**: Specify provider if you know one is faster for your use case
3. **Enable Fallback**: Keep fallback enabled for reliability
4. **Monitor Stats**: Check `/ai/stats` regularly to identify problematic keys

## Cost Optimization

- **Gemini**: Free tier available (rate limited)
- **OpenRouter**: Many free models available (look for `:free` suffix)
- **Smart Rotation**: The service automatically distributes load to minimize individual key usage