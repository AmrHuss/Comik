#!/usr/bin/env python3
"""
MangaPark Scraper Module
========================

A dedicated scraper for MangaPark.net that extracts manga data from
the latest pages (1-5) and provides detailed manga information.

Author: ManhwaVerse Development Team
Date: 2025
Version: 1.0
"""

import logging
import requests
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
import traceback
import time
import random
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MANGA_PARK_BASE_URL = "https://mangapark.net"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 1  # seconds

def get_headers():
    """Get standardized headers for HTTP requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://mangapark.net/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin'
    }

def make_request(url, retries=MAX_RETRIES):
    """Make HTTP request with retry logic and proper error handling."""
    for attempt in range(retries):
        try:
            # Add random delay to avoid being blocked
            if attempt > 0:
                delay = DELAY_BETWEEN_REQUESTS + random.uniform(0.5, 1.5)
                time.sleep(delay)
            
            response = requests.get(
                url, 
                headers=get_headers(), 
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                verify=False  # Disable SSL verification for problematic sites
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
            if attempt == retries - 1:
                logger.error(f"All {retries} attempts failed for {url}")
                return None
    return None

def scrape_mangapark_latest():
    """Scrape latest manga from MangaPark pages 1-5."""
    all_manga = []
    
    try:
        logger.info("Starting MangaPark latest manga scraping...")
        
        # Scrape pages 1-5
        for page in range(1, 6):
            page_url = f"{MANGA_PARK_BASE_URL}/latest/{page}"
            logger.info(f"Scraping page {page}: {page_url}")
            
            response = make_request(page_url)
            if not response:
                logger.warning(f"Failed to fetch page {page}")
                continue
            
            soup = BeautifulSoup(response.content, 'lxml')
            page_manga = parse_mangapark_cards(soup, page)
            all_manga.extend(page_manga)
            
            logger.info(f"Found {len(page_manga)} manga on page {page}")
            
            # Add delay between pages to be respectful
            if page < 5:
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Remove duplicates based on detail_url
        unique_manga = []
        seen_urls = set()
        for manga in all_manga:
            if manga['detail_url'] not in seen_urls:
                unique_manga.append(manga)
                seen_urls.add(manga['detail_url'])
        
        logger.info(f"Successfully scraped {len(unique_manga)} unique manga from MangaPark")
        return unique_manga
        
    except Exception as e:
        logger.error(f"Error scraping MangaPark latest: {e}")
        logger.error(traceback.format_exc())
        return []

def parse_mangapark_cards(soup, page_num):
    """Parse manga cards from MangaPark page."""
    manga_list = []
    
    try:
        # Find the main grid container
        grid_container = soup.select_one('div.grid.gap-5.grid-cols-1.border-t.border-t-base-200.pt-3.md\\:grid-cols-2.lg\\:grid-cols-3')
        
        if not grid_container:
            logger.warning(f"Could not find grid container on page {page_num}")
            return manga_list
        
        # Find all manga items
        manga_items = grid_container.select('div.flex.border-b.border-b-base-200.pb-3')
        logger.info(f"Found {len(manga_items)} manga items on page {page_num}")
        
        for item in manga_items:
            try:
                manga_data = parse_single_mangapark_item(item)
                if manga_data:
                    manga_list.append(manga_data)
            except Exception as e:
                logger.warning(f"Error parsing manga item: {e}")
                continue
        
        return manga_list
        
    except Exception as e:
        logger.error(f"Error parsing MangaPark cards on page {page_num}: {e}")
        return []

def parse_single_mangapark_item(item):
    """Parse a single manga item from MangaPark."""
    try:
        # Extract title and detail URL
        title_link = item.select_one('h3.font-bold a.link-hover.link-pri')
        if not title_link:
            return None
        
        title = title_link.get_text(strip=True)
        detail_url = urljoin(MANGA_PARK_BASE_URL, title_link['href'])
        
        # Extract cover image
        cover_img = item.select_one('div.shrink-0 img')
        cover_url = ""
        if cover_img:
            cover_url = cover_img.get('src', '')
            if cover_url and not cover_url.startswith('http'):
                # Handle relative URLs like /thumb/W600/...
                if cover_url.startswith('/'):
                    cover_url = MANGA_PARK_BASE_URL + cover_url
                else:
                    cover_url = urljoin(MANGA_PARK_BASE_URL, cover_url)
        
        if not cover_url:
            return None
        
        # Extract latest chapter first
        latest_chapter = "N/A"
        chapter_link = item.select_one('div.flex.flex-nowrap.justify-between a.link-hover.link-primary')
        if chapter_link:
            latest_chapter = chapter_link.get_text(strip=True)
        
        # Extract rating - try multiple selectors
        rating = "N/A"
        rating_selectors = [
            'span.flex.flex-nowrap.items-center.text-yellow-500 span.ml-1.font-bold',
            'span.text-yellow-500.font-bold',
            '.rating',
            '.score',
            'span[class*="rating"]',
            'div[class*="rating"]',
            '[class*="star"]',
            '[class*="score"]'
        ]
        for selector in rating_selectors:
            rating_elem = item.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                if rating_text and rating_text != 'N/A' and rating_text.replace('.', '').isdigit():
                    rating = rating_text
                    break
        
        # Extract chapter count - use a more reliable method
        chapter_count = 0
        # Try to get chapter count from the latest chapter text
        if latest_chapter and latest_chapter != "N/A":
            import re
            chapter_match = re.search(r'(\d+(?:\.\d+)?)', latest_chapter)
            if chapter_match:
                chapter_count = int(chapter_match.group(1))
        
        # Fallback to followers count if no chapter info
        if chapter_count == 0:
            followers_elem = item.select_one('span.swap-off span.ml-1')
            if followers_elem:
                followers_text = followers_elem.get_text(strip=True)
                # Convert "11.3K" to 11300, "3.5K" to 3500, etc.
                if 'K' in followers_text.upper():
                    try:
                        chapter_count = int(float(followers_text.replace('K', '').replace('k', '')) * 1000)
                    except:
                        chapter_count = 0
                else:
                    try:
                        chapter_count = int(followers_text.replace(',', ''))
                    except:
                        chapter_count = 0
        
        # Extract genres
        genres = []
        genre_elements = item.select('div.flex.flex-wrap.text-xs.opacity-70 span')
        for genre_elem in genre_elements:
            genre_text = genre_elem.get_text(strip=True)
            if genre_text and genre_text not in ['🇯🇵', '🇰🇷', '🇨🇳', ',']:  # Skip flag emojis and commas
                genres.append(genre_text)
        
        # Extract author (if available)
        author = "Unknown"
        # MangaPark doesn't always show author in the card view
        
        # Extract status
        status = "Ongoing"
        if any('completed' in genre.lower() for genre in genres):
            status = "Completed"
        
        # Create manga data object
        manga_data = {
            'title': title,
            'cover_url': cover_url,
            'detail_url': detail_url,
            'latest_chapter': latest_chapter,
            'rating': rating,
            'chapter_count': chapter_count,
            'genres': genres,
            'author': author,
            'status': status,
            'source': 'MangaPark'
        }
        
        return manga_data
        
    except Exception as e:
        logger.warning(f"Error parsing single MangaPark item: {e}")
        return None

def scrape_mangapark_details(detail_url):
    """Scrape detailed information for a specific manga from MangaPark."""
    try:
        logger.info(f"Scraping MangaPark details for: {detail_url}")
        
        response = make_request(detail_url)
        if not response:
            logger.warning(f"Failed to fetch details for {detail_url}")
            return None
        
        # Log response status for debugging
        logger.info(f"Response status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Log page title for debugging
        page_title = soup.select_one('title')
        if page_title:
            logger.info(f"Page title: {page_title.get_text(strip=True)}")
        
        # Check if we got a valid page
        if "404" in response.text or "not found" in response.text.lower():
            logger.warning(f"Page returned 404 or not found for {detail_url}")
            return None
        
        # Debug: Log what elements we can find
        logger.info(f"Looking for title elements...")
        title_candidates = soup.select('h1, h2, h3, .title')
        for i, elem in enumerate(title_candidates[:5]):  # Log first 5 candidates
            logger.info(f"Title candidate {i}: {elem.get_text(strip=True)[:50]}...")
        
        logger.info(f"Looking for image elements...")
        img_candidates = soup.select('img[src*="/thumb/"]')
        logger.info(f"Found {len(img_candidates)} image candidates")
        for i, elem in enumerate(img_candidates[:3]):  # Log first 3 candidates
            logger.info(f"Image candidate {i}: {elem.get('src', '')[:50]}...")
        
        logger.info(f"Looking for chapter elements...")
        chapter_candidates = soup.select('a[href*="chapter"], a[href*="ch-"]')
        logger.info(f"Found {len(chapter_candidates)} chapter candidates")
        
        # Extract title - based on actual HTML structure
        title = "Unknown Title"
        # Try multiple selectors for title
        title_selectors = [
            'h3.text-lg a',  # Simplified selector
            'h3 a',
            'h1',
            '.title',
            'h1.entry-title',
            'h2 a'
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                logger.info(f"Found title with selector {selector}: {title}")
                break
        
        # Extract cover image - based on actual HTML structure
        cover_image = ""
        # Try multiple selectors for cover image
        cover_selectors = [
            'div.w-24 img',  # Simplified selector
            'img[src*="/thumb/"]',
            'img[alt*="' + title + '"]',
            '.cover img',
            'img'
        ]
        for selector in cover_selectors:
            cover_elem = soup.select_one(selector)
            if cover_elem:
                cover_image = cover_elem.get('src', '')
                logger.info(f"Found cover image with selector {selector}: {cover_image[:50]}...")
                break
        
        # Handle relative URLs
        if cover_image and not cover_image.startswith('http'):
            if cover_image.startswith('/'):
                cover_image = MANGA_PARK_BASE_URL + cover_image
            else:
                cover_image = urljoin(MANGA_PARK_BASE_URL, cover_image)
        
        # Extract description - based on actual HTML structure
        description = "No description available"
        # Try the specific selector from the HTML
        desc_elem = soup.select_one('div.limit-html.prose.lg\\:prose-lg div.limit-html-p')
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        else:
            # Fallback selectors
            desc_selectors = [
                'div.prose p',
                '.description p',
                '.summary p',
                'p'
            ]
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if description and len(description) > 10:  # Make sure it's not just a short text
                        break
        
        # Extract rating - try multiple selectors
        rating = "N/A"
        rating_selectors = [
            'span.text-yellow-500.font-bold',
            '.rating',
            '.score',
            'span[class*="rating"]',
            'div[class*="rating"]',
            '[class*="star"]',
            '[class*="score"]',
            'span[class*="yellow"]',
            'div[class*="yellow"]'
        ]
        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                if rating_text and rating_text != 'N/A' and rating_text.replace('.', '').isdigit():
                    rating = rating_text
                    break
        
        # Extract status - try multiple selectors
        status = "Unknown"
        status_selectors = [
            'span.badge',
            '.status',
            '.state'
        ]
        for selector in status_selectors:
            status_elem = soup.select_one(selector)
            if status_elem:
                status = status_elem.get_text(strip=True)
                break
        
        # Extract genres - based on actual HTML structure
        genres = []
        # Try the specific selector from the HTML
        genre_elements = soup.select('div.flex.items-center.flex-wrap span')
        if genre_elements:
            for genre_elem in genre_elements:
                genre_text = genre_elem.get_text(strip=True)
                # Filter out non-genre text like flag emojis, commas, and "Genres:" label
                if (genre_text and 
                    genre_text not in ['🇬🇧', '🇰🇷', '🇨🇳', '🇯🇵', ',', 'Genres:', 'Tr From', 'English', 'Korean'] and
                    not genre_text.startswith('(') and
                    not genre_text.endswith(')') and
                    len(genre_text) > 1):
                    genres.append(genre_text)
        
        # If no genres found with specific selector, try fallbacks
        if not genres:
            genre_selectors = [
                'div.flex.flex-wrap a.badge',
                '.genres a',
                '.tags a',
                'a[href*="genre"]'
            ]
            for selector in genre_selectors:
                genre_elements = soup.select(selector)
                if genre_elements:
                    for genre_elem in genre_elements:
                        genre_text = genre_elem.get_text(strip=True)
                        if genre_text and genre_text not in ['🇯🇵', '🇰🇷', '🇨🇳']:
                            genres.append(genre_text)
                    if genres:  # If we found genres, break
                        break
        
        # Extract author - based on actual HTML structure
        author = "Unknown"
        # Try the specific selector from the HTML
        author_elem = soup.select_one('div.mt-2.text-sm.md\\:text-base.opacity-80 a.link-hover.link-primary')
        if author_elem:
            author = author_elem.get_text(strip=True)
        else:
            # Fallback selectors
            author_selectors = [
                'div.text-sm span:contains("Author")',
                '.author',
                '.creator',
                'span:contains("Author")'
            ]
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.find_next_sibling().get_text(strip=True) if author_elem.find_next_sibling() else author_elem.get_text(strip=True)
                    break
        
        # Extract chapters - based on actual HTML structure
        chapters = []
        # Try multiple selectors for chapters
        chapter_selectors = [
            'div.scrollable-panel a',  # Simplified selector
            'a[href*="chapter"]',
            'a[href*="ch-"]',
            'div.chapter-list a',
            'div.flex.flex-nowrap.justify-between a.link-hover.link-primary'
        ]
        
        chapter_elements = []
        for selector in chapter_selectors:
            elements = soup.select(selector)
            if elements:
                # Filter out non-chapter links
                chapter_links = [elem for elem in elements if 'ch-' in elem.get('href', '') or 'chapter' in elem.get('href', '').lower()]
                if chapter_links:
                    chapter_elements = chapter_links
                    logger.info(f"Found {len(chapter_links)} chapters with selector {selector}")
                    break
        
        # If no chapters found with specific selectors, try a broader approach
        if not chapter_elements:
            all_links = soup.select('a[href*="/title/"]')
            chapter_links = [link for link in all_links if 'ch-' in link.get('href', '') or 'chapter' in link.get('href', '').lower()]
            if chapter_links:
                chapter_elements = chapter_links
                logger.info(f"Found {len(chapter_links)} chapters with broad selector")
        
        for chapter_elem in chapter_elements:
            try:
                chapter_title = chapter_elem.get_text(strip=True)
                chapter_url = urljoin(MANGA_PARK_BASE_URL, chapter_elem['href'])
                
                # Try to extract date from parent element
                chapter_date = "Unknown Date"
                parent_elem = chapter_elem.find_parent()
                if parent_elem:
                    date_elem = parent_elem.select_one('time')
                    if date_elem:
                        chapter_date = date_elem.get_text(strip=True)
                
                chapters.append({
                    'title': chapter_title,
                    'date': chapter_date,
                    'url': chapter_url
                })
            except Exception as e:
                logger.warning(f"Error parsing chapter: {e}")
                continue
        
        return {
            'title': title,
            'cover_image': cover_image,
            'description': description,
            'rating': rating,
            'status': status,
            'genres': genres,
            'author': author,
            'chapters': chapters,
            'source': 'MangaPark'
        }
        
    except Exception as e:
        logger.error(f"Failed to scrape MangaPark details for {detail_url}: {e}")
        logger.error(traceback.format_exc())
        return None

def search_mangapark_by_title(title):
    """Search MangaPark for manga by title."""
    try:
        logger.info(f"Searching MangaPark for: {title}")
        
        search_url = f"{MANGA_PARK_BASE_URL}/search?q={quote(title)}"
        response = make_request(search_url)
        
        if not response:
            logger.warning(f"Failed to search MangaPark for {title}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        manga_list = parse_mangapark_cards(soup, 1)  # Search results use same formatss
        
        return manga_list
        
    except Exception as e:
        logger.error(f"Error searching MangaPark for {title}: {e}")
        return []
