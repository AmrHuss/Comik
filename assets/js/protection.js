


(function() {
    'use strict';
    
    // Disable right-click context menu
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Disable common developer tools shortcuts
    document.addEventListener('keydown', function(e) {
        // F12 key
        if (e.keyCode === 123) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+Shift+I (Windows/Linux) or Cmd+Opt+I (Mac)
        if ((e.ctrlKey && e.shiftKey && e.keyCode === 73) || 
            (e.metaKey && e.altKey && e.keyCode === 73)) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+Shift+J (Windows/Linux) or Cmd+Opt+J (Mac) - Console
        if ((e.ctrlKey && e.shiftKey && e.keyCode === 74) || 
            (e.metaKey && e.altKey && e.keyCode === 74)) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+U (Windows/Linux) or Cmd+Opt+U (Mac) - View Source
        if ((e.ctrlKey && e.keyCode === 85) || 
            (e.metaKey && e.altKey && e.keyCode === 85)) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+S (Windows/Linux) or Cmd+S (Mac) - Save Page
        if ((e.ctrlKey && e.keyCode === 83) || 
            (e.metaKey && e.keyCode === 83)) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+A (Windows/Linux) or Cmd+A (Mac) - Select All
        if ((e.ctrlKey && e.keyCode === 65) || 
            (e.metaKey && e.keyCode === 65)) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+C (Windows/Linux) or Cmd+C (Mac) - Copy
        if ((e.ctrlKey && e.keyCode === 67) || 
            (e.metaKey && e.keyCode === 67)) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+V (Windows/Linux) or Cmd+V (Mac) - Paste
        if ((e.ctrlKey && e.keyCode === 86) || 
            (e.metaKey && e.keyCode === 86)) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+X (Windows/Linux) or Cmd+X (Mac) - Cut
        if ((e.ctrlKey && e.keyCode === 88) || 
            (e.metaKey && e.keyCode === 88)) {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+P (Windows/Linux) or Cmd+P (Mac) - Print
        if ((e.ctrlKey && e.keyCode === 80) || 
            (e.metaKey && e.keyCode === 80)) {
            e.preventDefault();
            return false;
        }
    });
    
 
    // Disable drag and drop
    document.addEventListener('dragstart', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Basic developer tools detection (more aggressive)
    let devtools = {
        open: false,
        orientation: null
    };
    
    const threshold = 160;
    
    setInterval(function() {
        if (window.outerHeight - window.innerHeight > threshold || 
            window.outerWidth - window.innerWidth > threshold) {
            if (!devtools.open) {
                devtools.open = true;
                console.clear();
                console.log('%c⚠️ Developer Tools Detected', 'color: red; font-size: 20px; font-weight: bold;');
                console.log('%cThis website is protected. Please close developer tools to continue.', 'color: red; font-size: 14px;');
                
                // Optional: Redirect or show warning
                // window.location.href = 'about:blank';
            }
        } else {
            devtools.open = false;
        }
    }, 500);
    
    if (typeof console !== 'undefined') {
        
        console.log = function() {};
        console.warn = function() {};
        console.error = function() {};
        console.info = function() {};
        console.debug = function() {};
        console.trace = function() {};
        console.table = function() {};
        console.group = function() {};
        console.groupEnd = function() {};
        console.time = function() {};
        console.timeEnd = function() {};
    }
    
    // Disable common debugging methods
    if (typeof window.debugger !== 'undefined') {
        window.debugger = function() {};
    }
    
    // Disable eval and Function constructor (optional - can break legitimate functionality)
    if (typeof eval !== 'undefined') {
        window.eval = function() {
            throw new Error('eval is disabled');
        };
    }
    
    if (typeof Function !== 'undefined') {
        window.Function = function() {
            throw new Error('Function constructor is disabled');
        };
    }
    
    // Add a warning message to the console
    console.log('%c🚫 STOP!', 'color: red; font-size: 50px; font-weight: bold;');
    console.log('%cThis is a browser feature intended for developers. If someone told you to copy-paste something here to enable a ManhwaVerse feature or "hack" someone\'s account, it is a scam and will give them access to your account.', 'color: red; font-size: 16px;');
    
    // Optional: Clear console periodically
    setInterval(function() {
        console.clear();
    }, 3000);
    
})();
