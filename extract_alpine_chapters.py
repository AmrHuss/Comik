#!/usr/bin/env python3
"""
Extract chapter data from Alpine.js and API calls
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def extract_alpine_chapter_data(html_content):
    """Extract chapter data from Alpine.js calls."""
    try:
        print("🔍 Extracting Alpine.js chapter data...")
        
        # Look for ChapterList.loadDataChapter calls
        chapter_list_pattern = r"ChapterList\.loadDataChapter\('([^']+)',\s*JSON\.parse\('([^']+)'\)"
        matches = re.findall(chapter_list_pattern, html_content)
        
        for comic_slug, json_data in matches:
            print(f"Found ChapterList.loadDataChapter for: {comic_slug}")
            print(f"JSON data: {json_data[:200]}...")
            
            try:
                # Decode the JSON data
                decoded_data = json.loads(json_data)
                print(f"Decoded data: {decoded_data}")
                return decoded_data
            except Exception as e:
                print(f"Failed to decode JSON: {e}")
                continue
        
        # Look for other Alpine.js patterns
        alpine_patterns = [
            r'x-data="([^"]*)"',
            r'x-init="([^"]*)"',
            r'@click="([^"]*)"'
        ]
        
        for pattern in alpine_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if 'chapter' in match.lower() or 'Chapter' in match:
                    print(f"Found Alpine.js pattern: {match[:100]}...")
        
        return None
        
    except Exception as e:
        print(f"❌ Error extracting Alpine.js data: {e}")
        return None

def try_api_calls(comic_slug):
    """Try to make API calls to get chapter data."""
    try:
        print(f"🔍 Trying API calls for comic: {comic_slug}")
        
        # Try different API endpoints
        api_endpoints = [
            f"https://comick.live/api/comic/{comic_slug}/chapters",
            f"https://comick.live/api/comic/{comic_slug}",
            f"https://comick.live/api/chapter/{comic_slug}",
            f"https://comick.live/api/v1/comic/{comic_slug}/chapters",
            f"https://comick.live/api/v1/comic/{comic_slug}",
            f"https://comick.live/api/v2/comic/{comic_slug}/chapters",
            f"https://comick.live/api/v2/comic/{comic_slug}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://comick.live/comic/{comic_slug}',
            'Origin': 'https://comick.live'
        }
        
        for endpoint in api_endpoints:
            try:
                print(f"Trying API: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=10)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✅ Success! Data: {json.dumps(data, indent=2)[:500]}...")
                        return data
                    except:
                        print(f"Response is not JSON: {response.text[:200]}...")
                else:
                    print(f"Failed: {response.status_code}")
                    
            except Exception as e:
                print(f"Error calling {endpoint}: {e}")
                continue
        
        return None
        
    except Exception as e:
        print(f"❌ Error making API calls: {e}")
        return None

def extract_from_script_tags(html_content):
    """Extract all possible chapter data from script tags."""
    try:
        print("🔍 Extracting from all script tags...")
        
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        all_chapters = []
        
        for i, script in enumerate(scripts):
            # Look for arrays of chapter data
            array_patterns = [
                r'\[(.*?)\]',
                r'chapters\s*:\s*\[(.*?)\]',
                r'chapterList\s*:\s*\[(.*?)\]',
                r'firstChapters\s*:\s*\[(.*?)\]'
            ]
            
            for pattern in array_patterns:
                matches = re.findall(pattern, script, re.DOTALL)
                for match in matches:
                    if 'hid' in match and 'chapter' in match.lower():
                        print(f"Found chapter array in script {i}: {match[:100]}...")
                        
                        # Try to extract individual chapter objects
                        objects = re.findall(r'\{[^}]*"hid"[^}]*\}', match)
                        for obj_str in objects:
                            try:
                                obj = json.loads(obj_str)
                                if 'hid' in obj:
                                    all_chapters.append(obj)
                                    print(f"  Chapter: {obj}")
                            except:
                                continue
        
        return all_chapters
        
    except Exception as e:
        print(f"❌ Error extracting from script tags: {e}")
        return []

def test_comprehensive_chapter_extraction():
    """Test comprehensive chapter extraction."""
    test_url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    comic_slug = "00-the-beginning-after-the-end-1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        print(f"🔍 Testing comprehensive chapter extraction from: {test_url}")
        response = requests.get(test_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Method 1: Extract Alpine.js data
        print("\n📱 Method 1: Alpine.js data")
        alpine_data = extract_alpine_chapter_data(response.text)
        
        # Method 2: Try API calls
        print("\n🌐 Method 2: API calls")
        api_data = try_api_calls(comic_slug)
        
        # Method 3: Extract from script tags
        print("\n📜 Method 3: Script tags")
        script_chapters = extract_from_script_tags(response.text)
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"Alpine.js data: {alpine_data}")
        print(f"API data: {api_data}")
        print(f"Script chapters: {len(script_chapters)}")
        
        if script_chapters:
            print(f"Sample script chapters: {script_chapters[:3]}")
        
        return {
            'alpine_data': alpine_data,
            'api_data': api_data,
            'script_chapters': script_chapters
        }
        
    except Exception as e:
        print(f"❌ Error testing extraction: {e}")
        return {}

if __name__ == "__main__":
    test_comprehensive_chapter_extraction()

