import enum
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed" 
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    youtube_url = Column(String, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    transcript = relationship("Transcript", back_populates="job", uselist=False)

class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    title = Column(String, nullable=False)
    duration = Column(Float, nullable=False)  # seconds
    content = Column(Text, nullable=False)
    timestamps = Column(JSON, nullable=False)  # List[{"start": float, "end": float, "text": str}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    job = relationship("Job", back_populates="transcript")