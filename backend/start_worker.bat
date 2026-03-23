@echo off
REM Start Celery worker for CifraPartit
REM This starts workers for all queues: transcription, ocr, key_detection

celery -A app.celery_app worker --loglevel=info --concurrency=4 --pool=solo -Q transcription,ocr,key_detection
