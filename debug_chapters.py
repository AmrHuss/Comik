#!/usr/bin/env python3
"""Debug script for chapter data."""

import sys
import os
import re
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from comick_live_scraper import make_request, get_headers

def debug_chapters():
    """Debug chapter data extraction."""
    url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    print(f"Debugging chapter data for: {url}")
    
    # Make request
    response = make_request(url)
    if not response:
        print("❌ Failed to fetch page")
        return
    
    # Look for script tags
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, response.text, re.DOTALL)
    
    print(f"Found {len(scripts)} script tags")
    
    for i, script in enumerate(scripts):
        if 'chapter' in script.lower():
            print(f"\n🔍 Script {i} contains 'chapter':")
            print(f"Length: {len(script)} characters")
            print(f"First 300 chars: {script[:300]}")
            
            # Look for JSON patterns
            if '{' in script and '}' in script:
                print("Contains JSON-like structure")
                
                # Try to find all JSON objects
                json_objects = re.findall(r'\{[^{}]*\}', script)
                print(f"Found {len(json_objects)} potential JSON objects")
                
                for j, obj in enumerate(json_objects[:3]):  # Check first 3
                    try:
                        data = json.loads(obj)
                        if isinstance(data, dict):
                            print(f"  Object {j}: {list(data.keys())}")
                            if 'chapter' in str(data).lower():
                                print(f"    Contains chapter data: {data}")
                    except:
                        pass

if __name__ == "__main__":
    debug_chapters()
