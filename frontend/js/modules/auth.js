/**
 * LumaCart Authentication Module
 */
class AuthManager {
    constructor() {
        this.user = this.loadUser();
    }

    loadUser() {
        try {
            const raw = localStorage.getItem('lumacart_user');
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    setUser(user) {
        this.user = user;
        if (user) {
            localStorage.setItem('lumacart_user', JSON.stringify(user));
        } else {
            localStorage.removeItem('lumacart_user');
        }
        window.dispatchEvent(new CustomEvent('auth:change', { detail: { user } }));
    }

    isAuthenticated() {
        return !!window.apiClient.getAccessToken() && !!this.user;
    }

    isStaff() {
        return this.user && !!this.user.is_staff;
    }

    async login(email, password) {
        const response = await window.apiClient.post('/auth/login/', { email, password });
        const data = await ApiClient.parseResponse(response);

        if (!response.ok) {
            throw new Error(data.error || 'Login failed. Please check your credentials.');
        }

        window.apiClient.setTokens(data.tokens.access, data.tokens.refresh);
        this.setUser(data.user);

        // Merge any guest cart into user's DB cart
        try {
            await window.cartManager.mergeGuestCart();
        } catch (e) {
            console.warn('Guest cart merge deferred:', e);
        }

        return data;
    }

    async register(userData) {
        const response = await window.apiClient.post('/auth/register/', userData);
        const data = await ApiClient.parseResponse(response);

        if (!response.ok) {
            let errorMsg = 'Registration failed.';
            if (data.email) errorMsg = data.email[0];
            else if (data.password) errorMsg = data.password[0];
            else if (data.password_confirm) errorMsg = data.password_confirm[0];
            else if (data.error) errorMsg = data.error;
            throw new Error(errorMsg);
        }

        window.apiClient.setTokens(data.tokens.access, data.tokens.refresh);
        this.setUser(data.user);

        // Merge guest cart
        try {
            await window.cartManager.mergeGuestCart();
        } catch (e) {}

        return data;
    }

    logout() {
        window.apiClient.clearTokens();
        this.setUser(null);
        window.Toast.info('You have been logged out.');
        setTimeout(() => {
            window.location.href = '/index.html';
        }, 800);
    }

    async fetchProfile() {
        if (!this.isAuthenticated()) return null;
        try {
            const res = await window.apiClient.get('/auth/profile/');
            if (res.ok) {
                const user = await res.json();
                this.setUser(user);
                return user;
            }
        } catch (e) {
            console.error('Failed to fetch profile:', e);
        }
        return this.user;
    }

    updateNav() {
        const accountContainer = document.getElementById('nav-account-container');
        if (!accountContainer) return;

        if (this.isAuthenticated() && this.user) {
            const displayName = this.user.first_name || this.user.email.split('@')[0];
            const adminMenuItem = this.isStaff() 
                ? `<li><a href="/pages/admin.html" class="dropdown-item"><span class="icon">⚙</span> Staff Admin</a></li>` 
                : '';

            accountContainer.innerHTML = `
                <div class="dropdown">
                    <button class="nav-btn account-btn" id="accountMenuBtn" aria-label="Account Menu">
                        <span class="avatar-initial">${displayName.charAt(0).toUpperCase()}</span>
                        <span class="user-name-text">${displayName}</span>
                        <span class="dropdown-chevron">▾</span>
                    </button>
                    <div class="dropdown-menu" id="accountDropdownMenu">
                        <div class="dropdown-header">
                            <p class="dropdown-user-name">${this.user.first_name} ${this.user.last_name || ''}</p>
                            <p class="dropdown-user-email">${this.user.email}</p>
                        </div>
                        <div class="dropdown-divider"></div>
                        <ul class="dropdown-list">
                            <li><a href="/pages/orders.html" class="dropdown-item"><span class="icon">📦</span> My Orders</a></li>
                            <li><a href="/pages/wishlist.html" class="dropdown-item"><span class="icon">♡</span> Wishlist</a></li>
                            <li><a href="/pages/profile.html" class="dropdown-item"><span class="icon">👤</span> Account Settings</a></li>
                            ${adminMenuItem}
                            <div class="dropdown-divider"></div>
                            <li><button id="logoutBtn" class="dropdown-item text-danger"><span class="icon">↳</span> Sign Out</button></li>
                        </ul>
                    </div>
                </div>
            `;

            document.getElementById('logoutBtn')?.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });

            // Dropdown toggle
            const btn = document.getElementById('accountMenuBtn');
            const menu = document.getElementById('accountDropdownMenu');
            if (btn && menu) {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    menu.classList.toggle('active');
                });
                document.addEventListener('click', () => {
                    menu.classList.remove('active');
                });
            }
        } else {
            accountContainer.innerHTML = `
                <div class="auth-action-buttons">
                    <a href="/pages/login.html" class="btn btn-ghost btn-sm">Sign In</a>
                    <a href="/pages/register.html" class="btn btn-primary btn-sm">Register</a>
                </div>
            `;
        }
    }
}

window.authManager = new AuthManager();
