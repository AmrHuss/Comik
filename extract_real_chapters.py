#!/usr/bin/env python3
"""
Extract real chapter hash IDs from Comick HTML
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def extract_chapter_data_from_html(html_content, comic_slug):
    """Extract real chapter data including hash IDs from HTML."""
    try:
        print("🔍 Extracting real chapter data from HTML...")
        
        # Look for the language selector with hash IDs - try multiple patterns
        language_patterns = [
            r'<select[^>]*class="[^"]*rounded[^"]*"[^>]*>.*?</select>',
            r'<select[^>]*@change="getChapterByLanguage[^"]*"[^>]*>.*?</select>',
            r'<select[^>]*>.*?data-hid="[^"]*".*?</select>',
            r'<option[^>]*data-hid="[^"]*"[^>]*>.*?</option>'
        ]
        
        hash_ids = []
        for pattern in language_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                print(f"Found language selector match: {match[:100]}...")
                # Extract hash IDs from data-hid attributes
                hid_pattern = r'data-hid="([^"]+)"'
                found_hids = re.findall(hid_pattern, match)
                hash_ids.extend(found_hids)
                print(f"Found {len(found_hids)} hash IDs: {found_hids}")
        
        # Also look for hash IDs anywhere in the HTML
        all_hid_pattern = r'data-hid="([^"]+)"'
        all_hash_ids = re.findall(all_hid_pattern, html_content)
        print(f"Found {len(all_hash_ids)} total hash IDs in HTML: {all_hash_ids[:10]}...")
        
        # Look for chapter data in script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        chapters_data = []
        for i, script in enumerate(scripts):
            if 'firstChapters' in script and '{"id":' in script:
                print(f"Found firstChapters in script {i}")
                start_pos = script.find('{"id":')
                if start_pos != -1:
                    brace_count = 0
                    end_pos = start_pos
                    for j, char in enumerate(script[start_pos:], start_pos):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = j + 1
                                break
                    
                    try:
                        data = json.loads(script[start_pos:end_pos])
                        if 'firstChapters' in data and data['firstChapters']:
                            chapters_data = data['firstChapters']
                            print(f"✅ Found {len(chapters_data)} chapters in firstChapters")
                            break
                    except Exception as e:
                        print(f"❌ Failed to parse JSON in script {i}: {e}")
                        continue
        
        # Look for last chapter number
        last_chapter_pattern = r'last chapter:\s*([\d.]+)'
        last_chapter_match = re.search(last_chapter_pattern, html_content)
        last_chapter = None
        if last_chapter_match:
            last_chapter = last_chapter_match.group(1)
            print(f"Found last chapter: {last_chapter}")
        
        # Look for chapter list in script data
        chapter_list_pattern = r'chapterList\s*:\s*\[(.*?)\]'
        chapter_list_match = re.search(chapter_list_pattern, html_content, re.DOTALL)
        
        all_chapters = []
        if chapter_list_match:
            print("Found chapterList in script")
            chapter_list_str = chapter_list_match.group(1)
            # Try to extract individual chapter objects
            chapter_objects = re.findall(r'\{[^}]*"hid"[^}]*\}', chapter_list_str)
            print(f"Found {len(chapter_objects)} chapter objects")
            
            for obj_str in chapter_objects:
                try:
                    chapter_obj = json.loads(obj_str)
                    all_chapters.append(chapter_obj)
                except:
                    continue
        
        # Look for chapter data in Alpine.js data
        alpine_data_pattern = r'x-data="([^"]*)"'
        alpine_matches = re.findall(alpine_data_pattern, html_content)
        
        for alpine_data in alpine_matches:
            if 'chapter' in alpine_data and 'hid' in alpine_data:
                print("Found Alpine.js chapter data")
                # Try to extract chapter information
                try:
                    # Clean up the Alpine.js data
                    clean_data = alpine_data.replace("'", '"')
                    data = json.loads(clean_data)
                    if 'chapter' in data and 'hid' in data['chapter']:
                        print(f"Found chapter hash: {data['chapter']['hid']}")
                except:
                    continue
        
        # Look for chapter data in any script that contains hash IDs
        for i, script in enumerate(scripts):
            if 'hid' in script and ('chapter' in script or 'Chapter' in script):
                print(f"Script {i} contains hash IDs and chapter data")
                # Look for hash ID patterns
                hid_matches = re.findall(r'"hid"\s*:\s*"([^"]+)"', script)
                if hid_matches:
                    print(f"Found hash IDs in script {i}: {hid_matches}")
                    hash_ids.extend(hid_matches)
        
        return {
            'hash_ids': list(set(hash_ids)),  # Remove duplicates
            'chapters_data': chapters_data,
            'last_chapter': last_chapter,
            'all_chapters': all_chapters
        }
        
    except Exception as e:
        print(f"❌ Error extracting chapter data: {e}")
        return {}

def test_real_chapter_extraction():
    """Test extracting real chapter data from a Comick page."""
    test_url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        print(f"🔍 Testing real chapter extraction from: {test_url}")
        response = requests.get(test_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        comic_slug = "00-the-beginning-after-the-end-1"
        result = extract_chapter_data_from_html(response.text, comic_slug)
        
        print("\n📊 EXTRACTION RESULTS:")
        print(f"Hash IDs from language selector: {result.get('hash_ids', [])}")
        print(f"Chapters from firstChapters: {len(result.get('chapters_data', []))}")
        print(f"Last chapter: {result.get('last_chapter', 'Not found')}")
        print(f"All chapters from chapterList: {len(result.get('all_chapters', []))}")
        
        # Show sample chapter data
        if result.get('chapters_data'):
            print(f"\n📖 Sample chapter data:")
            for i, chapter in enumerate(result['chapters_data'][:3]):
                print(f"  Chapter {i+1}: {chapter}")
        
        # Show sample hash IDs
        if result.get('hash_ids'):
            print(f"\n🔑 Sample hash IDs:")
            for i, hid in enumerate(result['hash_ids'][:10]):
                print(f"  Hash {i+1}: {hid}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing extraction: {e}")
        return {}

if __name__ == "__main__":
    test_real_chapter_extraction()