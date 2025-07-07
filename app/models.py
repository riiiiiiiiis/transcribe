import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, JSON, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    youtube_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    duration = Column(Float, nullable=False)  # seconds
    content = Column(Text, nullable=False)
    timestamps = Column(JSON, nullable=False)  # List[{"start": float, "end": float, "text": str}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())