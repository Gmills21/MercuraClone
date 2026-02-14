# Error Handling Architecture

## Overview

OpenMercura uses a comprehensive error handling framework designed to:

1. **Never expose stack traces** to users
2. **Provide actionable error messages** that guide users to resolution
3. **Implement automatic retry logic** with exponential backoff
4. **Use circuit breakers** to prevent cascading failures
5. **Support graceful degradation** when services are unavailable

## Core Components

### 1. Error Types (`app/errors.py`)

Centralized error definitions with user-friendly messaging:

```python
from app.errors import AppError, ErrorCategory, ai_service_unavailable

# Example: Creating a user-friendly error
error = AppError(
    category=ErrorCategory.AI_SERVICE_ERROR,
    code="AI_SERVICE_UNAVAILABLE",
    message="AI service is temporarily unavailable. We're working on restoring it.",
    severity=ErrorSeverity.ERROR,
    http_status=503,
    retryable=True,
    retry_after_seconds=30,
    suggested_action="Please try again in a moment."
)
```

### 2. Resilience Utilities (`app/utils/resilience.py`)

Implements industry-standard patterns:

#### Retry with Exponential Backoff

```python
from app.utils.resilience import with_retry, RetryConfig

config = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    jitter=True  # Add randomness to prevent thundering herd
)

result = await with_retry(fetch_data, config=config)
```

#### Circuit Breaker

```python
from app.utils.resilience import CircuitBreaker

breaker = CircuitBreaker("quickbooks")

@breaker.protect
async def call_quickbooks_api():
    # If this fails 5 times, circuit opens for 60 seconds
    return await api_call()
```

#### Timeout Handling

```python
from app.utils.resilience import with_timeout

result = await with_timeout(
    slow_operation(),
    timeout_seconds=30.0,
    timeout_message="Operation timed out"
)
```

### 3. Global Error Handler (`app/middleware/error_handler.py`)

Catches all unhandled exceptions and converts them to user-friendly responses:

- Categorizes errors automatically
- Logs with appropriate severity
- Never leaks stack traces to clients
- Returns structured JSON with `error`, `retryable`, `suggested_action`

### 4. Service-Level Error Handling

Each external service implements specific error handling:

#### AI Provider Service
- Automatic failover between Gemini and OpenRouter
- Circuit breaker per provider
- Rate limit tracking per API key
- Graceful degradation when all providers fail

#### QuickBooks Integration
- Token refresh on 401 errors
- Circuit breaker for API failures
- Local data preservation when sync fails
- User-friendly messages for auth issues

#### Email Service
- Specific error handling for SMTP issues
- Retry logic for transient network failures
- Clear guidance for authentication errors
- Differentiation between user errors and system errors

## Error Response Format

All errors return a consistent JSON structure:

```json
{
  "success": false,
  "error": {
    "category": "ai_service_error",
    "code": "AI_SERVICE_UNAVAILABLE",
    "message": "AI service is temporarily unavailable...",
    "retryable": true,
    "retry_after": 30,
    "suggested_action": "Please try again in a moment."
  }
}
```

## Error Categories

| Category | Description | Example |
|----------|-------------|---------|
| `ai_service_error` | AI provider issues | Rate limited, model unavailable |
| `erp_error` | ERP integration issues | QuickBooks connection failed |
| `email_error` | SMTP/email issues | Auth failed, timeout |
| `database_error` | Database issues | Constraint violation, timeout |
| `network_error` | Network connectivity | Timeout, DNS failure |
| `validation_error` | User input issues | Missing field, invalid format |
| `auth_error` | Authentication | Token expired, invalid credentials |
| `authorization_error` | Permission | Access denied to resource |
| `not_found` | Missing resource | Quote doesn't exist |
| `rate_limit` | Too many requests | API rate limit exceeded |
| `insufficient_quota` | Plan limits | Extraction limit reached |
| `internal_error` | Unexpected | Uncategorized errors |

## Severity Levels

| Level | Use Case | Alerting |
|-------|----------|----------|
| `DEBUG` | Expected, routine | None |
| `INFO` | Expected, notable | None |
| `WARNING` | Unexpected, handled | Log only |
| `ERROR` | Problem, user affected | Log + monitor |
| `CRITICAL` | System-wide impact | Log + page on-call |

## Frontend Error Handling

Use the `useErrorHandler` hook for consistent error handling:

```typescript
import { useErrorHandler } from '@/hooks/useErrorHandler';

function MyComponent() {
  const { handleError, retry } = useErrorHandler();
  
  const fetchData = async () => {
    try {
      const response = await api.get('/data');
      return response.data;
    } catch (error) {
      // Automatically shows toast with user-friendly message
      handleError(error);
    }
  };
  
  // Use retry function for retryable errors
  return (
    <ErrorBoundary 
      error={error}
      onRetry={retry}
      retryable={error?.retryable}
    />
  );
}
```

## Best Practices

### For Backend Developers

1. **Always use structured errors** - Never raise raw exceptions that leak to users
2. **Set appropriate severity** - Don't log user errors as ERROR
3. **Provide suggested actions** - Guide users toward resolution
4. **Use retry logic** - Transient failures should auto-retry
5. **Implement circuit breakers** - Prevent cascading failures
6. **Log context** - Include request ID, user ID for debugging

### For Frontend Developers

1. **Check `retryable`** - Show retry button only when appropriate
2. **Display `suggested_action`** - Help users fix the issue
3. **Respect `retry_after`** - Don't hammer retry immediately
4. **Handle network errors** - Show offline indicator
5. **Use error boundaries** - Prevent app crashes

## Testing Error Scenarios

### Simulate AI Failure
```bash
# Temporarily break AI config
export GEMINI_API_KEY=invalid
export OPENROUTER_API_KEY_1=invalid
```

### Simulate Network Issues
```bash
# Use toxiproxy or similar to add latency/drops
toxiproxy-cli add -l localhost:8080 -u generativelanguage.googleapis.com:443 gemini
```

### Test Circuit Breaker
```python
# Force multiple failures to open circuit
for i in range(5):
    await ai_service.chat_completion(messages)  # With invalid key
# Circuit should now be open
```

## Monitoring

Key metrics to track:

- **Error rate by category** - Spot service degradation
- **Retry success rate** - Tune retry parameters
- **Circuit breaker state changes** - Detect persistent issues
- **Time to recovery** - Measure resilience
- **User retry rate** - Validate error messages are helpful

## Future Enhancements

- [ ] Error aggregation service (Sentry integration)
- [ ] Automatic alert routing based on severity
- [ ] Error trend analysis and prediction
- [ ] User-facing error reporting ("Report this issue")
- [ ] Retry queue for failed background jobs
