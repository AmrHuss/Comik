#!/usr/bin/env python3

import requests
import re
import json
from bs4 import BeautifulSoup

def extract_chapters_from_script():
    """Extract chapter data from script tags in the chapter page."""
    
    chapter_url = "https://comick.live/comic/00-the-beginning-after-the-end-1/r5bcQ_C5-chapter-1-en"
    
    print(f"🔍 Loading chapter page: {chapter_url}")
    
    try:
        response = requests.get(chapter_url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to load chapter page: {response.status_code}")
            return []
        
        print("✅ Chapter page loaded successfully")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for script tags with chapter data
        print("🔍 Looking for script tags with chapter data...")
        scripts = soup.find_all('script')
        
        chapters = []
        
        for i, script in enumerate(scripts):
            if script.string and ('chapterList' in script.string or 'chapterLangList' in script.string):
                print(f"📜 Found chapter data in script {i+1}")
                
                # Look for chapterList data
                chapter_list_match = re.search(r'"chapterList":\s*(\[.*?\])', script.string)
                if chapter_list_match:
                    try:
                        chapter_list_data = json.loads(chapter_list_match.group(1))
                        print(f"✅ Found chapterList with {len(chapter_list_data)} chapters")
                        
                        for chapter_data in chapter_list_data:
                            hid = chapter_data.get('hid', '')
                            chap = chapter_data.get('chap', '')
                            
                            if hid and chap:
                                chapter = {
                                    'title': f"Chapter {chap}",
                                    'url': f"https://comick.live/comic/00-the-beginning-after-the-end-1/{hid}-chapter-{chap}-en",
                                    'date': 'Unknown',
                                    'chapter_number': chap,
                                    'hid': hid
                                }
                                chapters.append(chapter)
                                print(f"  📖 Chapter {chap}: {hid}")
                        
                        break  # Found the data, no need to check other scripts
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse chapterList JSON: {e}")
                        continue
        
        print(f"\n✅ Extracted {len(chapters)} chapters with real hash IDs")
        return chapters
        
    except Exception as e:
        print(f"❌ Error extracting chapters: {e}")
        return []

def test_extracted_chapters():
    """Test the extracted chapters to make sure they work."""
    chapters = extract_chapters_from_script()
    
    if not chapters:
        print("❌ No chapters extracted")
        return
    
    # Test a few specific chapters
    test_chapters = ["1", "2", "3", "10", "50", "100"]
    
    print(f"\n🧪 Testing specific chapters...")
    
    for test_chap in test_chapters:
        matching_chapters = [ch for ch in chapters if ch['chapter_number'] == test_chap]
        
        if matching_chapters:
            chapter = matching_chapters[0]
            print(f"📖 Chapter {test_chap}: {chapter['hid']} - {chapter['url']}")
            
            # Test if the URL works
            try:
                test_response = requests.get(chapter['url'], timeout=10)
                if test_response.status_code == 200:
                    print(f"  ✅ Chapter {test_chap} loads successfully")
                else:
                    print(f"  ❌ Chapter {test_chap} failed: {test_response.status_code}")
            except Exception as e:
                print(f"  ❌ Chapter {test_chap} error: {e}")
        else:
            print(f"❌ Chapter {test_chap} not found")

if __name__ == "__main__":
    test_extracted_chapters()

