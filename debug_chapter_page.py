#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

def debug_chapter_page():
    """Debug what's actually in the chapter page HTML."""
    
    chapter_url = "https://comick.live/comic/00-the-beginning-after-the-end-1/r5bcQ_C5-chapter-1-en"
    
    print(f"🔍 Loading chapter page: {chapter_url}")
    
    try:
        response = requests.get(chapter_url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to load chapter page: {response.status_code}")
            return
        
        print("✅ Chapter page loaded successfully")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for all select elements
        print("🔍 Looking for all select elements...")
        select_elements = soup.find_all('select')
        print(f"Found {len(select_elements)} select elements")
        
        for i, select in enumerate(select_elements):
            print(f"\n📜 Select {i+1}:")
            print(f"  Classes: {select.get('class', [])}")
            print(f"  ID: {select.get('id', 'None')}")
            
            options = select.find_all('option')
            print(f"  Options: {len(options)}")
            
            if len(options) > 0:
                print("  First few options:")
                for j, option in enumerate(options[:5]):
                    value = option.get('value', '')
                    text = option.get_text(strip=True)
                    print(f"    {j+1}. Value: '{value}', Text: '{text}'")
                
                if len(options) > 5:
                    print(f"    ... and {len(options) - 5} more")
        
        # Also look for any script tags that might contain chapter data
        print("\n🔍 Looking for script tags with chapter data...")
        scripts = soup.find_all('script')
        
        for i, script in enumerate(scripts):
            if script.string and ('chapter' in script.string.lower() or 'hid' in script.string.lower()):
                print(f"📜 Script {i+1} contains chapter/hid data:")
                content = script.string[:500]  # First 500 chars
                print(f"  Content: {content}...")
                
                # Look for specific patterns
                if 'chapterList' in script.string:
                    print("  ✅ Found 'chapterList'")
                if 'chapterLangList' in script.string:
                    print("  ✅ Found 'chapterLangList'")
                if 'option' in script.string and 'value' in script.string:
                    print("  ✅ Found option/value patterns")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_chapter_page()

