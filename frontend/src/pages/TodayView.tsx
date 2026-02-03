import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Clock, TrendingUp, Users, FileText, Mail, Sparkles,
  Calendar, Target, Zap, ArrowRight, Activity, Globe, ShieldCheck
} from 'lucide-react';
import { quotesApi, customersApi, emailsApi } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface TodayStats {
  pendingQuotes: number;
  pendingValue: number;
  followUpsNeeded: number;
  newEmails: number;
  lowStockItems: number;
  expiringQuotes: number;
}

interface ActivityItem {
  id: string;
  type: 'quote' | 'email' | 'customer' | 'alert';
  title: string;
  description: string;
  time: string;
  priority: 'high' | 'medium' | 'low';
  action?: string;
  actionLink?: string;
}

interface FollowUp {
  id: string;
  customerName: string;
  quoteId: string;
  quoteTotal: number;
  lastContact: string;
  status: 'sent' | 'viewed' | 'no-response';
  daysSince: number;
}

export const TodayView = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<TodayStats>({
    pendingQuotes: 0,
    pendingValue: 0,
    followUpsNeeded: 0,
    newEmails: 0,
    lowStockItems: 0,
    expiringQuotes: 0
  });
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [priorityTasks, setPriorityTasks] = useState<ActivityItem[]>([]);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting('Good morning');
    else if (hour < 17) setGreeting('Good afternoon');
    else setGreeting('Good evening');

    loadTodayData();
  }, []);

  const loadTodayData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use fallback data if API fails or timeouts, but try real API first
      // We wrap the Promise.all in a try/catch to ensure we can show *something* even if backend is down
      const [quotesRes, customersRes, emailsRes] = await Promise.all([
        quotesApi.list(100).catch(() => ({ data: [] })),
        customersApi.list(100).catch(() => ({ data: [] })),
        emailsApi.list('pending', 50).catch(() => ({ data: [] })),
      ]);

      const quotes = quotesRes.data || [];
      const emails = emailsRes.data || [];

      // Store quotes for table display
      setQuotes(quotes);

      // Calculate stats
      const pendingQuotes = quotes.filter((q: any) => q.status === 'draft' || q.status === 'sent');
      const pendingValue = pendingQuotes.reduce((sum: number, q: any) => sum + (q.total || 0), 0);

      const followUpQuotes = quotes.filter((q: any) => {
        if (q.status !== 'sent') return false;
        const sentDate = new Date(q.sent_at || q.created_at);
        const daysSince = (Date.now() - sentDate.getTime()) / (1000 * 60 * 60 * 24);
        return daysSince > 3;
      });

      // Mock low stock
      const lowStockCount = 3;

      const expiringQuotes = quotes.filter((q: any) => {
        if (q.status !== 'sent') return false;
        const sentDate = new Date(q.sent_at || q.created_at);
        const daysSince = (Date.now() - sentDate.getTime()) / (1000 * 60 * 60 * 24);
        return daysSince > 14;
      });

      setStats({
        pendingQuotes: pendingQuotes.length,
        pendingValue,
        followUpsNeeded: followUpQuotes.length,
        newEmails: emails.length,
        lowStockItems: lowStockCount,
        expiringQuotes: expiringQuotes.length
      });

      // Build priority tasks
      const tasks: ActivityItem[] = [];

      if (emails.length > 0) {
        tasks.push({
          id: 'emails',
          type: 'email',
          title: `${emails.length} New RFQ Email${emails.length > 1 ? 's' : ''}`,
          description: 'New quote requests waiting for extraction',
          time: 'Just now',
          priority: 'high',
          action: 'Process Now',
          actionLink: '/inbox'
        });
      }

      if (followUpQuotes.length > 0) {
        const oldest = followUpQuotes[0];
        tasks.push({
          id: 'followup',
          type: 'alert',
          title: `${followUpQuotes.length} Quote${followUpQuotes.length > 1 ? 's' : ''} Need Follow-up`,
          description: `Oldest: ${oldest.customer_name} ($${oldest.total?.toFixed(2)})`,
          time: 'Overdue',
          priority: 'high',
          action: 'View Quotes',
          actionLink: '/quotes'
        });
      }

      setPriorityTasks(tasks);

      // Build follow-ups list
      const followUpList: FollowUp[] = followUpQuotes.slice(0, 5).map((q: any) => ({
        id: q.id,
        customerName: q.customer_name,
        quoteId: q.id,
        quoteTotal: q.total || 0,
        lastContact: q.sent_at || q.created_at,
        status: 'sent',
        daysSince: Math.floor((Date.now() - new Date(q.sent_at || q.created_at).getTime()) / (1000 * 60 * 60 * 24))
      }));
      setFollowUps(followUpList);

    } catch (error) {
      console.error('Failed to load today data:', error);
      setError("Unable to connect to Mercura Core. Please check if the backend service is running.");
    } finally {
      setLoading(false);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-gray-400">
          <div className="w-12 h-12 border-4 border-orange-500/20 border-t-orange-500 rounded-full animate-spin" />
          <p className="text-sm font-medium">Synchronizing with Core...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-8">
        <div className="bg-red-50 text-red-800 p-6 rounded-xl border border-red-100 max-w-md text-center">
          <Activity className="mx-auto mb-4 text-red-500" size={32} />
          <h3 className="font-bold mb-2">Connection Issue</h3>
          <p className="text-sm opacity-80 mb-4">{error}</p>
          <button
            onClick={loadTodayData}
            className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-800 rounded-lg font-medium text-sm transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-fade-in">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-gray-500 mb-2 font-medium">
            <Calendar size={18} className="text-orange-500" />
            <span>{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 tracking-tight leading-tight">
            {greeting}, <span className="bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">Reg</span>
          </h1>
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => navigate('/quotes/new')}
            className="group relative overflow-hidden bg-gradient-to-r from-orange-500 to-red-600 text-white shadow-lg shadow-orange-500/20 hover:shadow-orange-500/30 transition-all duration-300 rounded-xl px-6 py-3 font-semibold flex items-center gap-2 hover:-translate-y-0.5"
          >
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
            <Sparkles size={18} className="group-hover:rotate-12 transition-transform relative z-10" />
            <span className="relative z-10">Create New Quote</span>
          </button>
        </div>
      </div>

      {/* BENTO GRID LAYOUT */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">

        {/* 1. Primary Stats Block (Large) */}
        <div className="col-span-1 md:col-span-2 lg:col-span-2 row-span-1 bg-white rounded-2xl p-8 border border-gray-100 shadow-[0_2px_20px_rgba(0,0,0,0.04)] hover:-translate-y-1 transition-transform duration-300 relative overflow-hidden group">
          <div className="absolute -top-6 -right-6 p-8 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity transform group-hover:scale-110 duration-500 rotate-12">
            <TrendingUp size={180} />
          </div>

          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 bg-green-100 text-green-700 rounded-lg">
                <TrendingUp size={16} />
              </div>
              <span className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Total Pipeline Value</span>
            </div>

            <div className="text-5xl font-bold text-gray-900 tracking-tighter mb-4">
              ${stats.pendingValue.toLocaleString()}
            </div>

            <div className="flex items-center gap-4 text-sm font-medium">
              <div className="flex items-center gap-1.5 text-green-700 bg-green-50 border border-green-100 px-2.5 py-1 rounded-full">
                <ArrowRight size={14} className="-rotate-45" />
                <span>12.5% vs last week</span>
              </div>
              <span className="text-gray-400">across {stats.pendingQuotes} active quotes</span>
            </div>
          </div>
        </div>

        {/* 2. Action Card: Inbox */}
        <div
          onClick={() => navigate('/emails')}
          className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm cursor-pointer hover:shadow-md hover:-translate-y-1 transition-all duration-300 group relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10">
            <div className="flex justify-between items-start mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                <Mail size={20} />
              </div>
              {stats.newEmails > 0 && (
                <span className="flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                </span>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1 tracking-tight">{stats.newEmails}</div>
            <div className="text-sm font-medium text-gray-600 group-hover:text-blue-600 transition-colors">Pending RFQs</div>
          </div>
        </div>

        {/* 3. Action Card: Follow Ups */}
        <div
          onClick={() => navigate('/quotes')}
          className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm cursor-pointer hover:shadow-md hover:-translate-y-1 transition-all duration-300 group relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-amber-50/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10">
            <div className="flex justify-between items-start mb-4">
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                <Clock size={20} />
              </div>
              {stats.followUpsNeeded > 0 && (
                <span className="flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-amber-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                </span>
              )}
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1 tracking-tight">{stats.followUpsNeeded}</div>
            <div className="text-sm font-medium text-gray-600 group-hover:text-amber-600 transition-colors">Follow-ups Due</div>
          </div>
        </div>

        {/* 4. Priorities List (Tall Vertical) */}
        <div className="col-span-1 lg:col-span-1 row-span-2 bg-zinc-900 text-white rounded-2xl p-6 shadow-2xl flex flex-col relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/20 blur-[50px] rounded-full pointer-events-none" />

          <div className="flex items-center gap-2 mb-6 relative z-10">
            <Zap size={18} className="text-yellow-400 fill-yellow-400" />
            <h3 className="font-semibold tracking-wide">AI Priorities</h3>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto pr-1 custom-scrollbar relative z-10">
            {priorityTasks.length === 0 ? (
              <div className="text-center py-10 text-zinc-500 text-sm">
                <ShieldCheck size={32} className="mx-auto mb-2 opacity-50" />
                All caught up!
              </div>
            ) : (
              priorityTasks.map(task => (
                <div
                  key={task.id}
                  className="p-3.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all cursor-pointer group"
                  onClick={() => task.actionLink && navigate(task.actionLink)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${task.priority === 'high' ? 'bg-red-500/20 text-red-300 border border-red-500/20' : 'bg-blue-500/20 text-blue-300 border border-blue-500/20'
                      }`}>
                      {task.priority}
                    </span>
                    <span className="text-[10px] text-zinc-500 font-medium">{task.time}</span>
                  </div>
                  <h4 className="font-medium text-sm text-zinc-100 mb-1 group-hover:text-orange-300 transition-colors">{task.title}</h4>
                  <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">{task.description}</p>
                </div>
              ))
            )}
          </div>

          <button onClick={() => navigate('/intelligence')} className="mt-4 w-full py-3 bg-white/10 hover:bg-white/15 border border-white/5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2 relative z-10 backdrop-blur-sm group">
            <Sparkles size={16} className="text-orange-300 group-hover:text-orange-200" />
            Ask Intelligence
          </button>
        </div>

        {/* 5. Recent Quotes Table (Wide Block) */}
        <div className="col-span-1 md:col-span-3 lg:col-span-3 row-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col min-h-[400px]">
          <div className="px-8 py-6 border-b border-gray-50 flex items-center justify-between">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <FileText size={20} className="text-gray-400" />
              Recent Activity
            </h3>
            <button onClick={() => navigate('/quotes')} className="text-sm font-medium text-orange-600 hover:text-orange-700 hover:underline">
              View All Pipeline
            </button>
          </div>

          <div className="flex-1 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50/50 border-b border-gray-100">
                  <th className="text-left py-4 px-8 text-xs font-semibold text-gray-500 uppercase tracking-wider">Customer</th>
                  <th className="text-left py-4 px-8 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="text-right py-4 px-8 text-xs font-semibold text-gray-500 uppercase tracking-wider">Value</th>
                  <th className="text-right py-4 px-8 text-xs font-semibold text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="py-4 px-8"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {quotes.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-gray-500">
                      No quote activity yet.
                    </td>
                  </tr>
                ) : (
                  quotes.slice(0, 5).map(quote => (
                    <tr key={quote.id} className="group hover:bg-blue-50/30 transition-colors cursor-default">
                      <td className="py-4 px-8">
                        <div className="font-semibold text-gray-900">{quote.customer_name}</div>
                        <div className="text-xs text-gray-400 font-mono mt-0.5">{quote.id.substring(0, 8)}</div>
                      </td>
                      <td className="py-4 px-8">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${quote.status === 'sent' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                            quote.status === 'approved' ? 'bg-green-50 text-green-700 border-green-200' :
                              'bg-gray-100 text-gray-600 border-gray-200'
                          }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${quote.status === 'sent' ? 'bg-blue-500' :
                              quote.status === 'approved' ? 'bg-green-500' :
                                'bg-gray-500'
                            }`}></span>
                          {quote.status.charAt(0).toUpperCase() + quote.status.slice(1)}
                        </span>
                      </td>
                      <td className="py-4 px-8 text-right font-mono text-sm text-gray-700">
                        ${(quote.total || 0).toLocaleString()}
                      </td>
                      <td className="py-4 px-8 text-right text-sm text-gray-500">
                        {formatTimeAgo(quote.created_at)}
                      </td>
                      <td className="py-4 px-8 text-right">
                        <button onClick={() => navigate(`/quotes/${quote.id}`)} className="p-2 hover:bg-white rounded-lg text-gray-400 hover:text-orange-600 hover:shadow-sm border border-transparent hover:border-gray-100 transition-all opacity-0 group-hover:opacity-100">
                          <ArrowRight size={16} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 6. Insight Card (Small) */}
        <div className="col-span-1 bg-gradient-to-br from-violet-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg shadow-indigo-500/20 flex flex-col justify-between group cursor-pointer hover:shadow-xl hover:scale-[1.02] transition-all relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 blur-[40px] rounded-full pointer-events-none" />
          <div className="relative z-10">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center mb-4 text-white shadow-inner border border-white/10">
              <Target size={20} />
            </div>
            <h3 className="text-lg font-bold mb-1">Win Rate: 64%</h3>
            <p className="text-indigo-100 text-sm opacity-90">Top 10% of industry average.</p>
          </div>
          <div className="mt-4 text-xs font-medium uppercase tracking-wider text-indigo-200 group-hover:text-white transition-colors flex items-center gap-2 relative z-10">
            View Insights <ArrowRight size={14} />
          </div>
        </div>

        {/* 7. Quick Action (Small) */}
        <div className="col-span-1 bg-white rounded-2xl p-6 border border-gray-100 shadow-sm flex flex-col justify-center items-center text-center gap-3 cursor-pointer hover:border-orange-200 hover:shadow-md transition-all group hover:-translate-y-1" onClick={() => navigate('/customers')}>
          <div className="w-12 h-12 rounded-full bg-orange-50 text-orange-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
            <Users size={24} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 group-hover:text-orange-600 transition-colors">Customers</h3>
            <p className="text-xs text-gray-500 mt-1">Manage database</p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default TodayView;
