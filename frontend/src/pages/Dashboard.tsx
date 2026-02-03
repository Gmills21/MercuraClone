import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, FileText, Users, Package, TrendingUp, Clock, CheckCircle } from 'lucide-react';
import { quotesApi, statsApi } from '../services/api';

// Clean, professional stat card - no glassmorphism
const StatCard = ({ title, value, change, icon: Icon, href }: any) => (
  <Link to={href} className="block bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
        <p className="text-3xl font-semibold text-gray-900">{value}</p>
        {change && (
          <p className="text-sm text-emerald-600 mt-1 font-medium">{change}</p>
        )}
      </div>
      <div className="p-2 bg-gray-50 rounded-lg">
        <Icon size={20} className="text-gray-600" />
      </div>
    </div>
  </Link>
);

// Clean table component
const RecentQuotesTable = ({ quotes }: { quotes: any[] }) => (
  <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
    <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
      <h3 className="text-lg font-semibold text-gray-900">Recent Quotes</h3>
      <Link to="/quotes" className="text-sm font-medium text-orange-600 hover:text-orange-700 flex items-center gap-1">
        View all <ArrowRight size={16} />
      </Link>
    </div>
    <table className="w-full">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Customer</th>
          <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Amount</th>
          <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
          <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-200">
        {quotes.map((quote) => (
          <tr key={quote.id} className="hover:bg-gray-50">
            <td className="px-6 py-4 text-sm font-medium text-gray-900">
              {quote.customer_name || 'Unknown'}
            </td>
            <td className="px-6 py-4 text-sm text-gray-600">
              ${quote.total?.toFixed(2) || '0.00'}
            </td>
            <td className="px-6 py-4">
              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
                quote.status === 'accepted' ? 'bg-emerald-50 text-emerald-700' :
                quote.status === 'sent' ? 'bg-blue-50 text-blue-700' :
                'bg-gray-50 text-gray-700'
              }`}>
                {quote.status}
              </span>
            </td>
            <td className="px-6 py-4 text-sm text-gray-500">
              {new Date(quote.created_at).toLocaleDateString()}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// Quick actions panel
const QuickActions = () => (
  <div className="bg-white border border-gray-200 rounded-lg p-6">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
    <div className="space-y-3">
      <Link
        to="/quotes/new"
        className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-orange-500 hover:bg-orange-50 transition-colors"
      >
        <div className="p-2 bg-orange-50 rounded-lg">
          <FileText size={18} className="text-orange-600" />
        </div>
        <div>
          <p className="font-medium text-gray-900">Create Quote</p>
          <p className="text-sm text-gray-500">AI-powered quote creation</p>
        </div>
      </Link>
      
      <Link
        to="/customers"
        className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-orange-500 hover:bg-orange-50 transition-colors"
      >
        <div className="p-2 bg-orange-50 rounded-lg">
          <Users size={18} className="text-orange-600" />
        </div>
        <div>
          <p className="font-medium text-gray-900">Add Customer</p>
          <p className="text-sm text-gray-500">New customer to your CRM</p>
        </div>
      </Link>
      
      <Link
        to="/products"
        className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-orange-500 hover:bg-orange-50 transition-colors"
      >
        <div className="p-2 bg-orange-50 rounded-lg">
          <Package size={18} className="text-orange-600" />
        </div>
        <div>
          <p className="font-medium text-gray-900">Update Catalog</p>
          <p className="text-sm text-gray-500">Add or edit products</p>
        </div>
      </Link>
    </div>
  </div>
);

// AI Extraction card
const AIExtractionCard = () => (
  <div className="bg-gradient-to-br from-orange-50 to-white border border-orange-200 rounded-lg p-6">
    <div className="flex items-start gap-4">
      <div className="p-3 bg-orange-100 rounded-lg">
        <TrendingUp size={24} className="text-orange-600" />
      </div>
      <div className="flex-1">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">AI-Powered Extraction</h3>
        <p className="text-sm text-gray-600 mb-4">
          Upload RFQs, emails, or PDFs and let AI extract line items automatically.
        </p>
        <Link
          to="/extractions"
          className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700 transition-colors"
        >
          Try AI Extraction <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  </div>
);

export const Dashboard = () => {
  const [stats, setStats] = useState({
    totalQuotes: 0,
    totalCustomers: 0,
    totalProducts: 0,
    pendingQuotes: 0,
  });
  const [recentQuotes, setRecentQuotes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Try to fetch from API, fall back to mock data
      const [quotesRes, statsRes] = await Promise.all([
        quotesApi.list(5).catch(() => ({ data: [] })),
        statsApi.get(30).catch(() => ({ data: { total_quotes: 0, total_customers: 0 } })),
      ]);
      
      setRecentQuotes(quotesRes.data || []);
      setStats({
        totalQuotes: statsRes.data?.total_quotes || 0,
        totalCustomers: statsRes.data?.total_customers || 0,
        totalProducts: 0, // Would come from products API
        pendingQuotes: (quotesRes.data || []).filter((q: any) => q.status === 'draft').length,
      });
    } catch (error) {
      console.error('Dashboard load error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="grid grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Track quotes, customers, and performance</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
            value={stats.totalProducts || '-'}
            icon={Package}
            href="/products"
          />
          <StatCard
            title="Pending Quotes"
            value={stats.pendingQuotes}
            icon={Clock}
            href="/quotes"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Recent Quotes */}
          <div className="lg:col-span-2 space-y-6">
            <RecentQuotesTable quotes={recentQuotes} />
            
            {/* AI Feature Highlight */}
            <AIExtractionCard />
          </div>

          {/* Right Column - Quick Actions */}
          <div className="space-y-6">
            <QuickActions />
            
            {/* Getting Started / Tips */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">Getting Started</h3>
              <ul className="space-y-2 text-sm text-blue-800">
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
                  <span>Add your product catalog</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
                  <span>Import customers from CSV</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
                  <span>Try AI extraction on an RFQ</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
