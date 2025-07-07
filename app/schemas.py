from datetime import datetime
from typing import List, Dict, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
import re


class TranscribeRequest(BaseModel):
    url: str = Field(..., description="YouTube URL to transcribe")
    
    @field_validator('url')
    @classmethod
    def validate_youtube_url(cls, v):
        pattern = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        if not re.match(pattern, v):
            raise ValueError('Invalid YouTube URL')
        return v


class TranscriptResponse(BaseModel):
    transcript_id: UUID
    title: str
    duration: float
    content: str
    timestamps: List[Dict[str, Union[float, str]]]
    created_at: datetime
    
    model_config = {"from_attributes": True}