import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Mock User ID for "Sales-Ready MVP" since we don't have full auth yet
// In a real app, this would come from AuthContext
const TEST_USER_ID = '3d4df718-47c3-4903-b09e-711090412204'; // UUID format

export const api = axios.create({
    baseURL: API_URL,
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
    updateStatus: (id: string, status: string) => api.patch(`/quotes/${id}/status?status=${status}`),
};

export const productsApi = {
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
};

export const customersApi = {
    list: (limit = 100) => api.get(`/customers?limit=${limit}`),
    create: (data: any) => api.post('/customers/', data),
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
