import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Clock, TrendingUp, DollarSign, FileText, Target,
  ArrowUpRight, Calendar, AlertCircle, CheckCircle,
  Briefcase, Zap, BarChart3, ChevronRight
} from 'lucide-react';
import { api } from '../services/api';

interface TimeSummary {
  total_hours_saved: number;
  daily_average_hours: number;
  dollar_value: number;
  by_feature: Record<string, {
    count: number;
    hours_saved: number;
    description: string;
  }>;
}

interface QuoteEfficiency {
  total_quotes_created: number;
  quotes_accepted: number;
  win_rate_percent: number;
  total_revenue: number;
  average_quote_value: number;
  time_saved_hours: number;
  efficiency_gain_percent: number;
}

interface ROI {
  monthly_subscription_cost: number;
  time_saved_value: number;
  additional_revenue_attributed: number;
  total_value_generated: number;
  roi_percent: number;
  recommendation: string;
}

export const BusinessImpact = () => {
  const navigate = useNavigate();
  const [timeData, setTimeData] = useState<TimeSummary | null>(null);
  const [quoteData, setQuoteData] = useState<QuoteEfficiency | null>(null);
  const [roiData, setROIData] = useState<ROI | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.get('/impact/dashboard');
      setTimeData(res.data.time_this_month);
      setQuoteData(res.data.quote_efficiency);
      setROIData(res.data.roi);
    } catch (err) {
      console.error('Failed to load impact data:', err);
    } finally {
      setLoading(false);
    }
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Business Impact</h1>
              <p className="text-gray-600 mt-1">Measurable results from using OpenMercura</p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg">
              <TrendingUp className="text-green-600" size={20} />
              <span className="font-semibold text-green-700">
                {roiData?.roi_percent || 0}% ROI
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Top Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
              <Clock size={16} />
              Time Saved This Month
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {timeData?.total_hours_saved || 0}h
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {timeData?.daily_average_hours || 0}h avg/day
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
              <DollarSign size={16} />
              Value of Time Saved
            </div>
            <div className="text-3xl font-bold text-gray-900">
              ${(timeData?.dollar_value || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              At $50/hr estimated
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
              <FileText size={16} />
              Quotes Created
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {quoteData?.total_quotes_created || 0}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {quoteData?.win_rate_percent || 0}% win rate
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
              <Briefcase size={16} />
              Revenue Closed
            </div>
            <div className="text-3xl font-bold text-gray-900">
              ${(quoteData?.total_revenue || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Accepted quotes
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Time Savings by Feature */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                  <Zap size={18} className="text-orange-500" />
                  Time Savings by Feature
                </h2>
              </div>
              
              <div className="divide-y divide-gray-100">
                {timeData?.by_feature && Object.entries(timeData.by_feature).map(([key, data]) => (
                  <div key={key} className="px-6 py-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">{data.description}</span>
                      <span className="text-sm text-gray-500">{data.count} uses</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div 
                          className="bg-orange-500 h-2 rounded-full transition-all"
                          style={{ 
                            width: `${Math.min((data.hours_saved / (timeData?.total_hours_saved || 1)) * 100, 100)}%` 
                          }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700 w-20 text-right">
                        {data.hours_saved.toFixed(1)}h saved
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Efficiency Gain */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BarChart3 size={18} className="text-blue-500" />
                Quoting Efficiency
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-500">Traditional quoting time</p>
                    <p className="text-lg font-semibold text-gray-700">18 minutes per quote</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">With OpenMercura</p>
                    <p className="text-lg font-semibold text-green-700">2 minutes per quote</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                  <div>
                    <p className="font-semibold text-green-800">
                      {quoteData?.efficiency_gain_percent || 89}% faster quoting
                    </p>
                    <p className="text-sm text-green-700">
                      {quoteData?.time_saved_hours || 0} hours saved on {quoteData?.total_quotes_created || 0} quotes this month
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* ROI Breakdown */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                  <Target size={18} className="text-green-500" />
                  Return on Investment
                </h2>
              </div>
              
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Monthly subscription</span>
                  <span className="font-medium text-gray-900">
                    ${roiData?.monthly_subscription_cost || 99}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Time saved value</span>
                  <span className="font-medium text-green-700">
                    +${(roiData?.time_saved_value || 0).toLocaleString()}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Additional revenue</span>
                  <span className="font-medium text-green-700">
                    +${(roiData?.additional_revenue_attributed || 0).toLocaleString()}
                  </span>
                </div>
                
                <div className="border-t pt-4 flex items-center justify-between">
                  <span className="font-semibold text-gray-900">Total value generated</span>
                  <span className="text-xl font-bold text-green-700">
                    ${(roiData?.total_value_generated || 0).toLocaleString()}
                  </span>
                </div>
                
                <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
                  <TrendingUp className="text-green-600" size={20} />
                  <span className="font-semibold text-green-800">
                    {roiData?.roi_percent || 0}% ROI
                  </span>
                  <span className="text-sm text-green-600">
                    ({roiData?.recommendation || 'Good'})
                  </span>
                </div>
              </div>
            </div>

            {/* Monthly Projection */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <h2 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
                <Calendar size={18} />
                Annual Projection
              </h2>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-blue-800">Time saved (annual)</span>
                  <span className="font-semibold text-blue-900">
                    {((timeData?.total_hours_saved || 0) * 12).toFixed(0)} hours
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-blue-800">Value generated (annual)</span>
                  <span className="font-semibold text-blue-900">
                    ${((roiData?.total_value_generated || 0) * 12).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between border-t border-blue-200 pt-3">
                  <span className="text-blue-800">Annual ROI</span>
                  <span className="text-xl font-bold text-blue-900">
                    {roiData?.roi_percent || 0}%
                  </span>
                </div>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Key Performance Metrics</h2>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500 mb-1">Win Rate</p>
                  <p className={`text-2xl font-bold ${
                    (quoteData?.win_rate_percent || 0) >= 50 ? 'text-green-600' : 'text-amber-600'
                  }`}>
                    {quoteData?.win_rate_percent || 0}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {quoteData?.quotes_accepted || 0} of {quoteData?.total_quotes_created || 0} quotes
                  </p>
                </div>
                
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500 mb-1">Avg Quote Value</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${(quoteData?.average_quote_value || 0).toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Per accepted quote
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-8 bg-orange-50 border border-orange-200 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <ArrowUpRight className="text-orange-600" size={24} />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-orange-900 mb-1">
                Maximize Your Impact
              </h3>
              <p className="text-orange-800 mb-4">
                You're saving {timeData?.total_hours_saved || 0} hours this month. 
                Use Smart Quote for every RFQ to maximize time savings.
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => navigate('/quotes/new')}
                  className="px-4 py-2 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors"
                >
                  Create Quote
                </button>
                <button
                  onClick={() => navigate('/intelligence')}
                  className="px-4 py-2 text-orange-700 font-medium hover:bg-orange-100 rounded-lg transition-colors"
                >
                  Review Customers →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessImpact;
