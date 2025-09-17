#!/usr/bin/env python3
"""
ManhwaVerse Flask API - Vercel Production Ready
===============================================

A complete Flask API for scraping manhwa data from Asura Scans.
Optimized for Vercel serverless deployment with modern configuration.

Author: ManhwaVerse Development Team
Date: 2025
Version: Vercel Production v1.0
"""

import logging
import requests
from urllib.parse import urljoin, quote
from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import traceback

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Constants
BASE_URL = "https://asurascanz.com/"
REQUEST_TIMEOUT = 15
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

def parse_manga_cards_from_soup(soup):
    """Parse manga cards from BeautifulSoup object."""
    manga_list = []
    
    # Try different container selectors based on page type
    container_selectors = [
        'div.bs div.bsx',  # Main manga cards
        'div.bsx',         # Direct manga cards
        'div.utao.styletwo',  # Latest updates section
        'div.bs'           # Fallback for genre pages
    ]
    
    for selector in container_selectors:
        containers = soup.select(selector)
        logger.info(f"Found {len(containers)} containers with selector: {selector}")
        
        for container in containers:
            try:
                # Find the main link element
                link_element = container.find('a', href=True)
                if not link_element:
                    continue
                
                # Extract title with multiple fallback methods
                title = ""
                title_selectors = [
                    lambda: link_element.get('title', '').strip(),
                    lambda: container.find('h4', class_='tt'),
                    lambda: container.find('h3'),
                    lambda: container.find('div', class_='tt'),
                    lambda: container.find('h4')
                ]
                
                for selector_func in title_selectors:
                    try:
                        title_element = selector_func()
                        if title_element:
                            if hasattr(title_element, 'get_text'):
                                title = title_element.get_text(strip=True)
                            else:
                                title = str(title_element).strip()
                            if title:
                                break
                    except:
                        continue
                
                if not title:
                    continue
                
                # Extract detail URL
                detail_url = urljoin(BASE_URL, link_element['href'])
                
                # Extract cover image with fallback methods
                cover_url = ""
                img_element = container.find('img')
                if img_element:
                    cover_url = (
                        img_element.get('data-src') or 
                        img_element.get('src') or 
                        img_element.get('data-lazy-src', '')
                    ).strip()
                    
                    if cover_url and not cover_url.startswith('http'):
                        cover_url = urljoin(BASE_URL, cover_url)
                
                if not cover_url:
                    continue
                
                # Extract latest chapter information
                latest_chapter = "N/A"
                chapter_selectors = [
                    'div.epxs',
                    'ul li a',
                    '.chapternum',
                    '.chapter-title'
                ]
                
                for chapter_selector in chapter_selectors:
                    chapter_element = container.select_one(chapter_selector)
                    if chapter_element:
                        latest_chapter = chapter_element.get_text(strip=True)
                        if latest_chapter:
                            break
                
                # Create manga data object
                manga_data = {
                    'title': title,
                    'cover_url': cover_url,
                    'detail_url': detail_url,
                    'latest_chapter': latest_chapter
                }
                
                manga_list.append(manga_data)
                logger.debug(f"Successfully parsed manga: {title}")
                
            except Exception as e:
                logger.warning(f"Error parsing manga container: {e}")
                continue
    
    # Remove duplicates based on detail_url
    unique_manga = []
    seen_urls = set()
    for manga in manga_list:
        if manga['detail_url'] not in seen_urls:
            unique_manga.append(manga)
            seen_urls.add(manga['detail_url'])
    
    logger.info(f"Successfully parsed {len(unique_manga)} unique manga entries")
    return unique_manga

def scrape_manga_details(detail_url):
    """Scrape detailed information for a specific manga."""
    try:
        response = make_request(detail_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find main info container
        info_container = soup.select_one('div.main-info')
        if not info_container:
            logger.warning(f"Could not find main-info container for {detail_url}")
            return None
        
        # Extract title
        title_element = info_container.select_one('h1.entry-title')
        title = title_element.get_text(strip=True) if title_element else "Unknown Title"
        
        # Extract cover image
        cover_img = info_container.select_one('div.thumb img')
        cover_image = cover_img['src'] if cover_img and cover_img.get('src') else ""
        
        # Extract description
        desc_element = info_container.select_one('div.entry-content[itemprop="description"] p')
        description = desc_element.get_text(strip=True) if desc_element else "No description available"
        
        # Extract rating
        rating_element = info_container.select_one('div.num[itemprop="ratingValue"]')
        rating = rating_element.get_text(strip=True) if rating_element else "N/A"
        
        # Extract status
        status_element = info_container.select_one('.imptdt i')
        status = status_element.get_text(strip=True) if status_element else "Unknown"
        
        # Extract genres
        genre_elements = info_container.select('span.mgen a')
        genres = [genre.get_text(strip=True) for genre in genre_elements if genre.get_text(strip=True)]
        
        # Extract chapters
        chapters = []
        chapter_list_elements = soup.select('#chapterlist ul li')
        
        for chapter_li in chapter_list_elements:
            try:
                link = chapter_li.find('a')
                if link and link.get('href'):
                    chapter_title = "Unknown Chapter"
                    chapter_date = "Unknown Date"
                    
                    title_elem = link.select_one('.chapternum')
                    if title_elem:
                        chapter_title = title_elem.get_text(strip=True)
                    
                    date_elem = link.select_one('.chapterdate')
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
        
        return {
            'title': title,
            'cover_image': cover_image,
            'description': description,
            'rating': rating,
            'status': status,
            'genres': genres,
            'chapters': chapters
        }
        
    except Exception as e:
        logger.error(f"Failed to scrape details for {detail_url}: {e}")
        logger.error(traceback.format_exc())
        return None

# --- API Endpoints (All prefixed with /api/) ---

@app.route('/api/popular', methods=['GET'])
def get_popular_manga():
    """Get popular manga from the homepage."""
    try:
        logger.info("Fetching popular manga from homepage")
        response = make_request(BASE_URL)
        
        if not response:
            return jsonify({
                'success': False, 
                'error': 'Failed to fetch homepage data'
            }), 500
        
        soup = BeautifulSoup(response.content, 'lxml')
        manga_data = parse_manga_cards_from_soup(soup)
        
        if not manga_data:
            return jsonify({
                'success': False, 
                'error': 'No manga data found on homepage'
            }), 404
        
        return jsonify({
            'success': True, 
            'count': len(manga_data), 
            'data': manga_data
        })
        
    except Exception as e:
        logger.error(f"Error in /api/popular: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'Internal server error occurred'
        }), 500

@app.route('/api/genre', methods=['GET'])
def get_genre_manga():
    """Get manga by genre."""
    genre_name = request.args.get('name', '').strip().lower()
    
    if not genre_name:
        return jsonify({
            'success': False, 
            'error': 'Genre name is required'
        }), 400
    
    try:
        genre_url = f"{BASE_URL}genres/{genre_name}/"
        logger.info(f"Fetching manga for genre: {genre_name} from {genre_url}")
        
        response = make_request(genre_url)
        
        if not response:
            return jsonify({
                'success': False, 
                'error': f'Failed to fetch genre page for {genre_name}'
            }), 500
        
        soup = BeautifulSoup(response.content, 'lxml')
        manga_data = parse_manga_cards_from_soup(soup)
        
        if not manga_data:
            return jsonify({
                'success': False, 
                'error': f'No manga found for genre: {genre_name}'
            }), 404
        
        return jsonify({
            'success': True, 
            'count': len(manga_data), 
            'data': manga_data
        })
        
    except Exception as e:
        logger.error(f"Error in /api/genre for {genre_name}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'Internal server error occurred'
        }), 500

@app.route('/api/search', methods=['GET'])
def search_manga():
    """Search manga by query."""
    query = request.args.get('query', '').strip()
    
    if not query:
        return jsonify({
            'success': False, 
            'error': 'Search query is required'
        }), 400
    
    try:
        search_url = f"{BASE_URL}?s={quote(query)}"
        logger.info(f"Searching for: {query} at {search_url}")
        
        response = make_request(search_url)
        
        if not response:
            return jsonify({
                'success': False, 
                'error': 'Search request failed'
            }), 500
        
        soup = BeautifulSoup(response.content, 'lxml')
        manga_data = parse_manga_cards_from_soup(soup)
        
        return jsonify({
            'success': True, 
            'count': len(manga_data), 
            'data': manga_data
        })
        
    except Exception as e:
        logger.error(f"Error in /api/search for query '{query}': {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'Search failed due to internal error'
        }), 500

@app.route('/api/manga-details', methods=['GET'])
def get_manga_details():
    """Get detailed information for a specific manga."""
    detail_url = request.args.get('url', '').strip()
    
    if not detail_url:
        return jsonify({
            'success': False, 
            'error': 'Manga detail URL is required'
        }), 400
    
    try:
        logger.info(f"Fetching manga details for: {detail_url}")
        manga_details = scrape_manga_details(detail_url)
        
        if not manga_details:
            return jsonify({
                'success': False, 
                'error': 'Could not scrape details for the provided URL'
            }), 404
        
        return jsonify({
            'success': True, 
            'data': manga_details
        })
        
    except Exception as e:
        logger.error(f"Error in /api/manga-details for {detail_url}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'Failed to fetch manga details'
        }), 500

@app.route('/api/chapter', methods=['GET'])
def get_chapter_images():
    """Get chapter images from a chapter URL."""
    chapter_url = request.args.get('url', '').strip()
    
    if not chapter_url:
        return jsonify({
            'success': False, 
            'error': 'Chapter URL is required'
        }), 400
    
    try:
        logger.info(f"Fetching chapter images from: {chapter_url}")
        
        response = make_request(chapter_url)
        
        if not response:
            return jsonify({
                'success': False, 
                'error': 'Failed to fetch chapter page'
            }), 500
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find the reader area with multiple possible selectors
        reader_area = None
        reader_selectors = [
            '#readerarea',
            '.reading-content',
            '.reader-area',
            '#reading-content',
            '.chapter-content'
        ]
        
        for selector in reader_selectors:
            reader_area = soup.select_one(selector)
            if reader_area:
                logger.info(f"Found reader area with selector: {selector}")
                break
        
        if not reader_area:
            logger.warning(f"Could not find reader area in chapter: {chapter_url}")
            return jsonify({
                'success': False, 
                'error': 'Could not find the reader area on the chapter page'
            }), 404
        
        # Extract all images from the reader area
        images = reader_area.select('img')
        logger.info(f"Found {len(images)} images in reader area")
        
        image_urls = []
        for img in images:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                src = src.strip()
                # Filter for valid chapter images (not ads or trackers)
                if (src and 
                    ('asurascans.imagemanga.online' in src or 
                     'asurascans.com' in src or
                     'manga' in src.lower()) and
                    not any(ad in src.lower() for ad in ['ad', 'banner', 'tracker', 'pixel'])):
                    image_urls.append(src)
        
        if not image_urls:
            logger.warning(f"No valid chapter images found in: {chapter_url}")
            return jsonify({
                'success': False, 
                'error': 'No valid chapter images found in the reader area'
            }), 404
        
        logger.info(f"Successfully extracted {len(image_urls)} chapter images")
        return jsonify({
            'success': True, 
            'count': len(image_urls), 
            'data': image_urls
        })
        
    except Exception as e:
        logger.error(f"Error in /api/chapter for {chapter_url}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'An unexpected error occurred while fetching chapter images'
        }), 500

@app.route('/api', methods=['GET'])
def api_root():
    """API root endpoint for health checks."""
    return jsonify({
        'message': 'ManhwaVerse API is running',
        'version': '1.0.0',
        'endpoints': [
            '/api/popular',
            '/api/genre',
            '/api/search', 
            '/api/manga-details',
            '/api/chapter'
        ]
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False, 
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False, 
        'error': 'Internal server error'
    }), 500

# Vercel requires the app variable to be available
# No if __name__ == '__main__' block needed for Vercel