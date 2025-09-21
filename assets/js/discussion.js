/**
 * ManhwaVerse Discussion System
 * =============================
 * 
 * Handles community discussions, comments, and interactions
 * 
 * Author: ManhwaVerse Development Team
 * Date: 2025
 * Version: 1.0
 */

// --- Configuration ---
const DISCUSSION_API_BASE = '/api/discussions';
const COMMENTS_API_BASE = '/api/comments';

// --- State Management ---
let currentDiscussions = [];
let currentTab = 'recent';
let currentDiscussion = null;

// --- Initialize Discussion System ---
document.addEventListener('DOMContentLoaded', function() {
    initializeDiscussion();
    setupEventListeners();
    loadDiscussions();
    addFakeComments(); // Add fake comments for testing
});

/**
 * Initialize discussion system
 */
function initializeDiscussion() {
    console.log('Initializing discussion system...');
    
    // Check authentication
    if (window.auth && window.auth.isAuthenticated()) {
        showCreateDiscussionButton();
    } else {
        hideCreateDiscussionButton();
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
    
    // Create discussion form
    const createForm = document.getElementById('new-discussion-form');
    if (createForm) {
        createForm.addEventListener('submit', handleCreateDiscussion);
    }
    
    const cancelBtn = document.getElementById('cancel-discussion');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', hideCreateDiscussionForm);
    }
    
    // Modal controls
    const modal = document.getElementById('discussion-modal');
    const modalClose = document.getElementById('modal-close');
    
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }
    
    // Auth button
    const authBtn = document.getElementById('auth-btn');
    if (authBtn) {
        authBtn.addEventListener('click', () => {
            if (window.auth && window.auth.isAuthenticated()) {
                showUserMenu();
            } else {
                window.location.href = 'auth.html';
            }
        });
    }
}

/**
 * Switch discussion tab
 */
function switchTab(tab) {
    // Update active tab
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        }
    });
    
    currentTab = tab;
    loadDiscussions();
}

/**
 * Load discussions based on current tab
 */
async function loadDiscussions() {
    const discussionList = document.getElementById('discussion-list');
    if (!discussionList) return;
    
    // Show loading state
    showLoadingState(discussionList, 'Loading discussions...');
    
    try {
        let apiUrl = `${DISCUSSION_API_BASE}/${currentTab}`;
        
        // Add search parameter if searching
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value.trim()) {
            apiUrl += `?search=${encodeURIComponent(searchInput.value.trim())}`;
        }
        
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (response.ok) {
            currentDiscussions = data.discussions || [];
            renderDiscussions(currentDiscussions);
        } else {
            showErrorState(discussionList, data.error || 'Failed to load discussions');
        }
        
    } catch (error) {
        console.error('Error loading discussions:', error);
        showErrorState(discussionList, 'Network error. Please try again.');
    }
}

/**
 * Render discussions list
 */
function renderDiscussions(discussions) {
    const discussionList = document.getElementById('discussion-list');
    if (!discussionList) return;
    
    if (discussions.length === 0) {
        discussionList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💬</div>
                <h3>No discussions found</h3>
                <p>Be the first to start a discussion about your favorite manhwa!</p>
                ${window.auth && window.auth.isAuthenticated() ? 
                    '<button class="btn btn-primary" onclick="showCreateDiscussionForm()">Start Discussion</button>' : 
                    '<a href="auth.html" class="btn btn-primary">Sign In to Discuss</a>'
                }
            </div>
        `;
        return;
    }
    
    const discussionsHtml = discussions.map(discussion => createDiscussionItem(discussion)).join('');
    discussionList.innerHTML = discussionsHtml;
    
    // Add click listeners to discussion items
    const discussionItems = discussionList.querySelectorAll('.discussion-item');
    discussionItems.forEach(item => {
        item.addEventListener('click', () => {
            const discussionId = item.dataset.discussionId;
            openDiscussion(discussionId);
        });
    });
}

/**
 * Create discussion item HTML
 */
function createDiscussionItem(discussion) {
    const timeAgo = formatTimeAgo(discussion.created_at);
    const spoilerWarning = discussion.has_spoilers ? '<span class="spoiler-warning">SPOILERS</span>' : '';
    
    return `
        <div class="discussion-item" data-discussion-id="${discussion.id}">
            <div class="discussion-header-info">
                <div>
                    <h3 class="discussion-title">${discussion.title}${spoilerWarning}</h3>
                    <div class="discussion-meta">
                        <span class="discussion-type">${discussion.type}</span>
                        ${discussion.series ? `<span class="discussion-series">${discussion.series}</span>` : ''}
                        <span>${timeAgo}</span>
                    </div>
                </div>
            </div>
            
            <div class="discussion-content-preview">
                ${discussion.content}
            </div>
            
            <div class="discussion-footer">
                <div class="discussion-stats">
                    <div class="stat">
                        <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <span>${discussion.comment_count || 0}</span>
                    </div>
                    <div class="stat">
                        <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 9V5a3 3 0 0 0-6 0v4"></path>
                            <rect x="2" y="9" width="20" height="12" rx="2" ry="2"></rect>
                        </svg>
                        <span>${discussion.like_count || 0}</span>
                    </div>
                </div>
                
                <div class="discussion-author">
                    <div class="author-avatar">
                        ${discussion.author.username.charAt(0).toUpperCase()}
                    </div>
                    <div class="author-info">
                        <div class="author-name">${discussion.author.username}</div>
                        <div class="author-time">${timeAgo}</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Open discussion modal
 */
async function openDiscussion(discussionId) {
    const modal = document.getElementById('discussion-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    if (!modal || !modalTitle || !modalBody) return;
    
    // Show loading state
    modalBody.innerHTML = '<div class="loading-container"><div class="loading-spinner"></div><p>Loading discussion...</p></div>';
    modal.classList.add('show');
    
    try {
        const response = await fetch(`${DISCUSSION_API_BASE}/${discussionId}`);
        const data = await response.json();
        
        if (response.ok) {
            currentDiscussion = data.discussion;
            modalTitle.textContent = data.discussion.title;
            modalBody.innerHTML = renderDiscussionModal(data.discussion);
            
            // Setup comment form
            setupCommentForm(discussionId);
            
        } else {
            modalBody.innerHTML = `<div class="error-state"><p>Error loading discussion: ${data.error}</p></div>`;
        }
        
    } catch (error) {
        console.error('Error loading discussion:', error);
        modalBody.innerHTML = '<div class="error-state"><p>Network error. Please try again.</p></div>';
    }
}

/**
 * Render discussion modal content
 */
function renderDiscussionModal(discussion) {
    const timeAgo = formatTimeAgo(discussion.created_at);
    const spoilerWarning = discussion.has_spoilers ? '<span class="spoiler-warning">SPOILERS</span>' : '';
    
    return `
        <div class="discussion-detail">
            <div class="discussion-header">
                <div class="discussion-meta">
                    <span class="discussion-type">${discussion.type}</span>
                    ${discussion.series ? `<span class="discussion-series">${discussion.series}</span>` : ''}
                    <span>${timeAgo}</span>
                    ${spoilerWarning}
                </div>
            </div>
            
            <div class="discussion-content">
                ${discussion.content}
            </div>
            
            <div class="discussion-actions">
                <button class="btn btn-outline" onclick="likeDiscussion(${discussion.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 9V5a3 3 0 0 0-6 0v4"></path>
                        <rect x="2" y="9" width="20" height="12" rx="2" ry="2"></rect>
                    </svg>
                    Like (${discussion.like_count || 0})
                </button>
            </div>
            
            <div class="comments-section">
                <div class="comments-header">
                    <h3 class="comments-count">Comments (${discussion.comment_count || 0})</h3>
                </div>
                
                ${window.auth && window.auth.isAuthenticated() ? `
                    <div class="comment-form">
                        <textarea id="comment-text" placeholder="Write a comment..."></textarea>
                        <div class="comment-form-actions">
                            <button class="btn btn-primary" onclick="submitComment(${discussion.id})">Post Comment</button>
                        </div>
                    </div>
                ` : `
                    <div class="comment-form">
                        <p>Please <a href="auth.html">sign in</a> to comment.</p>
                    </div>
                `}
                
                <div class="comments-list" id="comments-list">
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <p>Loading comments...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup comment form
 */
function setupCommentForm(discussionId) {
    // Load comments
    loadComments(discussionId);
}

/**
 * Load comments for discussion
 */
async function loadComments(discussionId) {
    const commentsList = document.getElementById('comments-list');
    if (!commentsList) return;
    
    try {
        const response = await fetch(`${COMMENTS_API_BASE}/${discussionId}`);
        const data = await response.json();
        
        if (response.ok) {
            renderComments(data.comments || []);
        } else {
            commentsList.innerHTML = '<div class="error-state"><p>Error loading comments</p></div>';
        }
        
    } catch (error) {
        console.error('Error loading comments:', error);
        commentsList.innerHTML = '<div class="error-state"><p>Network error loading comments</p></div>';
    }
}

/**
 * Render comments
 */
function renderComments(comments) {
    const commentsList = document.getElementById('comments-list');
    if (!commentsList) return;
    
    if (comments.length === 0) {
        commentsList.innerHTML = '<div class="empty-state"><p>No comments yet. Be the first to comment!</p></div>';
        return;
    }
    
    const commentsHtml = comments.map(comment => createCommentItem(comment)).join('');
    commentsList.innerHTML = commentsHtml;
}

/**
 * Create comment item HTML
 */
function createCommentItem(comment) {
    const timeAgo = formatTimeAgo(comment.created_at);
    
    return `
        <div class="comment-item">
            <div class="comment-header">
                <div class="comment-author">
                    <div class="author-avatar">
                        ${comment.author.username.charAt(0).toUpperCase()}
                    </div>
                    <div class="author-info">
                        <div class="author-name">${comment.author.username}</div>
                        <div class="author-time">${timeAgo}</div>
                    </div>
                </div>
            </div>
            
            <div class="comment-content">
                ${comment.content}
            </div>
            
            <div class="comment-actions">
                <button class="comment-action" onclick="likeComment(${comment.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 9V5a3 3 0 0 0-6 0v4"></path>
                        <rect x="2" y="9" width="20" height="12" rx="2" ry="2"></rect>
                    </svg>
                    Like (${comment.like_count || 0})
                </button>
            </div>
        </div>
    `;
}

/**
 * Handle create discussion form submission
 */
async function handleCreateDiscussion(e) {
    e.preventDefault();
    
    if (!window.auth || !window.auth.isAuthenticated()) {
        showMessage('Please sign in to create a discussion', 'error');
        return;
    }
    
    const formData = new FormData(e.target);
    const discussionData = {
        title: formData.get('discussion-title') || document.getElementById('discussion-title').value,
        type: formData.get('discussion-type') || document.getElementById('discussion-type').value,
        series: formData.get('discussion-series') || document.getElementById('discussion-series').value,
        content: formData.get('discussion-content') || document.getElementById('discussion-content').value,
        has_spoilers: formData.get('spoiler-warning') || document.getElementById('spoiler-warning').checked
    };
    
    // Validate required fields
    if (!discussionData.title || !discussionData.type || !discussionData.content) {
        showMessage('Please fill in all required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(DISCUSSION_API_BASE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.auth.getAuthToken()}`
            },
            body: JSON.stringify(discussionData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('Discussion created successfully!', 'success');
            hideCreateDiscussionForm();
            loadDiscussions(); // Refresh discussions
        } else {
            showMessage(data.error || 'Failed to create discussion', 'error');
        }
        
    } catch (error) {
        console.error('Error creating discussion:', error);
        showMessage('Network error. Please try again.', 'error');
    }
}

/**
 * Submit comment
 */
async function submitComment(discussionId) {
    if (!window.auth || !window.auth.isAuthenticated()) {
        showMessage('Please sign in to comment', 'error');
        return;
    }
    
    const commentText = document.getElementById('comment-text');
    if (!commentText || !commentText.value.trim()) {
        showMessage('Please enter a comment', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${COMMENTS_API_BASE}/${discussionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.auth.getAuthToken()}`
            },
            body: JSON.stringify({
                content: commentText.value.trim()
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            commentText.value = '';
            loadComments(discussionId); // Refresh comments
            showMessage('Comment posted!', 'success');
        } else {
            showMessage(data.error || 'Failed to post comment', 'error');
        }
        
    } catch (error) {
        console.error('Error posting comment:', error);
        showMessage('Network error. Please try again.', 'error');
    }
}

/**
 * Like discussion
 */
async function likeDiscussion(discussionId) {
    if (!window.auth || !window.auth.isAuthenticated()) {
        showMessage('Please sign in to like discussions', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${DISCUSSION_API_BASE}/${discussionId}/like`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.auth.getAuthToken()}`
            }
        });
        
        if (response.ok) {
            // Refresh discussion data
            loadDiscussions();
        }
        
    } catch (error) {
        console.error('Error liking discussion:', error);
    }
}

/**
 * Like comment
 */
async function likeComment(commentId) {
    if (!window.auth || !window.auth.isAuthenticated()) {
        showMessage('Please sign in to like comments', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${COMMENTS_API_BASE}/${commentId}/like`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.auth.getAuthToken()}`
            }
        });
        
        if (response.ok) {
            // Refresh comments
            if (currentDiscussion) {
                loadComments(currentDiscussion.id);
            }
        }
        
    } catch (error) {
        console.error('Error liking comment:', error);
    }
}

/**
 * Show create discussion form
 */
function showCreateDiscussionForm() {
    const createForm = document.getElementById('create-discussion');
    if (createForm) {
        createForm.style.display = 'block';
        createForm.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Hide create discussion form
 */
function hideCreateDiscussionForm() {
    const createForm = document.getElementById('create-discussion');
    if (createForm) {
        createForm.style.display = 'none';
        // Reset form
        const form = document.getElementById('new-discussion-form');
        if (form) form.reset();
    }
}

/**
 * Show create discussion button
 */
function showCreateDiscussionButton() {
    // This would show a "Create Discussion" button in the UI
    console.log('User is authenticated, showing create discussion options');
}

/**
 * Hide create discussion button
 */
function hideCreateDiscussionButton() {
    // This would hide create discussion options for non-authenticated users
    console.log('User not authenticated, hiding create discussion options');
}

/**
 * Close modal
 */
function closeModal() {
    const modal = document.getElementById('discussion-modal');
    if (modal) {
        modal.classList.remove('show');
        currentDiscussion = null;
    }
}

/**
 * Handle search
 */
function handleSearch(e) {
    const query = e.target.value.trim();
    if (query.length >= 2 || query.length === 0) {
        loadDiscussions();
    }
}

/**
 * Show user menu
 */
function showUserMenu() {
    // This would show a dropdown menu with user options
    console.log('Showing user menu');
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
 * Show loading state
 */
function showLoadingState(container, message) {
    container.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Show error state
 */
function showErrorState(container, message) {
    container.innerHTML = `
        <div class="error-state">
            <div class="error-icon">⚠️</div>
            <p>${message}</p>
        </div>
    `;
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
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Add fake comments for testing purposes
 */
function addFakeComments() {
    // Check if we're on a chapter discussion page (reader.html)
    const chapterDiscussionsList = document.getElementById('chapter-discussions-list');
    const discussionCount = document.querySelector('.discussion-count');
    
    if (!chapterDiscussionsList) return;
    
    // Create fake comments data
    const fakeComments = [
        {
            id: 1,
            content: "This chapter was absolutely amazing! The art is getting better and better 🔥",
            author: { username: "testuser0" },
            created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
            like_count: 5
        },
        {
            id: 2,
            content: "CommentTest - I can't wait for the next chapter! The plot twist was unexpected",
            author: { username: "testuser1" },
            created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
            like_count: 3
        },
        {
            id: 3,
            content: "The character development in this series is incredible. Each chapter brings something new!",
            author: { username: "testuser0" },
            created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago
            like_count: 8
        },
        {
            id: 4,
            content: "CommentTest - Does anyone else think the MC is getting too overpowered? Still love it though 😅",
            author: { username: "testuser1" },
            created_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(), // 8 hours ago
            like_count: 2
        },
        {
            id: 5,
            content: "The fight scenes in this chapter were epic! The animation quality is top tier",
            author: { username: "testuser0" },
            created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(), // 12 hours ago
            like_count: 7
        },
        {
            id: 6,
            content: "CommentTest - I've been following this series since chapter 1 and it just keeps getting better!",
            author: { username: "testuser1" },
            created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
            like_count: 12
        }
    ];
    
    // Clear the empty state and add fake comments
    chapterDiscussionsList.innerHTML = '';
    
    // Create comment items
    fakeComments.forEach(comment => {
        const commentItem = createChapterCommentItem(comment);
        chapterDiscussionsList.appendChild(commentItem);
    });
    
    // Update the comment count
    if (discussionCount) {
        discussionCount.textContent = `${fakeComments.length} comments`;
    }
    
    console.log('Added 6 fake comments for testing');
}

/**
 * Create chapter comment item HTML
 */
function createChapterCommentItem(comment) {
    const timeAgo = formatTimeAgo(comment.created_at);
    
    const commentDiv = document.createElement('div');
    commentDiv.className = 'discussion-item';
    commentDiv.innerHTML = `
        <div class="discussion-header">
            <div class="discussion-author">
                <div class="author-avatar">
                    ${comment.author.username.charAt(0).toUpperCase()}
                </div>
                <div class="author-info">
                    <div class="author-name">${comment.author.username}</div>
                    <div class="author-time">${timeAgo}</div>
                </div>
            </div>
        </div>
        
        <div class="discussion-content">
            <p>${comment.content}</p>
        </div>
        
        <div class="discussion-actions">
            <button class="action-btn" onclick="likeChapterComment(${comment.id})">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 9V5a3 3 0 0 0-6 0v4"></path>
                    <rect x="2" y="9" width="20" height="12" rx="2" ry="2"></rect>
                </svg>
                Like (${comment.like_count || 0})
            </button>
        </div>
    `;
    
    return commentDiv;
}

/**
 * Format time ago
 */
function formatTimeAgo(dateString) {
    const now = new Date();
    const date = new Date(dateString);
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
}

/**
 * Like chapter comment (placeholder)
 */
function likeChapterComment(commentId) {
    console.log(`Liked comment ${commentId}`);
    // Add like functionality here
}

// Export functions for global access
window.discussion = {
    showCreateDiscussionForm,
    hideCreateDiscussionForm,
    submitComment,
    likeDiscussion,
    likeComment,
    closeModal
};

// Make likeChapterComment globally available
window.likeChapterComment = likeChapterComment;
