import React from 'react';
import { ArrowUpRight, DollarSign, FileText, CheckCircle, Clock, Users, ShoppingBag } from 'lucide-react';
import { Link } from 'react-router-dom';

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
    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
                    <p className="text-slate-400">Welcome back, here's what's happening today.</p>
                </div>
                <Link to="/quotes/new" className="btn-primary flex items-center gap-2">
                    <FileText size={18} />
                    Create New Quote
                </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Revenue" value="$45,231.89" change="+20.1% from last month" icon={DollarSign} trend="up" />
                <StatCard title="Quotes Generated" value="12" change="+4 today" icon={FileText} trend="up" />
                <StatCard title="Pending Approval" value="4" change="2 urgent" icon={Clock} trend="down" />
                <StatCard title="Conversion Rate" value="24.5%" change="+3.2%" icon={CheckCircle} trend="up" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 glass-panel rounded-2xl p-6">
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
                                {[1, 2, 3, 4, 5].map((i) => (
                                    <tr key={i} className="group hover:bg-slate-800/30 transition-colors">
                                        <td className="py-4 pl-4 font-medium text-slate-200">QT-{2024000 + i}</td>
                                        <td className="py-4 text-slate-400">Acme Industries</td>
                                        <td className="py-4 text-slate-400">Oct 24, 2024</td>
                                        <td className="py-4 text-slate-200 font-medium">$1,2{i}4.00</td>
                                        <td className="py-4">
                                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                                Pending
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="glass-panel rounded-2xl p-6">
                    <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
                    <div className="space-y-3">
                        <button className="w-full glass-card p-4 rounded-xl flex items-center gap-3 text-left group">
                            <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg group-hover:bg-purple-500/30 transition-colors">
                                <Users size={18} />
                            </div>
                            <div>
                                <span className="block text-slate-200 font-medium">Add Customer</span>
                                <span className="text-xs text-slate-500">Create new client profile</span>
                            </div>
                            <ArrowUpRight size={16} className="ml-auto text-slate-600 group-hover:text-slate-400 transition-colors" />
                        </button>
                        <button className="w-full glass-card p-4 rounded-xl flex items-center gap-3 text-left group">
                            <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                                <ShoppingBag size={18} />
                            </div>
                            <div>
                                <span className="block text-slate-200 font-medium">Browse Catalog</span>
                                <span className="text-xs text-slate-500">Check product availability</span>
                            </div>
                            <ArrowUpRight size={16} className="ml-auto text-slate-600 group-hover:text-slate-400 transition-colors" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
