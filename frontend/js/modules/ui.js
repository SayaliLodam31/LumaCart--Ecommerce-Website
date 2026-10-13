/**
 * LumaCart Global UI Shell Generator
 * Renders consistent header, category navigation, footer, and mobile bar across all storefront pages.
 */
document.addEventListener('DOMContentLoaded', () => {
    renderSiteHeader();
    renderSiteFooter();
    renderMobileBottomNav();

    // Initialize Global Managers
    if (window.authManager) window.authManager.updateNav();
    if (window.cartManager) window.cartManager.getCart();
    if (window.wishlistManager) window.wishlistManager.getWishlist();
    if (window.wsManager) window.wsManager.connect();

    // Listen for custom events
    window.addEventListener('auth:change', () => {
        if (window.authManager) window.authManager.updateNav();
        if (window.cartManager) window.cartManager.getCart();
        if (window.wishlistManager) window.wishlistManager.getWishlist();
    });
});

function renderSiteHeader() {
    const headerMount = document.getElementById('site-header-mount');
    if (!headerMount) return;

    headerMount.innerHTML = `
        <div class="top-announcement-bar">
            <span>Free Express Delivery on orders above ₹3,000 &bull; Complimentary Returns within 14 Days</span>
        </div>
        <header class="site-header">
            <div class="container header-main">
                <!-- Brand Logo -->
                <a href="/index.html" class="site-logo">
                    LumaCart<span class="logo-dot"></span>
                </a>

                <!-- Main Desktop Nav Links -->
                <nav class="desktop-main-nav" aria-label="Main Navigation">
                    <a href="/index.html" class="main-nav-link ${window.location.pathname === '/' || window.location.pathname.endsWith('index.html') ? 'active' : ''}">Home</a>
                    <a href="/pages/products.html" class="main-nav-link ${window.location.pathname.includes('products.html') ? 'active' : ''}">Collections</a>
                    <a href="/pages/products.html?new_arrival=true" class="main-nav-link">New Arrivals</a>
                </nav>

                <!-- Search Input with Debounce -->
                <div class="header-search-wrapper">
                    <span class="header-search-icon">🔍</span>
                    <input type="text" id="globalSearchInput" class="header-search-input" placeholder="Search silk shirts, heels, leather bags..." aria-label="Search Catalog" />
                </div>

                <!-- Right Actions: Wishlist, Cart, Account -->
                <div class="header-actions">
                    <a href="/pages/wishlist.html" class="nav-icon-btn" aria-label="Wishlist" title="Saved Wishlist">
                        <span style="font-size: 1.25rem;">♡</span>
                        <span class="nav-badge wishlist-count-badge" style="display: none;">0</span>
                    </a>

                    <a href="/pages/cart.html" class="nav-icon-btn" aria-label="Shopping Cart" title="Shopping Bag">
                        <span style="font-size: 1.25rem;">🛍</span>
                        <span class="nav-badge cart-count-badge" style="display: none;">0</span>
                    </a>

                    <!-- Dynamic Account Menu (populated by authManager) -->
                    <div id="nav-account-container"></div>
                </div>
            </div>

            <!-- Category Navigation Bar -->
            <nav class="category-nav-bar" aria-label="Category Navigation">
                <div class="container">
                    <ul class="category-nav-list" id="categoryNavList">
                        <li><a href="/pages/products.html" class="category-nav-link" data-cat="">All Collections</a></li>
                        <li><a href="/pages/products.html?category=womens-clothing" class="category-nav-link" data-cat="womens-clothing">Women's Clothing</a></li>
                        <li><a href="/pages/products.html?category=mens-clothing" class="category-nav-link" data-cat="mens-clothing">Men's Clothing</a></li>
                        <li><a href="/pages/products.html?category=shoes" class="category-nav-link" data-cat="shoes">Shoes</a></li>
                        <li><a href="/pages/products.html?category=bags" class="category-nav-link" data-cat="bags">Bags</a></li>
                        <li><a href="/pages/products.html?category=jewellery" class="category-nav-link" data-cat="jewellery">Jewellery</a></li>
                        <li><a href="/pages/products.html?category=accessories" class="category-nav-link" data-cat="accessories">Accessories</a></li>
                    </ul>
                </div>
            </nav>
        </header>
    `;

    // Highlight active category based on URL
    const urlParams = new URLSearchParams(window.location.search);
    const activeCat = urlParams.get('category') || (urlParams.get('new_arrival') === 'true' ? 'new-arrivals' : '');
    const links = document.querySelectorAll('.category-nav-link');
    links.forEach(l => {
        if (l.getAttribute('data-cat') === activeCat && (activeCat || window.location.pathname.includes('products.html'))) {
            l.classList.add('active');
        }
    });

    // Debounced search redirect
    const searchInput = document.getElementById('globalSearchInput');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim();
                if (query) {
                    window.location.href = `/pages/products.html?search=${encodeURIComponent(query)}`;
                }
            }
        });
    }
}

function renderSiteFooter() {
    const footerMount = document.getElementById('site-footer-mount');
    if (!footerMount) return;

    footerMount.innerHTML = `
        <footer class="site-footer">
            <div class="container">
                <div class="footer-grid">
                    <div class="footer-brand">
                        <a href="/index.html" class="site-logo">LumaCart<span class="logo-dot"></span></a>
                        <p class="footer-tagline" style="margin-top: 1rem;">
                            Curating modern timeless silhouettes in natural fibers, fine ethical jewellery, and handcrafted artisanal leather.
                        </p>
                    </div>

                    <div>
                        <h4 class="footer-heading">Collections</h4>
                        <ul class="footer-links">
                            <li><a href="/pages/products.html?category=womens-clothing">Women's Clothing</a></li>
                            <li><a href="/pages/products.html?category=mens-clothing">Men's Clothing</a></li>
                            <li><a href="/pages/products.html?category=shoes">Shoes & Footwear</a></li>
                            <li><a href="/pages/products.html?category=bags">Artisanal Bags</a></li>
                            <li><a href="/pages/products.html?category=jewellery">Jewellery & Gems</a></li>
                            <li><a href="/pages/products.html?category=accessories">Accessories & Watches</a></li>
                        </ul>
                    </div>

                    <div>
                        <h4 class="footer-heading">Client Services</h4>
                        <ul class="footer-links">
                            <li><a href="/pages/orders.html">Track Order Status</a></li>
                            <li><a href="/pages/cart.html">View Shopping Bag</a></li>
                            <li><a href="/pages/wishlist.html">Saved Wishlist</a></li>
                            <li><a href="/pages/profile.html">Shipping & Addresses</a></li>
                        </ul>
                    </div>

                    <div>
                        <h4 class="footer-heading">Payment & Security</h4>
                        <p style="font-size: 0.85rem; color: var(--color-text-muted); line-height: 1.6; margin-bottom: 1rem;">
                            Razorpay verified payments supporting UPI, RuPay, Credit/Debit Cards, and Net Banking. All transactions are 256-bit SSL encrypted.
                        </p>
                        <div style="display: flex; gap: 0.5rem; font-size: 1.5rem; opacity: 0.7;">
                            <span>💳</span> <span>🛡</span> <span>⚡</span>
                        </div>
                    </div>
                </div>

                <div class="footer-bottom">
                    <p>&copy; ${new Date().getFullYear()} LumaCart Fashion Technologies Ltd. All rights reserved.</p>
                    <p>Designed with minimal elegance for modern lifestyles.</p>
                </div>
            </div>
        </footer>
    `;
}

function renderMobileBottomNav() {
    const navMount = document.getElementById('mobile-bottom-nav-mount');
    if (!navMount) return;

    navMount.innerHTML = `
        <nav class="mobile-bottom-nav">
            <a href="/index.html" class="mobile-nav-item ${window.location.pathname.endsWith('index.html') || window.location.pathname === '/' ? 'active' : ''}">
                <span class="mobile-nav-icon">⌂</span>
                <span>Home</span>
            </a>
            <a href="/pages/products.html" class="mobile-nav-item ${window.location.pathname.includes('products.html') ? 'active' : ''}">
                <span class="mobile-nav-icon">⚲</span>
                <span>Shop</span>
            </a>
            <a href="/pages/wishlist.html" class="mobile-nav-item ${window.location.pathname.includes('wishlist.html') ? 'active' : ''}">
                <span class="mobile-nav-icon">♡</span>
                <span>Wishlist</span>
            </a>
            <a href="/pages/cart.html" class="mobile-nav-item ${window.location.pathname.includes('cart.html') ? 'active' : ''}">
                <span class="mobile-nav-icon">🛍</span>
                <span>Bag</span>
            </a>
            <a href="/pages/profile.html" class="mobile-nav-item ${window.location.pathname.includes('profile.html') || window.location.pathname.includes('login.html') ? 'active' : ''}">
                <span class="mobile-nav-icon">👤</span>
                <span>Account</span>
            </a>
        </nav>
    `;
}

// Global Product Card Renderer Helper
window.renderProductCard = function(product, index = 0) {
    const isWishlisted = window.wishlistManager ? window.wishlistManager.isInWishlist(product.id) : false;
    const hasDiscount = product.discount_price && parseFloat(product.discount_price) > 0 && parseFloat(product.discount_price) < parseFloat(product.base_price);
    const discountPercent = hasDiscount 
        ? Math.round(((parseFloat(product.base_price) - parseFloat(product.discount_price)) / parseFloat(product.base_price)) * 100) 
        : 0;

    let badgeHtml = '';
    if (product.is_new_arrival) {
        badgeHtml = '<span class="badge badge-sage card-tag">New</span>';
    } else if (hasDiscount) {
        badgeHtml = `<span class="badge badge-rose card-tag">-${discountPercent}%</span>`;
    }

    const colorDots = (product.available_colours || []).slice(0, 4).map(c => 
        `<span class="color-dot" style="background-color: ${c.hex};" title="${c.name}"></span>`
    ).join('');

    const ratingVal = product.average_rating ? Number(product.average_rating).toFixed(1) : '5.0';
    const reviewsVal = product.reviews_count !== undefined ? product.reviews_count : 0;

    // Viewport-aware priority: Initial above-the-fold cards (index < 4) load eagerly with high fetchpriority
    const isAboveFold = index < 4;
    const loadingAttr = isAboveFold ? 'eager' : 'lazy';
    const priorityAttr = isAboveFold ? 'high' : 'auto';

    return `
        <article class="product-card" data-product-id="${product.id}">
            <div class="product-card-image-box">
                <a href="/pages/product-detail.html?slug=${product.slug}" aria-label="View ${product.title}">
                    <img src="${product.primary_image || '/assets/images/placeholder.svg'}" 
                         alt="${product.title}" 
                         class="product-card-img" 
                         width="384"
                         height="512"
                         loading="${loadingAttr}" 
                         fetchpriority="${priorityAttr}"
                         decoding="async"
                         onerror="this.onerror=null;this.src='/assets/images/placeholder.svg';" />
                </a>
                ${badgeHtml}
                <button class="card-wishlist-btn ${isWishlisted ? 'active' : ''}" 
                        onclick="window.wishlistManager.toggle(${product.id}, '${product.title.replace(/'/g, "\\'")}')" 
                        aria-label="Save to wishlist" title="Save to wishlist">
                    ${isWishlisted ? '♥' : '♡'}
                </button>
                <div class="product-card-hover-action">
                    <a href="/pages/product-detail.html?slug=${product.slug}" class="product-card-view-btn">
                        View Details &rarr;
                    </a>
                </div>
            </div>
            <div class="product-card-body">
                <div class="product-card-meta-row">
                    <span class="product-card-brand">${product.brand_name || 'LumaCart'}</span>
                    <span class="product-card-rating">★ ${ratingVal} <span class="rating-count">(${reviewsVal})</span></span>
                </div>
                <h3 class="product-card-title">
                    <a href="/pages/product-detail.html?slug=${product.slug}">${product.title}</a>
                </h3>
                <div class="product-card-price-row">
                    <span class="current-price">${window.CONFIG.formatCurrency(product.current_price)}</span>
                    ${hasDiscount ? `<span class="original-price">${window.CONFIG.formatCurrency(product.base_price)}</span>` : ''}
                </div>
                ${colorDots ? `<div class="product-card-colors">${colorDots}</div>` : ''}
            </div>
        </article>
    `;
};
