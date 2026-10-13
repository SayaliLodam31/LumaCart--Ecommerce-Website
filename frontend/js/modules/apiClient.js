/**
 * LumaCart Centralized API Client
 * Handles JWT token injection, auto-refresh on 401, guest session tracking, and error normalization.
 */
class ApiClient {
    constructor() {
        this.baseUrl = window.CONFIG ? window.CONFIG.API_BASE : 'http://127.0.0.1:8000/api';
        this.isRefreshing = false;
        this.failedQueue = [];
    }

    getSessionKey() {
        let key = localStorage.getItem('lumacart_session_key');
        if (!key) {
            key = 'sess_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            localStorage.setItem('lumacart_session_key', key);
        }
        return key;
    }

    getAccessToken() {
        return localStorage.getItem('lumacart_access_token');
    }

    getRefreshToken() {
        return localStorage.getItem('lumacart_refresh_token');
    }

    setTokens(access, refresh) {
        if (access) localStorage.setItem('lumacart_access_token', access);
        if (refresh) localStorage.setItem('lumacart_refresh_token', refresh);
    }

    clearTokens() {
        localStorage.removeItem('lumacart_access_token');
        localStorage.removeItem('lumacart_refresh_token');
        localStorage.removeItem('lumacart_user');
    }

    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
        
        options.headers = options.headers || {};
        
        // Add content type if sending body and not FormData
        if (options.body && !(options.body instanceof FormData) && !options.headers['Content-Type']) {
            options.headers['Content-Type'] = 'application/json';
        }

        // Add guest session key
        options.headers['X-Session-Key'] = this.getSessionKey();

        // Add JWT bearer token if available
        const token = this.getAccessToken();
        if (token && !options.headers['Authorization']) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, options);

            // Handle 401 Unauthorized - Attempt token refresh
            if (response.status === 401 && this.getRefreshToken() && !options._retry && !endpoint.includes('/auth/login/')) {
                options._retry = true;
                const newAccess = await this.refreshAccessToken();
                if (newAccess) {
                    options.headers['Authorization'] = `Bearer ${newAccess}`;
                    return await fetch(url, options);
                }
            }

            return response;
        } catch (error) {
            console.error('API Client Network Error:', error);
            throw error;
        }
    }

    async refreshAccessToken() {
        const refresh = this.getRefreshToken();
        if (!refresh) return null;

        try {
            const res = await fetch(`${this.baseUrl}/auth/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh })
            });

            if (res.ok) {
                const data = await res.json();
                this.setTokens(data.access, data.refresh);
                return data.access;
            } else {
                this.clearTokens();
                window.dispatchEvent(new CustomEvent('auth:logout'));
                return null;
            }
        } catch (e) {
            this.clearTokens();
            return null;
        }
    }

    async get(endpoint, params = {}) {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== null && v !== '') {
                query.append(k, v);
            }
        });
        const queryString = query.toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    async post(endpoint, data = {}) {
        const isFormData = data instanceof FormData;
        return this.request(endpoint, {
            method: 'POST',
            body: isFormData ? data : JSON.stringify(data)
        });
    }

    async patch(endpoint, data = {}) {
        const isFormData = data instanceof FormData;
        return this.request(endpoint, {
            method: 'PATCH',
            body: isFormData ? data : JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    static async parseResponse(response) {
        const text = await response.text();
        try {
            return text ? JSON.parse(text) : {};
        } catch (e) {
            return { error: text || 'Invalid server response' };
        }
    }
}

window.apiClient = new ApiClient();
