/**
 * Error Handler Hook for OpenMercura Frontend
 * 
 * Provides consistent error handling across the application:
 * - User-friendly error messages
 * - Automatic retry logic
 * - Toast notifications
 * - Error categorization
 */

import { useState, useCallback } from 'react';
import { toast } from 'sonner';

export interface AppError {
  category: string;
  code: string;
  message: string;
  retryable: boolean;
  retry_after?: number;
  suggested_action?: string;
}

export interface ErrorResponse {
  success: false;
  error: AppError;
}

interface UseErrorHandlerOptions {
  /** Show toast notifications for errors */
  showToast?: boolean;
  /** Default error message if none provided */
  defaultMessage?: string;
  /** Callback when error occurs */
  onError?: (error: AppError) => void;
}

interface UseErrorHandlerReturn {
  /** Current error state */
  error: AppError | null;
  /** Whether an error occurred */
  hasError: boolean;
  /** Handle an error (from API or exception) */
  handleError: (error: unknown) => AppError;
  /** Clear the current error */
  clearError: () => void;
  /** Retry the last operation (if retryable) */
  retry: () => Promise<void>;
  /** Set a retry function to be called */
  setRetryFunction: (fn: () => Promise<void>) => void;
  /** Whether the current error is retryable */
  isRetryable: boolean;
  /** Seconds to wait before retry (if specified) */
  retryAfter: number | null;
}

/**
 * Parse error from various sources (API response, exception, etc.)
 */
function parseError(error: unknown): AppError {
  // Already structured error
  if (error && typeof error === 'object' && 'code' in error && 'message' in error) {
    return error as AppError;
  }

  // API error response
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as { response?: { data?: ErrorResponse } };
    if (axiosError.response?.data?.error) {
      return axiosError.response.data.error;
    }
  }

  // Fetch response
  if (error && typeof error === 'object' && 'json' in error) {
    const fetchError = error as { json: () => Promise<ErrorResponse> };
    // Note: This is async, caller should handle
  }

  // Network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      category: 'network_error',
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server. Please check your internet connection.',
      retryable: true,
      suggested_action: 'Check your internet connection and try again.'
    };
  }

  // Timeout errors
  if (error instanceof Error && error.name === 'AbortError') {
    return {
      category: 'network_error',
      code: 'REQUEST_TIMEOUT',
      message: 'The request took too long to complete. Please try again.',
      retryable: true,
      suggested_action: 'Try again with a smaller request or check your connection.'
    };
  }

  // Default error
  const message = error instanceof Error ? error.message : 'An unexpected error occurred';
  return {
    category: 'internal_error',
    code: 'UNKNOWN_ERROR',
    message,
    retryable: false,
    suggested_action: 'If this persists, please contact support.'
  };
}

/**
 * Hook for handling errors consistently across the application
 */
export function useErrorHandler(options: UseErrorHandlerOptions = {}): UseErrorHandlerReturn {
  const { showToast = true, defaultMessage = 'Something went wrong', onError } = options;
  
  const [error, setError] = useState<AppError | null>(null);
  const [retryFunction, setRetryFunctionState] = useState<(() => Promise<void>) | null>(null);

  const handleError = useCallback((err: unknown): AppError => {
    const parsedError = parseError(err);
    
    // Update state
    setError(parsedError);
    
    // Call callback if provided
    onError?.(parsedError);
    
    // Show toast notification
    if (showToast) {
      const toastOptions: { duration?: number; action?: { label: string; onClick: () => void } } = {};
      
      // Add retry action if error is retryable
      if (parsedError.retryable && retryFunction) {
        toastOptions.action = {
          label: 'Retry',
          onClick: () => retry()
        };
      }
      
      // Show error toast
      toast.error(parsedError.message, {
        description: parsedError.suggested_action,
        ...toastOptions
      });
    }
    
    return parsedError;
  }, [showToast, onError, retryFunction]);

  const clearError = useCallback(() => {
    setError(null);
    setRetryFunctionState(null);
  }, []);

  const setRetryFunction = useCallback((fn: () => Promise<void>) => {
    setRetryFunctionState(() => fn);
  }, []);

  const retry = useCallback(async () => {
    if (!retryFunction) {
      toast.error('No retry function available');
      return;
    }
    
    if (!error?.retryable) {
      toast.error('This error cannot be retried');
      return;
    }
    
    // Wait if retry_after is specified
    if (error.retry_after && error.retry_after > 0) {
      toast.info(`Waiting ${error.retry_after} seconds before retry...`);
      await new Promise(resolve => setTimeout(resolve, error.retry_after! * 1000));
    }
    
    // Clear error and retry
    clearError();
    
    try {
      await retryFunction();
    } catch (err) {
      handleError(err);
    }
  }, [error, retryFunction, clearError, handleError]);

  return {
    error,
    hasError: error !== null,
    handleError,
    clearError,
    retry,
    setRetryFunction,
    isRetryable: error?.retryable ?? false,
    retryAfter: error?.retry_after ?? null
  };
}

/**
 * Higher-order function to wrap async operations with error handling
 */
export function withErrorHandling<T extends (...args: any[]) => Promise<any>>(
  operation: T,
  options: UseErrorHandlerOptions = {}
): {
  execute: T;
  useHandler: () => UseErrorHandlerReturn;
} {
  let globalHandler: UseErrorHandlerReturn | null = null;

  const execute = async (...args: Parameters<T>): Promise<ReturnType<T>> => {
    try {
      return await operation(...args);
    } catch (error) {
      globalHandler?.handleError(error);
      throw error;
    }
  };

  const useHandler = (): UseErrorHandlerReturn => {
    const handler = useErrorHandler(options);
    globalHandler = handler;
    return handler;
  };

  return { execute: execute as T, useHandler };
}

/**
 * Error boundary fallback component
 */
export function ErrorFallback({ 
  error, 
  onRetry, 
  onReset 
}: { 
  error: AppError | null; 
  onRetry?: () => void;
  onReset?: () => void;
}) {
  if (!error) return null;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'network_error':
        return '🔌';
      case 'ai_service_error':
        return '🤖';
      case 'erp_error':
        return '📊';
      case 'email_error':
        return '📧';
      case 'auth_error':
      case 'authorization_error':
        return '🔒';
      case 'validation_error':
        return '⚠️';
      default:
        return '❌';
    }
  };

  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-6">
      <div className="flex items-start gap-4">
        <div className="text-2xl">{getCategoryIcon(error.category)}</div>
        <div className="flex-1">
          <h3 className="font-semibold text-red-900">
            {error.message}
          </h3>
          
          {error.suggested_action && (
            <p className="mt-2 text-sm text-red-700">
              {error.suggested_action}
            </p>
          )}
          
          {error.code && (
            <p className="mt-2 text-xs text-red-500">
              Error code: {error.code}
            </p>
          )}
          
          <div className="mt-4 flex gap-3">
            {error.retryable && onRetry && (
              <button
                onClick={onRetry}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Try Again
              </button>
            )}
            {onReset && (
              <button
                onClick={onReset}
                className="rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-100"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default useErrorHandler;
