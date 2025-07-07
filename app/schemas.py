from pydantic import BaseModel, Field
from typing import List, Dict, Union, Optional
from datetime import datetime
from uuid import UUID

class TranscribeRequest(BaseModel):
    url: str = Field(..., pattern=r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/')

class JobResponse(BaseModel):
    job_id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    transcript_id: Optional[UUID] = None
    error_message: Optional[str] = None

class JobPending(BaseModel):
    job_id: UUID
    youtube_url: str
    created_at: datetime

class CompleteJobRequest(BaseModel):
    title: str
    duration: float
    content: str
    timestamps: List[Dict[str, Union[float, str]]]

class FailJobRequest(BaseModel):
    error: str

class TranscriptResponse(BaseModel):
    transcript_id: UUID
    job_id: UUID
    title: str
    duration: float
    content: str
    timestamps: List[Dict[str, Union[float, str]]]
    created_at: datetime

class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime