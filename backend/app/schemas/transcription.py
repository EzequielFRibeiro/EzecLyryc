from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TranscriptionCreateRequest(BaseModel):
    """Request model for creating a transcription"""
    audio_file_key: str = Field(..., description="Storage key of the uploaded audio file")
    instrument_type: str = Field(..., description="Type of instrument (piano, guitar, bass, vocals, drums, strings, woodwinds, brass)")
    title: str = Field(..., min_length=1, max_length=200, description="Title for the transcription")
    melody_only: bool = Field(default=False, description="Extract only the melody line")
    polyphonic: bool = Field(default=False, description="Enable polyphonic transcription")


class TranscriptionResponse(BaseModel):
    """Response model for transcription details"""
    id: int
    user_id: int
    title: str
    instrument_type: str
    audio_url: str
    notation_data: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TranscriptionCreateResponse(BaseModel):
    """Response model for transcription creation"""
    transcription_id: int
    job_id: str
    status: str
    message: str


class TranscriptionListResponse(BaseModel):
    """Response model for listing transcriptions"""
    transcriptions: list[TranscriptionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TranscriptionDeleteRequest(BaseModel):
    """Request model for deleting a transcription"""
    confirmation_token: str = Field(..., description="Confirmation token (transcription ID as string)")
