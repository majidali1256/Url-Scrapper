# Deploying Your API to PythonAnywhere (FREE)

## Step 1: Create a Free Account
1. Go to [https://www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Click **"Start for free"**
3. Sign up with your email

## Step 2: Upload Your Files
1. Go to the **Files** tab
2. Upload these 2 files:
   - `api_deploy.py`
   - `scrapping_results.csv`

## Step 3: Create a Web App
1. Go to the **Web** tab
2. Click **"Add a new web app"**
3. Choose **Flask** and **Python 3.9**
4. Set the source code path to: `/home/YOUR_USERNAME/api_deploy.py`

## Step 4: Configure WSGI
1. Click on the **WSGI configuration file** link
2. Replace the content with:

```python
import sys
path = '/home/YOUR_USERNAME'
if path not in sys.path:
    sys.path.insert(0, path)

from api_deploy import app as application
```

3. Save the file

## Step 5: Install Dependencies
1. Go to **Consoles** tab
2. Start a **Bash** console
3. Run: `pip install flask flask-cors pandas`

## Step 6: Reload & Test
1. Go back to **Web** tab
2. Click **"Reload"**
3. Your API is now live at:
   `https://YOUR_USERNAME.pythonanywhere.com/search?query=education`

## API Usage

**Search endpoint:**
```
https://YOUR_USERNAME.pythonanywhere.com/search?query=machine+learning
```

**Response:**
```json
{
  "query": "machine learning",
  "count": 10,
  "articles": [
    {"url": "https://...", "title": "Article Title", "claps": 150},
    ...
  ]
}
```
