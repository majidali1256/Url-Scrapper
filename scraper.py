"""
Medium Article Web Scraper (Selenium Version) - Part A of Assignment
====================================================================

This version uses Selenium with a real browser to avoid being blocked by Medium.

Why Selenium?
- Medium blocks simple HTTP requests (403 Forbidden)
- Selenium controls a real browser (Chrome)
- This makes requests look like a real user

Usage:
    python scraper_selenium.py --input urls.txt --output scrapping_results.csv
    python scraper_selenium.py --url "https://medium.com/article" --output result.csv
"""

import argparse
import csv
import time
import os
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import Dict, List, Optional

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Import our utility functions
from utils import (
    extract_keywords,
    clean_text,
    parse_reading_time,
    parse_claps,
    is_external_link,
    format_csv_field
)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Time to wait for page to load (seconds)
PAGE_LOAD_TIMEOUT = 15

# Delay between requests to avoid rate limiting
REQUEST_DELAY = 2.0

# Run browser in headless mode (no visible window)
HEADLESS = True


# ============================================================================
# BROWSER SETUP
# ============================================================================

def create_driver():
    """
    Create and configure the Chrome WebDriver.
    
    WebDriver is like a remote control for Chrome browser.
    We configure it to:
    - Run in headless mode (no visible window) 
    - Disable images (faster loading)
    - Use a realistic user agent
    """
    print("🌐 Setting up Chrome browser...")
    
    # Configure Chrome options
    chrome_options = Options()
    
    if HEADLESS:
        chrome_options.add_argument("--headless=new")  # No window
    
    # Make browser look more like a real user
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Realistic user agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Disable automation flags (reduces detection)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Use webdriver-manager to automatically download ChromeDriver
    # This ensures you always have the correct version
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    print("✅ Browser ready!")
    return driver


# ============================================================================
# SCRAPING FUNCTIONS
# ============================================================================

def scrape_article(driver, url: str) -> Optional[Dict]:
    """
    Scrape a single Medium article using Selenium.
    """
    try:
        driver.get(url)
        # Step 2: Wait for article content to load
        # We wait for the article tag to appear
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article, h1, .pw-post-body-paragraph"))
            )
            # Scroll down to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        except:
            time.sleep(3)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        # Check for Cloudflare/Blocking
        page_title = soup.title.string if soup.title else ""
        if "Just a moment" in page_title or "Attention Required" in page_title:
            print(f"  ⚠ Blocked by Cloudflare for {url}")
            return None
            
        title = extract_title(soup)
        # Step 5: Extract all fields
        subtitle = extract_subtitle(soup)
        text = extract_article_text(soup)
        image_urls = extract_image_urls(soup)
        external_links = extract_external_links(soup)
        author_name, author_url = extract_author_info(soup)
        claps = extract_claps(soup)
        reading_time = extract_reading_time(soup)
        keywords = extract_keywords(text)
        
        return {
            'url': url,
            'title': title,
            'subtitle': subtitle,
            'text': text,
            'num_images': len(image_urls),
            'image_urls': '; '.join(image_urls),
            'num_external_links': len(external_links),
            'author_name': author_name,
            'author_url': author_url,
            'claps': claps,
            'reading_time': reading_time,
            'keywords': keywords
        }
        
    except Exception as e:
        print(f"  ⚠ Error scraping {url}: {e}")
        return None


def extract_title(soup: BeautifulSoup) -> str:
    """Extract article title."""
    # Try h1 first (most common)
    h1 = soup.find('h1')
    if h1 and h1.text.strip():
        return clean_text(h1.text)
    
    # Try Open Graph title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return clean_text(og_title['content'])
    
    # Try page title
    title_tag = soup.find('title')
    if title_tag:
        return clean_text(title_tag.text.split('|')[0])  # Remove "| Medium" suffix
    
    return "N/A"


def extract_subtitle(soup: BeautifulSoup) -> str:
    """Extract article subtitle/description."""
    # Try meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return clean_text(meta_desc['content'])
    
    # Try Open Graph description
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        return clean_text(og_desc['content'])
    
    # Try first h2 after h1
    h1 = soup.find('h1')
    if h1:
        h2 = h1.find_next('h2')
        if h2 and h2.text.strip():
            return clean_text(h2.text)
    
    return "N/A"


def extract_article_text(soup: BeautifulSoup) -> str:
    """Extract the main article text."""
    # Medium articles are usually in a 'section' or 'article'
    # The main text is often in paragraphs with specific classes
    
    text_parts = []
    
    # Strategy 1: Look for the main article container
    article = soup.find('article') or soup.find('section')
    
    if article:
        # Get paragraphs
        paragraphs = article.find_all(['p', 'h2', 'h3', 'blockquote', 'li'])
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 5:
                text_parts.append(text)
    
    # Strategy 2: If finding container failed, look for specific Medium classes
    if not text_parts:
        # standard medium paragraph class
        paras = soup.find_all('p', class_='pw-post-body-paragraph')
        text_parts = [p.get_text(strip=True) for p in paras if p.get_text(strip=True)]
    
    # Strategy 3: Fallback - look for all paragraphs in the body
    if not text_parts and soup.body:
        paras = soup.body.find_all('p')
        # Filter out short menu items/footer text
        text_parts = [p.get_text(strip=True) for p in paras 
                     if len(p.get_text(strip=True)) > 20]
    
    if text_parts:
        return clean_text(' '.join(text_parts))
        
    return "N/A"


def extract_image_urls(soup: BeautifulSoup) -> List[str]:
    """Extract image URLs from the article."""
    image_urls = []
    
    # Find article container
    article = soup.find('article') or soup
    
    # Find all images
    for img in article.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            # Filter for actual content images (not icons/avatars)
            if 'miro.medium.com' in src and 'max' in src:
                image_urls.append(src)
    
    return list(set(image_urls))  # Remove duplicates


def extract_external_links(soup: BeautifulSoup) -> List[str]:
    """Extract external links (not Medium/internal)."""
    external_links = []
    
    article = soup.find('article') or soup
    
    for link in article.find_all('a', href=True):
        href = link['href']
        
        # Check if external
        if href.startswith('http') and is_external_link(href):
            external_links.append(href)
    
    return list(set(external_links))


def extract_author_info(soup: BeautifulSoup) -> tuple:
    """Extract author name and profile URL."""
    author_name = "N/A"
    author_url = "N/A"
    
    # Try to find author link (usually contains @ in href)
    author_links = soup.find_all('a', href=lambda x: x and '/@' in x)
    
    for link in author_links:
        text = link.get_text(strip=True)
        if text and len(text) > 1 and not text.startswith('@'):
            author_name = text
            author_url = link['href']
            if not author_url.startswith('http'):
                author_url = 'https://medium.com' + author_url
            break
    
    # Fallback: check meta author
    if author_name == "N/A":
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            author_name = meta_author['content']
    
    return author_name, author_url


def extract_claps(soup: BeautifulSoup) -> int:
    """Extract the number of claps."""
    # 1. Look for specific testid
    clap_elements = soup.find_all(attrs={"data-testid": "clapCount"})
    for elem in clap_elements:
        return parse_claps(elem.get_text(strip=True))
    
    # 2. Look for buttons that might contain claps
    buttons = soup.find_all('button')
    for btn in buttons:
        text = btn.get_text(strip=True)
        # Regex for "1.5K" or "50"
        import re
        if re.match(r'^\d+(\.\d+)?[KkMm]?$', text):
            # Check context - surrounding elements oraria-labels
            if 'clap' in (btn.get('aria-label') or '').lower():
                return parse_claps(text)
    
    # 3. Check aria-labels on any element
    for elem in soup.find_all(attrs={'aria-label': True}):
        label = elem['aria-label']
        if 'clap' in label.lower():
            import re
            match = re.search(r'(\d+(\.\d+)?[KkMm]?)', label)
            if match:
                return parse_claps(match.group(1))
                
    # 4. Aggressive text search for "123 claps" pattern
    # This might be risky but good for fallback
    import re
    text = soup.get_text(" ", strip=True)
    # Look for "50 claps" or "1.2K claps"
    match = re.search(r'(\d+(\.\d+)?[KkMm]?)\s*claps', text, re.IGNORECASE)
    if match:
        return parse_claps(match.group(1))

    return 0


def extract_reading_time(soup: BeautifulSoup) -> str:
    """Extract estimated reading time."""
    # 1. Look for data-testid
    elem = soup.find(attrs={"data-testid": "storyReadTime"})
    if elem:
        return parse_reading_time(elem.get_text(strip=True))
        
    # 2. Look for text "min read"
    for elem in soup.find_all(['span', 'p']):
        text = elem.get_text(strip=True)
        if 'min read' in text.lower() and len(text) < 20:
             return parse_reading_time(text)
             
    # 3. Aria labels
    for elem in soup.find_all(attrs={'aria-label': True}):
        if 'min read' in elem['aria-label'].lower():
            return parse_reading_time(elem['aria-label'])
            
    return "N/A"


# ============================================================================
# MAIN SCRAPING LOGIC
# ============================================================================

def load_urls(input_file: str) -> List[str]:
    """Load URLs from a text file."""
    urls = []
    
    with open(input_file, 'r') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):
                urls.append(url)
    
    print(f"📝 Loaded {len(urls)} URLs from {input_file}")
    return urls


def save_to_csv(data: List[Dict], output_file: str):
    """Save scraped data to CSV file."""
    if not data:
        print("⚠ No data to save!")
        return
    
    columns = [
        'url', 'title', 'subtitle', 'text', 'num_images',
        'image_urls', 'num_external_links', 'author_name',
        'author_url', 'claps', 'reading_time', 'keywords'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"💾 Saved {len(data)} articles to {output_file}")


def scrape_all(urls: List[str], output_file: str, resume: bool = True):
    """
    Scrape all URLs and save to CSV.
    
    Features resume capability - can continue from where it left off.
    """
    scraped_data = []
    scraped_urls = set()
    
    # Load existing data if resuming
    if resume and os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scraped_data.append(row)
                scraped_urls.add(row.get('url', ''))
        print(f"📂 Resuming: Found {len(scraped_data)} existing entries")
    
    # Filter URLs
    urls_to_scrape = [u for u in urls if u not in scraped_urls]
    print(f"🔍 URLs to scrape: {len(urls_to_scrape)}")
    
    if not urls_to_scrape:
        print("✅ All URLs already scraped!")
        return
    
    # Create browser
    driver = create_driver()
    
    try:
        # Scrape each URL
        for url in tqdm(urls_to_scrape, desc="Scraping"):
            result = scrape_article(driver, url)
            
            if result:
                scraped_data.append(result)
                
                # Save progress every 10 articles
                if len(scraped_data) % 10 == 0:
                    save_to_csv(scraped_data, output_file)
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
        
        # Final save
        save_to_csv(scraped_data, output_file)
        
    finally:
        # Always close the browser
        driver.quit()
        print("🔒 Browser closed")
    
    print(f"\n✅ Scraping complete!")
    print(f"   Total articles: {len(scraped_data)}")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scrape Medium articles using Selenium'
    )
    
    parser.add_argument('--input', '-i', help='File with URLs to scrape')
    parser.add_argument('--url', '-u', help='Single URL to scrape')
    parser.add_argument('--output', '-o', default='scrapping_results.csv',
                       help='Output CSV file')
    parser.add_argument('--no-resume', action='store_true',
                       help='Start fresh, ignore existing data')
    
    args = parser.parse_args()
    
    if not args.input and not args.url:
        parser.print_help()
        print("\n❌ Please provide --input or --url")
        return
    
    print("\n🚀 Medium Article Scraper (Selenium)")
    print("=" * 50)
    
    if args.url:
        # Single URL mode
        driver = create_driver()
        try:
            result = scrape_article(driver, args.url)
            if result:
                save_to_csv([result], args.output)
                print(f"\n✅ Scraped: {result['title'][:50]}...")
            else:
                print("❌ Failed to scrape article")
        finally:
            driver.quit()
    else:
        # Batch mode
        if not os.path.exists(args.input):
            print(f"❌ File not found: {args.input}")
            return
        
        urls = load_urls(args.input)
        scrape_all(urls, args.output, resume=not args.no_resume)


if __name__ == '__main__':
    main()
