import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import './index.css';
import App from './App';
import { queryClient, prefetchDashboardData } from './lib/queryClient';
import { identifyUser } from './posthog';
import { InstantRouterProvider } from './components/InstantRouter';

// ============================================
// PERFORMANCE OPTIMIZATIONS
// ============================================

// Identify test user for analytics
identifyUser('3d4df718-47c3-4903-b09e-711090412204', {
  name: 'Demo User',
  role: 'Sales Manager',
  organization: 'Sanitär-Heinze',
});

// Prefetch dashboard data immediately for instant first load
prefetchDashboardData();

// ============================================
// BROWSER OPTIMIZATIONS
// ============================================

// Use passive event listeners for better scroll performance
document.addEventListener('touchstart', () => { }, { passive: true });
document.addEventListener('touchmove', () => { }, { passive: true });
document.addEventListener('wheel', () => { }, { passive: true });

// Preload critical resources
const preloadResources = () => {
  // Preconnect to API domain
  const apiDomain = import.meta.env.VITE_API_URL || '';
  if (apiDomain) {
    const dnsLink = document.createElement('link');
    dnsLink.rel = 'dns-prefetch';
    dnsLink.href = apiDomain;
    document.head.appendChild(dnsLink);

    const preconnectLink = document.createElement('link');
    preconnectLink.rel = 'preconnect';
    preconnectLink.href = apiDomain;
    preconnectLink.crossOrigin = 'anonymous';
    document.head.appendChild(preconnectLink);
  }
};

preloadResources();

// ============================================
// PERFORMANCE MONITORING (Development)
// ============================================

// web-vitals removed - package not installed
// To re-enable: npm install web-vitals
// if (import.meta.env.DEV) {
//   import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
//     getCLS(console.log);
//     getFID(console.log);
//     getFCP(console.log);
//     getLCP(console.log);
//     getTTFB(console.log);
//   });
// }

// ============================================
// RENDER APP
// ============================================

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

const root = createRoot(container);

root.render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <InstantRouterProvider maxCachedRoutes={5}>
        <App />
      </InstantRouterProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>,
);

// ============================================
// SERVICE WORKER REGISTRATION (Optional)
// ============================================

// Uncomment to enable offline support and faster subsequent loads
// if ('serviceWorker' in navigator) {
//   window.addEventListener('load', () => {
//     navigator.serviceWorker.register('/sw.js').catch(console.error);
//   });
// }
