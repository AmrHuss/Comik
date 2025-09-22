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
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title
        title = "Unknown Title"
        title_element = soup.find('h1')
        if title_element:
            title = title_element.get_text(strip=True)
        
        # Extract cover image
        cover_image = ""
        img_element = soup.find('img', class_=lambda x: x and 'select-none' in x and 'rounded-md' in x)
        if img_element:
            cover_image = img_element.get('src', '')
            if cover_image and not cover_image.startswith('http'):
                cover_image = urljoin(COMICK_BASE_URL, cover_image)
        
        # Convert cover image to use proxy if it's a Comick CDN image
        if cover_image and 'cdn1.comicknew.pictures' in cover_image:
            cover_image = convert_comick_cover_to_proxy_url(cover_image)
        
        # Extract description
        description = "No description available"
        desc_element = soup.find('p', class_=lambda x: x and 'prose' in x)
        if desc_element:
            description = desc_element.get_text(strip=True)
        
        # Extract genres
        genres = ['Action']  # Default to Action since we're scraping action genre
        genre_elements = soup.find_all('span', class_=lambda x: x and 'genre' in x.lower())
        if genre_elements:
            genres = [elem.get_text(strip=True) for elem in genre_elements]
        
        # Extract author
        author = "Unknown"
        author_elements = soup.find_all('span', class_=lambda x: x and 'text-gray' in x)
        for elem in author_elements:
            text = elem.get_text(strip=True)
            if text and not any(keyword in text.lower() for keyword in ['chapters', 'chapter', 'uploaded', 'rating', 'follow']):
                author = text
                break
        
        # Extract chapters from table
        chapters = []
        tbody = soup.find('tbody')
        if tbody:
            chapter_rows = tbody.find_all('tr')
            for row in chapter_rows:
                try:
                    # Extract chapter number/title
                    chapter_title = "Unknown Chapter"
                    title_span = row.find('span', class_=lambda x: x and 'font-semibold' in x)
                    if title_span:
                        chapter_title = title_span.get_text(strip=True)
                    
                    # Extract chapter URL
                    chapter_url = ""
                    link = row.find('a', href=True)
                    if link:
                        chapter_url = link['href']
                        if chapter_url and not chapter_url.startswith('http'):
                            chapter_url = urljoin(COMICK_BASE_URL, chapter_url)
                    
                    if chapter_url:
                        chapters.append({
                            'title': chapter_title,
                            'url': chapter_url,
                            'date': 'Unknown Date'
                        })
                except Exception as e:
                    logger.warning(f"Error parsing chapter row: {e}")
                    continue
        
        # Create detailed comic data
        comic_details = {
            'title': title,
            'cover_image': cover_image,
            'description': description,
            'rating': 'N/A',
            'status': 'Ongoing',
            'genres': genres,
            'author': author,
            'chapters': chapters
        }
        
        logger.info(f"Successfully scraped details for: {title}")
        return comic_details
        
    except Exception as e:
        logger.error(f"Error scraping Comick details for {detail_url}: {e}")
        logger.error(traceback.format_exc())
        return None

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
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all chapter images
        images = []
        img_elements = soup.find_all('img', class_=lambda x: x and 'mx-auto' in x and 'select-none' in x and 'chapter' in x)
        
        for img in img_elements:
            img_url = img.get('src')
            if not img_url:
                continue
            
            # Filter out placeholder/loading images
            if any(placeholder in img_url.lower() for placeholder in [
                'placeholder', 'default', 'loading', 'transparent',
                'blank', 'empty', '1x1', 'pixel', 'spacer'
            ]):
                logger.debug(f"Skipping placeholder image: {img_url}")
                continue
            
            # Ensure it's a full URL
            if not img_url.startswith('http'):
                img_url = urljoin(COMICK_BASE_URL, img_url)
            
            # Only add if it looks like a real Comick image URL
            if 'cdn1.comicknew.pictures' in img_url:
                # Convert to proxy URL
                img_url = convert_comick_image_to_proxy_url(img_url, chapter_url)
                images.append(img_url)
            else:
                logger.debug(f"Skipping non-Comick image: {img_url}")
        
        logger.info(f"Found {len(images)} chapter images")
        return images
        
    except Exception as e:
        logger.error(f"Error scraping Comick chapter images: {e}")
        logger.error(traceback.format_exc())
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
