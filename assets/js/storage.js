/**
 * ManhwaVerse Storage Manager
 * Handles reading history, bookmarks, and user preferences
 * Uses localStorage for persistence across sessions
 */

class StorageManager {
    constructor() {
        this.keys = {
            readingHistory: 'manhwa_reading_history',
            bookmarks: 'manhwa_bookmarks',
            readingProgress: 'manhwa_reading_progress',
            userPreferences: 'manhwa_user_preferences'
        };
        this.init();
    }

    init() {
        // Initialize storage if it doesn't exist
        if (!this.get(this.keys.readingHistory)) {
            this.set(this.keys.readingHistory, []);
        }
        if (!this.get(this.keys.bookmarks)) {
            this.set(this.keys.bookmarks, []);
        }
        if (!this.get(this.keys.readingProgress)) {
            this.set(this.keys.readingProgress, {});
        }
        if (!this.get(this.keys.userPreferences)) {
            this.set(this.keys.userPreferences, {
                theme: 'dark',
                readingMode: 'long-strip',
                autoScroll: false,
                fontSize: 'medium'
            });
        }
    }

    // Generic storage methods
    get(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error getting from storage:', error);
            return null;
        }
    }

    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error setting storage:', error);
            return false;
        }
    }

    // Reading History Methods
    addToHistory(mangaData, chapterData) {
        const history = this.get(this.keys.readingHistory) || [];
        const historyItem = {
            id: `${mangaData.title}_${chapterData.title}`,
            mangaTitle: mangaData.title,
            mangaCover: mangaData.cover_image || mangaData.cover_url,
            mangaUrl: mangaData.detail_url,
            chapterTitle: chapterData.title,
            chapterUrl: chapterData.url,
            readAt: new Date().toISOString(),
            source: mangaData.source || 'AsuraScanz'
        };

        // Remove existing entry if it exists
        const existingIndex = history.findIndex(item => item.id === historyItem.id);
        if (existingIndex !== -1) {
            history.splice(existingIndex, 1);
        }

        // Add to beginning of array (most recent first)
        history.unshift(historyItem);

        // Keep only last 100 entries
        if (history.length > 100) {
            history.splice(100);
        }

        this.set(this.keys.readingHistory, history);
        this.updateReadingProgress(mangaData.title, chapterData.title);
        return historyItem;
    }

    getReadingHistory(limit = 20) {
        const history = this.get(this.keys.readingHistory) || [];
        return history.slice(0, limit);
    }

    clearHistory() {
        this.set(this.keys.readingHistory, []);
    }

    // Bookmark Methods
    addBookmark(mangaData) {
        const bookmarks = this.get(this.keys.bookmarks) || [];
        const bookmark = {
            id: mangaData.title,
            title: mangaData.title,
            cover: mangaData.cover_image || mangaData.cover_url,
            detailUrl: mangaData.detail_url,
            addedAt: new Date().toISOString(),
            source: mangaData.source || 'AsuraScanz',
            lastReadChapter: null,
            status: 'reading' // reading, completed, plan-to-read
        };

        // Check if already bookmarked
        const existingIndex = bookmarks.findIndex(item => item.id === bookmark.id);
        if (existingIndex !== -1) {
            return false; // Already bookmarked
        }

        bookmarks.unshift(bookmark);
        this.set(this.keys.bookmarks, bookmarks);
        return bookmark;
    }

    removeBookmark(mangaTitle) {
        const bookmarks = this.get(this.keys.bookmarks) || [];
        const filteredBookmarks = bookmarks.filter(item => item.id !== mangaTitle);
        this.set(this.keys.bookmarks, filteredBookmarks);
        return true;
    }

    getBookmarks() {
        return this.get(this.keys.bookmarks) || [];
    }

    isBookmarked(mangaTitle) {
        const bookmarks = this.get(this.keys.bookmarks) || [];
        return bookmarks.some(item => item.id === mangaTitle);
    }

    updateBookmarkStatus(mangaTitle, status) {
        const bookmarks = this.get(this.keys.bookmarks) || [];
        const bookmark = bookmarks.find(item => item.id === mangaTitle);
        if (bookmark) {
            bookmark.status = status;
            this.set(this.keys.bookmarks, bookmarks);
            return true;
        }
        return false;
    }

    // Reading Progress Methods
    updateReadingProgress(mangaTitle, chapterTitle) {
        const progress = this.get(this.keys.readingProgress) || {};
        progress[mangaTitle] = {
            lastChapter: chapterTitle,
            lastReadAt: new Date().toISOString(),
            totalChapters: progress[mangaTitle]?.totalChapters || 0
        };
        this.set(this.keys.readingProgress, progress);
    }

    getReadingProgress(mangaTitle) {
        const progress = this.get(this.keys.readingProgress) || {};
        return progress[mangaTitle] || null;
    }

    setTotalChapters(mangaTitle, totalChapters) {
        const progress = this.get(this.keys.readingProgress) || {};
        if (!progress[mangaTitle]) {
            progress[mangaTitle] = {};
        }
        progress[mangaTitle].totalChapters = totalChapters;
        this.set(this.keys.readingProgress, progress);
    }

    // User Preferences Methods
    getPreferences() {
        return this.get(this.keys.userPreferences) || {};
    }

    updatePreferences(newPreferences) {
        const current = this.getPreferences();
        const updated = { ...current, ...newPreferences };
        this.set(this.keys.userPreferences, updated);
        return updated;
    }

    // Utility Methods
    exportData() {
        return {
            readingHistory: this.get(this.keys.readingHistory),
            bookmarks: this.get(this.keys.bookmarks),
            readingProgress: this.get(this.keys.readingProgress),
            userPreferences: this.get(this.keys.userPreferences),
            exportDate: new Date().toISOString()
        };
    }

    importData(data) {
        try {
            if (data.readingHistory) this.set(this.keys.readingHistory, data.readingHistory);
            if (data.bookmarks) this.set(this.keys.bookmarks, data.bookmarks);
            if (data.readingProgress) this.set(this.keys.readingProgress, data.readingProgress);
            if (data.userPreferences) this.set(this.keys.userPreferences, data.userPreferences);
            return true;
        } catch (error) {
            console.error('Error importing data:', error);
            return false;
        }
    }

    clearAllData() {
        Object.values(this.keys).forEach(key => {
            localStorage.removeItem(key);
        });
        this.init();
    }
}

// Create global instance
window.storageManager = new StorageManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StorageManager;
}
