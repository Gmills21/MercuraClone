import React, { useCallback, useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

// ============================================
// INSTANT INTERACTION FEEDBACK
// Every click/button press feels immediate
// ============================================

interface RippleEffectProps {
  color?: string;
  duration?: number;
}

// Ripple effect on click - instant visual feedback
export const useRipple = ({ color = 'rgba(255,255,255,0.3)', duration = 400 }: RippleEffectProps = {}) => {
  const [ripples, setRipples] = useState<Array<{ id: number; x: number; y: number }>>([]);
  const idCounter = useRef(0);

  const createRipple = useCallback((event: React.MouseEvent<HTMLElement>) => {
    const element = event.currentTarget;
    const rect = element.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const id = idCounter.current++;

    setRipples(prev => [...prev, { id, x, y }]);

    setTimeout(() => {
      setRipples(prev => prev.filter(r => r.id !== id));
    }, duration);
  }, [duration]);

  const RippleContainer = useCallback(({ className }: { className?: string }) => (
    <span className={clsx('absolute inset-0 overflow-hidden rounded-inherit pointer-events-none', className)}>
      <AnimatePresence>
        {ripples.map(ripple => (
          <motion.span
            key={ripple.id}
            initial={{ scale: 0, opacity: 0.5 }}
            animate={{ scale: 4, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: duration / 1000, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              left: ripple.x,
              top: ripple.y,
              width: 10,
              height: 10,
              marginLeft: -5,
              marginTop: -5,
              borderRadius: '50%',
              backgroundColor: color,
              transform: 'translateZ(0)',
            }}
          />
        ))}
      </AnimatePresence>
    </span>
  ), [ripples, color, duration]);

  return { createRipple, RippleContainer };
};

// Instant button with tactile feedback
interface InstantButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  rippleColor?: string;
  instantScale?: boolean;
}

export const InstantButton: React.FC<InstantButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  rippleColor,
  instantScale = true,
  className,
  onClick,
  disabled,
  ...props
}) => {
  const { createRipple, RippleContainer } = useRipple({ color: rippleColor });
  const [isPressed, setIsPressed] = useState(false);

  const handleClick = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    createRipple(e);
    onClick?.(e);
  }, [createRipple, onClick]);

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
    <motion.button
      onClick={handleClick}
      onPointerDown={() => setIsPressed(true)}
      onPointerUp={() => setIsPressed(false)}
      onPointerLeave={() => setIsPressed(false)}
      disabled={disabled || isLoading}
      whileTap={instantScale ? { scale: 0.97 } : undefined}
      animate={{
        scale: isPressed ? 0.97 : 1,
      }}
      transition={{ duration: 0.08, ease: 'easeOut' }}
      className={clsx(
        'relative overflow-hidden rounded-xl font-medium transition-colors duration-150',
        'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
      style={{ transform: 'translateZ(0)' }}
      {...props}
    >
      <RippleContainer />
      <span className={clsx('relative z-10 flex items-center justify-center gap-2', isLoading && 'opacity-0')}>
        {children}
      </span>
      {isLoading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <LoadingSpinner size="sm" />
        </span>
      )}
    </motion.button>
  );
};

// Loading spinner with smooth animation
export const LoadingSpinner: React.FC<{ size?: 'xs' | 'sm' | 'md' | 'lg'; className?: string }> = ({
  size = 'md',
  className,
}) => {
  const sizes = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      className={clsx(sizes[size], className)}
    >
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
    </motion.div>
  );
};

// Touch feedback for mobile
export const TouchFeedback: React.FC<{
  children: React.ReactElement;
  scale?: number;
  opacity?: number;
}> = ({ children, scale = 0.98, opacity = 0.8 }) => {
  return (
    <motion.div
      whileTap={{ scale, opacity }}
      transition={{ duration: 0.1 }}
      style={{ transform: 'translateZ(0)' }}
    >
      {children}
    </motion.div>
  );
};

// Skeleton that morphs into content
interface SkeletonMorphProps {
  isLoading: boolean;
  skeleton: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const SkeletonMorph: React.FC<SkeletonMorphProps> = ({
  isLoading,
  skeleton,
  children,
  className,
}) => {
  return (
    <div className={clsx('relative', className)}>
      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="skeleton"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {skeleton}
          </motion.div>
        ) : (
          <motion.div
            key="content"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Staggered list reveal
interface StaggerListProps {
  children: React.ReactNode[];
  staggerDelay?: number;
  className?: string;
}

export const StaggerList: React.FC<StaggerListProps> = ({
  children,
  staggerDelay = 0.03,
  className,
}) => {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
      className={className}
    >
      {React.Children.map(children, (child, index) => (
        <motion.div
          key={index}
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: {
              opacity: 1,
              y: 0,
              transition: {
                duration: 0.2,
                ease: [0.25, 0.1, 0.25, 1],
              },
            },
          }}
          style={{ transform: 'translateZ(0)' }}
        >
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
};

// Hover lift card effect
interface HoverCardProps {
  children: React.ReactNode;
  className?: string;
  lift?: number;
}

export const HoverCard: React.FC<HoverCardProps> = ({ children, className, lift = 4 }) => {
  return (
    <motion.div
      whileHover={{ 
        y: -lift, 
        boxShadow: '0 12px 40px rgba(0,0,0,0.08)',
      }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className={clsx('transition-shadow duration-200', className)}
      style={{ transform: 'translateZ(0)' }}
    >
      {children}
    </motion.div>
  );
};

// Press effect wrapper
interface PressableProps {
  children: React.ReactNode;
  onPress?: () => void;
  className?: string;
  disabled?: boolean;
}

export const Pressable: React.FC<PressableProps> = ({ children, onPress, className, disabled }) => {
  const [isPressed, setIsPressed] = useState(false);

  return (
    <motion.div
      onClick={disabled ? undefined : onPress}
      onPointerDown={() => !disabled && setIsPressed(true)}
      onPointerUp={() => setIsPressed(false)}
      onPointerLeave={() => setIsPressed(false)}
      animate={{ scale: isPressed ? 0.98 : 1 }}
      transition={{ duration: 0.08 }}
      className={clsx(disabled && 'opacity-50 cursor-not-allowed', className)}
      style={{ cursor: disabled ? 'not-allowed' : 'pointer', transform: 'translateZ(0)' }}
    >
      {children}
    </motion.div>
  );
};

// Optimized image with blur-up loading
interface OptimizedImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  placeholderColor?: string;
  aspectRatio?: string;
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  placeholderColor = '#f1f5f9',
  aspectRatio,
  className,
  style,
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);

  return (
    <div 
      className={clsx('relative overflow-hidden', className)}
      style={{ aspectRatio, ...style }}
    >
      {!isLoaded && (
        <div 
          className="absolute inset-0 animate-pulse"
          style={{ backgroundColor: placeholderColor }}
        />
      )}
      <motion.img
        src={src}
        alt={alt}
        onLoad={() => setIsLoaded(true)}
        initial={{ opacity: 0 }}
        animate={{ opacity: isLoaded ? 1 : 0 }}
        transition={{ duration: 0.3 }}
        className="w-full h-full object-cover"
        style={{ transform: 'translateZ(0)' }}
        {...props}
      />
    </div>
  );
};

export default {
  InstantButton,
  LoadingSpinner,
  TouchFeedback,
  SkeletonMorph,
  StaggerList,
  HoverCard,
  Pressable,
  OptimizedImage,
  useRipple,
};
