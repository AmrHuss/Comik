#!/usr/bin/env python3
"""
Fix image extraction from Comick chapters
"""

import requests
import re
import json
from bs4 import BeautifulSoup

def extract_chapter_images_fixed(html_content, chapter_url):
    """Fixed image extraction from Comick chapters."""
    try:
        print("🔍 Extracting chapter images with improved logic...")
        
        # Look for images in script tags (JSON data)
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        images = []
        for i, script in enumerate(scripts):
            print(f"Analyzing script {i}...")
            
            # Look for various image patterns
            if 'images' in script.lower() or 'image' in script.lower():
                print(f"  Script {i} contains image data")
                
                # Look for JSON objects with images
                json_objects = re.findall(r'\{[^{}]*"images"[^{}]*\}', script)
                for obj_str in json_objects:
                    try:
                        obj = json.loads(obj_str)
                        if 'images' in obj and isinstance(obj['images'], list):
                            images.extend(obj['images'])
                            print(f"    Found {len(obj['images'])} images in JSON object")
                    except:
                        continue
                
                # Look for arrays of images
                array_patterns = [
                    r'"images"\s*:\s*\[(.*?)\]',
                    r'images\s*:\s*\[(.*?)\]',
                    r'\[(.*?)\]'
                ]
                
                for pattern in array_patterns:
                    matches = re.findall(pattern, script, re.DOTALL)
                    for match in matches:
                        if 'url' in match and ('http' in match or 'cdn' in match):
                            print(f"    Found image array: {match[:100]}...")
                            
                            # Try to extract individual image objects
                            img_objects = re.findall(r'\{[^}]*"url"[^}]*\}', match)
                            for img_str in img_objects:
                                try:
                                    img_obj = json.loads(img_str)
                                    if 'url' in img_obj:
                                        images.append(img_obj)
                                        print(f"      Added image: {img_obj['url']}")
                                except:
                                    continue
        
        # Also look for images in HTML img tags
        soup = BeautifulSoup(html_content, 'lxml')
        img_tags = soup.find_all('img')
        print(f"Found {len(img_tags)} img tags in HTML")
        
        for img in img_tags:
            src = img.get('src', '')
            data_src = img.get('data-src', '')
            
            if src and 'cdn1.comicknew.pictures' in src:
                images.append({'url': src})
                print(f"Added img tag image: {src}")
            elif data_src and 'cdn1.comicknew.pictures' in data_src:
                images.append({'url': data_src})
                print(f"Added data-src image: {data_src}")
        
        # Process and deduplicate images
        processed_images = []
        seen_urls = set()
        
        for image in images:
            try:
                # Extract image URL
                img_url = image.get('url', '') if isinstance(image, dict) else str(image)
                if not img_url:
                    continue
                
                # Ensure it's a full URL
                if not img_url.startswith('http'):
                    img_url = f"https://comick.live{img_url}"
                
                # Only add if it looks like a real Comick image URL and not seen before
                if 'cdn1.comicknew.pictures' in img_url and img_url not in seen_urls:
                    processed_images.append(img_url)
                    seen_urls.add(img_url)
                    print(f"✅ Added unique image: {img_url}")
                else:
                    print(f"Skipping image: {img_url}")
                
            except Exception as e:
                print(f"Error processing image: {e}")
                continue
        
        print(f"✅ Final result: {len(processed_images)} unique images")
        return processed_images
        
    except Exception as e:
        print(f"❌ Error extracting chapter images: {e}")
        return []

def test_chapter_reading_fixed():
    """Test chapter reading with fixed image extraction."""
    # Test with the real chapter URL we found
    chapter_url = "https://comick.live/comic/00-the-beginning-after-the-end-1/rlKl2-chapter-0-pl"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://comick.live/comic/00-the-beginning-after-the-end-1'
    }
    
    try:
        print(f"🔍 Testing chapter reading: {chapter_url}")
        response = requests.get(chapter_url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Chapter URL is accessible!")
            
            # Extract images with fixed logic
            images = extract_chapter_images_fixed(response.text, chapter_url)
            
            if images:
                print(f"✅ Successfully extracted {len(images)} images!")
                print("Sample images:")
                for i, img in enumerate(images[:5]):
                    print(f"  Image {i+1}: {img}")
                return True, images
            else:
                print("❌ No images found")
                return False, []
        else:
            print(f"❌ Chapter URL not accessible: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"❌ Error testing chapter reading: {e}")
        return False, []

if __name__ == "__main__":
    test_chapter_reading_fixed()

