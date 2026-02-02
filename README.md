# VoC Code - Voice of Customer Analysis Platform

**Turn messy customer reviews into actionable insights using AI-powered analysis.**

This project scrapes reviews from Google Play and the Apple App Store, uses OpenAI to identify key "dimensions" (topics) of feedback, and analyzes sentiment to help businesses understand what their customers are really saying.

---

## 🏗 High-Level Architecture

```mermaid
graph TD
    User((User))
    subgraph Frontend [Frontend (Next.js)]
        UI[Web Dashboard]
        Router[App Router]
    end
    
    subgraph Backend [Backend (FastAPI)]
        API[API Endpoints]
        Worker[Background Worker]
    end
    
    subgraph Data [Data Persistence]
        CSV[Local CSV Storage]
        S3[(AWS S3 Bucket)]
    end
    
    subgraph External [External Services]
        OpenAI[OpenAI GPT-4o]
        GPlay[Google Play Store]
        AppStore[Apple App Store]
    end

    User -->|Views| UI
    UI -->|Requests Analysis| API
    API -->|Offloads Task| Worker
    Worker -->|Scrapes| GPlay
    Worker -->|Scrapes| AppStore
    Worker -->|Generates Dimensions| OpenAI
    Worker -->|Analyzes Sentiment| OpenAI
    Worker -->|Saves Results| CSV
    Worker -->|Syncs| S3
    API -->|Reads Results| CSV
    API -->|Returns Data| UI
```

---

## 🛠 Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Lucide React
- **Backend**: Python, FastAPI, Uvicorn
- **AI/ML**: OpenAI GPT-4o (via API)
- **Scraping**: `google-play-scraper`, `app-store-scraper`
- **Data**: Pandas, CSV, AWS S3
- **Infrastructure**: AWS Lambda (optional parts), Docker (implied potential)

## ✅ Prerequisites

Before running the project, ensure you have the following installed:

1.  **Python 3.8+**: For the backend API and scraping logic.
2.  **Node.js 16+**: For building and running the frontend development server.
3.  **AWS CLI**: Configured with credentials if you intend to deploy or sync to S3.
    *   `aws configure`
4.  **OpenAI API Key**: You need a valid API key to generate insights.

## 🚀 Installation & Setup

### 1. Backend Setup

Open a terminal and navigate to the project root:

```bash
cd VoC_code
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Set up your environment variables:
Create a `.env` file in the `backend/` directory (or root, check `main.py` loading):

```bash
# .env
OPENAI_API_KEY=your_sk_key_here
```

Run the Backend Server:

```bash
cd backend
uvicorn main:app --reload --port 8000
```
*The backend will be available at `http://localhost:8000`*

### 2. Frontend Setup (Next.js)

Open a **new** terminal window and navigate to the frontend directory:

```bash
cd VoC_code/frontend
```

Install Node dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

*The frontend will be available at `http://localhost:3000`*

To build for production:

```bash
npm run build
npm start
```

---

## 📂 Project Structure

- **`backend/`**: Contains the FastAPI application, services for scraping and analysis, and local data storage.
    - **`services/`**: Logic for `reviews` (scraping), `analysis` (AI), and `app_store` (metadata).
    - **`data/`**: Processed CSV files containing reviews and analysis results.
- **`frontend/`**: Next.js (App Router) application.
    - **`app/`**: Application routes and pages (`page.tsx`).
    - **`components/`**: Reusable UI components (`stepper/`, `ui/`, `results/`).
    - **`lib/`**: Utility functions and API wrappers (`api.ts`).

## 🤝 Glossary

See [GLOSSARY.md](./GLOSSARY.md) for a list of common terms and acronyms used in this project.
