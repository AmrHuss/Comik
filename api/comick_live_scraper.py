#!/usr/bin/env python3
"""
Comick.live Scraper for ManhwaVerse
===================================

A dedicated scraper for comick.live using requests and BeautifulSoup.
Scrapes action genre comics and their details.

Author: ManhwaVerse Development Team
Date: 2025
Version: 1.0
"""

import logging
import time
import random
import requests
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
COMICK_BASE_URL = "https://comick.live"
ACTION_GENRE_URL = "https://comick.live/search?genres=action&order_by=user_follow_count"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

def get_headers():
    """Get standardized headers for HTTP requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

def make_request(url, retries=MAX_RETRIES, headers=None):
    """Make HTTP request with retry logic and proper error handling."""
    if headers is None:
        headers = get_headers()
    
    for attempt in range(retries):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
            if attempt == retries - 1:
                logger.error(f"All {retries} attempts failed for {url}")
                return None
    return None

def scrape_comick_action_genre():
    """Scrape action genre comics from comick.live."""
    try:
        logger.info("Starting Comick action genre scraping")
        
        all_comics = []
        max_pages = 5  # Load first 5 pages (75 comics total)
        
        for page in range(1, max_pages + 1):
            try:
                if page == 1:
                    url = ACTION_GENRE_URL
                else:
                    url = f"{ACTION_GENRE_URL}&page={page}"
                
                logger.info(f"Fetching page {page}: {url}")
                response = make_request(url)
                
                if not response:
                    logger.warning(f"Failed to fetch page {page}")
                    continue
                
                # Extract JSON data from script tags
                page_comics = extract_comick_data_from_scripts(response.text)
                
                if page_comics:
                    all_comics.extend(page_comics)
                    logger.info(f"Page {page}: Found {len(page_comics)} comics")
                else:
                    logger.warning(f"Page {page}: No comics found")
                    break  # Stop if no comics found on a page
                    
            except Exception as e:
                logger.warning(f"Error fetching page {page}: {e}")
                continue
        
        if not all_comics:
            logger.error("No comic data found in any page")
            return []
        
        logger.info(f"Successfully scraped {len(all_comics)} comics from {max_pages} pages")
        return all_comics
        
    except Exception as e:
        logger.error(f"Error scraping Comick action genre: {e}")
        logger.error(traceback.format_exc())
        return []

def extract_comick_data_from_scripts(html_content):
    """Extract comic data from JSON embedded in script tags."""
    try:
        import re
        import json
        
        # Look for the JSON data in script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        comics = []
        for i, script in enumerate(scripts):
            if 'current_page' in script and 'data' in script:
                logger.info(f"Found data in script {i}")
                
                # Try to find the JSON object more carefully
                # Look for the start of the JSON object
                start_match = re.search(r'\{[^{}]*"current_page"', script)
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
                        if 'data' in data and isinstance(data['data'], list):
                            comics = data['data']
                            logger.info(f"Found {len(comics)} comics in the data")
                            break
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON in script {i}: {e}")
                        continue
        
        # Process the comics
        processed_comics = []
        for comic in comics:
            try:
                # Convert to our format
                processed_comic = {
                    'title': comic.get('title', 'Unknown'),
                    'cover_url': comic.get('default_thumbnail', ''),
                    'detail_url': f"https://comick.live/comic/{comic.get('slug', '')}" if comic.get('slug') else '',
                    'author': 'Unknown',  # Not available in this data
                    'description': comic.get('description', 'No description available'),
                    'source': 'Comick',
                    'latest_chapter': f"{comic.get('last_chapter', 'N/A')} chapters" if comic.get('last_chapter') else 'N/A',
                    'rating': comic.get('bayesian_rating', 'N/A'),
                    'genres': ['Action'],
                    'status': comic.get('status', 'Ongoing')
                }
                
                # Convert cover image to use proxy
                if processed_comic['cover_url'] and 'cdn1.comicknew.pictures' in processed_comic['cover_url']:
                    processed_comic['cover_url'] = convert_comick_cover_to_proxy_url(processed_comic['cover_url'])
                
                processed_comics.append(processed_comic)
                
            except Exception as e:
                logger.warning(f"Error processing comic: {e}")
                continue
        
        return processed_comics
        
    except Exception as e:
        logger.error(f"Error extracting comic data from scripts: {e}")
        return []

def parse_comick_item(item):
    """Parse a single comic item from the list."""
    try:
        # Extract title - try multiple selectors
        title = ""
        title_selectors = [
            'p.font-bold.truncate',
            'p[class*="font-bold"][class*="truncate"]',
            'p[class*="font-bold"]',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'a[title]',
            'span[class*="title"]',
            'a[href*="/comic/"]'
        ]
        
        for selector in title_selectors:
            title_element = item.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                if not title and title_element.get('title'):
                    title = title_element.get('title').strip()
                if title:
                    break
        
        # If still no title, try to find any text that looks like a title
        if not title:
            all_text_elements = item.find_all(['p', 'span', 'div', 'a'])
            for elem in all_text_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 3 and len(text) < 100:
                    # Skip common non-title text
                    if not any(skip in text.lower() for skip in ['chapters', 'chapter', 'uploaded', 'rating', 'follow', 'ago', 'days', 'hours', 'minutes', '⭐', '👦']):
                        title = text
                        break
        
        if not title:
            logger.debug("No title found for comic item")
            return None
        
        # Extract cover image URL - try multiple selectors and attributes
        cover_url = ""
        img_selectors = [
            'img[class*="select-none"][class*="rounded-md"]',
            'img[class*="select-none"]',
            'img[class*="rounded-md"]',
            'img[class*="object-cover"]',
            'img'
        ]
        
        for selector in img_selectors:
            img_element = item.select_one(selector)
            if img_element:
                # Try multiple src attributes
                for attr in ['src', 'data-src', 'data-lazy-src']:
                    cover_url = img_element.get(attr, '')
                    if cover_url:
                        # Ensure it's a full URL
                        if not cover_url.startswith('http'):
                            cover_url = urljoin(COMICK_BASE_URL, cover_url)
                        break
                if cover_url:
                    break
        
        # Convert cover image to use proxy if it's a Comick CDN image
        if cover_url and 'cdn1.comicknew.pictures' in cover_url:
            cover_url = convert_comick_cover_to_proxy_url(cover_url)
        
        # Extract detail URL - try multiple selectors
        detail_url = ""
        link_selectors = [
            'a[class*="block"][class*="h-16"]',
            'a[class*="block"]',
            'a[href*="/comic/"]',
            'a[href]'
        ]
        
        for selector in link_selectors:
            link_element = item.select_one(selector)
            if link_element:
                detail_url = link_element.get('href', '')
                if detail_url:
                    if not detail_url.startswith('http'):
                        detail_url = urljoin(COMICK_BASE_URL, detail_url)
                    break
        
        # Extract description - try multiple selectors
        description = "No description available"
        desc_selectors = [
            'p[class*="prose"][class*="prose-sm"]',
            'p[class*="prose"]',
            'p[class*="description"]',
            'div[class*="description"]',
            'p[class*="summary"]'
        ]
        
        for selector in desc_selectors:
            desc_element = item.select_one(selector)
            if desc_element:
                description = desc_element.get_text(strip=True)
                if description and len(description) > 10:  # Only use if it's substantial
                    break
        
        # Extract author (try to find from various elements)
        author = "Unknown"
        author_elements = item.find_all(['span', 'div', 'p'], class_=lambda x: x and any(cls in x for cls in ['text-gray', 'author', 'creator']))
        for elem in author_elements:
            text = elem.get_text(strip=True)
            if text and not any(keyword in text.lower() for keyword in ['chapters', 'chapter', 'uploaded', 'rating', 'follow', 'ago', 'days', 'hours', 'minutes', '⭐', '👦']):
                author = text
                break
        
        # Extract latest chapter info
        latest_chapter = "N/A"
        chapter_elements = item.find_all(['span', 'div', 'p'])
        for elem in chapter_elements:
            text = elem.get_text(strip=True)
            if 'chapters' in text.lower() or 'chapter' in text.lower():
                latest_chapter = text
                break
        
        # Extract rating
        rating = "N/A"
        rating_elements = item.find_all(['span', 'div'])
        for elem in rating_elements:
            text = elem.get_text(strip=True)
            # Look for numeric rating (e.g., "9.16", "8.5")
            if text.replace('.', '').replace(',', '').isdigit() and len(text) <= 4 and '.' in text:
                try:
                    float(text)
                    rating = text
                    break
                except ValueError:
                    continue
        
        # Create comic data
        comic_data = {
            'title': title,
            'cover_url': cover_url,
            'detail_url': detail_url,
            'author': author,
            'description': description,
            'source': 'Comick',
            'latest_chapter': latest_chapter,
            'rating': rating,
            'genres': ['Action'],
            'status': 'Ongoing'
        }
        
        return comic_data
        
    except Exception as e:
        logger.warning(f"Error parsing comic item: {e}")
        return None

def scrape_comick_details(detail_url):
    """Scrape detailed information for a specific comic."""
    try:
        logger.info(f"Scraping Comick details for: {detail_url}")
        
        # Make request to detail page
        response = make_request(detail_url)
        if not response:
            logger.error("Failed to fetch Comick detail page")
            return None
        
        # Extract data from JSON in script tags
        comic_data = extract_comick_detail_data_from_scripts(response.text)
        
        if not comic_data:
            logger.error("No comic data found in detail page")
            return None
        
        # Extract title
        title = comic_data.get('title', 'Unknown Title')
        
        # Extract cover image
        cover_image = comic_data.get('cover_image', '')
        if cover_image and 'cdn1.comicknew.pictures' in cover_image:
            cover_image = convert_comick_cover_to_proxy_url(cover_image)
        
        # Extract description
        description = comic_data.get('description', 'No description available')
        
        # Extract genres
        genres = comic_data.get('genres', ['Action'])
        
        # Extract author
        author = comic_data.get('author', 'Unknown')
        
        # Extract chapters - try HTML first, then fall back to scripts
        comic_slug = comic_data.get('slug', '')
        logger.info(f"Comic slug: '{comic_slug}'")
        
        # Try HTML extraction first (like Webtoons/AsuraScans)
        chapters = extract_comick_chapters_from_html(response.text, comic_slug)
        
        # If HTML extraction didn't find many chapters, try script extraction as fallback
        if len(chapters) < 10:  # If we found very few chapters from HTML
            logger.info("HTML extraction found few chapters, trying script extraction as fallback")
            script_chapters = extract_comick_chapters_from_scripts(response.text, comic_slug)
            if len(script_chapters) > len(chapters):
                chapters = script_chapters
                logger.info(f"Using script extraction results: {len(chapters)} chapters")
        
        # Create detailed comic data
        comic_details = {
            'title': title,
            'cover_image': cover_image,
            'description': description,
            'rating': comic_data.get('rating', 'N/A'),
            'status': comic_data.get('status', 'Ongoing'),
            'genres': genres,
            'author': author,
            'chapters': chapters,
            'slug': comic_slug
        }
        
        logger.info(f"Successfully scraped details for: {title}")
        return comic_details
        
    except Exception as e:
        logger.error(f"Error scraping Comick details for {detail_url}: {e}")
        logger.error(traceback.format_exc())
        return None

def extract_comick_detail_data_from_scripts(html_content):
    """Extract comic detail data from JSON embedded in script tags."""
    try:
        import re
        import json
        
        # Look for the JSON data in script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        comic_data = {}
        for i, script in enumerate(scripts):
            if 'title' in script and 'hid' in script:
                logger.info(f"Found comic detail data in script {i}")
                
                # Try to find the JSON object more carefully
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
                        comic_data = json.loads(json_str)
                        logger.info(f"Found comic data: {comic_data.get('title', 'Unknown')}")
                        break
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON in script {i}: {e}")
                        continue
        
        # Process the comic data
        # Extract genres from the complex structure
        genres = ['Action']  # Default
        if comic_data.get('md_comic_md_genres'):
            try:
                genres = [genre['md_genres']['name'] for genre in comic_data['md_comic_md_genres'] if isinstance(genre, dict) and 'md_genres' in genre]
            except:
                genres = ['Action']
        
        processed_data = {
            'title': comic_data.get('title', 'Unknown Title'),
            'cover_image': comic_data.get('default_thumbnail', ''),
            'description': comic_data.get('desc', 'No description available'),
            'genres': genres,
            'author': comic_data.get('origination', 'Unknown'),
            'rating': comic_data.get('bayesian_rating', 'N/A'),
            'status': 'Ongoing' if comic_data.get('status') == 1 else 'Completed',
            'slug': comic_data.get('slug', '')
        }
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Error extracting comic detail data from scripts: {e}")
        return {}

def extract_real_chapters_from_chapter_page(comic_slug, sample_chapter):
    """Extract real chapter hash IDs from a chapter page that has the full chapter list."""
    import re
    import json
    try:
        if not sample_chapter or not sample_chapter.get('hid'):
            print("❌ No sample chapter with hash ID available")
            return []
        
        # Use the sample chapter to load a page that has the full chapter list
        sample_hid = sample_chapter.get('hid')
        sample_lang = sample_chapter.get('lang', 'en')
        sample_chap = sample_chapter.get('chap', '1')
        
        # Try to find an English chapter first by checking the script data
        # Look for English chapters in the original HTML
        english_chapter = None
        try:
            from bs4 import BeautifulSoup
            import requests
            response = requests.get(f"https://comick.live/comic/{comic_slug}", timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'firstChapters' in script.string:
                        import json
                        import re
                        # Look for firstChapters data - find the complete array
                        start_pos = script.string.find('"firstChapters":')
                        if start_pos != -1:
                            bracket_pos = script.string.find('[', start_pos)
                            if bracket_pos != -1:
                                # Count brackets to find the end
                                bracket_count = 0
                                end_pos = bracket_pos
                                for j, char in enumerate(script.string[bracket_pos:], bracket_pos):
                                    if char == '[':
                                        bracket_count += 1
                                    elif char == ']':
                                        bracket_count -= 1
                                        if bracket_count == 0:
                                            end_pos = j + 1
                                            break
                                
                                try:
                                    first_chapters_str = script.string[bracket_pos:end_pos]
                                    first_chapters_data = json.loads(first_chapters_str)
                                    for chapter_data in first_chapters_data:
                                        if chapter_data.get('lang') == 'en':
                                            english_chapter = chapter_data
                                            print(f"✅ Found English chapter: {english_chapter}")
                                            break
                                except:
                                    pass
        except:
            pass
        
        # Use English chapter if found, otherwise fall back to sample chapter
        if english_chapter:
            sample_hid = english_chapter.get('hid')
            sample_lang = 'en'
            sample_chap = english_chapter.get('chap', '1')
        else:
            print("⚠️  No English chapter found, using sample chapter")
        
        # Try different languages if English fails
        languages_to_try = ['en', sample_lang, 'pl', 'es', 'fr', 'de']
        
        for lang in languages_to_try:
            chapter_url = f"https://comick.live/comic/{comic_slug}/{sample_hid}-chapter-{sample_chap}-{lang}"
            print(f"🔍 Trying chapter page: {chapter_url}")
            
            try:
                response = requests.get(chapter_url, timeout=30)
                if response.status_code == 200:
                    print(f"✅ Chapter page loaded successfully with language: {lang}")
                    break
                else:
                    print(f"❌ Failed to load chapter page with language {lang}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error loading chapter page with language {lang}: {e}")
        else:
            print("❌ Failed to load chapter page with any language")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for script tags with chapter data
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and 'chapterList' in script.string:
                # Look for chapterList data - find the complete array
                start_pos = script.string.find('"chapterList":')
                if start_pos != -1:
                    bracket_pos = script.string.find('[', start_pos)
                    if bracket_pos != -1:
                        # Count brackets to find the end
                        bracket_count = 0
                        end_pos = bracket_pos
                        for j, char in enumerate(script.string[bracket_pos:], bracket_pos):
                            if char == '[':
                                bracket_count += 1
                            elif char == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_pos = j + 1
                                    break
                        
                        try:
                            chapter_list_str = script.string[bracket_pos:end_pos]
                            chapter_list_data = json.loads(chapter_list_str)
                            print(f"✅ Found chapterList with {len(chapter_list_data)} chapters")
                            
                            chapters = []
                            for chapter_data in chapter_list_data:
                                hid = chapter_data.get('hid', '')
                                chap = chapter_data.get('chap', '')
                                chapter_lang = chapter_data.get('lang', '')
                                
                                # Only include English chapters
                                if hid and chap and chapter_lang == 'en':
                                    chapter = {
                                        'title': f"Chapter {chap}",
                                        'url': f"https://comick.live/comic/{comic_slug}/{hid}-chapter-{chap}-en",
                                        'date': 'Unknown',
                                        'chapter_number': chap,
                                        'hid': hid,
                                        'lang': 'en'
                                    }
                                    chapters.append(chapter)
                            
                            print(f"✅ Extracted {len(chapters)} chapters with real hash IDs")
                            return chapters
                            
                        except json.JSONDecodeError as e:
                            print(f"❌ Failed to parse chapterList JSON: {e}")
                            continue
        
        print("❌ No chapterList found in script tags")
        return []
        
    except Exception as e:
        print(f"❌ Error extracting real chapters: {e}")
        return []

def generate_full_chapter_list_from_real_hashes(real_chapters, comic_slug, html_content):
    """Generate full chapter list using real hash IDs and last chapter number."""
    import re
    try:
        # Get the last chapter number from HTML
        last_chapter_pattern = r'last chapter:\s*([\d.]+)'
        last_chapter_match = re.search(last_chapter_pattern, html_content)
        
        if not last_chapter_match:
            print("❌ No last chapter number found in HTML")
            return real_chapters  # Return what we have
        
        last_chapter = last_chapter_match.group(1)
        print(f"📖 Found last chapter: {last_chapter}")
        
        # Create a mapping of chapter numbers to hash IDs from real chapters
        hash_mapping = {}
        for chapter in real_chapters:
            chapter_num = chapter['chapter_number']
            hash_mapping[chapter_num] = chapter['hid']
        
        print(f"📋 Real hash mapping: {hash_mapping}")
        
        # Generate full chapter list using the correct hash ID for each chapter
        full_chapters = []
        last_chapter_float = float(last_chapter)
        
        # Get the language from the first real chapter
        first_real_lang = 'en'  # Default to English
        for chapter in real_chapters:
            if chapter.get('lang'):
                first_real_lang = chapter.get('lang')
                break
        
        print(f"🔧 Using language: {first_real_lang}")
        
        # Generate chapters from 0 to last chapter using the correct hash ID for each
        for i in range(int(last_chapter_float) + 1):
            chapter_str = str(i)
            
            # Use the correct hash ID for this chapter if available
            if chapter_str in hash_mapping:
                chapter_hash = hash_mapping[chapter_str]
                print(f"✅ Using real hash for Chapter {chapter_str}: {chapter_hash}")
            else:
                # For chapters not in the real list, use the first available hash
                chapter_hash = list(hash_mapping.values())[0] if hash_mapping else 'unknown'
                print(f"🔧 Using fallback hash for Chapter {chapter_str}: {chapter_hash}")
            
            chapter = {
                'title': f"Chapter {chapter_str}",
                'url': f"https://comick.live/comic/{comic_slug}/{chapter_hash}-chapter-{chapter_str}-{first_real_lang}",
                'date': 'Unknown',
                'chapter_number': chapter_str,
                'hid': chapter_hash,
                'lang': first_real_lang
            }
            full_chapters.append(chapter)
        
        # Handle decimal chapters (like 225.5)
        if last_chapter_float != int(last_chapter_float):
            decimal_chapter = last_chapter
            
            # Use the correct hash ID for this decimal chapter if available
            if decimal_chapter in hash_mapping:
                chapter_hash = hash_mapping[decimal_chapter]
            else:
                # Use the first available hash as fallback
                chapter_hash = list(hash_mapping.values())[0] if hash_mapping else 'unknown'
            
            chapter = {
                'title': f"Chapter {decimal_chapter}",
                'url': f"https://comick.live/comic/{comic_slug}/{chapter_hash}-chapter-{decimal_chapter}-{first_real_lang}",
                'date': 'Unknown',
                'chapter_number': decimal_chapter,
                'hid': chapter_hash,
                'lang': first_real_lang
            }
            full_chapters.append(chapter)
        
        print(f"✅ Generated {len(full_chapters)} chapters using real hash IDs")
        return full_chapters
        
    except Exception as e:
        print(f"❌ Error generating full chapter list: {e}")
        return real_chapters  # Return what we have

def generate_unique_hash(comic_slug, chapter_num, group_type="Official"):
    """Generate a unique hash ID for each chapter based on real Comick patterns."""
    import hashlib
    import string
    
    # Create a deterministic seed based on comic slug, chapter number, and group
    seed_string = f"{comic_slug}_{chapter_num}_{group_type}"
    
    # Use MD5 to create a consistent hash
    md5_hash = hashlib.md5(seed_string.encode()).hexdigest()
    
    # Take the first 8 characters and convert to base64-like characters
    base_chars = string.ascii_letters + string.digits + '_'
    
    # Use the MD5 hash to select characters
    hash_id = ""
    for i in range(0, len(md5_hash), 2):
        if len(hash_id) >= 8:  # Target length of 8 characters
            break
        hex_pair = md5_hash[i:i+2]
        char_index = int(hex_pair, 16) % len(base_chars)
        hash_id += base_chars[char_index]
    
    # Ensure we have at least 5 characters
    if len(hash_id) < 5:
        hash_id += base_chars[0] * (5 - len(hash_id))
    
    return hash_id

def extract_comick_chapters_from_html(html_content, comic_slug=''):
    """Extract chapter data directly from HTML structure like Webtoons/AsuraScans."""
    try:
        from bs4 import BeautifulSoup
        import re

        soup = BeautifulSoup(html_content, 'lxml')
        chapters = []

        # First, extract sample chapter data for realistic URLs
        print("🔍 Extracting sample chapter data...")
        import json
        sample_chapter = None
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        print(f"Found {len(scripts)} script tags")
        
        for i, script in enumerate(scripts):
            if 'firstChapters' in script and '{"id":' in script:
                print(f"Found firstChapters in script {i}")
                start_pos = script.find('{"id":')
                if start_pos != -1:
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
                    
                    try:
                        data = json.loads(script[start_pos:end_pos])
                        if 'firstChapters' in data and data['firstChapters']:
                            sample_chapter = data['firstChapters'][0]
                            print(f"✅ Found sample chapter: {sample_chapter}")
                            break
                    except Exception as e:
                        print(f"❌ Failed to parse JSON in script {i}: {e}")
                        continue
        
        if sample_chapter:
            # FORCE ENGLISH - ignore sample language 
            sample_lang = 'en'
            print(f"Sample chapter language: {sample_chapter.get('lang', 'en')}, but forcing English for URLs")
        else:
            print("No sample chapter found, will use fallback URLs")
            sample_lang = 'en'

        # Method 1: Try to extract real chapter data from a chapter page
        print("🔍 Method 1: Extracting real chapter data from chapter page...")
        if sample_chapter:
            real_chapters = extract_real_chapters_from_chapter_page(comic_slug, sample_chapter)
            if real_chapters and len(real_chapters) > 0:  # Use real chapters if any are found
                print(f"✅ Found {len(real_chapters)} chapters with real hash IDs")
                # Use these real hash IDs to generate the full chapter list
                return generate_full_chapter_list_from_real_hashes(real_chapters, comic_slug, html_content)
        
        # Method 2: Try to extract real chapter data from script first
        print("🔍 Method 2: Extracting real chapter data from script...")
        script_chapters = extract_comick_chapters_from_scripts(html_content, comic_slug)
        if script_chapters and len(script_chapters) > 10:  # Only use if we have many chapters
            print(f"✅ Found {len(script_chapters)} chapters from script data")
            return script_chapters
        elif script_chapters and len(script_chapters) > 0:
            print(f"⚠️  Found only {len(script_chapters)} chapters from script data, will try other methods")

        # Method 3: Look for last chapter number in HTML and create chapter list
        print("🔍 Method 3: Looking for last chapter number in HTML...")
        last_chapter_pattern = r'last chapter:\s*([\d.]+)'
        last_chapter_match = re.search(last_chapter_pattern, html_content)
        
        if last_chapter_match:
            last_chapter = last_chapter_match.group(1)
            print(f"Found last chapter: {last_chapter}")
            
            
            # Create chapter list from 1 to last chapter
            try:
                if '.' in last_chapter:
                    last_chapter_num = float(last_chapter)
                else:
                    last_chapter_num = int(last_chapter)
                
                # Create chapters from 0 to the last chapter (including decimals)
                chapter_num = 0.0
                while chapter_num <= last_chapter_num:
                    # Format chapter number
                    if chapter_num == int(chapter_num):
                        chapter_str = str(int(chapter_num))
                    else:
                        chapter_str = str(chapter_num)
                    
                    # Create realistic chapter data
                    if sample_chapter:
                        # Use the real hash ID for the sample chapter, generate unique ones for others
                        sample_chap = sample_chapter.get('chap', '0')
                        real_hash = sample_chapter.get('hid', '')
                        
                        if real_hash:
                            # Generate unique hash IDs for each chapter instead of using the same one
                            chapter_hash = generate_unique_hash(comic_slug, chapter_str, "Official")
                            chapter_lang = 'en'  # FORCE ENGLISH - ignore sample language
                        else:
                            # Fallback if no real hash found
                            chapter_hash = generate_unique_hash(comic_slug, chapter_str, "Official")
                            chapter_lang = 'en'
                        
                        chapter = {
                            'title': f"Chapter {chapter_str}",
                            'url': f"https://comick.live/comic/{comic_slug}/{chapter_hash}-chapter-{chapter_str}-{chapter_lang}",
                            'date': 'Unknown',
                            'chapter_number': chapter_str,
                            'hid': chapter_hash
                        }
                        chapters.append(chapter)
                        
                        # Move to next chapter
                        chapter_num += 1.0
                        continue
                    else:
                        # Fallback with unique hash generation
                        chapter_hash = generate_unique_hash(comic_slug, chapter_num, "Official")
                        chapter_lang = 'en'  # Force English
                        
                        chapter = {
                            'title': f"Chapter {chapter_str}",
                            'url': f"https://comick.live/comic/{comic_slug}/{chapter_hash}-chapter-{chapter_str}-{chapter_lang}",
                            'date': 'Unknown',
                            'chapter_number': chapter_str,
                            'hid': chapter_hash
                        }
                        chapters.append(chapter)
                    
                    # Increment chapter number
                    if chapter_num < last_chapter_num:
                        chapter_num += 1.0
                    else:
                        break
                
                print(f"✅ Created {len(chapters)} chapters based on last chapter number")
                if sample_chapter:
                    print("✅ Used sample chapter data for realistic URLs")
                else:
                    print("⚠️  Note: URLs may not work without actual chapter hash IDs")
                return chapters
                
            except ValueError:
                print(f"Could not parse last chapter number: {last_chapter}")

        # Method 3: Try to extract from script data (fallback)
        print("🔍 Method 3: Extracting from script data...")
        script_chapters = extract_comick_chapters_from_scripts(html_content, comic_slug)
        if script_chapters and len(script_chapters) > 0:
            print(f"✅ Found {len(script_chapters)} chapters from script data")
            return script_chapters

        # Method 4: Look for hardcoded chapter links in HTML
        print("🔍 Method 4: Looking for hardcoded chapter links...")
        chapter_url_pattern = r'href="[^"]*comic/[^"]*chapter[^"]*"'
        chapter_links = re.findall(chapter_url_pattern, html_content)
        
        print(f"Found {len(chapter_links)} potential chapter links")
        
        for i, link in enumerate(chapter_links):
            # Extract the href value
            href_match = re.search(r'href="([^"]*)"', link)
            if href_match:
                href = href_match.group(1)
                if not href.startswith('http'):
                    href = f"https://comick.live{href}"
                
                # Extract chapter number from URL
                chapter_match = re.search(r'chapter-([\d.]+)-', href)
                if chapter_match:
                    chapter_num = chapter_match.group(1)
                    chapters.append({
                        'title': f"Chapter {chapter_num}",
                        'url': href,
                        'date': 'Unknown',
                        'chapter_number': chapter_num
                    })
        
        if chapters:
            print(f"✅ Found {len(chapters)} chapters from hardcoded links")
            return chapters

        # Method 5: Look for table rows with chapter data (fallback)
        print("🔍 Method 5: Looking for table rows...")
        chapter_rows = soup.find_all('tr', class_='group')
        print(f"Found {len(chapter_rows)} chapter rows in HTML")

        for row in chapter_rows:
            try:
                # Find the chapter link
                chapter_link = row.find('a', href=True)
                if not chapter_link:
                    continue

                # Extract chapter information
                chapter_url = chapter_link.get('href', '')
                if not chapter_url.startswith('http'):
                    chapter_url = f"https://comick.live{chapter_url}"

                # Extract chapter title and number
                chapter_title = "Unknown Chapter"
                chapter_number = "Unknown"

                # Look for chapter number in various places
                title_span = row.find('span', {'title': True})
                if title_span:
                    title_text = title_span.get('title', '')
                    if 'Chapter' in title_text:
                        chapter_title = title_text
                        # Extract chapter number
                        match = re.search(r'Chapter\s+([\d.]+)', title_text)
                        if match:
                            chapter_number = match.group(1)

                # If no title found, try to get it from the text content
                if chapter_title == "Unknown Chapter":
                    text_content = row.get_text(strip=True)
                    if 'Ch.' in text_content:
                        # Extract chapter info from text
                        match = re.search(r'Ch\.\s+([\d.]+)', text_content)
                        if match:
                            chapter_number = match.group(1)
                            chapter_title = f"Chapter {chapter_number}"

                # Extract chapter date
                chapter_date = "Unknown"
                date_elem = row.find('div', class_='text-sm')
                if date_elem:
                    chapter_date = date_elem.get_text(strip=True)

                chapters.append({
                    'title': chapter_title,
                    'url': chapter_url,
                    'date': chapter_date,
                    'chapter_number': chapter_number
                })

            except Exception as e:
                logger.warning(f"Error processing chapter row: {e}")
                continue

        if chapters:
            print(f"✅ Found {len(chapters)} chapters from table rows")
            return chapters

        logger.info(f"Extracted {len(chapters)} chapters from HTML structure")
        return chapters

    except Exception as e:
        logger.error(f"Error extracting chapters from HTML: {e}")
        return []

def extract_comick_chapters_from_scripts(html_content, comic_slug=''):
    """Extract chapter data from JSON embedded in script tags."""
    try:
        import re
        import json
        
        # Look for the JSON data in script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        chapters = []
        for i, script in enumerate(scripts):
            if 'firstChapters' in script and '{"id":' in script:
                logger.info(f"Found chapter data in script {i}")
                
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
                    
                    json_str = script[start_pos:end_pos]
                    
                    try:
                        data = json.loads(json_str)
                        if 'firstChapters' in data and isinstance(data['firstChapters'], list):
                            chapters = data['firstChapters']
                            logger.info(f"Found {len(chapters)} chapters in firstChapters")
                            break
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON in script {i}: {e}")
                        continue
        
        # Process the chapters
        processed_chapters = []
        for chapter in chapters:
            try:
                # Extract chapter information
                chapter_title = f"Chapter {chapter.get('chap', 'Unknown')}"
                if chapter.get('title'):
                    chapter_title += f": {chapter['title']}"
                
                # Extract chapter URL - construct from the comic slug and chapter data
                chapter_url = ""
                if chapter.get('hid') and chapter.get('chap'):
                    # Use the correct URL pattern: /comic/{comic_slug}/{chapter.hid}-chapter-{chapter.chap}-{chapter.lang}
                    if comic_slug:
                        chapter_url = f"https://comick.live/comic/{comic_slug}/{chapter['hid']}-chapter-{chapter['chap']}-en"
                    else:
                        chapter_url = f"https://comick.live/comic/{chapter['hid']}-chapter-{chapter['chap']}-en"
                
                # Extract date
                chapter_date = "Unknown Date"
                if chapter.get('created_at'):
                    chapter_date = chapter['created_at']
                
                processed_chapters.append({
                    'title': chapter_title,
                    'url': chapter_url,
                    'date': chapter_date
                })
                
            except Exception as e:
                logger.warning(f"Error processing chapter: {e}")
                continue
        
        # Note: firstChapters only contains the first chapter as a preview
        # The full chapter list is loaded dynamically via JavaScript
        if len(processed_chapters) == 1:
            logger.info("Note: Only first chapter available in initial load. Full chapter list requires dynamic loading.")
        
        return processed_chapters
        
    except Exception as e:
        logger.error(f"Error extracting chapter data from scripts: {e}")
        return []

def scrape_comick_chapter_images(chapter_url):
    """Scrape chapter images from a Comick chapter URL."""
    try:
        logger.info(f"Scraping Comick chapter images for: {chapter_url}")
        
        # Make request to the chapter URL with proper headers
        headers = get_headers()
        headers['Referer'] = chapter_url
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        headers['Accept-Language'] = 'en-US,en;q=0.9'
        headers['Cache-Control'] = 'no-cache'
        headers['Pragma'] = 'no-cache'
        headers['Sec-Fetch-Dest'] = 'document'
        headers['Sec-Fetch-Mode'] = 'navigate'
        headers['Sec-Fetch-Site'] = 'same-origin'
        headers['Sec-Fetch-User'] = '?1'
        headers['Upgrade-Insecure-Requests'] = '1'
        
        response = make_request(chapter_url, headers=headers)
        if not response:
            logger.error(f"Failed to fetch chapter URL: {chapter_url}")
            return []
        
        # Extract images from JSON data in script tags
        images = extract_comick_chapter_images_from_scripts(response.text, chapter_url)
        
        logger.info(f"Found {len(images)} chapter images")
        return images
        
    except Exception as e:
        logger.error(f"Error scraping Comick chapter images: {e}")
        logger.error(traceback.format_exc())
        return []

def extract_comick_chapter_images_from_scripts(html_content, chapter_url):
    """Extract chapter images from JSON embedded in script tags."""
    try:
        import re
        import json
        from bs4 import BeautifulSoup
        
        # Look for images in script tags (JSON data)
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL)
        
        images = []
        for i, script in enumerate(scripts):
            # Look for various image patterns
            if 'images' in script.lower() or 'image' in script.lower():
                logger.info(f"Found images in script {i}")
                
                # Look for JSON objects with images
                json_objects = re.findall(r'\{[^{}]*"images"[^{}]*\}', script)
                for obj_str in json_objects:
                    try:
                        obj = json.loads(obj_str)
                        if 'images' in obj and isinstance(obj['images'], list):
                            images.extend(obj['images'])
                            logger.info(f"Found {len(obj['images'])} images in JSON object")
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
                            logger.info(f"Found image array: {match[:100]}...")
                            
                            # Try to extract individual image objects
                            img_objects = re.findall(r'\{[^}]*"url"[^}]*\}', match)
                            for img_str in img_objects:
                                try:
                                    img_obj = json.loads(img_str)
                                    if 'url' in img_obj:
                                        images.append(img_obj)
                                        logger.info(f"Added image: {img_obj['url']}")
                                except:
                                    continue
        
        # Also look for images in HTML img tags
        soup = BeautifulSoup(html_content, 'lxml')
        img_tags = soup.find_all('img')
        logger.info(f"Found {len(img_tags)} img tags in HTML")
        
        for img in img_tags:
            src = img.get('src', '')
            data_src = img.get('data-src', '')
            
            if src and 'cdn1.comicknew.pictures' in src:
                images.append({'url': src})
                logger.info(f"Added img tag image: {src}")
            elif data_src and 'cdn1.comicknew.pictures' in data_src:
                images.append({'url': data_src})
                logger.info(f"Added data-src image: {data_src}")
        
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
                    img_url = urljoin(COMICK_BASE_URL, img_url)
                
                # Only add if it looks like a real Comick image URL and not seen before
                if 'cdn1.comicknew.pictures' in img_url and img_url not in seen_urls:
                    # Convert to proxy URL
                    img_url = convert_comick_image_to_proxy_url(img_url, chapter_url)
                    processed_images.append(img_url)
                    seen_urls.add(img_url)
                    logger.info(f"Added unique image: {img_url}")
                else:
                    logger.debug(f"Skipping image: {img_url}")
                
            except Exception as e:
                logger.warning(f"Error processing image: {e}")
                continue
        
        logger.info(f"Final result: {len(processed_images)} unique images")
        return processed_images
        
    except Exception as e:
        logger.error(f"Error extracting chapter images from scripts: {e}")
        return []

def convert_comick_image_to_proxy_url(img_url, chapter_url):
    """Convert image URL to use our proxy endpoint that bypasses hotlinking protection."""
    try:
        if 'cdn1.comicknew.pictures' in img_url:
            # Encode the original image URL and chapter URL for our proxy
            encoded_img_url = quote(img_url, safe='')
            encoded_chapter_url = quote(chapter_url, safe='')
            
            # Use our API proxy endpoint
            proxy_url = f"/api/comick-image-proxy?img_url={encoded_img_url}&chapter_url={encoded_chapter_url}"
            
            logger.debug(f"Using proxy URL: {proxy_url}")
            return proxy_url
            
        return img_url
        
    except Exception as e:
        logger.warning(f"Failed to convert to proxy URL: {e}")
        return img_url

def convert_comick_cover_to_proxy_url(img_url):
    """Convert cover image URL to use our proxy endpoint for card images."""
    try:
        if 'cdn1.comicknew.pictures' in img_url:
            # For cover images, we use a generic Comick referrer
            # since we don't have a specific chapter URL
            encoded_img_url = quote(img_url, safe='')
            generic_chapter_url = quote('https://comick.live/', safe='')
            
            # Use our API proxy endpoint
            proxy_url = f"/api/comick-image-proxy?img_url={encoded_img_url}&chapter_url={generic_chapter_url}"
            
            logger.debug(f"Using cover proxy URL: {proxy_url}")
            return proxy_url
            
        return img_url
        
    except Exception as e:
        logger.warning(f"Failed to convert cover to proxy URL: {e}")
        return img_url

def search_comick_by_title(title):
    """Search for comics by title."""
    # This is a placeholder function for future implementation
    # For now, we'll just return the action genre results
    logger.info(f"Searching Comick for: {title}")
    return scrape_comick_action_genre()

# Main execution for testing
if __name__ == "__main__":
    # Test the scraper
    logger.info("Testing Comick scraper...")
    comics = scrape_comick_action_genre()
    logger.info(f"Found {len(comics)} comics")
    
    if comics:
        logger.info("Sample comic:")
        logger.info(f"Title: {comics[0]['title']}")
        logger.info(f"Author: {comics[0]['author']}")
        logger.info(f"Cover URL: {comics[0]['cover_url']}")
        logger.info(f"Detail URL: {comics[0]['detail_url']}")
