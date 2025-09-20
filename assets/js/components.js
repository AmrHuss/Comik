/**
 * ManhwaVerse UI Components
 * Reusable components for reading history, bookmarks, and user interface
 */

class UIComponents {
    constructor() {
        this.storage = window.storageManager;
    }

    // Create bookmark button component
    createBookmarkButton(mangaData, container) {
        const isBookmarked = this.storage.isBookmarked(mangaData.title);
        const button = document.createElement('button');
        button.className = `bookmark-btn ${isBookmarked ? 'bookmarked' : ''}`;
        button.innerHTML = `
            <svg class="bookmark-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="bookmark-text">${isBookmarked ? 'Bookmarked' : 'Bookmark'}</span>
        `;
        
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleBookmark(mangaData, button);
        });

        if (container) {
            container.appendChild(button);
        }
        
        return button;
    }

    // Toggle bookmark functionality
    toggleBookmark(mangaData, button) {
        const isBookmarked = this.storage.isBookmarked(mangaData.title);
        
        if (isBookmarked) {
            this.storage.removeBookmark(mangaData.title);
            button.classList.remove('bookmarked');
            button.querySelector('.bookmark-text').textContent = 'Bookmark';
            this.showNotification('Removed from bookmarks', 'success');
        } else {
            this.storage.addBookmark(mangaData);
            button.classList.add('bookmarked');
            button.querySelector('.bookmark-text').textContent = 'Bookmarked';
            this.showNotification('Added to bookmarks', 'success');
        }
    }

    // Create reading history item
    createHistoryItem(historyItem) {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <div class="history-cover">
                <img src="${historyItem.mangaCover}" alt="${historyItem.mangaTitle}" loading="lazy">
                <div class="history-overlay">
                    <button class="continue-reading-btn" data-chapter-url="${historyItem.chapterUrl}">
                        Continue Reading
                    </button>
                </div>
            </div>
            <div class="history-info">
                <h3 class="history-manga-title">${historyItem.mangaTitle}</h3>
                <p class="history-chapter-title">${historyItem.chapterTitle}</p>
                <div class="history-meta">
                    <span class="history-time">${this.formatTimeAgo(historyItem.readAt)}</span>
                    <span class="history-source">${historyItem.source}</span>
                </div>
            </div>
            <div class="history-actions">
                <button class="action-btn remove-history" data-id="${historyItem.id}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;

        // Add event listeners
        item.querySelector('.continue-reading-btn').addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = `reader.html?url=${encodeURIComponent(historyItem.chapterUrl)}&source=${encodeURIComponent(historyItem.source)}`;
        });

        item.querySelector('.remove-history').addEventListener('click', (e) => {
            e.preventDefault();
            this.removeHistoryItem(historyItem.id, item);
        });

        return item;
    }

    // Create bookmark item
    createBookmarkItem(bookmark) {
        const item = document.createElement('div');
        item.className = 'bookmark-item';
        item.innerHTML = `
            <div class="bookmark-cover">
                <img src="${bookmark.cover}" alt="${bookmark.title}" loading="lazy">
                <div class="bookmark-overlay">
                    <button class="read-manga-btn" data-detail-url="${bookmark.detailUrl}">
                        Read Now
                    </button>
                </div>
                <div class="bookmark-status ${bookmark.status}">
                    ${this.getStatusText(bookmark.status)}
                </div>
            </div>
            <div class="bookmark-info">
                <h3 class="bookmark-title">${bookmark.title}</h3>
                <div class="bookmark-meta">
                    <span class="bookmark-source">${bookmark.source}</span>
                    <span class="bookmark-added">Added ${this.formatTimeAgo(bookmark.addedAt)}</span>
                </div>
                ${bookmark.lastReadChapter ? `<p class="last-read">Last read: ${bookmark.lastReadChapter}</p>` : ''}
            </div>
            <div class="bookmark-actions">
                <select class="status-select" data-title="${bookmark.title}">
                    <option value="reading" ${bookmark.status === 'reading' ? 'selected' : ''}>Reading</option>
                    <option value="completed" ${bookmark.status === 'completed' ? 'selected' : ''}>Completed</option>
                    <option value="plan-to-read" ${bookmark.status === 'plan-to-read' ? 'selected' : ''}>Plan to Read</option>
                </select>
                <button class="action-btn remove-bookmark" data-title="${bookmark.title}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;

        // Add event listeners
        item.querySelector('.read-manga-btn').addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = bookmark.detailUrl;
        });

        item.querySelector('.status-select').addEventListener('change', (e) => {
            this.updateBookmarkStatus(e.target.dataset.title, e.target.value);
        });

        item.querySelector('.remove-bookmark').addEventListener('click', (e) => {
            e.preventDefault();
            this.removeBookmark(bookmark.title, item);
        });

        return item;
    }

    // Create reading progress indicator
    createProgressIndicator(mangaTitle) {
        const progress = this.storage.getReadingProgress(mangaTitle);
        if (!progress) return null;

        const progressBar = document.createElement('div');
        progressBar.className = 'reading-progress';
        
        const progressPercent = progress.totalChapters > 0 
            ? Math.min(100, (progress.totalChapters * 10)) // Mock progress calculation
            : 0;

        progressBar.innerHTML = `
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progressPercent}%"></div>
            </div>
            <span class="progress-text">${progressPercent}% Complete</span>
        `;

        return progressBar;
    }

    // Create Purple Glow notification system
    showNotification(message, type = 'info', duration = 3000) {
        // Remove existing notifications of the same type
        const existing = document.querySelectorAll(`.notification-${type}`);
        existing.forEach(n => n.remove());

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        // Get appropriate icon based on type
        const icons = {
            success: '✓',
            error: '✕',
            info: 'ℹ',
            warning: '⚠'
        };

        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">${icons[type] || icons.info}</div>
                <span class="notification-message">${message}</span>
                <button class="notification-close" aria-label="Close notification">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Trigger entrance animation
        requestAnimationFrame(() => {
            notification.classList.add('notification-enter');
        });

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('notification-exit');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, duration);

        // Close button functionality
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.add('notification-exit');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        });
    }

    // Utility methods
    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
        return date.toLocaleDateString();
    }

    getStatusText(status) {
        const statusMap = {
            'reading': 'Reading',
            'completed': 'Completed',
            'plan-to-read': 'Plan to Read'
        };
        return statusMap[status] || status;
    }

    // History management
    removeHistoryItem(id, element) {
        const history = this.storage.get(this.storage.keys.readingHistory) || [];
        const filtered = history.filter(item => item.id !== id);
        this.storage.set(this.storage.keys.readingHistory, filtered);
        element.remove();
        this.showNotification('Removed from history', 'success');
    }

    // Bookmark management
    updateBookmarkStatus(title, status) {
        this.storage.updateBookmarkStatus(title, status);
        this.showNotification(`Status updated to ${this.getStatusText(status)}`, 'success');
    }

    removeBookmark(title, element) {
        this.storage.removeBookmark(title);
        element.remove();
        this.showNotification('Removed from bookmarks', 'success');
    }
}

// Create global instance
window.uiComponents = new UIComponents();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIComponents;
}
