"""
Key detection tasks for analyzing musical key signatures.
"""
from celery import Task
from app.celery_app import celery_app
from app.tasks.task_status import TaskProgress
from app.services.key_detection import KeyDetector
from app.services.storage import storage_service
from app.database import SessionLocal
from app.models.transcription import Transcription
import tempfile
import os
import json
import librosa
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.key_detection.detect_key")
def detect_key(
    self: Task,
    transcription_id: int,
    audio_file_key: str
) -> dict:
    """
    Detect key signature of audio asynchronously.
    
    Args:
        self: Celery task instance
        transcription_id: Database ID of the transcription record
        audio_file_key: Storage key of the audio file
        
    Returns:
        Dictionary containing key detection results
    """
    progress = TaskProgress(self, total_steps=100)
    db = SessionLocal()
    temp_file_path = None
    
    try:
        # Load audio from storage
        progress.update(20, "Loading audio file")
        audio_data = storage_service.get_file(audio_file_key)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        # Load audio with librosa
        progress.update(40, "Analyzing harmonic content")
        y, sr = librosa.load(temp_file_path, sr=22050)
        
        # Detect key
        progress.update(60, "Detecting key signature")
        detector = KeyDetector(sample_rate=sr)
        key_result = detector.detect_key(y)
        
        # Update transcription in database
        progress.update(80, "Saving key detection results")
        transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
        if transcription:
            # Update notation data with key information
            if transcription.notation_data:
                notation_data = json.loads(transcription.notation_data)
                notation_data["detected_key"] = key_result
                transcription.notation_data = json.dumps(notation_data)
                db.commit()
        
        result = {
            "transcription_id": transcription_id,
            "key": key_result["key"],
            "mode": key_result["mode"],
            "key_signature": key_result["key_signature"],
            "confidence": key_result["confidence"],
            "status": "completed"
        }
        
        progress.complete(result)
        logger.info(f"Key detection completed: {key_result['key_signature']}")
        return result
        
    except Exception as e:
        error_msg = f"Key detection failed: {str(e)}"
        logger.error(f"Key detection failed for transcription {transcription_id}: {e}", exc_info=True)
        progress.fail(error_msg, {"reason": "processing_error", "details": str(e)})
        raise
        
    finally:
        db.close()
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
