"""
Transcription tasks for async audio processing.
"""
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from app.celery_app import celery_app
from app.tasks.task_status import TaskProgress
from app.services.transcription_engine import TranscriptionEngine
from app.services.polyphonic_transcription import PolyphonicTranscriber
from app.services.storage import storage_service
from app.database import SessionLocal
from app.models.transcription import Transcription, TranscriptionStatus
import tempfile
import os
import json
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.transcription.process_transcription")
def process_transcription(
    self: Task,
    transcription_id: int,
    audio_file_key: str,
    instrument_type: str,
    user_id: int,
    duration_limit: float = None,
    options: dict = None
) -> dict:
    """
    Process audio transcription asynchronously.
    
    Args:
        self: Celery task instance
        transcription_id: Database ID of the transcription record
        audio_file_key: Storage key of the audio file
        instrument_type: Type of instrument (piano, guitar, bass, etc.)
        user_id: ID of the user requesting transcription
        duration_limit: Maximum duration to process in seconds
        options: Additional transcription options (melody_only, polyphonic, etc.)
        
    Returns:
        Dictionary containing transcription results
    """
    progress = TaskProgress(self, total_steps=100)
    db = SessionLocal()
    temp_file_path = None
    
    try:
        # Update database status to processing
        transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")
        
        transcription.status = TranscriptionStatus.PROCESSING
        db.commit()
        
        # Step 1: Load audio from storage (10%)
        progress.update(5, "Loading audio file from storage")
        logger.info(f"Loading audio from storage: {audio_file_key}")
        
        audio_data = storage_service.get_file(audio_file_key)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        progress.update(10, "Audio file loaded successfully")
        
        # Step 2: Initialize transcription engine (15%)
        progress.update(15, "Initializing transcription engine")
        engine = TranscriptionEngine()
        
        # Step 3: Load and preprocess audio (25%)
        progress.update(20, "Loading and preprocessing audio")
        y, duration = engine.load_audio(temp_file_path, duration=duration_limit)
        y = engine.preprocess_audio(y)
        
        progress.update(25, f"Audio preprocessed: {duration:.2f}s")
        
        # Step 4: Detect notes (50%)
        progress.update(30, "Detecting notes and pitches")
        
        # Check if polyphonic transcription is requested
        use_polyphonic = options and options.get("polyphonic", False)
        
        if use_polyphonic:
            # Use polyphonic transcription
            poly_transcriber = PolyphonicTranscriber()
            onset_times = engine.detect_onsets(y)
            poly_result = poly_transcriber.transcribe_polyphonic(y, onset_times, max_voices=4)
            notes = poly_result["all_notes"]
            progress.update(50, f"Detected {len(notes)} notes across {poly_result['num_voices']} voices")
        else:
            # Use monophonic transcription
            notes = engine.detect_notes(y)
            progress.update(50, f"Detected {len(notes)} notes")
        
        # Step 5: Detect tempo and beats (65%)
        progress.update(55, "Detecting tempo and beats")
        tempo, beat_times = engine.detect_tempo_and_beats(y)
        progress.update(65, f"Detected tempo: {tempo:.2f} BPM")
        
        # Step 6: Quantize rhythm (75%)
        progress.update(70, "Quantizing rhythm")
        quantized_notes = engine.quantize_rhythm(notes, tempo, beat_times)
        progress.update(75, "Rhythm quantized")
        
        # Step 7: Generate notation data (85%)
        progress.update(80, "Generating notation data")
        notation_data = engine.generate_notation_data(
            quantized_notes,
            tempo,
            duration,
            instrument_type
        )
        progress.update(85, "Notation data generated")
        
        # Step 8: Save to database (95%)
        progress.update(90, "Saving transcription to database")
        
        transcription.notation_data = json.dumps(notation_data)
        transcription.duration = duration
        transcription.status = TranscriptionStatus.COMPLETED
        db.commit()
        
        progress.update(95, "Transcription saved")
        
        # Step 9: Complete (100%)
        result = {
            "transcription_id": transcription_id,
            "instrument_type": instrument_type,
            "duration": duration,
            "tempo": tempo,
            "total_notes": len(quantized_notes),
            "notation_data": notation_data,
            "status": "completed"
        }
        
        progress.complete(result)
        logger.info(f"Transcription {transcription_id} completed successfully")
        return result
        
    except SoftTimeLimitExceeded:
        error_msg = "Transcription processing exceeded time limit"
        logger.error(f"Transcription {transcription_id} timed out")
        
        # Update database
        if transcription:
            transcription.status = TranscriptionStatus.FAILED
            db.commit()
        
        progress.fail(error_msg, {"reason": "timeout"})
        raise
        
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        logger.error(f"Transcription {transcription_id} failed: {e}", exc_info=True)
        
        # Update database
        if transcription:
            transcription.status = TranscriptionStatus.FAILED
            db.commit()
        
        progress.fail(error_msg, {"reason": "processing_error", "details": str(e)})
        raise
        
    finally:
        # Cleanup
        db.close()
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@celery_app.task(bind=True, name="app.tasks.transcription.process_transcription_priority")
def process_transcription_priority(
    self: Task,
    transcription_id: int,
    audio_file_key: str,
    instrument_type: str,
    user_id: int,
    duration_limit: float = None,
    options: dict = None
) -> dict:
    """
    Process audio transcription with priority (for Pro users).
    
    This task has the same implementation as process_transcription but is routed
    with higher priority in the queue.
    
    Args:
        self: Celery task instance
        transcription_id: Database ID of the transcription record
        audio_file_key: Storage key of the audio file
        instrument_type: Type of instrument (piano, guitar, bass, etc.)
        user_id: ID of the user requesting transcription
        duration_limit: Maximum duration to process in seconds
        options: Additional transcription options (melody_only, polyphonic, etc.)
        
    Returns:
        Dictionary containing transcription results
    """
    # Delegate to the main transcription task
    return process_transcription(
        self,
        transcription_id,
        audio_file_key,
        instrument_type,
        user_id,
        duration_limit,
        options
    )
