import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, AlertCircle, CheckCircle, Star, Users,
  ArrowRight, Target, Zap, Activity, AlertTriangle,
  ChevronRight, Sparkles
} from 'lucide-react';
import { api } from '../services/api';

interface CustomerCategory {
  id: string;
  name: string;
  email?: string;
  company?: string;
  win_rate?: number;
  days_since?: number;
}

interface DashboardSummary {
  total_customers: number;
  vip_count: number;
  active_count: number;
  at_risk_count: number;
  new_count: number;
}

export const IntelligenceDashboard = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [categories, setCategories] = useState<{
    vip: CustomerCategory[];
    active: CustomerCategory[];
    at_risk: CustomerCategory[];
    new: CustomerCategory[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.get('/intelligence/customers');
      setSummary(res.data.summary);
      setCategories(res.data.categories);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const getActionableInsights = () => {
    const insights = [];
    
    if (summary) {
      if (summary.at_risk_count > 0) {
        insights.push({
          type: 'urgent',
          title: `${summary.at_risk_count} Customer${summary.at_risk_count > 1 ? 's' : ''} At Risk`,
          description: "They haven't requested a quote in 90+ days. Reach out before you lose them.",
          action: 'View At-Risk',
          actionLink: '#at-risk',
          color: 'red'
        });
      }
      
      if (summary.new_count > 0) {
        insights.push({
          type: 'opportunity',
          title: `${summary.new_count} New Customer${summary.new_count > 1 ? 's' : ''}`,
          description: "No quotes yet. First impressions matter - send a competitive quote soon.",
          action: 'View New',
          actionLink: '#new',
          color: 'blue'
        });
      }
      
      if (summary.vip_count > 0) {
        insights.push({
          type: 'good',
          title: `${summary.vip_count} VIP Customer${summary.vip_count > 1 ? 's' : ''}`,
          description: "High win rate + recent activity. Prioritize their requests.",
          action: 'View VIPs',
          actionLink: '#vip',
          color: 'green'
        });
      }
    }
    
    return insights;
  };

  const actionableInsights = getActionableInsights();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Customer Intelligence</h1>
              <p className="text-gray-600 mt-1">Understand your customers and take action</p>
            </div>
            <button
              onClick={() => navigate('/customers')}
              className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              View All Customers
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
              <Users size={16} />
              Total Customers
            </div>
            <div className="text-3xl font-bold text-gray-900">{summary?.total_customers || 0}</div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-xl p-5">
            <div className="flex items-center gap-2 text-green-700 text-sm mb-2">
              <Star size={16} />
              VIP Customers
            </div>
            <div className="text-3xl font-bold text-green-700">{summary?.vip_count || 0}</div>
            <div className="text-sm text-green-600 mt-1">High win rate</div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
            <div className="flex items-center gap-2 text-blue-700 text-sm mb-2">
              <Activity size={16} />
              Active
            </div>
            <div className="text-3xl font-bold text-blue-700">{summary?.active_count || 0}</div>
            <div className="text-sm text-blue-600 mt-1">Regular quotes</div>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-xl p-5">
            <div className="flex items-center gap-2 text-red-700 text-sm mb-2">
              <AlertTriangle size={16} />
              At Risk
            </div>
            <div className="text-3xl font-bold text-red-700">{summary?.at_risk_count || 0}</div>
            <div className="text-sm text-red-600 mt-1">90+ days quiet</div>
          </div>
        </div>

        {/* Actionable Insights */}
        {actionableInsights.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Zap className="text-amber-500" size={20} />
              Recommended Actions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {actionableInsights.map((insight, index) => (
                <div 
                  key={index} 
                  className={`rounded-xl p-5 border ${
                    insight.color === 'red' ? 'bg-red-50 border-red-200' :
                    insight.color === 'green' ? 'bg-green-50 border-green-200' :
                    'bg-blue-50 border-blue-200'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${
                      insight.color === 'red' ? 'bg-red-100' :
                      insight.color === 'green' ? 'bg-green-100' :
                      'bg-blue-100'
                    }`}>
                      {insight.color === 'red' ? <AlertTriangle size={20} className="text-red-600" /> :
                       insight.color === 'green' ? <CheckCircle size={20} className="text-green-600" /> :
                       <Sparkles size={20} className="text-blue-600" />}
                    </div>
                    <div className="flex-1">
                      <h3 className={`font-semibold ${
                        insight.color === 'red' ? 'text-red-900' :
                        insight.color === 'green' ? 'text-green-900' :
                        'text-blue-900'
                      }`}>{insight.title}</h3>
                      <p className={`text-sm mt-1 ${
                        insight.color === 'red' ? 'text-red-700' :
                        insight.color === 'green' ? 'text-green-700' :
                        'text-blue-700'
                      }`}>{insight.description}</p>
                      <button
                        onClick={() => {
                          const element = document.querySelector(insight.actionLink);
                          element?.scrollIntoView({ behavior: 'smooth' });
                        }}
                        className={`mt-3 text-sm font-medium ${
                          insight.color === 'red' ? 'text-red-700 hover:text-red-800' :
                          insight.color === 'green' ? 'text-green-700 hover:text-green-800' :
                          'text-blue-700 hover:text-blue-800'
                        }`}
                      >
                        {insight.action} →
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Customer Categories */}
        <div className="space-y-6">
          {/* VIP Section */}
          {categories?.vip && categories.vip.length > 0 && (
            <div id="vip" className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-green-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Star className="text-green-600" size={20} />
                    <h2 className="font-semibold text-gray-900">VIP Customers</h2>
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                      {categories.vip.length}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">High win rate, recent activity</p>
                </div>
              </div>
              <div className="divide-y divide-gray-100">
                {categories.vip.map((customer) => (
                  <div 
                    key={customer.id} 
                    onClick={() => navigate(`/intelligence/customers/${customer.id}`)}
                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center text-green-700 font-medium">
                        {customer.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{customer.name}</h3>
                        {customer.company && (
                          <p className="text-sm text-gray-500">{customer.company}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-medium text-green-600">
                          {customer.win_rate?.toFixed(0)}% Win Rate
                        </div>
                        <div className="text-xs text-gray-500">Excellent relationship</div>
                      </div>
                      <ChevronRight size={18} className="text-gray-400" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* At Risk Section */}
          {categories?.at_risk && categories.at_risk.length > 0 && (
            <div id="at-risk" className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-red-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="text-red-600" size={20} />
                    <h2 className="font-semibold text-gray-900">At Risk</h2>
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded-full">
                      {categories.at_risk.length}
                    </span>
                  </div>
                  <p className="text-sm text-red-600 font-medium">Needs immediate attention</p>
                </div>
              </div>
              <div className="divide-y divide-gray-100">
                {categories.at_risk.map((customer) => (
                  <div 
                    key={customer.id} 
                    onClick={() => navigate(`/intelligence/customers/${customer.id}`)}
                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center text-red-700 font-medium">
                        {customer.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{customer.name}</h3>
                        {customer.company && (
                          <p className="text-sm text-gray-500">{customer.company}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-medium text-red-600">
                          {customer.days_since} days since last quote
                        </div>
                        <div className="text-xs text-gray-500">Schedule check-in call</div>
                      </div>
                      <ChevronRight size={18} className="text-gray-400" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active Section */}
          {categories?.active && categories.active.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-blue-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="text-blue-600" size={20} />
                    <h2 className="font-semibold text-gray-900">Active Customers</h2>
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
                      {categories.active.length}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">Regular quote activity</p>
                </div>
              </div>
              <div className="divide-y divide-gray-100">
                {categories.active.slice(0, 5).map((customer) => (
                  <div 
                    key={customer.id} 
                    onClick={() => navigate(`/intelligence/customers/${customer.id}`)}
                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-medium">
                        {customer.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{customer.name}</h3>
                        {customer.company && (
                          <p className="text-sm text-gray-500">{customer.company}</p>
                        )}
                      </div>
                    </div>
                    <ChevronRight size={18} className="text-gray-400" />
                  </div>
                ))}
                {categories.active.length > 5 && (
                  <div className="px-6 py-3 text-center">
                    <button 
                      onClick={() => navigate('/customers')}
                      className="text-sm text-orange-600 font-medium hover:text-orange-700"
                    >
                      View {categories.active.length - 5} more →
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* New Section */}
          {categories?.new && categories.new.length > 0 && (
            <div id="new" className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="text-gray-600" size={20} />
                    <h2 className="font-semibold text-gray-900">New Customers</h2>
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
                      {categories.new.length}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">No quotes yet - first impression counts</p>
                </div>
              </div>
              <div className="divide-y divide-gray-100">
                {categories.new.map((customer) => (
                  <div 
                    key={customer.id} 
                    className="px-6 py-4 hover:bg-gray-50 transition-colors flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-700 font-medium">
                        {customer.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{customer.name}</h3>
                        {customer.company && (
                          <p className="text-sm text-gray-500">{customer.company}</p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => navigate(`/quotes/new?customer=${customer.id}`)}
                      className="px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700 transition-colors"
                    >
                      Create First Quote
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IntelligenceDashboard;
