#!/bin/bash

# Set the project directory (modify this to your actual path)
PROJECT_DIR="/home/collert/boloto-website"
VENV_DIR="$PROJECT_DIR/venv"

# Enter project directory
cd $PROJECT_DIR || { echo "Failed to cd into $PROJECT_DIR"; exit 1; }

# Pull latest changes
echo "🔄 Pulling latest changes from Git..."
git pull || { echo "❌ Git pull failed!"; exit 1; }

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate" || { echo "❌ Failed to activate venv"; exit 1; }

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt || { echo "❌ pip install failed!"; exit 1; }

# Apply database migrations
echo "🗄 Applying database migrations..."
python manage.py makemigrations || { echo "❌ Database migrations failed!"; exit 1; }
python manage.py migrate || { echo "❌ Database migrations failed!"; exit 1; }

# Collect static files
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput || { echo "❌ collectstatic failed!"; exit 1; }

# Restart Gunicorn
echo "🚀 Restarting Gunicorn..."
sudo systemctl restart gunicorn || { echo "❌ Failed to restart Gunicorn"; exit 1; }

echo "✅ Deployment completed successfully!"
