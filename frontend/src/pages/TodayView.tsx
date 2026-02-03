import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardList, Clock, AlertCircle, CheckCircle2, TrendingUp,
  Users, FileText, Mail, Phone, ArrowRight, Sparkles,
  Calendar, DollarSign, Package, Target, Zap, Bell, Camera, BarChart3, ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react';
import { quotesApi, customersApi, productsApi, emailsApi } from '../services/api';

interface TodayStats {
  pendingQuotes: number;
  pendingValue: number;
  followUpsNeeded: number;
  newEmails: number;
  lowStockItems: number;
  expiringQuotes: number;
}

interface Activity {
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
  const [activities, setActivities] = useState<Activity[]>([]);
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [priorityTasks, setPriorityTasks] = useState<Activity[]>([]);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
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
    try {
      // Load all data in parallel
      const [quotesRes, customersRes, emailsRes] = await Promise.all([
        quotesApi.list(100),
        customersApi.list(100),
        emailsApi.list('pending', 50),
      ]);

      const quotes = quotesRes.data || [];
      const customers = customersRes.data || [];
      const emails = emailsRes.data || [];

      // Store quotes for table display
      setQuotes(quotes);

      // Calculate stats
      const pendingQuotes = quotes.filter((q: any) => q.status === 'draft' || q.status === 'sent');
      const pendingValue = pendingQuotes.reduce((sum: number, q: any) => sum + (q.total || 0), 0);

      // Find quotes needing follow-up (sent > 3 days ago, no response)
      const followUpQuotes = quotes.filter((q: any) => {
        if (q.status !== 'sent') return false;
        const sentDate = new Date(q.sent_at || q.created_at);
        const daysSince = (Date.now() - sentDate.getTime()) / (1000 * 60 * 60 * 24);
        return daysSince > 3;
      });

      // Mock low stock (would come from products API)
      const lowStockCount = 3;

      // Expiring quotes (quotes sent > 14 days ago)
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
      const tasks: Activity[] = [];

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
          description: `Oldest: ${oldest.customer_name} ($${oldest.total?.toFixed(2)}) - ${Math.floor((Date.now() - new Date(oldest.sent_at || oldest.created_at).getTime()) / (1000 * 60 * 60 * 24))} days`,
          time: 'Overdue',
          priority: 'high',
          action: 'View Quotes',
          actionLink: '/quotes'
        });
      }

      if (expiringQuotes.length > 0) {
        tasks.push({
          id: 'expiring',
          type: 'alert',
          title: `${expiringQuotes.length} Quote${expiringQuotes.length > 1 ? 's' : ''} Expiring Soon`,
          description: 'Quotes sent >14 days ago may need renewal',
          time: 'Action needed',
          priority: 'medium',
          action: 'Review',
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

      // Build recent activity
      const recentActivity: Activity[] = [
        ...quotes.slice(0, 3).map((q: any) => ({
          id: q.id,
          type: 'quote' as const,
          title: `Quote ${q.status === 'draft' ? 'Created' : 'Sent'}`,
          description: `${q.customer_name} - $${q.total?.toFixed(2)}`,
          time: formatTimeAgo(q.created_at),
          priority: 'low' as const
        })),
        ...emails.slice(0, 2).map((e: any) => ({
          id: e.id,
          type: 'email' as const,
          title: 'RFQ Received',
          description: e.subject || 'New quote request',
          time: formatTimeAgo(e.received_at),
          priority: 'medium' as const
        }))
      ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 5);

      setActivities(recentActivity);

    } catch (error) {
      console.error('Failed to load today data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays} days ago`;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-700 border-red-200';
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'quote': return <FileText size={16} className="text-blue-600" />;
      case 'email': return <Mail size={16} className="text-purple-600" />;
      case 'customer': return <Users size={16} className="text-green-600" />;
      case 'alert': return <AlertCircle size={16} className="text-red-600" />;
      default: return <Bell size={16} className="text-gray-600" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-500">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-orange-500 border-t-transparent"></div>
          Loading your day...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">{greeting}, Reg</h1>
              <p className="text-gray-600 mt-1">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/quotes/new')}
                className="flex items-center gap-2 px-5 py-2.5 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors"
              >
                <Sparkles size={18} />
                Create Quote
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">

        {/* Stats Row - Condensed for simplicity */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <FileText size={14} />
              Pending Quotes
            </div>
            <div className="text-2xl font-bold text-gray-900">{stats.pendingQuotes}</div>
            <div className="text-sm text-gray-500">${stats.pendingValue.toLocaleString()}</div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <Clock size={14} />
              Follow-ups
            </div>
            <div className={`text-2xl font-bold ${stats.followUpsNeeded > 0 ? 'text-amber-600' : 'text-gray-900'}`}>
              {stats.followUpsNeeded}
            </div>
            <div className="text-sm text-gray-500">Need attention</div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <Mail size={14} />
              New RFQs
            </div>
            <div className={`text-2xl font-bold ${stats.newEmails > 0 ? 'text-blue-600' : 'text-gray-900'}`}>
              {stats.newEmails}
            </div>
            <div className="text-sm text-gray-500">To process</div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <TrendingUp size={14} />
              Win Rate
            </div>
            <div className="text-2xl font-bold text-green-600">64%</div>
            <div className="text-sm text-gray-500">This month</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Live Quotes & RFQs Table */}
          <div className="lg:col-span-2 space-y-6">
            {/* Smart Alerts - Compact */}
            {priorityTasks.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <Bell className="text-orange-500" size={18} />
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-gray-900">Smart Alerts</h3>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {priorityTasks.map((task) => (
                        <button
                          key={task.id}
                          onClick={() => task.actionLink && navigate(task.actionLink)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-orange-50 text-orange-700 text-xs font-medium rounded-lg hover:bg-orange-100 transition-colors"
                        >
                          {getTypeIcon(task.type)}
                          {task.title}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Live Quotes & RFQs Table */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="text-gray-700" size={20} />
                    <h2 className="font-semibold text-gray-900">Active Quotes & RFQs</h2>
                  </div>
                  <button
                    onClick={() => navigate('/quotes')}
                    className="text-sm text-orange-600 hover:text-orange-700 font-medium"
                  >
                    View All
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Customer</th>
                      <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Value</th>
                      <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Age</th>
                      <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {quotes.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-5 py-8 text-center text-gray-500">
                          No active quotes. Create your first quote to get started.
                        </td>
                      </tr>
                    ) : (
                      quotes.slice(0, 10).map((quote: any) => (
                        <tr key={quote.id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-5 py-3">
                            <div className="font-medium text-gray-900">{quote.customer_name}</div>
                            <div className="text-xs text-gray-500">ID: {quote.id.slice(0, 8)}</div>
                          </td>
                          <td className="px-5 py-3">
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${quote.status === 'sent' ? 'bg-blue-100 text-blue-700' :
                                quote.status === 'draft' ? 'bg-gray-100 text-gray-700' :
                                  'bg-green-100 text-green-700'
                              }`}>
                              {quote.status}
                            </span>
                          </td>
                          <td className="px-5 py-3 text-right font-semibold text-gray-900">
                            ${quote.total?.toLocaleString() || '0'}
                          </td>
                          <td className="px-5 py-3 text-sm text-gray-600">
                            {formatTimeAgo(quote.created_at)}
                          </td>
                          <td className="px-5 py-3 text-right">
                            <button
                              onClick={() => navigate(`/quotes/${quote.id}`)}
                              className="inline-flex items-center gap-1 text-sm font-medium text-orange-600 hover:text-orange-700"
                            >
                              View
                              <ArrowRight size={14} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Follow-ups - Compact */}
            {followUps.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-900">Needs Follow-up</h3>
                    <button
                      onClick={() => navigate('/quotes')}
                      className="text-xs text-orange-600 hover:text-orange-700 font-medium"
                    >
                      View All
                    </button>
                  </div>
                </div>
                <div className="divide-y divide-gray-100">
                  {followUps.slice(0, 3).map((followUp) => (
                    <div key={followUp.id} className="px-5 py-3 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 text-sm font-medium">
                            {followUp.customerName.charAt(0)}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-900">{followUp.customerName}</div>
                            <div className="text-xs text-gray-500">
                              ${followUp.quoteTotal.toLocaleString()} • {followUp.daysSince}d ago
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => navigate(`/quotes/${followUp.quoteId}`)}
                          className="px-3 py-1 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-md transition-colors"
                        >
                          Follow Up
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Insights & Stats */}
          <div className="space-y-6">
            {/* Quick Links - Minimal */}
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Links</h3>
              <div className="space-y-1">
                <button
                  onClick={() => navigate('/emails')}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <span>Process RFQs</span>
                  <ArrowRight size={14} className="text-gray-400" />
                </button>
                <button
                  onClick={() => navigate('/customers')}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <span>Customer List</span>
                  <ArrowRight size={14} className="text-gray-400" />
                </button>
                <button
                  onClick={() => navigate('/intelligence')}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <span>Analytics</span>
                  <ArrowRight size={14} className="text-gray-400" />
                </button>
              </div>
            </div>

            {/* Today's Insight - Subtle */}
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <TrendingUp className="text-blue-600" size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-1">Today's Insight</h3>
                  <p className="text-xs text-gray-600">
                    You have {stats.pendingQuotes} pending quotes worth ${stats.pendingValue.toLocaleString()}.
                    Following up on quotes &gt;3 days old could increase your win rate by 23%.
                  </p>
                </div>
              </div>
            </div>

            {/* This Week's Goals */}
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h2 className="font-semibold text-gray-900 mb-4">This Week's Goals</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Quotes Sent</span>
                    <span className="font-medium text-gray-900">12 / 20</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: '60%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Quote Value</span>
                    <span className="font-medium text-gray-900">$45K / $100K</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 rounded-full" style={{ width: '45%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Win Rate</span>
                    <span className="font-medium text-gray-900">64% / 70%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-500 rounded-full" style={{ width: '91%' }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h2 className="font-semibold text-gray-900 mb-4">This Month</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Quotes Sent</span>
                  <span className="font-semibold text-gray-900">47</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Total Value</span>
                  <span className="font-semibold text-gray-900">$284,500</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Avg Response</span>
                  <span className="font-semibold text-gray-900">2.3 days</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">New Customers</span>
                  <span className="font-semibold text-gray-900">8</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TodayView;
