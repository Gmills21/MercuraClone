import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Clock, TrendingUp, DollarSign, FileText, Target,
  ArrowUpRight, Calendar, AlertCircle, CheckCircle,
  Briefcase, Zap, BarChart3, Users, Calculator, Activity
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

interface SimulationResult {
  potential_savings: number;
  revenue_upside: number;
  hours_saved_annually: number;
  pipeline_value: number;
  currency: string;
}

export const BusinessImpact = () => {
  const navigate = useNavigate();
  // Real Data
  const [timeData, setTimeData] = useState<TimeSummary | null>(null);
  const [quoteData, setQuoteData] = useState<QuoteEfficiency | null>(null);
  const [roiData, setROIData] = useState<ROI | null>(null);

  // Simulation State
  const [inputs, setInputs] = useState({
    requests: 1000,
    employees: 3,
    manualTime: 60, // minutes
    avgValue: 400
  });

  const [simulation, setSimulation] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  useEffect(() => {
    loadRealData();
    runSimulation();
  }, []);

  // Debounce simulation updates
  useEffect(() => {
    const timer = setTimeout(() => {
      runSimulation();
    }, 500);
    return () => clearTimeout(timer);
  }, [inputs]);

  const loadRealData = async () => {
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

  const runSimulation = async () => {
    setCalculating(true);
    try {
      const res = await api.post('/impact/simulate', {
        requests_per_year: inputs.requests,
        employees: inputs.employees,
        manual_time_mins: inputs.manualTime,
        avg_value_per_quote: inputs.avgValue
      });
      setSimulation(res.data);
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setCalculating(false);
    }
  };

  const handleInputChange = (field: keyof typeof inputs, value: number) => {
    setInputs(prev => ({ ...prev, [field]: value }));
  };

  if (loading && !simulation) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Business Impact & ROI</h1>
              <p className="text-slate-500 mt-2 text-lg">Validate the value of high-velocity quoting.</p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 border border-emerald-200 rounded-full">
              <Activity className="text-emerald-600" size={20} />
              <span className="font-semibold text-emerald-700">
                Live Metrics
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8 space-y-12">

        {/* ROI Calculator Section - "Apple-esque" Card */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <Calculator className="text-orange-600" size={24} />
            <h2 className="text-2xl font-bold text-slate-900">ROI Calculator</h2>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-slate-200">

              {/* Inputs Column */}
              <div className="lg:col-span-5 p-8 space-y-8 bg-slate-50/50">
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      Annual Requests
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        value={inputs.requests}
                        onChange={(e) => handleInputChange('requests', parseInt(e.target.value) || 0)}
                        className="w-full pl-3 pr-4 py-3 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all text-slate-900 font-medium"
                      />
                      <span className="absolute right-4 top-3.5 text-slate-400 text-sm">RFQs/yr</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      Team Size
                    </label>
                    <div className="relative">
                      <Users className="absolute left-3 top-3.5 text-slate-400" size={18} />
                      <input
                        type="number"
                        value={inputs.employees}
                        onChange={(e) => handleInputChange('employees', parseInt(e.target.value) || 0)}
                        className="w-full pl-10 pr-4 py-3 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all text-slate-900 font-medium"
                      />
                      <span className="absolute right-4 top-3.5 text-slate-400 text-sm">Employees</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      Manual Processing Time
                    </label>
                    <div className="relative">
                      <Clock className="absolute left-3 top-3.5 text-slate-400" size={18} />
                      <input
                        type="number"
                        value={inputs.manualTime}
                        onChange={(e) => handleInputChange('manualTime', parseInt(e.target.value) || 0)}
                        className="w-full pl-10 pr-4 py-3 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all text-slate-900 font-medium"
                      />
                      <span className="absolute right-4 top-3.5 text-slate-400 text-sm">Mins/Quote</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      Avg Quote Value
                    </label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-3.5 text-slate-400" size={18} />
                      <input
                        type="number"
                        value={inputs.avgValue}
                        onChange={(e) => handleInputChange('avgValue', parseFloat(e.target.value) || 0)}
                        className="w-full pl-10 pr-4 py-3 bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all text-slate-900 font-medium"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Outputs Column */}
              <div className="lg:col-span-7 p-8 flex flex-col justify-center bg-white relative">
                {calculating && (
                  <div className="absolute top-4 right-4 animate-pulse text-orange-500 text-sm font-medium">
                    Updating...
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                  {/* Potential Savings Card */}
                  <div className="p-6 rounded-2xl bg-slate-900 text-white shadow-xl transform transition-transform hover:scale-105 duration-300">
                    <div className="flex items-center gap-2 text-slate-400 mb-4">
                      <Zap size={20} className="text-yellow-400" />
                      <span className="font-medium">Potential Savings</span>
                    </div>
                    <div className="text-4xl font-bold tracking-tight mb-2">
                      {simulation?.currency}
                      {simulation?.potential_savings.toLocaleString()}
                    </div>
                    <div className="text-sm text-slate-400">
                      Based on {simulation?.hours_saved_annually.toLocaleString()} hours saved annually
                    </div>
                  </div>

                  {/* Revenue Upside Card */}
                  <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-lg transform transition-transform hover:scale-105 duration-300">
                    <div className="flex items-center gap-2 text-slate-500 mb-4">
                      <TrendingUp size={20} className="text-emerald-500" />
                      <span className="font-medium text-slate-900">Revenue Upside</span>
                    </div>
                    <div className="text-4xl font-bold tracking-tight text-slate-900 mb-2">
                      {simulation?.currency}
                      {simulation?.revenue_upside.toLocaleString()}
                    </div>
                    <div className="text-sm text-slate-500">
                      Projected pipeline lift from increased velocity
                    </div>
                  </div>

                </div>

                {/* Visual Summary */}
                <div className="mt-10 p-6 bg-orange-50 rounded-xl border border-orange-100">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-white rounded-full shadow-sm text-orange-600">
                      <Target size={24} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900">The Velocity Advantage</h3>
                      <p className="text-slate-600 mt-1">
                        By automating {inputs.requests.toLocaleString()} requests, you reclaim
                        <span className="font-bold text-slate-900"> {simulation?.hours_saved_annually.toLocaleString()} hours </span>
                        of skilled labor. In a high-velocity sales culture, this translates directly to
                        <span className="font-bold text-emerald-600"> market dominance</span>.
                      </p>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </section>

        {/* Existing Actual Data Section - Moved down and styled */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Performance Dashboard</h2>
            <span className="text-sm text-slate-500">Based on your actual usage</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
              <div className="text-slate-500 text-sm mb-1 flex items-center gap-2"><Clock size={16} /> Time Saved</div>
              <div className="text-2xl font-bold text-slate-900">{timeData?.total_hours_saved || 0}h</div>
            </div>
            <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
              <div className="text-slate-500 text-sm mb-1 flex items-center gap-2"><FileText size={16} /> Quotes</div>
              <div className="text-2xl font-bold text-slate-900">{quoteData?.total_quotes_created || 0}</div>
            </div>
            <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
              <div className="text-slate-500 text-sm mb-1 flex items-center gap-2"><Target size={16} /> Win Rate</div>
              <div className="text-2xl font-bold text-slate-900">{quoteData?.win_rate_percent || 0}%</div>
            </div>
            <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
              <div className="text-slate-500 text-sm mb-1 flex items-center gap-2"><Briefcase size={16} /> Revenue</div>
              <div className="text-2xl font-bold text-slate-900">${(quoteData?.total_revenue || 0).toLocaleString()}</div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
};

export default BusinessImpact;
