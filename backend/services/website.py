import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json
import logging
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text):
    """Removing extra whitespace and newlines."""
    return re.sub(r'\s+', ' ', text).strip()

def analyze_url(url: str, openai_key: str):
    """
    Fetches URL content and uses OpenAI to extract company details 
    and suggested competitors.
    """
    if not url.startswith('http'):
        url = 'https://' + url

    try:
        # 1. Fetch Website Content
        logger.info(f"Fetching URL: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text content (limit to first 4000 chars to save tokens)
        text_content = clean_text(soup.get_text())[:4000]
        
        # Look for App Links specifically
        app_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'play.google.com' in href or 'apps.apple.com' in href:
                app_links.append(href)
        
        # 2. Call OpenAI
        client = OpenAI(api_key=openai_key)
        
        prompt = f"""
        Analyze the following website content and extract information about the company.
        
        Website Content:
        {text_content}
        
        Found App Links: {app_links}
        
        Return a JSON object with the following fields:
        - name: Company Name
        - description: A short description of what they do (max 1 sentence)
        - competitors: A list of 5 direct competitor names (only names)
        - android_id: The Android Package ID if found (e.g., com.example.app), else null.
        - apple_id: The Apple App ID if found (e.g., 123456789), else null.
        
        If you can't find specific app IDs, try to infer the most likely company name to search for later.
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured company data from website text. Return ONLY JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        content = completion.choices[0].message.content
        data = json.loads(content)
        
        # Format the result to match what the frontend expects (list of companies)
        # First item is the main company
        output = [{
            "company_name": data.get("name"),
            "website": url,
            "description": data.get("description"),
            "android_id": data.get("android_id"),
            "apple_id": data.get("apple_id"),
            "is_main": True
        }]
        
        # Add competitors
        for comp in data.get("competitors", []):
            output.append({
                "company_name": comp,
                "website": None, # We don't have their URLs yet
                "description": "Competitor",
                "android_id": None,
                "apple_id": None,
                "is_main": False
            })
            
        return output

    except Exception as e:
        logger.error(f"Error analyzing website: {e}")
        return {"error": str(e)}
