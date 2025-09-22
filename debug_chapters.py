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
        if 'chapter' in script.lower() or 'data' in script.lower():
            print(f"\n🔍 Script {i} contains 'chapter' or 'data':")
            print(f"Length: {len(script)} characters")
            print(f"First 500 chars: {script[:500]}")
            
            # Look for JSON patterns more carefully
            if '{' in script and '}' in script:
                print("Contains JSON-like structure")
                
                # Try to find larger JSON objects that might contain chapter data
                # Look for patterns like {"data": [...] or {"chapters": [...]}
                chapter_patterns = [
                    r'\{[^{}]*"data"[^{}]*\[[^\]]*chapter[^\]]*\]',
                    r'\{[^{}]*"chapters"[^{}]*\[[^\]]*\]',
                    r'\{[^{}]*"chapter"[^{}]*\}',
                    r'\{[^{}]*"data"[^{}]*\[[^\]]*\]'
                ]
                
                for pattern in chapter_patterns:
                    matches = re.findall(pattern, script, re.DOTALL)
                    if matches:
                        print(f"Found potential chapter data with pattern: {len(matches)} matches")
                        for j, match in enumerate(matches[:2]):  # Check first 2 matches
                            try:
                                data = json.loads(match)
                                print(f"  Match {j}: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                                if isinstance(data, dict) and 'data' in data:
                                    print(f"    Data array length: {len(data['data']) if isinstance(data['data'], list) else 'Not a list'}")
                                    if isinstance(data['data'], list) and data['data']:
                                        print(f"    First item keys: {list(data['data'][0].keys()) if isinstance(data['data'][0], dict) else 'Not a dict'}")
                            except json.JSONDecodeError as e:
                                print(f"  JSON decode error: {e}")
                
                # Also try to find the main JSON object that contains all the data
                try:
                    # Look for the main JSON object that starts with { and contains the comic data
                    # Use a more sophisticated approach to find the complete JSON object
                    if '{"id":' in script and '"title":' in script:
                        print(f"\n📋 Looking for main JSON object...")
                        
                        # Find the start of the JSON object
                        start_pos = script.find('{"id":')
                        if start_pos != -1:
                            # Find the matching closing brace by counting braces
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
                            
                            main_json = script[start_pos:end_pos]
                            print(f"Main JSON object found (length: {len(main_json)})")
                            
                            # Try to parse it
                            try:
                                main_data = json.loads(main_json)
                                print(f"Main data keys: {list(main_data.keys())}")
                                
                                # Look for chapter-related data in the main object
                                for key, value in main_data.items():
                                    if 'chapter' in key.lower():
                                        print(f"  Chapter-related key '{key}': {type(value)} - {len(value) if isinstance(value, list) else 'N/A'}")
                                        if isinstance(value, list) and value and isinstance(value[0], dict):
                                            print(f"    First item keys: {list(value[0].keys())}")
                                            print(f"    Sample first item: {value[0]}")
                                    elif isinstance(value, list) and value and isinstance(value[0], dict):
                                        # Check if this list contains chapter data
                                        first_item = value[0]
                                        if any('chapter' in str(k).lower() or 'chap' in str(k).lower() for k in first_item.keys()):
                                            print(f"  List '{key}' contains chapter data: {len(value)} items")
                                            print(f"    First item keys: {list(first_item.keys())}")
                                            print(f"    Sample first item: {first_item}")
                                            
                                # Also check for any other arrays that might contain chapters
                                print(f"\n🔍 Looking for all arrays in the data...")
                                for key, value in main_data.items():
                                    if isinstance(value, list) and value:
                                        print(f"  Array '{key}': {len(value)} items")
                                        if isinstance(value[0], dict):
                                            sample_keys = list(value[0].keys())
                                            print(f"    Sample keys: {sample_keys}")
                                            # Check if this looks like chapter data
                                            if any(k in sample_keys for k in ['chap', 'hid', 'title', 'lang']):
                                                print(f"    ⭐ This looks like chapter data!")
                                                print(f"    Sample item: {value[0]}")
                                        
                            except json.JSONDecodeError as e:
                                print(f"Failed to parse main JSON: {e}")
                                print(f"JSON preview: {main_json[:200]}...")
                                
                except Exception as e:
                    print(f"Error processing main JSON: {e}")

if __name__ == "__main__":
    debug_chapters()
