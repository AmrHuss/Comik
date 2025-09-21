#!/usr/bin/env python3
"""
HTML Template Updater for JavaScript Protection
===============================================

This script updates HTML files to use protected JavaScript files.

Author: ManhwaVerse Development Team
"""

import os
import re
from pathlib import Path

def update_html_files(protection_mode='loader'):
    """Update HTML files to use protected JavaScript."""
    
    html_files = [
        'index.html',
        'detail.html',
        'reader.html',
        'genres.html',
        'popular.html',
        'new-releases.html',
        'mangalist.html'
    ]
    
    for html_file in html_files:
        if not os.path.exists(html_file):
            print(f"Warning: {html_file} not found")
            continue
            
        print(f"Updating {html_file}...")
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if protection_mode == 'loader':
            # Replace script tags with loader
            old_scripts = [
                r'<script src="assets/js/main\.js"></script>',
                r'<script src="assets/js/components\.js"></script>'
            ]
            
            for script_pattern in old_scripts:
                content = re.sub(script_pattern, '', content)
            
            # Add loader script before closing body tag
            loader_script = '<script src="assets/js/protected/loader.js"></script>'
            content = content.replace('</body>', f'    {loader_script}\n</body>')
            
        elif protection_mode == 'obfuscated':
            # Replace with obfuscated versions
            content = re.sub(
                r'src="assets/js/main\.js"',
                'src="assets/js/obfuscated/main.js"',
                content
            )
            content = re.sub(
                r'src="assets/js/components\.js"',
                'src="assets/js/obfuscated/components.js"',
                content
            )
        
        # Write updated content
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {html_file}")

def main():
    print("HTML Template Updater for JavaScript Protection")
    print("=" * 50)
    
    print("\nChoose protection mode:")
    print("1. Loader mode (dynamic loading with integrity checks)")
    print("2. Obfuscated mode (simple obfuscation)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        update_html_files('loader')
        print("\nHTML files updated for loader mode!")
        print("Make sure to run protect_js.py first to generate protected files.")
    elif choice == '2':
        update_html_files('obfuscated')
        print("\nHTML files updated for obfuscated mode!")
        print("Make sure to run obfuscate_js.py first to generate obfuscated files.")
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
