import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || import.meta.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Mock User ID for "Sales-Ready MVP" since we don't have full auth yet
// In a real app, this would come from AuthContext
const TEST_USER_ID = '3d4df718-47c3-4903-b09e-711090412204'; // UUID format

// Timeout so hung requests (backend down, CORS, network) don't leave tabs spinning forever
const REQUEST_TIMEOUT_MS = 20000;

export const api = axios.create({
    baseURL: API_URL,
    timeout: REQUEST_TIMEOUT_MS,
    headers: {
        'Content-Type': 'application/json',
        'X-User-ID': TEST_USER_ID,
    },
});

export const quotesApi = {
    list: (limit = 50) => api.get(`/quotes?limit=${limit}`),
    get: (id: string) => api.get(`/quotes/${id}`),
    create: (data: any) => api.post('/quotes/', data),
    update: (id: string, data: any) => api.put(`/quotes/${id}`, data),
    patchUpdate: (id: string, data: any) => api.patch(`/quotes/${id}`, data),
    updateStatus: (id: string, status: string) => api.patch(`/quotes/${id}/status?status=${status}`),
};

export const productsApi = {
    list: (limit = 100) => api.get(`/products?limit=${limit}`),
    search: (query: string) => api.get(`/products/search?query=${query}`),
    upload: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/products/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
    uploadCompetitorMap: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/products/competitor-maps/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
    suggest: (items: any[]) => api.post('/products/suggest', { items }),
    chat: (query: string) => api.post('/products/chat', { query }),
    create: (data: any) => api.post('/products/', data),
};

export const customersApi = {
    list: (limit = 100) => api.get(`/customers?limit=${limit}`),
    create: (data: any) => api.post('/customers/', data),
};

export const projectsApi = {
    list: (limit = 100) => api.get(`/projects?limit=${limit}`),
    get: (id: string) => api.get(`/projects/${id}`),
    create: (data: any) => api.post('/projects/', data),
    update: (id: string, data: any) => api.patch(`/projects/${id}`, data),
    getQuotes: (id: string) => api.get(`/projects/${id}/quotes`),
};

export const emailsApi = {
    list: (status?: string, limit = 50) => api.get(`/data/emails?limit=${limit}${status ? `&status=${status}` : ''}`),
    get: (id: string) => api.get(`/data/emails/${id}`),
};

export const quotesApiExtended = {
    ...quotesApi,
    getByEmail: (emailId: string) => api.get(`/quotes/email/${emailId}`),
    generateExport: (quoteId: string, format: 'excel' | 'pdf' = 'excel') =>
        api.get(`/quotes/${quoteId}/generate-export?format=${format}`, { responseType: 'blob' }),
    draftReply: (quoteId: string) => api.post(`/quotes/${quoteId}/draft-reply`),
    generateLink: (quoteId: string) => api.post(`/quotes/${quoteId}/generate-link`),
    getPublicQuote: (token: string) => axios.get(`${API_URL}/quotes/public/${token}`),
    confirmQuote: (token: string, data: any) => axios.post(`${API_URL}/quotes/public/${token}/confirm`, data),
};

export const uploadApi = {
    upload: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/webhooks/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
};

export const statsApi = {
    get: (days: number = 30) => api.get(`/data/stats?days=${days}`),
};

export const extractionsApi = {
    parse: (data: { text: string; source_type?: string }) => api.post('/extractions/parse', data),
    list: (status?: string) => api.get(`/extractions/${status ? `?status=${status}` : ''}`),
    // Unified extraction (Text, Image, PDF, Excel)
    unifiedParse: (data: { text?: string; file?: File; source_type?: string }) => {
        const formData = new FormData();
        if (data.text) formData.append('text', data.text);
        if (data.file) formData.append('file', data.file);
        if (data.source_type) formData.append('source_type', data.source_type);

        return api.post('/extract/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
};

// Knowledge Base API (optional feature)
export const knowledgeBaseApi = {
    getStatus: () => api.get('/knowledge/status'),
    query: (question: string, docTypes?: string, useAi: boolean = true) => {
        const formData = new FormData();
        formData.append('question', question);
        formData.append('use_ai', String(useAi));
        if (docTypes) formData.append('doc_types', docTypes);
        return api.post('/knowledge/query', formData);
    },
    ingest: (file: File, docType: string, supplier?: string) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('doc_type', docType);
        if (supplier) formData.append('supplier', supplier);
        return api.post('/knowledge/ingest', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
    listDocuments: () => api.get('/knowledge/documents'),
};

// Billing API
export const billingApi = {
    getPlans: () => api.get('/billing/plans'),
    getSubscription: () => api.get('/billing/subscription'),
    updateSubscription: (data: any) => api.post('/billing/subscription/update', data),
    cancelSubscription: (cancelAtPeriodEnd: boolean = true) =>
        api.post('/billing/subscription/cancel', { cancel_at_period_end: cancelAtPeriodEnd }),
    createCheckoutSession: (data: any) => api.post('/billing/checkout/create-session', data),
    createBillingPortalSession: (returnUrl: string) =>
        api.post('/billing/portal/create-session', { return_url: returnUrl }),
    getInvoices: () => api.get('/billing/invoices'),
    getInvoice: (invoiceId: string) => api.get(`/billing/invoices/${invoiceId}`),
    getSeats: () => api.get('/billing/seats'),
    assignSeat: (email: string, name?: string) =>
        api.post('/billing/seats/assign', { sales_rep_email: email, sales_rep_name: name }),
    deactivateSeat: (seatId: string) => api.post(`/billing/seats/${seatId}/deactivate`),
    getUsage: () => api.get('/billing/usage'),
};

export const quickbooksApi = {
    exportQuote: (quoteId: string) => api.post(`/quickbooks/export-quote?quote_id=${quoteId}`),
};

export const organizationsApi = {
    getMe: () => api.get('/organizations/me'),
    getMembers: (orgId: string) => api.get(`/organizations/${orgId}/members`),
};
