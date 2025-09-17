/**
 * ManhwaVerse UI Components
 * Reusable components and utilities
 */

// Toast notification system
class Toast {
    constructor() {
        this.container = this.createContainer();
        document.body.appendChild(this.container);
    }

    createContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        return container;
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        toast.style.cssText = `
            background: ${type === 'error' ? '#dc2626' : type === 'success' ? '#059669' : '#4F46E5'};
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
            word-wrap: break-word;
        `;

        this.container.appendChild(toast);

        // Slide in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);

        // Auto remove
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }

    success(message, duration) {
        this.show(message, 'success', duration);
    }

    error(message, duration) {
        this.show(message, 'error', duration);
    }

    info(message, duration) {
        this.show(message, 'info', duration);
    }
}

// Initialize global toast instance
window.toast = new Toast();

// Loading spinner component
class LoadingSpinner {
    static create(size = 'medium') {
        const spinner = document.createElement('div');
        spinner.className = `loading-spinner loading-spinner-${size}`;
        
        const sizeMap = {
            small: '20px',
            medium: '40px',
            large: '60px'
        };
        
        spinner.innerHTML = `
            <div class="spinner-circle"></div>
        `;
        
        spinner.style.cssText = `
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        `;
        
        const circle = spinner.querySelector('.spinner-circle');
        circle.style.cssText = `
            width: ${sizeMap[size]};
            height: ${sizeMap[size]};
            border: 3px solid rgba(79, 70, 229, 0.3);
            border-top: 3px solid #4F46E5;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        `;
        
        // Add keyframes if not already added
        if (!document.querySelector('#spinner-styles')) {
            const style = document.createElement('style');
            style.id = 'spinner-styles';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
        
        return spinner;
    }
}

// Modal component
class Modal {
    constructor(title, content, options = {}) {
        this.title = title;
        this.content = content;
        this.options = {
            closable: true,
            size: 'medium',
            ...options
        };
        this.element = null;
        this.backdrop = null;
    }

    create() {
        // Create backdrop
        this.backdrop = document.createElement('div');
        this.backdrop.className = 'modal-backdrop';
        this.backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

        // Create modal
        this.element = document.createElement('div');
        this.element.className = `modal modal-${this.options.size}`;
        
        const sizeMap = {
            small: '400px',
            medium: '600px',
            large: '800px'
        };
        
        this.element.style.cssText = `
            background: var(--card-bg);
            border-radius: var(--radius-lg);
            max-width: ${sizeMap[this.options.size]};
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            transform: scale(0.9);
            transition: transform 0.3s ease;
        `;

        this.element.innerHTML = `
            <div class="modal-header" style="padding: 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin: 0; color: var(--text-primary);">${this.title}</h2>
                ${this.options.closable ? '<button class="modal-close" style="background: none; border: none; font-size: 24px; color: var(--text-secondary); cursor: pointer;">&times;</button>' : ''}
            </div>
            <div class="modal-content" style="padding: 20px;">
                ${this.content}
            </div>
        `;

        this.backdrop.appendChild(this.element);

        // Event listeners
        if (this.options.closable) {
            const closeBtn = this.element.querySelector('.modal-close');
            closeBtn?.addEventListener('click', () => this.close());
            
            this.backdrop.addEventListener('click', (e) => {
                if (e.target === this.backdrop) {
                    this.close();
                }
            });
        }

        return this;
    }

    show() {
        if (!this.element) this.create();
        
        document.body.appendChild(this.backdrop);
        document.body.style.overflow = 'hidden';
        
        // Animate in
        setTimeout(() => {
            this.backdrop.style.opacity = '1';
            this.element.style.transform = 'scale(1)';
        }, 10);

        return this;
    }

    close() {
        if (!this.backdrop) return;
        
        this.backdrop.style.opacity = '0';
        this.element.style.transform = 'scale(0.9)';
        
        setTimeout(() => {
            if (this.backdrop && this.backdrop.parentNode) {
                this.backdrop.parentNode.removeChild(this.backdrop);
                document.body.style.overflow = '';
            }
        }, 300);

        return this;
    }
}

// Utility functions
const Utils = {
    // Debounce function
    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },

    // Throttle function
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Format numbers (e.g., 1000 -> 1K)
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },

    // Sanitize HTML
    sanitizeHTML(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    },

    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            toast.success('Copied to clipboard!');
            return true;
        } catch (err) {
            console.error('Failed to copy:', err);
            toast.error('Failed to copy to clipboard');
            return false;
        }
    },

    // Get URL parameters
    getURLParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    }
};

// Image lazy loading utility
class LazyImageLoader {
    constructor() {
        this.observer = null;
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                this.handleIntersection.bind(this),
                {
                    rootMargin: '50px 0px',
                    threshold: 0.01
                }
            );
            
            this.observeImages();
        }
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                this.loadImage(entry.target);
                this.observer.unobserve(entry.target);
            }
        });
    }

    loadImage(img) {
        const src = img.dataset.src || img.dataset.lazySrc;
        if (src) {
            img.src = src;
            img.classList.add('loaded');
            img.removeAttribute('data-src');
            img.removeAttribute('data-lazy-src');
        }
    }

    observeImages() {
        const images = document.querySelectorAll('img[data-src], img[data-lazy-src]');
        images.forEach(img => {
            this.observer.observe(img);
        });
    }

    // Method to observe new images added dynamically
    observeNewImages() {
        this.observeImages();
    }
}

// Initialize lazy loading
window.lazyLoader = new LazyImageLoader();

// Export utilities globally
window.Modal = Modal;
window.LoadingSpinner = LoadingSpinner;
window.Utils = Utils;

// Initialize tooltips (simple implementation)
function initTooltips() {
    document.addEventListener('mouseover', (e) => {
        const element = e.target.closest('[data-tooltip]');
        if (element && !element.querySelector('.tooltip')) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = element.dataset.tooltip;
            tooltip.style.cssText = `
                position: absolute;
                background: #333;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                z-index: 1000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s ease;
                top: -30px;
                left: 50%;
                transform: translateX(-50%);
            `;
            
            element.style.position = 'relative';
            element.appendChild(tooltip);
            
            setTimeout(() => {
                tooltip.style.opacity = '1';
            }, 100);
        }
    });

    document.addEventListener('mouseout', (e) => {
        const element = e.target.closest('[data-tooltip]');
        if (element) {
            const tooltip = element.querySelector('.tooltip');
            if (tooltip) {
                tooltip.style.opacity = '0';
                setTimeout(() => {
                    if (tooltip.parentNode) {
                        tooltip.parentNode.removeChild(tooltip);
                    }
                }, 200);
            }
        }
    });
}

// Initialize components when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initTooltips();
});

console.log('ManhwaVerse Components loaded successfully!');