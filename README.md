# URL Scrapper

A Python project for scraping Medium articles into CSV data and searching that dataset through a Flask API.

## Project Overview

This repository includes:
- A Selenium-based scraper for collecting article metadata/content from Medium URLs.
- A TF-IDF powered search API over scraped results.
- A simple interactive CLI flow that combines scraping + search in one script.
- A lightweight PythonAnywhere deployment variant of the API.

## Features

- Scrape one URL or a batch of URLs from a text file.
- Resume scraping from an existing CSV file.
- Extract title, subtitle, body text, author info, claps, reading time, keywords, and image/link stats.
- Search scraped content with cosine similarity ranking.
- API endpoints for search and dataset statistics.

## Setup

### 1) Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

The scraper scripts also import `selenium` and `webdriver-manager`, so install them as well if they are not already available in your environment:

```bash
pip install selenium webdriver-manager
```

### 3) Download NLTK data (required for keyword extraction)

```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
```

## Run Instructions

### Scraper (batch mode)

```bash
python scraper.py --input "10k Urls.txt" --output scrapping_results.csv
```

### Scraper (single URL)

```bash
python scraper.py --url "https://medium.com/some-article" --output scrapping_results.csv
```

### Interactive scraper + search flow

```bash
python main.py
```

### Search API

```bash
python api.py
```

API default URL: `http://localhost:5001`

## API Usage Examples

### Search articles

```bash
curl "http://localhost:5001/search?query=machine+learning&limit=5"
```

### Dataset stats

```bash
curl "http://localhost:5001/stats"
```

### API info

```bash
curl "http://localhost:5001/"
```

## Configuration / Environment Variables

This project currently uses in-code constants (for example `CSV_FILE`, `TOP_K`, request delays/timeouts) and does **not** require environment variables.

## Testing and Validation

There is no formal pytest/unittest suite configured.

Available project test/check script:

```bash
python test_scraper.py
```

## Build Commands

No separate build step is defined for this repository.

## Deployment Notes

- `api_deploy.py` is a simplified API version intended for PythonAnywhere.
- `DEPLOY.md` contains the PythonAnywhere deployment walkthrough.

## Project Structure

- `scraper.py` - Main Selenium scraper CLI.
- `main.py` - Interactive scrape + search workflow.
- `api.py` - Flask API using TF-IDF/cosine similarity.
- `api_deploy.py` - Simplified deployment API.
- `utils.py` - Text cleaning/parsing/keyword helper utilities.
- `test_scraper.py` - Script-based checks for utilities and scraping flow.
- `analyze_words.py` - Top-word analysis from scraped CSV data.
- `requirements.txt` - Pinned Python dependencies.
- `DEPLOY.md` - Deployment guide.
- `scrapping_results.csv` - Existing scraped dataset file.
- `10k Urls.txt` - Example URL input file.

## Technology Stack

- **Language:** Python
- **Web/API:** Flask, Flask-CORS
- **Scraping:** Selenium, BeautifulSoup4, lxml, webdriver-manager
- **Data Processing:** pandas, NumPy
- **Search/ML:** scikit-learn (TF-IDF, cosine similarity)
- **NLP/Keywords:** NLTK, RAKE-NLTK
- **Utilities:** tqdm
- **Production server dependency:** gunicorn
