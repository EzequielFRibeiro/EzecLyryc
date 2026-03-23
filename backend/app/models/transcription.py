from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TranscriptionStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class InstrumentType(str, enum.Enum):
    PIANO = "piano"
    GUITAR = "guitar"
    BASS = "bass"
    VOCALS = "vocals"
    DRUMS = "drums"
    STRINGS = "strings"
    WOODWINDS = "woodwinds"
    BRASS = "brass"

class Transcription(Base):
    __tablename__ = "transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    instrument_type = Column(Enum(InstrumentType), nullable=False)
    audio_url = Column(String, nullable=False)
    notation_data = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)
    status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.QUEUED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="transcriptions")
