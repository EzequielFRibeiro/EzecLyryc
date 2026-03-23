# CifraPartit Project Structure

## Overview
Monorepo structure with separate backend (Python/FastAPI) and frontend (React/TypeScript) applications.

## Directory Structure

```
cifrapartit/
├── backend/                      # Python FastAPI backend
│   ├── alembic/                  # Database migrations
│   │   ├── versions/             # Migration files
│   │   ├── env.py                # Alembic environment config
│   │   └── script.py.mako        # Migration template
│   ├── app/
│   │   ├── api/                  # API route handlers
│   │   ├── models/               # SQLAlchemy models
│   │   │   ├── user.py           # User model
│   │   │   └── transcription.py  # Transcription model
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic layer
│   │   ├── tasks/                # Celery async tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── config.py             # Application settings
│   │   ├── database.py           # Database connection
│   │   └── main.py               # FastAPI application
│   ├── .env.example              # Environment variables template
│   ├── alembic.ini               # Alembic configuration
│   └── requirements.txt          # Python dependencies
│
├── frontend/                     # React TypeScript frontend
│   ├── src/
│   │   ├── lib/
│   │   │   └── api.ts            # Axios API client
│   │   ├── stores/
│   │   │   └── authStore.ts      # Zustand auth store
│   │   ├── App.tsx               # Main app component
│   │   ├── main.tsx              # Entry point
│   │   ├── index.css             # Global styles
│   │   └── vite-env.d.ts         # Vite type definitions
│   ├── .env.example              # Environment variables template
│   ├── index.html                # HTML template
│   ├── package.json              # Node dependencies
│   ├── tsconfig.json             # TypeScript config
│   ├── tsconfig.node.json        # TypeScript config for Vite
│   └── vite.config.ts            # Vite configuration
│
├── .gitignore                    # Git ignore rules
├── docker-compose.yml            # Infrastructure services
├── README.md                     # Project documentation
├── setup.sh                      # Setup script (Linux/Mac)
└── setup.bat                     # Setup script (Windows)
```

## Infrastructure Services (Docker Compose)

- **PostgreSQL** (port 5432): Main database
- **Redis** (port 6379): Cache and Celery broker
- **MinIO** (port 9000, console 9001): S3-compatible object storage

## Key Technologies

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration tool
- **Celery**: Distributed task queue
- **librosa**: Audio processing library
- **boto3**: S3 client for MinIO
- **yt-dlp**: YouTube audio extraction

### Frontend
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool
- **React Router**: Client-side routing
- **TanStack Query**: Server state management
- **Zustand**: Client state management
- **Axios**: HTTP client

## Configuration Files

### Backend (.env)
- Database connection
- Redis connection
- S3/MinIO credentials
- JWT secret
- Email SMTP settings
- File upload limits
- Tier limitations

### Frontend (.env)
- API base URL
- WebSocket base URL

## Next Steps

After Task 1 completion, the following will be implemented:
- Database models (User, Transcription, Subscription)
- Authentication system (JWT)
- File upload endpoints
- AI transcription engine
- Score editor UI
- Export functionality
