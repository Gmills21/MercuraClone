import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, Users, Package, LogOut, Inbox, Target, Sparkles, CreditCard, TrendingUp, BarChart3, Brain } from 'lucide-react';
import clsx from 'clsx';
import { NotificationCenter } from './NotificationCenter';

const SidebarItem = ({ icon: Icon, label, to }: { icon: any, label: string, to: string }) => {
  const location = useLocation();
  const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));

  return (
    <Link
      to={to}
      className={clsx(
        "flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors text-sm font-medium",
        isActive
          ? "bg-orange-50 text-orange-700 border border-orange-200"
          : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
      )}
    >
      <Icon size={18} className={isActive ? "text-orange-600" : "text-gray-400"} />
      <span>{label}</span>
    </Link>
  );
};

export const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex min-h-screen bg-white">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 flex flex-col h-screen fixed left-0 top-0 z-10 bg-white">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-gray-200">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-orange-600 rounded flex items-center justify-center">
              <span className="font-bold text-white text-sm">OM</span>
            </div>
            <span className="font-semibold text-lg text-gray-900">OpenMercura</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1">
          <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" />
          <SidebarItem icon={FileText} label="Quotes & RFQs" to="/quotes" />
          <SidebarItem icon={Inbox} label="Inbox" to="/emails" />

          <div className="pt-4 pb-2">
            <div className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Inventory</div>
          </div>
          <SidebarItem icon={Users} label="Customers" to="/customers" />
          <SidebarItem icon={Package} label="Products" to="/products" />

          <div className="pt-4 pb-2">
            <div className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Tools</div>
          </div>
          <SidebarItem icon={CreditCard} label="Integrations" to="/quickbooks" />
          <SidebarItem icon={BarChart3} label="Analytics" to="/intelligence" />
          <SidebarItem icon={Target} label="Cross Reference" to="/mappings" />
          <SidebarItem icon={Brain} label="Knowledge" to="/knowledge" />
        </nav>

        {/* User */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <span className="font-medium text-sm text-gray-600">JD</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">John Doe</p>
              <p className="text-xs text-gray-500 truncate">Admin</p>
            </div>
            <LogOut size={16} className="text-gray-400" />
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen">
        {/* Top Header with Notifications */}
        <div className="fixed top-0 right-0 left-64 z-20 bg-white/80 backdrop-blur-sm border-b border-gray-200/50">
          <div className="flex items-center justify-end px-6 py-3">
            <NotificationCenter />
          </div>
        </div>
        <div className="pt-14">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
