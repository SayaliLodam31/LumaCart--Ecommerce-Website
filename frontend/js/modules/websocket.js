/**
 * LumaCart WebSocket Client
 * Realtime stock, order status, and inventory updates.
 */
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000;
        this.pingTimer = null;
    }

    connect() {
        const wsUrl = window.CONFIG ? window.CONFIG.WS_URL : `ws://${window.location.host || '127.0.0.1:8000'}/ws/live/`;

        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                this.reconnectAttempts = 0;
                this.startPing();
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse WS message:', e);
                }
            };

            this.socket.onclose = (event) => {
                this.stopPing();
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    const timeout = this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts);
                    this.reconnectAttempts++;
                    setTimeout(() => this.connect(), timeout);
                }
            };

            this.socket.onerror = (error) => {
                // Silently fallback without interrupting standard REST API operations
            };
        } catch (e) {
            // WebSockets unavailable; standard REST APIs continue to operate as source of truth
        }
    }

    startPing() {
        this.stopPing();
        this.pingTimer = setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    }

    stopPing() {
        if (this.pingTimer) {
            clearInterval(this.pingTimer);
            this.pingTimer = null;
        }
    }

    handleMessage(data) {
        if (data.type === 'stock_updated') {
            window.dispatchEvent(new CustomEvent('stock:updated', { detail: data }));
            // If viewing this product, update UI live
            const stockBadge = document.querySelector(`[data-sku-stock="${data.sku}"]`);
            if (stockBadge) {
                stockBadge.textContent = `${data.available_stock} in stock`;
            }
        } else if (data.type === 'order_status_updated') {
            window.dispatchEvent(new CustomEvent('order:updated', { detail: data }));
            window.Toast.info(data.message || `Order status updated: ${data.status}`);
        } else if (data.type === 'cart_updated') {
            window.cartManager.getCart();
        } else if (data.type === 'broadcast') {
            window.Toast.info(data.message);
        }
    }
}

window.wsManager = new WebSocketManager();
