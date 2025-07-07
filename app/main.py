import logging
from datetime import datetime, timezone
UTC = timezone.utc
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import List

from .config import DEBUG, LOG_LEVEL
from .database import get_db, init_db, check_db_connection
from .schemas import (
    TranscribeRequest, JobResponse, JobPending, CompleteJobRequest, 
    FailJobRequest, TranscriptResponse, HealthResponse
)
from .models import Job, Transcript, JobStatus

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    yield

# Create FastAPI app
app = FastAPI(
    title="YouTube Transcription Railway API",
    description="Simple CRUD API for managing YouTube transcription jobs",
    version="1.0.0",
    debug=DEBUG,
    lifespan=lifespan
)

@app.post("/api/transcribe", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_transcription_job(request: TranscribeRequest, db: Session = Depends(get_db)):
    """Create a new transcription job"""
    try:
        # Create new job
        job = Job(youtube_url=request.url)
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created new job: {job.id}")
        
        return JobResponse(
            job_id=job.id,
            status=job.status.value,
            created_at=job.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.get("/api/jobs/pending", response_model=List[JobPending])
async def get_pending_jobs(db: Session = Depends(get_db)):
    """Get pending jobs for worker (returns one at a time, FIFO order)"""
    # Get oldest pending job
    job = db.query(Job).filter(
        Job.status == JobStatus.PENDING
    ).order_by(Job.created_at).first()
    
    if not job:
        return []
    
    return [JobPending(
        job_id=job.id,
        youtube_url=job.youtube_url,
        created_at=job.created_at
    )]

@app.put("/api/jobs/{job_id}/processing")
async def mark_job_processing(job_id: UUID, db: Session = Depends(get_db)):
    """Mark job as processing"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot mark job as processing. Current status: {job.status.value}"
        )
    
    job.status = JobStatus.PROCESSING
    job.updated_at = datetime.now(UTC)
    db.commit()
    
    logger.info(f"Job {job_id} marked as processing")
    
    return {"status": job.status.value}

@app.put("/api/jobs/{job_id}/complete")
async def complete_job(
    job_id: UUID, 
    request: CompleteJobRequest, 
    db: Session = Depends(get_db)
):
    """Complete job with transcription result"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot complete job. Current status: {job.status.value}"
        )
    
    try:
        # Create transcript
        transcript = Transcript(
            job_id=job.id,
            title=request.title,
            duration=request.duration,
            content=request.content,
            timestamps=request.timestamps
        )
        
        # Update job status
        job.status = JobStatus.COMPLETED
        job.updated_at = datetime.now(UTC)
        
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        logger.info(f"Job {job_id} completed with transcript {transcript.id}")
        
        return {
            "status": job.status.value,
            "transcript_id": transcript.id
        }
        
    except Exception as e:
        logger.error(f"Failed to complete job {job_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete job: {str(e)}")

@app.put("/api/jobs/{job_id}/fail")
async def fail_job(
    job_id: UUID, 
    request: FailJobRequest, 
    db: Session = Depends(get_db)
):
    """Mark job as failed with error message"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot fail job. Current status: {job.status.value}"
        )
    
    job.status = JobStatus.FAILED
    job.error_message = request.error
    job.updated_at = datetime.now(UTC)
    db.commit()
    
    logger.info(f"Job {job_id} marked as failed: {request.error}")
    
    return {"status": job.status.value}

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: UUID, db: Session = Depends(get_db)):
    """Get job status"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get transcript ID if job is completed
    transcript_id = None
    if job.status == JobStatus.COMPLETED and job.transcript:
        transcript_id = job.transcript.id
    
    return JobResponse(
        job_id=job.id,
        status=job.status.value,
        created_at=job.created_at,
        updated_at=job.updated_at,
        transcript_id=transcript_id,
        error_message=job.error_message
    )

@app.get("/api/transcripts/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(transcript_id: UUID, db: Session = Depends(get_db)):
    """Get transcript by ID"""
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return TranscriptResponse(
        transcript_id=transcript.id,
        job_id=transcript.job_id,
        title=transcript.title,
        duration=transcript.duration,
        content=transcript.content,
        timestamps=transcript.timestamps,
        created_at=transcript.created_at
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if check_db_connection() else "disconnected"
    
    return HealthResponse(
        status="healthy",
        database=db_status,
        timestamp=datetime.now(UTC)
    )