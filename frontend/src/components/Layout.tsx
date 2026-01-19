import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, Users, ShoppingBag, Settings, LogOut, Inbox } from 'lucide-react';
import clsx from 'clsx';

const SidebarItem = ({ icon: Icon, label, to }: { icon: any, label: string, to: string }) => {
    const location = useLocation();
    const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));

    return (
        <Link
            to={to}
            className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
                isActive
                    ? "bg-primary-500/10 text-primary-400 font-medium"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            )}
        >
            <Icon size={20} className={clsx("transition-transform group-hover:scale-110", isActive ? "text-primary-400" : "text-slate-500 group-hover:text-slate-300")} />
            <span>{label}</span>
            {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-400 shadow-[0_0_8px_rgba(56,189,248,0.5)]" />
            )}
        </Link>
    );
};

export const Layout = ({ children }: { children: React.ReactNode }) => {
    return (
        <div className="flex min-h-screen bg-slate-950 text-slate-100 overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950">
            {/* Sidebar */}
            <aside className="w-64 glass-panel border-r border-slate-800/50 flex flex-col h-screen fixed left-0 top-0 z-10 backdrop-blur-xl">
                <div className="p-6">
                    <div className="flex items-center gap-2 mb-8">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center shadow-lg shadow-primary-500/20">
                            <span className="font-bold text-white text-lg">M</span>
                        </div>
                        <span className="font-bold text-xl tracking-tight">Mercura</span>
                    </div>

                    <nav className="space-y-1">
                        <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" />
                        <SidebarItem icon={Inbox} label="Inbox" to="/emails" />
                        <SidebarItem icon={FileText} label="Quotes" to="/quotes" />
                        <SidebarItem icon={Users} label="Customers" to="/customers" />
                        <SidebarItem icon={ShoppingBag} label="Products" to="/products" />
                        <SidebarItem icon={ArrowLeftRight} label="Mappings" to="/mappings" />
                    </nav>
                </div>

                <div className="mt-auto p-6 border-t border-slate-800/50">
                    <div className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-slate-800/50 cursor-pointer transition-colors group">
                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center ring-2 ring-transparent group-hover:ring-primary-500/30 transition-all">
                            <span className="font-medium text-sm">JD</span>
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-200 truncate">John Doe</p>
                            <p className="text-xs text-slate-500 truncate">Sales Rep</p>
                        </div>
                        <LogOut size={16} className="text-slate-500 group-hover:text-slate-300" />
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 ml-64 p-8 overflow-y-auto h-screen relative">
                <div className="absolute top-0 left-0 w-full h-96 bg-primary-500/5 blur-[120px] pointer-events-none" />
                <div className="relative max-w-7xl mx-auto animate-fade-in">
                    {children}
                </div>
            </main>
        </div>
    );
};
