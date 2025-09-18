#!/usr/bin/env python3
"""
Webtoons.com Scraper Module for ManhwaVerse
===========================================

This module provides scraping functionality for webtoons.com,
including genre-based manga discovery and detailed manga information.
Uses Selenium for dynamic content handling.

Author: ManhwaVerse Development Team
Version: 2.0
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin, urlparse, quote
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBTOONS_BASE_URL = "https://www.webtoons.com/en/"
REQUEST_TIMEOUT = 20
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

def initialize_selenium_driver():
    """Initialize a headless Chrome WebDriver with optimized settings."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Faster loading
    chrome_options.add_argument(f"user-agent={get_headers()['User-Agent']}")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        logger.error(f"Error initializing Selenium driver: {e}")
        return None

def scrape_genre(genre_name):
    """
    Scrape webtoons by genre from webtoons.com using Selenium.
    
    Args:
        genre_name (str): The genre to scrape (e.g., 'action', 'romance')
    
    Returns:
        list: List of manga dictionaries with title, cover_url, detail_url, author, source
    """
    genre_url = urljoin(WEBTOONS_BASE_URL, f"genres/{genre_name}/")
    logger.info(f"Scraping webtoons for genre: {genre_name} from {genre_url}")
    
    driver = None
    try:
        driver = initialize_selenium_driver()
        if not driver:
            logger.error("Failed to initialize Selenium driver")
            return []
        
        driver.get(genre_url)
        
        # Wait for the main list of webtoons to be present
        WebDriverWait(driver, REQUEST_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.webtoon_list'))
        )
        
        # Additional wait for content to load
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        manga_list = []
        
        webtoon_list_ul = soup.select_one('ul.webtoon_list')
        if not webtoon_list_ul:
            logger.warning(f"Could not find webtoon_list on {genre_url}")
            return []
        
        for li in webtoon_list_ul.select('li'):
            try:
                title_strong = li.select_one('strong.title')
                cover_img = li.select_one('img')
                detail_link = li.select_one('a')
                author_div = li.select_one('div.author')
                
                if not (title_strong and cover_img and detail_link and author_div):
                    continue
                
                title = title_strong.get_text(strip=True)
                cover_url = cover_img.get('src') or cover_img.get('data-src')
                detail_url = urljoin(WEBTOONS_BASE_URL, detail_link.get('href'))
                author = author_div.get_text(strip=True)
                
                manga_list.append({
                    'title': title,
                    'cover_url': cover_url,
                    'detail_url': detail_url,
                    'author': author,
                    'source': 'Webtoons'
                })
            except Exception as e:
                logger.warning(f"Error parsing webtoon item: {e}")
                continue
        
        logger.info(f"Found {len(manga_list)} webtoons for genre: {genre_name}")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error scraping webtoons by genre: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def scrape_details(detail_url):
    """
    Scrape detailed information for a specific webtoon using Selenium.
    
    Args:
        detail_url (str): The detail page URL of the webtoon
    
    Returns:
        dict: Dictionary containing all manga details including chapters
    """
    logger.info(f"Scraping webtoon details from: {detail_url}")
    driver = None
    try:
        driver = initialize_selenium_driver()
        if not driver:
            logger.error("Failed to initialize Selenium driver")
            return None
        
        driver.get(detail_url)
        
        # Wait for the chapter list container to be present
        WebDriverWait(driver, REQUEST_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul#_listUl'))
        )
        
        # Additional wait for content to load
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        # Extract title
        title_element = soup.select_one('h1.subj')
        title = title_element.get_text(strip=True) if title_element else "Unknown Title"
        
        # Extract cover image
        cover_img = soup.select_one('span.thmb img')
        cover_image = cover_img['src'] if cover_img and cover_img.get('src') else ""
        
        # Extract description
        desc_element = soup.select_one('p.summary')
        description = desc_element.get_text(strip=True) if desc_element else "No description available"
        
        # Extract genres (Webtoons often has categories, not explicit genres like Asura)
        genre_elements = soup.select('h2.genre a')
        genres = [g.get_text(strip=True) for g in genre_elements]
        
        # Extract author
        author_element = soup.select_one('div.author_area p.author')
        author = author_element.get_text(strip=True) if author_element else "Unknown Author"
        
        # Extract chapters with pagination handling
        chapters = []
        chapter_list_ul = soup.select_one('ul#_listUl')
        
        if chapter_list_ul:
            # Get initial chapters
            for li in chapter_list_ul.select('li._episodeItem'):
                try:
                    link = li.select_one('a')
                    if link and link.get('href'):
                        chapter_title_element = li.select_one('p.sub_title')
                        chapter_title = chapter_title_element.get_text(strip=True) if chapter_title_element else "Chapter"
                        
                        chapters.append({
                            'title': chapter_title,
                            'date': 'N/A',  # Webtoons doesn't usually show dates in the list
                            'url': urljoin(WEBTOONS_BASE_URL, link['href'])
                        })
                except Exception as e:
                    logger.warning(f"Error parsing webtoon chapter: {e}")
                    continue
            
            # Try to load more chapters by clicking "Next" button
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'a.pg_next')
                if next_button and next_button.is_enabled():
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(2)  # Wait for new content to load
                    
                    # Parse additional chapters
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    chapter_list_ul = soup.select_one('ul#_listUl')
                    if chapter_list_ul:
                        for li in chapter_list_ul.select('li._episodeItem'):
                            try:
                                link = li.select_one('a')
                                if link and link.get('href'):
                                    chapter_title_element = li.select_one('p.sub_title')
                                    chapter_title = chapter_title_element.get_text(strip=True) if chapter_title_element else "Chapter"
                                    
                                    # Check if chapter already exists
                                    chapter_url = urljoin(WEBTOONS_BASE_URL, link['href'])
                                    if not any(ch['url'] == chapter_url for ch in chapters):
                                        chapters.append({
                                            'title': chapter_title,
                                            'date': 'N/A',
                                            'url': chapter_url
                                        })
                            except Exception as e:
                                logger.warning(f"Error parsing additional webtoon chapter: {e}")
                                continue
            except Exception as e:
                logger.info(f"No next page button found or error clicking it: {e}")
        
        # Reverse chapters to be newest first
        chapters.reverse()
        
        return {
            'title': title,
            'cover_image': cover_image,
            'description': description,
            'rating': 'N/A',  # Webtoons uses likes, not star ratings
            'status': 'Ongoing',  # Placeholder, needs more complex logic
            'genres': genres,
            'author': author,
            'chapters': chapters,
            'source': 'Webtoons'
        }
        
    except Exception as e:
        logger.error(f"Error scraping webtoon details: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def scrape_chapter_images(chapter_url):
    """
    Scrape chapter images for a specific webtoon chapter using Selenium.
    
    Args:
        chapter_url (str): The chapter reader URL
    
    Returns:
        list: List of image URLs for the chapter
    """
    logger.info(f"Scraping webtoon chapter images from: {chapter_url}")
    driver = None
    try:
        driver = initialize_selenium_driver()
        if not driver:
            logger.error("Failed to initialize Selenium driver")
            return []
        
        driver.get(chapter_url)
        
        # Wait for images to be present
        WebDriverWait(driver, REQUEST_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#_imageList img'))
        )
        
        # Additional wait for all images to load
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        image_urls = []
        viewer_area = soup.select_one('#_imageList')
        
        if viewer_area:
            for img in viewer_area.select('img'):
                src = img.get('src') or img.get('data-src')
                if src and 'img-webtoon.pstatic.net' in src:  # Specific domain for webtoons images
                    image_urls.append(src)
        
        logger.info(f"Found {len(image_urls)} images for chapter: {chapter_url}")
        return image_urls
        
    except Exception as e:
        logger.error(f"Error scraping webtoon chapter images: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def search_by_title(query):
    """
    Search for webtoons by title on webtoons.com using Selenium.
    
    Args:
        query (str): The search query
    
    Returns:
        list: List of search results
    """
    search_url = urljoin(WEBTOONS_BASE_URL, f"search?keyword={quote(query)}")
    logger.info(f"Searching webtoons for title: {query} from {search_url}")
    
    driver = None
    try:
        driver = initialize_selenium_driver()
        if not driver:
            logger.error("Failed to initialize Selenium driver")
            return []
        
        driver.get(search_url)
        
        # Wait for search results to load
        WebDriverWait(driver, REQUEST_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.search_result_list'))
        )
        
        # Additional wait for content to load
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        results = []
        
        for li in soup.select('ul.search_result_list li'):
            try:
                title_element = li.select_one('p.subj')
                detail_link = li.select_one('a')
                cover_img = li.select_one('img')
                
                if title_element and detail_link and cover_img:
                    title = title_element.get_text(strip=True)
                    detail_url = urljoin(WEBTOONS_BASE_URL, detail_link.get('href'))
                    cover_url = cover_img.get('src') or cover_img.get('data-src')
                    
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
    finally:
        if driver:
            driver.quit()