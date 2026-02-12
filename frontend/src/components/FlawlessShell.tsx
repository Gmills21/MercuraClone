import React, { useRef, useEffect, useState, useCallback, useMemo, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import clsx from 'clsx';

// ============================================
// FLAWLESS SHELL - Instant Tab Switching
// Steve Jobs-level smoothness
// ============================================

interface FlawlessShellProps {
  cachedRoutes: string[];
  maxCacheSize?: number;
  enableAnimation?: boolean;
  className?: string;
  children: React.ReactNode;
}

interface CachedPage {
  path: string;
  content: React.ReactNode;
  lastVisited: number;
  scrollY: number;
}

/**
 * FlawlessShell - The heart of instant navigation
 * 
 * KEY PRINCIPLES:
 * 1. Pages are kept mounted but hidden via CSS `display:none` — zero remount cost
 * 2. Only the active page is visible — no animation overhead for hidden pages
 * 3. On revisit, the page appears INSTANTLY (0ms) — it's already in the DOM
 * 4. Scroll position is automatically saved/restored per route
 * 5. LRU eviction keeps memory usage bounded
 */
export const FlawlessShell: React.FC<FlawlessShellProps> = ({
  cachedRoutes,
  maxCacheSize = 6,
  enableAnimation = true,
  className,
  children,
}) => {
  const location = useLocation();
  const currentPath = location.pathname;
  const [cache, setCache] = useState<Map<string, CachedPage>>(new Map());
  const scrollPositions = useRef<Map<string, number>>(new Map());
  const prevPathRef = useRef<string>(currentPath);
  const isFirstRender = useRef(true);

  // Determine if the current route should be cached
  const shouldCache = useMemo(() => {
    return cachedRoutes.some(route => currentPath === route || currentPath.startsWith(route + '/'));
  }, [currentPath, cachedRoutes]);

  // Save scroll position before route change
  useEffect(() => {
    const prevPath = prevPathRef.current;
    if (prevPath !== currentPath) {
      // Save scroll position of the page we're leaving
      scrollPositions.current.set(prevPath, window.scrollY || document.documentElement.scrollTop);
      prevPathRef.current = currentPath;
    }
  }, [currentPath]);

  // Update cache when route changes
  useEffect(() => {
    if (!shouldCache) return;

    setCache(prev => {
      const newCache = new Map(prev);
      const now = Date.now();

      // Update or add current route
      newCache.set(currentPath, {
        path: currentPath,
        content: children,
        lastVisited: now,
        scrollY: scrollPositions.current.get(currentPath) || 0,
      });

      // LRU eviction if over limit  
      if (newCache.size > maxCacheSize) {
        const entries = Array.from(newCache.entries())
          .filter(([path]) => path !== currentPath)
          .sort((a, b) => a[1].lastVisited - b[1].lastVisited);

        const toEvict = entries.slice(0, newCache.size - maxCacheSize);
        toEvict.forEach(([path]) => {
          newCache.delete(path);
          scrollPositions.current.delete(path);
        });
      }

      return newCache;
    });
  }, [currentPath, shouldCache, children, maxCacheSize]);

  // Restore scroll position when route becomes active
  useEffect(() => {
    if (shouldCache) {
      const savedScroll = scrollPositions.current.get(currentPath) || 0;
      // Use rAF for smooth restoration after paint
      requestAnimationFrame(() => {
        window.scrollTo(0, savedScroll);
      });
    }
  }, [currentPath, shouldCache]);

  // Track first render
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
    }
  }, []);

  // If this route isn't cacheable, just render children directly
  if (!shouldCache) {
    return (
      <div className={clsx('flawless-shell', className)}>
        <FlawlessPage enableAnimation={enableAnimation} isFirstRender={isFirstRender.current}>
          {children}
        </FlawlessPage>
      </div>
    );
  }

  // Render all cached pages — active one is visible, others are display:none
  return (
    <div className={clsx('flawless-shell', className)}>
      {Array.from(cache.entries()).map(([path, entry]) => {
        const isActive = path === currentPath;

        return (
          <div
            key={path}
            data-route={path}
            data-active={isActive}
            className={clsx(
              isActive ? 'flawless-page-active' : 'flawless-page-cached'
            )}
            style={{
              display: isActive ? 'block' : 'none',
              // Prevent layout thrash when showing
              contain: isActive ? undefined : 'strict',
            }}
            aria-hidden={!isActive}
          >
            {isActive && enableAnimation && !isFirstRender.current ? (
              <div className="flawless-enter" style={{ animationDuration: '150ms' }}>
                {entry.content}
              </div>
            ) : (
              entry.content
            )}
          </div>
        );
      })}
    </div>
  );
};

/**
 * FlawlessPage - Simple wrapper for page content with optional entrance animation
 * Uses pure CSS animations for maximum performance (no framer-motion overhead)
 */
interface FlawlessPageProps {
  children: React.ReactNode;
  className?: string;
  enableAnimation?: boolean;
  isFirstRender?: boolean;
}

export const FlawlessPage: React.FC<FlawlessPageProps> = ({
  children,
  className,
  enableAnimation = true,
  isFirstRender = false,
}) => {
  return (
    <div
      className={clsx(
        enableAnimation && !isFirstRender && 'flawless-enter',
        className
      )}
      style={{
        // GPU-accelerate the container
        transform: 'translateZ(0)',
        willChange: 'auto',
      }}
    >
      {children}
    </div>
  );
};

// ============================================
// INSTANT BUTTON
// Tactile feedback with no delay — pure CSS
// ============================================

interface InstantButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const InstantButton: React.FC<InstantButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className,
  disabled,
  ...props
}) => {
  const variants = {
    primary: 'bg-slate-900 text-white hover:bg-slate-800 active:bg-slate-950',
    secondary: 'bg-white text-slate-900 border border-slate-200 hover:bg-slate-50 active:bg-slate-100',
    ghost: 'bg-transparent text-slate-700 hover:bg-slate-100 active:bg-slate-200',
    danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  return (
    <button
      disabled={disabled || isLoading}
      className={clsx(
        'relative rounded-xl font-medium press-instant',
        'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        'transform-gpu select-none',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      <span className={clsx('relative z-10 flex items-center justify-center gap-2', isLoading && 'opacity-0')}>
        {children}
      </span>
      {isLoading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <LoadingSpinner size="sm" />
        </span>
      )}
    </button>
  );
};

// Loading spinner — pure CSS, no framer-motion
const LoadingSpinner: React.FC<{ size?: 'xs' | 'sm' | 'md' | 'lg' }> = ({
  size = 'md',
}) => {
  const sizes = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <div className={clsx(sizes[size], 'animate-spin')} style={{ animationDuration: '0.8s' }}>
      <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray="31.416"
          strokeDashoffset="10"
          className="opacity-25"
        />
        <path
          d="M12 2a10 10 0 0 1 10 10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          className="opacity-75"
        />
      </svg>
    </div>
  );
};

// ============================================
// INSTANT PRESSABLE
// For any clickable element needing tactile feedback — pure CSS
// ============================================

interface InstantPressableProps {
  children: React.ReactNode;
  onPress?: () => void;
  className?: string;
  disabled?: boolean;
}

export const InstantPressable: React.FC<InstantPressableProps> = ({
  children,
  onPress,
  className,
  disabled,
}) => {
  return (
    <div
      onClick={disabled ? undefined : onPress}
      className={clsx(
        'press-instant select-none',
        disabled && 'opacity-50 cursor-not-allowed',
        !disabled && 'cursor-pointer',
        className
      )}
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => {
        if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onPress?.();
        }
      }}
    >
      {children}
    </div>
  );
};

export default FlawlessShell;
