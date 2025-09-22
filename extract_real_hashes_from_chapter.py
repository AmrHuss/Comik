#!/usr/bin/env python3

import requests
import re
from bs4 import BeautifulSoup

def extract_real_hashes_from_chapter_page():
    """Extract real hash IDs from a chapter page that has the full chapter list."""
    
    # Use Chapter 1 which we know works
    chapter_url = "https://comick.live/comic/00-the-beginning-after-the-end-1/r5bcQ_C5-chapter-1-en"
    
    print(f"🔍 Loading chapter page: {chapter_url}")
    
    try:
        response = requests.get(chapter_url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to load chapter page: {response.status_code}")
            return []
        
        print("✅ Chapter page loaded successfully")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the chapter selector dropdown
        print("🔍 Looking for chapter selector dropdown...")
        
        # Find select elements that contain chapter options
        select_elements = soup.find_all('select')
        
        chapters = []
        
        for select in select_elements:
            # Look for options with value attributes (these are the hash IDs)
            options = select.find_all('option', value=True)
            
            if len(options) > 10:  # Only process if we have many options (likely the chapter list)
                print(f"✅ Found chapter selector with {len(options)} options")
                
                for option in options:
                    hid = option.get('value', '').strip()
                    chapter_text = option.get_text(strip=True)
                    
                    if hid and chapter_text and hid != 'settings' and hid != 'all':
                        # Extract chapter number from text (e.g., "225.5", "225", "1")
                        chapter_match = re.search(r'^(\d+(?:\.\d+)?)', chapter_text)
                        if chapter_match:
                            chapter_num = chapter_match.group(1)
                            
                            chapter = {
                                'title': f"Chapter {chapter_num}",
                                'url': f"https://comick.live/comic/00-the-beginning-after-the-end-1/{hid}-chapter-{chapter_num}-en",
                                'date': 'Unknown',
                                'chapter_number': chapter_num,
                                'hid': hid
                            }
                            chapters.append(chapter)
                            print(f"  📖 Chapter {chapter_num}: {hid}")
                
                break  # Found the chapter list, no need to check other selects
        
        print(f"\n✅ Extracted {len(chapters)} chapters with real hash IDs")
        return chapters
        
    except Exception as e:
        print(f"❌ Error extracting chapters: {e}")
        return []

def test_extracted_chapters():
    """Test the extracted chapters to make sure they work."""
    chapters = extract_real_hashes_from_chapter_page()
    
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

