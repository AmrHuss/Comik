#!/usr/bin/env python3
"""
Webtoons.com Scraper Module for ManhwaVerse
===========================================

This module provides scraping functionality for webtoons.com,
using the same requests + BeautifulSoup approach as AsuraScanz.

Author: ManhwaVerse Development Team
Version: 3.0 - Vercel Compatible
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin, urlparse, quote
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBTOONS_BASE_URL = "https://www.webtoons.com/en/"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

def get_headers():
    """Get standardized headers for HTTP requests with anti-scraping measures."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1'
    }

def make_request(url, max_retries=3, delay=1):
    """
    Make a robust HTTP request with retries and proper headers.
    
    Args:
        url (str): The URL to request
        max_retries (int): Maximum number of retry attempts
        delay (int): Delay between retries in seconds
    Returns:
        requests.Response or None: The response object if successful, None otherwise.
    """
    for attempt in range(max_retries):
        try:
            # Add random delay to avoid rate limiting
            if attempt > 0:
                time.sleep(delay * (attempt + 1))
            
            response = requests.get(url, headers=get_headers(), timeout=REQUEST_TIMEOUT)
            
            # Check for anti-scraping measures
            if response.status_code == 403:
                logger.warning(f"Access forbidden (403) for {url} - possible anti-scraping protection")
                return None
            elif response.status_code == 429:
                logger.warning(f"Rate limited (429) for {url} - waiting longer")
                time.sleep(delay * 2)
                continue
            elif response.status_code == 503:
                logger.warning(f"Service unavailable (503) for {url} - possible anti-scraping protection")
                return None
            
            response.raise_for_status()  # Raise an exception for other HTTP errors
            
            # Check if response contains anti-scraping content
            if 'cloudflare' in response.text.lower() or 'access denied' in response.text.lower():
                logger.warning(f"Anti-scraping protection detected for {url}")
                return None
                
            return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    logger.error(f"All {max_retries} attempts failed for {url}")
    return None

def scrape_genre(genre_name):
    """
    Scrape webtoons by genre from webtoons.com using requests + BeautifulSoup.
    
    Args:
        genre_name (str): The genre to scrape (e.g., 'action', 'romance')
    
    Returns:
        list: List of manga dictionaries with title, cover_url, detail_url, author, source
    """
    genre_url = urljoin(WEBTOONS_BASE_URL, f"genres/{genre_name}/")
    logger.info(f"Scraping webtoons for genre: {genre_name} from {genre_url}")
    
    try:
        response = make_request(genre_url)
        if not response:
            logger.warning(f"Failed to fetch genre page: {genre_url} - likely anti-scraping protection")
            return []
        
        # Check if we got a valid response
        if len(response.content) < 1000:  # Very small response might be an error page
            logger.warning(f"Received suspiciously small response ({len(response.content)} bytes) for {genre_url}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        manga_list = []
        
        # Look for webtoon cards in the genre page
        # Webtoons uses different selectors than AsuraScanz
        webtoon_cards = soup.select('ul.webtoon_list li')
        
        if not webtoon_cards:
            # Try alternative selectors
            webtoon_cards = soup.select('div.episode_thumb')
            if not webtoon_cards:
                webtoon_cards = soup.select('div.episode')
                if not webtoon_cards:
                    # Try even more generic selectors
                    webtoon_cards = soup.select('div[class*="episode"]') or soup.select('div[class*="webtoon"]')
        
        logger.info(f"Found {len(webtoon_cards)} webtoon cards")
        
        # If no cards found, return empty list (likely anti-scraping)
        if not webtoon_cards:
            logger.warning(f"No webtoon cards found for genre {genre_name} - possible anti-scraping protection")
            return []
        
        for card in webtoon_cards:
            try:
                # Extract title
                title_element = card.select_one('strong.title') or card.select_one('p.subj') or card.select_one('h3')
                title = title_element.get_text(strip=True) if title_element else "Unknown Title"
                
                # Extract cover image
                cover_img = card.select_one('img')
                cover_url = ""
                if cover_img:
                    cover_url = cover_img.get('src') or cover_img.get('data-src') or ""
                    if cover_url and not cover_url.startswith('http'):
                        cover_url = urljoin(WEBTOONS_BASE_URL, cover_url)
                
                # Extract detail URL
                detail_link = card.select_one('a')
                detail_url = ""
                if detail_link and detail_link.get('href'):
                    detail_url = urljoin(WEBTOONS_BASE_URL, detail_link.get('href'))
                
                # Extract author
                author_element = card.select_one('div.author') or card.select_one('p.author')
                author = author_element.get_text(strip=True) if author_element else "Unknown Author"
                
                if title and detail_url:  # Only add if we have essential data
                    manga_list.append({
                        'title': title,
                        'cover_url': cover_url,
                        'detail_url': detail_url,
                        'author': author,
                        'source': 'Webtoons'
                    })
                    
            except Exception as e:
                logger.warning(f"Error parsing webtoon card: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(manga_list)} webtoons for genre: {genre_name}")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error scraping webtoons by genre: {e}")
        return []

def scrape_details(detail_url):
    """
    Scrape detailed information for a specific webtoon using requests + BeautifulSoup.
    
    Args:
        detail_url (str): The detail page URL of the webtoon
    
    Returns:
        dict: Dictionary containing all manga details including chapters
    """
    logger.info(f"Scraping webtoon details from: {detail_url}")
    
    try:
        response = make_request(detail_url)
        if not response:
            logger.error(f"Failed to fetch detail page: {detail_url}")
            return None
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title
        title_element = soup.select_one('h1.subj') or soup.select_one('h1.title')
        title = title_element.get_text(strip=True) if title_element else "Unknown Title"
        
        # Extract cover image
        cover_img = soup.select_one('span.thmb img') or soup.select_one('div.episode_thumb img')
        cover_image = ""
        if cover_img and cover_img.get('src'):
            cover_image = cover_img.get('src')
            if not cover_image.startswith('http'):
                cover_image = urljoin(WEBTOONS_BASE_URL, cover_image)
        
        # Extract description
        desc_element = soup.select_one('p.summary') or soup.select_one('div.summary')
        description = desc_element.get_text(strip=True) if desc_element else "No description available"
        
        # Extract genres
        genre_elements = soup.select('h2.genre a') or soup.select('div.genre a')
        genres = [g.get_text(strip=True) for g in genre_elements]
        
        # Extract author
        author_element = soup.select_one('div.author_area p.author') or soup.select_one('p.author')
        author = author_element.get_text(strip=True) if author_element else "Unknown Author"
        
        # Extract chapters
        chapters = []
        chapter_list_ul = soup.select_one('ul#_listUl') or soup.select_one('ul.episode_list')
        
        if chapter_list_ul:
            chapter_items = chapter_list_ul.select('li._episodeItem') or chapter_list_ul.select('li.episode_item')
            
            for item in chapter_items:
                try:
                    link = item.select_one('a')
                    if link and link.get('href'):
                        chapter_title_element = item.select_one('p.sub_title') or item.select_one('span.title')
                        chapter_title = chapter_title_element.get_text(strip=True) if chapter_title_element else "Chapter"
                        
                        chapters.append({
                            'title': chapter_title,
                            'date': 'N/A',  # Webtoons doesn't usually show dates in the list
                            'url': urljoin(WEBTOONS_BASE_URL, link['href'])
                        })
                except Exception as e:
                    logger.warning(f"Error parsing webtoon chapter: {e}")
                    continue
        
        # Reverse chapters to be newest first
        chapters.reverse()
        
        return {
            'title': title,
            'cover_image': cover_image,
            'description': description,
            'rating': 'N/A',  # Webtoons uses likes, not star ratings
            'status': 'Ongoing',  # Placeholder
            'genres': genres,
            'author': author,
            'chapters': chapters,
            'source': 'Webtoons'
        }
        
    except Exception as e:
        logger.error(f"Error scraping webtoon details: {e}")
        return None

def scrape_chapter_images(chapter_url):
    """
    Scrape chapter images for a specific webtoon chapter using requests + BeautifulSoup.
    
    Args:
        chapter_url (str): The chapter reader URL
    
    Returns:
        list: List of image URLs for the chapter
    """
    logger.info(f"Scraping webtoon chapter images from: {chapter_url}")
    
    try:
        response = make_request(chapter_url)
        if not response:
            logger.error(f"Failed to fetch chapter page: {chapter_url}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        image_urls = []
        
        # Look for images in the chapter viewer
        image_selectors = [
            '#_imageList img',
            '.viewer_img img',
            '.episode_viewer img',
            'div.viewer img'
        ]
        
        for selector in image_selectors:
            images = soup.select(selector)
            if images:
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src and 'img-webtoon.pstatic.net' in src:
                        image_urls.append(src)
                break  # Use the first selector that finds images
        
        logger.info(f"Found {len(image_urls)} images for chapter: {chapter_url}")
        return image_urls
        
    except Exception as e:
        logger.error(f"Error scraping webtoon chapter images: {e}")
        return []

def search_by_title(query):
    """
    Search for webtoons by title on webtoons.com using requests + BeautifulSoup.
    
    Args:
        query (str): The search query
    
    Returns:
        list: List of search results
    """
    search_url = urljoin(WEBTOONS_BASE_URL, f"search?keyword={quote(query)}")
    logger.info(f"Searching webtoons for title: {query} from {search_url}")
    
    try:
        response = make_request(search_url)
        if not response:
            logger.error(f"Failed to fetch search page: {search_url}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        results = []
        
        # Look for search results
        search_items = soup.select('ul.search_result_list li') or soup.select('div.search_item')
        
        for item in search_items:
            try:
                title_element = item.select_one('p.subj') or item.select_one('h3')
                detail_link = item.select_one('a')
                cover_img = item.select_one('img')
                
                if title_element and detail_link and cover_img:
                    title = title_element.get_text(strip=True)
                    detail_url = urljoin(WEBTOONS_BASE_URL, detail_link.get('href'))
                    cover_url = cover_img.get('src') or cover_img.get('data-src')
                    
                    if cover_url and not cover_url.startswith('http'):
                        cover_url = urljoin(WEBTOONS_BASE_URL, cover_url)
                    
                    results.append({
                        'title': title,
                        'detail_url': detail_url,
                        'cover_url': cover_url,
                        'source': 'Webtoons'
                    })
            except Exception as e:
                logger.warning(f"Error parsing webtoon search result: {e}")
                continue
        
        logger.info(f"Found {len(results)} webtoons for search query: {query}")
        return results
        
    except Exception as e:
        logger.error(f"Error searching webtoons by title: {e}")
        return []