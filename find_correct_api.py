#!/usr/bin/env python3
"""
Find the correct API endpoint for getting all chapters
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def find_correct_api():
    """Find the correct API endpoint for getting all chapters."""
    
    # Try different API endpoints that might work
    api_endpoints = [
        "https://comick.live/api/comics/00-the-beginning-after-the-end-1/chapters?lang=en",
        "https://comick.live/api/comics/00-the-beginning-after-the-end-1/chapters?lang=en&limit=1000",
        "https://comick.live/api/comics/00-the-beginning-after-the-end-1/chapters?limit=1000",
        "https://comick.live/api/comics/00-the-beginning-after-the-end-1/chapters?page=1&limit=1000",
        "https://comick.live/api/v1/comics/00-the-beginning-after-the-end-1/chapters?lang=en",
        "https://comick.live/api/v1/comics/00-the-beginning-after-the-end-1/chapters?lang=en&limit=1000",
        "https://comick.live/api/v1/comics/00-the-beginning-after-the-end-1/chapters?limit=1000",
        "https://comick.live/api/v1/comics/00-the-beginning-after-the-end-1/chapters?page=1&limit=1000",
        "https://comick.live/api/comics/00-the-beginning-after-the-end-1/chapters?lang=en&page=1&limit=1000",
        "https://comick.live/api/comics/00-the-beginning-after-the-end-1/chapters?lang=en&page=1&limit=1000&order=asc",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://comick.live/comic/00-the-beginning-after-the-end-1'
    }
    
    for api_url in api_endpoints:
        print(f"\n🔍 Testing: {api_url}")
        
        try:
            response = requests.get(api_url, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success! Data type: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())}")
                        
                        if 'chapters' in data:
                            chapters = data['chapters']
                            print(f"   📚 Found {len(chapters)} chapters")
                            
                            # Show first few chapters
                            for i, chapter in enumerate(chapters[:5]):
                                if isinstance(chapter, dict):
                                    print(f"      Chapter {i+1}: {chapter.get('chap', 'N/A')} - {chapter.get('hid', 'N/A')} - {chapter.get('lang', 'N/A')} - {chapter.get('group_name', 'N/A')}")
                            
                            # Look for English chapters
                            en_chapters = [ch for ch in chapters if ch.get('lang') == 'en']
                            if en_chapters:
                                print(f"   🇺🇸 Found {len(en_chapters)} English chapters!")
                                for i, chapter in enumerate(en_chapters[:5]):
                                    print(f"      EN Chapter {i+1}: {chapter.get('chap', 'N/A')} - {chapter.get('hid', 'N/A')} - {chapter.get('group_name', 'N/A')}")
                            
                            return data  # Return the successful data
                            
                        elif 'data' in data:
                            data_content = data['data']
                            print(f"   Data content type: {type(data_content)}")
                            if isinstance(data_content, list):
                                print(f"   📚 Found {len(data_content)} items in data")
                                for i, item in enumerate(data_content[:5]):
                                    if isinstance(item, dict):
                                        print(f"      Item {i+1}: {item.get('chap', 'N/A')} - {item.get('hid', 'N/A')} - {item.get('lang', 'N/A')}")
                            
                    elif isinstance(data, list):
                        print(f"   📚 Found {len(data)} items")
                        for i, item in enumerate(data[:5]):
                            if isinstance(item, dict):
                                print(f"      Item {i+1}: {item.get('chap', 'N/A')} - {item.get('hid', 'N/A')} - {item.get('lang', 'N/A')}")
                        
                except json.JSONDecodeError:
                    print(f"   📄 Response is not JSON: {response.text[:200]}...")
                    
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ No working API endpoint found")
    return None

if __name__ == "__main__":
    find_correct_api()

