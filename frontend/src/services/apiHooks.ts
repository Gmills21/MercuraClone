// React Query hooks for OpenMercura API
// These hooks provide a type-safe, cached interface to all API calls

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryClient';
import {
  quotesApi,
  productsApi,
  customersApi,
  projectsApi,
  emailsApi,
  quotesApiExtended,
  statsApi,
  extractionsApi,
  knowledgeBaseApi,
  billingApi,
  quickbooksApi,
  organizationsApi,
  uploadApi,
} from './api';

// ==================== QUOTES ====================

export const useQuotes = (limit = 50) => {
  return useQuery({
    queryKey: queryKeys.quotes.list(limit),
    queryFn: () => quotesApi.list(limit).then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useQuote = (id: string | undefined) => {
  return useQuery({
    queryKey: queryKeys.quotes.detail(id || ''),
    queryFn: () => quotesApi.get(id!).then(res => res.data),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateQuote = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => quotesApi.create(data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.all });
    },
  });
};

export const useUpdateQuote = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      quotesApi.update(id, data).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.detail(variables.id) });
    },
  });
};

// ==================== CUSTOMERS ====================

export const useCustomers = (limit = 100) => {
  return useQuery({
    queryKey: queryKeys.customers.list(limit),
    queryFn: () => customersApi.list(limit).then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => customersApi.create(data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.all });
    },
  });
};

// ==================== PRODUCTS ====================

export const useProducts = (limit = 100) => {
  return useQuery({
    queryKey: queryKeys.products.list(limit),
    queryFn: () => productsApi.list(limit).then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useProductSearch = (query: string) => {
  return useQuery({
    queryKey: queryKeys.products.search(query),
    queryFn: () => productsApi.search(query).then(res => res.data),
    enabled: query.length > 0,
    staleTime: 2 * 60 * 1000,
  });
};

export const useCreateProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => productsApi.create(data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all });
    },
  });
};

// ==================== PROJECTS ====================

export const useProjects = (limit = 100) => {
  return useQuery({
    queryKey: queryKeys.projects.list(limit),
    queryFn: () => projectsApi.list(limit).then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useProject = (id: string | undefined) => {
  return useQuery({
    queryKey: queryKeys.projects.detail(id || ''),
    queryFn: () => projectsApi.get(id!).then(res => res.data),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
};

export const useProjectQuotes = (id: string | undefined) => {
  return useQuery({
    queryKey: queryKeys.projects.quotes(id || ''),
    queryFn: () => projectsApi.getQuotes(id!).then(res => res.data),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => projectsApi.create(data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
};

// ==================== EMAILS ====================

export const useEmails = (status?: string, limit = 50) => {
  return useQuery({
    queryKey: queryKeys.emails.list(status, limit),
    queryFn: () => emailsApi.list(status, limit).then(res => res.data),
    staleTime: 2 * 60 * 1000,
  });
};

// ==================== STATS ====================

export const useStats = (days = 30) => {
  return useQuery({
    queryKey: queryKeys.stats.dashboard(days),
    queryFn: () => statsApi.get(days).then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

// ==================== KNOWLEDGE BASE ====================

export const useKnowledgeBaseStatus = () => {
  return useQuery({
    queryKey: queryKeys.knowledgeBase.status,
    queryFn: () => knowledgeBaseApi.getStatus().then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useKnowledgeBaseDocuments = () => {
  return useQuery({
    queryKey: queryKeys.knowledgeBase.documents,
    queryFn: () => knowledgeBaseApi.listDocuments().then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

// ==================== BILLING ====================

export const useBillingPlans = () => {
  return useQuery({
    queryKey: queryKeys.billing.plans,
    queryFn: () => billingApi.getPlans().then(res => res.data),
    staleTime: 60 * 60 * 1000, // 1 hour
  });
};

export const useBillingSubscription = () => {
  return useQuery({
    queryKey: queryKeys.billing.subscription,
    queryFn: () => billingApi.getSubscription().then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useBillingInvoices = () => {
  return useQuery({
    queryKey: queryKeys.billing.invoices,
    queryFn: () => billingApi.getInvoices().then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useBillingSeats = () => {
  return useQuery({
    queryKey: queryKeys.billing.seats,
    queryFn: () => billingApi.getSeats().then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useBillingUsage = () => {
  return useQuery({
    queryKey: queryKeys.billing.usage,
    queryFn: () => billingApi.getUsage().then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

// ==================== ORGANIZATION ====================

export const useOrganization = () => {
  return useQuery({
    queryKey: queryKeys.organization.me,
    queryFn: () => organizationsApi.getMe().then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

export const useOrganizationMembers = (orgId: string | undefined) => {
  return useQuery({
    queryKey: queryKeys.organization.members(orgId || ''),
    queryFn: () => organizationsApi.getMembers(orgId!).then(res => res.data),
    enabled: !!orgId,
    staleTime: 5 * 60 * 1000,
  });
};

// ==================== MUTATIONS ====================

// Generic upload mutation
export const useUpload = () => {
  return useMutation({
    mutationFn: (file: File) => uploadApi.upload(file).then(res => res.data),
  });
};

// Product catalog upload
export const useUploadCatalog = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => productsApi.upload(file).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all });
    },
  });
};

// Competitor mapping upload
export const useUploadCompetitorMap = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => productsApi.uploadCompetitorMap(file).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all });
    },
  });
};

// Extraction mutation
export const useExtract = () => {
  return useMutation({
    mutationFn: (data: { text?: string; file?: File; source_type?: string }) =>
      extractionsApi.unifiedParse(data).then(res => res.data),
  });
};

// Knowledge base ingest
export const useKnowledgeBaseIngest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, docType, supplier }: { file: File; docType: string; supplier?: string }) =>
      knowledgeBaseApi.ingest(file, docType, supplier).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeBase.documents });
    },
  });
};

// QuickBooks export
export const useQuickbooksExport = () => {
  return useMutation({
    mutationFn: (quoteId: string) => quickbooksApi.exportQuote(quoteId).then(res => res.data),
  });
};

// Quote status update with optimistic update
export const useUpdateQuoteStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      quotesApi.updateStatus(id, status).then(res => res.data),
    onMutate: async ({ id, status }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.quotes.detail(id) });

      // Snapshot previous value
      const previousQuote = queryClient.getQueryData(queryKeys.quotes.detail(id));

      // Optimistically update
      queryClient.setQueryData(queryKeys.quotes.detail(id), (old: any) => ({
        ...old,
        status,
      }));

      return { previousQuote };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousQuote) {
        queryClient.setQueryData(
          queryKeys.quotes.detail(variables.id),
          context.previousQuote
        );
      }
    },
    onSettled: (data, error, variables) => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.quotes.all });
    },
  });
};

// Generate quote link
export const useGenerateQuoteLink = () => {
  return useMutation({
    mutationFn: (quoteId: string) => quotesApiExtended.generateLink(quoteId).then(res => res.data),
  });
};

// Draft reply
export const useDraftReply = () => {
  return useMutation({
    mutationFn: (quoteId: string) => quotesApiExtended.draftReply(quoteId).then(res => res.data),
  });
};

// ==================== PREFETCH HOOKS ====================

export const usePrefetchQuote = () => {
  const queryClient = useQueryClient();

  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.quotes.detail(id),
      queryFn: () => quotesApi.get(id).then(res => res.data),
      staleTime: 5 * 60 * 1000,
    });
  };
};

export const usePrefetchCustomer = () => {
  const queryClient = useQueryClient();

  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.customers.detail(id),
      queryFn: async () => {
        // Customer detail not in base API, fetch from list
        const res = await customersApi.list(100);
        return res.data.find((c: any) => c.id === id);
      },
      staleTime: 5 * 60 * 1000,
    });
  };
};
