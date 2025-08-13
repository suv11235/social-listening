# Social Listening (Starter)

A minimal social listening starter that ingests RSS feeds, stores mentions, and surfaces them in a simple web UI. Designed to be extended with additional sources (e.g., X/Twitter, Reddit) and analytics (sentiment, topic clustering, summarization).

## Tech
- Backend: FastAPI, SQLite (SQLAlchemy)
- Frontend: React + Vite + TypeScript

## Quick Start

### 1) Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev -- --port 5173
```

Open http://localhost:5173

## Features
- Add an RSS feed URL to ingest new posts as mentions
- Browse mentions with search and source filters
- Simple heuristic sentiment score placeholder (replaceable)

## API
- POST `/ingest/rss` { url: string }
- GET `/mentions?query=&source=&limit=&offset=`

## Next Steps
- Add real sentiment model, LLM-powered summaries, and topic clustering
- Add X/Twitter, Reddit, and News API connectors
- User auth and saved dashboards

## Config
- Environment variables: copy `.env.example` to `.env` in `backend/` if needed

## Notes
This is a scaffold you can evolve. The ingestion and analysis layers are intentionally simple and isolated behind services to ease future expansion.
