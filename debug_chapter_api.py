#!/usr/bin/env python3
"""
Debug script to find and test the Comick chapter API endpoint.
"""

import requests
import re
import json
from bs4 import BeautifulSoups

def make_request(url):
    """Make a request with proper headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def find_api_endpoints(html_content):
    """Find potential API endpoints in the HTML."""
    print("🔍 Looking for API endpoints...")
    
    # Look for various API patterns
    patterns = [
        r'loadDataChapter\([^,]+,\s*JSON\.parse\([^)]+\)',
        r'ChapterList\.loadDataChapter\([^,]+,\s*JSON\.parse\([^)]+\)',
        r'/api/[^"\s]*chapter[^"\s]*',
        r'https?://[^"\s]*api[^"\s]*chapter[^"\s]*',
        r'https?://api\.comick\.fun[^"\s]*',
        r'https?://[^"\s]*comick[^"\s]*api[^"\s]*'
    ]
    
    found_endpoints = []
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"Pattern '{pattern}' found {len(matches)} matches:")
            for match in matches[:3]:  # Show first 3 matches
                print(f"  {match}")
                found_endpoints.append(match)
    
    return found_endpoints

def extract_comic_info(html_content):
    """Extract comic information from the HTML."""
    print("\n📋 Extracting comic information...")
    
    # Look for the loadDataChapter function call
    pattern = r'loadDataChapter\([\'"]([^\'"]+)[\'"],\s*JSON\.parse\([^)]+\)'
    match = re.search(pattern, html_content)
    
    if match:
        comic_slug = match.group(1)
        print(f"Comic slug: {comic_slug}")
        return comic_slug
    else:
        print("Could not find comic slug in loadDataChapter call")
        return None

def test_api_endpoints(comic_slug):
    """Test various API endpoints for chapter data."""
    print(f"\n🧪 Testing API endpoints for comic: {comic_slug}")
    
    # Try different API endpoint patterns
    endpoints_to_try = [
        f"https://api.comick.fun/comic/{comic_slug}/chapters",
        f"https://api.comick.fun/comic/{comic_slug}",
        f"https://api.comick.fun/comic/{comic_slug}/chapter-list",
        f"https://api.comick.fun/comic/{comic_slug}/chapters?lang=en",
        f"https://api.comick.fun/comic/{comic_slug}/chapters?lang=all",
        f"https://api.comick.fun/comic/{comic_slug}/chapters?limit=1000",
        f"https://api.comick.fun/comic/{comic_slug}/chapters?limit=1000&lang=en"
    ]
    
    for endpoint in endpoints_to_try:
        print(f"\nTesting: {endpoint}")
        try:
            response = make_request(endpoint)
            if response and response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Status: {response.status_code}")
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Look for chapters in the response
                if isinstance(data, dict):
                    if 'chapters' in data:
                        chapters = data['chapters']
                        print(f"Found {len(chapters)} chapters")
                        if chapters and isinstance(chapters[0], dict):
                            print(f"First chapter keys: {list(chapters[0].keys())}")
                            print(f"Sample chapter: {chapters[0]}")
                        return data
                    elif 'data' in data and isinstance(data['data'], list):
                        chapters = data['data']
                        print(f"Found {len(chapters)} chapters in 'data' field")
                        if chapters and isinstance(chapters[0], dict):
                            print(f"First chapter keys: {list(chapters[0].keys())}")
                            print(f"Sample chapter: {chapters[0]}")
                        return data
                    else:
                        print("No chapters found in response")
                        print(f"Available keys: {list(data.keys())}")
                else:
                    print(f"Response is not a dict: {type(data)}")
            else:
                print(f"❌ Failed: Status {response.status_code if response else 'No response'}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return None

def main():
    """Main debug function."""
    url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    print(f"Debugging chapter API for: {url}")
    
    # Get the HTML content
    response = make_request(url)
    if not response:
        print("❌ Failed to fetch page")
        return
    
    # Find API endpoints
    endpoints = find_api_endpoints(response.text)
    
    # Extract comic information
    comic_slug = extract_comic_info(response.text)
    
    if comic_slug:
        # Test API endpoints
        chapter_data = test_api_endpoints(comic_slug)
        
        if chapter_data:
            print(f"\n🎉 Successfully found chapter data!")
            print(f"Total chapters: {len(chapter_data.get('chapters', chapter_data.get('data', [])))}")
        else:
            print("\n❌ Could not find chapter data via API")
    else:
        print("\n❌ Could not extract comic slug")

if __name__ == "__main__":
    main()

