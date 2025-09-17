/**
 * ManhwaVerse Frontend Logic - Vercel Production Ready
 * ====================================================
 * 
 * A comprehensive JavaScript module for the ManhwaVerse website.
 * Optimized for Vercel deployment with correct API endpoints.
 * 
 * Author: ManhwaVerse Development Team
 * Date: 2025
 * Version: Vercel Production v1.0
 */

// --- Configuration ---
const API_BASE_URL = '/api'; // Correct for Vercel deployment
const DEBOUNCE_DELAY = 300;
const MAX_SEARCH_RESULTS = 7;
const REQUEST_TIMEOUT = 15000;

// --- State Management ---
const AppState = {
    isLoading: false,
    currentPage: null,
    searchResults: [],
    lastSearchQuery: ''
};

// --- Utility Functions ---

/**
 * Debounce function to limit API calls during search
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Show loading state in a container
 */
function showLoadingState(container, message = 'Loading...') {
    if (!container) return;
    container.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <p class="loading-message">${message}</p>
        </div>
    `;
}

/**
 * Show error state in a container
 */
function showErrorState(container, message, retry = false) {
    if (!container) return;
    const retryButton = retry ? '<button class="retry-btn" onclick="location.reload()">Retry</button>' : '';
    container.innerHTML = `
        <div class="error-container">
            <div class="error-icon">⚠️</div>
            <p class="error-message">${message}</p>
            ${retryButton}
        </div>
    `;
}

/**
 * Show empty state in a container
 */
function showEmptyState(container, message = 'No content found.') {
    if (!container) return;
    container.innerHTML = `
        <div class="empty-container">
            <div class="empty-icon">📚</div>
            <p class="empty-message">${message}</p>
        </div>
    `;
}

/**
 * Make API request with proper error handling
 */
async function makeApiRequest(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('Request timed out. Please try again.');
        }
        
        throw error;
    }
}

// --- DOM Manipulation Functions ---

/**
 * Create a manga card element
 */
function createMangaCard(manga) {
    const cardLink = document.createElement('a');
    cardLink.href = `detail.html?url=${encodeURIComponent(manga.detail_url)}`;
    cardLink.className = 'manhwa-card';
    cardLink.setAttribute('data-title', manga.title);
    
    cardLink.innerHTML = `
        <div class="card-image">
            <img 
                src="${manga.cover_url}" 
                alt="${manga.title}" 
                loading="lazy" 
                onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'"
            >
            <div class="image-placeholder" style="display: none;">
                <span>📖</span>
            </div>
            <div class="card-overlay">
                <button class="read-btn" aria-label="View details for ${manga.title}">
                    View Details
                </button>
            </div>
        </div>
        <div class="card-content">
            <h3 class="card-title" title="${manga.title}">${manga.title}</h3>
            <p class="card-chapter">${manga.latest_chapter || 'N/A'}</p>
        </div>
    `;
    
    return cardLink;
}

/**
 * Create a search result item
 */
function createSearchResultItem(manga) {
    const item = document.createElement('a');
    item.href = `detail.html?url=${encodeURIComponent(manga.detail_url)}`;
    item.className = 'search-result-item';
    item.innerHTML = `
        <img src="${manga.cover_url}" alt="${manga.title}" loading="lazy">
        <span class="search-result-title">${manga.title}</span>
    `;
    return item;
}

/**
 * Display manga grid in a container
 */
function displayMangaGrid(container, mangaList) {
    if (!container) return;
    
    if (!mangaList || mangaList.length === 0) {
        showEmptyState(container, 'No manga found.');
        return;
    }
    
    container.innerHTML = '';
    mangaList.forEach(manga => {
        const card = createMangaCard(manga);
        container.appendChild(card);
    });
}

/**
 * Display search results in dropdown
 */
function displaySearchResults(container, results) {
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!results || results.length === 0) {
        container.innerHTML = '<p class="no-results">No results found.</p>';
        return;
    }
    
    results.slice(0, MAX_SEARCH_RESULTS).forEach(manga => {
        const item = createSearchResultItem(manga);
        container.appendChild(item);
    });
}

// --- Page-Specific Functions ---

/**
 * Load and display manga data for a specific page
 */
async function loadAndDisplayManga(apiUrl, gridSelector, pageTitle) {
    const grid = document.querySelector(gridSelector);
    const pageTitleElement = document.getElementById('page-title');
    
    if (pageTitleElement && pageTitle) {
        pageTitleElement.textContent = pageTitle;
    }
    
    if (!grid) {
        console.error(`Grid container not found: ${gridSelector}`);
        return;
    }
    
    showLoadingState(grid, 'Loading manga...');
    
    try {
        const result = await makeApiRequest(apiUrl);
        displayMangaGrid(grid, result.data);
    } catch (error) {
        console.error('Error loading manga:', error);
        showErrorState(grid, `Failed to load manga: ${error.message}`, true);
    }
}

/**
 * Load homepage content (trending and updates)
 */
async function loadHomepageContent() {
    const trendingGrid = document.querySelector('.trending-grid');
    const updatesGrid = document.querySelector('.updates-grid');
    
    if (!trendingGrid && !updatesGrid) {
        console.error('Homepage grid containers not found');
        return;
    }
    
    if (trendingGrid) {
        showLoadingState(trendingGrid, 'Loading trending manga...');
    }
    if (updatesGrid) {
        showLoadingState(updatesGrid, 'Loading latest updates...');
    }
    
    try {
        const result = await makeApiRequest(`${API_BASE_URL}/popular`);
        
        if (trendingGrid) {
            displayMangaGrid(trendingGrid, result.data.slice(0, 6));
        }
        if (updatesGrid) {
            displayMangaGrid(updatesGrid, result.data);
        }
    } catch (error) {
        console.error('Error loading homepage content:', error);
        
        if (trendingGrid) {
            showErrorState(trendingGrid, 'Failed to load trending manga.', true);
        }
        if (updatesGrid) {
            showErrorState(updatesGrid, 'Failed to load latest updates.', true);
        }
    }
}

/**
 * Handle manga list page (genre or search results)
 */
async function handleMangaListPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const genre = urlParams.get('genre');
    const searchQuery = urlParams.get('search');
    
    let apiUrl, pageTitle;
    
    if (genre) {
        const genreTitle = genre.charAt(0).toUpperCase() + genre.slice(1).replace('-', ' ');
        apiUrl = `${API_BASE_URL}/genre?name=${encodeURIComponent(genre)}`;
        pageTitle = `${genreTitle} Manhwa`;
    } else if (searchQuery) {
        apiUrl = `${API_BASE_URL}/search?query=${encodeURIComponent(searchQuery)}`;
        pageTitle = `Search Results for "${searchQuery}"`;
    } else {
        showErrorState(
            document.getElementById('manga-results-grid'), 
            'No genre or search query specified.'
        );
        return;
    }
    
    await loadAndDisplayManga(apiUrl, '#manga-results-grid', pageTitle);
}

/**
 * Handle manga detail page
 */
async function handleDetailPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const detailUrl = urlParams.get('url');
    const container = document.getElementById('detail-container');
    
    if (!detailUrl) {
        showErrorState(container, 'No manga URL provided.');
        return;
    }
    
    showLoadingState(container, 'Loading manga details...');
    
    try {
        const result = await makeApiRequest(`${API_BASE_URL}/manga-details?url=${encodeURIComponent(detailUrl)}`);
        displayMangaDetails(result.data);
    } catch (error) {
        console.error('Error loading manga details:', error);
        showErrorState(container, `Failed to load manga details: ${error.message}`, true);
    }
}

/**
 * Display manga details on detail page
 */
function displayMangaDetails(data) {
    const container = document.getElementById('detail-container');
    if (!container) return;
    
    // Update page title
    document.title = `${data.title} - ManhwaVerse`;
    
    // Create genres HTML
    const genresHtml = data.genres.map(genre => 
        `<span class="genre-tag">${genre}</span>`
    ).join('');
    
    // Create chapters HTML
    const chaptersHtml = data.chapters.map(chapter => `
        <a href="reader.html?url=${encodeURIComponent(chapter.url)}" class="chapter-item">
            <span class="chapter-title">${chapter.title}</span>
            <span class="chapter-date">${chapter.date}</span>
        </a>
    `).join('');
    
    container.innerHTML = `
        <div class="detail-grid">
            <div class="detail-cover">
                <img src="${data.cover_image}" alt="${data.title}" loading="lazy">
            </div>
            <div class="detail-info">
                <h1>${data.title}</h1>
                <div class="detail-meta">
                    <span class="detail-rating">⭐ ${data.rating}</span>
                    <span class="detail-status">${data.status}</span>
                </div>
                <div class="detail-genres">${genresHtml}</div>
                <p class="detail-description">${data.description}</p>
            </div>
        </div>
        <div class="chapter-list-container">
            <h2>Chapters</h2>
            <div class="chapter-list">${chaptersHtml}</div>
        </div>
    `;
}

// --- Search Functionality ---

/**
 * Handle search form submission
 */
function handleSearchSubmit(event) {
    event.preventDefault();
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    
    if (query) {
        window.location.href = `mangalist.html?search=${encodeURIComponent(query)}`;
    }
}

/**
 * Handle live search input
 */
async function handleLiveSearch(event) {
    const query = event.target.value.trim();
    const resultsContainer = document.getElementById('search-results-container') || createSearchResultsContainer();
    
    if (query.length < 2) {
        resultsContainer.style.display = 'none';
        return;
    }
    
    // Avoid duplicate requests
    if (query === AppState.lastSearchQuery) {
        return;
    }
    
    AppState.lastSearchQuery = query;
    resultsContainer.innerHTML = '<p class="searching">Searching...</p>';
    resultsContainer.style.display = 'block';
    
    try {
        const result = await makeApiRequest(`${API_BASE_URL}/search?query=${encodeURIComponent(query)}`);
        displaySearchResults(resultsContainer, result.data);
    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = '<p class="search-error">Search failed. Please try again.</p>';
    }
}

/**
 * Create search results container if it doesn't exist
 */
function createSearchResultsContainer() {
    const searchContainer = document.querySelector('.search-container');
    if (!searchContainer) return null;
    
    let container = document.getElementById('search-results-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'search-results-container';
        container.className = 'search-results-dropdown';
        searchContainer.appendChild(container);
    }
    return container;
}

/**
 * Hide search results dropdown
 */
function hideSearchResults() {
    const resultsContainer = document.getElementById('search-results-container');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
}

// --- Chapter Loading (Reader Page) ---

/**
 * Load chapter images for reader page
 */
async function loadChapterImages(chapterUrl) {
    try {
        const result = await makeApiRequest(`${API_BASE_URL}/chapter?url=${encodeURIComponent(chapterUrl)}`);
        return result.data;
    } catch (error) {
        console.error("Chapter load error:", error);
        throw error;
    }
}

// --- Page Initialization ---

/**
 * Initialize the current page based on data-page attribute
 */
function initializePage() {
    const page = document.body.dataset.page;
    console.log(`Initializing page: ${page}`);
    
    AppState.currentPage = page;
    
    switch (page) {
        case 'home':
            loadHomepageContent();
            break;
        case 'popular':
            loadAndDisplayManga(`${API_BASE_URL}/popular`, '.manhwa-grid', 'Popular Manhwa');
            break;
        case 'new-releases':
            loadAndDisplayManga(`${API_BASE_URL}/popular`, '.manhwa-grid', 'New Releases');
            break;
        case 'mangalist':
            handleMangaListPage();
            break;
        case 'detail':
            handleDetailPage();
            break;
        case 'reader':
            handleReaderPage();
            break;
        default:
            console.warn(`Unknown page type: ${page}`);
    }
}

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleLiveSearch, DEBOUNCE_DELAY));
    }
    
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }
    
    // Hide search results when clicking outside
    document.addEventListener('click', (event) => {
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer && !searchContainer.contains(event.target)) {
            hideSearchResults();
        }
    });
    
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            hideSearchResults();
        }
    });
    
    // Mobile menu functionality
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            mobileMenuToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // Close mobile menu when clicking on a link
        navMenu.addEventListener('click', (e) => {
            if (e.target.classList.contains('nav-link')) {
                mobileMenuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenuToggle.contains(e.target) && !navMenu.contains(e.target)) {
                mobileMenuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });
    }
}

// --- Chapter Navigation Functions ---

/**
 * Handle reader page initialization with chapter navigation
 */
async function handleReaderPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const chapterUrl = urlParams.get('url');
    const container = document.getElementById('reader-content');
    const prevBtn = document.getElementById('prev-chapter-btn');
    const nextBtn = document.getElementById('next-chapter-btn');
    const chapterTitle = document.getElementById('reader-title');
    
    if (!chapterUrl) {
        showErrorState(container, 'No chapter URL provided.');
        return;
    }
    
    if (!container) {
        console.error('Reader content container not found');
        return;
    }
    
    showLoadingState(container, 'Loading chapter...');
    
    try {
        const result = await makeApiRequest(`${API_BASE_URL}/chapter-details?url=${encodeURIComponent(chapterUrl)}`);
        
        // Display chapter images
        displayChapterImages(result.images, container);
        
        // Update navigation buttons
        updateChapterNavigation(prevBtn, nextBtn, result.prev_chapter_url, result.next_chapter_url);
        
        // Update chapter title with progress info
        if (chapterTitle) {
            const progress = `Chapter ${result.current_chapter_index + 1} of ${result.total_chapters}`;
            chapterTitle.textContent = progress;
        }
        
    } catch (error) {
        console.error('Error loading chapter details:', error);
        showErrorState(container, `Failed to load chapter: ${error.message}`, true);
    }
}

/**
 * Display chapter images in the reader
 */
function displayChapterImages(images, container) {
    if (!container) return;
    
    if (!images || images.length === 0) {
        showEmptyState(container, 'No chapter images found.');
        return;
    }
    
    container.innerHTML = '';
    
    images.forEach((imageUrl, index) => {
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = `Chapter page ${index + 1}`;
        img.className = 'reader-image';
        img.loading = 'lazy';
        
        // Add error handling for images
        img.onerror = function() {
            this.style.display = 'none';
            const placeholder = document.createElement('div');
            placeholder.className = 'image-placeholder';
            placeholder.innerHTML = `<span>📄</span><p>Page ${index + 1}</p>`;
            this.parentNode.insertBefore(placeholder, this.nextSibling);
        };
        
        container.appendChild(img);
    });
}

/**
 * Update chapter navigation buttons
 */
function updateChapterNavigation(prevBtn, nextBtn, prevUrl, nextUrl) {
    if (prevBtn) {
        if (prevUrl) {
            prevBtn.disabled = false;
            prevBtn.onclick = () => {
                window.location.href = `reader.html?url=${encodeURIComponent(prevUrl)}`;
            };
            prevBtn.textContent = '← Previous';
        } else {
            prevBtn.disabled = true;
            prevBtn.textContent = '← First';
        }
    }
    
    if (nextBtn) {
        if (nextUrl) {
            nextBtn.disabled = false;
            nextBtn.onclick = () => {
                window.location.href = `reader.html?url=${encodeURIComponent(nextUrl)}`;
            };
            nextBtn.textContent = 'Next →';
        } else {
            nextBtn.disabled = true;
            nextBtn.textContent = 'Last →';
        }
    }
}

// --- Global Functions (for external use) ---

/**
 * Global function for reader page to load chapter images
 */
window.loadChapterImages = loadChapterImages;

// --- Initialization ---

/**
 * Main initialization function
 */
function initialize() {
    try {
        initializeEventListeners();
        initializePage();
        console.log('ManhwaVerse frontend initialized successfully');
    } catch (error) {
        console.error('Failed to initialize ManhwaVerse frontend:', error);
    }
}

// Start the application when DOM is ready
document.addEventListener('DOMContentLoaded', initialize);