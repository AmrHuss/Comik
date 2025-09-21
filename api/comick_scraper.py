#!/usr/bin/env python3
"""
Comick.live Scraper - Simple HTML Scraping like Webtoons
========================================================

A simple scraper for Comick.live that:
- Scrapes HTML directly like Webtoons scraper
- Uses image proxy for all cover images
- Simple and reliable approach

Author: ManhwaVerse Development Team
Date: 2025
Version: 4.0
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

# Constants
COMICK_BASE_URL = "https://comick.live"
ACTION_GENRE_URL = "https://comick.live/search?genres=action&order_by=user_follow_count"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

def get_comick_headers():
    """Get headers optimized for Comick.live"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://comick.live/',
        'Origin': 'https://comick.live',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1'
    }

def make_request(url, retries=MAX_RETRIES, headers=None):
    """Make HTTP request with retry logic and proper error handling."""
    if headers is None:
        headers = get_comick_headers()
    
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
    """Scrape action genre manga from Comick.live - simple like Webtoons"""
    try:
        logger.info("Starting Comick action genre scraping")
        
        # Make request to action genre page
        logger.info(f"Fetching: {ACTION_GENRE_URL}")
        response = make_request(ACTION_GENRE_URL)
        
        if not response:
            logger.error("Failed to fetch Comick action genre page")
            return []
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find manga cards - try multiple selectors like Webtoons
        manga_cards = []
        selectors = [
            'div.cursor-pointer',
            'div[class*="cursor-pointer"]',
            'div[class*="manga"]',
            '.manga-card'
        ]
        
        for selector in selectors:
            manga_cards = soup.select(selector)
            if manga_cards:
                logger.info(f"Found {len(manga_cards)} manga cards with selector: {selector}")
                break
        
        if not manga_cards:
            logger.error("Could not find manga cards")
            return []
        
        manga_list = []
        
        # Process each manga card
        for i, card in enumerate(manga_cards[:20]):  # Limit to 20
            try:
                # Extract title - try multiple methods like Webtoons
                title = ""
                title_selectors = [
                    'p.font-bold',
                    'h3',
                    'h4',
                    '.title',
                    'a[title]'
                ]
                
                for selector in title_selectors:
                    title_elem = card.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title:
                            break
                
                if not title:
                    # Try getting title from link
                    link_elem = card.find('a')
                    if link_elem:
                        title = link_elem.get('title', '') or link_elem.get_text(strip=True)
                
                if not title:
                    title = f"Comick Manga {i+1}"
                
                # Extract cover image - try multiple methods
                cover_url = ""
                img_selectors = [
                    'img',
                    'img[src]',
                    'img[data-src]'
                ]
                
                for selector in img_selectors:
                    img_elem = card.select_one(selector)
                    if img_elem:
                        cover_url = img_elem.get('src') or img_elem.get('data-src', '')
                        if cover_url:
                            break
                
                # Convert relative URLs to absolute
                if cover_url and not cover_url.startswith('http'):
                    cover_url = urljoin(COMICK_BASE_URL, cover_url)
                
                # Extract description
                description = "Popular manga available on Comick.live"
                desc_selectors = [
                    'p.prose',
                    '.description',
                    '.summary',
                    'p'
                ]
                
                for selector in desc_selectors:
                    desc_elem = card.select_one(selector)
                    if desc_elem:
                        desc_text = desc_elem.get_text(strip=True)
                        if desc_text and len(desc_text) > 10:
                            description = desc_text
                            break
                
                # Extract chapters
                chapters = 0
                chapter_selectors = [
                    'span:contains("chapters")',
                    '.chapters',
                    '.chapter-count'
                ]
                
                for selector in chapter_selectors:
                    chapter_elem = card.select_one(selector)
                    if chapter_elem:
                        chapter_text = chapter_elem.get_text(strip=True)
                        match = re.search(r'(\d+(?:\.\d+)?)', chapter_text)
                        if match:
                            chapters = float(match.group(1))
                            break
                
                # Extract followers
                followers = 0
                follower_selectors = [
                    'span.text-xs.xl:text-lg',
                    '.followers',
                    '.follow-count'
                ]
                
                for selector in follower_selectors:
                    follower_elem = card.select_one(selector)
                    if follower_elem:
                        follower_text = follower_elem.get_text(strip=True)
                        if 'k' in follower_text:
                            followers = int(float(follower_text.replace('k', '')) * 1000)
                        else:
                            try:
                                followers = int(follower_text.replace(',', ''))
                            except:
                                followers = 0
                        break
                
                # Extract year
                year = "2024"
                year_selectors = [
                    'span[title="Published"]',
                    '.year',
                    '.published'
                ]
                
                for selector in year_selectors:
                    year_elem = card.select_one(selector)
                    if year_elem:
                        year = year_elem.get_text(strip=True)
                        break
                
                # Create slug
                slug = title.lower().replace(' ', '-').replace(':', '').replace('!', '').replace('?', '').replace("'", "")
                
                # Use proxy for cover images
                proxy_cover_url = f"/api/comick-image-proxy?img_url={cover_url}" if cover_url else ""
                
                # Create manga object
                manga = {
                    'title': title,
                    'description': description[:200] + '...' if len(description) > 200 else description,
                    'cover_url': proxy_cover_url,
                    'rating': "8.5",
                    'followers': followers,
                    'chapters': int(chapters) if chapters > 0 else 0,
                    'status': 'Ongoing',
                    'year': year,
                    'slug': slug,
                    'source': 'Comick',
                    'url': f"{COMICK_BASE_URL}/comic/{slug}",
                    'genres': ['Action'],
                    'titles': [title]
                }
                
                manga_list.append(manga)
                logger.debug(f"Added Comick manga: {title}")
                
            except Exception as e:
                logger.warning(f"Error processing manga card {i+1}: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(manga_list)} Comick manga")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error in scrape_comick_action_genre: {e}")
        return []

def scrape_comick_details(comic_url: str):
    """Scrape detailed information for a specific Comick comic"""
    try:
        logger.info(f"Scraping Comick details for: {comic_url}")
        
        response = make_request(comic_url)
        if not response:
            logger.error(f"Failed to fetch comic details from {comic_url}")
            return None
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
        
        # Extract cover image
        img_elem = soup.find('img')
        cover_url = ""
        if img_elem:
            cover_url = img_elem.get('src') or img_elem.get('data-src', '')
            if cover_url and not cover_url.startswith('http'):
                cover_url = urljoin(COMICK_BASE_URL, cover_url)
        
        # Extract description
        description = "Comick manga details"
        desc_elem = soup.find('div', class_='description') or soup.find('p')
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        
        # Create slug
        slug = title.lower().replace(' ', '-').replace(':', '').replace('!', '').replace('?', '').replace("'", "")
        
        return {
            'title': title,
            'cover_url': f"/api/comick-image-proxy?img_url={cover_url}" if cover_url else "",
            'description': description,
            'rating': "8.5",
            'followers': 1000,
            'chapters': 50,
            'status': 'Ongoing',
            'year': '2024',
            'slug': slug,
            'source': 'Comick',
            'url': comic_url,
            'genres': ['Action'],
            'titles': [title]
        }
        
    except Exception as e:
        logger.error(f"Error scraping Comick details: {e}")
        return None

def scrape_comick_chapter_images(chapter_url: str):
    """Scrape chapter images from Comick"""
    try:
        logger.info(f"Scraping chapter images from: {chapter_url}")
        
        response = make_request(chapter_url)
        if not response:
            logger.error(f"Failed to fetch chapter from {chapter_url}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find images in the chapter reader
        image_container = soup.find('div', class_='overflow-scroll')
        if not image_container:
            image_container = soup
        
        images = image_container.find_all('img', class_='mx-auto select-none chapter')
        if not images:
            # Fallback to any img tags
            images = image_container.find_all('img')
        
        image_urls = []
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(COMICK_BASE_URL, src)
                image_urls.append(src)
        
        logger.info(f"Found {len(image_urls)} chapter images")
        return image_urls
        
    except Exception as e:
        logger.error(f"Error scraping Comick chapter images: {e}")
        return []

def search_comick_by_title(title: str):
    """Search Comick by title"""
    try:
        logger.info(f"Searching Comick for: {title}")
        
        search_url = f"{COMICK_BASE_URL}/search?q={quote(title)}"
        response = make_request(search_url)
        
        if not response:
            logger.error(f"Failed to search Comick for {title}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        manga_list = []
        
        # Find search results
        cards = soup.find_all('div', class_='cursor-pointer')
        
        for card in cards[:10]:  # Limit to 10 results
            try:
                title_elem = card.find('p', class_='font-bold')
                title_text = title_elem.get_text(strip=True) if title_elem else ""
                
                if title.lower() in title_text.lower():
                    img_elem = card.find('img')
                    cover_url = ""
                    if img_elem:
                        cover_url = img_elem.get('src') or img_elem.get('data-src', '')
                        if cover_url and not cover_url.startswith('http'):
                            cover_url = urljoin(COMICK_BASE_URL, cover_url)
                    
                    slug = title_text.lower().replace(' ', '-')
                    
                    manga = {
                        'title': title_text,
                        'cover_url': f"/api/comick-image-proxy?img_url={cover_url}" if cover_url else "",
                        'description': f"Search result for {title}",
                        'rating': "8.5",
                        'followers': 1000,
                        'chapters': 50,
                        'status': 'Ongoing',
                        'year': '2024',
                        'slug': slug,
                        'source': 'Comick',
                        'url': f"{COMICK_BASE_URL}/comic/{slug}",
                        'genres': ['Action'],
                        'titles': [title_text]
                    }
                    manga_list.append(manga)
                    
            except Exception as e:
                logger.warning(f"Error processing search result: {e}")
                continue
        
        logger.info(f"Found {len(manga_list)} search results")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error searching Comick: {e}")
        return []