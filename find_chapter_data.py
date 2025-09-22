import requests
import re
import json
from bs4 import BeautifulSoup

def find_chapter_data():
    url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    
    print("🔍 Fetching comic page...")
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        print(f"❌ Failed to fetch page: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for the Alpine.js data structure
    print("🔍 Looking for Alpine.js chapter data...")
    
    # Find the div with x-data="ChapterList.loadDataChapter"
    chapter_div = soup.find('div', {'x-data': re.compile(r'ChapterList\.loadDataChapter')})
    
    if chapter_div:
        print("✅ Found ChapterList div")
        
        # Extract the x-data attribute
        x_data = chapter_div.get('x-data', '')
        print(f"📜 x-data: {x_data[:200]}...")
        
        # Look for the JSON.parse part - use DOTALL flag for multiline
        json_match = re.search(r'JSON\.parse\(\[(.*?)\]\)', x_data, re.DOTALL)
        if json_match:
            print("✅ Found JSON.parse data")
            json_str = json_match.group(1)
            print(f"📜 JSON data: {json_str[:200]}...")
            
            try:
                # Decode Unicode escape sequences
                decoded_json = json_str.encode().decode('unicode_escape')
                print(f"📜 Decoded JSON: {decoded_json[:200]}...")
                
                # Parse the JSON
                chapter_data = json.loads(f'[{decoded_json}]')
                print(f"✅ Parsed {len(chapter_data)} language options")
                
                for i, lang in enumerate(chapter_data):
                    print(f"  {i+1}. {lang['label']} ({lang['value']})")
                
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"❌ Failed to parse JSON: {e}")
        else:
            print("❌ No JSON.parse found in x-data")
    else:
        print("❌ No ChapterList div found")
    
    # Also look for any script tags that might contain chapter data
    print("\n🔍 Looking for chapter data in scripts...")
    scripts = soup.find_all('script')
    
    for i, script in enumerate(scripts):
        if script.string:
            content = script.string
            if 'ChapterList' in content or 'loadDataChapter' in content:
                print(f"📜 Script {i+1}: Found ChapterList reference")
                print(f"   Content preview: {content[:200]}...")
                
                # Look for chapter data patterns
                if 'hid' in content and 'chapter' in content:
                    print("   ✅ Contains chapter data patterns")
                    
                    # Try to extract chapter data
                    chapter_matches = re.findall(r'\{[^}]*"hid"[^}]*\}', content)
                    if chapter_matches:
                        print(f"   Found {len(chapter_matches)} potential chapter objects")
                        for j, match in enumerate(chapter_matches[:3]):  # Show first 3
                            print(f"     {j+1}. {match}")

if __name__ == "__main__":
    find_chapter_data()
