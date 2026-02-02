import pandas as pd
from openai import OpenAI
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_dimensions(reviews_sample, openai_key):
    """
    Analyzes a sample of reviews to suggest relevant analysis axes.
    """
    client = OpenAI(api_key=openai_key)
    
    # Format reviews for prompt
    reviews_text = "\n".join([f"- {r.get('text', '')}" for r in reviews_sample[:10]])
    
    prompt = f"""
    Analyze the following customer reviews and suggest 5 key "Dimensions" or "Topics" that would be valuable to track for this brand (e.g., "Delivery Speed", "Packaging", "Customer Service").
    
    Reviews Sample:
    {reviews_text}
    
    Return a JSON array of objects, where each object has:
    - dimension: The name of the dimension
    - description: What this dimension covers
    - keywords: A list of 3-5 related keywords
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert market researcher. Return ONLY JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        content = completion.choices[0].message.content
        data = json.loads(content)
        
        # Handle if wrapped in a key like "dimensions" or just array
        if "dimensions" in data:
            return data["dimensions"]
        elif isinstance(data, list):
            return data
        else:
            # Try to find array in values
            for v in data.values():
                if isinstance(v, list): return v
            return []
            
    except Exception as e:
        logger.error(f"Error generating dimensions: {e}")
        return []

def analyze_reviews(file_path, dimensions, openai_key):
    """
    Reads CSV, batches reviews, and sends to OpenAI for sentiment/topic analysis.
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return {"error": f"Could not read file: {e}"}
        
    client = OpenAI(api_key=openai_key)
    
    # Limit for prototype: Analyze top 50 reviews to save tokens/time
    # In production, use background worker + batching
    df_sample = df.head(50).copy()
    
    analyzed_results = []
    
    # Prepare dimensions string
    dims_str = "\n".join([f"- {d['dimension']}: {d['description']}" for d in dimensions])
    
    # Batch processing
    batch_size = 10
    total_batches = (len(df_sample) // batch_size) + 1
    
    for i in range(0, len(df_sample), batch_size):
        batch = df_sample.iloc[i:i+batch_size]
        batch_texts = []
        for idx, row in batch.iterrows():
            batch_texts.append(f"ID {idx}: {row['text']}")
            
        reviews_str = "\n".join(batch_texts)
        prompt = f"""
        Analyze the following reviews based on these dimensions:
        {dims_str}
        
        Reviews:
        {reviews_str}
        
        For EACH review, return a JSON object keyed by ID with:
        - sentiment_score: -1 to 1
        - sentiment_label: Positive, Neutral, Negative
        - topics: List of dimensions from the provided list that are mentioned.
        """
        
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert sentiment analyst. Return ONLY JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            content = completion.choices[0].message.content
            # Expected: { "ID 0": { ... }, "ID 1": { ... } }
            batch_result = json.loads(content)
            analyzed_results.append(batch_result)
            
        except Exception as e:
            logger.error(f"Error analyzing batch {i}: {e}")
            
    # Merge results back (simplified visualization for now)
    # Ideally we update the DF and save a new CSV
    
    return {
        "total_reviews": len(df),
        "analyzed_count": len(df_sample),
        "results": analyzed_results
    }
