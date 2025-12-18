"""
Utility functions for web scraping Medium articles.
This file contains helper functions used by the main scraper.
"""

import re
from typing import List, Optional
from rake_nltk import Rake

# Initialize RAKE for keyword extraction
# RAKE = Rapid Automatic Keyword Extraction
rake = Rake()


def extract_keywords(text: str, num_keywords: int = 10) -> str:
    """
    Extract keywords from text using RAKE algorithm.
    
    RAKE works by:
    1. Splitting text into candidate keywords based on stopwords
    2. Scoring each keyword based on word frequency and length
    3. Returning top-scored keywords
    
    Args:
        text: The article text to extract keywords from
        num_keywords: Number of keywords to extract (default 10)
    
    Returns:
        Comma-separated string of keywords
    """
    if not text or len(text.strip()) == 0:
        return ""
    
    try:
        rake.extract_keywords_from_text(text)
        # Get ranked phrases (returns list of tuples: (score, phrase))
        keywords = rake.get_ranked_phrases()[:num_keywords]
        return ", ".join(keywords)
    except Exception:
        return ""


def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace and special characters.
    
    Args:
        text: Raw text to clean
    
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove special unicode characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text.strip()


def parse_reading_time(time_str: str) -> str:
    """
    Extract reading time from Medium's format (e.g., "5 min read").
    
    Args:
        time_str: Raw reading time string from Medium
    
    Returns:
        Cleaned reading time string
    """
    if not time_str:
        return "N/A"
    
    # Look for pattern like "X min read"
    match = re.search(r'(\d+)\s*min', time_str.lower())
    if match:
        return f"{match.group(1)} min"
    return time_str.strip()


def parse_claps(claps_str: str) -> int:
    """
    Convert Medium claps string to integer.
    Medium shows claps like "1.2K" or "5K" for thousands.
    
    Args:
        claps_str: Raw claps string (e.g., "1.2K", "500", "10K")
    
    Returns:
        Integer count of claps
    """
    if not claps_str:
        return 0
    
    claps_str = claps_str.strip().upper()
    
    try:
        if 'K' in claps_str:
            # Convert "1.2K" to 1200
            number = float(claps_str.replace('K', ''))
            return int(number * 1000)
        elif 'M' in claps_str:
            # Convert "1.2M" to 1200000
            number = float(claps_str.replace('M', ''))
            return int(number * 1000000)
        else:
            return int(claps_str)
    except ValueError:
        return 0


def is_external_link(url: str, base_domain: str = "medium.com") -> bool:
    """
    Check if a URL is external (not from Medium).
    
    Args:
        url: The URL to check
        base_domain: The base domain to compare against
    
    Returns:
        True if external, False if internal
    """
    if not url:
        return False
    
    # External if it doesn't contain medium.com
    return base_domain not in url.lower()


def extract_image_urls(soup, article_url: str) -> List[str]:
    """
    Extract all image URLs from the article.
    
    Args:
        soup: BeautifulSoup object of the page
        article_url: The article URL (for resolving relative URLs)
    
    Returns:
        List of image URLs
    """
    image_urls = []
    
    # Find all img tags
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            # Skip small icons and tracking pixels
            if 'miro.medium.com' in src or 'cdn-images' in src:
                image_urls.append(src)
    
    return list(set(image_urls))  # Remove duplicates


def validate_url(url: str) -> bool:
    """
    Check if a URL is a valid Medium article URL.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid Medium URL, False otherwise
    """
    if not url:
        return False
    
    # Basic URL pattern check
    medium_patterns = [
        r'https?://medium\.com/',
        r'https?://[\w-]+\.medium\.com/',
        r'https?://towardsdatascience\.com/',
        r'https?://betterprogramming\.pub/',
    ]
    
    for pattern in medium_patterns:
        if re.match(pattern, url):
            return True
    
    return False


def format_csv_field(value) -> str:
    """
    Format a value for CSV output, handling special characters.
    
    Args:
        value: Any value to format
    
    Returns:
        String safe for CSV
    """
    if value is None:
        return ""
    
    value = str(value)
    # Replace newlines with spaces
    value = value.replace('\n', ' ').replace('\r', '')
    # Escape quotes
    value = value.replace('"', '""')
    
    return value
