import React, { useState, useEffect } from 'react';
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
    manualTime: 18, // minutes - Industry Baseline
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
      {/* Hero Header with Tech Grid Background */}
      <div className="relative bg-white border-b border-slate-200/60 overflow-hidden">
        {/* Tech grid pattern */}
        <div className="absolute inset-0 tech-grid opacity-60" />
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-orange-50/50 via-transparent to-slate-50/30" />

        <div className="relative max-w-6xl mx-auto px-12 py-14">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-slate-950 tracking-tighter">Business Impact & ROI</h1>
              <p className="text-slate-500 mt-3 text-lg">Validate the value of high-velocity quoting.</p>
            </div>
            <div className="flex items-center gap-2 px-5 py-2.5 bg-emerald-50/80 backdrop-blur-sm border border-emerald-200/60 rounded-full shadow-soft">
              <Activity className="text-emerald-600" size={20} />
              <span className="font-semibold text-emerald-700">
                Live Metrics
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-12 py-12 space-y-14">

        {/* ROI Calculator Section - Tech Grid Background */}
        <section>
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-orange-50 rounded-xl">
              <Calculator className="text-orange-600" size={24} />
            </div>
            <h2 className="text-2xl font-bold text-slate-950 tracking-tight">ROI Calculator</h2>
          </div>

          <div className="relative bg-white rounded-2xl shadow-soft border-minimal overflow-hidden">
            <div className="grid grid-cols-1 lg:grid-cols-12">

              {/* Inputs Column */}
              <div className="lg:col-span-5 p-10 space-y-8 bg-slate-50/50 border-r border-slate-100">
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-3 tracking-tight">
                      Annual Requests
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        value={inputs.requests}
                        onChange={(e) => handleInputChange('requests', parseInt(e.target.value) || 0)}
                        className="w-full pl-4 pr-20 py-4 bg-white border-minimal rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all text-slate-900 font-semibold text-lg shadow-soft"
                      />
                      <span className="absolute right-4 top-4 text-slate-400 text-sm font-medium">RFQs/yr</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-3 tracking-tight">
                      Team Size
                    </label>
                    <div className="relative">
                      <Users className="absolute left-4 top-4 text-slate-400" size={20} />
                      <input
                        type="number"
                        value={inputs.employees}
                        onChange={(e) => handleInputChange('employees', parseInt(e.target.value) || 0)}
                        className="w-full pl-12 pr-24 py-4 bg-white border-minimal rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all text-slate-900 font-semibold text-lg shadow-soft"
                      />
                      <span className="absolute right-4 top-4 text-slate-400 text-sm font-medium">Employees</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-3 tracking-tight">
                      Manual Processing Time
                    </label>
                    <div className="relative">
                      <Clock className="absolute left-4 top-4 text-slate-400" size={20} />
                      <input
                        type="number"
                        value={inputs.manualTime}
                        onChange={(e) => handleInputChange('manualTime', parseInt(e.target.value) || 0)}
                        className="w-full pl-12 pr-24 py-4 bg-white border-minimal rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all text-slate-900 font-semibold text-lg shadow-soft"
                      />
                      <span className="absolute right-4 top-4 text-slate-400 text-sm font-medium">Mins/Quote</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-3 tracking-tight">
                      Avg Quote Value
                    </label>
                    <div className="relative">
                      <DollarSign className="absolute left-4 top-4 text-slate-400" size={20} />
                      <input
                        type="number"
                        value={inputs.avgValue}
                        onChange={(e) => handleInputChange('avgValue', parseFloat(e.target.value) || 0)}
                        className="w-full pl-12 pr-4 py-4 bg-white border-minimal rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all text-slate-900 font-semibold text-lg shadow-soft"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Outputs Column with Tech Grid */}
              <div className="lg:col-span-7 p-10 flex flex-col justify-center relative overflow-hidden">
                {/* Subtle tech grid background */}
                <div className="absolute inset-0 tech-grid-fine opacity-40" />

                {calculating && (
                  <div className="absolute top-6 right-6 animate-pulse text-orange-500 text-sm font-semibold">
                    Updating...
                  </div>
                )}

                <div className="relative grid grid-cols-1 md:grid-cols-2 gap-6">

                  {/* Potential Savings Card */}
                  <div className="p-8 rounded-2xl bg-slate-950 text-white shadow-soft-xl transition-all hover:-translate-y-1 hover:shadow-soft-xl">
                    <div className="flex items-center gap-2 text-slate-400 mb-5">
                      <Zap size={20} className="text-yellow-400" />
                      <span className="font-semibold text-sm tracking-tight">Potential Savings</span>
                    </div>
                    <div className="text-5xl font-bold tracking-tighter mb-3">
                      {simulation?.currency}
                      {simulation?.potential_savings.toLocaleString()}
                    </div>
                    <div className="text-sm text-slate-400">
                      Based on {simulation?.hours_saved_annually.toLocaleString()} hours saved annually
                    </div>
                  </div>

                  {/* Revenue Upside Card */}
                  <div className="p-8 rounded-2xl bg-white border-minimal shadow-soft-lg transition-all hover:-translate-y-1">
                    <div className="flex items-center gap-2 text-slate-500 mb-5">
                      <TrendingUp size={20} className="text-emerald-500" />
                      <span className="font-semibold text-sm text-slate-700 tracking-tight">Revenue Upside</span>
                    </div>
                    <div className="text-5xl font-bold tracking-tighter text-slate-950 mb-3">
                      {simulation?.currency}
                      {simulation?.revenue_upside.toLocaleString()}
                    </div>
                    <div className="text-sm text-slate-500">
                      Projected pipeline lift from increased velocity
                    </div>
                  </div>

                </div>

                {/* Visual Summary - The Velocity Advantage */}
                <div className="relative mt-10 p-8 bg-gradient-to-br from-orange-50 to-amber-50/50 rounded-2xl border border-orange-100/60">
                  <div className="flex items-start gap-5">
                    <div className="p-4 bg-white rounded-2xl shadow-soft text-orange-600">
                      <Target size={28} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-slate-950 tracking-tight">The Velocity Advantage</h3>
                      <p className="text-slate-600 mt-2 text-lg leading-relaxed">
                        By automating {inputs.requests.toLocaleString()} requests, you reclaim
                        <span className="font-bold text-slate-950"> {simulation?.hours_saved_annually.toLocaleString()} hours </span>
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

        {/* Performance Dashboard Section */}
        <section>
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-slate-950 tracking-tight">Performance Dashboard</h2>
            <span className="text-sm text-slate-500 font-medium">Based on your actual usage</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bento-card p-8 transition-all hover:-translate-y-1">
              <div className="text-slate-500 text-sm mb-3 flex items-center gap-2 font-medium">
                <Clock size={16} />
                Time Saved
              </div>
              <div className="text-4xl font-bold text-slate-950 tracking-tighter">{timeData?.total_hours_saved || 0}h</div>
            </div>
            <div className="bento-card p-8 transition-all hover:-translate-y-1">
              <div className="text-slate-500 text-sm mb-3 flex items-center gap-2 font-medium">
                <FileText size={16} />
                Quotes
              </div>
              <div className="text-4xl font-bold text-slate-950 tracking-tighter">{quoteData?.total_quotes_created || 0}</div>
            </div>
            <div className="bento-card p-8 transition-all hover:-translate-y-1">
              <div className="text-slate-500 text-sm mb-3 flex items-center gap-2 font-medium">
                <Target size={16} />
                Win Rate
              </div>
              <div className="text-4xl font-bold text-slate-950 tracking-tighter">{quoteData?.win_rate_percent || 0}%</div>
            </div>
            <div className="bento-card p-8 transition-all hover:-translate-y-1">
              <div className="text-slate-500 text-sm mb-3 flex items-center gap-2 font-medium">
                <Briefcase size={16} />
                Revenue
              </div>
              <div className="text-4xl font-bold text-slate-950 tracking-tighter">${(quoteData?.total_revenue || 0).toLocaleString()}</div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
};

export default BusinessImpact;
