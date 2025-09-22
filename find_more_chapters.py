#!/usr/bin/env python3
"""
Find more chapter data and hash IDs from Comick HTML
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def find_all_chapter_data(html_content):
    """Find all chapter data and hash IDs from HTML."""
    try:
        print("🔍 Searching for all chapter data...")
        
        # Look for all script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        all_hash_ids = []
        all_chapter_data = []
        
        for i, script in enumerate(scripts):
            print(f"\n📜 Analyzing script {i}...")
            
            # Look for hash IDs in this script
            hid_matches = re.findall(r'"hid"\s*:\s*"([^"]+)"', script)
            if hid_matches:
                print(f"  Found {len(hid_matches)} hash IDs: {hid_matches}")
                all_hash_ids.extend(hid_matches)
            
            # Look for chapter data
            if 'chapter' in script.lower() or 'Chapter' in script:
                print(f"  Script contains chapter data")
                
                # Look for JSON objects with chapter data
                json_objects = re.findall(r'\{[^{}]*"hid"[^{}]*\}', script)
                for obj_str in json_objects:
                    try:
                        obj = json.loads(obj_str)
                        if 'hid' in obj:
                            all_chapter_data.append(obj)
                            print(f"    Chapter object: {obj}")
                    except:
                        continue
                
                # Look for arrays of chapter data
                array_pattern = r'\[(.*?)\]'
                arrays = re.findall(array_pattern, script)
                for array_str in arrays:
                    if 'hid' in array_str and 'chapter' in array_str.lower():
                        print(f"    Found chapter array: {array_str[:200]}...")
                        # Try to extract individual objects
                        objects = re.findall(r'\{[^}]*"hid"[^}]*\}', array_str)
                        for obj_str in objects:
                            try:
                                obj = json.loads(obj_str)
                                if 'hid' in obj:
                                    all_chapter_data.append(obj)
                            except:
                                continue
        
        # Look for specific patterns that might contain chapter lists
        patterns = [
            r'chapterList\s*:\s*\[(.*?)\]',
            r'chapters\s*:\s*\[(.*?)\]',
            r'chapterData\s*:\s*\[(.*?)\]',
            r'firstChapters\s*:\s*\[(.*?)\]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                print(f"Found pattern {pattern}: {match[:100]}...")
                # Extract hash IDs from this match
                hids = re.findall(r'"hid"\s*:\s*"([^"]+)"', match)
                if hids:
                    print(f"  Found {len(hids)} hash IDs: {hids}")
                    all_hash_ids.extend(hids)
        
        # Look for Alpine.js data
        alpine_pattern = r'x-data="([^"]*)"'
        alpine_matches = re.findall(alpine_pattern, html_content)
        
        for alpine_data in alpine_matches:
            if 'chapter' in alpine_data.lower():
                print(f"Found Alpine.js data: {alpine_data[:100]}...")
                # Extract hash IDs
                hids = re.findall(r'"hid"\s*:\s*"([^"]+)"', alpine_data)
                if hids:
                    print(f"  Found {len(hids)} hash IDs: {hids}")
                    all_hash_ids.extend(hids)
        
        # Remove duplicates
        unique_hash_ids = list(set(all_hash_ids))
        unique_chapter_data = []
        seen_hids = set()
        
        for chapter in all_chapter_data:
            if 'hid' in chapter and chapter['hid'] not in seen_hids:
                unique_chapter_data.append(chapter)
                seen_hids.add(chapter['hid'])
        
        print(f"\n📊 SUMMARY:")
        print(f"Total hash IDs found: {len(unique_hash_ids)}")
        print(f"Unique chapter data objects: {len(unique_chapter_data)}")
        
        return {
            'hash_ids': unique_hash_ids,
            'chapter_data': unique_chapter_data
        }
        
    except Exception as e:
        print(f"❌ Error finding chapter data: {e}")
        return {'hash_ids': [], 'chapter_data': []}

def test_comprehensive_extraction():
    """Test comprehensive chapter extraction."""
    test_url = "https://comick.live/comic/00-the-beginning-after-the-end-1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        print(f"🔍 Testing comprehensive chapter extraction from: {test_url}")
        response = requests.get(test_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = find_all_chapter_data(response.text)
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"Hash IDs: {result['hash_ids']}")
        print(f"Chapter data: {result['chapter_data']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing extraction: {e}")
        return {'hash_ids': [], 'chapter_data': []}

if __name__ == "__main__":
    test_comprehensive_extraction()

