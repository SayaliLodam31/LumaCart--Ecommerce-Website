/**
 * LumaCart Minimalist Toast Notification Module
 */
class ToastManager {
    constructor() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = 3500) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} toast-slide-in`;

        const iconMap = {
            success: '✓',
            error: '✕',
            info: 'ℹ',
            warning: '⚠'
        };

        toast.innerHTML = `
            <span class="toast-icon">${iconMap[type] || 'ℹ'}</span>
            <div class="toast-content">${message}</div>
            <button class="toast-close" aria-label="Close">&times;</button>
        `;

        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.dismiss(toast);
        });

        this.container.appendChild(toast);

        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(toast);
            }, duration);
        }
    }

    dismiss(toast) {
        toast.classList.remove('toast-slide-in');
        toast.classList.add('toast-fade-out');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }

    success(message, duration) { this.show(message, 'success', duration); }
    error(message, duration) { this.show(message, 'error', duration); }
    info(message, duration) { this.show(message, 'info', duration); }
    warning(message, duration) { this.show(message, 'warning', duration); }
}

window.Toast = new ToastManager();
