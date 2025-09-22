#!/usr/bin/env python3
"""
Find real chapter data with unique hash IDs
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def find_real_chapters():
    """Find real chapter data with unique hash IDs."""
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
    soup = BeautifulSoup(html_content, 'lxml')
    
    print("🔍 Looking for chapter data in scripts...")
    
    # Look for all script tags
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} script tags")
    
    for i, script in enumerate(scripts):
        script_content = str(script)
        
        # Look for chapter-related data
        if any(keyword in script_content for keyword in ['chapters', 'chapter', 'hid', 'lang']):
            print(f"\n📜 Script {i}:")
            print(f"Length: {len(script_content)}")
            
            # Look for JSON objects with chapter data
            json_patterns = [
                r'chapters\s*:\s*(\[.*?\])',
                r'firstChapters\s*:\s*(\[.*?\])',
                r'dupGroupChapters\s*:\s*(\[.*?\])',
                r'chapter\s*:\s*(\{.*?\})',
                r'chapters\s*=\s*(\[.*?\])',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, script_content, re.DOTALL)
                if matches:
                    print(f"✅ Found pattern: {pattern}")
                    for match in matches[:3]:  # Show first 3 matches
                        try:
                            data = json.loads(match)
                            print(f"   Data: {json.dumps(data, indent=2)[:500]}...")
                        except:
                            print(f"   Raw: {match[:200]}...")
            
            # Look for specific chapter structures
            if 'hid' in script_content and 'lang' in script_content:
                print("🔍 Looking for hid/lang patterns...")
                
                # Pattern for individual chapters
                chapter_pattern = r'\{[^}]*"hid"\s*:\s*"([^"]+)"[^}]*"lang"\s*:\s*"([^"]+)"[^}]*"chap"\s*:\s*"([^"]+)"[^}]*\}'
                chapters = re.findall(chapter_pattern, script_content)
                
                if chapters:
                    print(f"✅ Found {len(chapters)} individual chapters:")
                    for hid, lang, chap in chapters[:10]:  # Show first 10
                        print(f"   Chapter {chap}: hid={hid}, lang={lang}")
                
                # Pattern for chapter arrays
                array_pattern = r'\[([^]]*"hid"[^]]*)\]'
                arrays = re.findall(array_pattern, script_content)
                
                if arrays:
                    print(f"✅ Found {len(arrays)} chapter arrays")
                    for array in arrays[:2]:  # Show first 2 arrays
                        print(f"   Array: {array[:300]}...")

if __name__ == "__main__":
    find_real_chapters()

