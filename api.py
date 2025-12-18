"""
Medium Article Search API - Part B of Assignment
================================================

This script creates a REST API that:
- Takes text/keywords as input
- Searches through scraped articles
- Returns top 10 similar articles sorted by claps

Usage:
    python api.py

Then access:
    GET http://localhost:5001/search?query=machine+learning

How it works:
1. On startup, loads the CSV data into memory
2. Uses TF-IDF (Term Frequency-Inverse Document Frequency) to vectorize text
3. When a query comes in, finds similar articles using cosine similarity
4. Returns top 10 results sorted by claps
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ============================================================================
# FLASK APP SETUP
# ============================================================================

# Create Flask application
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing)
# This allows your API to be called from web pages on different domains
CORS(app)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Path to the scraped data CSV file
CSV_FILE = 'scrapping_results.csv'

# Number of results to return
TOP_K = 10

# Global variables for data and vectorizer
df = None  # Pandas DataFrame with our data
vectorizer = None  # TF-IDF vectorizer
tfidf_matrix = None  # Pre-computed TF-IDF vectors for all articles


# ============================================================================
# DATA LOADING AND PREPROCESSING
# ============================================================================

def load_data():
    """
    Load the scraped data from CSV and prepare for searching.
    
    This function:
    1. Reads the CSV file into a pandas DataFrame
    2. Creates a combined text field for searching
    3. Initializes the TF-IDF vectorizer
    4. Pre-computes TF-IDF vectors for all articles
    """
    global df, vectorizer, tfidf_matrix
    
    if not os.path.exists(CSV_FILE):
        print(f"⚠ Warning: {CSV_FILE} not found. API will return empty results.")
        print("  Run the scraper first: python scraper.py --input urls.txt")
        df = pd.DataFrame()
        return
    
    # Load CSV into DataFrame
    df = pd.read_csv(CSV_FILE)
    print(f"📊 Loaded {len(df)} articles from {CSV_FILE}")
    
    # Create combined text for searching
    # We combine title, subtitle, text, and keywords for better matching
    df['search_text'] = (
        df['title'].fillna('') + ' ' +
        df['subtitle'].fillna('') + ' ' +
        df['text'].fillna('') + ' ' +
        df['keywords'].fillna('')
    )
    
    # Initialize TF-IDF Vectorizer
    # TF-IDF = Term Frequency × Inverse Document Frequency
    # - TF: How often a word appears in a document
    # - IDF: How rare a word is across all documents
    # Words that are common everywhere (like "the") get low weight
    # Words that are specific to certain articles get high weight
    vectorizer = TfidfVectorizer(
        max_features=5000,  # Keep top 5000 words
        stop_words='english',  # Remove common English words
        ngram_range=(1, 2)  # Include single words and pairs
    )
    
    # Fit and transform all article texts
    # This converts each article into a vector of numbers
    tfidf_matrix = vectorizer.fit_transform(df['search_text'].tolist())
    print("✅ TF-IDF vectors computed for all articles")


def search_articles(query: str, top_k: int = TOP_K) -> list:
    """
    Search for articles similar to the query.
    
    How it works:
    1. Convert query text to TF-IDF vector
    2. Calculate cosine similarity between query and all articles
    3. Sort by similarity, then by claps
    4. Return top K results
    
    Args:
        query: Search keywords/text
        top_k: Number of results to return
    
    Returns:
        List of dictionaries with article URL and title
    """
    if df is None or df.empty:
        return []
    
    # Transform query to TF-IDF vector
    query_vector = vectorizer.transform([query])
    
    # Calculate cosine similarity
    # Cosine similarity measures the angle between two vectors
    # 1 = identical directions (very similar)
    # 0 = perpendicular (unrelated)
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    # Add similarity scores to dataframe
    df['similarity'] = similarities
    
    # Filter articles with some similarity (threshold > 0)
    similar_articles = df[df['similarity'] > 0].copy()
    
    if similar_articles.empty:
        # If no similar articles found, return top clapped articles
        print("  No similar articles found, returning top clapped articles")
        similar_articles = df.copy()
    
    # Sort by similarity first, then by claps
    # This ensures we get relevant articles with high engagement
    similar_articles = similar_articles.sort_values(
        by=['similarity', 'claps'],
        ascending=[False, False]
    )
    
    # Get top K results
    top_articles = similar_articles.head(top_k)
    
    # Format results
    results = []
    for _, row in top_articles.iterrows():
        results.append({
            'url': row['url'],
            'title': row['title'],
            'claps': int(row['claps']) if pd.notna(row['claps']) else 0,
            'author': row['author_name'] if pd.notna(row['author_name']) else 'Unknown',
            'similarity_score': round(float(row['similarity']), 4)
        })
    
    return results


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """
    Home endpoint - shows API usage information.
    """
    return jsonify({
        'name': 'Medium Article Search API',
        'description': 'Search for similar Medium articles based on keywords',
        'endpoints': {
            '/search': {
                'method': 'GET',
                'params': {
                    'query': 'Your search keywords (required)',
                    'limit': 'Number of results (optional, default 10)'
                },
                'example': '/search?query=machine+learning'
            },
            '/stats': {
                'method': 'GET',
                'description': 'Get statistics about the dataset'
            }
        },
        'total_articles': len(df) if df is not None else 0
    })


@app.route('/search')
def search():
    """
    Search endpoint - finds similar articles.
    
    Query Parameters:
        query: The search keywords (required)
        limit: Number of results to return (optional, default 10)
    
    Returns:
        JSON with list of matching articles
    """
    # Get query parameter
    query = request.args.get('query', '')
    
    if not query:
        return jsonify({
            'error': 'Please provide a query parameter',
            'example': '/search?query=data+science'
        }), 400
    
    # Get optional limit parameter
    try:
        limit = int(request.args.get('limit', TOP_K))
        limit = min(limit, 50)  # Cap at 50 results
    except ValueError:
        limit = TOP_K
    
    # Search for articles
    results = search_articles(query, limit)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'articles': results
    })


@app.route('/stats')
def stats():
    """
    Statistics endpoint - shows dataset information.
    """
    if df is None or df.empty:
        return jsonify({
            'error': 'No data loaded. Run the scraper first.'
        }), 404
    
    return jsonify({
        'total_articles': len(df),
        'total_claps': int(df['claps'].sum()) if 'claps' in df.columns else 0,
        'avg_claps': round(float(df['claps'].mean()), 2) if 'claps' in df.columns else 0,
        'unique_authors': df['author_name'].nunique() if 'author_name' in df.columns else 0,
        'articles_with_images': int((df['num_images'] > 0).sum()) if 'num_images' in df.columns else 0
    })


@app.route('/article/<int:index>')
def get_article(index: int):
    """
    Get a specific article by index.
    """
    if df is None or df.empty:
        return jsonify({'error': 'No data loaded'}), 404
    
    if index < 0 or index >= len(df):
        return jsonify({'error': 'Article not found'}), 404
    
    article = df.iloc[index].to_dict()
    return jsonify(article)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n🚀 Starting Medium Article Search API")
    print("=" * 50)
    
    # Load data on startup
    load_data()
    
    print("\n📡 API Endpoints:")
    print("   GET /           - API info")
    print("   GET /search     - Search articles")
    print("   GET /stats      - Dataset statistics")
    print("\n🌐 Starting server on http://localhost:5001")
    print("   Press Ctrl+C to stop\n")
    
    # Run the Flask development server
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5001,
        debug=True  # Enable debug mode for development
    )
