# YouTube Transcription Railway API

Simple CRUD API for managing YouTube transcription jobs. This server does NOT process videos - it only manages job state.

## Features

- Create transcription jobs from YouTube URLs
- Provide pending jobs to external workers
- Accept transcription results from workers
- Serve completed transcripts to users
- Health check endpoint

## API Endpoints

- `POST /api/transcribe` - Create new transcription job
- `GET /api/jobs/pending` - Get pending jobs for workers
- `PUT /api/jobs/{job_id}/processing` - Mark job as processing
- `PUT /api/jobs/{job_id}/complete` - Complete job with transcript
- `PUT /api/jobs/{job_id}/fail` - Mark job as failed
- `GET /api/jobs/{job_id}` - Get job status
- `GET /api/transcripts/{transcript_id}` - Get completed transcript
- `GET /health` - Health check

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL (via Docker or existing instance)

### Local Development

1. **Clone and navigate to the project:**
   ```bash
   cd railway-server
   ```

2. **Start PostgreSQL (if needed):**
   ```bash
   docker-compose up -d
   ```

3. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

6. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access API documentation:**
   - Open http://localhost:8000/docs

### Running Tests

```bash
pytest tests/test_api.py -v
```

### Stop PostgreSQL

```bash
docker-compose down
```

## Deployment on Railway

1. Create a new project on Railway
2. Add PostgreSQL database service
3. Deploy this repository
4. Railway will automatically:
   - Detect the Dockerfile
   - Build and deploy the app
   - Set the PORT environment variable

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `DEBUG` - Enable debug mode (default: False)
- `LOG_LEVEL` - Logging level (default: INFO)
- `PORT` - Server port (Railway sets this automatically)

## Architecture

This is a simple CRUD API that:
- Accepts YouTube URLs and creates jobs
- Provides jobs to external workers for processing
- Stores completed transcripts
- Does NOT process videos or audio files

The actual transcription is done by separate worker services.