import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || import.meta.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Timeout so hung requests (backend down, CORS, network) don't leave tabs spinning forever
const REQUEST_TIMEOUT_MS = 20000;

// CSRF token cache
let csrfToken: string | null = null;
let csrfTokenFetched = false;

export const api = axios.create({
    baseURL: API_URL,
    timeout: REQUEST_TIMEOUT_MS,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Important: allows cookies to be sent/received
});

// Fetch CSRF token
const fetchCSRFToken = async (): Promise<string | null> => {
    try {
        const response = await axios.get(`${API_URL}/auth/csrf-token`, {
            withCredentials: true,
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('mercura_token') || ''}`,
            },
        });
        return response.data.csrf_token;
    } catch (error) {
        console.warn('Failed to fetch CSRF token:', error);
        return null;
    }
};

// Add auth token and CSRF token to requests
api.interceptors.request.use(async (config) => {
    // Add auth token
    const token = localStorage.getItem('mercura_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    // Add CSRF token for state-changing operations
    const method = config.method?.toUpperCase();
    if (method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
        // Fetch token if not cached
        if (!csrfTokenFetched || !csrfToken) {
            csrfToken = await fetchCSRFToken();
            csrfTokenFetched = true;
        }

        if (csrfToken) {
            config.headers['X-CSRF-Token'] = csrfToken;
        }
    }

    return config;
});

// Handle CSRF errors - refresh token on 403
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Check if it's a CSRF error
        if (error.response?.status === 403 &&
            error.response?.data?.detail?.includes('CSRF') &&
            !originalRequest._retry) {

            originalRequest._retry = true;

            // Refresh CSRF token
            csrfToken = await fetchCSRFToken();
            if (csrfToken) {
                originalRequest.headers['X-CSRF-Token'] = csrfToken;
                return api(originalRequest);
            }
        }

        return Promise.reject(error);
    }
);

export const quotesApi = {
    list: (limit = 50) => api.get(`/quotes?limit=${limit}`),
    get: (id: string) => api.get(`/quotes/${id}`),
    create: (data: any, idempotencyKey?: string) => api.post('/quotes/', data, {
        headers: idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {}
    }),
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

        // CRITICAL FIX: Extended timeout for AI extraction (90 seconds)
        // Large files + AI processing can take time, but we need a reasonable limit
        return api.post('/extract/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: 90000, // 90 seconds for AI extraction (vs default 20s)
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
    getConfig: () => api.get('/billing/config'),
    getPlans: () => api.get('/billing/plans'),
    getSubscription: () => api.get('/billing/subscription'),
    updateSubscription: (data: any) => api.post('/billing/subscription/update', data),
    cancelSubscription: (cancelAtPeriodEnd: boolean = true, reason?: string, feedback?: string) =>
        api.post('/billing/subscription/cancel', {
            cancel_at_period_end: cancelAtPeriodEnd,
            ...(reason && { reason }),
            ...(feedback && { feedback }),
        }),
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

// Account self-service (e.g. delete)
export const accountApi = {
    deleteAccount: () => api.post('/account/delete'),
};

export const erpApi = {
    exportQuote: (quoteId: string, format: string) =>
        api.post(`/export/quote/${quoteId}/send?format=${format}`),
    downloadQuote: (quoteId: string, format: string) =>
        api.get(`/export/quote/${quoteId}?format=${format}`, { responseType: 'blob' }),
};

// AI Copilot API - Industrial Subject Matter Expert
export const copilotApi = {
    // Process a natural language command
    command: (command: string, quoteId?: string, context?: any) =>
        api.post('/copilot/command', { command, quote_id: quoteId, context }),

    // Analyze a quote and get recommendations
    analyze: (quoteId: string) => api.get(`/copilot/analyze/${quoteId}`),

    // Get context-aware command suggestions
    getSuggestions: (quoteId: string) => api.get(`/copilot/suggestions/${quoteId}`),

    // Apply a copilot-suggested change
    applyChange: (quoteId: string, change: any) =>
        api.post('/copilot/apply-change', { quote_id: quoteId, change }),

    // Health check
    health: () => api.get('/copilot/health'),
};

// PDF Generation API
export const pdfApi = {
    // Download quote as PDF
    downloadQuote: (quoteId: string) =>
        api.get(`/pdf/quote/${quoteId}`, { responseType: 'blob' }),

    // Preview quote PDF (inline)
    previewQuote: (quoteId: string) =>
        api.get(`/pdf/quote/${quoteId}/preview`, { responseType: 'blob' }),

    // Check PDF service status
    status: () => api.get('/pdf/status'),
};

// Email API
export const emailApi = {
    // Send quote via email with PDF attachment
    sendQuote: (quoteId: string, data: { to_email: string; to_name?: string; message?: string; include_pdf?: boolean }) =>
        api.post(`/email/quote/${quoteId}/send`, data),

    // Send custom email
    sendEmail: (data: { to_email: string; to_name?: string; subject: string; body_text: string; body_html?: string }) =>
        api.post('/email/send', data),

    // Test email configuration
    testConfig: (testEmail: string) =>
        api.post('/email/test', { test_email: testEmail }),

    // Check email service status
    status: () => api.get('/email/status'),
};

// CSV Import API
export const importApi = {
    // Preview import before committing
    preview: (importType: string, file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post(`/import/preview/${importType}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    // Import products
    importProducts: (file: File, columnMapping?: Record<string, string>) => {
        const formData = new FormData();
        formData.append('file', file);
        if (columnMapping) {
            formData.append('column_mapping', JSON.stringify(columnMapping));
        }
        return api.post('/import/products', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    // Import customers
    importCustomers: (file: File, columnMapping?: Record<string, string>) => {
        const formData = new FormData();
        formData.append('file', file);
        if (columnMapping) {
            formData.append('column_mapping', JSON.stringify(columnMapping));
        }
        return api.post('/import/customers', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    // Download import template
    downloadTemplate: (templateType: string) =>
        api.get(`/import/templates/${templateType}`, { responseType: 'blob' }),

    // Check import service status
    status: () => api.get('/import/status'),
};

// Auth API
export const authApi = {
    login: (email: string, password: string) =>
        api.post('/auth/login', { email, password }),

    register: (email: string, password: string, name: string, companyName: string) =>
        api.post('/auth/register', { email, password, name, company_name: companyName }),

    logout: () => api.post('/auth/logout'),

    me: () => api.get('/auth/me'),
};

// Demo Data API
export const demoDataApi = {
    load: () => api.post('/data/demo-data'),
};

// Settings API
export const settingsApi = {
    // Email Settings
    getEmailSettings: () => api.get('/settings/email'),
    updateEmailSettings: (data: {
        smtp_host: string;
        smtp_port: number;
        smtp_username: string;
        smtp_password: string;
        from_email?: string;
        from_name: string;
        use_tls: boolean;
        is_enabled: boolean;
    }) => api.post('/settings/email', data),
    deleteEmailSettings: () => api.delete('/settings/email'),
    testEmailConfig: (test_email: string) => api.post('/settings/email/test', { test_email }),
    getEmailProviders: () => api.get('/settings/email/providers'),
};

// Alerts API
export const alertsApi = {
    list: (unread_only: boolean = false, limit: number = 50) =>
        api.get(`/alerts/?unread_only=${unread_only}&limit=${limit}`),
    getUnreadCount: () => api.get('/alerts/unread-count'),
    check: () => api.post('/alerts/check'),
    markRead: (alertId: string) => api.post(`/alerts/${alertId}/read`),
    markAllRead: () => api.post('/alerts/mark-all-read'),
    dismiss: (alertId: string) => api.delete(`/alerts/${alertId}`),
    getTypes: () => api.get('/alerts/types'),
};

// Export consolidated in earlier emailApi definition above
