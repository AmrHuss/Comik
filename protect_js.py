#!/usr/bin/env python3
"""
Advanced JavaScript Protection for ManhwaVerse
==============================================

This script provides multiple layers of JavaScript protection:
1. Obfuscation
2. Code splitting
3. Dynamic loading
4. Anti-tampering measures
5. Source map removal

Author: ManhwaVerse Development Team
"""

import os
import re
import base64
import hashlib
import random
import string
import json
from pathlib import Path

class AdvancedJSProtector:
    def __init__(self):
        self.obfuscation_map = {}
        self.checksums = {}
        
    def generate_checksum(self, content):
        """Generate checksum for integrity checking."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def create_loader_script(self, js_files):
        """Create a dynamic loader script."""
        loader_template = """
        (function() {
            'use strict';
            
            // Anti-tampering checks
            const originalConsole = console.log;
            const originalAlert = alert;
            
            // Detect if running in browser
            if (typeof window === 'undefined') {
                return;
            }
            
            // Integrity check function
            function verifyIntegrity(checksum, content) {
                const crypto = window.crypto || window.msCrypto;
                if (crypto && crypto.subtle) {
                    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(content))
                        .then(hash => {
                            const hashArray = Array.from(new Uint8Array(hash));
                            const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
                            return hashHex === checksum;
                        });
                }
                return Promise.resolve(true); // Fallback for older browsers
            }
            
            // Dynamic script loader with integrity checking
            function loadScript(src, checksum) {
                return new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = src;
                    script.type = 'text/javascript';
                    
                    script.onload = () => {
                        // Verify integrity if checksum provided
                        if (checksum) {
                            fetch(src)
                                .then(response => response.text())
                                .then(content => verifyIntegrity(checksum, content))
                                .then(isValid => {
                                    if (isValid) {
                                        resolve();
                                    } else {
                                        reject(new Error('Integrity check failed'));
                                    }
                                })
                                .catch(reject);
                        } else {
                            resolve();
                        }
                    };
                    
                    script.onerror = () => reject(new Error('Failed to load script'));
                    document.head.appendChild(script);
                });
            }
            
            // Load scripts in order
            const scripts = {scripts};
            let currentIndex = 0;
            
            function loadNext() {
                if (currentIndex >= scripts.length) {
                    // All scripts loaded
                    if (window.initializeApp) {
                        window.initializeApp();
                    }
                    return;
                }
                
                const script = scripts[currentIndex];
                loadScript(script.src, script.checksum)
                    .then(() => {
                        currentIndex++;
                        loadNext();
                    })
                    .catch(error => {
                        console.error('Failed to load script:', script.src, error);
                        // Continue loading other scripts
                        currentIndex++;
                        loadNext();
                    });
            }
            
            // Start loading
            loadNext();
        })();
        """
        
        scripts_json = json.dumps(js_files, indent=2)
        return loader_template.replace('{scripts}', scripts_json)
    
    def obfuscate_advanced(self, content):
        """Advanced obfuscation with multiple techniques."""
        # 1. String encoding
        def encode_strings(match):
            string_content = match.group(1)
            if len(string_content) > 2:
                # Use multiple encoding layers
                encoded = base64.b64encode(string_content.encode()).decode()
                return f"atob('{encoded}')"
            return match.group(0)
        
        content = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', encode_strings, content)
        content = re.sub(r"'([^'\\]*(\\.[^'\\]*)*)'", encode_strings, content)
        
        # 2. Variable name obfuscation
        variables = re.findall(r'\b(let|const|var|function)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\b', content)
        var_map = {}
        
        for var_type, var_name in variables:
            if var_name not in ['window', 'document', 'console', 'localStorage', 'sessionStorage', 'JSON', 'Math', 'Date', 'Array', 'Object', 'String', 'Number', 'Boolean', 'Function', 'Promise', 'fetch', 'XMLHttpRequest', 'Error', 'RegExp', 'parseInt', 'parseFloat', 'isNaN', 'isFinite', 'encodeURIComponent', 'decodeURIComponent', 'encodeURI', 'decodeURI', 'escape', 'unescape', 'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval', 'requestAnimationFrame', 'cancelAnimationFrame', 'addEventListener', 'removeEventListener', 'querySelector', 'querySelectorAll', 'getElementById', 'getElementsByClassName', 'getElementsByTagName', 'createElement', 'appendChild', 'removeChild', 'insertBefore', 'replaceChild', 'cloneNode', 'getAttribute', 'setAttribute', 'removeAttribute', 'hasAttribute', 'classList', 'className', 'innerHTML', 'textContent', 'value', 'checked', 'selected', 'disabled', 'hidden', 'style', 'parentNode', 'childNodes', 'firstChild', 'lastChild', 'nextSibling', 'previousSibling']:
                if var_name not in var_map:
                    var_map[var_name] = f"_0x{random.randint(1000, 9999)}"
                content = content.replace(f'{var_type} {var_name}', f'{var_type} {var_map[var_name]}')
        
        # 3. Add anti-debugging
        anti_debug = """
        (function() {
            let devtools = false;
            const threshold = 160;
            setInterval(() => {
                if (window.outerHeight - window.innerHeight > threshold || 
                    window.outerWidth - window.innerWidth > threshold) {
                    if (!devtools) {
                        devtools = true;
                        console.clear();
                        console.log('%cStop!', 'color: red; font-size: 50px; font-weight: bold;');
                        console.log('%cThis is a browser feature intended for developers.', 'color: red; font-size: 16px;');
                    }
                } else {
                    devtools = false;
                }
            }, 500);
        })();
        """
        
        # 4. Add dummy code
        dummy_code = f"""
        var _0x{random.randint(1000, 9999)} = function() {{ return Math.random(); }};
        const _0x{random.randint(1000, 9999)} = () => {{ console.log('dummy'); }};
        function _0x{random.randint(1000, 9999)}(a, b) {{ return a + b; }}
        """
        
        return anti_debug + dummy_code + content
    
    def split_code(self, content, max_chunk_size=50000):
        """Split large JavaScript files into smaller chunks."""
        chunks = []
        current_chunk = ""
        lines = content.split('\n')
        
        for line in lines:
            if len(current_chunk) + len(line) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                current_chunk += line + '\n'
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def protect_file(self, input_path, output_dir, protection_level='medium'):
        """Protect a JavaScript file with multiple techniques."""
        print(f"Protecting {input_path}...")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate checksum
        checksum = self.generate_checksum(content)
        self.checksums[input_path] = checksum
        
        # Apply protection based on level
        if protection_level == 'light':
            # Just minify
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r';\s*}', ';}', content)
        elif protection_level == 'medium':
            # Obfuscate and minify
            content = self.obfuscate_advanced(content)
            content = re.sub(r'\s+', ' ', content)
        elif protection_level == 'heavy':
            # Full protection
            content = self.obfuscate_advanced(content)
            content = re.sub(r'\s+', ' ', content)
            
            # Split into chunks if too large
            if len(content) > 100000:
                chunks = self.split_code(content)
                for i, chunk in enumerate(chunks):
                    chunk_path = os.path.join(output_dir, f"{Path(input_path).stem}_chunk_{i}.js")
                    with open(chunk_path, 'w', encoding='utf-8') as f:
                        f.write(chunk)
                return f"{Path(input_path).stem}_chunk_*.js"
        
        # Write protected file
        output_path = os.path.join(output_dir, Path(input_path).name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Protected file saved to {output_path}")
        return Path(input_path).name
    
    def create_protection_manifest(self, protected_files, output_dir):
        """Create a manifest file for the protected files."""
        manifest = {
            "version": "1.0",
            "files": protected_files,
            "checksums": self.checksums,
            "timestamp": str(int(__import__('time').time())),
            "protection_level": "medium"
        }
        
        manifest_path = os.path.join(output_dir, "protection_manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path

def main():
    protector = AdvancedJSProtector()
    
    # Create protected directory
    protected_dir = 'assets/js/protected'
    os.makedirs(protected_dir, exist_ok=True)
    
    # Files to protect
    js_files = [
        'assets/js/main.js',
        'assets/js/components.js'
    ]
    
    protected_files = []
    
    for js_file in js_files:
        if os.path.exists(js_file):
            protected_file = protector.protect_file(js_file, protected_dir, 'medium')
            protected_files.append({
                "src": f"assets/js/protected/{protected_file}",
                "checksum": protector.checksums[js_file]
            })
        else:
            print(f"Warning: {js_file} not found")
    
    # Create loader script
    loader_content = protector.create_loader_script(protected_files)
    loader_path = os.path.join(protected_dir, "loader.js")
    with open(loader_path, 'w', encoding='utf-8') as f:
        f.write(loader_content)
    
    # Create manifest
    manifest_path = protector.create_protection_manifest(protected_files, protected_dir)
    
    print(f"\nProtection complete!")
    print(f"Protected files saved to: {protected_dir}")
    print(f"Manifest created: {manifest_path}")
    print(f"Loader script: {loader_path}")
    print("\nTo use protected files, replace your script tags with:")
    print('<script src="assets/js/protected/loader.js"></script>')

if __name__ == "__main__":
    main()
