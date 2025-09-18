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
const API_BASE_URL = '/api';
const DEBOUNCE_DELAY = 300;
const MAX_SEARCH_RESULTS = 7;
const REQUEST_TIMEOUT = 15000;

// --- Initialize Storage and Components ---
// Temporarily disabled for debugging
// let storageManager, uiComponents;

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
    console.log('Making API request to:', url);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!data.success) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('Request timed out. Please try again.');
        }
        
        console.error('API request failed:', error);
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
    
    // Temporarily disabled bookmark functionality
    const isBookmarked = false;
    
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
            <div class="bookmark-container">
                <button class="bookmark-btn ${isBookmarked ? 'bookmarked' : ''}" 
                        data-manga='${JSON.stringify(manga)}' 
                        onclick="event.preventDefault(); event.stopPropagation(); toggleBookmark(this)">
                    <svg class="bookmark-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <span class="bookmark-text">${isBookmarked ? 'Bookmarked' : 'Bookmark'}</span>
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
    
    console.log('Homepage content loading...');
    console.log('Trending grid found:', !!trendingGrid);
    console.log('Updates grid found:', !!updatesGrid);
    
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
        console.log('Making API request to:', `${API_BASE_URL}/popular`);
        const result = await makeApiRequest(`${API_BASE_URL}/popular`);
        console.log('API response received:', result);
        
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
    console.log('handleDetailPage called');
    const urlParams = new URLSearchParams(window.location.search);
    const detailUrl = urlParams.get('url');
    const container = document.getElementById('detail-container');
    const mangaContent = document.getElementById('manga-details-content');
    
    console.log('Detail URL:', detailUrl);
    console.log('Container found:', !!container);
    console.log('Manga content found:', !!mangaContent);
    
    if (!detailUrl) {
        console.error('No manga URL provided');
        showErrorState(container, 'No manga URL provided.');
        return;
    }
    
    if (mangaContent) {
        showLoadingState(mangaContent, 'Loading manga details...');
    }
    
    try {
        console.log('Making API request for manga details...');
        const result = await makeApiRequest(`${API_BASE_URL}/manga-details?url=${encodeURIComponent(detailUrl)}`);
        console.log('Manga details API response:', result);
        console.log('Calling displayMangaDetails with data:', result.data);
        displayMangaDetails(result.data);
        console.log('displayMangaDetails call completed');
    } catch (error) {
        console.error('Error loading manga details:', error);
        showErrorState(container, `Failed to load manga details: ${error.message}`, true);
    }
}

/**
 * Display manga details on detail page with source selector
 */
function displayMangaDetails(data, source = 'AsuraScanz') {
    console.log('displayMangaDetails called with data:', data);
    const container = document.getElementById('detail-container');
    const mangaContent = document.getElementById('manga-details-content');
    
    console.log('Container found:', !!container);
    console.log('Manga content found:', !!mangaContent);
    
    if (!container || !mangaContent) {
        console.error('Required elements not found for manga details display');
        return;
    }
    
    // Store current source and data globally
    window.currentMangaSource = source;
    window.currentMangaData = data;
    window.mangaChapters = data.chapters;
    
    // Store chapters in sessionStorage for chapter navigation
    sessionStorage.setItem('current_manga_chapters', JSON.stringify(data.chapters));
    
    // Show source selector if multiple sources available
    const sourceSelector = document.getElementById('source-selector');
    if (sourceSelector) {
        sourceSelector.style.display = 'block';
        initializeSourceSelector();
    }
    
    // Update page title
    document.title = `${data.title} - ManhwaVerse`;
    
    // Create genres HTML
    const genresHtml = data.genres.map(genre => 
        `<span class="genre-tag">${genre}</span>`
    ).join('');
    
    // Create chapters HTML (default: descending order - newest first)
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
            <div class="chapter-list-controls">
                <button id="sort-asc-btn" class="sort-btn">Sort Ascending ↑</button>
                <button id="sort-desc-btn" class="sort-btn active">Sort Descending ↓</button>
            </div>
            <div id="chapter-list" class="chapter-list">${chaptersHtml}</div>
        </div>
    `;
    
    // Add event listeners for sorting
    initializeChapterSorting();
}

/**
 * Initialize source selector functionality
 */
function initializeSourceSelector() {
    const sourceButtons = document.querySelectorAll('.source-btn');
    
    sourceButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const source = button.dataset.source;
            const mangaContent = document.getElementById('manga-details-content');
            
            if (!mangaContent) return;
            
            // Update active button
            sourceButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show loading state
            showLoadingState(mangaContent, `Loading from ${source}...`);
            
            try {
                // Fetch data from the selected source
                const data = await fetchMangaFromSource(window.currentMangaData.title, source);
                if (data) {
                    window.currentMangaSource = source;
                    window.currentMangaData = data;
                    window.mangaChapters = data.chapters;
                    sessionStorage.setItem('current_manga_chapters', JSON.stringify(data.chapters));
                    renderMangaContent(data, mangaContent);
                    initializeChapterSorting();
                } else {
                    showErrorState(mangaContent, `No data available from ${source}`);
                }
            } catch (error) {
                console.error(`Error loading from ${source}:`, error);
                showErrorState(mangaContent, `Failed to load from ${source}: ${error.message}`);
            }
        });
    });
}

/**
 * Fetch manga data from specific source
 */
async function fetchMangaFromSource(title, source) {
    try {
        const response = await makeApiRequest(`${API_BASE_URL}/unified-details?title=${encodeURIComponent(title)}&source=${encodeURIComponent(source)}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching from ${source}:`, error);
        return null;
    }
}

/**
 * Render manga content in the details container
 */
function renderMangaContent(data, container) {
    // Create genres HTML
    const genresHtml = data.genres.map(genre => 
        `<span class="genre-tag">${genre}</span>`
    ).join('');
    
    // Create chapters HTML (default: descending order - newest first)
    const chaptersHtml = data.chapters.map(chapter => `
        <a href="reader.html?url=${encodeURIComponent(chapter.url)}&source=${encodeURIComponent(data.source || 'AsuraScanz')}" class="chapter-item">
            <span class="chapter-title">${chapter.title}</span>
            <span class="chapter-date">${chapter.date}</span>
        </a>
    `).join('');
    
    // Create the complete HTML
    const html = `
        <div class="detail-grid">
            <div class="detail-cover">
                <img src="${data.cover_image || data.cover_url}" alt="${data.title}" loading="lazy">
            </div>
            <div class="detail-info">
                <h1>${data.title}</h1>
                <div class="detail-meta">
                    <span class="detail-rating">⭐ ${data.rating || 'N/A'}</span>
                    <span class="detail-status">${data.status || 'Ongoing'}</span>
                    <span class="detail-source">Source: ${data.source || 'Unknown'}</span>
                </div>
                <div class="detail-genres">${genresHtml}</div>
                <p class="detail-description">${data.description || 'No description available.'}</p>
            </div>
        </div>
        <div class="chapter-list-container">
            <h2>Chapters</h2>
            <div class="chapter-list-controls">
                <button id="sort-asc-btn" class="sort-btn">Sort Ascending ↑</button>
                <button id="sort-desc-btn" class="sort-btn active">Sort Descending ↓</button>
            </div>
            <div id="chapter-list" class="chapter-list">${chaptersHtml}</div>
        </div>
    `;
    
    // Inject the HTML
    container.innerHTML = html;
}

/**
 * Initialize chapter sorting functionality
 */
function initializeChapterSorting() {
    const sortAscBtn = document.getElementById('sort-asc-btn');
    const sortDescBtn = document.getElementById('sort-desc-btn');
    const chapterList = document.getElementById('chapter-list');
    
    if (!sortAscBtn || !sortDescBtn || !chapterList) return;
    
    // Sort ascending (oldest first)
    sortAscBtn.addEventListener('click', () => {
        if (window.mangaChapters) {
            const sortedChapters = [...window.mangaChapters].reverse();
            renderChapterList(sortedChapters, chapterList);
            updateSortButtons(sortAscBtn, sortDescBtn);
        }
    });
    
    // Sort descending (newest first)
    sortDescBtn.addEventListener('click', () => {
        if (window.mangaChapters) {
            const sortedChapters = [...window.mangaChapters];
            renderChapterList(sortedChapters, chapterList);
            updateSortButtons(sortDescBtn, sortAscBtn);
        }
    });
}

/**
 * Render chapter list HTML
 */
function renderChapterList(chapters, container) {
    const chaptersHtml = chapters.map(chapter => `
        <a href="reader.html?url=${encodeURIComponent(chapter.url)}" class="chapter-item">
            <span class="chapter-title">${chapter.title}</span>
            <span class="chapter-date">${chapter.date}</span>
        </a>
    `).join('');
    
    container.innerHTML = chaptersHtml;
}

/**
 * Update sort button active states
 */
function updateSortButtons(activeBtn, inactiveBtn) {
    activeBtn.classList.add('active');
    inactiveBtn.classList.remove('active');
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
        mobileMenuToggle.addEventListener('click', (e) => {
            e.stopPropagation();
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
 * Handle reader page initialization with sessionStorage-based chapter navigation
 */
async function handleReaderPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const chapterUrl = urlParams.get('url');
    const source = urlParams.get('source') || 'AsuraScanz';
    const container = document.getElementById('reader-content');
    const prevHeaderBtn = document.getElementById('prev-chapter-header');
    const nextHeaderBtn = document.getElementById('next-chapter-header');
    const prevFooterBtn = document.getElementById('prev-chapter-footer');
    const nextFooterBtn = document.getElementById('next-chapter-footer');
    const chapterTitle = document.getElementById('reader-title');
    const endOfChapterNav = document.getElementById('end-of-chapter-nav');
    
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
        // Load the chapter images using unified API
        const chapterResult = await makeApiRequest(`${API_BASE_URL}/unified-chapter-data?url=${encodeURIComponent(chapterUrl)}&source=${encodeURIComponent(source)}`);
        displayChapterImages(chapterResult.image_urls, container);
        
        // Get chapter navigation from sessionStorage
        const chapterList = JSON.parse(sessionStorage.getItem('current_manga_chapters') || '[]');
        
        if (chapterList.length > 0) {
            // Find current chapter index
            const currentIndex = chapterList.findIndex(chapter => chapter.url === chapterUrl);
            
            if (currentIndex !== -1) {
                // Determine next and previous chapters
                // Note: chapterList is newest-to-oldest, so:
                // - Previous chapter is at index + 1 (older chapter)
                // - Next chapter is at index - 1 (newer chapter)
                const prevChapter = currentIndex < chapterList.length - 1 ? chapterList[currentIndex + 1] : null;
                const nextChapter = currentIndex > 0 ? chapterList[currentIndex - 1] : null;
                
                // Update page title and header
                const currentChapter = chapterList[currentIndex];
                document.title = `${currentChapter.title} - ManhwaVerse`;
                if (chapterTitle) {
                    chapterTitle.textContent = currentChapter.title;
                }
                
                // Update navigation buttons
                updateChapterNavigation(prevHeaderBtn, nextHeaderBtn, prevChapter?.url, nextChapter?.url);
                updateChapterNavigation(prevFooterBtn, nextFooterBtn, prevChapter?.url, nextChapter?.url);
                
        // Show end-of-chapter navigation
        if (endOfChapterNav) {
            endOfChapterNav.style.display = 'flex';
        }
        
        // Initialize immersive reader UI
        initReaderUI();
        
        console.log('Chapter navigation:', {
            currentIndex,
            totalChapters: chapterList.length,
            prevChapter: prevChapter?.title,
            nextChapter: nextChapter?.title
        });
            } else {
                // Current chapter not found in list, show basic info
                showBasicChapterInfo(chapterUrl, chapterTitle, prevHeaderBtn, nextHeaderBtn, prevFooterBtn, nextFooterBtn, endOfChapterNav);
            }
        } else {
            // No chapter list available, show basic info
            showBasicChapterInfo(chapterUrl, chapterTitle, prevHeaderBtn, nextHeaderBtn, prevFooterBtn, nextFooterBtn, endOfChapterNav);
        }
        
    } catch (error) {
        console.error('Error loading chapter:', error);
        showErrorState(container, `Failed to load chapter: ${error.message}`, true);
    }
}

/**
 * Show basic chapter info when navigation data is not available
 */
function showBasicChapterInfo(chapterUrl, chapterTitle, prevHeaderBtn, nextHeaderBtn, prevFooterBtn, nextFooterBtn, endOfChapterNav) {
    // Extract manga title from chapter URL for basic display
    const mangaTitle = extractMangaTitleFromUrl(chapterUrl);
    const chapterTitleText = extractChapterTitleFromUrl(chapterUrl);
    
    document.title = `${chapterTitleText} - ${mangaTitle} - ManhwaVerse`;
    if (chapterTitle) {
        chapterTitle.textContent = `${mangaTitle} - ${chapterTitleText}`;
    }
    
    // Hide navigation buttons
    updateChapterNavigation(prevHeaderBtn, nextHeaderBtn, null, null);
    updateChapterNavigation(prevFooterBtn, nextFooterBtn, null, null);
    
    // Don't show end-of-chapter nav
    if (endOfChapterNav) {
        endOfChapterNav.style.display = 'none';
    }
}

/**
 * Extract manga title from chapter URL
 */
function extractMangaTitleFromUrl(chapterUrl) {
    try {
        const url = new URL(chapterUrl);
        const pathParts = url.pathname.split('/').filter(part => part);
        
        // Find the manga part (usually before 'chapter' or similar)
        for (let i = 0; i < pathParts.length; i++) {
            if (pathParts[i].includes('chapter') || pathParts[i].includes('ch')) {
                if (i > 0) {
                    return pathParts[i - 1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                }
            }
        }
        
        // Fallback: use the last part before the chapter
        if (pathParts.length > 1) {
            return pathParts[pathParts.length - 2].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        }
        
        return 'Unknown Manga';
    } catch (e) {
        return 'Unknown Manga';
    }
}

/**
 * Extract chapter title from chapter URL
 */
function extractChapterTitleFromUrl(chapterUrl) {
    try {
        const url = new URL(chapterUrl);
        const pathParts = url.pathname.split('/').filter(part => part);
        
        // Find the chapter part
        for (let i = 0; i < pathParts.length; i++) {
            if (pathParts[i].includes('chapter') || pathParts[i].includes('ch')) {
                return pathParts[i].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            }
        }
        
        // Fallback: use the last part
        const lastPart = pathParts[pathParts.length - 1];
        return lastPart.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    } catch (e) {
        return 'Chapter';
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
 * Update chapter navigation buttons/links
 */
function updateChapterNavigation(prevElement, nextElement, prevUrl, nextUrl) {
    console.log('Updating navigation:', { prevElement: !!prevElement, nextElement: !!nextElement, prevUrl, nextUrl });
    
    if (prevElement) {
        if (prevUrl) {
            console.log('Setting up previous button with URL:', prevUrl);
            prevElement.disabled = false;
            prevElement.style.display = 'block';
            prevElement.style.visibility = 'visible';
            prevElement.href = `reader.html?url=${encodeURIComponent(prevUrl)}`;
            prevElement.onclick = (e) => {
                e.preventDefault();
                window.location.href = `reader.html?url=${encodeURIComponent(prevUrl)}`;
            };
            if (prevElement.tagName === 'BUTTON') {
                prevElement.textContent = '← Previous';
            } else {
                prevElement.textContent = '← Previous Chapter';
            }
        } else {
            console.log('Hiding previous button - no URL');
            prevElement.disabled = true;
            prevElement.style.display = 'none';
            prevElement.style.visibility = 'hidden';
        }
    }
    
    if (nextElement) {
        if (nextUrl) {
            console.log('Setting up next button with URL:', nextUrl);
            nextElement.disabled = false;
            nextElement.style.display = 'block';
            nextElement.style.visibility = 'visible';
            nextElement.href = `reader.html?url=${encodeURIComponent(nextUrl)}`;
            nextElement.onclick = (e) => {
                e.preventDefault();
                window.location.href = `reader.html?url=${encodeURIComponent(nextUrl)}`;
            };
            if (nextElement.tagName === 'BUTTON') {
                nextElement.textContent = 'Next →';
            } else {
                nextElement.textContent = 'Next Chapter →';
            }
        } else {
            console.log('Hiding next button - no URL');
            nextElement.disabled = true;
            nextElement.style.display = 'none';
            nextElement.style.visibility = 'hidden';
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

/**
 * Initialize immersive reader UI with disappearing header
 */
function initReaderUI() {
    const header = document.querySelector('.header');
    if (!header) return;
    
    let lastScrollY = window.scrollY;
    let isScrolling = false;
    const scrollThreshold = 50; // Minimum scroll distance to trigger header hide/show
    
    const handleScroll = () => {
        if (isScrolling) return;
        
        isScrolling = true;
        requestAnimationFrame(() => {
            const currentScrollY = window.scrollY;
            const scrollDifference = Math.abs(currentScrollY - lastScrollY);
            
            // Only process if scroll difference is significant
            if (scrollDifference > scrollThreshold) {
                if (currentScrollY > lastScrollY && currentScrollY > 100) {
                    // Scrolling down - hide header
                    header.classList.add('header--hidden');
                } else if (currentScrollY < lastScrollY) {
                    // Scrolling up - show header
                    header.classList.remove('header--hidden');
                }
                
                lastScrollY = currentScrollY;
            }
            
            isScrolling = false;
        });
    };
    
    // Add scroll event listener with throttling
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // Clean up function (optional - for if the reader is dynamically loaded/unloaded)
    return () => {
        window.removeEventListener('scroll', handleScroll);
    };
}

// --- User Features Initialization ---
function initializeUserFeatures() {
    try {
        // Add bookmark buttons to existing manga cards
        addBookmarkButtonsToExistingCards();
        
        // Initialize reading history tracking
        initializeReadingHistory();
        
        // Add progress indicators
        addProgressIndicators();
    } catch (error) {
        console.error('Error initializing user features:', error);
    }
}

function addBookmarkButtonsToExistingCards() {
    const mangaCards = document.querySelectorAll('.manhwa-card');
    mangaCards.forEach(card => {
        const titleElement = card.querySelector('.manhwa-title');
        if (titleElement && !card.querySelector('.bookmark-btn')) {
            const title = titleElement.textContent;
            const cover = card.querySelector('.manhwa-cover img')?.src;
            const detailUrl = card.closest('a')?.href;
            
            if (title && detailUrl) {
                const mangaData = {
                    title: title,
                    cover_image: cover,
                    detail_url: detailUrl,
                    source: 'AsuraScanz'
                };
                
                const bookmarkContainer = document.createElement('div');
                bookmarkContainer.className = 'bookmark-container';
                card.appendChild(bookmarkContainer);
                uiComponents.createBookmarkButton(mangaData, bookmarkContainer);
            }
        }
    });
}

function initializeReadingHistory() {
    // Track when user reads a chapter
    const currentUrl = window.location.href;
    if (currentUrl.includes('reader.html')) {
        const urlParams = new URLSearchParams(window.location.search);
        const chapterUrl = urlParams.get('url');
        const source = urlParams.get('source') || 'AsuraScanz';
        
        if (chapterUrl) {
            // Get manga data from session storage or URL
            const mangaData = getMangaDataFromContext();
            const chapterData = {
                title: extractChapterTitleFromUrl(chapterUrl),
                url: chapterUrl
            };
            
            if (mangaData && chapterData.title) {
                storageManager.addToHistory(mangaData, chapterData);
            }
        }
    }
}

function getMangaDataFromContext() {
    // Try to get from session storage first
    const storedData = sessionStorage.getItem('current_manga_data');
    if (storedData) {
        return JSON.parse(storedData);
    }
    
    // Fallback: extract from URL or page context
    const currentUrl = window.location.href;
    if (currentUrl.includes('reader.html')) {
        const urlParams = new URLSearchParams(window.location.search);
        const chapterUrl = urlParams.get('url');
        
        if (chapterUrl) {
            return {
                title: extractMangaTitleFromUrl(chapterUrl),
                cover_image: 'assets/images/default-cover.jpg',
                detail_url: '#',
                source: urlParams.get('source') || 'AsuraScanz'
            };
        }
    }
    
    return null;
}

function addProgressIndicators() {
    const mangaCards = document.querySelectorAll('.manhwa-card');
    mangaCards.forEach(card => {
        const titleElement = card.querySelector('.manhwa-title');
        if (titleElement) {
            const title = titleElement.textContent;
            const progress = storageManager.getReadingProgress(title);
            
            if (progress) {
                const progressIndicator = uiComponents.createProgressIndicator(title);
                if (progressIndicator) {
                    card.appendChild(progressIndicator);
                }
            }
        }
    });
}

// Global functions for inline event handlers
window.toggleBookmark = function(button) {
    if (!storageManager || !uiComponents) {
        console.warn('Storage or components not available for bookmark toggle');
        return;
    }
    
    try {
        const mangaData = JSON.parse(button.dataset.manga);
        const isBookmarked = storageManager.isBookmarked(mangaData.title);
        
        if (isBookmarked) {
            storageManager.removeBookmark(mangaData.title);
            button.classList.remove('bookmarked');
            button.querySelector('.bookmark-text').textContent = 'Bookmark';
            uiComponents.showNotification('Removed from bookmarks', 'success');
        } else {
            storageManager.addBookmark(mangaData);
            button.classList.add('bookmarked');
            button.querySelector('.bookmark-text').textContent = 'Bookmarked';
            uiComponents.showNotification('Added to bookmarks', 'success');
        }
    } catch (error) {
        console.error('Error toggling bookmark:', error);
    }
};

// Start the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initialize();
});