from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.transcription import Transcription, TranscriptionStatus, InstrumentType
from app.schemas.transcription import (
    TranscriptionCreateRequest,
    TranscriptionCreateResponse,
    TranscriptionResponse,
    TranscriptionListResponse,
    TranscriptionDeleteRequest
)
from app.middleware.auth import get_current_active_user
from app.tasks.transcription import process_transcription, process_transcription_priority
from app.services.storage import storage_service
from app.services.export_service import export_service, ExportFormat
from app.config import settings
from datetime import datetime, timedelta
from typing import Optional
import json
import logging
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transcriptions", tags=["transcriptions"])


def check_daily_transcription_limit(user: User, db: Session) -> None:
    """
    Check if user has exceeded daily transcription limit.
    
    Free users: 3 transcriptions per day
    Pro users: unlimited
    
    Raises:
        HTTPException: 429 if limit exceeded
    """
    if user.subscription_tier == "pro":
        return  # Pro users have unlimited transcriptions
    
    # Count transcriptions created today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(func.count(Transcription.id)).filter(
        Transcription.user_id == user.id,
        Transcription.created_at >= today_start
    ).scalar()
    
    if today_count >= settings.FREE_TIER_MAX_TRANSCRIPTIONS_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily transcription limit reached ({settings.FREE_TIER_MAX_TRANSCRIPTIONS_PER_DAY} per day for free users). Upgrade to Pro for unlimited transcriptions."
        )


def get_duration_limit(user: User) -> float:
    """
    Get the maximum duration limit for a user based on their subscription tier.
    
    Returns:
        Maximum duration in seconds
    """
    if user.subscription_tier == "pro":
        return settings.PRO_TIER_MAX_DURATION_SECONDS
    else:
        return settings.FREE_TIER_MAX_DURATION_SECONDS


@router.post("", response_model=TranscriptionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_transcription(
    request: TranscriptionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new transcription job.
    
    Validates user subscription tier and daily limits:
    - Free tier: 30 seconds max, 3 per day
    - Pro tier: 15 minutes max, unlimited
    
    Queues the transcription job for async processing and returns job ID.
    
    Raises:
        HTTPException 400: Invalid instrument type or audio file
        HTTPException 429: Daily limit exceeded
    """
    # Check daily transcription limit
    check_daily_transcription_limit(current_user, db)
    
    # Validate instrument type
    try:
        instrument_type = InstrumentType(request.instrument_type.lower())
    except ValueError:
        valid_types = [t.value for t in InstrumentType]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid instrument type. Valid types: {', '.join(valid_types)}"
        )
    
    # Verify audio file exists in storage
    try:
        storage_service.get_file(request.audio_file_key)
    except Exception as e:
        logger.error(f"Audio file not found in storage: {request.audio_file_key}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file not found. Please upload the file first."
        )
    
    # Get duration limit based on subscription tier
    duration_limit = get_duration_limit(current_user)
    
    # Create transcription record
    transcription = Transcription(
        user_id=current_user.id,
        title=request.title,
        instrument_type=instrument_type,
        audio_url=request.audio_file_key,
        status=TranscriptionStatus.QUEUED
    )
    
    db.add(transcription)
    db.commit()
    db.refresh(transcription)
    
    # Prepare transcription options
    options = {
        "melody_only": request.melody_only,
        "polyphonic": request.polyphonic
    }
    
    # Queue transcription job
    try:
        if current_user.subscription_tier == "pro":
            # Pro users get priority processing
            task = process_transcription_priority.apply_async(
                args=[
                    transcription.id,
                    request.audio_file_key,
                    instrument_type.value,
                    current_user.id,
                    duration_limit,
                    options
                ]
            )
        else:
            # Free users use standard queue
            task = process_transcription.apply_async(
                args=[
                    transcription.id,
                    request.audio_file_key,
                    instrument_type.value,
                    current_user.id,
                    duration_limit,
                    options
                ]
            )
        
        job_id = task.id
        
        logger.info(f"Transcription job queued: {transcription.id}, job_id: {job_id}, user: {current_user.email}")
        
        return TranscriptionCreateResponse(
            transcription_id=transcription.id,
            job_id=job_id,
            status="queued",
            message=f"Transcription queued successfully. Maximum duration: {duration_limit}s"
        )
        
    except Exception as e:
        logger.error(f"Failed to queue transcription job: {e}")
        # Clean up transcription record
        db.delete(transcription)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue transcription job. Please try again."
        )


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get transcription details by ID.
    
    Returns transcription status, notation data, detected key, and instrument type.
    Access is restricted to the transcription owner.
    
    Raises:
        HTTPException 404: Transcription not found
        HTTPException 403: Access denied (not owner)
    """
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
    
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    # Check ownership
    if transcription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own transcriptions."
        )
    
    # Parse notation data if it exists
    response_data = {
        "id": transcription.id,
        "user_id": transcription.user_id,
        "title": transcription.title,
        "instrument_type": transcription.instrument_type.value,
        "audio_url": transcription.audio_url,
        "notation_data": json.loads(transcription.notation_data) if transcription.notation_data else None,
        "duration": transcription.duration,
        "status": transcription.status.value,
        "created_at": transcription.created_at,
        "updated_at": transcription.updated_at
    }
    
    return response_data


@router.get("", response_model=TranscriptionListResponse)
async def list_transcriptions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    instrument_type: Optional[str] = Query(None, description="Filter by instrument type"),
    search: Optional[str] = Query(None, description="Search by title"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List user's transcriptions with pagination.
    
    Supports filtering by instrument type and searching by title.
    Returns paginated list of transcriptions ordered by creation date (newest first).
    
    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - instrument_type: Filter by instrument (optional)
    - search: Search in title (optional)
    """
    # Build query
    query = db.query(Transcription).filter(Transcription.user_id == current_user.id)
    
    # Apply instrument type filter
    if instrument_type:
        try:
            instrument_enum = InstrumentType(instrument_type.lower())
            query = query.filter(Transcription.instrument_type == instrument_enum)
        except ValueError:
            valid_types = [t.value for t in InstrumentType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid instrument type. Valid types: {', '.join(valid_types)}"
            )
    
    # Apply search filter
    if search:
        query = query.filter(Transcription.title.ilike(f"%{search}%"))
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size
    
    # Get paginated results
    transcriptions = query.order_by(Transcription.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to response format
    transcription_responses = []
    for t in transcriptions:
        transcription_responses.append({
            "id": t.id,
            "user_id": t.user_id,
            "title": t.title,
            "instrument_type": t.instrument_type.value,
            "audio_url": t.audio_url,
            "notation_data": json.loads(t.notation_data) if t.notation_data else None,
            "duration": t.duration,
            "status": t.status.value,
            "created_at": t.created_at,
            "updated_at": t.updated_at
        })
    
    return TranscriptionListResponse(
        transcriptions=transcription_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.delete("/{transcription_id}", status_code=status.HTTP_200_OK)
async def delete_transcription(
    transcription_id: int,
    request: TranscriptionDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a transcription and associated files.
    
    Requires confirmation token (transcription ID as string) to prevent accidental deletion.
    Deletes both the database record and the audio file from storage.
    
    Raises:
        HTTPException 404: Transcription not found
        HTTPException 403: Access denied (not owner)
        HTTPException 400: Invalid confirmation token
    """
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
    
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    # Check ownership
    if transcription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only delete your own transcriptions."
        )
    
    # Verify confirmation token
    if request.confirmation_token != str(transcription_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation token. Please provide the transcription ID as confirmation."
        )
    
    # Delete audio file from storage
    try:
        storage_service.delete_file(transcription.audio_url)
        logger.info(f"Deleted audio file from storage: {transcription.audio_url}")
    except Exception as e:
        logger.warning(f"Failed to delete audio file from storage: {e}")
        # Continue with database deletion even if storage deletion fails
    
    # Delete transcription from database
    db.delete(transcription)
    db.commit()
    
    logger.info(f"Transcription deleted: {transcription_id}, user: {current_user.email}")
    
    return {
        "message": "Transcription deleted successfully",
        "transcription_id": transcription_id
    }


@router.post("/{transcription_id}/export", status_code=status.HTTP_200_OK)
async def export_transcription(
    transcription_id: int,
    format: str = Query(..., description="Export format: pdf, musicxml, midi, gpx, gp5"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export transcription to specified format.
    
    Generates export file and stores in S3 with 24-hour expiration.
    
    Supported formats:
    - PDF: Available for all users
    - MusicXML: Pro users only
    - MIDI: Pro users only
    - GPX (Guitar Pro 7): Pro users only
    - GP5 (Guitar Pro 5): Pro users only
    
    Returns download URL valid for 24 hours.
    
    Raises:
        HTTPException 404: Transcription not found
        HTTPException 403: Access denied (not owner)
        HTTPException 400: Invalid format or tier restriction
        HTTPException 422: Transcription not completed
    """
    # Get transcription
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
    
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    # Check ownership
    if transcription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only export your own transcriptions."
        )
    
    # Check transcription status
    if transcription.status != TranscriptionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot export transcription with status '{transcription.status.value}'. Only completed transcriptions can be exported."
        )
    
    # Validate format and subscription tier
    format_lower = format.lower()
    is_valid, error_message = export_service.validate_format(format_lower, current_user.subscription_tier)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Parse notation data
    try:
        notation_data = json.loads(transcription.notation_data) if transcription.notation_data else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid notation data format"
        )
    
    # Generate export file
    try:
        export_data = export_service.export(format_lower, notation_data, transcription.title)
    except Exception as e:
        logger.error(f"Export generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate export: {str(e)}"
        )
    
    # Upload to storage
    try:
        file_extension = export_service.get_file_extension(format_lower)
        content_type = export_service.get_content_type(format_lower)
        
        export_key = storage_service.upload_file(
            file_data=io.BytesIO(export_data),
            file_extension=file_extension,
            content_type=content_type,
            user_id=current_user.id
        )
        
        # Generate presigned URL with 24-hour expiration
        download_url = storage_service.get_file_url(export_key, expiration=86400)  # 24 hours
        
        logger.info(f"Export generated: transcription_id={transcription_id}, format={format_lower}, user={current_user.email}")
        
        return {
            "message": "Export generated successfully",
            "transcription_id": transcription_id,
            "format": format_lower,
            "download_url": download_url,
            "expires_in_hours": 24,
            "file_size_bytes": len(export_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to upload export file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store export file. Please try again."
        )
