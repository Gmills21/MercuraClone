import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Bell, Check, Trash2, Mail, Clock, AlertTriangle,
  CheckCheck, RefreshCw, Filter, Settings
} from 'lucide-react';
import { api } from '../services/api';

interface Alert {
  id: string;
  type: string;
  priority: 'high' | 'medium';
  title: string;
  message: string;
  created_at: string;
  read: boolean;
  action_link?: string;
  action_text?: string;
}

// Only 3 essential alert types
const alertTypes = [
  { id: 'new_rfq', name: 'New Quote Request', icon: Mail, color: 'text-blue-600', bg: 'bg-blue-100', desc: 'New RFQ email received' },
  { id: 'follow_up_needed', name: 'Follow-up Needed', icon: Clock, color: 'text-amber-600', bg: 'bg-amber-100', desc: 'Quote sent 3-7 days ago, no response' },
  { id: 'quote_expiring', name: 'Quote Expiring', icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-100', desc: 'Quote expires in 7 days' },
];

export const AlertsPage = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread' | 'high' | 'medium' | 'low'>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.get('/alerts/');
      setAlerts(res.data.alerts);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (alertId: string) => {
    try {
      await api.post(`/alerts/${alertId}/read`);
      setAlerts(alerts.map(a => a.id === alertId ? { ...a, read: true } : a));
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('/alerts/mark-all-read');
      setAlerts(alerts.map(a => ({ ...a, read: true })));
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const dismissAlert = async (alertId: string) => {
    try {
      await api.delete(`/alerts/${alertId}`);
      setAlerts(alerts.filter(a => a.id !== alertId));
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  };

  const runAlertCheck = async () => {
    setLoading(true);
    try {
      await api.post('/alerts/check');
      await loadAlerts();
    } catch (err) {
      console.error('Failed to run alert check:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'unread' && alert.read) return false;
    if (filter !== 'all' && filter !== 'unread' && alert.priority !== filter) return false;
    if (typeFilter !== 'all' && alert.type !== typeFilter) return false;
    return true;
  });

  const unreadCount = alerts.filter(a => !a.read).length;
  const highPriorityCount = alerts.filter(a => a.priority === 'high' && !a.read).length;

  const getAlertTypeInfo = (type: string) => {
    return alertTypes.find(t => t.id === type) || alertTypes[0];
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-orange-100 rounded-xl">
                <Bell className="text-orange-600" size={28} />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">Smart Alerts</h1>
                <p className="text-gray-600 mt-1">
                  {unreadCount > 0 ? (
                    <span className="text-orange-600 font-medium">
                      {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
                      {highPriorityCount > 0 && ` • ${highPriorityCount} high priority`}
                    </span>
                  ) : (
                    "You're all caught up!"
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={runAlertCheck}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                Check Now
              </button>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <CheckCheck size={18} />
                  Mark All Read
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Filters */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-gray-400" />
              <span className="text-sm font-medium text-gray-700">Filter:</span>
            </div>
            
            <div className="flex items-center gap-2">
              {[
                { id: 'all', label: 'All', count: alerts.length },
                { id: 'unread', label: 'Unread', count: unreadCount },
                { id: 'high', label: 'High Priority', count: alerts.filter(a => a.priority === 'high').length },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setFilter(f.id as any)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                    filter === f.id
                      ? 'bg-orange-100 text-orange-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {f.label}
                  <span className="ml-1.5 text-xs text-gray-400">({f.count})</span>
                </button>
              ))}
            </div>

            <div className="h-6 w-px bg-gray-200" />

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="all">All Types</option>
              {alertTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-orange-500 border-t-transparent"></div>
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="text-center py-12 bg-white border border-gray-200 rounded-xl">
              <Bell className="mx-auto mb-4 text-gray-300" size={48} />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {filter === 'all' ? 'No notifications yet' : 'No matching notifications'}
              </h3>
              <p className="text-gray-500 max-w-md mx-auto">
                {filter === 'all' 
                  ? "We'll notify you about important events like new RFQs, follow-up reminders, and quote expirations."
                  : "Try adjusting your filters to see more notifications."
                }
              </p>
            </div>
          ) : (
            filteredAlerts.map((alert) => {
              const typeInfo = getAlertTypeInfo(alert.type);
              const Icon = typeInfo.icon;
              
              return (
                <div
                  key={alert.id}
                  className={`bg-white border rounded-xl p-5 transition-all hover:shadow-md ${
                    alert.read 
                      ? 'border-gray-200 opacity-60' 
                      : 'border-l-4 border-l-orange-500 border-gray-200 shadow-sm'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className={`p-3 rounded-lg ${typeInfo.bg} flex-shrink-0`}>
                      <Icon className={typeInfo.color} size={22} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                            {!alert.read && (
                              <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs font-medium rounded-full">
                                New
                              </span>
                            )}
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                              alert.priority === 'high' ? 'bg-red-100 text-red-700' :
                              alert.priority === 'medium' ? 'bg-amber-100 text-amber-700' :
                              'bg-blue-100 text-blue-700'
                            }`}>
                              {alert.priority}
                            </span>
                          </div>
                          <p className="text-gray-600">{alert.message}</p>
                          <p className="text-sm text-gray-400 mt-2">{formatTime(alert.created_at)}</p>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                          {alert.action_link && (
                            <button
                              onClick={() => navigate(alert.action_link!)}
                              className="px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700 transition-colors"
                            >
                              {alert.action_text || 'View'}
                            </button>
                          )}
                          {!alert.read && (
                            <button
                              onClick={() => markAsRead(alert.id)}
                              className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                              title="Mark as read"
                            >
                              <Check size={18} />
                            </button>
                          )}
                          <button
                            onClick={() => dismissAlert(alert.id)}
                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Dismiss"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Alert Types Info */}
        <div className="mt-8 bg-gray-50 border border-gray-200 rounded-xl p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Settings size={18} />
            Alert Types
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {alertTypes.map((type) => {
              const Icon = type.icon;
              const count = alerts.filter(a => a.type === type.id).length;
              
              return (
                <div key={type.id} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
                  <div className={`p-2 rounded-lg ${type.bg}`}>
                    <Icon className={type.color} size={16} />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{type.name}</p>
                    <p className="text-xs text-gray-500">{count} alerts</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertsPage;
