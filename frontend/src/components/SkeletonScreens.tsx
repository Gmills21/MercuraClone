import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

// ============================================
// ENHANCED SKELETON SCREENS
// Smooth morphing from skeleton to content
// ============================================

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  circle?: boolean;
  pulse?: boolean;
  shimmer?: boolean;
}

// Base skeleton element
export const Skeleton: React.FC<SkeletonProps> = ({
  className,
  width,
  height,
  circle = false,
  pulse = false,
  shimmer = true,
}) => {
  return (
    <div
      className={clsx(
        'bg-slate-200',
        circle && 'rounded-full',
        !circle && 'rounded-lg',
        shimmer && 'animate-shimmer',
        pulse && 'animate-pulse',
        className
      )}
      style={{
        width,
        height,
        willChange: 'transform',
        transform: 'translateZ(0)',
      }}
    />
  );
};

// Dashboard skeleton - matches TodayView layout
export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton width={200} height={32} />
        <Skeleton width={300} height={20} />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="p-6 bg-white rounded-2xl border border-slate-200/60 space-y-4">
            <div className="flex items-center justify-between">
              <Skeleton width={40} height={40} circle />
              <Skeleton width={60} height={24} />
            </div>
            <Skeleton width={120} height={28} />
            <Skeleton width={80} height={16} />
          </div>
        ))}
      </div>

      {/* Main content area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-4">
          <Skeleton width={150} height={24} />
          <div className="bg-white rounded-2xl border border-slate-200/60 p-6 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-4 py-3">
                <Skeleton width={48} height={48} circle />
                <div className="flex-1 space-y-2">
                  <Skeleton width="60%" height={18} />
                  <Skeleton width="40%" height={14} />
                </div>
                <Skeleton width={80} height={32} />
              </div>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          <Skeleton width={150} height={24} />
          <div className="bg-white rounded-2xl border border-slate-200/60 p-6 space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton width="80%" height={16} />
                <Skeleton width="60%" height={12} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Table skeleton - matches Quotes/Customers/Emails pages
interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
}

export const TableSkeleton: React.FC<TableSkeletonProps> = ({
  rows = 8,
  columns = 5,
  showHeader = true,
}) => {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="space-y-2">
          <Skeleton width={180} height={28} />
          <Skeleton width={250} height={16} />
        </div>
        <Skeleton width={120} height={40} />
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200/60 overflow-hidden">
        {showHeader && (
          <div className="grid gap-4 p-4 border-b border-slate-200/60 bg-slate-50/50">
            <div className="flex gap-4">
              {[...Array(columns)].map((_, i) => (
                <Skeleton key={i} width={`${80 + Math.random() * 40}px`} height={16} />
              ))}
            </div>
          </div>
        )}
        <div className="divide-y divide-slate-100">
          {[...Array(rows)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 p-4">
              <Skeleton width={40} height={40} circle />
              <div className="flex-1 grid grid-cols-5 gap-4">
                <Skeleton width="80%" height={16} />
                <Skeleton width="60%" height={16} />
                <Skeleton width="70%" height={16} />
                <Skeleton width={80} height={24} className="rounded-full" />
                <Skeleton width={100} height={16} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4">
        <Skeleton width={120} height={16} />
        <div className="flex gap-2">
          <Skeleton width={36} height={36} />
          <Skeleton width={36} height={36} />
          <Skeleton width={36} height={36} />
        </div>
      </div>
    </div>
  );
};

// Card grid skeleton - matches Products page
interface CardGridSkeletonProps {
  cards?: number;
}

export const CardGridSkeleton: React.FC<CardGridSkeletonProps> = ({ cards = 6 }) => {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="space-y-2">
          <Skeleton width={180} height={28} />
          <Skeleton width={250} height={16} />
        </div>
        <Skeleton width={120} height={40} />
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <Skeleton width={200} height={40} />
        <Skeleton width={150} height={40} />
        <Skeleton width={100} height={40} />
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(cards)].map((_, i) => (
          <div key={i} className="bg-white rounded-2xl border border-slate-200/60 p-5 space-y-4">
            <div className="flex items-start justify-between">
              <Skeleton width={60} height={24} className="rounded-full" />
              <Skeleton width={24} height={24} circle />
            </div>
            <Skeleton width="80%" height={20} />
            <Skeleton width="60%" height={16} />
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <Skeleton width={80} height={16} />
              <Skeleton width={100} height={32} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Form skeleton - matches SmartQuote/CreateQuote
export const FormSkeleton: React.FC = () => {
  return (
    <div className="p-8 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <Skeleton width={250} height={32} />
        <div className="mt-2">
          <Skeleton width={400} height={16} />
        </div>
      </div>

      {/* Form sections */}
      <div className="space-y-8">
        {/* Section 1 */}
        <div className="bg-white rounded-2xl border border-slate-200/60 p-6 space-y-6">
          <Skeleton width={150} height={20} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Skeleton width={80} height={14} />
              <Skeleton width="100%" height={44} />
            </div>
            <div className="space-y-2">
              <Skeleton width={80} height={14} />
              <Skeleton width="100%" height={44} />
            </div>
          </div>
          <div className="space-y-2">
            <Skeleton width={80} height={14} />
            <Skeleton width="100%" height={120} />
          </div>
        </div>

        {/* Section 2 */}
        <div className="bg-white rounded-2xl border border-slate-200/60 p-6 space-y-6">
          <Skeleton width={180} height={20} />
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex gap-4 p-4 bg-slate-50 rounded-xl">
                <Skeleton width={60} height={60} />
                <div className="flex-1 space-y-2">
                  <Skeleton width="40%" height={16} />
                  <Skeleton width="30%" height={14} />
                </div>
                <Skeleton width={100} height={36} />
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Skeleton width={100} height={44} />
          <Skeleton width={140} height={44} />
        </div>
      </div>
    </div>
  );
};

// Detail view skeleton - matches QuoteReview
export const DetailSkeleton: React.FC = () => {
  return (
    <div className="p-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-6">
        <Skeleton width={60} height={16} />
        <Skeleton width={16} height={16} />
        <Skeleton width={80} height={16} />
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="space-y-2">
          <Skeleton width={300} height={28} />
          <div className="flex items-center gap-3">
            <Skeleton width={80} height={24} className="rounded-full" />
            <Skeleton width={120} height={16} />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton width={100} height={40} />
          <Skeleton width={120} height={40} />
        </div>
      </div>

      {/* Two column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/60 p-6 space-y-6">
            <Skeleton width={150} height={20} />
            <div className="space-y-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex justify-between py-3 border-b border-slate-100">
                  <Skeleton width={120} height={16} />
                  <Skeleton width={200} height={16} />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/60 p-6 space-y-4">
            <Skeleton width={150} height={20} />
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-slate-50 rounded-xl">
                <Skeleton width={48} height={48} circle />
                <div className="flex-1 space-y-2">
                  <Skeleton width="50%" height={16} />
                  <Skeleton width="30%" height={14} />
                </div>
                <Skeleton width={80} height={16} />
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/60 p-6 space-y-4">
            <Skeleton width={100} height={18} />
            <Skeleton width="100%" height={60} />
            <div className="pt-4 border-t border-slate-100 space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex justify-between">
                  <Skeleton width={80} height={14} />
                  <Skeleton width={60} height={14} />
                </div>
              ))}
              <div className="pt-3 border-t border-slate-100">
                <div className="flex justify-between">
                  <Skeleton width={60} height={18} />
                  <Skeleton width={80} height={18} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Page skeleton selector based on type
interface PageSkeletonProps {
  type: 'dashboard' | 'table' | 'cards' | 'form' | 'detail';
  rows?: number;
  columns?: number;
  cards?: number;
}

export const PageSkeleton: React.FC<PageSkeletonProps> = ({ type, ...props }) => {
  switch (type) {
    case 'dashboard':
      return <DashboardSkeleton />;
    case 'table':
      return <TableSkeleton {...props} />;
    case 'cards':
      return <CardGridSkeleton {...(props as { cards?: number })} />;
    case 'form':
      return <FormSkeleton />;
    case 'detail':
      return <DetailSkeleton />;
    default:
      return <DashboardSkeleton />;
  }
};

// Morphing skeleton wrapper
interface MorphingSkeletonProps {
  isLoading: boolean;
  type: 'dashboard' | 'table' | 'cards' | 'form' | 'detail';
  children: React.ReactNode;
  className?: string;
}

export const MorphingSkeleton: React.FC<MorphingSkeletonProps> = ({
  isLoading,
  type,
  children,
  className,
}) => {
  return (
    <div className={clsx('relative', className)}>
      <motion.div
        initial={false}
        animate={{
          opacity: isLoading ? 1 : 0,
          scale: isLoading ? 1 : 0.98,
        }}
        transition={{ duration: 0.2 }}
        className={clsx('absolute inset-0', !isLoading && 'pointer-events-none')}
        style={{ willChange: 'opacity, transform' }}
      >
        <PageSkeleton type={type} />
      </motion.div>
      <motion.div
        initial={false}
        animate={{
          opacity: isLoading ? 0 : 1,
          y: isLoading ? 8 : 0,
        }}
        transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
        className={clsx(isLoading && 'pointer-events-none')}
        style={{ willChange: 'opacity, transform' }}
      >
        {children}
      </motion.div>
    </div>
  );
};

// ============================================
// BACKWARDS-COMPATIBLE ALIASES
// ============================================

// Alias for pages that import SkeletonTable
export const SkeletonTable: React.FC<{ rows?: number; columns?: number }> = ({ rows = 6, columns = 5 }) => (
  <TableSkeleton rows={rows} columns={columns} />
);

// Alias for pages that import SkeletonText
export const SkeletonText: React.FC<{ className?: string; lines?: number; lineHeight?: string }> = ({
  className,
  lines = 1,
  lineHeight,
}) => (
  <div className={clsx('space-y-2', className)}>
    {[...Array(lines)].map((_, i) => (
      <Skeleton key={i} width="100%" height={lineHeight ? parseInt(lineHeight.replace('h-', '')) * 4 : 16} />
    ))}
  </div>
);

// TodayView skeleton - matches the TodayView layout
export const TodayViewSkeleton: React.FC = () => (
  <div className="space-y-10 p-8">
    {/* Header */}
    <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div className="space-y-3">
        <Skeleton width={200} height={18} />
        <Skeleton width={350} height={40} />
      </div>
      <Skeleton width={140} height={48} className="rounded-xl" />
    </div>

    {/* Bento Grid */}
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
      {/* Pipeline Value - large card */}
      <div className="col-span-2 bg-white rounded-2xl p-8 border border-slate-200/60 space-y-4">
        <div className="flex items-center gap-2">
          <Skeleton width={32} height={32} circle />
          <Skeleton width={200} height={16} />
        </div>
        <Skeleton width={250} height={48} />
        <div className="flex gap-4">
          <Skeleton width={150} height={28} className="rounded-full" />
          <Skeleton width={180} height={16} />
        </div>
      </div>

      {/* Small stat cards */}
      {[...Array(2)].map((_, i) => (
        <div key={i} className="bg-white rounded-2xl p-6 border border-slate-200/60 space-y-4">
          <div className="flex justify-between items-start">
            <Skeleton width={40} height={40} className="rounded-xl" />
            <Skeleton width={12} height={12} circle />
          </div>
          <Skeleton width={60} height={36} />
          <Skeleton width={100} height={16} />
        </div>
      ))}

      {/* Priorities card */}
      <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/60 space-y-4 row-span-2">
        <div className="flex items-center gap-2">
          <Skeleton width={18} height={18} />
          <Skeleton width={100} height={18} />
        </div>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="p-3 bg-white rounded-xl space-y-2">
            <div className="flex justify-between">
              <Skeleton width={50} height={18} className="rounded-full" />
              <Skeleton width={60} height={12} />
            </div>
            <Skeleton width="80%" height={14} />
            <Skeleton width="60%" height={12} />
          </div>
        ))}
        <Skeleton width="100%" height={44} className="rounded-xl mt-4" />
      </div>

      {/* Recent activity table */}
      <div className="col-span-3 bg-white rounded-2xl border border-slate-200/60 overflow-hidden row-span-2">
        <div className="px-8 py-6 flex items-center justify-between border-b border-slate-100">
          <Skeleton width={150} height={20} />
          <Skeleton width={120} height={16} />
        </div>
        <div className="divide-y divide-slate-50">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 py-4 px-8">
              <div className="flex-1 space-y-1">
                <Skeleton width="40%" height={16} />
                <Skeleton width="25%" height={12} />
              </div>
              <Skeleton width={80} height={24} className="rounded-full" />
              <Skeleton width={80} height={16} />
              <Skeleton width={60} height={16} />
            </div>
          ))}
        </div>
      </div>

      {/* Small insight cards */}
      <div className="bg-indigo-50 rounded-2xl p-6 space-y-3">
        <Skeleton width={40} height={40} className="rounded-xl" />
        <Skeleton width={120} height={22} />
        <Skeleton width="80%" height={14} />
      </div>
      <div className="bg-white rounded-2xl p-6 border border-slate-200/60 flex flex-col items-center gap-3">
        <Skeleton width={48} height={48} circle />
        <Skeleton width={80} height={16} />
        <Skeleton width={100} height={12} />
      </div>
    </div>
  </div>
);

export default {
  Skeleton,
  DashboardSkeleton,
  TableSkeleton,
  CardGridSkeleton,
  FormSkeleton,
  DetailSkeleton,
  PageSkeleton,
  MorphingSkeleton,
  SkeletonTable,
  SkeletonText,
  TodayViewSkeleton,
};
