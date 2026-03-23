# CifraPartit - Quick Start Guide

## Prerequisites

Before starting, ensure you have installed:
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- **FFmpeg** - [Download](https://ffmpeg.org/download.html)

## Automated Setup

### Windows
```bash
setup.bat
```

### Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

## Manual Setup

### 1. Start Infrastructure Services

```bash
docker-compose up -d
```

Wait ~10 seconds for services to initialize.

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run migrations
alembic upgrade head
```

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
```

## Running the Application

### Terminal 1: Backend API
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Celery Worker (for async tasks)
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
celery -A app.celery_app worker --loglevel=info
```

### Terminal 3: Frontend
```bash
cd frontend
npm run dev
```

## Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Verify Installation

1. Open http://localhost:8000/health - should return `{"status": "healthy"}`
2. Open http://localhost:5173 - should show CifraPartit homepage
3. Check Docker containers: `docker-compose ps` - all should be "Up"

## Troubleshooting

### Port Already in Use
If ports 5432, 6379, 8000, or 5173 are in use:
- Stop conflicting services
- Or modify ports in docker-compose.yml and .env files

### Database Connection Error
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Python Dependencies Error
```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Node Dependencies Error
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

After successful setup:
1. Review the [README.md](README.md) for detailed documentation
2. Check [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for architecture overview
3. Explore the API documentation at http://localhost:8000/docs
4. Start implementing features from the tasks list

## Development Workflow

1. Create a new branch for your feature
2. Make changes to backend or frontend
3. Test locally
4. Run migrations if database schema changed: `alembic revision --autogenerate -m "description"`
5. Commit and push changes

## Stopping Services

```bash
# Stop Docker services
docker-compose down

# Stop backend/frontend (Ctrl+C in respective terminals)
```

## Clean Restart

```bash
# Stop and remove all data
docker-compose down -v

# Restart setup
./setup.sh  # or setup.bat on Windows
```
