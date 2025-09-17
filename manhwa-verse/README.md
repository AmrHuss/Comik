# 🎌 ManhwaVerse - Complete Manga Reading Platform

A modern, responsive website for reading manhwa and webtoons with a complete Flask API backend that scrapes data from Asura Scans.

## ✨ Features

### Frontend
- **Modern Dark Theme** - Premium dark design with purple accents
- **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **Dynamic Content** - Real-time data loading from API
- **Interactive Navigation** - Smooth page transitions and active states
- **Manga Reader** - Dedicated reader page for chapter viewing

### Backend API
- **Flask REST API** - Clean, well-documented endpoints
- **CORS Enabled** - Frontend can access API without issues
- **Web Scraping** - Automated data extraction from Asura Scans
- **Error Handling** - Comprehensive error handling and logging
- **Data Validation** - Ensures clean, valid data

## 🚀 Quick Start

### 1. Setup
```bash
# Run the setup script
python setup.py

# Or install dependencies manually
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python app.py
```

### 3. Open the Frontend
Open `index.html` in your web browser, or visit:
- **API**: http://127.0.0.1:5000
- **Frontend**: Open `index.html` in your browser

## 📁 Project Structure

```
manhwa-verse/
├── app.py                 # Flask API server
├── requirements.txt       # Python dependencies
├── setup.py              # Setup script
├── index.html            # Homepage
├── popular.html          # Popular manga page
├── new-releases.html     # New releases page
├── genres.html           # Browse by genre page
├── reader.html           # Manga reader page
├── assets/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   ├── js/
│   │   └── main.js       # Frontend JavaScript
│   └── images/
│       └── TowerOfGod.jpg # Sample image
└── README.md             # This file
```

## 🔌 API Endpoints

### GET /api/popular
Get popular manga from Asura Scans.

**Response:**
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "title": "Solo Leveling",
      "cover_url": "https://asurascans.com/covers/solo-leveling.jpg",
      "detail_url": "https://asurascans.com/manga/solo-leveling/"
    }
  ]
}
```

### GET /api/chapter?url=CHAPTER_URL
Get chapter images from a specific chapter.

**Response:**
```json
{
  "success": true,
  "count": 15,
  "data": [
    "https://asurascans.com/manga/solo-leveling/chapter-1/page-1.jpg",
    "https://asurascans.com/manga/solo-leveling/chapter-1/page-2.jpg"
  ]
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "ManhwaVerse API is running",
  "version": "1.0.0"
}
```

## 🎨 Frontend Pages

### Homepage (index.html)
- Hero section with featured manga
- Trending manga grid
- Latest updates section
- Genre browsing buttons

### Popular (popular.html)
- Filterable popular manga
- Time-based filters (This Week, This Month, All Time)
- Responsive manga grid

### New Releases (new-releases.html)
- Latest manga releases
- Clean grid layout
- Real-time data loading

### Genres (genres.html)
- Visual genre browsing
- Styled genre cards
- Hover effects and animations

### Reader (reader.html)
- Chapter image viewer
- Navigation controls
- Responsive image display

## 🛠️ Technology Stack

### Backend
- **Python 3.7+**
- **Flask** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Requests** - HTTP library
- **BeautifulSoup4** - HTML parsing
- **LXML** - XML/HTML parser

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with variables
- **JavaScript (ES6+)** - Dynamic functionality
- **Google Fonts** - Typography

## 🔧 Configuration

### API Configuration
The API base URL can be changed in `assets/js/main.js`:
```javascript
const API_BASE_URL = 'http://127.0.0.1:5000';
```

### Scraping Configuration
Scraping settings can be modified in `app.py`:
- Base URL for Asura Scans
- Request headers
- Retry logic
- Data validation rules

## 📱 Responsive Design

The website is fully responsive with breakpoints:
- **Desktop**: 1024px and above
- **Tablet**: 768px - 1023px
- **Mobile**: 480px - 767px
- **Small Mobile**: Below 480px

## 🎯 Usage Examples

### Loading Popular Manga
```javascript
// The frontend automatically loads popular manga on page load
// Data is fetched from /api/popular and displayed in grids
```

### Loading Chapter Images
```javascript
// Load chapter images for the reader
const images = await loadChapterImages('https://asurascans.com/manga/chapter-1/');
```

### Creating Manga Cards
```javascript
// Manga cards are created dynamically from API data
const mangaCard = createMangaCard({
  title: 'Solo Leveling',
  cover_url: 'https://example.com/cover.jpg',
  detail_url: 'https://example.com/manga/solo-leveling/'
});
```

## 🐛 Troubleshooting

### Common Issues

1. **API not responding**
   - Check if Flask server is running
   - Verify the API URL in main.js
   - Check browser console for errors

2. **No manga data loading**
   - Check if Asura Scans is accessible
   - Verify scraping selectors in app.py
   - Check API logs for errors

3. **CORS errors**
   - Ensure Flask-CORS is installed
   - Check CORS configuration in app.py

4. **Images not loading**
   - Check if image URLs are valid
   - Verify network connectivity
   - Check browser console for 404 errors

### Debug Mode

Enable debug logging by modifying the logging level in `app.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Deployment

### Local Development
1. Run `python app.py`
2. Open `index.html` in browser
3. API available at http://127.0.0.1:5000

### Production Deployment
1. Use a production WSGI server (e.g., Gunicorn)
2. Set up reverse proxy (e.g., Nginx)
3. Configure environment variables
4. Set up SSL certificates
5. Configure domain and DNS

## 📝 Development

### Adding New Features
1. Backend: Modify `app.py` for new API endpoints
2. Frontend: Update `main.js` for new functionality
3. Styling: Modify `style.css` for visual changes

### Code Structure
- **Backend**: Single file (`app.py`) with modular functions
- **Frontend**: Organized JavaScript with clear separation of concerns
- **Styling**: CSS variables for easy theming

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please respect the terms of service of the websites being scraped.

## 🙏 Acknowledgments

- Asura Scans for providing manga content
- Flask community for the excellent framework
- BeautifulSoup for HTML parsing capabilities

---

**ManhwaVerse** - Your ultimate destination for reading the best manhwa and webtoons! 🎌
