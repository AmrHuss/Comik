# --- Filename: api/index.py ---

import logging
import requests
from urllib.parse import urljoin, quote
from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

BASE_URL = "https://asurascanz.com/"

def get_headers():
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def parse_manga_cards_from_soup(soup):
    manga_list = []
    manga_containers = soup.select('div.bs, div.bsx, div.utao.styletwo')
    for container in manga_containers:
        try:
            link_element = container.find('a', href=True)
            if not link_element: continue
            title = link_element.get('title', '').strip() or (container.find('h4') or container.find('h3') or container.find('.tt')).get_text(strip=True)
            detail_url = urljoin(BASE_URL, link_element['href'])
            img_element = container.find('img')
            if not img_element: continue
            cover_url = (img_element.get('data-src') or img_element.get('src', '')).strip()
            chapter_element = container.find('div', class_='epxs') or container.select_one('ul li a')
            latest_chapter = chapter_element.get_text(strip=True) if chapter_element else "N/A"
            if title and detail_url and cover_url:
                manga_list.append({'title': title, 'cover_url': cover_url, 'detail_url': detail_url, 'latest_chapter': latest_chapter})
        except Exception: continue
    return list({manga['detail_url']: manga for manga in manga_list}.values())

def scrape_manga_details(detail_url):
    try:
        response = requests.get(detail_url, headers=get_headers(), timeout=9)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        info_container = soup.select_one('div.main-info')
        if not info_container: return None
        title = info_container.select_one('h1.entry-title').get_text(strip=True)
        cover_image = info_container.select_one('div.thumb img')['src']
        description = info_container.select_one('div.entry-content[itemprop="description"] p').get_text(strip=True)
        rating = info_container.select_one('div.num[itemprop="ratingValue"]').get_text(strip=True)
        status = info_container.select_one('.imptdt i').get_text(strip=True)
        genres = [a.get_text(strip=True) for a in info_container.select('span.mgen a')]
        chapters = []
        chapter_list_elements = soup.select('#chapterlist ul li')
        for chapter_li in chapter_list_elements:
            link = chapter_li.find('a')
            if link and link.get('href'):
                chapters.append({
                    'title': link.select_one('.chapternum').get_text(strip=True),
                    'date': link.select_one('.chapterdate').get_text(strip=True),
                    'url': link['href']
                })
        return {'title': title, 'cover_image': cover_image, 'description': description, 'rating': rating, 'status': status, 'genres': genres, 'chapters': chapters}
    except Exception: return None

# --- API Endpoints with Correct Prefixes ---
@app.route('/api/popular', methods=['GET'])
def get_popular_manga():
    try:
        response = requests.get(BASE_URL, headers=get_headers(), timeout=9)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        manga_data = parse_manga_cards_from_soup(soup)
        return jsonify({'success': True, 'count': len(manga_data), 'data': manga_data})
    except Exception: return jsonify({'success': False, 'error': 'Failed to scrape homepage.'}), 500

@app.route('/api/manga-details', methods=['GET'])
def get_manga_details():
    detail_url = request.args.get('url')
    if not detail_url: return jsonify({'success': False, 'error': 'Manga detail URL is required.'}), 400
    manga_details = scrape_manga_details(detail_url)
    if manga_details: return jsonify({'success': True, 'data': manga_details})
    return jsonify({'success': False, 'error': 'Could not scrape details.'}), 404

@app.route('/api/chapter', methods=['GET'])
def get_chapter_images():
    chapter_url = request.args.get('url')
    if not chapter_url: return jsonify({'success': False, 'error': 'Chapter URL is required.'}), 400
    try:
        response = requests.get(chapter_url, headers=get_headers(), timeout=9)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        reader_area = soup.select_one('#readerarea, .reading-content')
        if not reader_area: return jsonify({'success': False, 'error': 'Reader area not found.'}), 404
        images = reader_area.select('img')
        image_urls = [img['src'].strip() for img in images if img.get('src') and 'asurascans.imagemanga.online' in img.get('src')]
        return jsonify({'success': True, 'count': len(image_urls), 'data': image_urls})
    except Exception: return jsonify({'success': False, 'error': 'An unexpected error occurred.'}), 500

@app.route('/api/genre', methods=['GET'])
def get_genre_manga():
    genre_name = request.args.get('name')
    if not genre_name: return jsonify({'success': False, 'error': 'Genre name is required.'}), 400
    genre_url = f"{BASE_URL}genres/{genre_name}/"
    try:
        response = requests.get(genre_url, headers=get_headers(), timeout=9)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        manga_data = parse_manga_cards_from_soup(soup)
        if not manga_data: return jsonify({'success': False, 'error': f'No manga found for genre: {genre_name}.'}), 404
        return jsonify({'success': True, 'count': len(manga_data), 'data': manga_data})
    except Exception: return jsonify({'success': False, 'error': 'Internal server error.'}), 500

@app.route('/api/search', methods=['GET'])
def search_manga():
    query = request.args.get('query')
    if not query: return jsonify({'success': False, 'error': 'Query is required.'}), 400
    search_url = f"{BASE_URL}?s={quote(query)}"
    try:
        response = requests.get(search_url, headers=get_headers(), timeout=9)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        manga_data = parse_manga_cards_from_soup(soup)
        return jsonify({'success': True, 'count': len(manga_data), 'data': manga_data})
    except Exception: return jsonify({'success': False, 'error': 'Search failed.'}), 500

# Vercel needs a root handler for the /api/index.py file itself
@app.route('/api', methods=['GET'])
def api_root():
    return jsonify({'message': 'Welcome to the ManhwaVerse API root.'})