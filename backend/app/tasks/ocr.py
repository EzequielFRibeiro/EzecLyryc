"""
OCR (Optical Music Recognition) tasks for sheet music scanning.
"""
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from app.celery_app import celery_app
from app.tasks.task_status import TaskProgress
from app.services.ocr_scanner import OCRScanner
from app.services.storage import storage_service
from app.database import SessionLocal
from app.models.transcription import Transcription, TranscriptionStatus
import json
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.ocr.process_sheet_music_scan")
def process_sheet_music_scan(
    self: Task,
    transcription_id: int,
    image_file_key: str,
    filename: str,
    user_id: int,
    options: dict = None
) -> dict:
    """
    Process sheet music image using OCR asynchronously.
    
    Args:
        self: Celery task instance
        transcription_id: Database ID of the transcription record
        image_file_key: Storage key of the image file
        filename: Original filename
        user_id: ID of the user requesting OCR
        options: Additional OCR options
        
    Returns:
        Dictionary containing OCR results and transcription data
    """
    progress = TaskProgress(self, total_steps=100)
    db = SessionLocal()
    
    try:
        # Update database status
        transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")
        
        transcription.status = TranscriptionStatus.PROCESSING
        db.commit()
        
        # Load image from storage
        progress.update(10, "Loading sheet music image")
        logger.info(f"Loading image from storage: {image_file_key}")
        image_data = storage_service.get_file(image_file_key)
        
        # Initialize OCR scanner
        progress.update(20, "Initializing OCR scanner")
        scanner = OCRScanner()
        
        # Validate image
        progress.update(30, "Validating image quality")
        is_valid, error_msg = scanner.validate_image(image_data, filename)
        if not is_valid:
            raise ValueError(f"Image validation failed: {error_msg}")
        
        # Preprocess image
        progress.update(40, "Preprocessing image")
        img = scanner.preprocess_image(image_data)
        
        # Detect notation elements
        progress.update(60, "Detecting musical notation elements")
        elements = scanner.detect_notation_elements(img)
        
        # Generate transcription
        progress.update(80, "Generating editable transcription")
        notation_data = scanner.generate_transcription(
            elements,
            img.shape[1],
            img.shape[0]
        )
        
        # Save to database
        progress.update(90, "Saving transcription")
        transcription.notation_data = json.dumps(notation_data)
        transcription.status = TranscriptionStatus.COMPLETED
        db.commit()
        
        result = {
            "transcription_id": transcription_id,
            "notation_data": notation_data,
            "detected_elements": {
                "notes": len(elements.get("notes", [])),
                "clefs": len(elements.get("clefs", [])),
                "barlines": len(elements.get("barlines", []))
            },
            "status": "completed"
        }
        
        progress.complete(result)
        logger.info(f"OCR scan completed for transcription {transcription_id}")
        return result
        
    except SoftTimeLimitExceeded:
        error_msg = "OCR processing exceeded time limit"
        logger.error(f"OCR scan {transcription_id} timed out")
        
        if transcription:
            transcription.status = TranscriptionStatus.FAILED
            db.commit()
        
        progress.fail(error_msg, {"reason": "timeout"})
        raise
        
    except ValueError as e:
        # Image quality or validation errors
        error_msg = str(e)
        logger.warning(f"OCR scan {transcription_id} failed validation: {e}")
        
        if transcription:
            transcription.status = TranscriptionStatus.FAILED
            db.commit()
        
        progress.fail(error_msg, {"reason": "validation_error", "details": str(e)})
        raise
        
    except Exception as e:
        error_msg = f"OCR processing failed: {str(e)}"
        logger.error(f"OCR scan {transcription_id} failed: {e}", exc_info=True)
        
        if transcription:
            transcription.status = TranscriptionStatus.FAILED
            db.commit()
        
        progress.fail(error_msg, {"reason": "processing_error", "details": str(e)})
        raise
        
    finally:
        db.close()
