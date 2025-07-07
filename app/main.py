import logging
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from .config import DEBUG, LOG_LEVEL
from .database import get_db, init_db, check_db_connection
from .schemas import TranscribeRequest, TranscriptResponse
from .models import Transcript
from .transcription import process_video_transcription

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="YouTube Transcription API",
    description="Simple API for transcribing YouTube videos",
    version="1.0.0",
    debug=DEBUG
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@app.post("/api/transcribe", response_model=TranscriptResponse)
async def transcribe_video(request: TranscribeRequest, db: Session = Depends(get_db)):
    """
    Accept YouTube URL and return ready transcript (synchronous, 2-5 minutes wait)
    """
    try:
        logger.info(f"Starting transcription for URL: {request.url}")
        
        # Process video transcription (synchronous)
        result = process_video_transcription(request.url, db)
        
        logger.info(f"Transcription completed: {result['transcript_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.get("/api/transcripts/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(transcript_id: UUID, db: Session = Depends(get_db)):
    """
    Return saved transcript by ID
    """
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return TranscriptResponse(
        transcript_id=transcript.id,
        title=transcript.title,
        duration=transcript.duration,
        content=transcript.content,
        timestamps=transcript.timestamps,
        created_at=transcript.created_at
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    db_status = "connected" if check_db_connection() else "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status
    }