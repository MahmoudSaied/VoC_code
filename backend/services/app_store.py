from google_play_scraper import search
from app_store_scraper import AppStore
from openai import OpenAI
import json
import logging
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_google_play(query):
    try:
        results = search(query, lang='en', country='us')
        if results:
            return results[0]['appId']
    except Exception as e:
        logger.warning(f"Google Play search failed for {query}: {e}")
    return None

def search_app_store(query):
    try:
        app = AppStore(country='us', app_name=query)
        app.search(query)
        if app.search_results:
            return str(app.search_results[0]['trackId'])
    except Exception as e:
        logger.warning(f"App Store search failed for {query}: {e}")
    return None

def resolve_app_ids(company_list, openai_key):
    """
    Takes a list of company objects and attempts to fill in missing 
    android_id and apple_id fields.
    """
    
    def process_company(company):
        name = company.get('company_name') or company.get('name')
        if not name:
            return company
            
        # 1. Try filling Android ID
        if not company.get('android_id'):
            found_id = search_google_play(name)
            if found_id:
                company['android_id'] = found_id
                
        # 2. Try filling Apple ID
        if not company.get('apple_id'):
            found_id = search_app_store(name)
            if found_id:
                company['apple_id'] = found_id
                
        # 3. Fallback: If still missing, maybe use OpenAI to guess package name patterns? 
        # (Skipping for now to keep it fast, search is usually good enough)
        
        return company

    # Run in parallel to speed up
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_company, company_list))
        
    return results
