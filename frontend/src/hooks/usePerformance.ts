import { useEffect, useRef, useCallback, useState } from 'react';

// ============================================
// PERFORMANCE MONITORING HOOK
// ============================================

interface PerformanceMetrics {
  fcp: number | null;
  lcp: number | null;
  fid: number | null;
  cls: number | null;
  ttfb: number | null;
}

export const usePerformanceMonitor = (enabled = true) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fcp: null,
    lcp: null,
    fid: null,
    cls: null,
    ttfb: null,
  });

  useEffect(() => {
    if (!enabled || typeof window === 'undefined') return;

    // First Contentful Paint
    const observeFCP = () => {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const fcp = entries.find(e => e.name === 'first-contentful-paint');
        if (fcp) {
          setMetrics(prev => ({ ...prev, fcp: fcp.startTime }));
        }
      });
      observer.observe({ entryTypes: ['paint'] });
      return () => observer.disconnect();
    };

    // Largest Contentful Paint
    const observeLCP = () => {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        setMetrics(prev => ({ ...prev, lcp: lastEntry.startTime }));
      });
      observer.observe({ entryTypes: ['largest-contentful-paint'] });
      return () => observer.disconnect();
    };

    // First Input Delay
    const observeFID = () => {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const firstEntry = entries[0] as PerformanceEventTiming;
        if (firstEntry) {
          setMetrics(prev => ({ ...prev, fid: firstEntry.processingStart - firstEntry.startTime }));
        }
      });
      observer.observe({ entryTypes: ['first-input'] });
      return () => observer.disconnect();
    };

    // Cumulative Layout Shift
    const observeCLS = () => {
      let clsValue = 0;
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        setMetrics(prev => ({ ...prev, cls: clsValue }));
      });
      observer.observe({ entryTypes: ['layout-shift'] });
      return () => observer.disconnect();
    };

    // Time to First Byte
    const observeTTFB = () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navigation) {
        setMetrics(prev => ({ ...prev, ttfb: navigation.responseStart - navigation.startTime }));
      }
    };

    const cleanupFCP = observeFCP();
    const cleanupLCP = observeLCP();
    const cleanupFID = observeFID();
    const cleanupCLS = observeCLS();
    observeTTFB();

    return () => {
      cleanupFCP();
      cleanupLCP();
      cleanupFID();
      cleanupCLS();
    };
  }, [enabled]);

  return metrics;
};

// ============================================
// INTERSECTION OBSERVER FOR LAZY LOADING
// ============================================

interface UseIntersectionObserverOptions {
  threshold?: number;
  rootMargin?: string;
  triggerOnce?: boolean;
}

export const useIntersectionObserver = (
  options: UseIntersectionObserverOptions = {}
) => {
  const { threshold = 0, rootMargin = '0px', triggerOnce = true } = options;
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasTriggered, setHasTriggered] = useState(false);
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    if (triggerOnce && hasTriggered) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true);
          if (triggerOnce) {
            setHasTriggered(true);
            observer.unobserve(element);
          }
        } else if (!triggerOnce) {
          setIsIntersecting(false);
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [threshold, rootMargin, triggerOnce, hasTriggered]);

  return { ref: elementRef, isIntersecting, hasTriggered };
};

// ============================================
// RAF THROTTLE FOR SMOOTH ANIMATIONS
// ============================================

export const useRafThrottle = <T extends (...args: any[]) => void>(callback: T) => {
  const rafId = useRef<number | null>(null);
  const lastArgs = useRef<Parameters<T> | null>(null);

  const throttled = useCallback((...args: Parameters<T>) => {
    lastArgs.current = args;

    if (rafId.current === null) {
      rafId.current = requestAnimationFrame(() => {
        if (lastArgs.current) {
          callback(...lastArgs.current);
        }
        rafId.current = null;
      });
    }
  }, [callback]);

  useEffect(() => {
    return () => {
      if (rafId.current !== null) {
        cancelAnimationFrame(rafId.current);
      }
    };
  }, []);

  return throttled;
};

// ============================================
// DEBOUNCE FOR SEARCH INPUTS
// ============================================

export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
};

// ============================================
// INSTANT CLICK FEEDBACK
// ============================================

export const useInstantClick = <T extends HTMLElement>(
  onClick: (e: React.MouseEvent<T>) => void
) => {
  const [isPressed, setIsPressed] = useState(false);

  const handlePointerDown = useCallback(() => {
    setIsPressed(true);
  }, []);

  const handlePointerUp = useCallback(() => {
    setIsPressed(false);
  }, []);

  const handleClick = useCallback((e: React.MouseEvent<T>) => {
    setIsPressed(false);
    onClick(e);
  }, [onClick]);

  return {
    isPressed,
    handlers: {
      onPointerDown: handlePointerDown,
      onPointerUp: handlePointerUp,
      onPointerLeave: handlePointerUp,
      onClick: handleClick,
    },
  };
};

// ============================================
// ROUTE PRELOADING ON IDLE
// ============================================

export const useIdlePreload = (preloadFn: () => void, delay = 2000) => {
  const hasPreloaded = useRef(false);

  useEffect(() => {
    if (hasPreloaded.current) return;

    const timer = setTimeout(() => {
      const scheduleWork = (window as any).requestIdleCallback || setTimeout;
      
      scheduleWork(() => {
        if (!hasPreloaded.current) {
          preloadFn();
          hasPreloaded.current = true;
        }
      }, { timeout: 5000 });
    }, delay);

    return () => clearTimeout(timer);
  }, [preloadFn, delay]);
};

// ============================================
// SMOOTH SCROLL
// ============================================

export const useSmoothScroll = () => {
  const scrollTo = useCallback((element: HTMLElement | null, behavior: ScrollBehavior = 'smooth') => {
    if (!element) return;
    
    element.scrollIntoView({
      behavior,
      block: 'start',
    });
  }, []);

  const scrollToTop = useCallback((behavior: ScrollBehavior = 'smooth') => {
    window.scrollTo({ top: 0, behavior });
  }, []);

  return { scrollTo, scrollToTop };
};

// ============================================
// VIEWPORT VISIBILITY
// ============================================

export const useViewportVisibility = () => {
  const [isVisible, setIsVisible] = useState(!document.hidden);

  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  return isVisible;
};

// ============================================
// NETWORK STATUS
// ============================================

export const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [connectionType, setConnectionType] = useState<string>('unknown');

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Get connection info if available
    const connection = (navigator as any).connection;
    if (connection) {
      setConnectionType(connection.effectiveType || 'unknown');
      connection.addEventListener('change', () => {
        setConnectionType(connection.effectiveType || 'unknown');
      });
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { isOnline, connectionType };
};

export default {
  usePerformanceMonitor,
  useIntersectionObserver,
  useRafThrottle,
  useDebounce,
  useInstantClick,
  useIdlePreload,
  useSmoothScroll,
  useViewportVisibility,
  useNetworkStatus,
};
