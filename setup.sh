#!/bin/bash

echo "🎵 CifraPartit Setup Script"
echo "============================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start infrastructure services
echo "🚀 Starting infrastructure services (PostgreSQL, Redis, MinIO)..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "✅ Infrastructure services started"
echo ""

# Setup backend
echo "🐍 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

echo "Running database migrations..."
alembic upgrade head

cd ..
echo "✅ Backend setup complete"
echo ""

# Setup frontend
echo "⚛️  Setting up frontend..."
cd frontend

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

echo "Installing Node dependencies..."
npm install

cd ..
echo "✅ Frontend setup complete"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Services:"
echo "  API:          http://localhost:8000"
echo "  Frontend:     http://localhost:5173"
echo "  MinIO Console: http://localhost:9001"
