/**
 * Alerts Page - Smart notifications for actionable items
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    Bell, CheckCircle, Mail, Clock, AlertTriangle, 
    RefreshCw, Loader2, X, ArrowRight, Inbox
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { alertsApi } from '../services/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface Alert {
    id: string;
    type: string;
    priority: 'high' | 'medium' | 'low';
    title: string;
    message: string;
    is_read: boolean;
    action_link: string;
    action_text: string;
    created_at: string;
    related_entity_type: string;
    related_entity_id: string;
}

const alertIcons: Record<string, React.ElementType> = {
    new_rfq: Mail,
    follow_up_needed: Clock,
    quote_expiring: AlertTriangle,
};

const alertColors: Record<string, { bg: string; border: string; icon: string }> = {
    new_rfq: { bg: 'bg-blue-50', border: 'border-blue-200', icon: 'text-blue-600' },
    follow_up_needed: { bg: 'bg-amber-50', border: 'border-amber-200', icon: 'text-amber-600' },
    quote_expiring: { bg: 'bg-orange-50', border: 'border-orange-200', icon: 'text-orange-600' },
};

export default function AlertsPage() {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [activeFilter, setActiveFilter] = useState<'all' | 'unread'>('all');
    const [isChecking, setIsChecking] = useState(false);

    // Fetch alerts
    const { data: alertsData, isLoading } = useQuery({
        queryKey: ['alerts', activeFilter],
        queryFn: () => alertsApi.list(activeFilter === 'unread', 50),
        select: (res) => res.data,
    });

    // Fetch unread count (for badge)
    const { data: unreadData } = useQuery({
        queryKey: ['alerts-unread-count'],
        queryFn: () => alertsApi.getUnreadCount(),
        select: (res) => res.data.unread_count,
        refetchInterval: 30000, // Refetch every 30 seconds
    });

    const alerts = alertsData?.alerts || [];
    const unreadCount = unreadData || 0;

    // Mark read mutation
    const markReadMutation = useMutation({
        mutationFn: (alertId: string) => alertsApi.markRead(alertId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
            queryClient.invalidateQueries({ queryKey: ['alerts-unread-count'] });
        },
    });

    // Mark all read mutation
    const markAllReadMutation = useMutation({
        mutationFn: () => alertsApi.markAllRead(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
            queryClient.invalidateQueries({ queryKey: ['alerts-unread-count'] });
        },
    });

    // Dismiss mutation
    const dismissMutation = useMutation({
        mutationFn: (alertId: string) => alertsApi.dismiss(alertId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
            queryClient.invalidateQueries({ queryKey: ['alerts-unread-count'] });
        },
    });

    // Run alert checks
    const handleCheckNow = async () => {
        setIsChecking(true);
        try {
            await alertsApi.check();
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
        } catch (err) {
            console.error('Failed to check alerts:', err);
        } finally {
            setIsChecking(false);
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
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    const handleAlertClick = (alert: Alert) => {
        // Mark as read
        if (!alert.is_read) {
            markReadMutation.mutate(alert.id);
        }
        
        // Navigate if action link exists
        if (alert.action_link) {
            navigate(alert.action_link);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header */}
            <div className="bg-white border-b border-slate-200">
                <div className="max-w-5xl mx-auto px-6 py-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-orange-100 rounded-lg">
                                <Bell className="text-orange-600" size={24} />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
                                <p className="text-slate-600">
                                    {unreadCount > 0 ? (
                                        <span className="flex items-center gap-1">
                                            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                                            {unreadCount} unread alert{unreadCount !== 1 ? 's' : ''}
                                        </span>
                                    ) : (
                                        'All caught up!'
                                    )}
                                </p>
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                            <Button
                                variant="outline"
                                onClick={handleCheckNow}
                                disabled={isChecking}
                                className="gap-2"
                            >
                                {isChecking ? (
                                    <Loader2 className="animate-spin" size={16} />
                                ) : (
                                    <RefreshCw size={16} />
                                )}
                                Check Now
                            </Button>
                            
                            {unreadCount > 0 && (
                                <Button
                                    variant="ghost"
                                    onClick={() => markAllReadMutation.mutate()}
                                    disabled={markAllReadMutation.isPending}
                                    className="gap-2"
                                >
                                    <CheckCircle size={16} />
                                    Mark All Read
                                </Button>
                            )}
                        </div>
                    </div>

                    {/* Filter Tabs */}
                    <div className="flex gap-4 mt-6">
                        <button
                            onClick={() => setActiveFilter('all')}
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                                activeFilter === 'all'
                                    ? 'bg-slate-900 text-white'
                                    : 'text-slate-600 hover:bg-slate-100'
                            }`}
                        >
                            All Alerts
                        </button>
                        <button
                            onClick={() => setActiveFilter('unread')}
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2 ${
                                activeFilter === 'unread'
                                    ? 'bg-slate-900 text-white'
                                    : 'text-slate-600 hover:bg-slate-100'
                            }`}
                        >
                            Unread
                            {unreadCount > 0 && (
                                <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                                    {unreadCount}
                                </span>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Alerts List */}
            <div className="max-w-5xl mx-auto px-6 py-8">
                {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="animate-spin text-orange-500" size={32} />
                    </div>
                ) : alerts.length === 0 ? (
                    <div className="text-center py-16">
                        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Inbox className="text-slate-400" size={32} />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900 mb-1">
                            {activeFilter === 'unread' ? 'No unread alerts' : 'No alerts yet'}
                        </h3>
                        <p className="text-slate-500 mb-4">
                            {activeFilter === 'unread' 
                                ? 'You\'ve read all your alerts!' 
                                : 'Alerts appear when you have new RFQs, need follow-ups, or quotes expiring.'}
                        </p>
                        <Button variant="outline" onClick={handleCheckNow} disabled={isChecking}>
                            {isChecking ? 'Checking...' : 'Check for New Alerts'}
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {alerts.map((alert: Alert) => {
                            const Icon = alertIcons[alert.type] || Bell;
                            const colors = alertColors[alert.type] || { 
                                bg: 'bg-slate-50', 
                                border: 'border-slate-200',
                                icon: 'text-slate-600'
                            };
                            
                            return (
                                <div
                                    key={alert.id}
                                    onClick={() => handleAlertClick(alert)}
                                    className={`group relative p-4 rounded-xl border cursor-pointer transition-all ${
                                        alert.is_read
                                            ? 'bg-white border-slate-200 hover:border-slate-300'
                                            : `${colors.bg} ${colors.border} border-2 hover:shadow-md`
                                    }`}
                                >
                                    <div className="flex items-start gap-4">
                                        {/* Icon */}
                                        <div className={`p-2 rounded-lg ${alert.is_read ? 'bg-slate-100' : 'bg-white/50'}`}>
                                            <Icon className={colors.icon} size={20} />
                                        </div>
                                        
                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-4">
                                                <div>
                                                    <h3 className={`font-medium ${alert.is_read ? 'text-slate-700' : 'text-slate-900'}`}>
                                                        {alert.title}
                                                        {!alert.is_read && (
                                                            <span className="ml-2 w-2 h-2 bg-orange-500 rounded-full inline-block"></span>
                                                        )}
                                                    </h3>
                                                    <p className={`text-sm mt-0.5 ${alert.is_read ? 'text-slate-500' : 'text-slate-600'}`}>
                                                        {alert.message}
                                                    </p>
                                                </div>
                                                <span className="text-xs text-slate-400 whitespace-nowrap">
                                                    {formatTimeAgo(alert.created_at)}
                                                </span>
                                            </div>
                                            
                                            {/* Action Button */}
                                            {alert.action_link && (
                                                <div className="mt-3 flex items-center gap-2">
                                                    <span className="text-sm font-medium text-orange-600 flex items-center gap-1 group-hover:underline">
                                                        {alert.action_text || 'View'}
                                                        <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                        
                                        {/* Actions */}
                                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            {!alert.is_read && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        markReadMutation.mutate(alert.id);
                                                    }}
                                                    className="p-1.5 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                                                    title="Mark as read"
                                                >
                                                    <CheckCircle size={18} />
                                                </button>
                                            )}
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    dismissMutation.mutate(alert.id);
                                                }}
                                                className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                                                title="Dismiss"
                                            >
                                                <X size={18} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
