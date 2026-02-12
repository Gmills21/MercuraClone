import { motion } from 'framer-motion';
import React, { Suspense } from 'react';

// ============================================
// GPU-OPTIMIZED PAGE TRANSITIONS
// ============================================

/**
 * PageTransition - Ultra-light fade animation
 * 
 * Uses ONLY opacity (GPU-composited property)
 * No transform animations that cause layout/paint
 */
export const PageTransition = ({ children }: { children: React.ReactNode }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{
        duration: 0.15,
        ease: 'easeOut',
      }}
      style={{ 
        willChange: 'opacity',
        // Use contain to isolate this layer
        contain: 'layout style paint',
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * RouteTransition - Even lighter for route changes
 * Instant feel with barely perceptible fade
 */
export const RouteTransition = ({ children }: { children: React.ReactNode }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{
        duration: 0.12,
        ease: 'linear',
      }}
      style={{ 
        willChange: 'opacity',
        height: '100%',
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * TabTransition - Instant switch with micro-fade
 * Used when switching between cached tabs
 */
export const TabTransition = ({ 
  children, 
  isActive 
}: { 
  children: React.ReactNode; 
  isActive: boolean;
}) => {
  if (!isActive) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{
        duration: 0.1,
        ease: 'easeOut',
      }}
      style={{ 
        willChange: 'opacity',
        transform: 'translateZ(0)', // GPU layer
      }}
    >
      {children}
    </motion.div>
  );
};

// ============================================
// STAGGER ANIMATIONS (OPTIMIZED)
// ============================================

export const StaggerContainer = ({
  children,
  staggerDelay = 0.03,
}: {
  children: React.ReactNode;
  staggerDelay?: number;
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
    >
      {children}
    </motion.div>
  );
};

export const StaggerItem = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            duration: 0.2,
            ease: 'easeOut',
          },
        },
      }}
      className={className}
      style={{ willChange: 'opacity' }}
    >
      {children}
    </motion.div>
  );
};

// ============================================
// SIMPLE UTILITY ANIMATIONS
// ============================================

export const FadeIn = ({
  children,
  delay = 0,
  duration = 0.2,
  className,
}: {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration, delay, ease: 'easeOut' }}
      className={className}
      style={{ willChange: 'opacity' }}
    >
      {children}
    </motion.div>
  );
};

// Hover effects using CSS transforms (GPU-friendly)
export const HoverScale = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <div className={`transition-transform duration-150 active:scale-[0.98] hover:scale-[1.02] ${className || ''}`}>
      {children}
    </div>
  );
};

// Use CSS for height animations - better performance
export const SmoothHeight = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <div 
      className={`grid transition-all duration-200 ease-out ${className || ''}`}
      style={{ 
        gridTemplateRows: '1fr',
      }}
    >
      <div className="overflow-hidden">
        {children}
      </div>
    </div>
  );
};

// Slide in using opacity only (GPU-optimized)
export const SlideIn = ({
  children,
  className,
}: {
  children: React.ReactNode;
  direction?: 'left' | 'right' | 'up' | 'down';
  className?: string;
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      className={className}
      style={{ willChange: 'transform, opacity' }}
    >
      {children}
    </motion.div>
  );
};

// ============================================
// SUSPENSE WRAPPER
// ============================================

export const SuspenseWithSkeleton = ({
  children,
  skeleton: SkeletonComponent,
}: {
  children: React.ReactNode;
  skeleton: React.ComponentType;
}) => {
  return (
    <Suspense
      fallback={
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.1 }}
        >
          <SkeletonComponent />
        </motion.div>
      }
    >
      {children}
    </Suspense>
  );
};

// ============================================
// DEFAULT EXPORT
// ============================================

export default {
  PageTransition,
  RouteTransition,
  TabTransition,
  StaggerContainer,
  StaggerItem,
  FadeIn,
  HoverScale,
  SmoothHeight,
  SlideIn,
  SuspenseWithSkeleton,
};
