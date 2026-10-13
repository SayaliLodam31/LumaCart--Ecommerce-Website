/**
 * LumaCart Wishlist Module
 */
class WishlistManager {
    constructor() {
        this.wishlistProductIds = new Set();
        this.wishlistData = null;
    }

    async getWishlist() {
        if (!window.authManager.isAuthenticated()) {
            this.wishlistProductIds.clear();
            this.updateBadges();
            return null;
        }

        try {
            const res = await window.apiClient.get('/wishlist/');
            if (res.ok) {
                this.wishlistData = await res.json();
                this.wishlistProductIds = new Set(this.wishlistData.items.map(item => item.product.id));
                this.updateBadges();
                return this.wishlistData;
            }
        } catch (e) {
            console.error('Failed to fetch wishlist:', e);
        }
        return null;
    }

    isInWishlist(productId) {
        return this.wishlistProductIds.has(parseInt(productId));
    }

    async toggle(productId, productTitle = 'Item') {
        if (!window.authManager.isAuthenticated()) {
            window.Toast.info('Please sign in to save items to your wishlist.');
            setTimeout(() => {
                window.location.href = `/pages/login.html?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`;
            }, 1000);
            return false;
        }

        const id = parseInt(productId);
        const exists = this.isInWishlist(id);

        try {
            if (exists) {
                const res = await window.apiClient.delete(`/wishlist/${id}/`);
                if (res.ok) {
                    this.wishlistProductIds.delete(id);
                    window.Toast.info(`Removed '${productTitle}' from wishlist.`);
                }
            } else {
                const res = await window.apiClient.post('/wishlist/', { product_id: id });
                if (res.ok) {
                    this.wishlistProductIds.add(id);
                    window.Toast.success(`Added '${productTitle}' to wishlist!`);
                }
            }
            this.updateBadges();
            window.dispatchEvent(new CustomEvent('wishlist:updated', { detail: { ids: Array.from(this.wishlistProductIds) } }));
            return !exists;
        } catch (e) {
            window.Toast.error('Could not update wishlist.');
            return exists;
        }
    }

    updateBadges() {
        const count = this.wishlistProductIds.size;
        const badges = document.querySelectorAll('.wishlist-count-badge');
        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-flex' : 'none';
        });
    }
}

window.wishlistManager = new WishlistManager();
