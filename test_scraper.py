"""
Test Script - Verify your scraper works correctly
=================================================

This script tests the scraper on a few URLs before running on all 58,000.
Always test on a small sample first!

Usage:
    python test_scraper.py
"""

from scraper import scrape_article, save_to_csv
from utils import clean_text, parse_claps, extract_keywords
import json

# Test URLs (use real Medium articles)
TEST_URLS = [
    "https://towardsdatascience.com/a-complete-guide-to-web-scraping-in-python-f47e2e7034b1",
]


def test_utility_functions():
    """Test utility functions work correctly."""
    print("\n🧪 Testing Utility Functions")
    print("-" * 40)
    
    # Test clean_text
    dirty = "  Hello   World  \n\n  Test  "
    clean = clean_text(dirty)
    print(f"clean_text: '{dirty}' -> '{clean}'")
    assert clean == "Hello World Test", "clean_text failed!"
    print("   ✅ clean_text works!")
    
    # Test parse_claps
    test_cases = [
        ("1.2K", 1200),
        ("500", 500),
        ("2.5K", 2500),
        ("1M", 1000000),
        ("", 0),
    ]
    for input_val, expected in test_cases:
        result = parse_claps(input_val)
        print(f"parse_claps: '{input_val}' -> {result} (expected: {expected})")
        assert result == expected, f"parse_claps failed for {input_val}!"
    print("   ✅ parse_claps works!")
    
    # Test extract_keywords
    text = "Machine learning and artificial intelligence are transforming data science."
    keywords = extract_keywords(text, num_keywords=3)
    print(f"extract_keywords: '{text[:50]}...' -> '{keywords}'")
    assert len(keywords) > 0, "extract_keywords returned empty!"
    print("   ✅ extract_keywords works!")


def test_scraper():
    """Test the scraper on a real URL."""
    print("\n🧪 Testing Scraper")
    print("-" * 40)
    
    for url in TEST_URLS:
        print(f"\nScraping: {url[:60]}...")
        result = scrape_article(url)
        
        if result:
            print("   ✅ Scraping successful!")
            print(f"   Title: {result['title'][:50]}...")
            print(f"   Author: {result['author_name']}")
            print(f"   Claps: {result['claps']}")
            print(f"   Reading Time: {result['reading_time']}")
            print(f"   Images: {result['num_images']}")
            print(f"   External Links: {result['num_external_links']}")
            print(f"   Keywords: {result['keywords'][:50]}...")
            
            # Save result to test file
            save_to_csv([result], 'test_output.csv')
            print("   💾 Saved to test_output.csv")
        else:
            print("   ❌ Scraping failed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("    WEB SCRAPER TEST SUITE")
    print("=" * 50)
    
    try:
        test_utility_functions()
        test_scraper()
        
        print("\n" + "=" * 50)
        print("    ALL TESTS PASSED! ✅")
        print("=" * 50)
        print("\nYou can now run the full scraper:")
        print("   python scraper.py --input urls.txt --output scrapping_results.csv")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == '__main__':
    main()
