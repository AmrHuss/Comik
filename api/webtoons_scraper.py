"""
Webtoons.com Scraper Module for ManhwaVerse
============================================

A robust scraper for webtoons.com using Selenium to handle JavaScript-heavy content.
This module provides comprehensive scraping functionality for webtoons.com,
including genre-based manga discovery and detailed manga information.

Author: ManhwaVerse Development Team
Version: 2.0 - Selenium Enhanced
"""

import logging
import time
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
WEBTOONS_BASE_URL = "https://www.webtoons.com/en/"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
PAGE_LOAD_TIMEOUT = 20

class WebtoonsScraper:
    """Main scraper class for webtoons.com"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def _setup_driver(self):
        """Initialize Chrome WebDriver with optimal settings for Vercel"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Use webdriver-manager to handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            self.wait = WebDriverWait(self.driver, REQUEST_TIMEOUT)
            
            logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def _cleanup_driver(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver cleaned up successfully")
            except Exception as e:
                logger.warning(f"Error during WebDriver cleanup: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def _safe_get(self, url: str, max_retries: int = MAX_RETRIES) -> bool:
        """Safely navigate to URL with retries"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to load: {url} (attempt {attempt + 1})")
                self.driver.get(url)
                
                # Wait for page to load
                time.sleep(2)
                
                # Check if page loaded successfully
                if "webtoons.com" in self.driver.current_url:
                    logger.info(f"Successfully loaded: {url}")
                    return True
                else:
                    logger.warning(f"Unexpected redirect to: {self.driver.current_url}")
                    
            except TimeoutException:
                logger.warning(f"Timeout loading {url} (attempt {attempt + 1})")
            except WebDriverException as e:
                logger.warning(f"WebDriver error loading {url} (attempt {attempt + 1}): {e}")
            except Exception as e:
                logger.warning(f"Unexpected error loading {url} (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
        
        logger.error(f"Failed to load {url} after {max_retries} attempts")
        return False

def scrape_webtoons_by_genre(genre_name: str) -> List[Dict]:
    """
    Scrape webtoons by genre from webtoons.com using Selenium.
    
    Args:
        genre_name (str): The genre to search for (e.g., "action", "romance")
        
    Returns:
        List[Dict]: List of manga dictionaries with title, cover_url, detail_url, author
    """
    scraper = WebtoonsScraper()
    manga_list = []
    
    try:
        # Setup WebDriver
        if not scraper._setup_driver():
            logger.error("Failed to initialize WebDriver")
            return []
        
        # Construct genre URL
        genre_url = urljoin(WEBTOONS_BASE_URL, f"genres/{genre_name}/")
        logger.info(f"Scraping webtoons for genre: {genre_name} from {genre_url}")
        
        # Navigate to genre page
        if not scraper._safe_get(genre_url):
            return []
        
        # Wait for the webtoon list to load
        try:
            scraper.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.webtoon_list"))
            )
            logger.info("Webtoon list loaded successfully")
        except TimeoutException:
            logger.warning("Webtoon list did not load within timeout")
            return []
        
        # Get page source and parse with BeautifulSoup
        page_source = scraper.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        
        # Find the webtoon list
        webtoon_list_ul = soup.select_one('ul.webtoon_list')
        if not webtoon_list_ul:
            logger.warning(f"Could not find webtoon_list on {genre_url}")
            return []
        
        # Extract manga data from each list item
        for li in webtoon_list_ul.select('li'):
            try:
                # Extract title
                title_strong = li.select_one('strong.title')
                if not title_strong:
                    continue
                title = title_strong.get_text(strip=True)
                
                # Extract cover image
                cover_img = li.select_one('img')
                if not cover_img:
                    continue
                cover_url = cover_img.get('src') or cover_img.get('data-src')
                if not cover_url:
                    continue
                
                # Extract detail URL
                detail_link = li.select_one('a')
                if not detail_link or not detail_link.get('href'):
                    continue
                detail_url = urljoin(WEBTOONS_BASE_URL, detail_link.get('href'))
                
                # Extract author
                author_div = li.select_one('div.author')
                author = author_div.get_text(strip=True) if author_div else "Unknown Author"
                
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
        
        logger.info(f"Successfully scraped {len(manga_list)} webtoons for genre: {genre_name}")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error in scrape_webtoons_by_genre: {e}")
        return []
    finally:
        scraper._cleanup_driver()

def scrape_webtoons_details(detail_url: str) -> Optional[Dict]:
    """
    Scrape detailed information for a specific webtoon.
    
    Args:
        detail_url (str): The detail page URL
        
    Returns:
        Optional[Dict]: Dictionary containing detailed manga information
    """
    scraper = WebtoonsScraper()
    
    try:
        # Setup WebDriver
        if not scraper._setup_driver():
            logger.error("Failed to initialize WebDriver")
            return None
        
        logger.info(f"Scraping webtoon details from: {detail_url}")
        
        # Navigate to detail page
        if not scraper._safe_get(detail_url):
            return None
        
        # Wait for the chapter list to load
        try:
            scraper.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul#_listUl"))
            )
            logger.info("Chapter list loaded successfully")
        except TimeoutException:
            logger.warning("Chapter list did not load within timeout")
            # Continue anyway, we might still get basic info
        
        # Get page source and parse with BeautifulSoup
        page_source = scraper.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        
        # Extract title
        title_element = soup.select_one('h1.subj')
        title = title_element.get_text(strip=True) if title_element else "Unknown Title"
        
        # Extract cover image
        cover_img = soup.select_one('span.thmb img')
        cover_image = cover_img.get('src') if cover_img and cover_img.get('src') else ""
        
        # Extract description
        desc_element = soup.select_one('p.summary')
        description = desc_element.get_text(strip=True) if desc_element else "No description available"
        
        # Extract genres
        genre_elements = soup.select('h2.genre a')
        genres = [g.get_text(strip=True) for g in genre_elements] if genre_elements else []
        
        # Extract author
        author_element = soup.select_one('div.author_area .author')
        author = author_element.get_text(strip=True) if author_element else "Unknown Author"
        
        # Extract chapters
        chapters = []
        chapter_list_ul = soup.select_one('ul#_listUl')
        if chapter_list_ul:
            for li in chapter_list_ul.select('li._episodeItem'):
                try:
                    link = li.select_one('a')
                    if link and link.get('href'):
                        chapter_title_element = li.select_one('.sub_title')
                        chapter_title = chapter_title_element.get_text(strip=True) if chapter_title_element else "Chapter"
                        
                        # Extract date if available
                        date_element = li.select_one('.date')
                        chapter_date = date_element.get_text(strip=True) if date_element else "N/A"
                        
                        chapters.append({
                            'title': chapter_title,
                            'date': chapter_date,
                            'url': urljoin(WEBTOONS_BASE_URL, link.get('href'))
                        })
                except Exception as e:
                    logger.warning(f"Error parsing webtoon chapter: {e}")
                    continue
        
        # Reverse chapters to be newest first
        chapters.reverse()
        
        result = {
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
        
        logger.info(f"Successfully scraped details for: {title}")
        return result
        
    except Exception as e:
        logger.error(f"Error in scrape_webtoons_details: {e}")
        return None
    finally:
        scraper._cleanup_driver()

def scrape_webtoons_chapter_images(chapter_url: str) -> List[str]:
    """
    Scrape chapter images for a specific webtoon chapter.
    
    Args:
        chapter_url (str): The chapter reader URL
        
    Returns:
        List[str]: List of image URLs
    """
    scraper = WebtoonsScraper()
    image_urls = []
    
    try:
        # Setup WebDriver
        if not scraper._setup_driver():
            logger.error("Failed to initialize WebDriver")
            return []
        
        logger.info(f"Scraping webtoon chapter images from: {chapter_url}")
        
        # Navigate to chapter page
        if not scraper._safe_get(chapter_url):
            return []
        
        # Wait for images to load
        try:
            scraper.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#_imageList, .viewer_img"))
            )
            logger.info("Chapter images loaded successfully")
        except TimeoutException:
            logger.warning("Chapter images did not load within timeout")
            # Continue anyway, we might still get some images
        
        # Get page source and parse with BeautifulSoup
        page_source = scraper.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        
        # Find image container
        viewer_area = soup.select_one('#_imageList') or soup.select_one('.viewer_img')
        
        if viewer_area:
            for img in viewer_area.select('img'):
                src = img.get('src') or img.get('data-src')
                if src and 'img-webtoon.pstatic.net' in src:
                    image_urls.append(src)
        
        logger.info(f"Found {len(image_urls)} images for chapter: {chapter_url}")
        return image_urls
        
    except Exception as e:
        logger.error(f"Error in scrape_webtoons_chapter_images: {e}")
        return []
    finally:
        scraper._cleanup_driver()

def search_webtoons_by_title(title: str) -> List[Dict]:
    """
    Search for webtoons by title.
    
    Args:
        title (str): The title to search for
        
    Returns:
        List[Dict]: List of matching webtoons
    """
    scraper = WebtoonsScraper()
    manga_list = []
    
    try:
        # Setup WebDriver
        if not scraper._setup_driver():
            logger.error("Failed to initialize WebDriver")
            return []
        
        # Construct search URL
        search_url = f"{WEBTOONS_BASE_URL}search?keyword={title}"
        logger.info(f"Searching webtoons for: {title} at {search_url}")
        
        # Navigate to search page
        if not scraper._safe_get(search_url):
            return []
        
        # Wait for search results to load
        try:
            scraper.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search_result_list, .webtoon_list"))
            )
            logger.info("Search results loaded successfully")
        except TimeoutException:
            logger.warning("Search results did not load within timeout")
            return []
        
        # Get page source and parse with BeautifulSoup
        page_source = scraper.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        
        # Find search results
        results_container = soup.select_one('.search_result_list') or soup.select_one('.webtoon_list')
        if not results_container:
            logger.warning("No search results container found")
            return []
        
        # Extract manga data from search results
        for li in results_container.select('li'):
            try:
                # Extract title
                title_element = li.select_one('strong.title, .subj')
                if not title_element:
                    continue
                manga_title = title_element.get_text(strip=True)
                
                # Extract cover image
                cover_img = li.select_one('img')
                if not cover_img:
                    continue
                cover_url = cover_img.get('src') or cover_img.get('data-src')
                if not cover_url:
                    continue
                
                # Extract detail URL
                detail_link = li.select_one('a')
                if not detail_link or not detail_link.get('href'):
                    continue
                detail_url = urljoin(WEBTOONS_BASE_URL, detail_link.get('href'))
                
                # Extract author
                author_element = li.select_one('div.author, .author')
                author = author_element.get_text(strip=True) if author_element else "Unknown Author"
                
                manga_list.append({
                    'title': manga_title,
                    'cover_url': cover_url,
                    'detail_url': detail_url,
                    'author': author,
                    'source': 'Webtoons'
                })
                
            except Exception as e:
                logger.warning(f"Error parsing search result item: {e}")
                continue
        
        logger.info(f"Found {len(manga_list)} webtoons matching: {title}")
        return manga_list
        
    except Exception as e:
        logger.error(f"Error in search_webtoons_by_title: {e}")
        return []
    finally:
        scraper._cleanup_driver()