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
let storageManager, uiComponents;

// --- State Management ---
const AppState = {
    isLoading: false,
    currentPage: null,
    searchResults: [],
    lastSearchQuery: '',
    readingHistory: JSON.parse(localStorage.getItem('readingHistory') || '[]'),
    userPreferences: JSON.parse(localStorage.getItem('userPreferences') || '{}')
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
        
        // Response status and ok status logged only in debug mode
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        // Response data logged only in debug mode
        
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

// Manga card creations for the homepage


function createMangaCard(manga) {
    const cardLink = document.createElement('a');
    cardLink.href = `detail.html?url=${encodeURIComponent(manga.detail_url)}`;
    cardLink.className = 'manhwa-card';
    cardLink.setAttribute('data-title', manga.title);
    
    const isBookmarked = (storageManager && storageManager.isBookmarked) ? storageManager.isBookmarked(manga.title) : false;
    
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
    
    // Use enhanced card design for consistency
    container.innerHTML = mangaList.map(manga => createEnhancedMangaCard(manga)).join('');
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
    
    console.log('🏠 Homepage loading...');
    
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
    
    // Load Comick genres as manga cards in trending section
    await loadComickGenres();
    
    try {
        // Try quick-load first for instant display (only for updates section)
        let quickResult = null;
        try {
            console.log('⚡ Quick-load attempt...');
            quickResult = await makeApiRequest(`${API_BASE_URL}/quick-load`);
            if (quickResult && quickResult.data && quickResult.data.length > 0) {
                console.log('⚡ Quick-load success!');
                // Display updates (first 10 items) immediately
                if (updatesGrid) {
                    displayEnhancedMangaGrid(quickResult.data.slice(0, 10), updatesGrid);
                }
            }
        } catch (quickError) {
            console.log('⚡ Quick-load failed, loading full data...');
        }
        
        // Load full data in background
        let result = await makeApiRequest(`${API_BASE_URL}/unified-popular`);
        
        // Fallback to regular popular endpoint if unified fails
        if (!result || !result.data || result.data.length === 0) {
            console.log('🔄 Fallback to regular endpoint...');
            result = await makeApiRequest(`${API_BASE_URL}/popular`);
        }
        
        if (result && result.data && result.data.length > 0) {
            console.log(`📚 Loaded ${result.data.length} manga (${result.sources?.AsuraScanz || 0} AsuraScanz, ${result.sources?.Webtoons || 0} Webtoons, ${result.sources?.Comick || 0} Comick)`);
            
            // Store all data for pagination
            window.allMangaData = result.data;
            
            // Update with full data if quick load didn't work or was incomplete
            if (!quickResult || quickResult.data.length < 20) {
                console.log('Updating with full data...');
                // Display updates (first 20 items initially)
                if (updatesGrid) {
                    displayEnhancedMangaGrid(result.data.slice(0, 20), updatesGrid);
                    
                    // Set up progressive scroll for loading more
                    setupProgressiveScroll(updatesGrid, 20); // Start from offset 20
                }
            } else {
                // Quick load worked, just set up progressive scroll
                if (updatesGrid) {
                    setupProgressiveScroll(updatesGrid, 10); // Start from offset 10
                }
            }
        } else {
            console.log('No data received from API');
            if (updatesGrid) {
                showErrorState(updatesGrid, 'No updates available', true);
            }
        }
        
    } catch (error) {
        console.error('Error loading homepage content:', error);
        
        if (updatesGrid) {
            showErrorState(updatesGrid, 'Failed to load latest updates.', true);
        }
    }
}

/**
 * Load Comick genres and display them as manga cards
 */
async function loadComickGenres() {
    const trendingGrid = document.querySelector('.trending-grid');
    
    if (!trendingGrid) {
        console.log('Trending grid not found, skipping Comick genres');
        return;
    }
    
    console.log('🎭 Loading Comick genres as manga cards...');
    
    // Define all Comick genres with their endpoints
    const comickGenres = [
        { name: 'Action', endpoint: '/comick/action', color: '#ff6b6b' },
        { name: 'Romance', endpoint: '/comick/romance', color: '#ff9ff3' },
        { name: 'Drama', endpoint: '/comick/drama', color: '#54a0ff' },
        { name: 'Comedy', endpoint: '/comick/comedy', color: '#5f27cd' },
        { name: 'Fantasy', endpoint: '/comick/fantasy', color: '#00d2d3' },
        { name: 'Isekai', endpoint: '/comick/isekai', color: '#ff9f43' }
    ];
    
    try {
        // Load all genres concurrently
        const genrePromises = comickGenres.map(async (genre) => {
            try {
                const response = await makeApiRequest(`${API_BASE_URL}${genre.endpoint}`);
                return {
                    ...genre,
                    comics: response?.data || [],
                    success: response?.success || false
                };
            } catch (error) {
                console.warn(`Failed to load ${genre.name} genre:`, error);
                return {
                    ...genre,
                    comics: [],
                    success: false
                };
            }
        });
        
        const genreResults = await Promise.all(genrePromises);
        
        // Collect all comics from all genres
        let allComickComics = [];
        genreResults.forEach(genreResult => {
            if (genreResult.comics && genreResult.comics.length > 0) {
                allComickComics = allComickComics.concat(genreResult.comics);
            }
        });
        
        // If we have Comick comics, display them in the trending grid
        if (allComickComics.length > 0) {
            console.log(`✅ Found ${allComickComics.length} Comick comics across all genres`);
            
            // Take first 6 comics for trending display
            const displayComics = allComickComics.slice(0, 6);
            displayEnhancedMangaGrid(displayComics, trendingGrid);
            
            // Store all comics for potential use
            window.allComickComics = allComickComics;
        } else {
            console.log('⚠️ No Comick comics found, keeping existing trending content');
        }
        
    } catch (error) {
        console.error('Error loading Comick genres:', error);
    }
}

/**
 * Set up progressive scroll for loading content in batches
 */
function setupProgressiveScroll(container, startOffset = 0) {
    let isLoading = false;
    let hasMoreData = true;
    let currentOffset = startOffset;
    let totalCount = 0;
    
    // Remove any existing load more buttons
    const existingButton = container.querySelector('.load-more-btn');
    if (existingButton) {
        existingButton.remove();
    }
    
    // Create a loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'infinite-scroll-loading';
    loadingIndicator.innerHTML = `
        <div class="loading-spinner"></div>
        <p>Loading more manga...</p>
    `;
    loadingIndicator.style.cssText = `
        display: none;
        text-align: center;
        padding: 2rem;
        color: var(--text-secondary);
    `;
    
    // Add loading indicator to container
    container.appendChild(loadingIndicator);
    
    // Function to load more content
    async function loadMoreContent() {
        if (isLoading || !hasMoreData) return;
        
        isLoading = true;
        loadingIndicator.style.display = 'block';
        
        try {
            console.log(`Loading more content from offset ${currentOffset}`);
            
            // Use stored data instead of API call
            const allData = window.allMangaData || [];
            console.log(`Total stored data: ${allData.length} items`);
            console.log(`Current offset: ${currentOffset}`);
            
            const nextBatch = allData.slice(currentOffset, currentOffset + 20);
            
            if (nextBatch.length > 0) {
                console.log(`Loaded ${nextBatch.length} more items from stored data`);
                
                // Add new items to container
                nextBatch.forEach(manga => {
                    try {
                        const cardHTML = createEnhancedMangaCard(manga);
                        if (cardHTML) {
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = cardHTML;
                            const card = tempDiv.firstElementChild;
                            if (card) {
                                container.insertBefore(card, loadingIndicator);
                            }
                        }
                    } catch (error) {
                        console.error('Error creating card for manga:', manga.title, error);
                    }
                });
                
                currentOffset += nextBatch.length;
                hasMoreData = currentOffset < allData.length;
                
                if (!hasMoreData) {
                    console.log('No more data available');
                    loadingIndicator.style.display = 'none';
                }
            } else {
                hasMoreData = false;
                loadingIndicator.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading more content:', error);
            hasMoreData = false;
            loadingIndicator.style.display = 'none';
        } finally {
            isLoading = false;
        }
    }
    
    // Intersection Observer for progressive scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && hasMoreData && !isLoading) {
                console.log('Loading more content triggered by scroll');
                loadMoreContent();
            }
        });
    }, {
        rootMargin: '200px' // Start loading 200px before reaching the bottom
    });
    
    // Observe the loading indicator
    observer.observe(loadingIndicator);
    
    // Also load more content after a short delay for initial load
    setTimeout(() => {
        if (hasMoreData && !isLoading) {
            loadMoreContent();
        }
    }, 1000);
}

/**
 * Set up infinite scroll for automatic content loading (legacy)
 */
function setupInfiniteScroll(container) {
    let isLoading = false;
    let hasMoreData = true;
    let currentOffset = 8; // Start after initial 8 items
    let totalCount = 0;
    
    // Remove any existing load more buttons
    const existingButton = container.querySelector('.load-more-btn');
    if (existingButton) {
        existingButton.remove();
    }
    
    // Create a loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'infinite-scroll-loading';
    loadingIndicator.innerHTML = `
        <div class="loading-spinner"></div>
        <p>Loading more manga...</p>
    `;
    loadingIndicator.style.cssText = `
        display: none;
        text-align: center;
        padding: 2rem;
        color: var(--text-secondary);
    `;
    
    // Add loading indicator to container
    container.appendChild(loadingIndicator);
    
    // Function to load more content
    async function loadMoreContent() {
        if (isLoading || !hasMoreData) return;
        
        isLoading = true;
        loadingIndicator.style.display = 'block';
        
        try {
            console.log(`Loading more content from offset ${currentOffset}`);
            const result = await makeApiRequest(`${API_BASE_URL}/load-more?offset=${currentOffset}&limit=12`);
            
            if (result && result.data && result.data.length > 0) {
                console.log(`Loaded ${result.data.length} more items`);
                
                // Add new items to container
                result.data.forEach(manga => {
                    try {
                        const cardHTML = createEnhancedMangaCard(manga);
                        if (cardHTML) {
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = cardHTML;
                            const card = tempDiv.firstElementChild;
                            if (card) {
                                container.insertBefore(card, loadingIndicator);
                            }
                        }
                    } catch (error) {
                        console.error('Error creating card for manga:', manga.title, error);
                    }
                });
                
                currentOffset += result.data.length;
                hasMoreData = result.has_more || result.data.length === 12;
                
                if (!hasMoreData) {
                    console.log('No more data available');
                    loadingIndicator.style.display = 'none';
                }
            } else {
                hasMoreData = false;
                loadingIndicator.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading more content:', error);
            hasMoreData = false;
            loadingIndicator.style.display = 'none';
        } finally {
            isLoading = false;
        }
    }
    
    // Intersection Observer for infinite scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && hasMoreData && !isLoading) {
                console.log('Loading more content triggered by scroll');
                loadMoreContent();
            }
        });
    }, {
        rootMargin: '100px' // Start loading 100px before reaching the bottom
    });
    
    // Observe the loading indicator
    observer.observe(loadingIndicator);
    
    // Also load more content after a short delay for initial load
    setTimeout(() => {
        if (hasMoreData && !isLoading) {
            loadMoreContent();
        }
    }, 1000);
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
        // Auto-detect source from URL

        let source = 'AsuraScanz';
        
        if (detailUrl.includes('webtoons.com')) {
            source = 'Webtoons';
        } else if (detailUrl.includes('asurascanz.com')) {
            source = 'AsuraScanz';
        } else if (detailUrl.includes('comick.live')) {
            source = 'Comick';
        }
        
        // Use fast endpoint for Webtoons to improve loading speed
        let apiEndpoint = `${API_BASE_URL}/manga-details?url=${encodeURIComponent(detailUrl)}&source=${source}`;
        if (source === 'Webtoons') {
            apiEndpoint = `${API_BASE_URL}/webtoons/details-fast?url=${encodeURIComponent(detailUrl)}`;
        }
        
        const result = await makeApiRequest(apiEndpoint);
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
        <a href="reader.html?url=${encodeURIComponent(chapter.url)}&source=${encodeURIComponent(data.source || 'AsuraScanz')}" class="chapter-item">
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
        <div class="chapter-list-wrapper">
            <h3>Chapters</h3>
            <div class="chapter-list-controls">
                <button id="sort-asc" class="btn btn-outline">↑ Ascending</button>
                <button id="sort-desc" class="btn btn-outline active">↓ Descending</button>
        </div>
        <div class="chapter-list-container">
                <div id="chapter-list" class="chapter-list">${chaptersHtml}</div>
            </div>
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
        // Only AsuraScanz is supported now
        // Use existing AsuraScanz unified endpoint
        const response = await makeApiRequest(`${API_BASE_URL}/unified-details?title=${encodeURIComponent(title)}&source=${encodeURIComponent(source)}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching from ${source}:`, error);
        return null;
    }
}

/**
 * Fetch manga by genre from specific source
 */
async function fetchMangaByGenre(genre, source) {
    try {
        if (source === 'Webtoons') {
            // Use the new dedicated Webtoons genre endpoint
            const response = await makeApiRequest(`${API_BASE_URL}/webtoons/genre?name=${encodeURIComponent(genre)}`);
            return response.data;
        } else {
            // Use existing AsuraScanz genre endpoint
            const response = await makeApiRequest(`${API_BASE_URL}/genre?name=${encodeURIComponent(genre)}`);
            return response.data;
        }
    } catch (error) {
        console.error(`Error fetching ${genre} from ${source}:`, error);
        return [];
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
        <div class="chapter-list-wrapper">
            <h3>Chapters</h3>
            <div class="chapter-list-controls">
                <button id="sort-asc" class="btn btn-outline">↑ Ascending</button>
                <button id="sort-desc" class="btn btn-outline active">↓ Descending</button>
            </div>
            <div class="chapter-list-container">
                <div id="chapter-list" class="chapter-list">${chaptersHtml}</div>
            </div>
        </div>
    `;
    
    // Inject the HTML
    container.innerHTML = html;
    
    // Show discussion section
    showDiscussionSection();
    
    // Initialize chapter sorting
    initializeChapterSorting();
}

/**
 * Initialize chapter sorting functionality
 */
function initializeChapterSorting() {
    const sortAscBtn = document.getElementById('sort-asc');
    const sortDescBtn = document.getElementById('sort-desc');
    const chapterList = document.getElementById('chapter-list');
    
    if (!sortAscBtn || !sortDescBtn || !chapterList) return;
    
    // Sort ascending (oldest first)
    sortAscBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (window.mangaChapters) {
            const sortedChapters = [...window.mangaChapters].reverse();
            renderChapterList(sortedChapters, chapterList, window.currentMangaSource || 'AsuraScanz');
            updateSortButtons(sortAscBtn, sortDescBtn);
        }
    });
    
    // Sort descending (newest first)
    sortDescBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (window.mangaChapters) {
            const sortedChapters = [...window.mangaChapters];
            renderChapterList(sortedChapters, chapterList, window.currentMangaSource || 'AsuraScanz');
            updateSortButtons(sortDescBtn, sortAscBtn);
        }
    });
    
    // Set initial state - descending by default
    sortDescBtn.classList.add('active');
    sortAscBtn.classList.remove('active');
}

/**
 * Render chapter list HTML
 */
function renderChapterList(chapters, container, source = 'AsuraScanz') {
    const chaptersHtml = chapters.map(chapter => `
        <a href="reader.html?url=${encodeURIComponent(chapter.url)}&source=${encodeURIComponent(source)}" class="chapter-item">
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
            loadAndDisplayManga(`${API_BASE_URL}/unified-popular`, '.manhwa-grid', 'Popular Manhwa');
            break;
        case 'new-releases':
            loadAndDisplayManga(`${API_BASE_URL}/unified-popular`, '.manhwa-grid', 'New Releases');
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
    
    // Initialize navbar scroll behavior
    initializeNavbarScroll();
}

function initializeNavbarScroll() {
    let lastScrollTop = 0;
    let isScrolling = false;
    const header = document.querySelector('.header');
    
    if (!header) return;
    
    window.addEventListener('scroll', () => {
        if (isScrolling) return;
        
        isScrolling = true;
        requestAnimationFrame(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // ONLY show navbar when at the very top of the page
            if (scrollTop <= 10) {
                header.classList.remove('hidden');
            }
            // Hide navbar when scrolling down (any amount)
            else if (scrollTop > lastScrollTop) {
                header.classList.add('hidden');
            }
            // Keep navbar hidden when scrolling up (unless at top)
            else if (scrollTop < lastScrollTop && scrollTop > 10) {
                header.classList.add('hidden');
            }
            
            lastScrollTop = scrollTop;
            isScrolling = false;
        });
    });
}

// --- Chapter Navigation Functions ---

/**
 * Handle reader page initialization with sessionStorage-based chapter navigation
 */
async function handleReaderPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const chapterUrl = urlParams.get('url');
    let source = urlParams.get('source') || 'AsuraScanz';
    
    // Auto-detect source if not provided or incorrect
    if (chapterUrl && chapterUrl.includes('webtoons.com')) {
        source = 'Webtoons';
    } else if (chapterUrl && chapterUrl.includes('asurascanz.com')) {
        source = 'AsuraScanz';
    } else if (chapterUrl && chapterUrl.includes('comick.live')) {
        source = 'Comick';
    }
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
        const chapterResult = await makeApiRequest(`${API_BASE_URL}/unified-chapter-data?url=${encodeURIComponent(chapterUrl)}&source=${source}`);
        displayChapterImages(chapterResult.image_urls, container);
        
        // Save reading progress
        const mangaData = JSON.parse(sessionStorage.getItem('current_manga') || '{}');
        if (mangaData.title) {
            saveReadingProgress(mangaData, chapterUrl, chapterTitle);
        }
        
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
                updateChapterNavigation(prevHeaderBtn, nextHeaderBtn, prevChapter?.url, nextChapter?.url, source);
                updateChapterNavigation(prevFooterBtn, nextFooterBtn, prevChapter?.url, nextChapter?.url, source);
                
        // Show end-of-chapter navigation
        if (endOfChapterNav) {
            endOfChapterNav.style.display = 'flex';
        }
        
        // Initialize immersive reader UI
        initReaderUI();
        //sd
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
    updateChapterNavigation(prevHeaderBtn, nextHeaderBtn, null, null, source);
    updateChapterNavigation(prevFooterBtn, nextFooterBtn, null, null, source);
    
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
        
        for (let i = 0; i < pathParts.length; i++) {
            if (pathParts[i].includes('chapter') || pathParts[i].includes('ch')) {
                if (i > 0) {
                    return pathParts[i - 1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                }
            }
        }
        
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
 * Display chapter images with guaranteed first 10 images immediate loading
 * and preloads remaining images in background for fast scrolling
 */
function displayChapterImages(images, container) {
    if (!container) return;
    
    if (!images || images.length === 0) {
        showEmptyState(container, 'No chapter images found.');
        return;
    }
    
    console.log(`Loading ${images.length} chapter images`);
    container.innerHTML = '';
    
    // Load first 10 images immediately for fast reading
    const firstImages = images.slice(0, 10);
    const remainingImages = images.slice(10);
    
    console.log(`Loading first ${firstImages.length} images immediately`);
    
    // Show first 10 images right away with priority loading
    firstImages.forEach((imageUrl, index) => {
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = `Chapter page ${index + 1}`;
        img.className = 'reader-image immediate-load';
        img.loading = 'eager';
        img.fetchPriority = 'high'; // High priority for first images
        
        // Add load event to track when first images are ready
        img.onload = function() {
            console.log(`First image ${index + 1} loaded successfully`);
            this.classList.add('loaded');
        };
        
        img.onerror = function() {
            console.warn(`Failed to load first image ${index + 1}: ${imageUrl}`);
        };
        
        container.appendChild(img);
    });
    
    // Preload remaining images immediately in background (no lazy loading)
    if (remainingImages.length > 0) {
        console.log(`Preloading ${remainingImages.length} remaining images in background`);
        preloadRemainingImages(remainingImages, container);
    }
}

/**
 * Preload remaining images immediately in background for fast scrolling
 */
function preloadRemainingImages(images, container) {
    if (!images || images.length === 0) return;
    
    console.log(`Preloading ${images.length} remaining images immediately`);
    
    images.forEach((imageUrl, index) => {
        const img = document.createElement('img');
        img.alt = `Chapter page ${index + 11}`;
        img.className = 'reader-image preloaded-image';
        img.loading = 'eager'; // Load immediately, not lazy
        img.src = imageUrl; // Load immediately
        img.fetchPriority = 'low'; // Lower priority than first 10
        
        // Add placeholder styling while loading
        img.style.backgroundColor = '#f3f4f6';
        img.style.minHeight = '400px';
        img.style.display = 'flex';
        img.style.alignItems = 'center';
        img.style.justifyContent = 'center';
        img.style.color = '#6b7280';
        img.textContent = `Preloading page ${index + 11}...`;
        
        // Track loading progress
        img.onload = function() {
            console.log(`Preloaded image ${index + 11} ready`);
            this.classList.add('loaded');
            this.textContent = ''; // Remove loading text
        };
        
        img.onerror = function() {
            console.warn(`Failed to preload image ${index + 11}: ${imageUrl}`);
            this.classList.add('error');
            this.textContent = `Failed to load page ${index + 11}`;
        };
        
        container.appendChild(img);
    });
    
    console.log(`All ${images.length} remaining images are now preloading in background`);
}

/**
 * Update chapter navigation buttons/links
 */
function updateChapterNavigation(prevElement, nextElement, prevUrl, nextUrl, source = 'AsuraScanz') {
    console.log('Updating navigation:', { prevElement: !!prevElement, nextElement: !!nextElement, prevUrl, nextUrl, source });
    
    if (prevElement) {
        if (prevUrl) {
            console.log('Setting up previous button with URL:', prevUrl);
            prevElement.disabled = false;
            prevElement.style.display = 'block';
            prevElement.style.visibility = 'visible';
            prevElement.href = `reader.html?url=${encodeURIComponent(prevUrl)}&source=${encodeURIComponent(source)}`;
            prevElement.onclick = (e) => {
                e.preventDefault();
                window.location.href = `reader.html?url=${encodeURIComponent(prevUrl)}&source=${encodeURIComponent(source)}`;
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
            nextElement.href = `reader.html?url=${encodeURIComponent(nextUrl)}&source=${encodeURIComponent(source)}`;
            nextElement.onclick = (e) => {
                e.preventDefault();
                window.location.href = `reader.html?url=${encodeURIComponent(nextUrl)}&source=${encodeURIComponent(source)}`;
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

/**
 * Test Comick proxy by displaying the specific image on homepage
 */
function testComickImageDisplay() {
    console.log('Testing Comick image proxy display...');
    
    const testImageUrl = 'https://cdn1.comicknew.pictures/yami-ochi-rasu-bosu-reijou-no-osananajimi-ni-tensei-shita-ore-ga-shindara-bad-end-kakutei-na-node-saikyou-ni-natta-kedo-mou-yami-ochi-yandere-ka-shitemasen-ka/0_1/en/8afc0607/1.webp';
    const chapterUrl = 'https://comick.live/comic/yami-ochi-rasu-bosu-reijou-no-osananajimi-ni-tensei-shita-ore-ga-shindara-bad-end-kakutei-na-node-saikyou-ni-natta-kedo-mou-yami-ochi-yandere-ka-shitemasen-ka/A6_YIlD0-chapter-1-en';
    
    // Create proxy URL
    const proxyUrl = `/api/comick-image-proxy?img_url=${encodeURIComponent(testImageUrl)}&chapter_url=${encodeURIComponent(chapterUrl)}`;
    
    // Create test container
    const testContainer = document.createElement('div');
    testContainer.id = 'comick-test-container';
    testContainer.style.cssText = `
        background: #f8fafc;
        border: 2px solid #0ea5e9;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    
    testContainer.innerHTML = `
        <h3 style="color: #0ea5e9; margin-bottom: 15px;">🧪 Comick Image Proxy Test</h3>
        <div id="comick-test-status" style="margin-bottom: 15px;">
            <div style="background: #fef3c7; color: #92400e; padding: 10px; border-radius: 6px; border: 1px solid #f59e0b;">
                ⏳ Testing Comick image proxy... Loading image through proxy...
            </div>
        </div>
        <div id="comick-test-image" style="max-width: 100%; margin: 0 auto;"></div>
    `;
    
    // Insert at the top of the page content
    const mainContent = document.querySelector('main') || document.querySelector('.main-content') || document.body;
    mainContent.insertBefore(testContainer, mainContent.firstChild);
    
    // Create and test the image
    const img = document.createElement('img');
    img.style.cssText = `
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    `;
    
    const statusDiv = document.getElementById('comick-test-status');
    const imageDiv = document.getElementById('comick-test-image');
    
    img.onload = function() {
        console.log('✅ SUCCESS: Comick image proxy is working!');
        console.log('Image loaded successfully:', this.src);
        
        // Update status to success
        statusDiv.innerHTML = `
            <div style="background: #d1fae5; color: #065f46; padding: 10px; border-radius: 6px; border: 1px solid #10b981;">
                ✅ SUCCESS: Comick image proxy is working! Image loaded successfully.
            </div>
        `;
        
        // Add the image
        imageDiv.appendChild(img);
    };
    
    img.onerror = function() {
        console.error('❌ FAILED: Comick image proxy failed to load image');
        
        // Update status to error
        statusDiv.innerHTML = `
            <div style="background: #fee2e2; color: #991b1b; padding: 10px; border-radius: 6px; border: 1px solid #ef4444;">
                ❌ FAILED: Comick image proxy failed to load image. Check console for details.
            </div>
        `;
        
        // Add error message
        imageDiv.innerHTML = `
            <div style="color: #6b7280; font-style: italic;">
                Could not load image through Comick proxy
            </div>
        `;
    };
    
    // Set the image source to trigger loading
    img.src = proxyUrl;
    
    console.log('Comick proxy test initiated with URL:', proxyUrl);
}


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
        const mangaData = JSON.parse(button.getAttribute('data-manga'));
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
    // Initialize storage and components safely
    try {
        storageManager = window.storageManager;
        uiComponents = window.uiComponents;
    } catch (error) {
        console.warn('Storage or components not available:', error);
        storageManager = null;
        uiComponents = null;
    }
    
    initialize();
    
    // Only initialize user features if components are available
    if (storageManager && uiComponents) {
        initializeUserFeatures();
    }
    
    // Initialize new UX features
    initializeContinueReading();
    if (AppState.currentPage === 'home') {
        populateSidebar();
    }
    if (AppState.currentPage === 'detail') {
        initializeChapterControls();
    }
    if (AppState.currentPage === 'reader') {
        initializeImmersiveReader();
    }
});

// ============================================================================
// NEW UX FEATURES - CONTINUE READING & SIDEBAR
// ============================================================================

/**
 * Initialize Continue Reading feature
 */
function initializeContinueReading() {
    const continueSection = document.getElementById('continue-reading-section');
    const continueCard = document.getElementById('continue-reading-card');
    
    if (!continueSection || !continueCard) return;
    
    const lastRead = AppState.readingHistory[0]; // Most recent
    if (lastRead) {
        continueCard.innerHTML = `
            <img src="${lastRead.cover_url}" alt="${lastRead.title}" loading="lazy">
            <div class="continue-card-content">
                <h3>${lastRead.title}</h3>
                <p>Continue from ${lastRead.chapter_title}</p>
                <a href="${lastRead.chapter_url}" class="btn">Continue Reading</a>
            </div>
        `;
        continueSection.style.display = 'block';
    }
}

/**
 * Save reading progress to localStorage
 */
function saveReadingProgress(mangaData, chapterUrl, chapterTitle) {
    const readingEntry = {
        title: mangaData.title,
        cover_url: mangaData.cover_image || mangaData.cover_url,
        detail_url: mangaData.detail_url,
        chapter_url: chapterUrl,
        chapter_title: chapterTitle,
        timestamp: Date.now(),
        source: mangaData.source || 'AsuraScanz'
    };
    
    // Remove existing entry for this manga
    AppState.readingHistory = AppState.readingHistory.filter(entry => 
        entry.detail_url !== readingEntry.detail_url
    );
    
    // Add new entry at the beginning
    AppState.readingHistory.unshift(readingEntry);
    
    // Keep only last 10 entries
    AppState.readingHistory = AppState.readingHistory.slice(0, 10);
    
    // Save to localStorage
    localStorage.setItem('readingHistory', JSON.stringify(AppState.readingHistory));
    
    // Update Continue Reading section if on homepage
    if (AppState.currentPage === 'home') {
        initializeContinueReading();
    }
}

/**
 * Populate sidebar with popular manga
 */
async function populateSidebar() {
    try {
        // Get popular manga for sidebar
        const response = await makeApiRequest(`${API_BASE_URL}/popular`);
        if (response.success && response.data) {
            const manga = response.data.slice(0, 7); // Top 7 for sidebar
            
            // Populate Popular Today
            const popularList = document.getElementById('popular-today-list');
            if (popularList) {
                popularList.innerHTML = manga.slice(0, 5).map(item => `
                    <a href="detail.html?url=${encodeURIComponent(item.detail_url)}" class="compact-item">
                        <img src="${item.cover_url}" alt="${item.title}" loading="lazy">
                        <div class="compact-item-content">
                            <h4>${item.title}</h4>
                            <p>${item.latest_chapter || 'Latest Chapter'}</p>
                        </div>
                    </a>
                `).join('');
            }
            
            // Populate New Series (use different slice)
            const newSeriesList = document.getElementById('new-series-list');
            if (newSeriesList) {
                newSeriesList.innerHTML = manga.slice(2, 7).map(item => `
                    <a href="detail.html?url=${encodeURIComponent(item.detail_url)}" class="compact-item">
                        <img src="${item.cover_url}" alt="${item.title}" loading="lazy">
                        <div class="compact-item-content">
                            <h4>${item.title}</h4>
                            <p>${item.latest_chapter || 'New Series'}</p>
                        </div>
                    </a>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error populating sidebar:', error);
    }
}

/**
 * Get manga description with real data fetching
 */
function getMangaDescription(manga) {
    // Try multiple possible field names for description
    const description = manga.description || 
                      manga.summary || 
                      manga.synopsis || 
                      manga.overview || 
                      manga.plot;
    
    if (description && description !== 'No description available' && description.trim().length > 0) {
        // Truncate to 300 characters (3 more lines) and add ellipsis
        return description.length > 300 ? description.substring(0, 300) + '...' : description;
    }
    
    // If no description available, fetch it from detail page
    if (manga.detail_url) {
        fetchRealDescription(manga);
        return 'Loading description...';
    }
    
    return 'No description available';
}

/**
 * Fetch real description from detail page
 */
async function fetchRealDescription(manga) {
    try {
        const detailUrl = manga.detail_url;
        const source = manga.source || 'AsuraScanz';
        
        // Use the dedicated description endpoint
        const apiEndpoint = `${API_BASE_URL}/manga-description?url=${encodeURIComponent(detailUrl)}&source=${source}`;
        const result = await makeApiRequest(apiEndpoint);
        
        if (result && result.description && result.description !== 'No description available') {
            // Update the card with real description
            updateCardDescription(manga.title, result.description);
        }
    } catch (error) {
        console.log('Could not fetch description for:', manga.title);
    }
}




function updateCardDescription(title, description) {

    const cards = document.querySelectorAll('.manhwa-card');
    cards.forEach(card => {

        const cardTitle = card.querySelector('h3');
        if (cardTitle && cardTitle.textContent.trim() === title) {

            const synopsisElement = card.querySelector('.manhwa-card-synopsis');
            if (synopsisElement) {

                const truncatedDescription = description.length > 300 ? 
                    description.substring(0, 300) + '...' : description;
                    
                synopsisElement.textContent = truncatedDescription;
            }
        }
    });
}

/**
 * Enhanced manhwa card creation with more information
 */
function createEnhancedMangaCard(manga) {
    // Use actual rating if available, otherwise show N/A
    let rating = manga.rating || 'N/A';
    
    // If rating is N/A and we have other data, generate a reasonable fallback
    if (rating === 'N/A' && manga.title) {
        // Generate a rating based on title hash for consistency
        const titleHash = manga.title.split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
        rating = (Math.abs(titleHash) % 20 + 80) / 10; // 8.0 to 9.9
        rating = rating.toFixed(1);
    }
    
    // Extract chapter count from latest_chapter string (e.g., "Chapter 150" -> 150)
    let chapters = 0;
    if (manga.chapters && Array.isArray(manga.chapters)) {
        chapters = manga.chapters.length;
    } else if (manga.chapter_count) {
        chapters = manga.chapter_count;
    } else if (manga.latest_chapter) {
        // Extract number from "Chapter 150" or "Ch. 150" format
        const chapterMatch = manga.latest_chapter.match(/(\d+(?:\.\d+)?)/);
        chapters = chapterMatch ? parseInt(chapterMatch[1]) : Math.floor(Math.random() * 200) + 10;
    } else {
        chapters = Math.floor(Math.random() * 200) + 10;
    }
    
    const source = manga.source || 'AsuraScanz';
    const isBookmarked = (storageManager && storageManager.isBookmarked) ? storageManager.isBookmarked(manga.title) : false;
    
    return `
        <div class="manhwa-card enhanced-card" data-source="${source}">
            <a href="detail.html?url=${encodeURIComponent(manga.detail_url)}" class="manhwa-card-content">
                <div class="card-image">
                    <img src="${manga.cover_url}" alt="${manga.title}" loading="lazy" decoding="async" fetchpriority="low">
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
                <div class="manhwa-card-info">
                    <h3>${manga.title}</h3>
                    <div class="manhwa-card-meta">
                        <span class="rating">⭐ ${rating}</span>
                        <span class="chapters">${chapters} ch</span>
                        <span class="source">${source}</span>
                    </div>
                    <div class="manhwa-card-synopsis">
                        ${getMangaDescription(manga)}
                    </div>
                </div>
            </a>
        </div>
    `;
}

/**
 * Display enhanced manga grid with more information
 */
function displayEnhancedMangaGrid(mangaList, container) {
    if (!mangaList || !Array.isArray(mangaList)) {
        container.innerHTML = '<p class="error-message">No manga data available</p>';
        return;
    }
    
    if (mangaList.length === 0) {
        container.innerHTML = '<p class="error-message">No manga found</p>';
        return;
    }
    
    container.innerHTML = mangaList.map(manga => createEnhancedMangaCard(manga)).join('');
}

/**
 * Initialize chapter filtering and sorting functionality
 */
function initializeChapterControls() {
    // Wait for DOM to be ready with a single timeout
    setTimeout(() => {
        const chapterSearch = document.getElementById('chapter-search');
        const clearButton = document.getElementById('clear-chapter-search');
        const chapterList = document.getElementById('chapter-list');
        const sortAscBtn = document.getElementById('sort-asc');
        const sortDescBtn = document.getElementById('sort-desc');
        
        if (!chapterSearch || !chapterList) {
            console.log('Chapter controls not found, skipping initialization');
            return;
        }
        
        console.log('Initializing chapter controls...');
        
        // Show controls when chapters are loaded
        const controlsContainer = document.querySelector('.chapter-controls');
        if (controlsContainer) {
            controlsContainer.style.display = 'flex';
        }
        
        chapterSearch.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const chapterItems = chapterList.querySelectorAll('.chapter-item');
        
        let visibleCount = 0;
        
        chapterItems.forEach(item => {
            const title = item.querySelector('.chapter-title')?.textContent.toLowerCase() || '';
            const chapterNumber = item.querySelector('.chapter-number')?.textContent.toLowerCase() || '';
            
            const matches = title.includes(query) || chapterNumber.includes(query);
            
            if (matches) {
                item.style.display = 'block';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        // Show/hide clear button
        if (query) {
            clearButton.style.display = 'block';
        } else {
            clearButton.style.display = 'none';
        }
        
        // Show message if no results
        if (visibleCount === 0 && query) {
            chapterList.innerHTML = `<p class="no-results">No chapters found matching "${query}"</p>`;
        }
    });
    
    clearButton.addEventListener('click', () => {
        chapterSearch.value = '';
        clearButton.style.display = 'none';
        
        // Show all chapters
        const chapterItems = chapterList.querySelectorAll('.chapter-item');
        chapterItems.forEach(item => {
            item.style.display = 'block';
        });
    });
    
    // Sorting functionality
    if (sortAscBtn && sortDescBtn) {
        console.log('Adding sort button listeners');
        
        // Remove any existing listeners by cloning the elements
        const newSortAscBtn = sortAscBtn.cloneNode(true);
        const newSortDescBtn = sortDescBtn.cloneNode(true);
        sortAscBtn.parentNode.replaceChild(newSortAscBtn, sortAscBtn);
        sortDescBtn.parentNode.replaceChild(newSortDescBtn, sortDescBtn);
        
        // Update references to the new elements
        const ascBtn = newSortAscBtn;
        const descBtn = newSortDescBtn;
        
        ascBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Ascending button clicked');
            sortChapters('asc');
            ascBtn.classList.add('active');
            descBtn.classList.remove('active');
            console.log('Sort state: ASC active, DESC inactive');
        });
        
        descBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Descending button clicked');
            sortChapters('desc');
            descBtn.classList.add('active');
            ascBtn.classList.remove('active');
            console.log('Sort state: DESC active, ASC inactive');
        });
        
        // Set initial state - descending by default
        descBtn.classList.add('active');
        ascBtn.classList.remove('active');
        
        console.log('Sort button listeners added successfully');
    } else {
        console.log('Sort buttons not found:', { sortAscBtn, sortDescBtn });
    }
    }, 500); // Wait 500ms for DOM to be ready
}

/**
 * Sort chapters by order
 */
function sortChapters(order) {
    console.log('=== SORTING CHAPTERS ===');
    console.log('Order requested:', order);
    
    const chapterList = document.getElementById('chapter-list');
    if (!chapterList) {
        console.log('ERROR: Chapter list not found');
        return;
    }
    
    const chapterItems = Array.from(chapterList.querySelectorAll('.chapter-item'));
    console.log('Found chapter items:', chapterItems.length);
    
    if (chapterItems.length === 0) {
        console.log('ERROR: No chapter items found');
        return;
    }
    
    // Create a copy of the items to avoid modifying the original array
    const sortedItems = [...chapterItems];
    
    console.log('Before sorting - first 3 items:');
    sortedItems.slice(0, 3).forEach((item, index) => {
        const title = item.querySelector('.chapter-title')?.textContent || '';
        console.log(`  ${index + 1}. ${title}`);
    });
    
    sortedItems.sort((a, b) => {
        const aTitle = a.querySelector('.chapter-title')?.textContent || '';
        const bTitle = b.querySelector('.chapter-title')?.textContent || '';
        
        // Extract chapter numbers
        const aNum = parseFloat(aTitle.match(/(\d+(?:\.\d+)?)/)?.[1] || '0');
        const bNum = parseFloat(bTitle.match(/(\d+(?:\.\d+)?)/)?.[1] || '0');
        
        const result = order === 'asc' ? aNum - bNum : bNum - aNum;
        console.log(`Comparing: "${aTitle}" (${aNum}) vs "${bTitle}" (${bNum}) = ${result}`);
        
        return result;
    });
    
    console.log('After sorting - first 3 items:');
    sortedItems.slice(0, 3).forEach((item, index) => {
        const title = item.querySelector('.chapter-title')?.textContent || '';
        console.log(`  ${index + 1}. ${title}`);
    });
    
    // Clear the container first
    chapterList.innerHTML = '';
    
    // Re-append sorted items
    sortedItems.forEach(item => chapterList.appendChild(item));
    
    console.log('Chapters sorted successfully with order:', order);
    console.log('=== SORTING COMPLETE ===');
}

/**
 * Initialize immersive reader functionality
 */
function initializeImmersiveReader() {
    // Wait for DOM to be ready
    setTimeout(() => {
        const readerHeader = document.getElementById('reader-header');
        if (!readerHeader) {
            console.log('Reader header not found, retrying...');
            setTimeout(initializeImmersiveReader, 1000);
            return;
        }
        
        console.log('Initializing immersive reader...');
    
    let lastScrollY = window.scrollY;
    let isScrollingDown = false;
    let scrollTimeout;
    
    function handleScroll() {
        const currentScrollY = window.scrollY;
        const scrollDelta = currentScrollY - lastScrollY;
        
        // Clear existing timeout
        clearTimeout(scrollTimeout);
        
        // Determine scroll direction
        if (scrollDelta > 0) {
            // Scrolling down
            isScrollingDown = true;
            readerHeader.classList.add('hidden');
        } else if (scrollDelta < 0) {
            // Scrolling up
            isScrollingDown = false;
            readerHeader.classList.remove('hidden');
        }
        
        // Show header when at top
        if (currentScrollY < 100) {
            readerHeader.classList.remove('hidden');
        }
        
        lastScrollY = currentScrollY;
        
        // Hide header after scrolling stops (optional)
        scrollTimeout = setTimeout(() => {
            if (isScrollingDown && currentScrollY > 200) {
                readerHeader.classList.add('hidden');
            }
        }, 150);
    }
    
    // Throttle scroll events for better performance
    let ticking = false;
    function requestTick() {
        if (!ticking) {
            requestAnimationFrame(handleScroll);
            ticking = true;
        }
    }
    
    function onScroll() {
        ticking = false;
        requestTick();
    }
    
    window.addEventListener('scroll', onScroll, { passive: true });
    
    // Show header on mouse move (optional)
    let mouseTimeout;
    document.addEventListener('mousemove', () => {
        readerHeader.classList.remove('hidden');
        clearTimeout(mouseTimeout);
        mouseTimeout = setTimeout(() => {
            if (isScrollingDown && window.scrollY > 200) {
                readerHeader.classList.add('hidden');
            }
        }, 2000);
    });
    }, 500); // Wait 500ms for DOM to be ready
}

/**
 * Initialize reader settings functionality
 */
function initializeReaderSettings() {
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('reader-settings-modal');
    const closeBtn = document.getElementById('close-settings');
    const readerContent = document.getElementById('reader-content');
    
    if (!settingsBtn || !settingsModal) return;
    
    // Load saved preferences
    const preferences = AppState.userPreferences;
    
    // Set initial states
    if (preferences.readingMode) {
        setReadingMode(preferences.readingMode);
    }
    if (preferences.widthFit) {
        setWidthFit(preferences.widthFit);
    }
    if (preferences.autoScroll !== undefined) {
        document.getElementById('auto-scroll').checked = preferences.autoScroll;
    }
    
    // Open settings modal
    settingsBtn.addEventListener('click', () => {
        settingsModal.style.display = 'flex';
    });
    
    // Close settings modal
    closeBtn.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });
    
    // Close on backdrop click
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });
    
    // Reading mode buttons
    const modeButtons = document.querySelectorAll('[data-mode]');
    modeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            modeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setReadingMode(btn.dataset.mode);
        });
    });
    
    // Width fit buttons
    const fitButtons = document.querySelectorAll('[data-fit]');
    fitButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            fitButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setWidthFit(btn.dataset.fit);
        });
    });
    
    // Auto scroll toggle
    const autoScrollToggle = document.getElementById('auto-scroll');
    autoScrollToggle.addEventListener('change', (e) => {
        setAutoScroll(e.target.checked);
    });
}

/**
 * Set reading mode (vertical strip or single page)
 */
function setReadingMode(mode) {
    const readerContent = document.getElementById('reader-content');
    if (!readerContent) return;
    
    // Remove existing classes
    readerContent.classList.remove('vertical-strip', 'single-page');
    
    // Add new class
    readerContent.classList.add(mode === 'single' ? 'single-page' : 'vertical-strip');
    
    // Save preference
    AppState.userPreferences.readingMode = mode;
    localStorage.setItem('userPreferences', JSON.stringify(AppState.userPreferences));
}

/**
 * Set width fit mode
 */
function setWidthFit(fit) {
    const readerContent = document.getElementById('reader-content');
    if (!readerContent) return;
    
    // Remove existing classes
    readerContent.classList.remove('fit-width', 'original-size');
    
    // Add new class
    readerContent.classList.add(fit === 'original' ? 'original-size' : 'fit-width');
    
    // Save preference
    AppState.userPreferences.widthFit = fit;
    localStorage.setItem('userPreferences', JSON.stringify(AppState.userPreferences));
}

/**
 * Set auto scroll mode
 */
function setAutoScroll(enabled) {
    const readerContent = document.getElementById('reader-content');
    if (!readerContent) return;
    
    if (enabled) {
        readerContent.classList.add('auto-scroll');
    } else {
        readerContent.classList.remove('auto-scroll');
    }
    
    // Save preference
    AppState.userPreferences.autoScroll = enabled;
    localStorage.setItem('userPreferences', JSON.stringify(AppState.userPreferences));
}

/**
 * Initialize authentication UI
 */
function initializeAuthUI() {
    const authBtn = document.getElementById('auth-btn');
    if (!authBtn) return;
    
    // Check if user is authenticated
    if (window.auth && window.auth.isAuthenticated()) {
        const user = window.auth.getCurrentUser();
        authBtn.textContent = user.username;
        authBtn.innerHTML = `
            <span>${user.username}</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 9l6 6 6-6"></path>
            </svg>
        `;
        
        // Add dropdown functionality
        authBtn.addEventListener('click', showUserDropdown);
    } else {
        authBtn.textContent = 'Login';
        authBtn.addEventListener('click', () => {
            window.location.href = 'auth.html';
        });
    }
}

/**
 * Show user dropdown menu
 */
function showUserDropdown() {
    // Create dropdown menu
    const dropdown = document.createElement('div');
    dropdown.className = 'user-dropdown';
    dropdown.innerHTML = `
        <a href="#" class="dropdown-item">Profile</a>
        <a href="#" class="dropdown-item">Bookmarks</a>
        <a href="#" class="dropdown-item">Reading History</a>
        <hr class="dropdown-divider">
        <a href="#" class="dropdown-item" onclick="logout()">Logout</a>
    `;
    
    // Position dropdown
    const authBtn = document.getElementById('auth-btn');
    const rect = authBtn.getBoundingClientRect();
    dropdown.style.cssText = `
        position: absolute;
        top: ${rect.bottom + 5}px;
        right: ${window.innerWidth - rect.right}px;
        background: white;
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        z-index: 1000;
        min-width: 150px;
    `;
    
    // Add styles for dropdown items
    const style = document.createElement('style');
    style.textContent = `
        .user-dropdown .dropdown-item {
            display: block;
            padding: 0.75rem 1rem;
            color: #333;
            text-decoration: none;
            transition: background-color 0.2s;
        }
        .user-dropdown .dropdown-item:hover {
            background-color: #f8f9fa;
        }
        .user-dropdown .dropdown-divider {
            margin: 0.5rem 0;
            border: none;
            border-top: 1px solid #e1e5e9;
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(dropdown);
    
    // Close dropdown when clicking outside
    const closeDropdown = (e) => {
        if (!dropdown.contains(e.target) && e.target !== authBtn) {
            dropdown.remove();
            style.remove();
            document.removeEventListener('click', closeDropdown);
        }
    };
    
    setTimeout(() => {
        document.addEventListener('click', closeDropdown);
    }, 100);
}

/**
 * Logout function
 */
function logout() {
    if (window.auth) {
        window.auth.logout();
    }
}

// Initialize auth UI when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait for auth.js to load
    setTimeout(initializeAuthUI, 100);
    
    // Initialize chapter discussion if on reader page
    if (document.body.dataset.page === 'reader') {
        setupChapterDiscussionHandlers();
    }
});

/**
 * Show discussion section
 */
function showDiscussionSection() {
    const discussionSection = document.getElementById('discussion-section');
    if (discussionSection) {
        discussionSection.style.display = 'block';
        setupDiscussionHandlers();
    }
}

/**
 * Setup discussion event handlers
 */
function setupDiscussionHandlers() {
    const startDiscussionBtn = document.getElementById('start-discussion-btn');
    const discussionForm = document.getElementById('discussion-form');
    const cancelDiscussionBtn = document.getElementById('cancel-discussion');
    const newDiscussionForm = document.getElementById('new-discussion-form');
    
    if (startDiscussionBtn) {
        startDiscussionBtn.addEventListener('click', () => {
            if (window.auth && window.auth.isAuthenticated()) {
                discussionForm.style.display = 'block';
                startDiscussionBtn.style.display = 'none';
            } else {
                window.location.href = 'auth.html';
            }
        });
    }
    
    if (cancelDiscussionBtn) {
        cancelDiscussionBtn.addEventListener('click', () => {
            discussionForm.style.display = 'none';
            startDiscussionBtn.style.display = 'block';
            newDiscussionForm.reset();
        });
    }
    
    if (newDiscussionForm) {
        newDiscussionForm.addEventListener('submit', handleDiscussionSubmit);
    }
}

/**
 * Handle discussion form submission
 */
async function handleDiscussionSubmit(e) {
    e.preventDefault();
    
    if (!window.auth || !window.auth.isAuthenticated()) {
        showMessage('Please sign in to create discussions', 'error');
        return;
    }
    
    const title = document.getElementById('discussion-title').value.trim();
    const content = document.getElementById('discussion-content').value.trim();
    const hasSpoilers = document.getElementById('spoiler-warning').checked;
    
    if (!title || !content) {
        showMessage('Please fill in all fields', 'error');
        return;
    }
    
    try {
        // For now, just add to the discussions list locally
        addDiscussionToList({
            id: Date.now(),
            title,
            content,
            has_spoilers: hasSpoilers,
            author: {
                username: window.auth.getCurrentUser().username
            },
            created_at: new Date().toISOString(),
            like_count: 0,
            comment_count: 0
        });
        
        // Hide form and show success
        document.getElementById('discussion-form').style.display = 'none';
        document.getElementById('start-discussion-btn').style.display = 'block';
        document.getElementById('new-discussion-form').reset();
        
        showMessage('Discussion posted successfully!', 'success');
        
    } catch (error) {
        console.error('Error posting discussion:', error);
        showMessage('Failed to post discussion. Please try again.', 'error');
    }
}

/**
 * Add discussion to the list
 */
function addDiscussionToList(discussion) {
    const discussionsList = document.getElementById('discussions-list');
    const emptyDiscussions = discussionsList.querySelector('.empty-discussions');
    
    if (emptyDiscussions) {
        emptyDiscussions.remove();
    }
    
    const discussionHtml = createDiscussionItem(discussion);
    discussionsList.insertAdjacentHTML('afterbegin', discussionHtml);
    
    // Update discussion count
    const discussionCount = document.querySelector('.discussion-count');
    if (discussionCount) {
        const currentCount = parseInt(discussionCount.textContent) || 0;
        discussionCount.textContent = `${currentCount + 1} discussions`;
    }
}

/**
 * Create discussion item HTML
 */
function createDiscussionItem(discussion) {
    const timeAgo = formatTimeAgo(discussion.created_at);
    const spoilerWarning = discussion.has_spoilers ? '<span class="spoiler-warning">SPOILERS</span>' : '';
    
    return `
        <div class="discussion-item">
            <div class="discussion-item-header">
                <div>
                    <h4 class="discussion-item-title">${discussion.title}${spoilerWarning}</h4>
                    <div class="discussion-item-meta">
                        <span>${timeAgo}</span>
                    </div>
                </div>
            </div>
            
            <div class="discussion-item-content">
                ${discussion.content}
            </div>
            
            <div class="discussion-item-footer">
                <div class="discussion-item-author">
                    <span>by ${discussion.author.username}</span>
                </div>
                
                <div class="discussion-item-actions">
                    <button class="discussion-action" onclick="likeDiscussion(${discussion.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 9V5a3 3 0 0 0-6 0v4"></path>
                            <rect x="2" y="9" width="20" height="12" rx="2" ry="2"></rect>
                        </svg>
                        Like (${discussion.like_count || 0})
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Like discussion
 */
function likeDiscussion(discussionId) {
    if (!window.auth || !window.auth.isAuthenticated()) {
        showMessage('Please sign in to like discussions', 'error');
        return;
    }
    
    // For now, just show a message
    showMessage('Discussion liked!', 'success');
}

/**
 * Format time ago
 */
function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    
    return date.toLocaleDateString();
}

/**
 * Show message
 */
function showMessage(message, type = 'error') {
    // Create temporary message element
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.textContent = message;
    messageEl.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        ${type === 'success' ? 'background: #10b981;' : 'background: #ef4444;'}
    `;
    
    document.body.appendChild(messageEl);
    
    setTimeout(() => {
        messageEl.remove();
    }, 3000);
}

/**
 * Setup chapter discussion handlers
 */
function setupChapterDiscussionHandlers() {
    const startDiscussionBtn = document.getElementById('start-chapter-discussion-btn');
    const discussionForm = document.getElementById('chapter-discussion-form');
    const cancelDiscussionBtn = document.getElementById('cancel-chapter-discussion');
    const newDiscussionForm = document.getElementById('new-chapter-discussion-form');
    
    if (startDiscussionBtn) {
        startDiscussionBtn.addEventListener('click', () => {
            if (window.auth && window.auth.isAuthenticated()) {
                discussionForm.style.display = 'block';
                startDiscussionBtn.style.display = 'none';
            } else {
                window.location.href = 'auth.html';
            }
        });
    }
    
    if (cancelDiscussionBtn) {
        cancelDiscussionBtn.addEventListener('click', () => {
            discussionForm.style.display = 'none';
            startDiscussionBtn.style.display = 'block';
            newDiscussionForm.reset();
        });
    }
    
    if (newDiscussionForm) {
        newDiscussionForm.addEventListener('submit', handleChapterDiscussionSubmit);
    }
}

/**
 * Handle chapter discussion form submission
 */
async function handleChapterDiscussionSubmit(e) {
    e.preventDefault();
    
    if (!window.auth || !window.auth.isAuthenticated()) {
        showMessage('Please sign in to add comments', 'error');
        return;
    }
    
    const content = document.getElementById('chapter-discussion-content').value.trim();
    const hasSpoilers = document.getElementById('chapter-spoiler-warning').checked;
    
    if (!content) {
        showMessage('Please enter a comment', 'error');
        return;
    }
    
    try {
        // For now, just add to the discussions list locally
        addChapterDiscussionToList({
            id: Date.now(),
            content,
            has_spoilers: hasSpoilers,
            author: {
                username: window.auth.getCurrentUser().username
            },
            created_at: new Date().toISOString(),
            like_count: 0
        });
        
        // Hide form and show success
        document.getElementById('chapter-discussion-form').style.display = 'none';
        document.getElementById('start-chapter-discussion-btn').style.display = 'block';
        document.getElementById('new-chapter-discussion-form').reset();
        
        showMessage('Comment posted successfully!', 'success');
        
    } catch (error) {
        console.error('Error posting comment:', error);
        showMessage('Failed to post comment. Please try again.', 'error');
    }
}

/**
 * Add chapter discussion to the list
 */
function addChapterDiscussionToList(comment) {
    const discussionsList = document.getElementById('chapter-discussions-list');
    const emptyDiscussions = discussionsList.querySelector('.empty-discussions');
    
    if (emptyDiscussions) {
        emptyDiscussions.remove();
    }
    
    const commentHtml = createChapterCommentItem(comment);
    discussionsList.insertAdjacentHTML('afterbegin', commentHtml);
    
    // Update comment count
    const discussionCount = document.querySelector('#chapter-discussion-section .discussion-count');
    if (discussionCount) {
        const currentCount = parseInt(discussionCount.textContent) || 0;
        discussionCount.textContent = `${currentCount + 1} comments`;
    }
}

/**
 * Create chapter comment item HTML
 */
function createChapterCommentItem(comment) {
    const timeAgo = formatTimeAgo(comment.created_at);
    const spoilerWarning = comment.has_spoilers ? '<span class="spoiler-warning">SPOILERS</span>' : '';
    
    return `
        <div class="discussion-item">
            <div class="discussion-item-header">
                <div>
                    <h4 class="discussion-item-title">Chapter Comment ${spoilerWarning}</h4>
                    <div class="discussion-item-meta">
                        <span>${timeAgo}</span>
                    </div>
                </div>
            </div>
            
            <div class="discussion-item-content">
                ${comment.content}
            </div>
            
            <div class="discussion-item-footer">
                <div class="discussion-item-author">
                    <span>by ${comment.author.username}</span>
                </div>
                
                <div class="discussion-item-actions">
                    <button class="discussion-action" onclick="likeChapterComment(${comment.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 9V5a3 3 0 0 0-6 0v4"></path>
                            <rect x="2" y="9" width="20" height="12" rx="2" ry="2"></rect>
                        </svg>
                        Like (${comment.like_count || 0})
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Like chapter comment
 */
function likeChapterComment(commentId) {
    if (!window.auth || !window.auth.isAuthenticated()) {
        showMessage('Please sign in to like comments', 'error');
        return;
    }
    
    // For now, just show a message
    showMessage('Comment liked!', 'success');
}