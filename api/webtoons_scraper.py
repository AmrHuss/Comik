"""
Webtoons.com Scraper Module for ManhwaVerse
============================================

This module provides scraping functionality for webtoons.com,
including genre-based manga discovery and detailed manga information.

Author: ManhwaVerse Development Team
Version: 1.0
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin, urlparse
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_request(url, max_retries=3, delay=1):
    """
    Make a robust HTTP request with retries and proper headers.
    
    Args:
        url (str): The URL to request
        max_retries (int): Maximum number of retry attempts
        delay (int): Delay between retries in seconds
        
    Returns:
        requests.Response or None: The response object or None if failed
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                logger.error(f"All request attempts failed for {url}")
                return None

def scrape_webtoons_by_genre(genre_name):
    """
    Scrape manga from webtoons.com by genre.
    
    Args:
        genre_name (str): The genre to scrape (e.g., 'drama', 'action', 'romance')
        
    Returns:
        list: List of manga dictionaries with title, cover_url, detail_url, author
    """
    try:
        # Construct the genre URL
        genre_url = f"https://www.webtoons.com/en/genres/{genre_name.lower()}/"
        logger.info(f"Scraping Webtoons genre: {genre_name} from {genre_url}")
        
        # Make the request
        response = make_request(genre_url)
        if not response:
            logger.error(f"Failed to fetch Webtoons genre page: {genre_url}")
            return []
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find all manga items in the webtoon list
        manga_items = soup.select('ul.webtoon_list li')
        logger.info(f"Found {len(manga_items)} manga items")
        
        manga_list = []
        
        for item in manga_items:
            try:
                # Extract title
                title_elem = item.select_one('strong.title')
                title = title_elem.get_text(strip=True) if title_elem else 'Unknown Title'
                
                # Extract cover image URL
                img_elem = item.select_one('img')
                cover_url = img_elem.get('src') if img_elem else None
                if cover_url and not cover_url.startswith('http'):
                    cover_url = urljoin('https://www.webtoons.com', cover_url)
                
                # Extract detail URL
                link_elem = item.select_one('a')
                detail_url = link_elem.get('href') if link_elem else None
                if detail_url and not detail_url.startswith('http'):
                    detail_url = urljoin('https://www.webtoons.com', detail_url)
                
                # Extract author
                author_elem = item.select_one('div.author')
                author = author_elem.get_text(strip=True) if author_elem else 'Unknown Author'
                
                # Only add if we have essential data
                if title and cover_url and detail_url:
                    manga_data = {
                        'title': title,
                        'cover_url': cover_url,
                        'detail_url': detail_url,
                        'author': author,
                        'source': 'Webtoons'
                    }
                    manga_list.append(manga_data)
                    logger.debug(f"Added Webtoons manga: {title}")
                else:
                    logger.warning(f"Skipping incomplete manga data: {title}")
                    
            except Exception as e:
                logger.warning(f"Error processing manga item: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(manga_list)} manga from Webtoons")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error scraping Webtoons genre {genre_name}: {e}")
        return []

def scrape_webtoons_details(detail_url):
    """
    Scrape detailed information from a Webtoons manga detail page.
    
    Args:
        detail_url (str): The URL of the manga detail page
        
    Returns:
        dict: Detailed manga information including description, genres, and chapters
    """
    try:
        logger.info(f"Scraping Webtoons details from: {detail_url}")
        
        # Make the request
        response = make_request(detail_url)
        if not response:
            logger.error(f"Failed to fetch Webtoons detail page: {detail_url}")
            return None
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title
        title_elem = soup.select_one('h1.subj')
        title = title_elem.get_text(strip=True) if title_elem else 'Unknown Title'
        
        # Extract description
        desc_elem = soup.select_one('p.summary')
        description = desc_elem.get_text(strip=True) if desc_elem else 'No description available'
        
        # Extract genres
        genres = []
        genre_elems = soup.select('div.genre span')
        for genre_elem in genre_elems:
            genre_text = genre_elem.get_text(strip=True)
            if genre_text:
                genres.append(genre_text)
        
        # Extract author
        author_elem = soup.select_one('div.author')
        author = author_elem.get_text(strip=True) if author_elem else 'Unknown Author'
        
        # Extract rating (if available)
        rating_elem = soup.select_one('div.rating span')
        rating = rating_elem.get_text(strip=True) if rating_elem else 'N/A'
        
        # Extract status
        status_elem = soup.select_one('div.status')
        status = status_elem.get_text(strip=True) if status_elem else 'Ongoing'
        
        # Extract chapters from multiple pages
        chapters = []
        page = 1
        max_pages = 3  # Limit to first 3 pages to avoid too many requests
        
        while page <= max_pages:
            try:
                # Construct chapter list URL
                if page == 1:
                    chapter_url = detail_url
                else:
                    chapter_url = f"{detail_url}?page={page}"
                
                logger.info(f"Scraping chapters page {page}: {chapter_url}")
                
                # Make request for chapter list
                chapter_response = make_request(chapter_url)
                if not chapter_response:
                    break
                
                chapter_soup = BeautifulSoup(chapter_response.content, 'lxml')
                
                # Find chapter list
                chapter_list = chapter_soup.select('ul#_listUl li')
                
                if not chapter_list:
                    logger.info(f"No chapters found on page {page}, stopping")
                    break
                
                for chapter_item in chapter_list:
                    try:
                        # Extract chapter title
                        title_elem = chapter_item.select_one('span.subj')
                        chapter_title = title_elem.get_text(strip=True) if title_elem else f'Chapter {len(chapters) + 1}'
                        
                        # Extract chapter URL
                        link_elem = chapter_item.select_one('a')
                        chapter_url = link_elem.get('href') if link_elem else None
                        if chapter_url and not chapter_url.startswith('http'):
                            chapter_url = urljoin('https://www.webtoons.com', chapter_url)
                        
                        # Extract chapter date
                        date_elem = chapter_item.select_one('span.date')
                        chapter_date = date_elem.get_text(strip=True) if date_elem else 'Unknown Date'
                        
                        if chapter_url:
                            chapters.append({
                                'title': chapter_title,
                                'url': chapter_url,
                                'date': chapter_date
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error processing chapter item: {e}")
                        continue
                
                page += 1
                time.sleep(0.5)  # Small delay between requests
                
            except Exception as e:
                logger.warning(f"Error scraping chapter page {page}: {e}")
                break
        
        # Sort chapters by date (newest first)
        chapters.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        logger.info(f"Successfully scraped {len(chapters)} chapters for {title}")
        
        return {
            'title': title,
            'description': description,
            'genres': genres,
            'author': author,
            'rating': rating,
            'status': status,
            'chapters': chapters,
            'source': 'Webtoons'
        }
        
    except Exception as e:
        logger.error(f"Error scraping Webtoons details from {detail_url}: {e}")
        return None

def scrape_webtoons_chapter_images(chapter_url):
    """
    Scrape chapter images from a Webtoons chapter page.
    
    Args:
        chapter_url (str): The URL of the chapter page
        
    Returns:
        list: List of image URLs for the chapter
    """
    try:
        logger.info(f"Scraping Webtoons chapter images from: {chapter_url}")
        
        # Make the request
        response = make_request(chapter_url)
        if not response:
            logger.error(f"Failed to fetch Webtoons chapter page: {chapter_url}")
            return []
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find the viewer container
        viewer = soup.select_one('#_imageList')
        if not viewer:
            logger.warning("Could not find image viewer container")
            return []
        
        # Extract all image URLs
        images = viewer.select('img')
        image_urls = []
        
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src:
                if not src.startswith('http'):
                    src = urljoin('https://www.webtoons.com', src)
                image_urls.append(src)
        
        logger.info(f"Found {len(image_urls)} chapter images")
        return image_urls
        
    except Exception as e:
        logger.error(f"Error scraping Webtoons chapter images from {chapter_url}: {e}")
        return []
