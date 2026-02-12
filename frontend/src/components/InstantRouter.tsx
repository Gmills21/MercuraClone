import React, { createContext, useContext, useCallback, useRef, useEffect, useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

// ============================================
// TYPES
// ============================================

interface CacheEntry {
  path: string;
  element: React.ReactNode;
  scrollPosition: number;
  lastVisited: number;
}

interface InstantRouterContextType {
  preloadRoute: (path: string) => void;
  switchRoute: (path: string) => void;
  getScrollPosition: (path: string) => number;
  saveScrollPosition: (path: string, position: number) => void;
}

// ============================================
// CONTEXT
// ============================================

const InstantRouterContext = createContext<InstantRouterContextType | null>(null);

export const useInstantRouter = () => {
  const context = useContext(InstantRouterContext);
  if (!context) {
    throw new Error('useInstantRouter must be used within InstantRouterProvider');
  }
  return context;
};

// ============================================
// SCROLL RESTORATION
// ============================================

const scrollPositions = new Map<string, number>();

export const saveScrollPosition = (path: string, position: number) => {
  scrollPositions.set(path, position);
};

export const getScrollPosition = (path: string): number => {
  return scrollPositions.get(path) || 0;
};

// ============================================
// INSTANT TAB SWITCHER - GPU OPTIMIZED
// ============================================

interface InstantTabSwitcherProps {
  routes: { path: string; element: React.ReactNode }[];
  currentPath: string;
  maxCacheSize?: number;
  enableAnimation?: boolean;
}

/**
 * InstantTabSwitcher - The heart of flawless navigation
 * 
 * Key optimizations:
 * 1. Uses CSS `display: none` for hidden routes (no motion.div overhead)
 * 2. Only the entering route gets a subtle opacity animation
 * 3. All routes are GPU-accelerated but hidden routes are removed from render tree
 * 4. Scroll position is restored instantly per tab
 */
export const InstantTabSwitcher: React.FC<InstantTabSwitcherProps> = ({
  routes,
  currentPath,
  maxCacheSize = 5,
  enableAnimation = true,
}) => {
  const [cache, setCache] = useState<Map<string, CacheEntry>>(new Map());
  const containerRef = useRef<HTMLDivElement>(null);
  const prevPathRef = useRef(currentPath);
  const routeRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Save scroll position before switching
  useEffect(() => {
    const currentEl = routeRefs.current.get(prevPathRef.current);
    if (currentEl) {
      saveScrollPosition(prevPathRef.current, currentEl.scrollTop);
    }
    prevPathRef.current = currentPath;
  }, [currentPath]);

  // Update cache when route changes - INSTANT, no animation delay
  useEffect(() => {
    setCache(prev => {
      const newCache = new Map(prev);
      const now = Date.now();

      // Add current route to cache if not exists
      const route = routes.find(r => r.path === currentPath);
      if (route && !newCache.has(currentPath)) {
        newCache.set(currentPath, {
          path: currentPath,
          element: route.element,
          scrollPosition: getScrollPosition(currentPath),
          lastVisited: now,
        });
      } else if (route && newCache.has(currentPath)) {
        // Update last visited
        const entry = newCache.get(currentPath)!;
        entry.lastVisited = now;
      }

      // Evict oldest routes if over limit
      if (newCache.size > maxCacheSize) {
        const entries = Array.from(newCache.entries())
          .filter(([path]) => path !== currentPath)
          .sort((a, b) => a[1].lastVisited - b[1].lastVisited);

        const toEvict = entries.slice(0, newCache.size - maxCacheSize);
        toEvict.forEach(([path]) => newCache.delete(path));
      }

      return newCache;
    });
  }, [currentPath, routes, maxCacheSize]);

  // Restore scroll position after route becomes active
  useEffect(() => {
    const scrollPos = getScrollPosition(currentPath);
    const el = routeRefs.current.get(currentPath);
    if (el && scrollPos > 0) {
      // Use requestAnimationFrame for smooth restoration
      requestAnimationFrame(() => {
        el.scrollTop = scrollPos;
      });
    }
  }, [currentPath, cache]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden"
      style={{ contain: 'strict' }}
    >
      {Array.from(cache.entries()).map(([path, entry]) => {
        const isActive = path === currentPath;

        return (
          <RouteTab
            key={path}
            path={path}
            isActive={isActive}
            enableAnimation={enableAnimation}
            containerRef={(el) => {
              if (el) routeRefs.current.set(path, el);
              else routeRefs.current.delete(path);
            }}
          >
            {entry.element}
          </RouteTab>
        );
      })}
    </div>
  );
};

// ============================================
// ROUTE TAB COMPONENT
// ============================================

interface RouteTabProps {
  path: string;
  isActive: boolean;
  children: React.ReactNode;
  enableAnimation: boolean;
  containerRef: (el: HTMLDivElement | null) => void;
}

/**
 * RouteTab - Individual tab wrapper
 * 
 * CRITICAL: Uses display:none for hidden routes instead of AnimatePresence
 * This removes hidden routes from the DOM render tree completely,
 * eliminating GPU memory pressure from motion.div calculations.
 */
const RouteTab: React.FC<RouteTabProps> = ({
  isActive,
  children,
  enableAnimation,
  containerRef,
}) => {
  const innerRef = useRef<HTMLDivElement>(null);

  // Merge refs
  const setRefs = useCallback((el: HTMLDivElement | null) => {
    innerRef.current = el;
    containerRef(el);
  }, [containerRef]);

  // Use CSS display:none for hidden routes - instant, no overhead
  if (!isActive) {
    return (
      <div
        ref={setRefs}
        className="absolute inset-0 hidden"
        aria-hidden="true"
      >
        {children}
      </div>
    );
  }

  // Active route: subtle fade-in animation using GPU-accelerated opacity only
  return (
    <motion.div
      ref={setRefs}
      className="absolute inset-0 w-full h-full overflow-auto custom-scrollbar"
      initial={enableAnimation ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{
        duration: 0.15,
        ease: 'easeOut',
      }}
      style={{
        willChange: 'opacity',
        transform: 'translateZ(0)', // Force GPU layer
        zIndex: 10,
      }}
    >
      {children}
    </motion.div>
  );
};

// ============================================
// PRELOADING
// ============================================

const PRELOAD_QUEUE: string[] = [];
let isPreloading = false;

const processPreloadQueue = async () => {
  if (isPreloading || PRELOAD_QUEUE.length === 0) return;
  isPreloading = true;

  const path = PRELOAD_QUEUE.shift();
  if (path) {
    // Redundant - App.tsx preloader handles core routes
    /*
    try {
      const routeModule = await import(`../pages${path === '/' ? '/LandingPage' : path}.tsx`);
      if (routeModule?.default?.preload) {
        await routeModule.default.preload();
      }
    } catch {
      // Silently fail
    }
    */
  }

  isPreloading = false;
  setTimeout(processPreloadQueue, 50);
};

// ============================================
// INSTANT LINK
// ============================================

interface InstantLinkProps {
  to: string;
  children: React.ReactNode;
  className?: string;
  preloadDelay?: number;
  onClick?: () => void;
}

export const InstantLink: React.FC<InstantLinkProps> = ({
  to,
  children,
  className,
  preloadDelay = 50,
  onClick,
}) => {
  const navigate = useNavigate();
  const preloadTimeoutRef = useRef<number | null>(null);

  const handleMouseEnter = useCallback(() => {
    preloadTimeoutRef.current = window.setTimeout(() => {
      PRELOAD_QUEUE.push(to);
      processPreloadQueue();
    }, preloadDelay);
  }, [to, preloadDelay]);

  const handleMouseLeave = useCallback(() => {
    if (preloadTimeoutRef.current) {
      clearTimeout(preloadTimeoutRef.current);
    }
  }, []);

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    if (onClick) onClick();
    navigate(to);
  }, [navigate, to, onClick]);

  return (
    <a
      href={to}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onTouchStart={() => {
        PRELOAD_QUEUE.push(to);
        processPreloadQueue();
      }}
      className={`press-instant ${className || ''}`}
    >
      {children}
    </a>
  );
};

// ============================================
// ROUTE PRELOADER
// ============================================

export const RoutePreloader: React.FC<{
  routes: string[];
  delay?: number;
}> = ({ routes, delay = 2000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      const scheduleWork = (window as any).requestIdleCallback ||
        ((cb: () => void) => setTimeout(cb, 1));

      scheduleWork(() => {
        routes.forEach((path, index) => {
          setTimeout(() => {
            PRELOAD_QUEUE.push(path);
            processPreloadQueue();
          }, index * 100);
        });
      });
    }, delay);

    return () => clearTimeout(timer);
  }, [routes, delay]);

  return null;
};

// ============================================
// PROVIDER
// ============================================

interface InstantRouterProviderProps {
  children: React.ReactNode;
  maxCachedRoutes?: number;
}

export const InstantRouterProvider: React.FC<InstantRouterProviderProps> = ({
  children,
}) => {
  const preloadRoute = useCallback((path: string) => {
    PRELOAD_QUEUE.push(path);
    processPreloadQueue();
  }, []);

  const switchRoute = useCallback(() => {
    // Instant switch - navigation happens immediately via React Router
  }, []);

  const value = useMemo(() => ({
    preloadRoute,
    switchRoute,
    getScrollPosition,
    saveScrollPosition,
  }), [preloadRoute, switchRoute]);

  return (
    <InstantRouterContext.Provider value={value}>
      {children}
    </InstantRouterContext.Provider>
  );
};

// ============================================
// LEGACY EXPORTS (for backwards compatibility)
// ============================================

/** @deprecated Use InstantTabSwitcher instead */
export const RouteCache = InstantTabSwitcher;

/** @deprecated TabTransition removed - use CSS-only transitions */
export const TabTransition = ({ children }: { children: React.ReactNode }) => <>{children}</>;

export default InstantRouterProvider;
