#!/usr/bin/env python3
"""Find the correct API endpoint for chapters."""

import sys
import os
import re
import json
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from comick_live_scraper import make_request, get_headers

def find_chapter_api():
    """Find the chapter API endpoint."""
    url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    print(f"Finding chapter API for: {url}")
    
    # Make request
    response = make_request(url)
    if not response:
        print("❌ Failed to fetch page")
        return
    
    # Look for API endpoints in script tags
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, response.text, re.DOTALL)
    
    print(f"Found {len(scripts)} script tags")
    
    for i, script in enumerate(scripts):
        if 'api' in script.lower() and 'chapter' in script.lower():
            print(f"\n🔍 Script {i} contains 'api' and 'chapter':")
            print(f"Length: {len(script)} characters")
            print(f"First 500 chars: {script[:500]}")
            
            # Look for API URLs
            api_urls = re.findall(r'https?://[^\s"\']*api[^\s"\']*', script)
            if api_urls:
                print(f"Found API URLs: {api_urls}")
            
            # Look for chapter-related patterns
            chapter_patterns = re.findall(r'[^\s"\']*chapter[^\s"\']*', script)
            if chapter_patterns:
                print(f"Found chapter patterns: {chapter_patterns[:10]}")  # First 10
    
    # Try common Comick API patterns
    comic_id = "00-the-beginning-after-the-end-1"
    possible_endpoints = [
        f"https://comick.live/api/v1/comic/{comic_id}/chapters",
        f"https://api.comick.live/v1/comic/{comic_id}/chapters",
        f"https://comick.live/api/comic/{comic_id}/chapters",
        f"https://comick.live/api/v1/comic/{comic_id}",
        f"https://api.comick.live/v1/comic/{comic_id}",
    ]
    
    print(f"\n🔍 Testing possible API endpoints:")
    for endpoint in possible_endpoints:
        try:
            print(f"Testing: {endpoint}")
            headers = get_headers()
            headers['Referer'] = url
            response = requests.get(endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ SUCCESS: {endpoint}")
                try:
                    data = response.json()
                    print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    if 'chapters' in str(data).lower():
                        print(f"Contains chapter data!")
                        print(f"Sample: {str(data)[:500]}")
                except:
                    print(f"Response: {response.text[:200]}")
            else:
                print(f"❌ Status {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_chapter_api()
