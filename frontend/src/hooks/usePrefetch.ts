import { useCallback } from 'react';
import {
  prefetchQuotes,
  prefetchCustomers,
  prefetchProducts,
  prefetchProjects,
  prefetchEmails,
  queryClient,
  queryKeys,
} from '../lib/queryClient';
import { statsApi, billingApi } from '../services/api';

export const usePrefetch = () => {
  // Prefetch specific routes
  const prefetchRoute = useCallback((path: string) => {
    switch (path) {
      case '/quotes':
      case '/quotes/new':
        prefetchQuotes();
        break;
      case '/customers':
        prefetchCustomers();
        break;
      case '/products':
        prefetchProducts();
        break;
      case '/projects':
        prefetchProjects();
        break;
      case '/emails':
        prefetchEmails();
        break;
      case '/intelligence':
        prefetchIntelligence();
        break;
      case '/quickbooks':
        // QuickBooks data is typically small, prefetch not critical
        break;
      default:
        break;
    }
  }, []);

  // Individual prefetch functions
  const prefetchQuotesHandler = useCallback(() => {
    prefetchQuotes();
  }, []);

  const prefetchCustomersHandler = useCallback(() => {
    prefetchCustomers();
  }, []);

  const prefetchProductsHandler = useCallback(() => {
    prefetchProducts();
  }, []);

  const prefetchProjectsHandler = useCallback(() => {
    prefetchProjects();
  }, []);

  const prefetchEmailsHandler = useCallback(() => {
    prefetchEmails();
  }, []);

  const prefetchBilling = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.billing.subscription,
      queryFn: async () => {
        const res = await billingApi.getSubscription();
        return res.data;
      },
      staleTime: 5 * 60 * 1000,
    });

    queryClient.prefetchQuery({
      queryKey: queryKeys.billing.usage,
      queryFn: async () => {
        const res = await billingApi.getUsage();
        return res.data;
      },
      staleTime: 5 * 60 * 1000,
    });
  }, []);

  const prefetchIntelligence = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.stats.dashboard(30),
      queryFn: async () => {
        const res = await statsApi.get(30);
        return res.data;
      },
      staleTime: 5 * 60 * 1000,
    });
  }, []);

  return {
    prefetchRoute,
    prefetchQuotes: prefetchQuotesHandler,
    prefetchCustomers: prefetchCustomersHandler,
    prefetchProducts: prefetchProductsHandler,
    prefetchProjects: prefetchProjectsHandler,
    prefetchEmails: prefetchEmailsHandler,
    prefetchBilling,
    prefetchIntelligence,
  };
};

// Helper function for intelligence prefetch
const prefetchIntelligence = () => {
  queryClient.prefetchQuery({
    queryKey: queryKeys.stats.dashboard(30),
    queryFn: async () => {
      const res = await statsApi.get(30);
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });
};

export default usePrefetch;
