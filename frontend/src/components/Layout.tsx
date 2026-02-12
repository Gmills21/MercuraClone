import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, FileText, Users, Package, LogOut, Inbox, 
  Target, CreditCard, BarChart3, Brain, Shield, Briefcase, 
  ChevronDown, MoreHorizontal, Settings, Search, Sparkles, Command 
} from 'lucide-react';
import clsx from 'clsx';
import { NotificationCenter } from './NotificationCenter';
import { usePrefetch } from '../hooks/usePrefetch';
import { InstantButton, Pressable } from './InstantFeedback';

// ============================================
// SIDEBAR ITEM WITH PREFETCH & INSTANT FEEDBACK
// ============================================

interface SidebarItemProps {
  icon: React.ElementType;
  label: string;
  to: string;
  onHover?: () => void;
  badge?: number;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ 
  icon: Icon, 
  label, 
  to, 
  onHover,
  badge,
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isPressed, setIsPressed] = useState(false);
  const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    navigate(to);
  }, [navigate, to]);

  return (
    <Pressable
      onPress={() => navigate(to)}
      className={clsx(
        "flex items-center gap-3 px-4 py-2.5 rounded-xl transition-colors duration-150 text-sm font-medium w-full",
        isActive
          ? "bg-slate-950 text-white shadow-soft"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      )}
    >
      <motion.div
        animate={{ scale: isActive ? 1.1 : 1 }}
        transition={{ duration: 0.15 }}
      >
        <Icon 
          size={18} 
          className={clsx(
            "transition-colors duration-150",
            isActive ? "text-white" : "text-slate-500"
          )} 
        />
      </motion.div>
      <span className="flex-1">{label}</span>
      {badge !== undefined && badge > 0 && (
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="px-2 py-0.5 text-xs bg-red-500 text-white rounded-full"
        >
          {badge}
        </motion.span>
      )}
    </Pressable>
  );
};

// ============================================
// COLLAPSIBLE "MORE" MENU
// ============================================

const MoreMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const { prefetchRoute } = usePrefetch();

  const moreItems = [
    { icon: Target, label: 'Cross Reference', to: '/mappings' },
    { icon: Brain, label: 'Knowledge Base', to: '/knowledge' },
  ];

  const isAnyActive = moreItems.some(item =>
    location.pathname === item.to || location.pathname.startsWith(item.to)
  );

  return (
    <div>
      <Pressable
        onPress={() => setIsOpen(!isOpen)}
        className={clsx(
          "w-full flex items-center justify-between gap-3 px-4 py-2.5 rounded-xl transition-colors duration-150 text-sm font-medium",
          isAnyActive
            ? "bg-slate-950 text-white"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
        )}
      >
        <div className="flex items-center gap-3">
          <MoreHorizontal size={18} className={isAnyActive ? "text-white" : "text-slate-500"} />
          <span>More</span>
        </div>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={16} />
        </motion.div>
      </Pressable>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
            className="overflow-hidden"
          >
            <div className="mt-2 ml-4 pl-4 border-l border-slate-200 space-y-1">
              {moreItems.map(item => (
                <Link
                  key={item.to}
                  to={item.to}
                  onMouseEnter={() => prefetchRoute(item.to)}
                  className={clsx(
                    "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-150 text-sm",
                    location.pathname === item.to || location.pathname.startsWith(item.to)
                      ? "bg-slate-100 text-slate-900"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"
                  )}
                >
                  <item.icon size={16} />
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ============================================
// USER MENU DROPDOWN
// ============================================

const UserMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const { prefetchBilling } = usePrefetch();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isSecurityActive = location.pathname === '/security';

  return (
    <div className="relative" ref={menuRef}>
      <Pressable
        onPress={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-slate-100 transition-colors duration-150"
      >
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center shadow-soft">
          <span className="font-semibold text-sm text-white">JD</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-900 truncate tracking-tight">John Doe</p>
          <p className="text-xs text-slate-500 truncate">Admin</p>
        </div>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={16} className="text-slate-400" />
        </motion.div>
      </Pressable>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute bottom-full left-0 right-0 mb-2 bg-white border-minimal rounded-xl shadow-soft-lg overflow-hidden z-50"
          >
            <div className="p-2">
              <Link
                to="/security"
                onClick={() => setIsOpen(false)}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-150 text-sm w-full",
                  isSecurityActive
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-600 hover:bg-slate-50"
                )}
              >
                <Shield size={16} className={isSecurityActive ? "text-slate-700" : "text-slate-500"} />
                <span>Security & Privacy</span>
              </Link>
              <Link
                to="/account/billing"
                onClick={() => setIsOpen(false)}
                onMouseEnter={prefetchBilling}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-150 text-sm w-full text-slate-600 hover:bg-slate-50"
              >
                <Settings size={16} className="text-slate-500" />
                <span>Account Settings</span>
              </Link>
            </div>
            <div className="border-t border-slate-100 p-2">
              <Pressable
                onPress={() => {/* handle sign out */}}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-150 text-sm w-full text-red-600 hover:bg-red-50"
              >
                <LogOut size={16} className="text-red-500" />
                <span>Sign Out</span>
              </Pressable>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ============================================
// COMMAND PALETTE / SEARCH MODAL
// ============================================

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const { prefetchRoute } = usePrefetch();

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  const quickActions = [
    { label: 'New Request', shortcut: 'N', action: () => { navigate('/quotes/new'); onClose(); }, path: '/quotes/new' },
    { label: 'View Quotes', shortcut: 'Q', action: () => { navigate('/quotes'); onClose(); }, path: '/quotes' },
    { label: 'RFQ Inbox', shortcut: 'I', action: () => { navigate('/emails'); onClose(); }, path: '/emails' },
    { label: 'Customers', shortcut: 'C', action: () => { navigate('/customers'); onClose(); }, path: '/customers' },
    { label: 'Products', shortcut: 'P', action: () => { navigate('/products'); onClose(); }, path: '/products' },
    { label: 'Dashboard', shortcut: 'D', action: () => { navigate('/dashboard'); onClose(); }, path: '/dashboard' },
  ];

  const filteredActions = query
    ? quickActions.filter(a => a.label.toLowerCase().includes(query.toLowerCase()))
    : quickActions;

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]" 
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm"
      />
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.95 }}
        transition={{ duration: 0.15, ease: 'easeOut' }}
        className="relative w-full max-w-lg bg-white rounded-2xl shadow-soft-xl overflow-hidden border-minimal"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-100">
          <Search size={20} className="text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search or jump to..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 text-sm outline-none placeholder-slate-400 text-slate-900 bg-transparent"
          />
          <kbd className="px-2 py-1 text-xs bg-slate-100 text-slate-500 rounded-md font-mono">ESC</kbd>
        </div>
        <div className="max-h-[300px] overflow-y-auto custom-scrollbar">
          <div className="p-2">
            <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Quick Actions
            </div>
            {filteredActions.map((action, index) => (
              <motion.button
                key={action.label}
                onClick={action.action}
                onMouseEnter={() => action.path && prefetchRoute(action.path)}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm text-slate-700 hover:bg-slate-50 transition-colors duration-150"
              >
                <div className="flex items-center gap-3">
                  <Sparkles size={16} className="text-slate-400" />
                  <span className="font-medium">{action.label}</span>
                </div>
                <kbd className="px-2 py-0.5 text-xs bg-slate-100 text-slate-500 rounded-md font-mono">
                  {action.shortcut}
                </kbd>
              </motion.button>
            ))}
          </div>
        </div>
        <div className="border-t border-slate-100 px-5 py-3 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>
            Tip: Press <kbd className="px-1.5 py-0.5 bg-slate-200 rounded-md font-mono">N</kbd> anywhere for new quote
          </span>
          <div className="flex items-center gap-2">
            <Command size={12} />
            <span>Command Palette</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

// ============================================
// MAIN LAYOUT COMPONENT
// ============================================

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const { 
    prefetchQuotes, 
    prefetchCustomers, 
    prefetchProducts, 
    prefetchProjects, 
    prefetchEmails,
  } = usePrefetch();

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if in an input field
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) {
        return;
      }

      // `/` - Open search/command palette
      if (e.key === '/') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }

      // `n` - New quote
      if (e.key === 'n' || e.key === 'N') {
        e.preventDefault();
        navigate('/quotes/new');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);

  return (
    <div className="flex min-h-screen bg-slate-50 gpu-accelerated">
      {/* Command Palette */}
      <AnimatePresence>
        {commandPaletteOpen && (
          <CommandPalette 
            isOpen={commandPaletteOpen} 
            onClose={() => setCommandPaletteOpen(false)} 
          />
        )}
      </AnimatePresence>

      {/* Sidebar - Clean, minimal */}
      <aside className="w-64 border-r border-slate-200/60 flex flex-col h-screen fixed left-0 top-0 z-10 bg-white">
        {/* Logo */}
        <div className="px-6 py-6">
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity duration-150">
            <div className="w-9 h-9 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center shadow-soft">
              <span className="font-bold text-white text-sm">OM</span>
            </div>
            <span className="font-bold text-xl text-slate-950 tracking-tight">OpenMercura</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto custom-scrollbar">
          <SidebarItem 
            icon={LayoutDashboard} 
            label="Dashboard" 
            to="/dashboard" 
          />
          <SidebarItem 
            icon={FileText} 
            label="Quotes & RFQs" 
            to="/quotes" 
            onHover={prefetchQuotes}
          />
          <SidebarItem 
            icon={Inbox} 
            label="RFQ Inbox" 
            to="/emails" 
            onHover={prefetchEmails}
            badge={3}
          />

          <div className="pt-6 pb-2">
            <div className="px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Inventory
            </div>
          </div>
          <SidebarItem 
            icon={Users} 
            label="Customers" 
            to="/customers" 
            onHover={prefetchCustomers}
          />
          <SidebarItem 
            icon={Briefcase} 
            label="Projects" 
            to="/projects" 
            onHover={prefetchProjects}
          />
          <SidebarItem 
            icon={Package} 
            label="Products" 
            to="/products" 
            onHover={prefetchProducts}
          />

          <div className="pt-6 pb-2">
            <div className="px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Tools
            </div>
          </div>
          <SidebarItem 
            icon={CreditCard} 
            label="Integrations" 
            to="/quickbooks" 
          />
          <SidebarItem 
            icon={BarChart3} 
            label="Analytics" 
            to="/intelligence" 
          />

          {/* More dropdown for secondary tools */}
          <MoreMenu />
        </nav>

        {/* User Menu with Dropdown */}
        <div className="p-4 border-t border-slate-100">
          <UserMenu />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen">
        {/* Top Header - Glass effect */}
        <div className="fixed top-0 right-0 left-64 z-20 bg-white/90 backdrop-blur-xl border-b border-slate-200/40">
          <div className="flex items-center justify-between px-8 py-4">
            {/* Search trigger */}
            <Pressable
              onPress={() => setCommandPaletteOpen(true)}
              className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-500 bg-slate-100/60 hover:bg-slate-100 rounded-xl transition-colors duration-150 shadow-inner-soft"
            >
              <Search size={15} />
              <span>Search...</span>
              <kbd className="ml-6 px-2 py-0.5 text-xs bg-white text-slate-400 rounded-md font-mono shadow-soft">
                /
              </kbd>
            </Pressable>
            <NotificationCenter />
          </div>
        </div>
        
        {/* Page Content */}
        <div className="pt-16 h-full">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
            className="h-full"
          >
            {children}
          </motion.div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
