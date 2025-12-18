"""
Medium Article Search API - Deployment Version
===============================================

This is a simplified version for deploying to PythonAnywhere.
It provides an API endpoint that:
- Takes text/keywords as input
- Returns top 10 similar articles (URL + Title) sorted by claps

Deploy to: https://www.pythonanywhere.com (Free tier)

Endpoints:
    GET /search?query=machine+learning
    GET /
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# Load data on startup
CSV_FILE = 'scrapping_results.csv'
df = None

def load_data():
    global df
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        print(f"Loaded {len(df)} articles")
    else:
        df = pd.DataFrame()
        print("No data file found")

# Simple keyword matching (no sklearn dependency for easier deployment)
def search_simple(query, top_k=10):
    if df is None or df.empty:
        return []
    
    query_words = query.lower().split()
    scores = []
    
    for idx, row in df.iterrows():
        text = str(row.get('title', '')) + ' ' + str(row.get('text', '')) + ' ' + str(row.get('keywords', ''))
        text = text.lower()
        
        # Count matching words
        score = sum(1 for word in query_words if word in text)
        if score > 0:
            scores.append((idx, score, row.get('claps', 0)))
    
    # Sort by score first, then by claps
    scores.sort(key=lambda x: (-x[1], -x[2]))
    
    results = []
    for idx, score, claps in scores[:top_k]:
        row = df.iloc[idx]
        results.append({
            'url': row.get('url', ''),
            'title': row.get('title', 'N/A'),
            'claps': int(claps) if pd.notna(claps) else 0
        })
    
    return results


@app.route('/')
def home():
    return jsonify({
        'name': 'Medium Article Search API',
        'usage': '/search?query=your+keywords',
        'example': '/search?query=machine+learning',
        'total_articles': len(df) if df is not None else 0
    })


@app.route('/search')
def search():
    query = request.args.get('query', '')
    
    if not query:
        return jsonify({
            'error': 'Please provide a query parameter',
            'example': '/search?query=education'
        }), 400
    
    results = search_simple(query)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'articles': results
    })


# For PythonAnywhere WSGI
load_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
