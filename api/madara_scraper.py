#!/usr/bin/env python3
"""
MadaraScans.com Scraper Module for ManhwaVerse
==============================================

This module provides scraping functionality for madarascans.com,
using the same requests + BeautifulSoup approach as AsuraScanz.

Author: ManhwaVerse Development Team
Version: 1.0 - Vercel Compatible
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

MADARA_BASE_URL = "https://madarascans.com/"
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
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    logger.error(f"All {max_retries} attempts failed for {url}")
    return None

def scrape_popular():
    """
    Scrape popular and recently updated manga from MadaraScans homepage.
    
    Returns:
        list: List of manga dictionaries with title, cover_url, detail_url, latest_chapter, source
    """
    logger.info(f"Scraping popular manga from MadaraScans homepage: {MADARA_BASE_URL}")
    
    try:
        response = make_request(MADARA_BASE_URL)
        if not response:
            logger.warning(f"Failed to fetch MadaraScans homepage: {MADARA_BASE_URL}")
            return []
        
        # Check if we got a valid response
        if len(response.content) < 1000:  # Very small response might be an error page
            logger.warning(f"Received suspiciously small response ({len(response.content)} bytes) for {MADARA_BASE_URL}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        manga_list = []
        
        # Look for manga cards in containers with class .bs or .bsx
        manga_cards = soup.select('.bs .bsx') or soup.select('.bsx')
        
        if not manga_cards:
            # Try alternative selectors
            manga_cards = soup.select('div[class*="bs"]')
            if not manga_cards:
                manga_cards = soup.select('div[class*="manga"]')
                if not manga_cards:
                    # Try even more generic selectors
                    manga_cards = soup.select('div[class*="card"]') or soup.select('article')
        
        logger.info(f"Found {len(manga_cards)} manga cards")
        
        # If no cards found, return empty list (likely anti-scraping or site structure changed)
        if not manga_cards:
            logger.warning(f"No manga cards found on MadaraScans homepage - possible anti-scraping protection")
            return []
        
        for card in manga_cards:
            try:
                # Extract title from the title attribute of the main <a> tag
                main_link = card.select_one('a[title]')
                if not main_link:
                    continue
                
                title = main_link.get('title', '').strip()
                if not title:
                    continue
                
                # Extract cover image from <img> tag
                cover_img = card.select_one('img')
                cover_url = ""
                if cover_img:
                    cover_url = cover_img.get('src') or cover_img.get('data-src') or ""
                    if cover_url and not cover_url.startswith('http'):
                        cover_url = urljoin(MADARA_BASE_URL, cover_url)
                
                # Extract detail URL from href of main <a> tag
                detail_url = main_link.get('href', '')
                if detail_url and not detail_url.startswith('http'):
                    detail_url = urljoin(MADARA_BASE_URL, detail_url)
                
                # Extract latest chapter from <div class="epxs">
                latest_chapter = ""
                epxs_div = card.select_one('.epxs')
                if epxs_div:
                    latest_chapter = epxs_div.get_text(strip=True)
                
                # Only add if we have essential data
                if title and detail_url:
                    manga_list.append({
                        'title': title,
                        'cover_url': cover_url,
                        'detail_url': detail_url,
                        'latest_chapter': latest_chapter,
                        'source': 'MadaraScans'
                    })
                    
            except Exception as e:
                logger.warning(f"Error parsing manga card: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(manga_list)} popular manga from MadaraScans")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error scraping MadaraScans popular: {e}")
        return []

def scrape_details(detail_url):
    """
    Scrape detailed information for a specific manga from MadaraScans.
    
    Args:
        detail_url (str): The detail page URL of the manga
    
    Returns:
        dict: Dictionary containing all manga details including chapters
    """
    logger.info(f"Scraping MadaraScans details from: {detail_url}")
    
    try:
        response = make_request(detail_url)
        if not response:
            logger.error(f"Failed to fetch detail page: {detail_url}")
            return None
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title from <h1 class="entry-title">
        title_element = soup.select_one('h1.entry-title')
        title = title_element.get_text(strip=True) if title_element else "Unknown Title"
        
        # Extract cover image from <img> inside <div class="thumb">
        cover_img = soup.select_one('.thumb img')
        cover_image = ""
        if cover_img and cover_img.get('src'):
            cover_image = cover_img.get('src')
            if not cover_image.startswith('http'):
                cover_image = urljoin(MADARA_BASE_URL, cover_image)
        
        # Extract description from <div class="entry-content"> paragraph
        desc_element = soup.select_one('.entry-content p')
        description = desc_element.get_text(strip=True) if desc_element else "No description available"
        
        # Extract genres from <a> tags inside <span class="mgen">
        genre_elements = soup.select('.mgen a')
        genres = [g.get_text(strip=True) for g in genre_elements]
        
        # Extract status from <i> tag inside <div class="imptdt"> that contains "Status"
        status = "Unknown"
        imptdt_divs = soup.select('.imptdt')
        for div in imptdt_divs:
            if 'status' in div.get_text().lower():
                i_tag = div.select_one('i')
                if i_tag:
                    status = i_tag.get_text(strip=True)
                break
        
        # Extract chapters from <div id="chapterlist"> -> <ul> -> <li>
        chapters = []
        chapter_list_div = soup.select_one('#chapterlist')
        
        if chapter_list_div:
            chapter_ul = chapter_list_div.select_one('ul')
            if chapter_ul:
                chapter_items = chapter_ul.select('li')
                
                for item in chapter_items:
                    try:
                        # Extract chapter title from <span class="chapternum">
                        chapter_title_element = item.select_one('.chapternum')
                        chapter_title = chapter_title_element.get_text(strip=True) if chapter_title_element else "Chapter"
                        
                        # Extract chapter date from <span class="chapterdate">
                        chapter_date_element = item.select_one('.chapterdate')
                        chapter_date = chapter_date_element.get_text(strip=True) if chapter_date_element else "N/A"
                        
                        # Extract chapter URL from <a> tag's href
                        chapter_link = item.select_one('a')
                        chapter_url = ""
                        if chapter_link and chapter_link.get('href'):
                            chapter_url = chapter_link.get('href')
                            if not chapter_url.startswith('http'):
                                chapter_url = urljoin(MADARA_BASE_URL, chapter_url)
                        
                        if chapter_title and chapter_url:
                            chapters.append({
                                'title': chapter_title,
                                'date': chapter_date,
                                'url': chapter_url
                            })
                    except Exception as e:
                        logger.warning(f"Error parsing chapter item: {e}")
                        continue
        
        # Reverse chapters to be newest first
        chapters.reverse()
        
        return {
            'title': title,
            'cover_image': cover_image,
            'description': description,
            'rating': 'N/A',  # MadaraScans doesn't show ratings in the format we need
            'status': status,
            'genres': genres,
            'author': 'Unknown Author',  # MadaraScans doesn't show author in the format we need
            'chapters': chapters,
            'source': 'MadaraScans'
        }
        
    except Exception as e:
        logger.error(f"Error scraping MadaraScans details: {e}")
        return None
