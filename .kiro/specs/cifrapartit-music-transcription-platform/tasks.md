# Implementation Plan: CifraPartit Music Transcription Platform

## Overview

Este plano implementa uma plataforma web completa de transcrição musical baseada em IA. A arquitetura usa Python/FastAPI para o backend, React/TypeScript para o frontend, PostgreSQL para dados estruturados, Redis para cache e filas, e S3-compatible storage para arquivos. O motor de IA usa modelos especializados por instrumento para transcrição de áudio em notação musical.

## Tasks

- [x] 1. Setup project structure and core infrastructure
  - Create monorepo structure with backend (Python/FastAPI) and frontend (React/TypeScript)
  - Configure Docker Compose for PostgreSQL, Redis, and MinIO (S3-compatible storage)
  - Setup Python virtual environment and install core dependencies (FastAPI, SQLAlchemy, Celery, librosa)
  - Setup React app with TypeScript, Vite, and core dependencies (React Router, TanStack Query, Zustand)
  - Create .env.example files with required environment variables
  - Setup database migrations with Alembic
  - _Requirements: 21.1, 21.3, 23.2_

- [x] 2. Implement database models and core schemas
  - [x] 2.1 Create SQLAlchemy models for User, Transcription, Songbook, Subscription
    - Define User model with email, hashed_password, is_verified, subscription_tier, created_at
    - Define Transcription model with user_id, title, instrument_type, audio_url, notation_data, duration, status, created_at
    - Define Subscription model with user_id, tier (free/pro), expires_at, payment_status
    - Implement database relationships and foreign keys
    - _Requirements: 10.1, 11.1, 13.1_
  
  - [x] 2.2 Write unit tests for database models
    - Test model creation, relationships, and constraints
    - Test cascade deletes and data integrity
    - _Requirements: 10.1, 11.1_

- [x] 3. Implement user authentication system
  - [x] 3.1 Create authentication endpoints (register, login, verify-email, reset-password)
    - Implement POST /api/auth/register with email validation and password hashing (bcrypt cost 12)
    - Implement POST /api/auth/login with JWT token generation
    - Implement POST /api/auth/verify-email with token validation
    - Implement POST /api/auth/reset-password with email token flow
    - Implement rate limiting (5 attempts per 15 minutes per IP)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.7, 23.1_
  
  - [x] 3.2 Create JWT authentication middleware
    - Implement token validation and user context injection
    - Implement token refresh mechanism
    - _Requirements: 10.4, 23.2_
  
  - [x] 3.3 Write unit tests for authentication endpoints
    - Test registration validation, login flow, password reset
    - Test rate limiting and security measures
    - _Requirements: 10.1, 10.6, 10.7_

- [x] 4. Implement file upload and storage system
  - [x] 4.1 Create file upload endpoint with validation
    - Implement POST /api/upload with multipart form data handling
    - Validate file formats (MP3, WAV, FLAC, OGG, M4A, AAC, MP4, AVI, MOV, WEBM)
    - Validate file size limit (100MB max)
    - Extract audio from video files using FFmpeg
    - Store files in S3-compatible storage with unique keys
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  
  - [x] 4.2 Implement browser recording audio upload
    - Create POST /api/upload/recording endpoint for browser-recorded audio
    - Accept WebM audio format from browser MediaRecorder API
    - Convert to standard format if needed
    - _Requirements: 2.4_
  
  - [x] 4.3 Implement YouTube audio extraction
    - Create POST /api/upload/youtube endpoint accepting YouTube URL
    - Use yt-dlp library to extract audio
    - Limit extraction to first 15 minutes
    - Handle extraction errors and restrictions
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 4.4 Write unit tests for file upload validation
    - Test file format validation, size limits, error handling
    - _Requirements: 1.4, 1.5_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Celery task queue and worker infrastructure
  - [x] 6.1 Setup Celery with Redis broker
    - Configure Celery app with Redis connection
    - Create task routing for transcription, OCR, and key detection
    - Implement task status tracking and progress updates
    - _Requirements: 4.6, 4.7, 21.3_
  
  - [x] 6.2 Create WebSocket connection manager for real-time updates
    - Implement WebSocket endpoint at /ws/transcription/{job_id}
    - Send progress notifications during processing
    - Handle connection lifecycle and reconnection
    - _Requirements: 4.4_

- [x] 7. Implement AI transcription engine core
  - [x] 7.1 Create base transcription service with librosa
    - Implement audio loading and preprocessing with librosa
    - Create note detection using onset detection and pitch tracking
    - Implement rhythm quantization and beat tracking
    - Generate basic notation data structure (notes, durations, time signatures)
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 7.2 Implement polyphonic transcription
    - Use multi-pitch detection algorithms for simultaneous notes
    - Implement voice separation for multiple melodic lines
    - _Requirements: 4.2_
  
  - [x] 7.3 Create Celery task for async transcription processing
    - Implement @celery.task decorated function
    - Load audio from storage, process, save results to database
    - Send WebSocket progress updates
    - Handle processing errors and timeouts
    - _Requirements: 4.6, 4.7, 22.1, 22.5_
  
  - [x] 7.4 Write unit tests for transcription core functions
    - Test note detection, rhythm quantization, data structure generation
    - _Requirements: 4.1, 4.2_

- [x] 8. Implement instrument-specific transcription models
  - [x] 8.1 Create instrument model selector and routing
    - Define instrument types enum (piano, guitar, bass, vocals, drums, strings, woodwinds, brass)
    - Route to specialized processing based on instrument type
    - _Requirements: 5.1, 5.2_
  
  - [x] 8.2 Implement guitar/bass tablature generation
    - Create fret position calculator from detected pitches
    - Generate 6-string tablature for guitar, 4-string for bass
    - Optimize fingering positions for playability
    - _Requirements: 5.3, 5.4, 8.1, 8.2, 8.3_
  
  - [x] 8.3 Implement piano grand staff notation
    - Split notes into treble and bass clef ranges
    - Generate two-staff notation data
    - _Requirements: 5.6_
  
  - [x] 8.4 Implement drums percussion notation
    - Map detected drum hits to percussion staff notation
    - Identify kick, snare, hi-hat, toms, cymbals
    - _Requirements: 5.5_
  
  - [x] 8.5 Write integration tests for instrument-specific models
    - Test tablature generation accuracy, piano staff splitting, drum notation
    - _Requirements: 5.3, 5.4, 5.5, 5.6_

- [x] 9. Implement key detection and melody extraction
  - [x] 9.1 Create key detection service
    - Implement harmonic analysis using chroma features
    - Detect major/minor key signatures using Krumhansl-Schmuckler algorithm
    - Return detected key (e.g., "C major", "A minor")
    - _Requirements: 16.1, 16.2_
  
  - [x] 9.2 Implement melody scanner (melody-only extraction)
    - Isolate dominant melodic line using source separation
    - Suppress harmonic and accompaniment elements
    - Generate single-voice transcription
    - _Requirements: 15.1, 15.2, 15.3_
  
  - [x] 9.3 Write unit tests for key detection
    - Test key detection accuracy on known audio samples
    - _Requirements: 16.1, 16.2_

- [x] 10. Implement OCR sheet music scanner
  - [x] 10.1 Create OCR scanning service
    - Accept image uploads (JPG, PNG, PDF)
    - Use Audiveris or similar OMR library for notation recognition
    - Detect notes, rests, clefs, time signatures, key signatures
    - Generate editable transcription data structure
    - _Requirements: 14.1, 14.2, 14.3, 14.4_
  
  - [x] 10.2 Create Celery task for async OCR processing
    - Implement async OCR task with progress tracking
    - Handle image quality errors with helpful messages
    - _Requirements: 14.5, 14.6_
  
  - [x] 10.3 Write unit tests for OCR recognition
    - Test notation element detection on sample sheet music images
    - _Requirements: 14.1, 14.2_

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement transcription API endpoints
  - [x] 12.1 Create POST /api/transcriptions endpoint
    - Accept audio file ID, instrument type, options (melody-only, etc.)
    - Validate user subscription tier and daily limits
    - Enforce free tier limits (30 seconds, 3 per day)
    - Queue transcription job and return job ID
    - _Requirements: 4.7, 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [x] 12.2 Create GET /api/transcriptions/{id} endpoint
    - Return transcription status and data
    - Include notation data, detected key, instrument type
    - Restrict access to transcription owner
    - _Requirements: 11.2, 23.3_
  
  - [x] 12.3 Create GET /api/transcriptions endpoint (list user's transcriptions)
    - Return paginated list of user's transcriptions
    - Support filtering by instrument type
    - Support search by title
    - _Requirements: 11.2, 11.3, 11.4_
  
  - [x] 12.4 Create DELETE /api/transcriptions/{id} endpoint
    - Require confirmation token
    - Delete transcription and associated files
    - _Requirements: 11.5, 11.6_
  
  - [x] 12.5 Write integration tests for transcription endpoints
    - Test creation, retrieval, listing, deletion flows
    - Test authorization and tier limits
    - _Requirements: 12.1, 12.2, 12.3, 23.3_

- [x] 13. Implement export functionality
  - [x] 13.1 Create export service for multiple formats
    - Implement PDF export using music21 or LilyPond
    - Implement MusicXML export with proper schema validation
    - Implement MIDI export with note and timing data
    - Implement GPX (Guitar Pro 7) export
    - Implement GP5 (Guitar Pro 5) export
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [x] 13.2 Create POST /api/transcriptions/{id}/export endpoint
    - Accept format parameter (pdf, musicxml, midi, gpx, gp5)
    - Validate user subscription tier (free users only PDF)
    - Generate export file and store in S3
    - Return download URL with 24-hour expiration
    - _Requirements: 9.7, 12.3, 13.3_
  
  - [x] 13.3 Add copyright metadata to PDF exports
    - Embed "© 2024 Ezequiel Ribeiro" in PDF metadata
    - _Requirements: 19.1, 19.5_
  
  - [x] 13.4 Write unit tests for export format generation
    - Test each export format for validity and completeness
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 14. Implement subscription and payment system
  - [x] 14.1 Create subscription management endpoints
    - Implement POST /api/subscriptions/upgrade for Pro upgrade
    - Implement GET /api/subscriptions/status for current subscription
    - Implement webhook endpoint for payment provider callbacks
    - Update user subscription tier and expiration date
    - _Requirements: 13.5, 13.6_
  
  - [x] 14.2 Implement Pro user priority queue
    - Modify Celery task routing to prioritize Pro users
    - Ensure Pro users get faster processing
    - _Requirements: 13.4_
  
  - [x] 14.3 Write unit tests for subscription logic
    - Test tier upgrades, expiration handling, priority queue
    - _Requirements: 13.5, 13.6_

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement frontend core structure
  - [x] 16.1 Create React app structure with routing
    - Setup React Router with routes: /, /login, /register, /dashboard, /editor/:id, /piano, /guitarra, /vocal, /bateria, /cordas, /sopro
    - Create layout components (Header, Footer, Sidebar)
    - Implement responsive navigation menu
    - _Requirements: 17.1, 18.1, 18.2, 18.3_
  
  - [x] 16.2 Setup state management with Zustand
    - Create auth store for user session
    - Create transcription store for current transcription data
    - Create UI store for modals, notifications, loading states
    - _Requirements: 11.7_
  
  - [x] 16.3 Setup API client with TanStack Query
    - Create axios instance with auth interceptors
    - Create React Query hooks for all API endpoints
    - Implement automatic token refresh
    - _Requirements: 10.4_

- [x] 17. Implement authentication UI
  - [x] 17.1 Create registration page
    - Build registration form with email and password fields
    - Implement client-side validation
    - Show verification email sent message
    - _Requirements: 10.1, 10.2_
  
  - [x] 17.2 Create login page
    - Build login form with email and password
    - Implement "Forgot Password" link
    - Show error messages for invalid credentials
    - _Requirements: 10.4, 10.6_
  
  - [x] 17.3 Create password reset flow
    - Build password reset request page
    - Build password reset confirmation page
    - _Requirements: 10.5_
  
  - [x] 17.4 Implement protected route wrapper
    - Redirect unauthenticated users to login
    - Persist auth state across page refreshes
    - _Requirements: 10.4_

- [x] 18. Implement file upload UI
  - [x] 18.1 Create upload component with drag-and-drop
  - [x] 18.2 Create browser audio recorder component
  - [x] 18.3 Create YouTube URL input component
  - [x] 18.4 Create instrument selector component

- [x] 19. Implement transcription processing UI
  - [x] 19.1 Create transcription job status component
  - [x] 19.2 Create error handling and retry UI

- [x] 20. Implement score editor UI
- [x] 21. Implement Piano Roll view
- [x] 22. Implement tablature view
- [x] 23. Checkpoint - Ensure all tests pass
- [x] 24. Implement key signature and transposition UI
- [x] 25. Implement songbook/dashboard UI
- [x] 26. Implement export UI
- [x] 27. Implement subscription UI
- [x] 28. Implement instrument-specific landing pages
- [x] 29. Implement home page and marketing content
- [x] 30. Implement help and documentation features
- [x] 31. Implement footer and legal pages
- [x] 32. Checkpoint - Ensure all tests pass
- [x] 33. Implement responsive design and mobile optimization
- [x] 34. Implement SEO optimization
- [x] 35. Implement performance optimizations
- [x] 36. Implement security hardening
- [x] 37. Implement error logging and monitoring
- [x] 38. Final integration and testing
- [x] 39. Final checkpoint - Ensure all tests pass
  - [ ] 20.1 Create notation display component
    - Integrate VexFlow or similar library for music notation rendering
    - Display standard staff notation with notes, rests, clefs
    - Show time signature, key signature, tempo markings
    - _Requirements: 6.1, 6.3_
  
  - [ ] 20.2 Implement note editing functionality
    - Enable click to select notes
    - Implement add, delete, modify note operations
    - Update display within 100ms of changes
    - _Requirements: 6.2, 6.5_
  
  - [ ] 20.3 Implement undo/redo functionality
    - Track editing history
    - Add undo/redo buttons
    - Support keyboard shortcuts (Ctrl+Z, Ctrl+Y)
    - _Requirements: 6.6_
  
  - [ ] 20.4 Implement auto-save
    - Save changes every 30 seconds
    - Show save status indicator
    - _Requirements: 6.7_
  
  - [ ] 20.5 Create playback controls
    - Add play/pause button
    - Implement audio playback of notation using Web Audio API or Tone.js
    - Highlight current note during playback
    - _Requirements: 6.4_

- [ ] 21. Implement Piano Roll view
  - [ ] 21.1 Create Piano Roll visualization component
    - Build pitch-time grid with horizontal note bars
    - Implement zoom and pan controls
    - _Requirements: 7.1, 7.2_
  
  - [ ] 21.2 Implement Piano Roll editing
    - Enable drag to move notes horizontally (timing)
    - Enable drag to move notes vertically (pitch)
    - Enable resize to change note duration
    - _Requirements: 7.3, 7.4, 7.5_
  
  - [ ] 21.3 Implement view toggle between standard notation and Piano Roll
    - Add toggle button
    - Preserve note data when switching views
    - _Requirements: 7.6_

- [ ] 22. Implement tablature view
  - [ ] 22.1 Create tablature display component
    - Render 6-string tablature for guitar
    - Render 4-string tablature for bass
    - Show fret numbers on string lines
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ] 22.2 Implement tablature editing
    - Enable click to edit fret positions
    - Sync changes with standard notation
    - _Requirements: 8.5, 8.6_
  
  - [ ] 22.3 Implement view toggle between standard notation and tablature
    - Add toggle button for guitar/bass transcriptions
    - _Requirements: 8.4_

- [ ] 23. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 24. Implement key signature and transposition UI
  - [ ] 24.1 Display detected key signature
    - Show detected key in editor header
    - _Requirements: 16.2, 16.3_
  
  - [ ] 24.2 Implement key signature override
    - Add dropdown to manually select key signature
    - Offer to transpose all notes when key changes
    - _Requirements: 16.4, 16.5_

- [ ] 25. Implement songbook/dashboard UI
  - [ ] 25.1 Create dashboard page with transcription list
    - Display transcriptions in card or table format
    - Show title, instrument, date, duration for each
    - Implement pagination
    - _Requirements: 11.2_
  
  - [ ] 25.2 Implement search and filter functionality
    - Add search input for title search
    - Add filter dropdown for instrument type
    - Update list dynamically
    - _Requirements: 11.3, 11.4_
  
  - [ ] 25.3 Implement delete functionality
    - Add delete button with confirmation modal
    - Remove transcription from list after deletion
    - _Requirements: 11.5, 11.6_

- [ ] 26. Implement export UI
  - [ ] 26.1 Create export modal component
    - Show available export formats based on subscription tier
    - Display format descriptions (PDF, MusicXML, MIDI, GPX, GP5)
    - Show upgrade prompt for free users trying non-PDF formats
    - _Requirements: 9.1, 12.3, 13.3_
  
  - [ ] 26.2 Implement export download flow
    - Trigger export generation on format selection
    - Show generation progress
    - Provide download link when ready
    - _Requirements: 9.7_

- [ ] 27. Implement subscription UI
  - [ ] 27.1 Create pricing/plans page
    - Display free vs Pro feature comparison
    - Show pricing information
    - Add "Upgrade to Pro" call-to-action buttons
    - _Requirements: 12.5, 13.5_
  
  - [ ] 27.2 Create subscription upgrade flow
    - Build payment form (integrate with Stripe or similar)
    - Handle payment success/failure
    - Update UI to reflect Pro status
    - _Requirements: 13.5_
  
  - [ ] 27.3 Display tier limitations
    - Show remaining daily transcriptions for free users
    - Show duration limits in upload UI
    - Display upgrade prompts when limits reached
    - _Requirements: 12.1, 12.2, 12.4, 12.5_

- [ ] 28. Implement instrument-specific landing pages
  - [ ] 28.1 Create landing page template component
    - Build reusable template with hero section, features, examples
    - Include instrument-specific content slots
    - _Requirements: 17.1, 17.2_
  
  - [ ] 28.2 Create content for each instrument page
    - Write copy for /piano, /guitarra, /vocal, /bateria, /cordas, /sopro
    - Add instrument-specific audio sample demos
    - Pre-configure instrument selection for transcription
    - _Requirements: 17.2, 17.3, 17.4_

- [ ] 29. Implement home page and marketing content
  - [ ] 29.1 Create home page with hero section
    - Build hero with headline, description, CTA button
    - Add feature highlights section
    - _Requirements: 20.1, 20.3_
  
  - [ ] 29.2 Create testimonials section
    - Build testimonial carousel component
    - Display at least 6 testimonials with name, role, text
    - _Requirements: 25.1, 25.2, 25.3, 25.5_
  
  - [ ] 29.3 Create "Como Funciona" page
    - Write step-by-step explanation of transcription process
    - Add visual diagrams or illustrations
    - _Requirements: 24.1_
  
  - [ ] 29.4 Create FAQ page
    - Write at least 15 common questions with detailed answers
    - Implement expandable accordion UI
    - _Requirements: 24.2, 24.3_

- [ ] 30. Implement help and documentation features
  - [ ] 30.1 Add tooltips to editor UI
    - Implement tooltip component
    - Add tooltips to complex editor controls
    - _Requirements: 24.5_
  
  - [ ] 30.2 Create contact form
    - Build contact form with name, email, message fields
    - Implement form submission to support email
    - _Requirements: 24.6_
  
  - [ ] 30.3 Create video tutorials section
    - Embed tutorial videos demonstrating key features
    - _Requirements: 24.4_

- [ ] 31. Implement footer and legal pages
  - [ ] 31.1 Create footer component
    - Display "© 2024 Ezequiel Ribeiro. Todos os direitos reservados."
    - Add links to credits, privacy policy, terms of service
    - _Requirements: 19.1, 19.2_
  
  - [ ] 31.2 Create credits page
    - State that CifraPartit is created and owned by Ezequiel Ribeiro
    - Clarify no affiliation with Klang.io
    - _Requirements: 19.2, 19.3, 19.4_
  
  - [ ] 31.3 Create privacy policy and terms of service pages
    - Write privacy policy covering data collection and usage
    - Write terms of service
    - _Requirements: 23.4_

- [ ] 32. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 33. Implement responsive design and mobile optimization
  - [ ] 33.1 Apply responsive CSS to all components
    - Use CSS media queries for breakpoints (320px, 768px, 1024px)
    - Test layout on desktop, tablet, mobile viewports
    - _Requirements: 18.1, 18.2, 18.3_
  
  - [ ] 33.2 Optimize editor for touch devices
    - Implement touch-friendly controls for mobile
    - Add pinch-to-zoom and pan gestures
    - Adapt editor layout for screens below 768px
    - _Requirements: 18.4, 18.5_

- [ ] 34. Implement SEO optimization
  - [ ] 34.1 Add meta tags to all pages
    - Implement React Helmet or similar for dynamic meta tags
    - Add title, description, keywords for each page
    - _Requirements: 20.1_
  
  - [ ] 34.2 Implement Open Graph tags
    - Add OG tags for social media sharing
    - Include og:title, og:description, og:image
    - _Requirements: 20.4_
  
  - [ ] 34.3 Generate sitemap.xml
    - Create sitemap generation script
    - List all public pages
    - _Requirements: 20.2_
  
  - [ ] 34.4 Implement structured data markup
    - Add JSON-LD structured data for music-related content
    - _Requirements: 20.6_
  
  - [ ] 34.5 Optimize for Lighthouse SEO score
    - Run Lighthouse audit
    - Fix issues to achieve score of at least 90
    - _Requirements: 20.5_

- [ ] 35. Implement performance optimizations
  - [ ] 35.1 Optimize frontend bundle size
    - Implement code splitting with React.lazy
    - Enable tree shaking and minification
    - _Requirements: 21.1_
  
  - [ ] 35.2 Implement caching strategies
    - Configure cache headers for static assets (7 days)
    - Implement service worker for offline support (optional)
    - _Requirements: 21.5_
  
  - [ ] 35.3 Enable compression
    - Configure gzip/brotli compression on backend
    - _Requirements: 21.6_
  
  - [ ] 35.4 Optimize score editor rendering
    - Implement virtualization for large scores (500+ notes)
    - Ensure rendering completes within 1 second
    - _Requirements: 21.2_

- [ ] 36. Implement security hardening
  - [ ] 36.1 Add CSRF protection
    - Implement CSRF tokens for all state-changing operations
    - _Requirements: 23.5_
  
  - [ ] 36.2 Add input sanitization
    - Sanitize all user inputs to prevent XSS
    - Use DOMPurify or similar library on frontend
    - _Requirements: 23.6_
  
  - [ ] 36.3 Implement HTTPS enforcement
    - Configure SSL/TLS certificates
    - Redirect HTTP to HTTPS
    - _Requirements: 23.2_

- [ ] 37. Implement error logging and monitoring
  - [ ] 37.1 Setup backend error logging
    - Configure structured logging with Python logging module
    - Log errors with context (user ID, request ID, stack trace)
    - _Requirements: 22.2_
  
  - [ ] 37.2 Setup frontend error tracking
    - Integrate Sentry or similar error tracking service
    - Capture and report JavaScript errors
    - _Requirements: 22.1_

- [ ] 38. Final integration and testing
  - [ ] 38.1 Perform end-to-end testing
    - Test complete user flows: registration → upload → transcription → editing → export
    - Test free tier limitations enforcement
    - Test Pro tier features
    - _Requirements: 12.1, 12.2, 12.3, 13.1, 13.2, 13.3_
  
  - [ ] 38.2 Write integration tests for critical paths
    - Test authentication flow
    - Test transcription creation and processing
    - Test export generation
    - _Requirements: 10.1, 4.1, 9.1_
  
  - [ ] 38.3 Perform load testing
    - Test concurrent transcription processing (10 jobs)
    - Verify queue handling under load
    - _Requirements: 21.3, 21.4_

- [ ] 39. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Backend uses Python/FastAPI, frontend uses React/TypeScript
- AI transcription uses librosa for audio processing
- Database: PostgreSQL, Cache/Queue: Redis, Storage: S3-compatible (MinIO)
- All user data is encrypted and transmitted over HTTPS
- Free tier: 30s duration, 3/day, PDF only
- Pro tier: 15min duration, unlimited, all formats, priority processing
