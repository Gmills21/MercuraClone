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
    updateStatus: (id: string, status: string) => api.patch(`/quotes/${id}/status?status=${status}`),
};

export const productsApi = {
    search: (query: string) => api.get(`/products/search?query=${query}`),
};

export const customersApi = {
    list: (limit = 100) => api.get(`/customers?limit=${limit}`),
    create: (data: any) => api.post('/customers/', data),
};
