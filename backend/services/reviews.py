import pandas as pd
from google_play_scraper import Sort, reviews
import requests
import json
import os
import boto3
from datetime import datetime
import concurrent.futures
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
RUN_GOOGLE_PLAY = True
RUN_APP_STORE = True
COUNTRIES = ['sa', 'ae', 'kw', 'bh', 'qa', 'om', 'us']

# 1. Google Play Scraper
def scrape_google_play(brand_name, app_id):
    if not app_id:
        return pd.DataFrame()

    logger.info(f"--- 🟢 Starting Google Play Scrape for {brand_name} ({app_id}) ---")
    six_months_ago = datetime.now() - pd.DateOffset(months=6)
    
    def process_country(country):
        try:
            continuation_token = None
            country_reviews = []
            while True:
                result, continuation_token = reviews(
                    app_id, lang='en', country=country, sort=Sort.NEWEST,
                    count=200, continuation_token=continuation_token
                )
                if not result: break
                
                batch_oldest_date = None
                for r in result:
                    r_date = r['at']
                    if r_date < six_months_ago: continue
                    r['country'] = country 
                    country_reviews.append(r)
                    batch_oldest_date = r_date

                if batch_oldest_date and batch_oldest_date < six_months_ago: break
                if not continuation_token: break
                if len(country_reviews) > 2000: break
            
            return country_reviews
        except Exception as e:
            return []

    all_reviews = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(COUNTRIES)) as executor:
        future_to_country = {executor.submit(process_country, country): country for country in COUNTRIES}
        for future in concurrent.futures.as_completed(future_to_country):
            res = future.result()
            if res: all_reviews.extend(res)

    if not all_reviews: return pd.DataFrame()

    df = pd.DataFrame(all_reviews)
    if df.empty: return pd.DataFrame()

    needed_cols = ['content', 'score', 'at', 'userName', 'country']
    for c in needed_cols:
        if c not in df.columns: return pd.DataFrame()

    df = df[needed_cols]
    df.columns = ['text', 'rating', 'date', 'source_user', 'region']
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df['platform'] = df['region'].apply(lambda x: f'Google Play ({x.upper()})')
    df['brand'] = brand_name
    df = df.drop(columns=['region'])
    return df

# 2. Apple App Store Scraper
def scrape_app_store(brand_name, app_id):
    if not app_id: return pd.DataFrame()
    logger.info(f"--- 🍎 Starting Apple App Store Scrape for {brand_name} ---")
    six_months_ago = pd.Timestamp(datetime.now() - pd.DateOffset(months=6))
    
    def process_country(country):
        country_reviews = []
        try:
            for page in range(1, 11): 
                url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code != 200: break
                    data = resp.json()
                    entries = data.get('feed', {}).get('entry', [])
                    if not entries: break
                    if isinstance(entries, dict): entries = [entries]

                    stop_paging = False
                    for entry in entries:
                        try:
                            date_str = entry.get('updated', {}).get('label', '')
                            entry_date = pd.to_datetime(date_str)
                            if entry_date.tz_localize(None) < six_months_ago:
                                stop_paging = True
                                continue
                            review = {
                                'text': entry.get('content', {}).get('label', ''),
                                'rating': int(entry.get('im:rating', {}).get('label', '0')),
                                'date': entry_date.strftime('%Y-%m-%d'),
                                'source_user': entry.get('author', {}).get('name', {}).get('label', 'Anonymous'),
                                'platform': f'App Store ({country.upper()})',
                                'brand': brand_name
                            }
                            country_reviews.append(review)
                        except: continue
                    if stop_paging: break
                except: break
        except: pass
        return country_reviews

    all_reviews = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(COUNTRIES)) as executor:
        future_to_country = {executor.submit(process_country, country): country for country in COUNTRIES}
        for future in concurrent.futures.as_completed(future_to_country):
            res = future.result()
            if res: all_reviews.extend(res)

    df = pd.DataFrame(all_reviews)
    if df.empty: return pd.DataFrame()
    return df

# MAIN LOGIC
def run_scraper_service(job_id, brands_list):
    """
    Main function to run scraping. Saves result to backend/data/{job_id}.csv
    """
    logger.info(f"🚀 Starting Scraping Job {job_id}")
    all_dfs = []

    for brand in brands_list:
        name = brand.get('name') or brand.get('company_name')
        if not name: continue
        
        android_id = brand.get('android_id', '')
        if android_id and ':' in android_id: android_id = android_id.split(':')[-1].strip()
        apple_id = brand.get('apple_id')

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            if RUN_GOOGLE_PLAY: executor.submit(scrape_google_play, name, android_id)
            if RUN_APP_STORE: executor.submit(scrape_app_store, name, apple_id)
            # Wait for results logic or collect differently? 
            # The original logic used as_completed. Let's replicate simply.
        
        # Sequential for simplicity in this port, or parallel:
        if RUN_GOOGLE_PLAY:
            df = scrape_google_play(name, android_id)
            if not df.empty: all_dfs.append(df)
        if RUN_APP_STORE:
            df = scrape_app_store(name, apple_id)
            if not df.empty: all_dfs.append(df)

    # Combine & Save
    result_metadata = {
        "status": "failed", 
        "message": "No data collected",
        "file_path": None,
        "summary": "",
        "brand_names": [],
        "sample_reviews": []
    }
    
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        final_df.drop_duplicates(subset=['text', 'source_user', 'date', 'brand'], inplace=True)
        
        filename = f"{job_id}.csv"
        file_path = os.path.join(DATA_DIR, filename)
        final_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        # Summary
        summary_lines = []
        brands = final_df['brand'].unique()
        for b in brands:
            brand_df = final_df[final_df['brand'] == b]
            play_count = len(brand_df[brand_df['platform'].str.contains('Google Play', case=False, na=False)])
            app_count = len(brand_df[brand_df['platform'].str.contains('App Store', case=False, na=False)])
            summary_lines.append(f"{b} - Playstore Reviews {play_count} - App Store {app_count}")
            
        summary_text = "\n".join(summary_lines)
        
        # Samples
        sample_reviews = []
        if not final_df.empty:
            sample_df = final_df.sample(n=min(5, len(final_df)))
            sample_reviews = sample_df.to_dict(orient='records')
            
        result_metadata.update({
            "status": "completed",
            "message": "Scraping successful",
            "file_path": file_path,
            "summary": summary_text,
            "brand_names": list(brands),
            "sample_reviews": sample_reviews
        })
        
    return result_metadata
