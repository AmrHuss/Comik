import requests
import re
import json
from bs4 import BeautifulSoup

def extract_loaded_chapters():
    url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    
    print("🔍 Fetching comic page...")
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        print(f"❌ Failed to fetch page: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for chapter rows in the table
    print("🔍 Looking for chapter rows in HTML...")
    
    # Find all table rows that contain chapter data
    chapter_rows = soup.find_all('tr', class_=re.compile(r'group.*border'))
    
    print(f"Found {len(chapter_rows)} chapter rows")
    
    chapters = []
    
    for i, row in enumerate(chapter_rows):
        # Look for the chapter link
        chapter_link = row.find('a', href=re.compile(r'/comic/.*chapter'))
        
        if chapter_link:
            href = chapter_link.get('href', '')
            print(f"Row {i+1}: {href}")
            
            # Extract chapter info from href
            # Format: /comic/00-the-beginning-after-the-end-1/{hid}-chapter-{chap}-{lang}
            match = re.search(r'/comic/[^/]+/([^-]+)-chapter-([^-]+)-([^/]+)', href)
            if match:
                hid, chap, lang = match.groups()
                chapters.append({
                    'hid': hid,
                    'chapter': chap,
                    'lang': lang,
                    'url': href
                })
                print(f"  ✅ Chapter {chap} ({lang}): {hid}")
            else:
                print(f"  ❌ Could not parse: {href}")
        
        # Also look for chapter number in the span
        chapter_span = row.find('span', {'x-text': re.compile(r"'Ch\. ' \+ chapter\.chap")})
        if chapter_span:
            title = chapter_span.get('title', '')
            if 'Chapter' in title:
                chap_num = title.replace('Chapter ', '')
                print(f"  📖 Chapter number: {chap_num}")
    
    print(f"\n✅ Found {len(chapters)} chapters with hash IDs:")
    for i, ch in enumerate(chapters[:10]):  # Show first 10
        print(f"  {i+1}. Chapter {ch['chapter']} ({ch['lang']}): {ch['hid']}")
    
    if len(chapters) > 10:
        print(f"  ... and {len(chapters) - 10} more")
    
    return chapters

if __name__ == "__main__":
    extract_loaded_chapters()

