import React, { useEffect, useState } from 'react';
import { ArrowUpRight, DollarSign, FileText, CheckCircle, Clock, Users, ShoppingBag, TrendingUp, Zap, Target, AlertCircle, Mail, Copy, CheckCircle2, Link2, Power, Info } from 'lucide-react';
import { Link } from 'react-router-dom';
import { statsApi, quotesApi } from '../services/api';

const StatCard = ({ title, value, change, icon: Icon, trend }: any) => (
    <div className="glass-card p-6 rounded-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Icon size={64} />
        </div>
        <div className="relative z-10">
            <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-slate-800/50 rounded-lg">
                    <Icon size={20} className="text-primary-400" />
                </div>
                <h3 className="text-slate-400 font-medium text-sm">{title}</h3>
            </div>
            <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                    {value}
                </span>
                {change && (
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                        {change}
                    </span>
                )}
            </div>
        </div>
    </div>
);

export const Dashboard = () => {
    const [stats, setStats] = useState<any>(null);
    const [quotes, setQuotes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState(30);
    const [webhookEnabled, setWebhookEnabled] = useState(true);
    const [webhookCopied, setWebhookCopied] = useState(false);
    
    // Construct webhook URL from API base URL
    const API_BASE = 'http://localhost:8000';
    const webhookUrl = `${API_BASE}/webhooks/inbound-email`;
    const intakeEmail = 'intake@our-startup.com';

    useEffect(() => {
        fetchDashboardData();
    }, [timeRange]);

    const fetchDashboardData = async () => {
        setLoading(true);
        try {
            const [statsRes, quotesRes] = await Promise.all([
                statsApi.get(timeRange),
                quotesApi.list(20)
            ]);
            setStats(statsRes.data);
            setQuotes(quotesRes.data || []);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    // Calculate win rate predictor (simplified - based on quote status and age)
    const calculateWinRate = (quote: any) => {
        // High probability if:
        // - Recently created (within 7 days)
        // - Has high confidence items
        // - Total amount is reasonable (not too high/low)
        const createdDate = new Date(quote.created_at);
        const daysSinceCreated = (Date.now() - createdDate.getTime()) / (1000 * 60 * 60 * 24);
        
        let score = 0.5; // Base score
        
        if (daysSinceCreated < 7) score += 0.2;
        if (quote.total_amount > 1000 && quote.total_amount < 50000) score += 0.15;
        if (quote.items && quote.items.length > 0) {
            const avgConfidence = quote.items.reduce((sum: number, item: any) => {
                return sum + (item.metadata?.original_extraction?.confidence_score || 0.5);
            }, 0) / quote.items.length;
            score += avgConfidence * 0.15;
        }
        
        return Math.min(1, score);
    };

    const highProbabilityQuotes = quotes
        .filter(q => q.status === 'draft' || q.status === 'pending_approval')
        .map(q => ({ ...q, winProbability: calculateWinRate(q) }))
        .filter(q => q.winProbability > 0.65)
        .sort((a, b) => b.winProbability - a.winProbability)
        .slice(0, 5);

    if (loading) {
        return (
            <div className="space-y-8">
                <div className="text-center py-12 text-slate-500">Loading dashboard...</div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
                    <p className="text-slate-400">Welcome back, here's what's happening today.</p>
                </div>
                <div className="flex items-center gap-3">
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(Number(e.target.value))}
                        className="input-field"
                    >
                        <option value={7}>Last 7 days</option>
                        <option value={30}>Last 30 days</option>
                        <option value={90}>Last 90 days</option>
                    </select>
                    <Link to="/quotes/new" className="btn-primary flex items-center gap-2">
                        <FileText size={18} />
                        Create New Quote
                    </Link>
                </div>
            </div>

            {/* Phase 1: Connection Center - 1-Click Inbox Sync */}
            <div className="glass-panel rounded-2xl p-6 border-2 border-blue-500/30 bg-gradient-to-br from-blue-500/10 to-purple-500/10">
                <div className="flex items-start justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-blue-500/20 rounded-xl">
                            <Mail size={24} className="text-blue-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                Connection Center
                                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                    3-Minute Setup
                                </span>
                            </h2>
                            <p className="text-sm text-slate-400 mt-1">Eliminate Integration Anxiety - No IT Permission Required</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setWebhookEnabled(!webhookEnabled)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                            webhookEnabled
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30'
                                : 'bg-slate-700/50 text-slate-400 border border-slate-600 hover:bg-slate-700'
                        }`}
                    >
                        <Power size={16} className={webhookEnabled ? 'text-emerald-400' : 'text-slate-500'} />
                        {webhookEnabled ? 'Active' : 'Inactive'}
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Email Forwarding Section */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-3">
                            <CheckCircle2 size={18} className="text-blue-400" />
                            <h3 className="text-lg font-semibold text-white">1-Click Inbox Sync</h3>
                        </div>
                        <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700/50">
                            <p className="text-sm text-slate-400 mb-3">Forward your quote request emails to:</p>
                            <div className="flex items-center gap-2 mb-4">
                                <div className="flex-1 px-4 py-3 bg-slate-800/50 rounded-lg border border-slate-700/50 font-mono text-sm text-white">
                                    {intakeEmail}
                                </div>
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(intakeEmail);
                                        setWebhookCopied(true);
                                        setTimeout(() => setWebhookCopied(false), 2000);
                                    }}
                                    className="p-3 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
                                    title="Copy email address"
                                >
                                    {webhookCopied ? (
                                        <CheckCircle2 size={18} className="text-white" />
                                    ) : (
                                        <Copy size={18} className="text-white" />
                                    )}
                                </button>
                            </div>
                            <div className="flex items-start gap-2 text-xs text-slate-400">
                                <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
                                <span>Works with Gmail, Outlook, and any email provider. No API keys or complex setup required.</span>
                            </div>
                        </div>
                    </div>

                    {/* Webhook URL Section */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-3">
                            <Link2 size={18} className="text-purple-400" />
                            <h3 className="text-lg font-semibold text-white">Webhook Endpoint</h3>
                        </div>
                        <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700/50">
                            <p className="text-sm text-slate-400 mb-3">For advanced integrations (SendGrid/Mailgun):</p>
                            <div className="flex items-center gap-2 mb-4">
                                <div className="flex-1 px-4 py-3 bg-slate-800/50 rounded-lg border border-slate-700/50 font-mono text-xs text-white break-all">
                                    {webhookUrl}
                                </div>
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(webhookUrl);
                                        setWebhookCopied(true);
                                        setTimeout(() => setWebhookCopied(false), 2000);
                                    }}
                                    className="p-3 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors flex-shrink-0"
                                    title="Copy webhook URL"
                                >
                                    {webhookCopied ? (
                                        <CheckCircle2 size={18} className="text-white" />
                                    ) : (
                                        <Copy size={18} className="text-white" />
                                    )}
                                </button>
                            </div>
                            <div className="flex items-start gap-2 text-xs text-slate-400">
                                <Info size={14} className="mt-0.5 flex-shrink-0" />
                                <span>Configure this URL in your email provider's webhook settings for automated processing.</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Status Indicator */}
                <div className="mt-6 pt-6 border-t border-slate-700/50">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${webhookEnabled ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600'}`}></div>
                            <span className="text-sm text-slate-400">
                                {webhookEnabled ? 'Connection active - Ready to receive emails' : 'Connection inactive'}
                            </span>
                        </div>
                        <div className="text-xs text-slate-500">
                            vs. Mercura: 3 days → 3 minutes
                        </div>
                    </div>
                </div>
            </div>

            {/* Margin Added Tracker - Massive Counter */}
            {stats && (
                <div className="p-8 rounded-2xl bg-gradient-to-r from-emerald-500/20 via-green-500/20 to-teal-500/20 border border-emerald-500/30">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-6">
                            <div className="p-4 bg-emerald-500/20 rounded-2xl">
                                <DollarSign size={48} className="text-emerald-400" />
                            </div>
                            <div>
                                <div className="text-sm text-emerald-300 font-medium mb-2">Total Margin Added</div>
                                <div className="text-5xl font-bold text-white mb-1">
                                    ${stats.total_margin_added?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                                </div>
                                <div className="text-sm text-emerald-400">
                                    Additional profit from AI optimizations over the last {timeRange} days
                                </div>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-bold text-emerald-400">
                                {stats.total_quotes || 0} Quotes
                            </div>
                            <div className="text-sm text-slate-400">Processed</div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard 
                    title="Total Revenue" 
                    value={`$${stats?.total_quotes ? (stats.total_quotes * 5000).toLocaleString() : '0'}`} 
                    change={`${stats?.quotes_per_day || 0} quotes/day`} 
                    icon={DollarSign} 
                    trend="up" 
                />
                <StatCard 
                    title="Quotes Generated" 
                    value={stats?.total_quotes || 0} 
                    change={`${stats?.processed_emails || 0} emails processed`} 
                    icon={FileText} 
                    trend="up" 
                />
                <StatCard 
                    title="Time Saved" 
                    value={`${stats?.time_saved_hours || 0}h`} 
                    change={`${stats?.time_saved_minutes || 0} minutes saved`} 
                    icon={Clock} 
                    trend="up" 
                />
                <StatCard 
                    title="Quote Velocity" 
                    value={`${stats?.quotes_per_day || 0}/day`} 
                    change={`${stats?.time_saved_minutes ? Math.round(stats.time_saved_minutes / (stats.total_quotes || 1)) : 0} min/quote`} 
                    icon={Zap} 
                    trend="up" 
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    {/* Win-Rate Predictor */}
                    <div className="glass-panel rounded-2xl p-6">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                    <Target size={20} className="text-blue-400" />
                                    High-Probability Quotes
                                </h2>
                                <p className="text-sm text-slate-400 mt-1">Quotes with highest win probability</p>
                            </div>
                            <Link to="/quotes" className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
                                View all <ArrowUpRight size={14} />
                            </Link>
                        </div>
                        {highProbabilityQuotes.length > 0 ? (
                            <div className="space-y-3">
                                {highProbabilityQuotes.map((quote) => (
                                    <Link
                                        key={quote.id}
                                        to={`/quotes/${quote.id}`}
                                        className="block p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-blue-500/50 transition-colors group"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <span className="text-sm font-medium text-white">{quote.quote_number}</span>
                                                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                                        {(quote.winProbability * 100).toFixed(0)}% Win Rate
                                                    </span>
                                                </div>
                                                <div className="text-xs text-slate-400">
                                                    ${quote.total_amount?.toFixed(2) || '0.00'} • {quote.items?.length || 0} items
                                                </div>
                                            </div>
                                            <ArrowUpRight size={16} className="text-slate-600 group-hover:text-blue-400 transition-colors" />
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8 text-slate-500 text-sm">
                                No high-probability quotes found. Create quotes to see predictions.
                            </div>
                        )}
                    </div>

                    {/* Recent Quotes */}
                    <div className="glass-panel rounded-2xl p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-semibold text-white">Recent Quotes</h2>
                            <Link to="/quotes" className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
                                View all <ArrowUpRight size={14} />
                            </Link>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead>
                                    <tr className="border-b border-slate-800 text-slate-400">
                                        <th className="pb-3 pl-4">Quote #</th>
                                        <th className="pb-3">Customer</th>
                                        <th className="pb-3">Date</th>
                                        <th className="pb-3">Amount</th>
                                        <th className="pb-3">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/50">
                                    {quotes.slice(0, 5).map((quote) => (
                                        <tr key={quote.id} className="group hover:bg-slate-800/30 transition-colors">
                                            <td className="py-4 pl-4 font-medium text-slate-200">
                                                <Link to={`/quotes/${quote.id}`} className="hover:text-primary-400">
                                                    {quote.quote_number}
                                                </Link>
                                            </td>
                                            <td className="py-4 text-slate-400">
                                                {quote.customers?.name || quote.metadata?.source_sender || 'N/A'}
                                            </td>
                                            <td className="py-4 text-slate-400">
                                                {new Date(quote.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="py-4 text-slate-200 font-medium">
                                                ${quote.total_amount?.toFixed(2) || '0.00'}
                                            </td>
                                            <td className="py-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                    quote.status === 'draft' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                                                    quote.status === 'sent' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                                                    quote.status === 'accepted' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                                    'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                                                }`}>
                                                    {quote.status.replace('_', ' ')}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                    {quotes.length === 0 && (
                                        <tr>
                                            <td colSpan={5} className="text-center py-8 text-slate-500">
                                                No quotes yet. Create your first quote to get started.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="glass-panel rounded-2xl p-6">
                        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
                        <div className="space-y-3">
                            <Link to="/customers" className="w-full glass-card p-4 rounded-xl flex items-center gap-3 text-left group">
                                <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg group-hover:bg-purple-500/30 transition-colors">
                                    <Users size={18} />
                                </div>
                                <div>
                                    <span className="block text-slate-200 font-medium">Add Customer</span>
                                    <span className="text-xs text-slate-500">Create new client profile</span>
                                </div>
                                <ArrowUpRight size={16} className="ml-auto text-slate-600 group-hover:text-slate-400 transition-colors" />
                            </Link>
                            <Link to="/products" className="w-full glass-card p-4 rounded-xl flex items-center gap-3 text-left group">
                                <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                                    <ShoppingBag size={18} />
                                </div>
                                <div>
                                    <span className="block text-slate-200 font-medium">Browse Catalog</span>
                                    <span className="text-xs text-slate-500">Check product availability</span>
                                </div>
                                <ArrowUpRight size={16} className="ml-auto text-slate-600 group-hover:text-slate-400 transition-colors" />
                            </Link>
                        </div>
                    </div>

                    {/* Quote Velocity Card */}
                    {stats && (
                        <div className="glass-panel rounded-2xl p-6 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                            <div className="flex items-center gap-3 mb-4">
                                <Zap size={20} className="text-blue-400" />
                                <h3 className="text-lg font-semibold text-white">Quote Velocity</h3>
                            </div>
                            <div className="space-y-3">
                                <div>
                                    <div className="text-3xl font-bold text-white mb-1">
                                        {stats.time_saved_minutes ? Math.round(stats.time_saved_minutes / (stats.total_quotes || 1)) : 0} min
                                    </div>
                                    <div className="text-xs text-slate-400">Average time per quote</div>
                                </div>
                                <div className="pt-3 border-t border-slate-700/50">
                                    <div className="text-sm text-slate-300 mb-1">Time Saved vs Human Average</div>
                                    <div className="text-lg font-semibold text-blue-400">
                                        {stats.time_saved_hours || 0} hours saved
                                    </div>
                                    <div className="text-xs text-slate-500 mt-1">
                                        Human average: 30 min/quote • AI-assisted: 5 min/quote
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
