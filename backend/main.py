from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
import asyncio
import uuid

# Services
from services.website import analyze_url
from services.app_store import resolve_app_ids
from services.reviews import run_scraper_service
from services.analysis import generate_dimensions, analyze_reviews

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="VoC Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Job Store (for simplicity, use Redis/DB in prod)
JOBS = {}

# --- Pydantic Models ---
class WebsiteRequest(BaseModel):
    website: str

class Company(BaseModel):
    company_name: Optional[str] = None
    # name field removed to avoid duplication. Frontend/Backend should use company_name.
    # Logic in scripts handles fallback if valid keys provided.
    website: Optional[str] = None
    description: Optional[str] = None
    android_id: Optional[str] = None
    apple_id: Optional[str] = None
    is_main: Optional[bool] = False

class ScrapRequest(BaseModel):
    brands: List[Company]
    job_id: Optional[str] = None

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "VoC Backend is running"}

@app.post("/api/analyze-website")
async def api_analyze_website(request: WebsiteRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API Key not configured")
    
    result = analyze_url(request.website, OPENAI_API_KEY)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/appids")
async def api_appids(companies: List[Company]):
    # Convert Pydantic models to dicts, excluding nulls to avoid UI clutter
    valid_companies = [c.dict(exclude_none=True) for c in companies]
    result = resolve_app_ids(valid_companies, OPENAI_API_KEY)
    return result

@app.post("/api/scrap-reviews")
async def api_scrap_reviews(request: ScrapRequest, background_tasks: BackgroundTasks):
    job_id = request.job_id or str(uuid.uuid4())
    
    # Initialize Job Status
    JOBS[job_id] = {
        "status": "pending",
        "message": "Job started",
        "created_at": str(asyncio.get_event_loop().time())
    }
    
    # Validation
    brands_list = [b.dict() for b in request.brands]
    
    # Add to background task
    background_tasks.add_task(process_scraping_job, job_id, brands_list)
    
    return {"message": "Scraping started", "job_id": job_id}

@app.get("/api/check-status")
async def check_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# --- Background Worker ---
def process_scraping_job(job_id, brands_list):
    try:
        JOBS[job_id]["status"] = "running"
        result = run_scraper_service(job_id, brands_list)
        
        # Update Job Store with results
        JOBS[job_id].update(result) # result has status: completed/failed
        
    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["message"] = str(e)

@app.post("/api/scrapped-data")
async def api_scrapped_data2(request: dict):
    # n8n workflow "VoC Data Collection" -> trigger 1 of "VoC Analysis"
    # Expected payload via main flow: just needs s3_key or dimensions generation
    
    # Minimal implementation based on plan:
    # "Generates Analysis Dimensions using OpenAI"
    
    s3_key = request.get("s3_key")
    # For local dev, we might just look up job ID or file path
    # If s3_key is actually a job_id (from our file naming convention), let's use that.
    
    job_id = s3_key.replace("scrapped_data/", "").replace(".csv", "") if s3_key else None
    
    if not job_id and "job_id" in request:
        job_id = request["job_id"]
        
    # Read the data locally
    if job_id:
        file_path = f"backend/data/{job_id}.csv" 
    else:
        # Fallback/Mock
        return {"error": "Missing job_id or s3_key"}
        
    try:
        # Read sample
        df = pd.read_csv(file_path)
        sample = df.sample(n=min(10, len(df))).to_dict(orient='records')
        
        dimensions = generate_dimensions(sample, OPENAI_API_KEY)
        
        return {
            "message": "Dimensions generated",
            "body": { # replicating n8n structure slightly for frontend compatibility
                "dimensions": dimensions,
                "s3_bucket": "local", 
                "s3_key": file_path 
            }
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

@app.post("/api/final-analysis")
async def api_final_analysis(request: dict):
    # Expected: { dimensions: [...], file_key: ... }
    dimensions = request.get("dimensions", [])
    file_path = request.get("file_key")
    
    if not file_path: 
        return {"error": "Missing file_key"}
        
    # Run Analysis
    # In real world, this should also be a background task as it takes time!
    # For now, running sync to keep it simple as per plan Phase 1/2
    
    result = analyze_reviews(file_path, dimensions, OPENAI_API_KEY)
    
    # We could send an email here using a library if requested, 
    # but for now just return success to UI.
    
    return {
        "status": "success",
        "message": "Analysis complete",
        "result": result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

