FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir celery>=5.5.3 django>=5.2.3 django-ninja>=1.4.3 psycopg2-binary>=2.9.10 python-dotenv>=1.1.1 redis>=6.2.0 requests>=2.32.4

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create entrypoint script
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]