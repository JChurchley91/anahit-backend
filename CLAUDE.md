# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django backend application for managing news search configurations and articles. The system is designed to work with a separate scraper service that retrieves news articles based on user configurations.

## Development Commands

### Environment Setup
- `uv sync` - Install and synchronize dependencies
- `uv sync --dev` - Install with development dependencies
- `uv add <package>` - Add a new dependency
- `uv remove <package>` - Remove a dependency

### Django Commands
- `python manage.py runserver` - Start the Django development server (default: http://127.0.0.1:8000)
- `python manage.py makemigrations` - Create new database migrations
- `python manage.py migrate` - Apply database migrations
- `python manage.py createsuperuser` - Create Django admin user
- `python manage.py collectstatic` - Collect static files to staticfiles/ directory
- `python manage.py collectstatic --noinput` - Collect static files without prompts (for CI/CD)
- `python manage.py check` - Check for Django configuration issues
- `python manage.py shell` - Open Django shell for debugging

### Testing
- `python run_tests.py` - Run all tests (recommended)
- `python run_tests.py tests/test_models.py` - Run specific test file
- `python run_tests.py -v` - Run tests with verbose output
- `python run_tests.py --cov=news_config` - Run tests with coverage report
- `python run_tests.py -k "test_name"` - Run specific test by name
- `DJANGO_SETTINGS_MODULE=anahit_backend.settings uv run pytest` - Alternative way to run tests

### Building & Packaging
- `uv build` - Build source distribution and wheel packages
- `uv build --wheel` - Build wheel package only
- `uv build --sdist` - Build source distribution only

### Database
- PostgreSQL database: `anahit-web` on localhost:5432
- Environment variables configured in `.env` file
- User: `postgres`, Password configured in `.env`

## API Endpoints

The Django Ninja API is available at `/api/` with the following endpoints:

### Search Configurations
- `GET /api/configs` - List all active search configurations
- `GET /api/configs/{id}` - Get specific configuration
- `POST /api/configs` - Create new configuration
- `PUT /api/configs/{id}` - Update configuration
- `DELETE /api/configs/{id}` - Delete configuration
- `PATCH /api/configs/{id}/last-executed` - Update last execution time (used by scraper)

### Articles
- `GET /api/articles` - List recent articles (limit: 50)
- `GET /api/configs/{id}/articles` - Get articles for specific configuration
- `POST /api/articles` - Create new article (used by scraper)

API documentation available at `/api/docs` when server is running.

## Project Structure

- `anahit_backend/` - Main Django project directory
  - `settings.py` - Django configuration
  - `urls.py` - URL routing
- `news_config/` - Django app for news management
  - `models.py` - Database models (NewsSearchConfig, NewsArticle)
  - `api.py` - Django Ninja API endpoints
- `manage.py` - Django management script
- `.env` - Environment variables (database config, secrets)

## Models

### NewsSearchConfig
- User-specific search configurations
- Includes keywords, sources, domains, language preferences
- Scheduling frequency (hourly, daily, weekly)
- Tracks last execution time for scraper coordination

### NewsArticle  
- Stores articles retrieved by external scraper
- Links to search configuration that found the article
- Includes article metadata (title, URL, publish date, source, etc.)