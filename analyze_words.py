import pandas as pd
from collections import Counter
import re
import os

def get_top_words():
    if not os.path.exists('scrapping_results.csv'):
        print("❌ 'scrapping_results.csv' not found.")
        return

    try:
        df = pd.read_csv('scrapping_results.csv')
        
        # Combine all text
        all_text = ' '.join(df['title'].dropna().astype(str) + ' ' + df['text'].dropna().astype(str))
        
        # Tokenize and clean
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        
        # extensive stop words list
        stop_words = {
            'the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'it', 'for', 'with', 'as', 'was', 'on', 'at', 
            'by', 'an', 'be', 'this', 'which', 'or', 'from', 'but', 'not', 'are', 'you', 'have', 'had', 'they', 
            'we', 'he', 'she', 'his', 'her', 'their', 'my', 'i', 'me', 'him', 'so', 'if', 'all', 'one', 'has', 
            'would', 'could', 'can', 'will', 'do', 'no', 'what', 'who', 'when', 'where', 'why', 'how', 'there', 
            'out', 'up', 'down', 'into', 'over', 'under', 'about', 'then', 'than', 'just', 'more', 'some', 
            'very', 'like', 'see', 'saw', 'said', 'say', 'says', 'been', 'were', 'your', 'did', 'them', 'now',
            'time', 'will', 'make' # often common in medium articles
        }
        
        filtered_words = [w for w in words if w not in stop_words]
        
        top_10 = Counter(filtered_words).most_common(10)
        
        print("\n📊 TOP 10 WORDS IN SCRAPED DATA:")
        print("================================")
        for i, (word, count) in enumerate(top_10, 1):
            print(f"{i}. {word}: {count}")
            
    except Exception as e:
        print(f"Error analyzing data: {e}")

if __name__ == "__main__":
    get_top_words()
