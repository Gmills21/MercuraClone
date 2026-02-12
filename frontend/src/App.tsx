import { Suspense, lazy, useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Outlet } from 'react-router-dom';
import { Layout } from './components/Layout';
import { PageSkeleton } from './components/SkeletonScreens';
import { FlawlessShell, FlawlessPage } from './components/FlawlessShell';
import { queryClient, prefetchDashboardData } from './lib/queryClient';

// ============================================
// LAZY LOADED PAGES WITH PRELOAD SUPPORT
// ============================================

// Core pages - preloaded after initial load for instant switching
const TodayView = lazy(() => import('./pages/TodayView'));
const Quotes = lazy(() => import('./pages/Quotes'));
const Customers = lazy(() => import('./pages/Customers'));
const Products = lazy(() => import('./pages/Products'));
const Emails = lazy(() => import('./pages/Emails'));
const Projects = lazy(() => import('./pages/Projects'));

// Secondary pages - loaded on demand
const SmartQuote = lazy(() => import('./pages/SmartQuote'));
const QuoteReview = lazy(() => import('./pages/QuoteReview'));
const QuoteView = lazy(() => import('./pages/QuoteView'));
const CompetitorMapping = lazy(() => import('./pages/CompetitorMapping'));
const QuickBooksIntegration = lazy(() => import('./pages/QuickBooksIntegration'));
const AlertsPage = lazy(() => import('./pages/AlertsPage'));
const CustomerIntelligence = lazy(() => import('./pages/CustomerIntelligence'));
const IntelligenceDashboard = lazy(() => import('./pages/IntelligenceDashboard'));
const CameraCapture = lazy(() => import('./pages/CameraCapture'));
const KnowledgeBasePage = lazy(() => import('./pages/KnowledgeBasePage'));
const AccountBilling = lazy(() => import('./pages/AccountBilling'));
const Security = lazy(() => import('./pages/Security'));
const CreateQuote = lazy(() => import('./pages/CreateQuote'));
const LandingPage = lazy(() => import('./pages/LandingPage'));

// ============================================
// ROUTE PRELOADING - eagerly load core pages on idle
// ============================================

const PRELOAD_IMPORTS = [
  () => import('./pages/TodayView'),
  () => import('./pages/Quotes'),
  () => import('./pages/Customers'),
  () => import('./pages/Products'),
  () => import('./pages/Emails'),
  () => import('./pages/Projects'),
];

// Routes that FlawlessShell should cache (main tabs)
const CACHED_ROUTES = [
  '/dashboard',
  '/app/dashboard',
  '/quotes',
  '/emails',
  '/customers',
  '/projects',
  '/products',
  '/intelligence',
  '/impact',
];

// ============================================
// SUSPENSE WRAPPER WITH SKELETON FALLBACK
// ============================================

const SuspenseWrapper = ({
  children,
  type = 'table'
}: {
  children: React.ReactNode;
  type?: 'dashboard' | 'table' | 'cards' | 'form' | 'detail';
}) => (
  <Suspense fallback={<PageSkeleton type={type} />}>
    {children}
  </Suspense>
);

// ============================================
// FLAWLESS LAYOUT - INSTANT TAB SWITCHING
// ============================================

const FlawlessLayout: React.FC = () => {
  return (
    <Layout>
      <FlawlessShell
        cachedRoutes={CACHED_ROUTES}
        maxCacheSize={6}
        enableAnimation={true}
        className="flex-1"
      >
        <div className="p-6">
          <Outlet />
        </div>
      </FlawlessShell>
    </Layout>
  );
};

// ============================================
// ROUTE DEFINITIONS
// ============================================

const DashboardRoute = () => (
  <SuspenseWrapper type="dashboard">
    <TodayView />
  </SuspenseWrapper>
);

const QuotesRoute = () => (
  <SuspenseWrapper type="table">
    <Quotes />
  </SuspenseWrapper>
);

const EmailsRoute = () => (
  <SuspenseWrapper type="table">
    <Emails />
  </SuspenseWrapper>
);

const CustomersRoute = () => (
  <SuspenseWrapper type="table">
    <Customers />
  </SuspenseWrapper>
);

const ProjectsRoute = () => (
  <SuspenseWrapper type="table">
    <Projects />
  </SuspenseWrapper>
);

const ProductsRoute = () => (
  <SuspenseWrapper type="cards">
    <Products />
  </SuspenseWrapper>
);

// ============================================
// PRELOADER COMPONENT
// Uses requestIdleCallback to preload pages during idle time
// ============================================

const Preloader: React.FC = () => {
  useEffect(() => {
    // Delay preloading to avoid competing with initial page render
    const timer = setTimeout(() => {
      const scheduleWork = (window as any).requestIdleCallback ||
        ((cb: () => void) => setTimeout(cb, 50));

      PRELOAD_IMPORTS.forEach((importFn, index) => {
        // Stagger by 150ms per import to avoid network congestion
        setTimeout(() => {
          scheduleWork(() => {
            importFn().catch(() => {
              // Silently fail — component will load on demand
            });
          });
        }, index * 150);
      });
    }, 1500); // Wait 1.5s after app mounts

    return () => clearTimeout(timer);
  }, []);

  return null;
};

// ============================================
// MAIN APP
// ============================================

function App() {
  const [isReady, setIsReady] = useState(false);

  // Prefetch dashboard data and mark ready
  useEffect(() => {
    prefetchDashboardData();
    // Mark as ready on next frame — avoids flash
    requestAnimationFrame(() => {
      setIsReady(true);
    });
  }, []);

  // Add GPU acceleration class to body
  useEffect(() => {
    document.body.classList.add('gpu-accelerated');
    return () => {
      document.body.classList.remove('gpu-accelerated');
    };
  }, []);

  if (!isReady) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <PageSkeleton type="dashboard" />
      </div>
    );
  }

  return (
    <Router>
      {/* Preload core pages during idle time */}
      <Preloader />

      <Routes>
        {/* Public routes - no layout */}
        <Route
          path="/quote/:token"
          element={
            <SuspenseWrapper type="cards">
              <QuoteView />
            </SuspenseWrapper>
          }
        />

        {/* Public landing page */}
        <Route
          path="/"
          element={
            <SuspenseWrapper type="cards">
              <LandingPage />
            </SuspenseWrapper>
          }
        />

        {/* Protected routes with FlawlessShell for instant navigation */}
        <Route element={<FlawlessLayout />}>
          <Route path="/app/dashboard" element={<DashboardRoute />} />
          <Route path="/dashboard" element={<DashboardRoute />} />
          <Route path="/emails" element={<EmailsRoute />} />
          <Route path="/quotes" element={<QuotesRoute />} />
          <Route path="/quotes/new" element={
            <SuspenseWrapper type="cards"><SmartQuote /></SuspenseWrapper>
          } />
          <Route path="/quotes/create" element={
            <SuspenseWrapper type="form"><CreateQuote /></SuspenseWrapper>
          } />
          <Route path="/quotes/:id" element={
            <SuspenseWrapper type="detail"><QuoteReview /></SuspenseWrapper>
          } />
          <Route path="/customers" element={<CustomersRoute />} />
          <Route path="/projects" element={<ProjectsRoute />} />
          <Route path="/products" element={<ProductsRoute />} />
          <Route path="/mappings" element={
            <SuspenseWrapper type="cards"><CompetitorMapping /></SuspenseWrapper>
          } />
          <Route path="/quickbooks" element={
            <SuspenseWrapper type="cards"><QuickBooksIntegration /></SuspenseWrapper>
          } />
          <Route path="/alerts" element={
            <SuspenseWrapper type="cards"><AlertsPage /></SuspenseWrapper>
          } />
          <Route path="/intelligence" element={
            <SuspenseWrapper type="dashboard"><IntelligenceDashboard /></SuspenseWrapper>
          } />
          <Route path="/intelligence/customers/:customerId" element={
            <SuspenseWrapper type="cards"><CustomerIntelligence /></SuspenseWrapper>
          } />
          <Route path="/impact" element={
            <SuspenseWrapper type="dashboard"><IntelligenceDashboard /></SuspenseWrapper>
          } />
          <Route path="/camera" element={
            <SuspenseWrapper type="cards"><CameraCapture /></SuspenseWrapper>
          } />
          <Route path="/knowledge" element={
            <SuspenseWrapper type="cards"><KnowledgeBasePage /></SuspenseWrapper>
          } />
          <Route path="/account/billing" element={
            <SuspenseWrapper type="cards"><AccountBilling /></SuspenseWrapper>
          } />
          <Route path="/security" element={
            <SuspenseWrapper type="cards"><Security /></SuspenseWrapper>
          } />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
