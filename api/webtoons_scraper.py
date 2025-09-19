#!/usr/bin/env python3
"""
Webtoons Scraper for ManhwaVerse
================================

A dedicated scraper for webtoons.com using requests and BeautifulSoup.
Scrapes action genre webtoons and their details.

Author: ManhwaVerse Development Team
Date: 2025
Version: 1.0
"""

import logging
import time
import random
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
WEBTOONS_BASE_URL = "https://www.webtoons.com"
ACTION_GENRE_URL = "https://www.webtoons.com/en/genres/action?sortOrder=MANA"
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

def scrape_webtoons_action_genre():
    """Scrape action genre webtoons from webtoons.com."""
    try:
        logger.info("Starting Webtoons action genre scraping")
        
        # Make request to action genre page
        logger.info(f"Fetching: {ACTION_GENRE_URL}")
        response = make_request(ACTION_GENRE_URL)
        
        if not response:
            logger.error("Failed to fetch Webtoons action genre page")
            return []
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find webtoon list - try multiple selectors
        webtoon_list = None
        selectors = [
            'ul.webtoon_list',
            'ul[class*="webtoon"]',
            'ul[class*="list"]',
            '.webtoon_list'
        ]
        
        for selector in selectors:
            webtoon_list = soup.select_one(selector)
            if webtoon_list:
                logger.info(f"Found webtoon list with selector: {selector}")
                break
        
        if not webtoon_list:
            logger.error("Could not find webtoon_list container")
            # Try to find any list items as fallback
            webtoon_items = soup.find_all('li')
            if webtoon_items:
                logger.info(f"Found {len(webtoon_items)} list items as fallback")
                webtoons = []
                for item in webtoon_items[:20]:  # Limit to first 20 items
                    try:
                        webtoon_data = parse_webtoon_item(item)
                        if webtoon_data:
                            webtoons.append(webtoon_data)
                    except Exception as e:
                        logger.warning(f"Error parsing webtoon item: {e}")
                        continue
                return webtoons
            return []
        
        # Parse webtoon items
        webtoon_items = webtoon_list.find_all('li')
        logger.info(f"Found {len(webtoon_items)} webtoon items")
        
        webtoons = []
        for item in webtoon_items:
            try:
                webtoon_data = parse_webtoon_item(item)
                if webtoon_data:
                    webtoons.append(webtoon_data)
            except Exception as e:
                logger.warning(f"Error parsing webtoon item: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(webtoons)} webtoons")
        return webtoons
        
    except Exception as e:
        logger.error(f"Error scraping Webtoons action genre: {e}")
        logger.error(traceback.format_exc())
        return []

def parse_webtoon_item(item):
    """Parse a single webtoon item from the list."""
    try:
        # Extract title - try multiple selectors
        title = ""
        title_selectors = [
            'strong.title',
            '.title',
            'strong[class*="title"]',
            'h3',
            'h4',
            'a[title]'
        ]
        
        for selector in title_selectors:
            title_element = item.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                if not title and title_element.get('title'):
                    title = title_element.get('title').strip()
                if title:
                    break
        
        if not title:
            return None
        
        # Extract cover image - try multiple selectors and attributes
        cover_url = ""
        img_selectors = [
            'img',
            '.thmb img',
            'img[src*="webtoon"]',
            'img[src*="pstatic"]'
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
                            cover_url = urljoin(WEBTOONS_BASE_URL, cover_url)
                        break
                if cover_url:
                    break
        
        # Convert cover image to use proxy if it's a Webtoons CDN image
        if cover_url and 'webtoon-phinf.pstatic.net' in cover_url:
            cover_url = convert_cover_to_proxy_url(cover_url)
        
        # Extract detail URL
        detail_url = ""
        link_element = item.find('a', href=True)
        if link_element:
            detail_url = link_element['href']
            if detail_url and not detail_url.startswith('http'):
                detail_url = urljoin(WEBTOONS_BASE_URL, detail_url)
        
        # Extract author - try multiple selectors
        author = "Unknown"
        author_selectors = [
            'div.author',
            '.author',
            'div[class*="author"]',
            '.creator',
            '.artist'
        ]
        
        for selector in author_selectors:
            author_element = item.select_one(selector)
            if author_element:
                author = author_element.get_text(strip=True)
                if author:
                    break
        
        # Extract latest chapter info if available
        latest_chapter = "N/A"
        chapter_selectors = [
            '.episode',
            '.chapter',
            '.latest',
            'span[class*="episode"]',
            'span[class*="chapter"]'
        ]
        
        for selector in chapter_selectors:
            chapter_element = item.select_one(selector)
            if chapter_element:
                latest_chapter = chapter_element.get_text(strip=True)
                if latest_chapter:
                    break
        
        # Create webtoon data
        webtoon_data = {
            'title': title,
            'cover_url': cover_url,
            'detail_url': detail_url,
            'author': author,
            'source': 'Webtoons',
            'latest_chapter': latest_chapter,
            'rating': 'N/A',
            'genres': ['Action'],
            'status': 'Ongoing'
        }
        
        return webtoon_data
        
    except Exception as e:
        logger.warning(f"Error parsing webtoon item: {e}")
        return None

def scrape_webtoons_details(detail_url):
    """Scrape detailed information for a specific webtoon."""
    try:
        logger.info(f"Scraping Webtoons details for: {detail_url}")
        
        # Make request to detail page
        response = make_request(detail_url)
        if not response:
            logger.error("Failed to fetch Webtoons detail page")
            return None
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title - try multiple selectors
        title = "Unknown Title"
        title_selectors = [
            'h1.subj',
            'h1[class*="subj"]',
            'h1',
            '.subj'
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                break
        
        # Extract cover image - try multiple selectors
        cover_image = ""
        cover_selectors = [
            'span.thmb img',
            '.thmb img',
            'img[class*="thmb"]',
            '.cover img',
            'img[alt*="cover"]'
        ]
        
        for selector in cover_selectors:
            img_tag = soup.select_one(selector)
            if img_tag:
                cover_image = img_tag.get('src', '')
                if cover_image and not cover_image.startswith('http'):
                    cover_image = urljoin(WEBTOONS_BASE_URL, cover_image)
                break
        
        # Convert cover image to use proxy if it's a Webtoons CDN image
        if cover_image and 'webtoon-phinf.pstatic.net' in cover_image:
            cover_image = convert_cover_to_proxy_url(cover_image)
        
        # Extract description - try multiple selectors
        description = "No description available"
        desc_selectors = [
            'p.summary',
            '.summary',
            'p[class*="summary"]',
            '.description',
            'p[class*="description"]'
        ]
        
        for selector in desc_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                description = desc_element.get_text(strip=True)
                break
        
        # Extract genres - try multiple selectors
        genres = ['Action']  # Default to Action since we're scraping action genre
        genre_selectors = [
            'h2.genre',
            '.genre',
            'h2[class*="genre"]',
            '.genres',
            '.tags'
        ]
        
        for selector in genre_selectors:
            genre_element = soup.select_one(selector)
            if genre_element:
                genre_text = genre_element.get_text(strip=True)
                if genre_text:
                    genres = [g.strip() for g in genre_text.split(',') if g.strip()]
                break
        
        # Extract author - try multiple selectors
        author = "Unknown"
        author_selectors = [
            'div.author_area',
            '.author_area',
            'div[class*="author"]',
            '.author',
            '.creator'
        ]
        
        for selector in author_selectors:
            author_element = soup.select_one(selector)
            if author_element:
                author = author_element.get_text(strip=True)
                break
        
        # Extract chapters from all pages with pagination
        chapters = []
        current_page = 1
        max_pages = 10  # Limit to prevent infinite loops
        
        while current_page <= max_pages:
            logger.info(f"Scraping chapters from page {current_page}")
            
            # Get the current page URL - Webtoons uses different pagination structure
            if current_page == 1:
                page_url = detail_url
            else:
                # Webtoons pagination uses &page=N format
                if '?' in detail_url:
                    page_url = f"{detail_url}&page={current_page}"
                else:
                    page_url = f"{detail_url}?page={current_page}"
            
            # Make request to the page
            page_response = make_request(page_url)
            if not page_response:
                logger.warning(f"Failed to fetch page {current_page}")
                break
                
            page_soup = BeautifulSoup(page_response.text, 'html.parser')
            
            # Find chapter list on this page
            chapter_list = page_soup.find('ul', {'id': '_listUl'})
            if not chapter_list:
                logger.info(f"No chapter list found on page {current_page}, stopping pagination")
                break
                
            chapter_items = chapter_list.find_all('li', class_='_episodeItem')
            if not chapter_items:
                logger.info(f"No chapter items found on page {current_page}, stopping pagination")
                break
                
            # Extract chapters from this page
            page_chapters = []
            for chapter_item in chapter_items:
                try:
                    link = chapter_item.find('a', href=True)
                    if link:
                        chapter_title = "Unknown Chapter"
                        chapter_date = "Unknown Date"
                        
                        # Extract chapter title - look for the episode title
                        title_elem = chapter_item.find('span', class_='subj')
                        if not title_elem:
                            title_elem = chapter_item.find('span', class_='tx')
                        if not title_elem:
                            title_elem = chapter_item.find('span', class_='title')
                        if not title_elem:
                            title_elem = chapter_item.find('a')
                        
                        if title_elem:
                            chapter_title = title_elem.get_text(strip=True)
                        
                        # Extract chapter date
                        date_elem = chapter_item.find('span', class_='date')
                        if not date_elem:
                            date_elem = chapter_item.find('span', class_='time')
                        
                        if date_elem:
                            chapter_date = date_elem.get_text(strip=True)
                        
                        # Ensure URL is absolute
                        chapter_url = link['href']
                        if not chapter_url.startswith('http'):
                            chapter_url = urljoin(WEBTOONS_BASE_URL, chapter_url)
                        
                        page_chapters.append({
                            'title': chapter_title,
                            'date': chapter_date,
                            'url': chapter_url
                        })
                except Exception as e:
                    logger.warning(f"Error parsing chapter: {e}")
                    continue
            
            if not page_chapters:
                logger.info(f"No chapters found on page {current_page}, stopping pagination")
                break
                
            chapters.extend(page_chapters)
            logger.info(f"Found {len(page_chapters)} chapters on page {current_page}")
            
            # Check if there's a next page by looking at pagination
            # Webtoons shows page numbers like "1 2 3 4 5 6 7 8 9"
            pagination_links = page_soup.find_all('a', href=True)
            next_page_found = False
            
            for link in pagination_links:
                href = link.get('href', '')
                if f'page={current_page + 1}' in href or f'&page={current_page + 1}' in href:
                    next_page_found = True
                    break
            
            if not next_page_found:
                logger.info(f"No next page found after page {current_page}, stopping pagination")
                break
                
            current_page += 1
        
        # Create detailed webtoon data
        webtoon_details = {
            'title': title,
            'cover_image': cover_image,
            'description': description,
            'rating': 'N/A',  # Webtoons doesn't show ratings on detail pages
            'status': 'Ongoing',
            'genres': genres,
            'author': author,
            'chapters': chapters
        }
        
        logger.info(f"Successfully scraped details for: {title}")
        return webtoon_details
        
    except Exception as e:
        logger.error(f"Error scraping Webtoons details for {detail_url}: {e}")
        logger.error(traceback.format_exc())
        return None

def search_webtoons_by_title(title):
    """Search for webtoons by title."""
    # This is a placeholder function for future implementation
    # For now, we'll just return the action genre results
    logger.info(f"Searching Webtoons for: {title}")
    return scrape_webtoons_action_genre()

def scrape_webtoons_chapter_images(chapter_url):
    """Scrape chapter images from a Webtoons episode URL."""
    try:
        logger.info(f"Scraping Webtoons chapter images for: {chapter_url}")
        
        # Make request to the chapter URL with proper headers
        headers = get_headers()
        headers['Referer'] = chapter_url  # Use the specific chapter URL as referer
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
        
        # Find the image container using the correct selector
        # Look for div with classes containing both viewer_img and _img_viewer_area
        image_container = soup.find('div', class_=lambda x: x and 'viewer_img' in x and '_img_viewer_area' in x)
        if not image_container:
            # Fallback to the old selector if the new one doesn't work
            image_container = soup.find('div', {'id': '_imageList'})
            if not image_container:
                logger.error("Could not find image container with viewer_img and _img_viewer_area classes")
                return []
        
        # Extract all images using data-url attribute
        images = []
        img_elements = image_container.find_all('img', class_='_images')
        
        for img in img_elements:
            # Get data-url attribute (not src) for actual images
            img_url = img.get('data-url')
            if not img_url:
                # Fallback to src if data-url is not available
                img_url = img.get('src')
            
            if img_url:
                # Filter out placeholder/loading images
                if any(placeholder in img_url.lower() for placeholder in [
                    'bg_transparency.png', 'placeholder', 'default', 'loading', 'transparent'
                ]):
                    logger.debug(f"Skipping placeholder image: {img_url}")
                    continue
                
                # Remove quality compression to get full quality images
                if '?type=q90' in img_url:
                    img_url = img_url.split('?type=q90')[0]
                
                # Ensure it's a full URL
                if not img_url.startswith('http'):
                    img_url = urljoin(WEBTOONS_BASE_URL, img_url)
                
                # Convert to the proper CDN URL format that bypasses hotlinking protection
                img_url = convert_to_proper_cdn_url(img_url, chapter_url)
                
                images.append(img_url)
        
        logger.info(f"Found {len(images)} actual chapter images (filtered out placeholders)")
        return images
        
    except Exception as e:
        logger.error(f"Error scraping Webtoons chapter images: {e}")
        logger.error(traceback.format_exc())
        return []

def convert_to_proper_cdn_url(img_url, chapter_url):
    """Convert image URL to use our proxy endpoint that bypasses hotlinking protection."""
    try:
        # Instead of trying to access the image directly, we'll use our API proxy
        # This will handle the proper headers and authentication
        if 'webtoon-phinf.pstatic.net' in img_url:
            # Encode the original image URL and chapter URL for our proxy
            import urllib.parse
            encoded_img_url = urllib.parse.quote(img_url, safe='')
            encoded_chapter_url = urllib.parse.quote(chapter_url, safe='')
            
            # Use our API proxy endpoint
            proxy_url = f"/api/webtoons-image-proxy?img_url={encoded_img_url}&chapter_url={encoded_chapter_url}"
            
            logger.debug(f"Using proxy URL: {proxy_url}")
            return proxy_url
            
        return img_url
        
    except Exception as e:
        logger.warning(f"Failed to convert to proxy URL: {e}")
        return img_url

def convert_cover_to_proxy_url(img_url):
    """Convert cover image URL to use our proxy endpoint for card images."""
    try:
        if 'webtoon-phinf.pstatic.net' in img_url:
            # For cover images, we use a generic Webtoons referrer
            # since we don't have a specific chapter URL
            import urllib.parse
            encoded_img_url = urllib.parse.quote(img_url, safe='')
            generic_chapter_url = urllib.parse.quote('https://www.webtoons.com/', safe='')
            
            # Use our API proxy endpoint
            proxy_url = f"/api/webtoons-image-proxy?img_url={encoded_img_url}&chapter_url={generic_chapter_url}"
            
            logger.debug(f"Using cover proxy URL: {proxy_url}")
            return proxy_url
            
        return img_url
        
    except Exception as e:
        logger.warning(f"Failed to convert cover to proxy URL: {e}")
        return img_url

# Main execution for testing
if __name__ == "__main__":
    # Test the scraper
    logger.info("Testing Webtoons scraper...")
    webtoons = scrape_webtoons_action_genre()
    logger.info(f"Found {len(webtoons)} webtoons")
    
    if webtoons:
        logger.info("Sample webtoon:")
        logger.info(f"Title: {webtoons[0]['title']}")
        logger.info(f"Author: {webtoons[0]['author']}")
        logger.info(f"Cover URL: {webtoons[0]['cover_url']}")
        logger.info(f"Detail URL: {webtoons[0]['detail_url']}")
