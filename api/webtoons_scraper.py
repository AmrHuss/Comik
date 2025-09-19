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

def make_request(url, retries=MAX_RETRIES):
    """Make HTTP request with retry logic and proper error handling."""
    for attempt in range(retries):
        try:
            response = requests.get(
                url, 
                headers=get_headers(), 
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
        
        # Extract chapters - try multiple selectors
        chapters = []
        chapter_selectors = [
            'ul#_listUl li._episodeItem',
            'ul[id*="list"] li[class*="episode"]',
            'ul li[class*="episode"]',
            '.episode-list li',
            '.chapter-list li'
        ]
        
        for selector in chapter_selectors:
            chapter_items = soup.select(selector)
            if chapter_items:
                for chapter_item in chapter_items:
                    try:
                        link = chapter_item.find('a', href=True)
                        if link:
                            chapter_title = "Unknown Chapter"
                            chapter_date = "Unknown Date"
                            
                            # Extract chapter title
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
                            
                            chapters.append({
                                'title': chapter_title,
                                'date': chapter_date,
                                'url': link['href']
                            })
                    except Exception as e:
                        logger.warning(f"Error parsing chapter: {e}")
                        continue
                break
        
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
        
        # Make request to the chapter URL
        response = make_request(chapter_url)
        if not response:
            logger.error(f"Failed to fetch chapter URL: {chapter_url}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the image container
        image_container = soup.find('div', {'id': '_imageList'})
        if not image_container:
            logger.error("Could not find image container with id '_imageList'")
            return []
        
        # Extract all images
        images = []
        img_elements = image_container.find_all('img', class_='_images')
        
        for img in img_elements:
            img_src = img.get('src') or img.get('data-url')
            if img_src:
                # Ensure it's a full URL
                if not img_src.startswith('http'):
                    img_src = urljoin(WEBTOONS_BASE_URL, img_src)
                images.append(img_src)
        
        logger.info(f"Found {len(images)} images for chapter")
        return images
        
    except Exception as e:
        logger.error(f"Error scraping Webtoons chapter images: {e}")
        logger.error(traceback.format_exc())
        return []

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
