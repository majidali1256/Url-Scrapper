# Medium Web Scraper Assignment

## Overview
This project processes Medium articles for data science analysis.
- **Part A**: Web Scraper (Selenium-based) to extract article data.
- **Part B**: Flask API to search for similar articles.

## Prerequisites
- Python 3.8+
- Google Chrome installed (for Selenium)

## Setup
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This will also install Selenium and WebDriver Manager.*

2. **Download NLTK Data** (Run once)
   ```bash
   python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
   ```

## Part A: Web Scraper
The scraper uses Selenium to bypass Medium's anti-bot protection.

**Run the scraper:**
```bash
python scraper.py --input urls.txt --output scrapping_results.csv
```

**Options:**
- `--input`: File with URLs (default: urls.txt)
- `--output`: Output CSV file (default: scrapping_results.csv)
- `--url`: Scrape a single URL for testing
- `--no-resume`: Start fresh (ignore existing CSV)

**Example:**
```bash
python scraper.py --url "https://medium.com/@ageitgey/machine-learning-is-fun-80ea3ec3c471"
```

## Part B: Search API
The API searches your scraped data using TF-IDF similarity.

1. **Start the API:**
   ```bash
   python api.py
   ```

2. **Search Articles:**
   Open your browser or use curl:
   ```
   http://localhost:5001/search?query=machine+learning
   ```

**API Endpoints:**
- `GET /search?query=...` - Returns top 10 similar articles
- `GET /stats` - View dataset statistics

## Project Files
- `scraper.py`: Main Selenium scraper
- `api.py`: Flask API
- `utils.py`: Helper functions
- `urls.txt`: List of URLs to scrape
- `scrapping_results.csv`: Output data
