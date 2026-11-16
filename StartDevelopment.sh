#!/bin/bash
# StartDevelopment.sh - Start ReadWise development environment

echo ""
echo "======================================"
echo " ReadWise Development Startup"
echo "======================================"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Check if Redis is available
echo "Checking Redis availability..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo ""
    echo "⚠️  WARNING: Redis is not running!"
    echo ""
    echo "To use Celery async tasks, start Redis:"
    echo "  - Mac: brew install redis && redis-server"
    echo "  - Linux: apt-get install redis-server && redis-server"
    echo "  - Docker: docker run -p 6379:6379 redis"
    echo ""
    echo "Celery will not work until Redis is available."
    echo ""
else
    echo "✓ Redis is running"
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Run tests
echo ""
echo "Running tests..."
python manage.py test accounts --verbosity=2

# Print startup instructions
echo ""
echo "======================================"
echo " Startup Complete!"
echo "======================================"
echo ""
echo "Services to start in separate terminals:"
echo ""
echo "1. Celery Worker:"
echo "   celery -A readwise worker -l info"
echo ""
echo "2. Django Development Server:"
echo "   python manage.py runserver"
echo ""
echo "Then open browser to: http://localhost:8000"
echo ""
echo "======================================"
echo ""
