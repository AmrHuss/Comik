#!/usr/bin/env python3
"""Debug script for Comick detail scraper."""

import sys
import os
import re
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from comick_live_scraper import make_request, get_headers

def debug_detail_scraper():
    """Debug the detail scraper to see what's in the script tags."""
    url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    print(f"Debugging detail scraper with: {url}")
    
    # Make request
    response = make_request(url)
    if not response:
        print("❌ Failed to fetch page")
        return
    
    print(f"✅ Page fetched successfully ({len(response.text)} characters)")
    
    # Look for script tags
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, response.text, re.DOTALL)
    
    print(f"Found {len(scripts)} script tags")
    
    for i, script in enumerate(scripts):
        if 'title' in script and 'hid' in script:
            print(f"\n🔍 Script {i} contains 'title' and 'hid':")
            print(f"Length: {len(script)} characters")
            
            # Try to find JSON
            try:
                # Look for the start of the JSON object
                start_match = re.search(r'\{[^{}]*"title"', script)
                if start_match:
                    start_pos = start_match.start()
                    
                    # Find the matching closing brace
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
                    
                    json_str = script[start_pos:end_pos]
                    
                    try:
                        data = json.loads(json_str)
                        print(f"✅ JSON parsed successfully!")
                        print(f"Keys: {list(data.keys())}")
                        print(f"Title: {data.get('title', 'N/A')}")
                        print(f"Description: {data.get('description', 'N/A')}")
                        print(f"Origination: {data.get('origination', 'N/A')}")
                        print(f"Status: {data.get('status', 'N/A')}")
                        print(f"Genres: {data.get('genres', 'N/A')}")
                        break
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parse error: {e}")
                        continue
                else:
                    print("❌ No JSON object found with 'title' key")
            except Exception as e:
                print(f"❌ Error processing script: {e}")
    
    # Also look for chapter data
    print(f"\n🔍 Looking for chapter data...")
    for i, script in enumerate(scripts):
        if 'chapter' in script and 'data' in script:
            print(f"Script {i} contains 'chapter' and 'data'")
            print(f"Length: {len(script)} characters")
            print(f"First 200 chars: {script[:200]}")
            break

if __name__ == "__main__":
    debug_detail_scraper()