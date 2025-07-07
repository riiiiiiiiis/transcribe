# YouTube Transcription API

Simple MVP backend for YouTube video transcription using FastAPI, PostgreSQL, and OpenAI Whisper.

## Features

- Synchronous YouTube video transcription (2-5 minutes processing time)
- RESTful API with FastAPI
- PostgreSQL database for storing transcripts
- OpenAI Whisper integration for high-quality transcription
- Automatic timestamp generation

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key
- ffmpeg (for audio processing)

## Local Development Setup

### 1. Start PostgreSQL in Docker
```bash
# Start PostgreSQL container
docker-compose up -d

# Check that PostgreSQL is running
docker-compose ps
```

### 2. Setup Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy yt-dlp openai pytest python-dotenv psycopg2-binary
```

### 3. Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Edit .env with your OpenAI API key
# DATABASE_URL is already configured for Docker PostgreSQL
```

### 4. Initialize Database
```bash
# Create database tables
python -c "from app.database import init_db; init_db()"
```

### 5. Run the Application
```bash
# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test the API
```bash
# Run tests
pytest tests/ -v

# Or test manually at: http://localhost:8000/docs
```

### 7. Stop PostgreSQL
```bash
# When finished developing
docker-compose down
```

## Troubleshooting

### macOS Issues
```bash
# If psycopg2-binary installation fails on M1 Mac:
pip install psycopg2-binary --no-cache-dir

# If ffmpeg is missing:
brew install ffmpeg

# Check PostgreSQL is running:
docker-compose ps
```

### Database Issues
```bash
# Reset database:
docker-compose down -v
docker-compose up -d
python -c "from app.database import init_db; init_db()"
```

## Configuration

Update `.env` file with your settings:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/transcription_db

# OpenAI
OPENAI_API_KEY=sk-...

# App Settings
DEBUG=False
LOG_LEVEL=INFO

# Railway
PORT=8000
```

## Running the Application

### Local Development

```bash
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
docker build -t youtube-transcription .
docker run -p 8000:8000 --env-file .env youtube-transcription
```

## API Endpoints

### POST /api/transcribe

Transcribe a YouTube video (synchronous, 2-5 minutes wait).

Request:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

Response:
```json
{
  "transcript_id": "uuid-4-string",
  "title": "Video Title",
  "duration": 300,
  "content": "Full transcript text...",
  "timestamps": [
    {"start": 0.0, "end": 5.2, "text": "Hello and welcome"},
    {"start": 5.2, "end": 10.1, "text": "to this video"}
  ],
  "created_at": "2025-07-06T12:05:00Z"
}
```

### GET /api/transcripts/{transcript_id}

Get a saved transcript by ID.

### GET /health

Health check endpoint.

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

## Deployment on Railway

1. Install Railway CLI
2. Login to Railway: `railway login`
3. Create new project: `railway init`
4. Add PostgreSQL database: `railway add`
5. Deploy: `railway up`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # PostgreSQL connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── transcription.py     # Business logic
│   └── utils.py             # Helper functions
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API tests
│   └── test_transcription.py # Logic tests
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

## Performance Metrics

- Processing time for 5-minute video: < 3 minutes
- Transcription success rate: > 95%
- API response time: < 200ms (except transcribe endpoint)
- Target uptime: > 99%

## License

MIT