@echo off
echo 🎵 CifraPartit Setup Script
echo ============================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

echo ✅ Docker is running
echo.

REM Start infrastructure services
echo 🚀 Starting infrastructure services (PostgreSQL, Redis, MinIO)...
docker-compose up -d

echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo ✅ Infrastructure services started
echo.

REM Setup backend
echo 🐍 Setting up backend...
cd backend

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
)

echo Running database migrations...
alembic upgrade head

cd ..
echo ✅ Backend setup complete
echo.

REM Setup frontend
echo ⚛️  Setting up frontend...
cd frontend

if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
)

echo Installing Node dependencies...
call npm install

cd ..
echo ✅ Frontend setup complete
echo.

echo 🎉 Setup complete!
echo.
echo To start the application:
echo   Backend:  cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo   Frontend: cd frontend ^&^& npm run dev
echo.
echo Services:
echo   API:           http://localhost:8000
echo   Frontend:      http://localhost:5173
echo   MinIO Console: http://localhost:9001
