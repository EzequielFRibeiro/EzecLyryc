from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


class UploadResponse(BaseModel):
    """Response model for file upload"""
    file_key: str = Field(..., description="Unique key for the uploaded file in storage")
    file_size: int = Field(..., description="Size of the uploaded file in bytes")
    file_format: str = Field(..., description="Format of the uploaded file")
    duration: Optional[float] = Field(None, description="Duration of audio in seconds")
    message: str = Field(..., description="Success message")


class UploadError(BaseModel):
    """Error response for file upload"""
    detail: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")


class YouTubeUploadRequest(BaseModel):
    """Request model for YouTube URL upload"""
    url: str = Field(..., description="YouTube video URL")
