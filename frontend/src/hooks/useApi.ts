import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  quotesApi,
  quotesApiExtended,
  customersApi,
  productsApi,
  projectsApi,
  emailsApi,
  statsApi,
  knowledgeBaseApi,
  billingApi,
  extractionsApi,
  uploadApi,
} from '../services/api';
import { queryKeys } from '../lib/queryClient';

// Quotes Hooks
export const useQuotes = (limit = 50) => {
  return useQuery({
    queryKey: queryKeys.quotes.list(limit),
    queryFn: async () => {
      const res = await quotesApi.list(limit);
      return res.data || [];
    },
  });
};

export const useQuote = (id: string) => {
  return useQuery({
    queryKey: queryKeys.quotes.detail(id),
    queryFn: async () => {
      const res = await quotesApi.get(id);
      return res.data;
    },
    enabled: !!id,
  });
};

export const useCreateQuote = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => quotesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.all });
    },
  });
};

export const useUpdateQuote = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => quotesApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.all });
    },
  });
};

export const useUpdateQuoteStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      quotesApi.updateStatus(id, status),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.all });
    },
  });
};

// Customers Hooks
export const useCustomers = (limit = 100) => {
  return useQuery({
    queryKey: queryKeys.customers.list(limit),
    queryFn: async () => {
      const res = await customersApi.list(limit);
      return res.data || [];
    },
  });
};

export const useCreateCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => customersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.all });
    },
  });
};

// Products Hooks
export const useProducts = (limit = 100) => {
  return useQuery({
    queryKey: queryKeys.products.list(limit),
    queryFn: async () => {
      const res = await productsApi.list(limit);
      return res.data || [];
    },
  });
};

export const useSearchProducts = (query: string) => {
  return useQuery({
    queryKey: queryKeys.products.search(query),
    queryFn: async () => {
      const res = await productsApi.search(query);
      return res.data || [];
    },
    enabled: query.length > 0,
  });
};

export const useUploadProducts = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => productsApi.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all });
    },
  });
};

// Projects Hooks
export const useProjects = (limit = 100) => {
  return useQuery({
    queryKey: queryKeys.projects.list(limit),
    queryFn: async () => {
      const res = await projectsApi.list(limit);
      return res.data || [];
    },
  });
};

export const useProject = (id: string) => {
  return useQuery({
    queryKey: queryKeys.projects.detail(id),
    queryFn: async () => {
      const res = await projectsApi.get(id);
      return res.data;
    },
    enabled: !!id,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
};

export const useProjectQuotes = (id: string) => {
  return useQuery({
    queryKey: queryKeys.projects.quotes(id),
    queryFn: async () => {
      const res = await projectsApi.getQuotes(id);
      return res.data || [];
    },
    enabled: !!id,
  });
};

// Emails Hooks
export const useEmails = (status?: string, limit = 50) => {
  return useQuery({
    queryKey: queryKeys.emails.list(status, limit),
    queryFn: async () => {
      const res = await emailsApi.list(status, limit);
      return res.data || [];
    },
  });
};

export const useEmail = (id: string) => {
  return useQuery({
    queryKey: queryKeys.emails.detail(id),
    queryFn: async () => {
      const res = await emailsApi.get(id);
      return res.data;
    },
    enabled: !!id,
  });
};

// Stats Hooks
export const useStats = (days = 30) => {
  return useQuery({
    queryKey: queryKeys.stats.dashboard(days),
    queryFn: async () => {
      const res = await statsApi.get(days);
      return res.data;
    },
  });
};

// Dashboard Data Hook (combines multiple queries)
export const useDashboardData = () => {
  const quotes = useQuotes(100);
  const customers = useCustomers(100);
  const emails = useEmails('pending', 50);

  return {
    quotes: quotes.data || [],
    customers: customers.data || [],
    emails: emails.data || [],
    isLoading: quotes.isLoading || customers.isLoading || emails.isLoading,
    isError: quotes.isError || customers.isError || emails.isError,
    error: quotes.error || customers.error || emails.error,
  };
};

// Knowledge Base Hooks
export const useKnowledgeStatus = () => {
  return useQuery({
    queryKey: queryKeys.knowledgeBase.status,
    queryFn: async () => {
      const res = await knowledgeBaseApi.getStatus();
      return res.data;
    },
  });
};

export const useKnowledgeDocuments = () => {
  return useQuery({
    queryKey: queryKeys.knowledgeBase.documents,
    queryFn: async () => {
      const res = await knowledgeBaseApi.listDocuments();
      return res.data || [];
    },
  });
};

// Billing Hooks
export const useSubscription = () => {
  return useQuery({
    queryKey: queryKeys.billing.subscription,
    queryFn: async () => {
      const res = await billingApi.getSubscription();
      return res.data;
    },
  });
};

export const useBillingPlans = () => {
  return useQuery({
    queryKey: queryKeys.billing.plans,
    queryFn: async () => {
      const res = await billingApi.getPlans();
      return res.data || [];
    },
  });
};

export const useBillingUsage = () => {
  return useQuery({
    queryKey: queryKeys.billing.usage,
    queryFn: async () => {
      const res = await billingApi.getUsage();
      return res.data;
    },
  });
};

// Extraction Hooks
export const useExtractionParse = () => {
  return useMutation({
    mutationFn: (data: { text: string; source_type?: string }) =>
      extractionsApi.parse(data),
  });
};

export const useUnifiedExtraction = () => {
  return useMutation({
    mutationFn: (data: { text?: string; file?: File; source_type?: string }) =>
      extractionsApi.unifiedParse(data),
  });
};

// Upload Hook
export const useUpload = () => {
  return useMutation({
    mutationFn: (file: File) => uploadApi.upload(file),
  });
};
