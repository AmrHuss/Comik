#!/usr/bin/env python3
"""
Quick test to see what's happening with chapter URLs.
"""

import requests

def test_chapter_urls():
    """Test different chapter URL patterns to see what works."""
    print("🔍 Testing different chapter URL patterns...")
    
    comic_slug = '00-the-beginning-after-the-end-1'
    real_hash = 'rlKl2'  # From the working sample
    
    # Test different URL patterns
    test_urls = [
        f"https://comick.live/comic/{comic_slug}/{real_hash}-chapter-1-en",
        f"https://comick.live/comic/{comic_slug}/{real_hash}-chapter-1-pl",
        f"https://comick.live/comic/{comic_slug}/{real_hash}-chapter-0-pl",  # This one we know works
        f"https://comick.live/comic/{comic_slug}/{real_hash}-chapter-2-pl",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://comick.live/'
    }
    
    for i, url in enumerate(test_urls):
        print(f'\nTest {i+1}: {url}')
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f'  Status: {response.status_code}')
            if response.status_code == 200:
                print('  ✅ Works!')
                # Check if it contains chapter content
                if 'chapter' in response.text.lower() or 'image' in response.text.lower():
                    print('  ✅ Contains chapter content!')
                else:
                    print('  ⚠️  No chapter content found')
            else:
                print(f'  ❌ Failed with status {response.status_code}')
        except Exception as e:
            print(f'  ❌ Error: {e}')

if __name__ == "__main__":
    test_chapter_urls()


