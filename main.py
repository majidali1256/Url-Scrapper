"""
Interactive Medium Article Scraper & Search Engine
===================================================

Simple interactive script that:
1. Shows numbered list of files to scrape
2. User picks a file by number
3. Scrapes that file
4. Asks for a search word
5. Shows top 10 matching articles

Usage:
    python main.py
"""

import os
import csv
import time
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Import utility functions
from utils import extract_keywords, clean_text, parse_reading_time, parse_claps

# ============================================================================
# CONFIGURATION
# ============================================================================

PAGE_LOAD_TIMEOUT = 15
REQUEST_DELAY = 2
OUTPUT_CSV = 'scrapping_results.csv'

CSV_COLUMNS = [
    'url', 'source', 'title', 'subtitle', 'claps', 'reading_time',
    'author_name', 'author_url', 'num_images', 'image_urls',
    'external_links', 'keywords', 'text'
]

# ============================================================================
# BROWSER SETUP
# ============================================================================

def create_driver():
    """Create a Chrome browser that looks like a real user."""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    return driver


# ============================================================================
# SCRAPING FUNCTIONS
# ============================================================================

def scrape_article(driver, url):
    """Scrape a single article and return its data."""
    try:
        driver.get(url)
        time.sleep(2)
        
        if "Just a moment" in driver.title or "Attention Required" in driver.title:
            return None
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.find('h1')
        title = clean_text(title.get_text()) if title else 'N/A'
        
        subtitle_elem = soup.find('h2')
        subtitle = clean_text(subtitle_elem.get_text()) if subtitle_elem else 'N/A'
        
        article = soup.find('article') or soup.find('main') or soup.body
        paragraphs = article.find_all('p') if article else []
        text = ' '.join([clean_text(p.get_text()) for p in paragraphs if len(p.get_text()) > 20])
        
        claps = 0
        clap_elem = soup.find(attrs={'data-testid': 'clapCount'})
        if clap_elem:
            claps = parse_claps(clap_elem.get_text())
        
        reading_time = 'N/A'
        time_elem = soup.find(string=lambda s: s and 'min read' in s.lower())
        if time_elem:
            reading_time = parse_reading_time(time_elem)
        
        author_name = 'Unknown'
        author_url = ''
        author_link = soup.find('a', href=lambda h: h and '/@' in h)
        if author_link:
            author_name = clean_text(author_link.get_text())
            author_url = author_link.get('href', '')
        
        images = soup.find_all('img')
        image_urls = [img.get('src', '') for img in images if img.get('src')]
        
        keywords = extract_keywords(text)
        
        return {
            'url': url,
            'source': 'Medium',
            'title': title,
            'subtitle': subtitle,
            'claps': claps,
            'reading_time': reading_time,
            'author_name': author_name,
            'author_url': author_url,
            'num_images': len(image_urls),
            'image_urls': ';'.join(image_urls[:5]),
            'external_links': '',
            'keywords': ','.join(keywords),
            'text': text[:5000]
        }
        
    except Exception as e:
        return None


def scrape_urls(urls, output_file):
    """Scrape all URLs and save to CSV."""
    print(f"\n🌐 Setting up Chrome browser...")
    driver = create_driver()
    print("✅ Browser ready!\n")
    
    existing_urls = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_urls = {row['url'] for row in reader}
        print(f"📂 Resuming: Found {len(existing_urls)} existing entries")
    
    urls_to_scrape = [u for u in urls if u not in existing_urls]
    print(f"🔍 URLs to scrape: {len(urls_to_scrape)}")
    
    if not urls_to_scrape:
        print("✅ All URLs already scraped!")
        driver.quit()
        return
    
    if not os.path.exists(output_file):
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
    
    scraped_count = 0
    try:
        for url in tqdm(urls_to_scrape, desc="Scraping"):
            result = scrape_article(driver, url)
            if result:
                with open(output_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                    writer.writerow(result)
                scraped_count += 1
            time.sleep(REQUEST_DELAY)
    except KeyboardInterrupt:
        print("\n⏹ Scraping stopped by user")
    finally:
        driver.quit()
        print(f"\n🔒 Browser closed")
        print(f"💾 Saved {scraped_count} new articles to {output_file}")


# ============================================================================
# SEARCH FUNCTIONS
# ============================================================================

def search_articles(csv_file, query, top_k=10):
    """Search for matching articles and return top K results."""
    if not os.path.exists(csv_file):
        print(f"❌ Error: {csv_file} not found.")
        return None
    
    df = pd.read_csv(csv_file)
    print(f"\n📊 Loaded {len(df)} articles")
    
    if df.empty:
        print("❌ No articles found.")
        return None
    
    df['search_text'] = (
        df['title'].fillna('') + ' ' +
        df['subtitle'].fillna('') + ' ' +
        df['text'].fillna('') + ' ' +
        df['keywords'].fillna('')
    )
    
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(df['search_text'].tolist())
    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    df['similarity'] = similarities
    
    results = df[df['similarity'] > 0].sort_values(
        by=['similarity', 'claps'],
        ascending=[False, False]
    ).head(top_k)
    
    return results


def display_results(results, query):
    """Display search results in a nice format."""
    if results is None or results.empty:
        print(f"\n❌ No articles found matching '{query}'")
        return
    
    print(f"\n" + "=" * 60)
    print(f"🔍 TOP {len(results)} RESULTS FOR: '{query}'")
    print("=" * 60)
    
    for i, (_, row) in enumerate(results.iterrows(), 1):
        print(f"\n{i}. {row['title']}")
        print(f"   📊 Similarity: {row['similarity']:.2%}")
        print(f"   👏 Claps: {row['claps']}")
        print(f"   ⏱ Reading Time: {row['reading_time']}")
        print(f"   ✍ Author: {row['author_name']}")
        print(f"   🔗 URL: {row['url']}")
    
    print("\n" + "=" * 60)


# ============================================================================
# MAIN - SIMPLE INTERACTIVE FLOW
# ============================================================================

def main():
    print("\n" + "=" * 60)
    print("🚀 MEDIUM ARTICLE SCRAPER & SEARCH ENGINE")
    print("=" * 60)
    
    # STEP 1: Show available files with numbers
    print("\n📂 AVAILABLE FILES TO SCRAPE:")
    print("-" * 40)
    
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
    
    if not txt_files:
        print("❌ No .txt files found in current directory!")
        return
    
    for i, filename in enumerate(txt_files, 1):
        # Count lines in file
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for line in f if line.strip())
        print(f"   {i}. {filename} ({line_count} URLs)")
    
    # STEP 2: User picks a file
    print()
    while True:
        try:
            choice = input("👉 Enter file number to scrape (or 0 to skip): ").strip()
            choice = int(choice)
            if choice == 0:
                print("⏭ Skipping scraping...")
                break
            if 1 <= choice <= len(txt_files):
                selected_file = txt_files[choice - 1]
                print(f"\n✅ Selected: {selected_file}")
                
                # Load URLs
                with open(selected_file, 'r', encoding='utf-8', errors='ignore') as f:
                    urls = [line.strip() for line in f if line.strip()]
                
                print(f"📝 Total URLs in file: {len(urls)}")
                
                # Ask how many URLs to scrape
                while True:
                    count_input = input("🔢 How many URLs to scrape? (enter number or 'all'): ").strip().lower()
                    if count_input == 'all':
                        print(f"📝 Will scrape all {len(urls)} URLs")
                        break
                    try:
                        count = int(count_input)
                        if count > 0:
                            urls = urls[:count]  # Limit to requested count
                            print(f"📝 Will scrape {len(urls)} URLs")
                            break
                        else:
                            print("❌ Please enter a positive number")
                    except ValueError:
                        print("❌ Please enter a number or 'all'")
                
                # Start scraping
                scrape_urls(urls, OUTPUT_CSV)
                break
            else:
                print(f"❌ Please enter a number between 1 and {len(txt_files)} (or 0 to skip)")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n⏹ Cancelled")
            break
    
    # STEP 3: Search mode
    if os.path.exists(OUTPUT_CSV):
        print("\n" + "=" * 60)
        print("🔍 SEARCH MODE")
        print("=" * 60)
        
        while True:
            query = input("\n🔎 Enter search word (or 'exit' to quit): ").strip()
            
            if query.lower() == 'exit':
                print("\n👋 Goodbye!")
                break
            
            if not query:
                print("❌ Please enter a search word")
                continue
            
            results = search_articles(OUTPUT_CSV, query)
            display_results(results, query)
    else:
        print("\n❌ No scraped data found. Please scrape some URLs first.")
    
    print("\n👋 Done!")


if __name__ == '__main__':
    main()
