/**
 * LumaCart Global Frontend Configuration
 */
const CONFIG = {
    // API Base URL - relative to current host
    API_BASE: window.location.origin.startsWith('http') 
        ? `${window.location.origin}/api` 
        : 'http://127.0.0.1:8001/api',
    
    // WebSocket URL
    WS_URL: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host || '127.0.0.1:8001'}/ws/live/`,


    // Razorpay Public Key (Provided by backend or fallback to test key)
    DEFAULT_RAZORPAY_KEY: 'rzp_test_lumacart2026',

    // Currency Formatter
    formatCurrency: (amount) => {
        const num = parseFloat(amount || 0);
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(num);
    }
};

window.CONFIG = CONFIG;
