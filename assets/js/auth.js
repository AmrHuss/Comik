/**
 * ManhwaVerse Authentication System
 * =================================
 * 
 * Handles user signup, login, and session management
 * 
 * Author: ManhwaVerse Development Team
 * Date: 2025
 * Version: 1.0
 */

// --- Configuration ---
const AUTH_API_BASE = '/api/auth';
const STORAGE_KEYS = {
    USER: 'manhwaverse_user',
    TOKEN: 'manhwaverse_token',
    REMEMBER: 'manhwaverse_remember'
};

// --- State Management ---
let currentUser = null;
let authToken = null;

// --- Initialize Authentication ---
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    setupEventListeners();
    checkExistingSession();
});

/**
 * Initialize authentication system
 */
function initializeAuth() {
    console.log('Initializing authentication system...');
    
    // Load existing session if available
    const savedUser = localStorage.getItem(STORAGE_KEYS.USER);
    const savedToken = localStorage.getItem(STORAGE_KEYS.TOKEN);
    
    if (savedUser && savedToken) {
        try {
            currentUser = JSON.parse(savedUser);
            authToken = savedToken;
            console.log('Existing session found for user:', currentUser.username);
        } catch (error) {
            console.error('Error loading saved session:', error);
            clearSession();
        }
    }
}

/**
 * Setup event listeners for auth forms
 */
function setupEventListeners() {
    // Form switching
    const switchToSignup = document.getElementById('switch-to-signup');
    const switchToSignin = document.getElementById('switch-to-signin');
    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');
    
    if (switchToSignup) {
        switchToSignup.addEventListener('click', (e) => {
            e.preventDefault();
            switchForm('signup');
        });
    }
    
    if (switchToSignin) {
        switchToSignin.addEventListener('click', (e) => {
            e.preventDefault();
            switchForm('signin');
        });
    }
    
    // Form submissions
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleSignup);
    }
    
    // Social login buttons
    setupSocialLogin();
    
    // Real-time validation
    setupFormValidation();
}

/**
 * Switch between signin and signup forms
 */
function switchForm(formType) {
    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');
    
    if (formType === 'signup') {
        signinForm.classList.remove('active');
        signupForm.classList.add('active');
    } else {
        signupForm.classList.remove('active');
        signinForm.classList.add('active');
    }
    
    // Clear form errors
    clearFormErrors();
}

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const remember = document.getElementById('remember-me').checked;
    
    // Clear previous errors
    clearFormErrors();
    
    // Validate inputs
    if (!validateEmail(email)) {
        showFieldError('login-email', 'Please enter a valid email address');
        return;
    }
    
    if (!password) {
        showFieldError('login-password', 'Password is required');
        return;
    }
    
    // Show loading state
    const loginBtn = document.getElementById('login-btn');
    setButtonLoading(loginBtn, true);
    
    try {
        const response = await fetch(`${AUTH_API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                password,
                remember
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Login successful
            currentUser = data.user;
            authToken = data.token;
            
            // Save session
            saveSession(remember);
            
            // Show success message
            showMessage('Login successful! Redirecting...', 'success');
            
            // Redirect to homepage after short delay
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
            
        } else {
            // Login failed
            showMessage(data.error || 'Login failed. Please try again.', 'error');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showMessage('Network error. Please check your connection and try again.', 'error');
    } finally {
        setButtonLoading(loginBtn, false);
    }
}

/**
 * Handle signup form submission
 */
async function handleSignup(e) {
    e.preventDefault();
    
    const username = document.getElementById('signup-username').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;
    const agreeTerms = document.getElementById('agree-terms').checked;
    
    // Clear previous errors
    clearFormErrors();
    
    // Validate inputs
    let hasErrors = false;
    
    if (!username || username.length < 3) {
        showFieldError('signup-username', 'Username must be at least 3 characters long');
        hasErrors = true;
    }
    
    if (!validateEmail(email)) {
        showFieldError('signup-email', 'Please enter a valid email address');
        hasErrors = true;
    }
    
    if (!password || password.length < 6) {
        showFieldError('signup-password', 'Password must be at least 6 characters long');
        hasErrors = true;
    }
    
    if (password !== confirmPassword) {
        showFieldError('signup-confirm-password', 'Passwords do not match');
        hasErrors = true;
    }
    
    if (!agreeTerms) {
        showMessage('Please agree to the Terms of Service and Privacy Policy', 'error');
        hasErrors = true;
    }
    
    if (hasErrors) return;
    
    // Show loading state
    const signupBtn = document.getElementById('signup-btn');
    setButtonLoading(signupBtn, true);
    
    try {
        const response = await fetch(`${AUTH_API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Signup successful
            currentUser = data.user;
            authToken = data.token;
            
            // Save session
            saveSession(true);
            
            // Show success message
            showMessage('Account created successfully! Redirecting...', 'success');
            
            // Redirect to homepage after short delay
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
            
        } else {
            // Signup failed
            if (data.field) {
                showFieldError(data.field, data.error);
            } else {
                showMessage(data.error || 'Signup failed. Please try again.', 'error');
            }
        }
        
    } catch (error) {
        console.error('Signup error:', error);
        showMessage('Network error. Please check your connection and try again.', 'error');
    } finally {
        setButtonLoading(signupBtn, false);
    }
}

/**
 * Setup social login functionality
 */
function setupSocialLogin() {
    // Google login
    const googleLogin = document.getElementById('google-login');
    const googleSignup = document.getElementById('google-signup');
    
    if (googleLogin) {
        googleLogin.addEventListener('click', () => initiateSocialLogin('google'));
    }
    
    if (googleSignup) {
        googleSignup.addEventListener('click', () => initiateSocialLogin('google'));
    }
    
    // Discord login
    const discordLogin = document.getElementById('discord-login');
    const discordSignup = document.getElementById('discord-signup');
    
    if (discordLogin) {
        discordLogin.addEventListener('click', () => initiateSocialLogin('discord'));
    }
    
    if (discordSignup) {
        discordSignup.addEventListener('click', () => initiateSocialLogin('discord'));
    }
}

/**
 * Initiate social login
 */
async function initiateSocialLogin(provider) {
    try {
        // For now, we'll simulate social login
        // In a real implementation, you'd redirect to OAuth provider
        showMessage(`${provider} login coming soon!`, 'error');
        
        // Example of how real social login would work:
        // window.location.href = `${AUTH_API_BASE}/social/${provider}`;
        
    } catch (error) {
        console.error(`${provider} login error:`, error);
        showMessage(`${provider} login failed. Please try again.`, 'error');
    }
}

/**
 * Setup real-time form validation
 */
function setupFormValidation() {
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', () => {
            const email = input.value.trim();
            if (email && !validateEmail(email)) {
                showFieldError(input.id, 'Please enter a valid email address');
            } else {
                clearFieldError(input.id);
            }
        });
    });
    
    // Password confirmation
    const confirmPasswordInput = document.getElementById('signup-confirm-password');
    const passwordInput = document.getElementById('signup-password');
    
    if (confirmPasswordInput && passwordInput) {
        confirmPasswordInput.addEventListener('blur', () => {
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            
            if (confirmPassword && password !== confirmPassword) {
                showFieldError('signup-confirm-password', 'Passwords do not match');
            } else {
                clearFieldError('signup-confirm-password');
            }
        });
    }
}

/**
 * Validate email format
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Show field error
 */
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}-error`);
    
    if (field) {
        field.classList.add('error');
    }
    
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
}

/**
 * Clear field error
 */
function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}-error`);
    
    if (field) {
        field.classList.remove('error');
    }
    
    if (errorElement) {
        errorElement.classList.remove('show');
    }
}

/**
 * Clear all form errors
 */
function clearFormErrors() {
    const errorElements = document.querySelectorAll('.form-error');
    const errorFields = document.querySelectorAll('.form-input.error');
    
    errorElements.forEach(element => {
        element.classList.remove('show');
    });
    
    errorFields.forEach(field => {
        field.classList.remove('error');
    });
}

/**
 * Show message to user
 */
function showMessage(message, type = 'error') {
    // Remove existing messages
    const existingMessage = document.querySelector('.auth-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create new message
    const messageElement = document.createElement('div');
    messageElement.className = `auth-message ${type}`;
    messageElement.textContent = message;
    
    // Insert at top of form
    const form = document.querySelector('.auth-form.active .form');
    if (form) {
        form.insertBefore(messageElement, form.firstChild);
    }
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.remove();
        }
    }, 5000);
}

/**
 * Set button loading state
 */
function setButtonLoading(button, loading) {
    const btnText = button.querySelector('.btn-text');
    const btnSpinner = button.querySelector('.btn-spinner');
    
    if (loading) {
        button.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnSpinner) btnSpinner.style.display = 'block';
    } else {
        button.disabled = false;
        if (btnText) btnText.style.display = 'block';
        if (btnSpinner) btnSpinner.style.display = 'none';
    }
}

/**
 * Save user session
 */
function saveSession(remember = false) {
    if (currentUser && authToken) {
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(currentUser));
        localStorage.setItem(STORAGE_KEYS.TOKEN, authToken);
        localStorage.setItem(STORAGE_KEYS.REMEMBER, remember.toString());
        
        console.log('Session saved for user:', currentUser.username);
    }
}

/**
 * Clear user session
 */
function clearSession() {
    localStorage.removeItem(STORAGE_KEYS.USER);
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REMEMBER);
    
    currentUser = null;
    authToken = null;
    
    console.log('Session cleared');
}

/**
 * Check existing session
 */
function checkExistingSession() {
    if (currentUser && authToken) {
        // Verify token is still valid
        verifyToken().catch(() => {
            clearSession();
        });
    }
}

/**
 * Verify authentication token
 */
async function verifyToken() {
    try {
        const response = await fetch(`${AUTH_API_BASE}/verify`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Token verification failed');
        }
        
        return true;
    } catch (error) {
        console.error('Token verification error:', error);
        return false;
    }
}

/**
 * Logout user
 */
function logout() {
    clearSession();
    window.location.href = 'auth.html';
}

/**
 * Get current user
 */
function getCurrentUser() {
    return currentUser;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return currentUser !== null && authToken !== null;
}

/**
 * Get auth token
 */
function getAuthToken() {
    return authToken;
}

// Export functions for use in other scripts
window.auth = {
    getCurrentUser,
    isAuthenticated,
    getAuthToken,
    logout,
    clearSession
};
