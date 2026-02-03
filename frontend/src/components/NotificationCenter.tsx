import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Bell, X, Check, CheckCheck, Mail, Clock, AlertTriangle, Trash2
} from 'lucide-react';
import { api } from '../services/api';

interface Alert {
  id: string;
  type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  message: string;
  created_at: string;
  read: boolean;
  action_link?: string;
  action_text?: string;
}

export const NotificationCenter = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load alerts on mount and when opened
  useEffect(() => {
    loadUnreadCount();
    
    // Check for new alerts every 30 seconds
    const interval = setInterval(() => {
      loadUnreadCount();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadAlerts();
    }
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadUnreadCount = async () => {
    try {
      const res = await api.get('/alerts/unread-count');
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      console.error('Failed to load unread count:', err);
    }
  };

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.get('/alerts/');
      setAlerts(res.data.alerts);
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (alertId: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      await api.post(`/alerts/${alertId}/read`);
      setAlerts(alerts.map(a => a.id === alertId ? { ...a, read: true } : a));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('/alerts/mark-all-read');
      setAlerts(alerts.map(a => ({ ...a, read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const dismissAlert = async (alertId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/alerts/${alertId}`);
      const alert = alerts.find(a => a.id === alertId);
      setAlerts(alerts.filter(a => a.id !== alertId));
      if (alert && !alert.read) {
        setUnreadCount(Math.max(0, unreadCount - 1));
      }
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  };

  const handleAlertClick = (alert: Alert) => {
    if (!alert.read) {
      markAsRead(alert.id);
    }
    if (alert.action_link) {
      navigate(alert.action_link);
      setIsOpen(false);
    }
  };

  const getAlertIcon = (type: string) => {
    // Only 3 essential alert types - keeping it simple
    switch (type) {
      case 'new_rfq':
        return <Mail size={18} className="text-blue-600" />;
      case 'follow_up_needed':
        return <Clock size={18} className="text-amber-600" />;
      case 'quote_expiring':
        return <AlertTriangle size={18} className="text-red-600" />;
      default:
        return <Bell size={18} className="text-gray-600" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-500';
      case 'medium':
        return 'bg-amber-500';
      case 'low':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatTime = (dateString: string) => {
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
    return `${diffDays}d ago`;
  };

  const unreadAlerts = alerts.filter(a => !a.read);
  const readAlerts = alerts.filter(a => a.read);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <Bell size={22} />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-xl shadow-2xl border border-gray-200 z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2">
              <Bell size={18} className="text-gray-600" />
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded-full">
                  {unreadCount} new
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
                  title="Mark all as read"
                >
                  <CheckCheck size={16} />
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Alerts List */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-orange-500 border-t-transparent"></div>
              </div>
            ) : alerts.length === 0 ? (
              <div className="text-center py-8 px-4">
                <Bell className="mx-auto mb-3 text-gray-300" size={40} />
                <p className="text-gray-500">No notifications yet</p>
                <p className="text-sm text-gray-400 mt-1">
                  We'll notify you about important events
                </p>
              </div>
            ) : (
              <>
                {/* Unread Alerts */}
                {unreadAlerts.length > 0 && (
                  <div className="bg-blue-50/50">
                    <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      New
                    </div>
                    {unreadAlerts.map((alert) => (
                      <div
                        key={alert.id}
                        onClick={() => handleAlertClick(alert)}
                        className="relative px-4 py-3 hover:bg-blue-50 cursor-pointer border-l-4 border-blue-500 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-white rounded-lg shadow-sm">
                            {getAlertIcon(alert.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <h4 className="font-medium text-gray-900 text-sm">
                                {alert.title}
                              </h4>
                              <span className="text-xs text-gray-400 whitespace-nowrap">
                                {formatTime(alert.created_at)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-0.5 line-clamp-2">
                              {alert.message}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              {alert.action_text && (
                                <span className="text-xs font-medium text-orange-600">
                                  {alert.action_text} →
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1 absolute top-2 right-2 opacity-0 hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => markAsRead(alert.id, e)}
                            className="p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded"
                            title="Mark as read"
                          >
                            <Check size={14} />
                          </button>
                          <button
                            onClick={(e) => dismissAlert(alert.id, e)}
                            className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                            title="Dismiss"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Read Alerts */}
                {readAlerts.length > 0 && (
                  <div>
                    <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Earlier
                    </div>
                    {readAlerts.map((alert) => (
                      <div
                        key={alert.id}
                        onClick={() => handleAlertClick(alert)}
                        className="relative px-4 py-3 hover:bg-gray-50 cursor-pointer border-l-4 border-transparent transition-colors opacity-60"
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-gray-100 rounded-lg">
                            {getAlertIcon(alert.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <h4 className="font-medium text-gray-900 text-sm">
                                {alert.title}
                              </h4>
                              <span className="text-xs text-gray-400 whitespace-nowrap">
                                {formatTime(alert.created_at)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-0.5 line-clamp-2">
                              {alert.message}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={(e) => dismissAlert(alert.id, e)}
                          className="absolute top-2 right-2 p-1 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded opacity-0 hover:opacity-100 transition-opacity"
                          title="Dismiss"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
            <button
              onClick={() => {
                navigate('/alerts');
                setIsOpen(false);
              }}
              className="w-full text-center text-sm text-gray-600 hover:text-gray-900 font-medium"
            >
              View all notifications →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;
