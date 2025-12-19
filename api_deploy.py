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
# Use absolute path based on script location
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(SCRIPT_DIR, 'scrapping_results.csv')
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
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medium Article Search</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #1a1a2e; color: white; }
            h1 { color: #00d4ff; }
            input[type="text"] { padding: 15px; width: 70%; font-size: 18px; border-radius: 5px; border: none; }
            button { padding: 15px 30px; font-size: 18px; background: #00d4ff; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #00a8cc; }
            .result { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .result a { color: #00d4ff; text-decoration: none; }
            .claps { color: #ffd700; }
            #results { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>🔍 Medium Article Search</h1>
        <p>Total Articles: ''' + str(len(df) if df is not None else 0) + '''</p>
        <form onsubmit="search(event)">
            <input type="text" id="query" placeholder="Enter your search keyword..." required>
            <button type="submit">Search</button>
        </form>
        <div id="results"></div>
        <script>
            async function search(e) {
                e.preventDefault();
                const query = document.getElementById('query').value;
                const res = await fetch('/search?query=' + encodeURIComponent(query));
                const data = await res.json();
                let html = '<h2>Found ' + data.count + ' results for "' + data.query + '"</h2>';
                data.articles.forEach((a, i) => {
                    html += '<div class="result"><strong>' + (i+1) + '. ' + a.title + '</strong><br>';
                    html += '<span class="claps">👏 ' + a.claps + ' claps</span><br>';
                    html += '<a href="' + a.url + '" target="_blank">' + a.url + '</a></div>';
                });
                document.getElementById('results').innerHTML = html;
            }
        </script>
    </body>
    </html>
    '''
    return html


@app.route('/search')
def search():
    query = request.args.get('query', '')
    
    if not query:
        return '''
        <html><body style="font-family:Arial;max-width:800px;margin:50px auto;padding:20px;">
        <h1>Error</h1><p>Please provide a query parameter</p>
        <p>Example: <a href="/search?query=good">/search?query=good</a></p>
        <a href="/">← Back to Home</a>
        </body></html>
        ''', 400
    
    results = search_simple(query)
    
    # Build HTML Table view
    html = f'''
    <html>
    <head><title>Search Results</title>
    <style>
        body {{ font-family: Arial; max-width: 1000px; margin: 30px auto; padding: 20px; background: #fdfdfd; color: #333; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #2c3e50; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        a {{ color: #3498db; text-decoration: none; word-break: break-all; }}
        a:hover {{ text-decoration: underline; }}
        .back {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #2c3e50; color: white; text-decoration: none; border-radius: 5px; }}
        .stats {{ font-size: 0.9em; color: #7f8c8d; margin-top: 5px; }}
    </style>
    </head>
    <body>
        <h1>🔍 Search Results: "{query}"</h1>
        <p>Found {len(results)} articles</p>
        
        <table>
            <thead>
                <tr>
                    <th width="5%">#</th>
                    <th width="40%">Title</th>
                    <th width="10%">Claps</th>
                    <th width="45%">URL</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for i, article in enumerate(results, 1):
        html += f'''
        <tr>
            <td>{i}</td>
            <td>
                <strong>{article['title']}</strong>
            </td>
            <td>👏 {article['claps']}</td>
            <td><a href="{article['url']}" target="_blank">{article['url']}</a></td>
        </tr>
        '''
    
    html += '''
            </tbody>
        </table>
        <a href="/" class="back">← Back to Search</a>
    </body>
    </html>
    '''
    
    return html


# For PythonAnywhere WSGI
load_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
