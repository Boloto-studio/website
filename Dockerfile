
# Use official Python image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files (optional, uncomment if needed)
RUN python manage.py collectstatic --noinput

# Expose port (Django will run on 8080)
EXPOSE 8080

# Start Django app on port 8080
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
