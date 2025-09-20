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
# MangaPark scraper temporarily disabled
# from api.mangapark_scraper import scrape_mangapark_latest, scrape_mangapark_details, search_mangapark_by_title

# Webtoons scraper
from api.webtoons_scraper import scrape_webtoons_action_genre, scrape_webtoons_details, search_webtoons_by_title, scrape_webtoons_chapter_images

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
    """Get detailed information for a specific manga from the specified source."""
    detail_url = request.args.get('url', '').strip()
    source = request.args.get('source', '').strip()
    
    if not detail_url:
        return jsonify({
            'success': False, 
            'error': 'Manga detail URL is required'
        }), 400
    
    try:
        # Auto-detect source based on URL if not provided
        if not source:
            if 'webtoons.com' in detail_url:
                source = 'Webtoons'
            elif 'asurascanz.com' in detail_url:
                source = 'AsuraScanz'
            else:
                source = 'AsuraScanz'  # Default fallback
        
        logger.info(f"Fetching manga details for: {detail_url} from {source}")
        
        if source.lower() == 'webtoons':
            # Use Webtoons scraper
            manga_details = scrape_webtoons_details(detail_url)
        else:
            # Use AsuraScanz scraper (default)
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

@app.route('/api/chapter-data', methods=['GET'])
def get_chapter_data():
    """Get complete chapter data for seamless reader navigation."""
    chapter_url = request.args.get('url', '').strip()
    
    if not chapter_url:
        return jsonify({
            'success': False, 
            'error': 'Chapter URL is required'
        }), 400
    
    try:
        logger.info(f"Fetching complete chapter data for: {chapter_url}")
        
        # Step 1: Scrape current chapter images
        chapter_response = make_request(chapter_url)
        if not chapter_response:
            return jsonify({
                'success': False, 
                'error': 'Failed to fetch chapter page'
            }), 500
        
        chapter_soup = BeautifulSoup(chapter_response.content, 'lxml')
        
        # Find the reader area
        reader_area = None
        reader_selectors = [
            '#readerarea',
            '.reading-content',
            '.reader-area',
            '#reading-content',
            '.chapter-content'
        ]
        
        for selector in reader_selectors:
            reader_area = chapter_soup.select_one(selector)
            if reader_area:
                logger.info(f"Found reader area with selector: {selector}")
                break
        
        if not reader_area:
            logger.warning(f"Could not find reader area in chapter: {chapter_url}")
            return jsonify({
                'success': False, 
                'error': 'Could not find the reader area on the chapter page'
            }), 404
        
        # Extract chapter images
        images = reader_area.select('img')
        logger.info(f"Found {len(images)} images in reader area")
        
        image_urls = []
        for img in images:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                src = src.strip()
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
        
        # Step 2: Extract manga URL from chapter URL
        manga_url = chapter_url
        if '/chapter-' in manga_url:
            manga_url = manga_url.rsplit('/chapter-', 1)[0]
        elif '/chapter/' in manga_url:
            manga_url = manga_url.rsplit('/chapter/', 1)[0]
        else:
            # Try to extract by removing the last part
            manga_url = '/'.join(chapter_url.split('/')[:-1])
        
        logger.info(f"Extracted manga URL: {manga_url}")
        
        # Step 3: Get manga details to find all chapters
        manga_details = scrape_manga_details(manga_url)
        if not manga_details or not manga_details.get('chapters'):
            logger.warning(f"Could not find manga chapters for: {manga_url}")
            # Return just the images without navigation
            return jsonify({
                'success': True,
                'manga_title': 'Unknown Manga',
                'current_chapter_title': 'Chapter',
                'image_urls': image_urls,
                'next_chapter_url': None,
                'prev_chapter_url': None
            })
        
        chapters = manga_details['chapters']
        manga_title = manga_details.get('title', 'Unknown Manga')
        logger.info(f"Found {len(chapters)} chapters for manga: {manga_title}")
        
        # Step 4: Find current chapter in the list
        current_chapter_title = 'Chapter'
        current_chapter_index = None
        
        for i, chapter in enumerate(chapters):
            if chapter['url'] == chapter_url:
                current_chapter_index = i
                current_chapter_title = chapter.get('title', f'Chapter {i+1}')
                break
        
        if current_chapter_index is None:
            logger.warning(f"Current chapter not found in manga chapters")
            # Return just the images without navigation
            return jsonify({
                'success': True,
                'manga_title': manga_title,
                'current_chapter_title': 'Chapter',
                'image_urls': image_urls,
                'next_chapter_url': None,
                'prev_chapter_url': None
            })
        
        # Step 5: Find previous and next chapter URLs
        prev_chapter_url = None
        next_chapter_url = None
        
        # Previous chapter (higher index in the list)
        if current_chapter_index < len(chapters) - 1:
            prev_chapter_url = chapters[current_chapter_index + 1]['url']
        
        # Next chapter (lower index in the list)
        if current_chapter_index > 0:
            next_chapter_url = chapters[current_chapter_index - 1]['url']
        
        logger.info(f"Chapter navigation - Prev: {prev_chapter_url is not None}, Next: {next_chapter_url is not None}")
        
        return jsonify({
            'success': True,
            'manga_title': manga_title,
            'current_chapter_title': current_chapter_title,
            'image_urls': image_urls,
            'next_chapter_url': next_chapter_url,
            'prev_chapter_url': prev_chapter_url
        })
        
    except Exception as e:
        logger.error(f"Error in /api/chapter-data for {chapter_url}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'An unexpected error occurred while fetching chapter data'
        }), 500

@app.route('/api/chapter-details', methods=['GET'])
def get_chapter_details():
    """Get chapter images and navigation info for reader page."""
    chapter_url = request.args.get('url', '').strip()
    
    if not chapter_url:
        return jsonify({
            'success': False, 
            'error': 'Chapter URL is required'
        }), 400
    
    try:
        logger.info(f"Fetching chapter details for: {chapter_url}")
        
        # First, try to get chapter images using the existing /api/chapter logic
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
        
        # For now, return just the images without navigation
        # Navigation can be added later when the basic functionality works
        return jsonify({
            'success': True,
            'images': image_urls,
            'prev_chapter_url': None,
            'next_chapter_url': None,
            'current_chapter_index': 0,
            'total_chapters': 1
        })
        
    except Exception as e:
        logger.error(f"Error in /api/chapter-details for {chapter_url}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'An unexpected error occurred while fetching chapter details'
        }), 500

@app.route('/api/unified-popular', methods=['GET'])
def get_unified_popular():
    """Get popular manga from multiple sources."""
    try:
        logger.info("Fetching unified popular manga from multiple sources")
        
        # Get popular manga from AsuraScanz
        asura_manga = []
        try:
            asura_response = make_request('https://asurascanz.com/')
            if asura_response:
                asura_soup = BeautifulSoup(asura_response.content, 'lxml')
                asura_manga = parse_manga_cards_from_soup(asura_soup)
                # Add source flag
                for manga in asura_manga:
                    manga['source'] = 'AsuraScanz'
        except Exception as e:
            logger.warning(f"Failed to fetch AsuraScanz popular: {e}")
        
        # Get popular manga from Webtoons
        webtoons_manga = []
        try:
            webtoons_manga = scrape_webtoons_action_genre()
        except Exception as e:
            logger.warning(f"Failed to fetch Webtoons popular: {e}")
        
        # Combine all manga
        all_manga = asura_manga + webtoons_manga
        logger.info(f"Returning {len(all_manga)} popular manga from AsuraScanz and Webtoons")
        
        return jsonify({
            'success': True,
            'data': all_manga,
            'sources': {
                'AsuraScanz': len(asura_manga),
                'Webtoons': len(webtoons_manga)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in unified popular endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch popular manga from multiple sources'
        }), 500

@app.route('/api/unified-details', methods=['GET'])
def get_unified_details():
    """Get manga details from the specified source."""
    title = request.args.get('title', '').strip()
    source = request.args.get('source', 'AsuraScanz').strip()
    
    if not title:
        return jsonify({
            'success': False,
            'error': 'Title parameter is required'
        }), 400
    
    try:
        logger.info(f"Fetching unified details for '{title}' from {source}")
        
        if source.lower() == 'asurascanz':
            # Use existing AsuraScanz detail scraper
            # For now, we'll need to find the detail URL first
            # This is a simplified version - in production, you'd want to store/cache URLs
            return jsonify({
                'success': False,
                'error': 'AsuraScanz unified details not yet implemented'
            }), 501
            
        elif source.lower() == 'webtoons':
            # Search Webtoons for the title and get details
            try:
                search_results = search_webtoons_by_title(title)
                if search_results:
                    # Get details for the first result
                    detail_url = search_results[0]['detail_url']
                    manga_details = scrape_webtoons_details(detail_url)
                    if manga_details:
                        return jsonify({
                            'success': True,
                            'data': manga_details
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Could not fetch details for the found manga'
                        }), 404
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No manga found with that title'
                    }), 404
            except Exception as e:
                logger.error(f"Error fetching Webtoons details: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to fetch Webtoons details'
                }), 500
            
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown source: {source}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error in unified details endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch manga details'
        }), 500

@app.route('/api/source-search', methods=['GET'])
def search_manga_sources():
    """Search for manga across multiple sources."""
    title = request.args.get('title', '').strip()
    
    if not title:
        return jsonify({
            'success': False,
            'error': 'Title parameter is required'
        }), 400
    
    try:
        logger.info(f"Searching for manga: {title}")
        sources = []
        
        # Search AsuraScanz
        try:
            # Search AsuraScanz using the existing search endpoint logic
            # This would need to be implemented or we can use a different approach
            asura_results = []  # Placeholder - would need proper implementation
            if asura_results:
                sources.append({
                    'source': 'AsuraScanz',
                    'detail_url': asura_results[0]['detail_url'],
                    'title': asura_results[0]['title'],
                    'cover_url': asura_results[0]['cover_url']
                })
        except Exception as e:
            logger.warning(f"Error searching AsuraScanz: {e}")
        
        # Search Webtoons
        try:
            webtoons_results = search_webtoons_by_title(title)
            if webtoons_results:
                sources.append({
                    'source': 'Webtoons',
                    'detail_url': webtoons_results[0]['detail_url'],
                    'title': webtoons_results[0]['title'],
                    'cover_url': webtoons_results[0]['cover_url']
                })
        except Exception as e:
            logger.warning(f"Error searching Webtoons: {e}")
        
        return jsonify({
            'success': True,
            'sources': sources,
            'total_found': len(sources)
        })
        
    except Exception as e:
        logger.error(f"Error in source search: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to search manga sources'
        }), 500

@app.route('/api/unified-chapter-data', methods=['GET'])
def get_unified_chapter_data():
    """Get chapter data from the specified source."""
    chapter_url = request.args.get('url', '').strip()
    source = request.args.get('source', 'AsuraScanz').strip()
    
    if not chapter_url:
        return jsonify({
            'success': False,
            'error': 'Chapter URL parameter is required'
        }), 400
    
    try:
        logger.info(f"Fetching unified chapter data from {source}: {chapter_url}")
        
        if source.lower() == 'asurascanz':
            # Use existing AsuraScanz chapter scraper
            try:
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
                    src = img.get('src') or img.get('data-src')
                    if src:
                        # Convert relative URLs to absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = urljoin(chapter_url, src)
                        image_urls.append(src)
                
                if image_urls:
                    return jsonify({
                        'success': True,
                        'image_urls': image_urls,
                        'source': 'AsuraScanz'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No chapter images found'
                    }), 404
                    
            except Exception as e:
                logger.error(f"Error scraping AsuraScanz chapter: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to scrape chapter: {str(e)}'
                }), 500
            
        elif source.lower() == 'webtoons':
            # Use Webtoons chapter scraper
            try:
                images = scrape_webtoons_chapter_images(chapter_url)
                if images:
                    return jsonify({
                        'success': True,
                        'image_urls': images,
                        'source': 'Webtoons'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No chapter images found'
                    }), 404
            except Exception as e:
                logger.error(f"Error scraping Webtoons chapter: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to scrape chapter: {str(e)}'
                }), 500
                
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown source: {source}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error in unified chapter data endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch chapter data'
        }), 500

# Webtoons endpoints
@app.route('/api/webtoons/popular', methods=['GET'])
def get_webtoons_popular():
    """Get popular manga from Webtoons action genre."""
    try:
        logger.info("Fetching popular manga from Webtoons")
        manga_data = scrape_webtoons_action_genre()
        
        if not manga_data:
            return jsonify({
                'success': False, 
                'error': 'No manga data found from Webtoons'
            }), 404
        
        return jsonify({
            'success': True, 
            'count': len(manga_data), 
            'data': manga_data
        })
        
    except Exception as e:
        logger.error(f"Error in /api/webtoons/popular: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'Internal server error occurred'
        }), 500

@app.route('/api/webtoons/details', methods=['GET'])
def get_webtoons_details():
    """Get detailed information for a specific manga from Webtoons."""
    detail_url = request.args.get('url', '').strip()
    
    if not detail_url:
        return jsonify({
            'success': False, 
            'error': 'Manga detail URL is required'
        }), 400
    
    try:
        logger.info(f"Fetching Webtoons details for: {detail_url}")
        manga_details = scrape_webtoons_details(detail_url)
        
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
        logger.error(f"Error in /api/webtoons/details for {detail_url}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'Failed to fetch manga details'
        }), 500

@app.route('/api/webtoons/search', methods=['GET'])
def search_webtoons():
    """Search manga by title on Webtoons."""
    query = request.args.get('query', '').strip()
    
    if not query:
        return jsonify({
            'success': False, 
            'error': 'Search query is required'
        }), 400
    
    try:
        logger.info(f"Searching Webtoons for: {query}")
        manga_data = search_webtoons_by_title(query)
        
        return jsonify({
            'success': True, 
            'count': len(manga_data), 
            'data': manga_data
        })
        
    except Exception as e:
        logger.error(f"Error in /api/webtoons/search for query '{query}': {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False, 
            'error': 'Search failed due to internal error'
        }), 500

# MadaraScans endpoints removed - keeping only AsuraScanz

@app.route('/api/webtoons-image-proxy', methods=['GET'])
def webtoons_image_proxy():
    """Proxy endpoint for Webtoons images to bypass hotlinking protection."""
    try:
        img_url = request.args.get('img_url')
        chapter_url = request.args.get('chapter_url')
        
        if not img_url or not chapter_url:
            return jsonify({
                'success': False,
                'error': 'Missing img_url or chapter_url parameter'
            }), 400
        
        # Decode the URLs
        import urllib.parse
        img_url = urllib.parse.unquote(img_url)
        chapter_url = urllib.parse.unquote(chapter_url)
        
        # Set up proper headers to bypass hotlinking protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': chapter_url,  # This is crucial - use the specific chapter URL
            'Origin': 'https://www.webtoons.com',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Make the request to get the image
        response = requests.get(img_url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Return the image with proper headers
        from flask import Response
        return Response(
            response.content,
            mimetype=response.headers.get('content-type', 'image/jpeg'),
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Webtoons image: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch image: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in image proxy: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
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
            '/api/chapter',
            '/api/chapter-details',
            '/api/chapter-data',
            '/api/unified-popular',
            '/api/unified-details',
            '/api/unified-chapter-data',
            '/api/source-search',
            '/api/webtoons/popular',
            '/api/webtoons/details',
            '/api/webtoons/search',
            '/api/webtoons-image-proxy'
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