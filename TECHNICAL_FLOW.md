# Technical Flow Documentation

## 1. Step 1: Analyze Website

**User Action**: Enters a URL (e.g., `https://example.com`) and clicks "Analyze Website".

### Frontend
- **Component**: `frontend/components/stepper/StepWebsite.tsx` (`handleSubmit`)
- **Action**: Calls `VoCService.analyzeWebsite(url)` from `lib/api.ts`.
- **Request**: `POST /api/analyze-website` with `{ website: "..." }`.

### Backend
- **Endpoint**: `backend/main.py` -> `api_analyze_website`
- **Logic**: 
    1. Calls `services.website.analyze_url`.
    2. Uses OpenAI to extract company name, description, and competitors.
- **Response**: JSON array of `Company` objects (Main company + Competitors).

### Return to Frontend
- **UI Update**: `VocStepper.tsx` receives data via `onComplete`.
- **Transition**: Moves to Step 2.

---

## 2. Step 2: Verify Competitors

**User Action**: Reviews the list of companies, adds/removes items, adds website URLs, checks for accuracy, and clicks "Confirm Competitors".

### Frontend
- **Component**: `frontend/components/stepper/StepCompetitors.tsx` (`handleSubmit`)
- **Action**: Calls `VoCService.resolveAppIds(items)`.
- **Request**: `POST /api/appids` with List of `Company` objects.

### Backend
- **Endpoint**: `backend/main.py` -> `api_appids`
- **Logic**:
    1. Calls `services.app_store.resolve_app_ids`.
    2. For each company, searches Google Play and Apple App Store for App IDs.
- **Response**: List of `Company` objects enriched with `android_id` and `apple_id`.

### Return to Frontend
- **UI Update**: `VocStepper` updates state.
- **Transition**: Moves to Step 3.

---

## 3. Step 3: Start Scraping

**User Action**: Verifies App IDs and clicks "Start Scraping Reviews".

### Frontend
- **Component**: `frontend/components/stepper/StepAppIds.tsx` (`handleStartScraping`)
- **Action**: Calls `VoCService.startScraping`.
- **Request**: `POST /api/scrap-reviews` with `{ brands: [...], job_id: "..." }`.

### Backend
- **Endpoint**: `backend/main.py` -> `api_scrap_reviews`
- **Logic**:
    1. Creates a `job_id` (if not provided).
    2. Sets job status to `pending` in global `JOBS` dictionary.
    3. **Background Task**: Spawns `process_scraping_job` to run asynchronously.
        - Calls `services.reviews.run_scraper_service` to scrape Google Play / App Store.
        - Saves CSV to `backend/data/{job_id}.csv`.
        - Updates `JOBS[job_id]` with status `completed` and summary.
- **Response**: Immediate `{ message: "Scraping started", job_id: "..." }`.

### Return to Frontend
- **UI Update**: `VocStepper` moves to Step 4 (Polling View).

---

## 4. Step 4: Polling & Results

**User Action**: Waits while a spinner shows "Scraping in Progress".

### Frontend
- **Component**: `frontend/components/results/SuccessView.tsx` (`useEffect` polling)
- **Action**: Calls `VoCService.checkStatus(jobId)` every 10 seconds.
- **Request**: `GET /api/check-status?job_id=...`

### Backend
- **Endpoint**: `backend/main.py` -> `check_status`
- **Logic**: Returns the current state object from `JOBS` dictionary.

### Frontend Transition
- **Condition**: When status is `completed` or `s3_key` is present.
- **UI Update**: Shows "Scraping Complete", displays summary stats, and shows "Process Extracted Data" button.

---

## 5. Step 5: Generate Dimensions

**User Action**: Clicks "Process Extracted Data".

### Frontend
- **Component**: `SuccessView.tsx` (`handleProcessData`)
- **Action**: Calls `VoCService.sendToWebhook`.
- **Request**: `POST /api/scrapped-data`.

### Backend
- **Endpoint**: `backend/main.py` -> `api_scrapped_data2`
- **Logic**:
    1. Reads the local CSV file.
    2. Samples 10 reviews.
    3. Calls `services.analysis.generate_dimensions` (OpenAI) to suggest topics.
- **Response**: JSON with suggested dimensions (e.g., "Price", "Quality").

### Return to Frontend
- **UI Update**: Displays a form with the suggested dimensions for user editing.

---

## 6. Step 6: Final Analysis

**User Action**: User edits keywords/descriptions and clicks "Submit Dimensions".

### Frontend
- **Component**: `SuccessView.tsx` (`handleSubmitDimensions`)
- **Action**: Calls `VoCService.submitDimensions`.
- **Request**: `POST /api/final-analysis`.

### Backend
- **Endpoint**: `backend/main.py` -> `api_final_analysis`
- **Logic**:
    1. Calls `services.analysis.analyze_reviews`.
    2. Uses OpenAI to classify sentiment/topics for reviews based on user's dimensions.
    3. Returns success message.

### Return to Frontend
- **UI Update**: Shows Final Success Card ("VoC Magic is happening").
