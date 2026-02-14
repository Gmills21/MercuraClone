/**
 * Authentication Context for Mercura
 * Handles login, register, logout, and token management
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface User {
    id: string;
    email: string;
    name: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, name: string, companyName: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = import.meta.env.VITE_API_URL || import.meta.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Initialize auth state from localStorage
    useEffect(() => {
        const storedToken = localStorage.getItem('mercura_token');
        const storedUser = localStorage.getItem('mercura_user');

        if (storedToken && storedUser) {
            try {
                const parsedUser = JSON.parse(storedUser);
                setToken(storedToken);
                setUser(parsedUser);

                // Validate token is still valid (optional - can add API call here)
                // For now, we trust localStorage until an API call fails
            } catch (error) {
                console.error('Failed to parse stored user:', error);
                // Clear invalid data
                localStorage.removeItem('mercura_token');
                localStorage.removeItem('mercura_user');
            }
        }
        setIsLoading(false);
    }, []);

    const login = useCallback(async (email: string, password: string) => {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();

        // CRITICAL: Immediately persist to localStorage BEFORE setting state
        // This prevents race conditions where page refresh happens before state sync
        localStorage.setItem('mercura_token', data.access_token);
        localStorage.setItem('mercura_user', JSON.stringify(data.user));

        // Then update React state
        setToken(data.access_token);
        setUser(data.user);
    }, []);

    const register = useCallback(async (email: string, password: string, name: string, companyName: string) => {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, name, company_name: companyName }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }

        const data = await response.json();

        // CRITICAL: Immediately persist to localStorage BEFORE setting state
        localStorage.setItem('mercura_token', data.access_token);
        localStorage.setItem('mercura_user', JSON.stringify(data.user));

        // Then update React state
        setToken(data.access_token);
        setUser(data.user);

        // Store onboarding flag
        if (data.onboarding_required) {
            localStorage.setItem('mercura_onboarding_required', 'true');
        }
    }, []);

    const logout = useCallback(async () => {
        if (token) {
            try {
                await fetch(`${API_URL}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                });
            } catch (e) {
                // Ignore logout errors
            }
        }

        setToken(null);
        setUser(null);
        localStorage.removeItem('mercura_token');
        localStorage.removeItem('mercura_user');
        localStorage.removeItem('mercura_onboarding_required');
    }, [token]);

    return (
        <AuthContext.Provider value={{
            user,
            token,
            isLoading,
            isAuthenticated: !!token && !!user,
            login,
            register,
            logout,
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
