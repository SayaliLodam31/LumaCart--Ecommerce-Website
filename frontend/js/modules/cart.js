/**
 * LumaCart Shopping Cart Module
 * Database-backed cart with guest fallback and automatic server-side recalculation.
 */
class CartManager {
    constructor() {
        this.cart = null;
        this.isLoading = false;
    }

    async getCart() {
        try {
            const res = await window.apiClient.get('/cart/');
            if (res.ok) {
                this.cart = await res.json();
                this.updateBadges();
                return this.cart;
            }
        } catch (e) {
            console.error('Failed to fetch cart:', e);
        }
        return this.cart;
    }

    async addToCart(variantId, quantity = 1) {
        try {
            const res = await window.apiClient.post('/cart/items/', {
                variant_id: variantId,
                quantity: parseInt(quantity)
            });
            const data = await ApiClient.parseResponse(res);

            if (!res.ok) {
                window.Toast.error(data.error || 'Failed to add item to cart.');
                return false;
            }

            this.cart = data.cart;
            this.updateBadges();
            window.Toast.success(data.message || 'Item added to bag!');
            window.dispatchEvent(new CustomEvent('cart:updated', { detail: { cart: this.cart } }));
            return true;
        } catch (e) {
            window.Toast.error('Network error. Could not add item.');
            return false;
        }
    }

    async updateQuantity(itemId, quantity) {
        try {
            const res = await window.apiClient.patch(`/cart/items/${itemId}/`, { quantity });
            const data = await ApiClient.parseResponse(res);

            if (!res.ok) {
                window.Toast.error(data.error || 'Failed to update quantity.');
                return false;
            }

            this.cart = data.cart;
            this.updateBadges();
            window.dispatchEvent(new CustomEvent('cart:updated', { detail: { cart: this.cart } }));
            return true;
        } catch (e) {
            window.Toast.error('Network error updating cart.');
            return false;
        }
    }

    async removeItem(itemId) {
        try {
            const res = await window.apiClient.delete(`/cart/items/${itemId}/`);
            const data = await ApiClient.parseResponse(res);

            if (res.ok) {
                this.cart = data.cart;
                this.updateBadges();
                window.Toast.info('Item removed from your bag.');
                window.dispatchEvent(new CustomEvent('cart:updated', { detail: { cart: this.cart } }));
                return true;
            }
        } catch (e) {
            window.Toast.error('Failed to remove item.');
        }
        return false;
    }

    async applyCoupon(code) {
        try {
            const res = await window.apiClient.post('/cart/apply-coupon/', { code });
            const data = await ApiClient.parseResponse(res);

            if (!res.ok) {
                window.Toast.error(data.error || 'Invalid or expired coupon.');
                return false;
            }

            this.cart = data.cart;
            window.Toast.success(data.message || 'Coupon applied successfully!');
            window.dispatchEvent(new CustomEvent('cart:updated', { detail: { cart: this.cart } }));
            return true;
        } catch (e) {
            window.Toast.error('Error applying coupon.');
            return false;
        }
    }

    async removeCoupon() {
        try {
            const res = await window.apiClient.post('/cart/remove-coupon/');
            const data = await ApiClient.parseResponse(res);

            if (res.ok) {
                this.cart = data.cart;
                window.Toast.info('Coupon removed.');
                window.dispatchEvent(new CustomEvent('cart:updated', { detail: { cart: this.cart } }));
                return true;
            }
        } catch (e) {
            console.error(e);
        }
        return false;
    }

    async mergeGuestCart() {
        const sessionKey = localStorage.getItem('lumacart_session_key');
        if (!sessionKey) return;

        try {
            const res = await window.apiClient.post('/cart/merge/', { session_key: sessionKey });
            if (res.ok) {
                const data = await res.json();
                this.cart = data.cart;
                this.updateBadges();
            }
        } catch (e) {
            console.warn('Cart merge error:', e);
        }
    }

    updateBadges() {
        const count = this.cart ? this.cart.total_items_count : 0;
        const badges = document.querySelectorAll('.cart-count-badge');
        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-flex' : 'none';
        });
    }
}

window.cartManager = new CartManager();
