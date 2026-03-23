#!/bin/bash
# Start Celery worker for CifraPartit
# This starts workers for all queues: transcription, ocr, key_detection

celery -A app.celery_app worker --loglevel=info --concurrency=4 -Q transcription,ocr,key_detection
