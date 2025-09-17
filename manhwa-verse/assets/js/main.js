/**
 * ManhwaVerse Frontend Logic (v12 - Definitive Version)
 * ======================================================
 * This is the complete, final script that powers the entire front-end.
 *
 * Features:
 * - Dedicated logic for all pages (home, popular, genres, etc.).
 * - Fully functional live search with a results dropdown.
 * - Complete handling for the manga detail page.
 * - Complete handling for the manga list/results page.
 * - Robust API fetching with clear loading and error states.
 */
const API_BASE_URL = '/api';

// --- Universal Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
    // Attach live search handler to the search input on all pages
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleLiveSearch, 300));
    }
    
    // Attach search form handler to redirect to a results page on submit
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }

    // Hide search results dropdown when clicking anywhere else on the page
    document.addEventListener('click', (e) => {
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer && !searchContainer.contains(e.target)) {
            hideSearchResults();
        }
    });

    // Run the specific logic for the current page
    initializePage();
});

// --- Page Initializer ---
function initializePage() {
    const page = document.body.dataset.page;
    console.log(`Initializing page: ${page}`);

    switch (page) {
        case 'home':
            loadHomepageContent();
            break;
        case 'popular':
            loadAndDisplayManga(`${API_BASE_URL}/api/popular`, '.manhwa-grid', 'Popular Manhwa');
            break;
        case 'new-releases':
            loadAndDisplayManga(`${API_BASE_URL}/api/popular`, '.manhwa-grid', 'New Releases');
            break;
        case 'mangalist':
            handleMangaListPage();
            break;
        case 'detail':
            handleDetailPage();
            break;
    }
}

// --- Specific Page Handlers ---

async function loadHomepageContent() {
    const trendingGrid = document.querySelector('.trending-grid');
    const updatesGrid = document.querySelector('.updates-grid');
    if (!trendingGrid || !updatesGrid) return;
    
    trendingGrid.innerHTML = '<p class="loading-message">Loading Trending...</p>';
    updatesGrid.innerHTML = '<p class="loading-message">Loading Updates...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/popular`);
        const result = await response.json();
        if (!result.success) throw new Error(result.error);

        // Populate Trending: a slice of the full list
        displayMangaGrid(trendingGrid, result.data.slice(0, 6));

        // Populate Latest Updates: the full list
        displayMangaGrid(updatesGrid, result.data);
    } catch (error) {
        trendingGrid.innerHTML = '<p class="error-message">Could not load trending manga.</p>';
        updatesGrid.innerHTML = '<p class="error-message">Could not load latest updates.</p>';
    }
}

async function handleMangaListPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const genre = urlParams.get('genre');
    const searchQuery = urlParams.get('search');

    if (genre) {
        const genreTitle = genre.charAt(0).toUpperCase() + genre.slice(1).replace('-', ' ');
        loadAndDisplayManga(`${API_BASE_URL}/api/genre?name=${genre}`, '#manga-results-grid', `${genreTitle} Manhwa`);
    } else if (searchQuery) {
        loadAndDisplayManga(`${API_BASE_URL}/api/search?query=${searchQuery}`, '#manga-results-grid', `Search Results for "${searchQuery}"`);
    }
}

async function handleDetailPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const detailUrl = urlParams.get('url');
    const container = document.getElementById('detail-container');

    if (!detailUrl) {
        container.innerHTML = `<p class="error-message">No manga URL provided.</p>`;
        return;
    }

    container.innerHTML = '<p class="loading-message">Loading details...</p>';
    try {
        const response = await fetch(`${API_BASE_URL}/api/manga-details?url=${encodeURIComponent(detailUrl)}`);
        const result = await response.json();
        if (result.success) {
            displayMangaDetails(result.data);
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        container.innerHTML = `<p class="error-message">Could not load details. ${error.message}</p>`;
    }
}

// --- Search Functionality ---
function debounce(func, delay) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

function handleSearchSubmit(event) {
    event.preventDefault();
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    if (query) {
        // Redirect to the dedicated results page
        window.location.href = `mangalist.html?search=${encodeURIComponent(query)}`;
    }
}

async function handleLiveSearch(event) {
    const query = event.target.value.trim();
    const resultsContainer = document.getElementById('search-results-container') || createSearchResultsContainer();

    if (query.length < 2) {
        resultsContainer.style.display = 'none';
        return;
    }
    resultsContainer.innerHTML = '<p class="loading-message" style="padding: 1rem;">Searching...</p>';
    resultsContainer.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE_URL}/api/search?query=${encodeURIComponent(query)}`);
        const result = await response.json();

        resultsContainer.innerHTML = '';
        if (result.success && result.data.length > 0) {
            result.data.slice(0, 7).forEach(manga => { // Limit to 7 results
                const item = document.createElement('a');
                // Link to the detail page, not the reader
                item.href = `detail.html?url=${encodeURIComponent(manga.detail_url)}`;
                item.className = 'search-result-item';
                item.innerHTML = `<img src="${manga.cover_url}" alt=""><span>${manga.title}</span>`;
                resultsContainer.appendChild(item);
            });
        } else {
            resultsContainer.innerHTML = '<p class="error-message" style="padding: 1rem;">No results found.</p>';
        }
    } catch (error) {
        resultsContainer.innerHTML = '<p class="error-message" style="padding: 1rem;">Search failed.</p>';
    }
}

function createSearchResultsContainer() {
    const searchContainer = document.querySelector('.search-container');
    if (!searchContainer) return null;
    let container = document.getElementById('search-results-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'search-results-container';
        searchContainer.appendChild(container);
    }
    return container;
}

function hideSearchResults() {
    const resultsContainer = document.getElementById('search-results-container');
    if (resultsContainer) resultsContainer.style.display = 'none';
}

// --- Dynamic Element Creation & Display ---

function displayMangaDetails(data) {
    const container = document.getElementById('detail-container');
    document.title = `${data.title} - ManhwaVerse`; // Update page title

    const genresHtml = data.genres.map(genre => `<span class="genre-tag">${genre}</span>`).join('');
    const chaptersHtml = data.chapters.map(chapter => `
        <a href="reader.html?url=${encodeURIComponent(chapter.url)}" class="chapter-item">
            <span class="chapter-title">${chapter.title}</span>
            <span class="chapter-date">${chapter.date}</span>
        </a>
    `).join('');

    container.innerHTML = `
        <div class="detail-grid">
            <div class="detail-cover"><img src="${data.cover_image}" alt="${data.title}"></div>
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

function createMangaCard(manga) {
    const cardLink = document.createElement('a');
    cardLink.href = `detail.html?url=${encodeURIComponent(manga.detail_url)}`;
    cardLink.className = 'manhwa-card';
    cardLink.innerHTML = `
        <div class="card-image">
            <img src="${manga.cover_url}" alt="${manga.title}" loading="lazy" onerror="this.style.display='none'">
            <div class="card-overlay"><button class="read-btn">View Details</button></div>
        </div>
        <div class="card-content">
            <h3 class="card-title">${manga.title}</h3>
            <p class="card-chapter">${manga.latest_chapter}</p>
        </div>
    `;
    return cardLink;
}

function displayMangaGrid(container, mangaList) {
    if (!container) return;
    if (!mangaList || mangaList.length === 0) {
        container.innerHTML = '<p class="error-message">No manga found.</p>';
        return;
    }
    container.innerHTML = '';
    mangaList.forEach(manga => {
        container.appendChild(createMangaCard(manga));
    });
}

async function loadAndDisplayManga(apiUrl, gridSelector, pageTitleText) {
    const grid = document.querySelector(gridSelector);
    const pageTitle = document.getElementById('page-title');

    if (pageTitle && pageTitleText) pageTitle.textContent = pageTitleText;
    if (!grid) return;
    
    grid.innerHTML = '<p class="loading-message">Loading manga...</p>';
    try {
        const response = await fetch(apiUrl);
        const result = await response.json();

        if (result.success && result.data) {
            const dataToShow = result.data.latest_updates || result.data; // Handle homepage structure
            displayMangaGrid(grid, dataToShow);
        } else {
            throw new Error(result.error || "No manga found.");
        }
    } catch (error) {
        grid.innerHTML = `<p class="error-message">${error.message}</p>`;
    }
}

// Global function for reader page, as it's called from inline script
window.loadChapterImages = async function(chapterUrl) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chapter?url=${encodeURIComponent(chapterUrl)}`);
        const result = await response.json();
        if (result.success) {
            return result.data;
        }
        throw new Error(result.error || 'Failed to load chapter images');
    } catch (error) {
        console.error("Chapter load error:", error);
        throw error; // Re-throw to be caught by the calling function
    }
};