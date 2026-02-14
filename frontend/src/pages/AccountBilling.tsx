import React, { useEffect, useState } from 'react';
import {
    CreditCard, Users, Calendar, Download, AlertCircle,
    CheckCircle, XCircle, Settings, Plus, Trash2, ExternalLink,
    TrendingUp, DollarSign, Package, Shield, Mail
} from 'lucide-react';
import { billingApi } from '../services/api';

interface SubscriptionPlan {
    id: string;
    name: string;
    description: string;
    price_per_seat: number;
    billing_interval: 'monthly' | 'yearly';
    features: string[];
    max_seats: number | null;
    paddle_plan_id?: string;
}

interface Subscription {
    id: string;
    plan_id: string;
    status: string;
    seats: number;
    price_per_seat: number;
    total_amount: number;
    billing_interval: string;
    current_period_start: string;
    current_period_end: string;
    cancel_at_period_end: boolean;
}

interface Invoice {
    id: string;
    invoice_number: string;
    amount: number;
    currency: string;
    status: string;
    invoice_date: string;
    paid_at: string | null;
    invoice_pdf_url: string | null;
}

interface SeatAssignment {
    id: string;
    sales_rep_email: string;
    sales_rep_name: string | null;
    is_active: boolean;
    assigned_at: string;
}

export const AccountBilling = () => {
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [seats, setSeats] = useState<SeatAssignment[]>([]);
    const [usage, setUsage] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'plans' | 'invoices' | 'seats'>('overview');
    
    // Billing configuration status
    const [billingEnabled, setBillingEnabled] = useState<boolean>(true);
    const [billingMessage, setBillingMessage] = useState<string>('');
    const [billingConfig, setBillingConfig] = useState<any>(null);
    
    // Seat assignment modal state
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [assignEmail, setAssignEmail] = useState('');
    const [assignName, setAssignName] = useState('');
    const [assignLoading, setAssignLoading] = useState(false);

    useEffect(() => {
        loadBillingData();
        
        // Check for Paddle checkout return
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('success') === 'true') {
            // Clear the URL parameter
            window.history.replaceState({}, '', window.location.pathname);
            // Show success message (could use a toast here)
            setTimeout(() => {
                alert('Payment successful! Your subscription has been updated.');
            }, 500);
        } else if (urlParams.get('canceled') === 'true') {
            window.history.replaceState({}, '', window.location.pathname);
        }
    }, []);

    const loadBillingData = async () => {
        try {
            // First check if billing is configured
            const configRes = await billingApi.getConfig();
            setBillingConfig(configRes.data);
            setBillingEnabled(configRes.data.enabled);
            setBillingMessage(configRes.data.message);
            
            if (!configRes.data.enabled) {
                // Billing not configured - still load plans for display but show notice
                const plansRes = await billingApi.getPlans();
                setPlans(plansRes.data);
                setLoading(false);
                return;
            }

            const [subRes, plansRes, invoicesRes, seatsRes, usageRes] = await Promise.all([
                billingApi.getSubscription(),
                billingApi.getPlans(),
                billingApi.getInvoices(),
                billingApi.getSeats(),
                billingApi.getUsage()
            ]);

            setSubscription(subRes.data);
            setPlans(plansRes.data);
            setInvoices(invoicesRes.data.invoices || []);
            setSeats(seatsRes.data.seats || []);
            setUsage(usageRes.data);
        } catch (error: any) {
            console.error('Failed to load billing data:', error);
            // Check if it's a billing not configured error
            if (error.response?.data?.detail?.code === 'BILLING_NOT_CONFIGURED') {
                setBillingEnabled(false);
                setBillingMessage(error.response.data.detail.message);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleUpgradePlan = async (planId: string) => {
        if (!billingEnabled) {
            alert('Subscription billing is not yet enabled. Please contact support@mercura.ai to upgrade your account.');
            return;
        }
        
        try {
            const response = await billingApi.createCheckoutSession({
                plan_id: planId,
                seats: subscription?.seats || 1,
                billing_interval: 'monthly',
                success_url: `${window.location.origin}/account/billing?success=true`,
                cancel_url: `${window.location.origin}/account/billing?canceled=true`
            });

            // Redirect to Paddle checkout
            window.location.href = response.data.checkout_url;
        } catch (error: any) {
            console.error('Failed to create checkout session:', error);
            const errorDetail = error.response?.data?.detail;
            if (errorDetail?.code === 'BILLING_NOT_CONFIGURED') {
                alert(errorDetail.message || 'Billing is not configured. Please contact support.');
            } else {
                alert('Unable to create checkout session. Please try again or contact support.');
            }
        }
    };

    const handleUpdateSeats = async (newSeats: number) => {
        try {
            await billingApi.updateSubscription({ seats: newSeats });
            await loadBillingData();
        } catch (error) {
            console.error('Failed to update seats:', error);
        }
    };

    const handleCancelSubscription = async () => {
        if (!confirm('Are you sure you want to cancel your subscription?')) return;

        try {
            await billingApi.cancelSubscription(true);
            await loadBillingData();
        } catch (error) {
            console.error('Failed to cancel subscription:', error);
        }
    };

    const handleAssignSeat = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!assignEmail.trim()) return;
        
        setAssignLoading(true);
        try {
            await billingApi.assignSeat(assignEmail.trim(), assignName.trim() || undefined);
            setAssignEmail('');
            setAssignName('');
            setShowAssignModal(false);
            await loadBillingData();
        } catch (error) {
            console.error('Failed to assign seat:', error);
            alert('Failed to assign seat. Please check if you have available seats.');
        } finally {
            setAssignLoading(false);
        }
    };

    const handleDeactivateSeat = async (seatId: string) => {
        if (!confirm('Remove this team member? They will lose access immediately.')) return;
        
        try {
            await billingApi.deactivateSeat(seatId);
            await loadBillingData();
        } catch (error) {
            console.error('Failed to deactivate seat:', error);
        }
    };

    const getStatusBadge = (status: string) => {
        const styles = {
            active: 'bg-green-100 text-green-800',
            trial: 'bg-blue-100 text-blue-800',
            past_due: 'bg-red-100 text-red-800',
            canceled: 'bg-gray-100 text-gray-800'
        };

        return (
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${styles[status as keyof typeof styles] || styles.active}`}>
                {status.replace('_', ' ').toUpperCase()}
            </span>
        );
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-2 border-orange-500 border-t-transparent"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50/50">
            {/* Billing Not Configured Notice */}
            {!billingEnabled && (
                <div className="bg-amber-50 border-b border-amber-200">
                    <div className="max-w-7xl mx-auto px-8 py-4">
                        <div className="flex items-start gap-3">
                            <AlertCircle className="text-amber-600 flex-shrink-0 mt-0.5" size={20} />
                            <div>
                                <h3 className="font-semibold text-amber-900">Subscription Billing Not Yet Available</h3>
                                <p className="text-amber-800 mt-1">
                                    {billingMessage || 'Subscription billing is not yet enabled for your account.'}
                                    {' '}Please contact <a href="mailto:support@mercura.ai" className="underline font-medium">support@mercura.ai</a> to upgrade your account.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            {/* Header */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-8 py-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-semibold text-gray-900">Account & Billing</h1>
                            <p className="text-gray-600 mt-1">Manage your subscription and billing settings</p>
                        </div>
                        {subscription && (
                            <div className="flex items-center gap-3">
                                {getStatusBadge(subscription.status)}
                            </div>
                        )}
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-6 mt-6 border-b border-gray-200">
                        {[
                            { id: 'overview', label: 'Overview', icon: TrendingUp },
                            { id: 'plans', label: 'Plans & Pricing', icon: Package },
                            { id: 'invoices', label: 'Invoices', icon: Download },
                            { id: 'seats', label: 'Team Seats', icon: Users }
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${activeTab === tab.id
                                    ? 'border-orange-500 text-orange-600'
                                    : 'border-transparent text-gray-600 hover:text-gray-900'
                                    }`}
                            >
                                <tab.icon size={18} />
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-8 py-8">
                {/* Overview Tab */}
                {activeTab === 'overview' && subscription && (
                    <div className="space-y-6">
                        {/* Current Plan Card */}
                        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                            <div className="flex items-start justify-between">
                                <div>
                                    <h2 className="text-xl font-semibold text-gray-900">Current Plan</h2>
                                    <p className="text-gray-600 mt-1">
                                        {plans.find(p => p.id === subscription.plan_id)?.name || 'Professional'} Plan
                                    </p>
                                </div>
                                <button
                                    onClick={() => setActiveTab('plans')}
                                    disabled={!billingEnabled}
                                    className={`px-4 py-2 rounded-lg transition-colors ${
                                        billingEnabled
                                            ? 'bg-orange-600 text-white hover:bg-orange-700'
                                            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                    }`}
                                    title={billingEnabled ? '' : 'Contact support to upgrade your account'}
                                >
                                    {billingEnabled ? 'Upgrade Plan' : 'Contact Support to Upgrade'}
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                                        <DollarSign className="text-orange-600" size={24} />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Monthly Cost</p>
                                        <p className="text-2xl font-bold text-gray-900">${subscription.total_amount}</p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                        <Users className="text-blue-600" size={24} />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Active Seats</p>
                                        <p className="text-2xl font-bold text-gray-900">{subscription.seats}</p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                        <Calendar className="text-green-600" size={24} />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Next Billing Date</p>
                                        <p className="text-lg font-semibold text-gray-900">
                                            {new Date(subscription.current_period_end).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Usage Stats */}
                        {usage && (
                            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                                <h2 className="text-xl font-semibold text-gray-900 mb-4">Usage This Period</h2>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div>
                                        <p className="text-sm text-gray-600">Quotes Generated</p>
                                        <p className="text-3xl font-bold text-gray-900 mt-1">{usage.quotes_generated}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Emails Processed</p>
                                        <p className="text-3xl font-bold text-gray-900 mt-1">{usage.emails_processed}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Seat Utilization</p>
                                        <p className="text-3xl font-bold text-gray-900 mt-1">
                                            {usage.seats_used}/{usage.seats_total}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Manage Subscription */}
                        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">Manage Subscription</h2>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                    <div>
                                        <p className="font-medium text-gray-900">Add or Remove Seats</p>
                                        <p className="text-sm text-gray-600">$150/month per sales rep</p>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <button
                                            onClick={() => handleUpdateSeats(subscription.seats - 1)}
                                            disabled={subscription.seats <= 1}
                                            className="w-8 h-8 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                                        >
                                            -
                                        </button>
                                        <span className="font-semibold text-gray-900 w-8 text-center">{subscription.seats}</span>
                                        <button
                                            onClick={() => handleUpdateSeats(subscription.seats + 1)}
                                            className="w-8 h-8 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                                        >
                                            +
                                        </button>
                                    </div>
                                </div>

                                <button
                                    onClick={handleCancelSubscription}
                                    className="w-full p-4 text-left bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
                                >
                                    <p className="font-medium text-red-900">Cancel Subscription</p>
                                    <p className="text-sm text-red-700">Your subscription will remain active until the end of the billing period</p>
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Plans Tab */}
                {activeTab === 'plans' && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {plans.map(plan => (
                            <div
                                key={plan.id}
                                className={`bg-white border-2 rounded-xl p-6 shadow-sm transition-all ${subscription?.plan_id === plan.id
                                    ? 'border-orange-500 ring-2 ring-orange-200'
                                    : 'border-gray-200 hover:border-orange-300'
                                    }`}
                            >
                                <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                                <p className="text-gray-600 mt-2">{plan.description}</p>
                                <div className="mt-4">
                                    <span className="text-4xl font-bold text-gray-900">${plan.price_per_seat}</span>
                                    <span className="text-gray-600">/seat/month</span>
                                </div>

                                <ul className="mt-6 space-y-3">
                                    {plan.features.map((feature, idx) => (
                                        <li key={idx} className="flex items-start gap-2">
                                            <CheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={18} />
                                            <span className="text-gray-700">{feature}</span>
                                        </li>
                                    ))}
                                </ul>

                                <button
                                    onClick={() => handleUpgradePlan(plan.paddle_plan_id || plan.id)}
                                    disabled={subscription?.plan_id === plan.id || !billingEnabled}
                                    className={`w-full mt-6 px-4 py-3 rounded-lg font-medium transition-colors ${
                                        subscription?.plan_id === plan.id
                                            ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                                            : !billingEnabled
                                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                                : 'bg-orange-600 text-white hover:bg-orange-700'
                                    }`}
                                >
                                    {subscription?.plan_id === plan.id 
                                        ? 'Current Plan' 
                                        : !billingEnabled 
                                            ? 'Contact Support to Upgrade'
                                            : 'Select Plan'}
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                {/* Invoices Tab */}
                {activeTab === 'invoices' && (
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
                        {invoices.length === 0 ? (
                            <div className="p-12 text-center">
                                <Download className="mx-auto text-gray-300" size={48} />
                                <h3 className="text-lg font-medium text-gray-900 mt-4">No invoices yet</h3>
                                <p className="text-gray-600 mt-2">Your invoices will appear here once you have an active subscription</p>
                            </div>
                        ) : (
                            <table className="w-full">
                                <thead>
                                    <tr className="bg-gray-50 border-b border-gray-200">
                                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase">Invoice</th>
                                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase">Date</th>
                                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase">Amount</th>
                                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                                        <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {invoices.map(invoice => (
                                        <tr key={invoice.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 font-medium text-gray-900">{invoice.invoice_number}</td>
                                            <td className="px-6 py-4 text-gray-600">
                                                {new Date(invoice.invoice_date).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 text-gray-900">${invoice.amount}</td>
                                            <td className="px-6 py-4">{getStatusBadge(invoice.status)}</td>
                                            <td className="px-6 py-4 text-right">
                                                {invoice.invoice_pdf_url && (
                                                    <a
                                                        href={invoice.invoice_pdf_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-2 text-orange-600 hover:text-orange-700"
                                                    >
                                                        <Download size={16} />
                                                        Download
                                                    </a>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}

                {/* Seats Tab */}
                {activeTab === 'seats' && (
                    <div className="space-y-6">
                        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                            <div className="flex items-center justify-between mb-6">
                                <div>
                                    <h2 className="text-xl font-semibold text-gray-900">Team Seats</h2>
                                    <p className="text-gray-600 mt-1">
                                        {seats.filter(s => s.is_active).length} of {subscription?.seats || 0} seats assigned
                                    </p>
                                </div>
                                <button 
                                    onClick={() => setShowAssignModal(true)}
                                    disabled={seats.filter(s => s.is_active).length >= (subscription?.seats || 0)}
                                    className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Plus size={18} />
                                    Assign Seat
                                </button>
                            </div>

                            {seats.length === 0 ? (
                                <div className="text-center py-12">
                                    <Users className="mx-auto text-gray-300" size={48} />
                                    <h3 className="text-lg font-medium text-gray-900 mt-4">No seats assigned</h3>
                                    <p className="text-gray-600 mt-2">Assign seats to your sales team members</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {seats.map(seat => (
                                        <div key={seat.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                                                    <span className="text-orange-600 font-semibold">
                                                        {seat.sales_rep_name?.charAt(0) || seat.sales_rep_email.charAt(0).toUpperCase()}
                                                    </span>
                                                </div>
                                                <div>
                                                    <p className="font-medium text-gray-900">{seat.sales_rep_name || 'Unnamed'}</p>
                                                    <p className="text-sm text-gray-600">{seat.sales_rep_email}</p>
                                                </div>
                                            </div>
                                            <button 
                                                onClick={() => handleDeactivateSeat(seat.id)}
                                                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Assign Seat Modal */}
                {showAssignModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
                            <h3 className="text-xl font-semibold text-gray-900 mb-4">Assign Seat</h3>
                            <p className="text-gray-600 mb-6">
                                Invite a team member to use Mercura. They'll receive an email invitation.
                            </p>
                            <form onSubmit={handleAssignSeat} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                                    <input
                                        type="email"
                                        value={assignEmail}
                                        onChange={(e) => setAssignEmail(e.target.value)}
                                        placeholder="colleague@company.com"
                                        required
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Name (optional)</label>
                                    <input
                                        type="text"
                                        value={assignName}
                                        onChange={(e) => setAssignName(e.target.value)}
                                        placeholder="John Doe"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                                    />
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowAssignModal(false)}
                                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={assignLoading || !assignEmail.trim()}
                                        className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50"
                                    >
                                        {assignLoading ? 'Assigning...' : 'Assign Seat'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AccountBilling;
