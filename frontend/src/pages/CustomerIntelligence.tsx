import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  TrendingUp, AlertCircle, CheckCircle, Clock, DollarSign,
  ArrowRight, Users, Target, Zap, Activity, Calendar,
  ChevronRight, Star, Phone, Mail, Building
} from 'lucide-react';
import { api } from '../services/api';

interface Insight {
  type: string;
  title: string;
  description: string;
  action: string;
  action_link: string;
  impact: 'high' | 'medium' | 'low';
  metric_value?: number;
  metric_label?: string;
}

interface Prediction {
  title: string;
  prediction: string;
  explanation: string;
  confidence: 'high' | 'medium' | 'low';
}

export const CustomerIntelligence = () => {
  const { customerId } = useParams();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState<any>(null);
  const [healthScore, setHealthScore] = useState<any>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (customerId) {
      loadIntelligence();
    }
  }, [customerId]);

  const loadIntelligence = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/intelligence/customers/${customerId}`);
      setCustomer(res.data.customer);
      setHealthScore(res.data.health_score);
      setInsights(res.data.insights);
      setMetrics(res.data.metrics);
      setPredictions(res.data.predictions);
    } catch (err) {
      console.error('Failed to load intelligence:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (color: string) => {
    switch (color) {
      case 'green': return 'bg-green-500';
      case 'blue': return 'bg-blue-500';
      case 'amber': return 'bg-amber-500';
      case 'red': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getScoreBg = (color: string) => {
    switch (color) {
      case 'green': return 'bg-green-50 border-green-200';
      case 'blue': return 'bg-blue-50 border-blue-200';
      case 'amber': return 'bg-amber-50 border-amber-200';
      case 'red': return 'bg-red-50 border-red-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getImpactBadge = (impact: string) => {
    switch (impact) {
      case 'high':
        return <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded-full">High Impact</span>;
      case 'medium':
        return <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">Medium</span>;
      default:
        return <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">Low</span>;
    }
  };

  const formatCurrency = (value: number) => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

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
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <button onClick={() => navigate('/customers')} className="hover:text-gray-700">Customers</button>
            <ChevronRight size={14} />
            <span className="text-gray-900">Intelligence</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-orange-100 rounded-xl flex items-center justify-center">
                <Users className="text-orange-600" size={28} />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">{customer?.name}</h1>
                <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                  {customer?.email && (
                    <span className="flex items-center gap-1">
                      <Mail size={14} />
                      {customer.email}
                    </span>
                  )}
                  {customer?.company && (
                    <span className="flex items-center gap-1">
                      <Building size={14} />
                      {customer.company}
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <button
              onClick={() => navigate(`/quotes/new?customer=${customerId}`)}
              className="flex items-center gap-2 px-5 py-2.5 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors"
            >
              <Zap size={18} />
              Create Quote
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Health Score */}
        {healthScore && (
          <div className={`rounded-xl p-6 mb-6 border ${getScoreBg(healthScore.color)}`}>
            <div className="flex items-start gap-6">
              {/* Score Circle */}
              <div className="flex-shrink-0">
                <div className="relative w-24 h-24">
                  <svg className="w-24 h-24 transform -rotate-90">
                    <circle
                      cx="48"
                      cy="48"
                      r="44"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      className="text-white/50"
                    />
                    <circle
                      cx="48"
                      cy="48"
                      r="44"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      strokeDasharray={`${(healthScore.score / 100) * 276} 276`}
                      className={getScoreColor(healthScore.color)}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-gray-900">{healthScore.score}</span>
                  </div>
                </div>
              </div>

              {/* Score Info */}
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-lg font-semibold text-gray-900">Relationship Health</h2>
                  <span className={`px-3 py-1 text-sm font-medium rounded-full text-white ${getScoreColor(healthScore.color)}`}>
                    {healthScore.label}
                  </span>
                </div>
                <p className="text-gray-700">{healthScore.explanation}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Insights */}
          <div className="lg:col-span-2 space-y-6">
            {/* Key Insights */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center gap-2">
                  <Target className="text-orange-500" size={20} />
                  <h2 className="font-semibold text-gray-900">What You Should Know</h2>
                </div>
              </div>

              <div className="divide-y divide-gray-100">
                {insights.length === 0 ? (
                  <div className="px-6 py-8 text-center">
                    <CheckCircle className="mx-auto mb-3 text-green-500" size={40} />
                    <p className="text-gray-600">No insights yet. Create your first quote to start building intelligence.</p>
                  </div>
                ) : (
                  insights.map((insight, index) => (
                    <div key={index} className="p-6 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            {getImpactBadge(insight.impact)}
                            <h3 className="font-semibold text-gray-900">{insight.title}</h3>
                          </div>
                          <p className="text-gray-600 mb-3">{insight.description}</p>
                          
                          {insight.metric_value !== undefined && (
                            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg text-sm">
                              <span className="text-gray-500">{insight.metric_label}:</span>
                              <span className="font-semibold text-gray-900">
                                {insight.metric_label?.includes('Rate') 
                                  ? `${insight.metric_value.toFixed(0)}%`
                                  : insight.metric_label?.includes('Value') || insight.metric_label?.includes('Order')
                                    ? formatCurrency(insight.metric_value)
                                    : insight.metric_value.toFixed(0)}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="mt-4">
                        <button
                          onClick={() => navigate(insight.action_link)}
                          className="inline-flex items-center gap-1 text-sm font-medium text-orange-600 hover:text-orange-700"
                        >
                          {insight.action}
                          <ArrowRight size={14} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Predictions */}
            {predictions.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center gap-2">
                    <Activity className="text-purple-500" size={20} />
                    <h2 className="font-semibold text-gray-900">What Might Happen Next</h2>
                  </div>
                </div>

                <div className="divide-y divide-gray-100">
                  {predictions.map((prediction, index) => (
                    <div key={index} className="p-6">
                      <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-lg ${
                          prediction.confidence === 'high' ? 'bg-green-100' :
                          prediction.confidence === 'medium' ? 'bg-blue-100' : 'bg-gray-100'
                        }`}>
                          <TrendingUp className={`${
                            prediction.confidence === 'high' ? 'text-green-600' :
                            prediction.confidence === 'medium' ? 'text-blue-600' : 'text-gray-600'
                          }`} size={18} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium text-gray-900">{prediction.title}</h3>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              prediction.confidence === 'high' ? 'bg-green-100 text-green-700' :
                              prediction.confidence === 'medium' ? 'bg-blue-100 text-blue-700' :
                              'bg-gray-100 text-gray-600'
                            }`}>
                              {prediction.confidence} confidence
                            </span>
                          </div>
                          <p className="text-lg font-semibold text-gray-900 mb-1">{prediction.prediction}</p>
                          <p className="text-sm text-gray-500">{prediction.explanation}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Metrics & Quick Stats */}
          <div className="space-y-6">
            {/* Key Metrics */}
            {metrics && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Activity size={18} className="text-gray-400" />
                  By The Numbers
                </h2>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Total Quotes</span>
                    <span className="font-semibold text-gray-900">{metrics.total_quotes}</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Win Rate</span>
                    <span className={`font-semibold ${metrics.win_rate >= 50 ? 'text-green-600' : 'text-amber-600'}`}>
                      {metrics.win_rate.toFixed(0)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Average Quote</span>
                    <span className="font-semibold text-gray-900">{formatCurrency(metrics.avg_quote_value)}</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-100">
                    <span className="text-green-700">Lifetime Value</span>
                    <span className="font-semibold text-green-700">{formatCurrency(metrics.lifetime_value)}</span>
                  </div>
                  
                  {metrics.quotes_this_month > 0 && (
                    <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-100">
                      <span className="text-blue-700">This Month</span>
                      <span className="font-semibold text-blue-700">{metrics.quotes_this_month} quotes</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="space-y-2">
                <button
                  onClick={() => navigate(`/quotes?customer=${customerId}`)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg hover:bg-gray-50 border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <Clock size={18} className="text-gray-400" />
                  <span className="font-medium text-gray-700">View Quote History</span>
                </button>
                
                <button
                  onClick={() => navigate(`/customers/${customerId}`)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg hover:bg-gray-50 border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <Phone size={18} className="text-gray-400" />
                  <span className="font-medium text-gray-700">Contact Details</span>
                </button>
                
                <button
                  onClick={() => navigate(`/quotes/new?customer=${customerId}`)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg bg-orange-50 border border-orange-200 hover:bg-orange-100 transition-colors"
                >
                  <Star size={18} className="text-orange-500" />
                  <span className="font-medium text-orange-700">Create New Quote</span>
                </button>
              </div>
            </div>

            {/* Help Card */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <h3 className="font-semibold text-blue-900 mb-2">What is Customer Intelligence?</h3>
              <p className="text-sm text-blue-800 mb-3">
                We analyze your quote history to find patterns and opportunities. 
                The health score (0-100) shows relationship strength.
              </p>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-blue-800"><strong>80-100:</strong> Excellent - VIP treatment</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-blue-800"><strong>60-79:</strong> Good - Keep nurturing</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                  <span className="text-blue-800"><strong>40-59:</strong> At Risk - Reach out</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span className="text-blue-800"><strong>0-39:</strong> Needs work - Schedule call</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerIntelligence;
