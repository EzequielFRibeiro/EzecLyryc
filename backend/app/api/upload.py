from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.schemas.upload import UploadResponse, UploadError, YouTubeUploadRequest
from app.services.storage import storage_service
from app.services.audio_processor import audio_processor
from app.middleware.auth import get_optional_user
from app.models.user import User
from app.config import settings
import tempfile
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])

# File format mappings
AUDIO_FORMATS = {fmt.lower() for fmt in settings.allowed_audio_formats_list}
VIDEO_FORMATS = {fmt.lower() for fmt in settings.allowed_video_formats_list}
ALL_FORMATS = AUDIO_FORMATS | VIDEO_FORMATS

# MIME type mappings
MIME_TYPE_MAP = {
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'flac': 'audio/flac',
    'ogg': 'audio/ogg',
    'm4a': 'audio/mp4',
    'aac': 'audio/aac',
    'mp4': 'video/mp4',
    'avi': 'video/x-msvideo',
    'mov': 'video/quicktime',
    'webm': 'video/webm'
}


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def validate_file_format(file_extension: str) -> None:
    """
    Validate that file format is supported.
    
    Raises:
        HTTPException: If format is not supported
    """
    if file_extension not in ALL_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Supported formats: {', '.join(sorted(ALL_FORMATS))}"
        )


def validate_file_size(file_size: int) -> None:
    """
    Validate that file size is within limits.
    
    Raises:
        HTTPException: If file is too large
    """
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )


@router.post("/upload/recording", response_model=UploadResponse)
async def upload_recording(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Upload browser-recorded audio for transcription.
    
    Accepts WebM audio format from browser MediaRecorder API.
    Automatically converts WebM to MP3 for standardization.
    
    File size limit: 100MB
    
    Returns:
        UploadResponse with file key, size, format, and duration
    
    Raises:
        HTTPException 400: Invalid file format
        HTTPException 413: File too large
        HTTPException 500: Processing error
    """
    # Extract and validate file extension
    file_extension = get_file_extension(file.filename)
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a valid extension"
        )
    
    # Accept WebM format (common browser recording format)
    if file_extension not in ['webm', 'wav', 'ogg']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported recording format. Supported formats: webm, wav, ogg"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    validate_file_size(file_size)
    
    # Create temporary file for processing
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}")
    try:
        temp_file.write(file_content)
        temp_file.close()
        
        # Convert WebM to MP3 for standardization
        audio_file_path = temp_file.name
        final_extension = file_extension
        
        if file_extension == 'webm':
            logger.info(f"Converting WebM recording to MP3: {file.filename}")
            try:
                # Convert WebM to MP3
                audio_file_path = audio_processor.convert_audio_format(
                    temp_file.name,
                    output_format="mp3"
                )
                final_extension = "mp3"
            except Exception as e:
                logger.error(f"Failed to convert WebM recording: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to convert recording to standard format"
                )
        
        # Get audio duration
        duration = audio_processor.get_audio_duration(audio_file_path)
        
        # Upload to S3 storage
        try:
            with open(audio_file_path, 'rb') as audio_file:
                content_type = MIME_TYPE_MAP.get(final_extension, 'application/octet-stream')
                user_id = current_user.id if current_user else None
                
                file_key = storage_service.upload_file(
                    file_data=audio_file,
                    file_extension=final_extension,
                    content_type=content_type,
                    user_id=user_id
                )
        except Exception as e:
            logger.error(f"Failed to upload recording to storage: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store uploaded recording"
            )
        
        # Clean up temporary files
        if file_extension == 'webm' and audio_file_path != temp_file.name:
            try:
                os.unlink(audio_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary audio file: {e}")
        
        return UploadResponse(
            file_key=file_key,
            file_size=file_size,
            file_format=final_extension,
            duration=duration,
            message="Recording uploaded successfully"
        )
        
    finally:
        # Clean up original temporary file
        try:
            os.unlink(temp_file.name)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Upload audio or video file for transcription.
    
    Accepts audio formats (MP3, WAV, FLAC, OGG, M4A, AAC) and video formats (MP4, AVI, MOV, WEBM).
    For video files, audio is automatically extracted using FFmpeg.
    
    File size limit: 100MB
    
    Returns:
        UploadResponse with file key, size, format, and duration
    
    Raises:
        HTTPException 400: Invalid file format
        HTTPException 413: File too large
        HTTPException 500: Processing error
    """
    # Extract and validate file extension
    file_extension = get_file_extension(file.filename)
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a valid extension"
        )
    
    validate_file_format(file_extension)
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    validate_file_size(file_size)
    
    # Create temporary file for processing
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}")
    try:
        temp_file.write(file_content)
        temp_file.close()
        
        # Determine if this is a video file that needs audio extraction
        is_video = file_extension in VIDEO_FORMATS
        audio_file_path = temp_file.name
        final_extension = file_extension
        
        if is_video:
            logger.info(f"Extracting audio from video file: {file.filename}")
            try:
                # Extract audio from video
                audio_file_path = audio_processor.extract_audio_from_video(
                    temp_file.name,
                    output_format="mp3"
                )
                final_extension = "mp3"
            except Exception as e:
                logger.error(f"Failed to extract audio from video: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to extract audio from video file"
                )
        
        # Get audio duration
        duration = audio_processor.get_audio_duration(audio_file_path)
        
        # Upload to S3 storage
        try:
            with open(audio_file_path, 'rb') as audio_file:
                content_type = MIME_TYPE_MAP.get(final_extension, 'application/octet-stream')
                user_id = current_user.id if current_user else None
                
                file_key = storage_service.upload_file(
                    file_data=audio_file,
                    file_extension=final_extension,
                    content_type=content_type,
                    user_id=user_id
                )
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store uploaded file"
            )
        
        # Clean up temporary files
        if is_video and audio_file_path != temp_file.name:
            try:
                os.unlink(audio_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary audio file: {e}")
        
        return UploadResponse(
            file_key=file_key,
            file_size=file_size,
            file_format=final_extension,
            duration=duration,
            message="File uploaded successfully"
        )
        
    finally:
        # Clean up original temporary file
        try:
            os.unlink(temp_file.name)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")


@router.post("/upload/youtube", response_model=UploadResponse)
async def upload_youtube(
    request: YouTubeUploadRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Extract audio from YouTube video for transcription.
    
    Accepts a YouTube URL and extracts the audio track using yt-dlp.
    Audio is automatically converted to MP3 format.
    
    Duration limit: 15 minutes (900 seconds)
    If video is longer, only the first 15 minutes are extracted.
    
    Returns:
        UploadResponse with file key, size, format, and duration
    
    Raises:
        HTTPException 400: Invalid YouTube URL or video restrictions
        HTTPException 500: Extraction error
    """
    youtube_url = request.url.strip()
    
    # Basic URL validation
    if not youtube_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube URL is required"
        )
    
    # Check if URL looks like a YouTube URL
    if not any(domain in youtube_url.lower() for domain in ['youtube.com', 'youtu.be']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL. Please provide a valid YouTube video URL."
        )
    
    audio_file_path = None
    try:
        # Extract audio from YouTube
        logger.info(f"Extracting audio from YouTube URL: {youtube_url}")
        audio_file_path, duration = audio_processor.extract_audio_from_youtube(
            youtube_url,
            max_duration_seconds=settings.YOUTUBE_MAX_DURATION_SECONDS
        )
        
        # Get file size
        file_size = os.path.getsize(audio_file_path)
        
        # Validate file size (should not exceed max upload size)
        max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Extracted audio exceeds maximum size limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )
        
        # Upload to S3 storage
        try:
            with open(audio_file_path, 'rb') as audio_file:
                user_id = current_user.id if current_user else None
                
                file_key = storage_service.upload_file(
                    file_data=audio_file,
                    file_extension="mp3",
                    content_type="audio/mpeg",
                    user_id=user_id
                )
        except Exception as e:
            logger.error(f"Failed to upload YouTube audio to storage: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store extracted audio"
            )
        
        return UploadResponse(
            file_key=file_key,
            file_size=file_size,
            file_format="mp3",
            duration=duration,
            message="YouTube audio extracted successfully"
        )
        
    except ValueError as e:
        # User-facing errors (invalid URL, restrictions, etc.)
        logger.warning(f"YouTube extraction failed with user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error during YouTube extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract audio from YouTube. Please try again or use direct file upload."
        )
    finally:
        # Clean up temporary file
        if audio_file_path and os.path.exists(audio_file_path):
            try:
                os.unlink(audio_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary YouTube audio file: {e}")
