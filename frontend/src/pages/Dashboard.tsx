import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, FileText, Users, Package, TrendingUp, Clock, CheckCircle, Sparkles, Zap, BarChart3 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { quotesApi, statsApi } from '../services/api';
import { queryKeys } from '../lib/queryClient';
import { DashboardSkeleton } from '../components/SkeletonScreens';

// Bento Grid Stat Card with hover lift effect
const StatCard = ({ title, value, change, icon: Icon, href, size = 'default' }: any) => (
  <Link
    to={href}
    className={`group bento-card p-8 flex flex-col justify-between transition-all hover:-translate-y-1 ${size === 'large' ? 'md:col-span-2' : ''
      }`}
  >
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-slate-500 mb-2 tracking-tight">{title}</p>
        <p className="text-4xl font-bold text-slate-950 tracking-tighter">{value}</p>
        {change && (
          <p className="text-sm text-emerald-600 mt-2 font-medium flex items-center gap-1">
            <TrendingUp size={14} />
            {change}
          </p>
        )}
      </div>
      <div className="p-3 bg-slate-50 rounded-xl group-hover:bg-orange-50 transition-colors">
        <Icon size={22} className="text-slate-600 group-hover:text-orange-600 transition-colors" />
      </div>
    </div>
  </Link>
);

// Hero Action Card - Large Bento Grid item with gradient
const HeroActionCard = () => (
  <div className="md:col-span-2 tech-grid bento-card overflow-hidden relative group transition-all hover:-translate-y-1">
    {/* Gradient overlay */}
    <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 via-transparent to-amber-500/5 pointer-events-none" />

    <div className="relative p-10">
      <div className="flex items-start gap-6">
        <div className="p-4 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl shadow-soft-lg">
          <Sparkles size={28} className="text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-slate-950 tracking-tight mb-2">
            AI-Powered Quote Extraction
          </h3>
          <p className="text-slate-600 text-lg mb-6 leading-relaxed max-w-xl">
            Upload RFQs, emails, or PDFs and let AI extract line items automatically.
            Zero-error precision with human-in-the-loop verification.
          </p>
          <Link
            to="/quotes/new"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-950 text-white text-sm font-semibold rounded-xl hover:bg-slate-800 transition-all shadow-soft group-hover:shadow-soft-lg"
          >
            New Request
            <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>
    </div>
  </div>
);

// Recent Quotes Table - Clean, minimal design
const RecentQuotesTable = ({ quotes }: { quotes: any[] }) => (
  <div className="md:col-span-2 bento-card overflow-hidden transition-all hover:-translate-y-1">
    <div className="px-8 py-6 flex items-center justify-between">
      <h3 className="text-lg font-semibold text-slate-950 tracking-tight">Recent Quotes</h3>
      <Link
        to="/quotes"
        className="text-sm font-medium text-slate-600 hover:text-orange-600 flex items-center gap-1 transition-colors"
      >
        View all <ArrowRight size={14} />
      </Link>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-t border-slate-100">
            <th className="px-8 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Customer</th>
            <th className="px-8 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Amount</th>
            <th className="px-8 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Assignee</th>
            <th className="px-8 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
            <th className="px-8 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {quotes.map((quote) => (
            <tr key={quote.id} className="hover:bg-slate-50/50 transition-colors">
              <td className="px-8 py-5 text-sm font-medium text-slate-950">
                {quote.customer_name || 'Unknown'}
              </td>
              <td className="px-8 py-5 text-sm text-slate-600 font-medium">
                ${quote.total?.toFixed(2) || '0.00'}
              </td>
              <td className="px-8 py-5">
                {quote.assignee_name ? (
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-[9px] font-bold">
                      {quote.assignee_name.split(' ').map((n: string) => n[0]).join('').toUpperCase()}
                    </div>
                    <span className="text-sm text-slate-700">{quote.assignee_name}</span>
                  </div>
                ) : (
                  <span className="text-sm text-slate-400 font-medium">Unassigned</span>
                )}
              </td>
              <td className="px-8 py-5">
                <span className={`inline-flex px-2.5 py-1 text-xs font-medium rounded-full ${quote.status === 'accepted' ? 'bg-emerald-50 text-emerald-700' :
                  quote.status === 'sent' ? 'bg-blue-50 text-blue-700' :
                    'bg-slate-100 text-slate-700'
                  }`}>
                  {quote.status}
                </span>
              </td>
              <td className="px-8 py-5 text-sm text-slate-500">
                {new Date(quote.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

// Quick Action Card with hover lift
const QuickActionCard = ({ icon: Icon, title, description, to, color = 'orange' }: any) => {
  const colorClasses = {
    orange: 'bg-orange-50 text-orange-600 group-hover:bg-orange-100',
    blue: 'bg-blue-50 text-blue-600 group-hover:bg-blue-100',
    emerald: 'bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100',
    purple: 'bg-purple-50 text-purple-600 group-hover:bg-purple-100',
  };

  return (
    <Link
      to={to}
      className="group bento-card p-6 flex items-start gap-4 transition-all hover:-translate-y-1"
    >
      <div className={`p-3 rounded-xl transition-colors ${colorClasses[color as keyof typeof colorClasses]}`}>
        <Icon size={20} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-slate-950 tracking-tight">{title}</p>
        <p className="text-sm text-slate-500 mt-0.5">{description}</p>
      </div>
      <ArrowRight size={16} className="text-slate-300 group-hover:text-slate-600 group-hover:translate-x-0.5 transition-all mt-1" />
    </Link>
  );
};

// Insights Card
const InsightsCard = () => (
  <div className="bento-card p-8 transition-all hover:-translate-y-1">
    <div className="flex items-center gap-3 mb-4">
      <div className="p-2 bg-amber-50 rounded-lg">
        <Zap size={18} className="text-amber-600" />
      </div>
      <h3 className="text-sm font-semibold text-slate-950 tracking-tight">Getting Started</h3>
    </div>
    <ul className="space-y-3 text-sm">
      <li className="flex items-start gap-2.5 text-slate-600">
        <CheckCircle size={16} className="mt-0.5 flex-shrink-0 text-emerald-500" />
        <span>Add your product catalog</span>
      </li>
      <li className="flex items-start gap-2.5 text-slate-600">
        <CheckCircle size={16} className="mt-0.5 flex-shrink-0 text-emerald-500" />
        <span>Import customers from CSV</span>
      </li>
      <li className="flex items-start gap-2.5 text-slate-600">
        <CheckCircle size={16} className="mt-0.5 flex-shrink-0 text-slate-300" />
        <span>Try AI extraction on an RFQ</span>
      </li>
    </ul>
  </div>
);

// Metrics Mini Card
const MetricsMiniCard = ({ icon: Icon, label, value, trend }: any) => (
  <div className="bento-card p-6 transition-all hover:-translate-y-1">
    <div className="flex items-center gap-2 text-slate-500 mb-2">
      <Icon size={14} />
      <span className="text-xs font-medium uppercase tracking-wider">{label}</span>
    </div>
    <div className="text-2xl font-bold text-slate-950 tracking-tight">{value}</div>
    {trend && (
      <div className="text-xs text-emerald-600 font-medium mt-1">{trend}</div>
    )}
  </div>
);

export const Dashboard = () => {
  // Cached data fetching - survives route switches
  const { data: recentQuotes = [], isLoading: quotesLoading } = useQuery({
    queryKey: queryKeys.quotes.list(),
    queryFn: async () => {
      const res = await quotesApi.list(5);
      return res.data || [];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: queryKeys.stats.dashboard(),
    queryFn: async () => {
      const res = await statsApi.get(30);
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });

  const loading = quotesLoading || statsLoading;

  const stats = {
    totalQuotes: statsData?.total_quotes || 0,
    totalCustomers: statsData?.total_customers || 0,
    totalProducts: 0,
    pendingQuotes: recentQuotes.filter((q: any) => q.status === 'draft').length,
  };

  if (loading && !statsData && recentQuotes.length === 0) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header with generous padding */}
      <div className="bg-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-12 py-10">
          <h1 className="text-3xl font-bold text-slate-950 tracking-tight">Dashboard</h1>
          <p className="text-slate-500 mt-2 text-lg">Track quotes, customers, and performance</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-12 py-10">
        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

          {/* Row 1: Stats */}
          <StatCard
            title="Total Quotes"
            value={stats.totalQuotes}
            change="+12% this month"
            icon={FileText}
            href="/quotes"
          />
          <StatCard
            title="Customers"
            value={stats.totalCustomers}
            change="+5 new"
            icon={Users}
            href="/customers"
          />
          <StatCard
            title="Products"
            value={stats.totalProducts || '—'}
            icon={Package}
            href="/products"
          />
          <StatCard
            title="Pending Quotes"
            value={stats.pendingQuotes}
            icon={Clock}
            href="/quotes"
          />

          {/* Row 2: Hero Card spanning 2 columns + Quick Actions */}
          <HeroActionCard />

          {/* Quick Actions Stack */}
          <div className="md:col-span-2 flex flex-col gap-6">
            <QuickActionCard
              icon={FileText}
              title="Create Quote"
              description="AI-powered quote creation"
              to="/quotes/new"
              color="orange"
            />
            <QuickActionCard
              icon={Users}
              title="Add Customer"
              description="New customer to your CRM"
              to="/customers"
              color="blue"
            />
            <QuickActionCard
              icon={Package}
              title="Update Catalog"
              description="Add or edit products"
              to="/products"
              color="emerald"
            />
          </div>

          {/* Row 3: Recent Quotes Table + Insights */}
          <RecentQuotesTable quotes={recentQuotes} />

          <InsightsCard />

          <MetricsMiniCard
            icon={BarChart3}
            label="Efficiency"
            value="85%"
            trend="+12% vs last month"
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
