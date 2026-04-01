@echo off
REM StartDevelopment.bat - Start ReadWise development environment

echo.
echo ======================================
echo  ReadWise Development Startup
echo ======================================
echo.

REM Check if .venv exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Check if Redis is available
echo Checking Redis availability...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  WARNING: Redis is not running!
    echo.
    echo To use Celery async tasks, start Redis:
    echo   - Option 1: redis-server (if installed)
    echo   - Option 2: Use WSL: wsl redis-server
    echo   - Option 3: Use Docker: docker run -p 6379:6379 redis
    echo.
    echo Celery will not work until Redis is available.
    echo.
) else (
    echo ✓ Redis is running
)

REM Run migrations
echo Running migrations...
python manage.py migrate --quiet

REM Run tests
echo.
echo Running tests...
python manage.py test accounts --verbosity=2

REM Print startup instructions
echo.
echo ======================================
echo  Startup Complete!
echo ======================================
echo.
echo Services to start in separate terminals:
echo.
echo 1. Celery Worker:
echo    celery -A readwise worker -l info
echo.
echo 2. Django Development Server:
echo    python manage.py runserver
echo.
echo Then open browser to: http://localhost:8000
echo.
echo ======================================
echo.
