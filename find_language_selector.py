#!/usr/bin/env python3
"""
Find language selector with multiple chapter hash IDs
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def find_language_selector():
    """Find language selector with multiple chapter hash IDs."""
    url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print("🔍 Fetching comic page...")
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch page: {response.status_code}")
        return
    
    html_content = response.text
    
    print("🔍 Looking for language selector...")
    
    # Look for the specific language selector HTML you mentioned
    language_selector_patterns = [
        r'<select[^>]*class="[^"]*rounded[^"]*"[^>]*@change="getChapterByLanguage[^>]*>.*?</select>',
        r'<option[^>]*value="[^"]*"[^>]*data-hid="([^"]*)"[^>]*>([^<]*)</option>',
        r'data-hid="([^"]*)"',
        r'getChapterByLanguage',
    ]
    
    for pattern in language_selector_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if matches:
            print(f"✅ Found language selector pattern: {pattern}")
            for match in matches[:10]:  # Show first 10 matches
                print(f"   Match: {match}")
    
    # Look for Alpine.js data
    print("\n🔍 Looking for Alpine.js data...")
    
    alpine_patterns = [
        r'x-data="[^"]*"',
        r'x-for="[^"]*"',
        r'dupGroupChapters',
        r'chapter\s*:\s*\{[^}]*\}',
    ]
    
    for pattern in alpine_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if matches:
            print(f"✅ Found Alpine pattern: {pattern}")
            for match in matches[:5]:  # Show first 5 matches
                print(f"   Match: {match}")
    
    # Look for specific data-hid attributes
    print("\n🔍 Looking for data-hid attributes...")
    
    hid_matches = re.findall(r'data-hid="([^"]*)"', html_content)
    if hid_matches:
        print(f"✅ Found {len(hid_matches)} data-hid attributes:")
        for i, hid in enumerate(hid_matches[:10]):  # Show first 10
            print(f"   {i+1}: {hid}")
    
    # Look for the specific structure you mentioned
    print("\n🔍 Looking for specific structure...")
    
    specific_pattern = r'<option[^>]*value="([^"]*)"[^>]*x-text="([^"]*)"[^>]*:data-hid="([^"]*)"[^>]*:selected="[^"]*" value="([^"]*)" data-hid="([^"]*)"[^>]*>([^<]*)</option>'
    specific_matches = re.findall(specific_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    if specific_matches:
        print(f"✅ Found {len(specific_matches)} specific option matches:")
        for i, match in enumerate(specific_matches):
            print(f"   {i+1}: {match}")
    else:
        print("❌ No specific option matches found")
        
        # Try simpler pattern
        simple_pattern = r'<option[^>]*data-hid="([^"]*)"[^>]*>([^<]*)</option>'
        simple_matches = re.findall(simple_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        if simple_matches:
            print(f"✅ Found {len(simple_matches)} simple option matches:")
            for i, match in enumerate(simple_matches):
                print(f"   {i+1}: {match}")

if __name__ == "__main__":
    find_language_selector()

