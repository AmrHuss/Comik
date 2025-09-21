#!/usr/bin/env python3
"""
Comick.live Scraper - Cloudflare Bypass Ready
=============================================

A specialized scraper for Comick.live that handles:
- Cloudflare protection bypass
- Action genre manga scraping
- Chapter data extraction
- Image URL extraction with proxy support

Author: ManhwaVerse Development Team
Date: 2025
Version: 1.0
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

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

def scrape_comick_action_genre():
    """Scrape action genre manga from Comick.live using real scraping"""
    try:
        # Try to scrape from Comick's actual website
        url = "https://comick.live/search?genres=action&order_by=user_follow_count"
        headers = get_comick_headers()
        
        logger.info(f"Scraping Comick action genre from: {url}")
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        # Parse the HTML to extract manga data
        soup = BeautifulSoup(response.content, 'html.parser')
        
        manga_list = []
        
        # Look for manga cards using the correct selectors from the HTML structure
        manga_cards = soup.find_all('div', class_='cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700')
        
        logger.info(f"Found {len(manga_cards)} manga cards")
        
        for i, card in enumerate(manga_cards[:20]):  # Limit to 20
            try:
                # Extract title from the correct element
                title_elem = card.find('p', class_='font-bold truncate dark:text-gray-300')
                title = title_elem.get_text(strip=True) if title_elem else f"Comick Manga {i+1}"
                
                # Extract cover image from the correct element
                img_elem = card.find('img', class_='select-none rounded-md object-cover')
                cover_url = ""
                if img_elem:
                    cover_url = img_elem.get('src') or img_elem.get('data-src', '')
                    if cover_url and not cover_url.startswith('http'):
                        cover_url = "https://comick.live" + cover_url
                
                # Extract description
                desc_elem = card.find('p', class_='prose prose-sm dark:prose-invert text-gray-600 dark:text-gray-400 text-xs md:text-sm md:pr-12 overflow-ellipsis mt-2 line-clamp-2')
                description = desc_elem.get_text(strip=True) if desc_elem else "Popular manga available on Comick.live"
                
                # Extract additional titles
                titles_elem = card.find('p', class_='text-xs md:text-sm text-gray-600 dark:text-gray-400 line-clamp-1 truncate')
                additional_titles = []
                if titles_elem:
                    additional_titles = [t.strip() for t in titles_elem.get_text(strip=True).split(',')]
                
                # Extract chapters
                chapters_elem = card.find('span', string=lambda text: text and 'chapters' in text)
                chapters = 0
                if chapters_elem:
                    chapters_text = chapters_elem.get_text(strip=True)
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)', chapters_text)
                    if match:
                        chapters = float(match.group(1))
                
                # Extract year
                year_elem = card.find('span', title='Published')
                year = year_elem.get_text(strip=True) if year_elem else "2024"
                
                # Extract followers
                followers_elem = card.find('span', class_='text-xs xl:text-lg')
                followers = 0
                if followers_elem:
                    followers_text = followers_elem.get_text(strip=True)
                    if 'k' in followers_text:
                        followers = int(float(followers_text.replace('k', '')) * 1000)
                    else:
                        followers = int(followers_text.replace(',', ''))
                
                # Extract rating
                rating_elem = card.find('div', title='Rating count')
                rating = 0
                if rating_elem:
                    rating_text = rating_elem.find('span', class_='text-xs xl:text-lg')
                    if rating_text:
                        rating = float(rating_text.get_text(strip=True))
                
                # Create slug from title
                slug = title.lower().replace(' ', '-').replace(':', '').replace('!', '').replace('?', '').replace("'", "")
                
                manga = {
                    'title': title,
                    'description': description[:200] + '...' if len(description) > 200 else description,
                    'cover_url': f"/api/comick-image-proxy?img_url={cover_url}" if cover_url else "",
                    'rating': str(rating) if rating > 0 else "N/A",
                    'followers': followers,
                    'chapters': int(chapters) if chapters > 0 else 0,
                    'status': 'Ongoing',
                    'year': year,
                    'slug': slug,
                    'source': 'Comick',
                    'url': f"https://comick.live/comic/{slug}",
                    'genres': ['Action'],
                    'titles': [title] + additional_titles
                }
                
                manga_list.append(manga)
                
            except Exception as e:
                logger.warning(f"Error processing manga card {i+1}: {e}")
                continue
        
        if manga_list:
            logger.info(f"Successfully scraped {len(manga_list)} Comick manga")
            return manga_list
        else:
            logger.warning("No manga found, trying fallback")
            return scrape_comick_fallback()
        
    except Exception as e:
        logger.error(f"Error scraping Comick action genre: {e}")
        return scrape_comick_fallback()


def scrape_comick_details(comic_url: str):
    """Scrape detailed information for a specific Comick comic"""
    try:
        headers = get_comick_headers()
        
        logger.info(f"Scraping Comick details: {comic_url}")
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(comic_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract comic data from script tags
        script_tags = soup.find_all('script')
        comic_data = None
        
        for script in script_tags:
            if script.string and 'comic' in script.string and 'title' in script.string:
                try:
                    script_content = script.string
                    # Look for comic object
                    start_idx = script_content.find('"comic":{')
                    if start_idx != -1:
                        # Find the end of the comic object
                        brace_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(script_content[start_idx:], start_idx):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        comic_json = script_content[start_idx:end_idx]
                        comic_json = comic_json.replace('"comic":', '')
                        comic_data = json.loads(comic_json)
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse comic details from script: {e}")
                    continue
        
        if not comic_data:
            logger.warning("No comic details found in page scripts")
            return None
        
        # Extract chapters data
        chapters_data = None
        for script in script_tags:
            if script.string and 'chapters' in script.string and 'hid' in script.string:
                try:
                    script_content = script.string
                    start_idx = script_content.find('"chapters":[')
                    if start_idx != -1:
                        bracket_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(script_content[start_idx:], start_idx):
                            if char == '[':
                                bracket_count += 1
                            elif char == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        chapters_json = script_content[start_idx:end_idx]
                        chapters_json = chapters_json.replace('"chapters":', '')
                        chapters_data = json.loads(chapters_json)
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse chapters from script: {e}")
                    continue
        
        # Build manga details
        manga_details = {
            'title': comic_data.get('title', 'Unknown Title'),
            'description': comic_data.get('description', 'No description available'),
            'cover_url': comic_data.get('default_thumbnail', ''),
            'rating': str(comic_data.get('bayesian_rating', 'N/A')),
            'followers': comic_data.get('user_follow_count', 0),
            'chapters': comic_data.get('last_chapter', 0),
            'status': comic_data.get('status', 'Unknown'),
            'year': comic_data.get('year', 'Unknown'),
            'slug': comic_data.get('slug', ''),
            'source': 'Comick',
            'url': comic_url,
            'genres': comic_data.get('genres', []),
            'titles': comic_data.get('titles', []),
            'chapters_list': []
        }
        
        # Use proxy for cover image
        if manga_details['cover_url']:
            manga_details['cover_url'] = f"/api/comick-image-proxy?img_url={manga_details['cover_url']}"
        
        # Process chapters
        if chapters_data:
            for chapter in chapters_data[:50]:  # Limit to first 50 chapters
                try:
                    chapter_info = {
                        'title': f"Chapter {chapter.get('chap', 'Unknown')}",
                        'chapter_number': chapter.get('chap', 0),
                        'url': f"https://comick.live/comic/{comic_data.get('slug', '')}/{chapter.get('hid', '')}-chapter-{chapter.get('chap', '')}-{chapter.get('lang', 'en')}",
                        'language': chapter.get('lang', 'en'),
                        'uploaded_at': chapter.get('updated_at', ''),
                        'group_name': chapter.get('group_name', ['Unknown'])[0] if chapter.get('group_name') else 'Unknown'
                    }
                    manga_details['chapters_list'].append(chapter_info)
                except Exception as e:
                    logger.warning(f"Error processing chapter: {e}")
                    continue
        
        logger.info(f"Successfully scraped Comick details for: {manga_details['title']}")
        return manga_details
        
    except Exception as e:
        logger.error(f"Error scraping Comick details for {comic_url}: {e}")
        return None

def scrape_comick_chapter_images(chapter_url: str):
    """Scrape chapter images from Comick.live"""
    try:
        headers = get_comick_headers()
        
        logger.info(f"Scraping Comick chapter images: {chapter_url}")
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(chapter_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the script tag containing chapter data
        script_tags = soup.find_all('script')
        chapter_data = None
        
        for script in script_tags:
            if script.string and 'chapter' in script.string and 'images' in script.string:
                try:
                    script_content = script.string
                    # Look for chapter object
                    start_idx = script_content.find('"chapter":{')
                    if start_idx != -1:
                        # Find the end of the chapter object
                        brace_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(script_content[start_idx:], start_idx):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        chapter_json = script_content[start_idx:end_idx]
                        chapter_json = chapter_json.replace('"chapter":', '')
                        chapter_data = json.loads(chapter_json)
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse chapter data from script: {e}")
                    continue
        
        if not chapter_data or 'images' not in chapter_data:
            logger.warning("No chapter images found in page scripts")
            return []
        
        images = []
        for img in chapter_data['images']:
            try:
                # Use proxy for all images
                proxy_url = f"/api/comick-image-proxy?img_url={img['url']}&chapter_url={chapter_url}"
                images.append(proxy_url)
            except Exception as e:
                logger.warning(f"Error processing image: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(images)} Comick chapter images")
        return images
        
    except Exception as e:
        logger.error(f"Error scraping Comick chapter images for {chapter_url}: {e}")
        return []

def search_comick_by_title(title: str):
    """Search Comick.live by title"""
    try:
        search_url = f"https://comick.live/search?q={title}"
        headers = get_comick_headers()
        
        logger.info(f"Searching Comick for: {title}")
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(search_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Similar to scrape_comick_action_genre but for search results
        script_tags = soup.find_all('script')
        comic_data = None
        
        for script in script_tags:
            if script.string and 'comics' in script.string and 'user_follow_count' in script.string:
                try:
                    script_content = script.string
                    start_idx = script_content.find('"comics":[')
                    if start_idx != -1:
                        bracket_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(script_content[start_idx:], start_idx):
                            if char == '[':
                                bracket_count += 1
                            elif char == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        comics_json = script_content[start_idx:end_idx]
                        comics_json = comics_json.replace('"comics":', '')
                        comic_data = json.loads(comics_json)
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse search results from script: {e}")
                    continue
        
        if not comic_data:
            logger.warning("No search results found")
            return []
        
        manga_list = []
        for comic in comic_data[:10]:  # Limit to first 10 results
            try:
                manga = {
                    'title': comic.get('title', 'Unknown Title'),
                    'description': comic.get('description', 'No description available'),
                    'cover_url': comic.get('default_thumbnail', ''),
                    'rating': str(comic.get('bayesian_rating', 'N/A')),
                    'followers': comic.get('user_follow_count', 0),
                    'chapters': comic.get('last_chapter', 0),
                    'status': comic.get('status', 'Unknown'),
                    'year': comic.get('year', 'Unknown'),
                    'slug': comic.get('slug', ''),
                    'source': 'Comick',
                    'url': f"https://comick.live/comic/{comic.get('slug', '')}",
                    'genres': comic.get('genres', []),
                    'titles': comic.get('titles', [])
                }
                
                # Use proxy for cover image
                if manga['cover_url']:
                    manga['cover_url'] = f"/api/comick-image-proxy?img_url={manga['cover_url']}"
                
                manga_list.append(manga)
                
            except Exception as e:
                logger.warning(f"Error processing search result {comic.get('title', 'unknown')}: {e}")
                continue
        
        logger.info(f"Found {len(manga_list)} Comick search results for: {title}")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error searching Comick for {title}: {e}")
        return []
