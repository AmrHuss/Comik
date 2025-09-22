#!/usr/bin/env python3
"""
Find API endpoints for getting all chapters
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def find_chapter_api():
    """Find API endpoints for getting all chapters."""
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
    
    print("🔍 Looking for API endpoints...")
    
    # Look for API endpoints in the HTML
    api_patterns = [
        r'api/comics/[^"\']+/chapters',
        r'/api/[^"\']*chapter[^"\']*',
        r'fetch\(["\']([^"\']*api[^"\']*)["\']',
        r'axios\.get\(["\']([^"\']*api[^"\']*)["\']',
        r'\.get\(["\']([^"\']*api[^"\']*)["\']',
    ]
    
    for pattern in api_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"✅ Found API pattern: {pattern}")
            for match in matches[:5]:  # Show first 5 matches
                print(f"   API: {match}")
    
    # Look for JavaScript that loads chapters
    print("\n🔍 Looking for chapter loading JavaScript...")
    
    js_patterns = [
        r'getChapterByLanguage[^}]*}',
        r'loadChapters[^}]*}',
        r'fetchChapters[^}]*}',
        r'chapters\s*=\s*[^;]+',
    ]
    
    for pattern in js_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL)
        if matches:
            print(f"✅ Found JS pattern: {pattern}")
            for match in matches[:3]:  # Show first 3 matches
                print(f"   JS: {match[:200]}...")
    
    # Try to find the comic slug and test API endpoints
    print("\n🔍 Testing potential API endpoints...")
    
    # Extract comic slug
    slug_match = re.search(r'comic/([^/]+)', url)
    if slug_match:
        comic_slug = slug_match.group(1)
        print(f"Comic slug: {comic_slug}")
        
        # Test common API endpoints
        api_endpoints = [
            f"https://comick.live/api/comics/{comic_slug}/chapters",
            f"https://comick.live/api/comics/{comic_slug}",
            f"https://comick.live/api/v1/comics/{comic_slug}/chapters",
            f"https://comick.live/api/v1/comics/{comic_slug}",
        ]
        
        for api_url in api_endpoints:
            try:
                print(f"Testing: {api_url}")
                api_response = requests.get(api_url, headers=headers, timeout=10)
                print(f"   Status: {api_response.status_code}")
                
                if api_response.status_code == 200:
                    try:
                        data = api_response.json()
                        print(f"   ✅ Success! Data keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                        
                        # Look for chapters in the response
                        if isinstance(data, dict) and 'chapters' in data:
                            chapters = data['chapters']
                            print(f"   📚 Found {len(chapters)} chapters")
                            for i, chapter in enumerate(chapters[:5]):  # Show first 5
                                if isinstance(chapter, dict):
                                    print(f"      Chapter {i+1}: {chapter.get('chap', 'N/A')} - {chapter.get('hid', 'N/A')} - {chapter.get('lang', 'N/A')}")
                        elif isinstance(data, list):
                            print(f"   📚 Found {len(data)} items")
                            for i, item in enumerate(data[:5]):  # Show first 5
                                if isinstance(item, dict):
                                    print(f"      Item {i+1}: {item.get('chap', 'N/A')} - {item.get('hid', 'N/A')} - {item.get('lang', 'N/A')}")
                    except:
                        print(f"   📄 Response is not JSON: {api_response.text[:200]}...")
                else:
                    print(f"   ❌ Failed: {api_response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    find_chapter_api()