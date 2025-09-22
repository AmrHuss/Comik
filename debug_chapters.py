#!/usr/bin/env python3
"""
Debug script for comick.live chapter data.
FINAL VERSION: Uses the direct API endpoint with a full set of browser headers,
including 'Origin' and 'Referer', to bypass advanced anti-bot measures.
"""
import requests
import json

def get_headers(origin_url):
    """
    Get a comprehensive set of standardized headers to mimic a real browser.
    The 'Origin' and 'Referer' headers are critical for this API.
    """
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': origin_url,  # <-- CRUCIAL: The API checks where the request is "originating" from.
        'Referer': origin_url, # <-- CRUCIAL: The API checks the page that "referred" the user.
        'Sec-Ch-Ua': '"Not/A)Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }

def debug_chapters_api():
    """Debugs chapter data extraction by calling the backend API directly."""
    
    # 1. Define the target comic URL. This will be used for BOTH the Origin and Referer headers.
    comic_url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    print(f"[*] Debugging chapter data for: {comic_url}")
    
    try:
        comic_slug = comic_url.split("/")[-1]
        print(f"[*] Extracted Comic Slug: {comic_slug}")
    except IndexError:
        print("❌ Could not extract comic slug from URL.")
        return

    # 2. Construct the API URL to fetch ALL chapters.
    api_url = f"https://api.comick.fun/comic/{comic_slug}/chapters?limit=99999"
    print(f"[*] Constructed API URL: {api_url}")

    # 3. Make the API request with the COMPLETE set of headers.
    try:
        print(f"[*] Making direct API request with full browser headers...")
        
        # The Origin and Referer must be the main site URL
        headers = get_headers(origin_url="https://comick.live")
        
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        print("✅ Success! Received API response.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch data from API: {e}")
        return

    # 4. Parse the JSON response
    try:
        data = response.json()
        chapters = data.get('chapters', [])
        
        if not chapters:
            print("❌ No 'chapters' key found in the API response or the list is empty.")
            print("Full response:", data)
            return

        num_chapters = len(chapters)
        print(f"\n✅✅✅ SUCCESS! Found {num_chapters} chapters in the API response. ✅✅✅")
        
        if num_chapters > 0:
            print("\n🔍 Displaying first 5 chapters found:")
            for i, chapter in enumerate(chapters[:5]):
                chap_num = chapter.get('chap', 'N/A')
                chap_title = chapter.get('title', '')
                chap_hid = chapter.get('hid', 'N/A')
                chap_lang = chapter.get('lang', 'N/A')
                
                full_chapter_url = f"https://comick.live/comic/{comic_slug}/{chap_hid}-chapter-{chap_num}-{chap_lang}"
                
                print(f"  {i+1}. Chapter {chap_num}: '{chap_title}' - URL: {full_chapter_url}")

    except json.JSONDecodeError:
        print("❌ Failed to parse the response as JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    debug_chapters_api()