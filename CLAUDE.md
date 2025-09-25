# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django REST API project with JWT authentication, Clerk.com integration, and Docker deployment. The project uses Django REST Framework with multiple apps organized under the `app/` directory.

## Development Commands

All Django commands must be run with the virtual environment activated:
```bash
source .venv/bin/activate
```

### Core Django Commands
- **Run development server**: `python manage.py runserver`
- **Run tests**: `python manage.py test`
- **Check for issues**: `python manage.py check`
- **Database migrations**: `python manage.py migrate`
- **Create migrations**: `python manage.py makemigrations`
- **Collect static files**: `python manage.py collectstatic`

### Code Quality & Linting

The project uses modern Python linting tools for consistent code quality:

**Quick Commands:**
- **Run all linting tools**: `./scripts/lint.sh`
- **Check/fix with ruff**: `ruff check --fix .`
- **Format code with black**: `black .`
- **Sort imports**: `isort .`
- **Type checking**: `mypy .`
- **Run pre-commit checks**: `pre-commit run --all-files`

**Tools Configured:**
- **Ruff**: Ultra-fast Python linter and formatter
- **Black**: Uncompromising code formatter
- **isort**: Import statement organizer
- **Flake8**: Style and complexity checking
- **MyPy**: Static type checker
- **Pre-commit**: Automated git hook enforcement

**Automation:**
- Pre-commit hooks automatically run linting on git commits
- VS Code integration with format-on-save and auto-fix
- Django-specific rules for optimal Django development

### Docker Commands
- **Build and run**: `docker-compose up --build`
- **Collect static in Docker**: `docker-compose run --rm django python manage.py collectstatic --noinput`

## Project Architecture

### Main Components
- **srv/**: Django project settings, WSGI/ASGI configuration, and URL routing
  - `settings.py`: Main configuration file with apps, middleware, database settings
  - `urls.py`: Root URL patterns
- **restAPI/**: Core API app containing:
  - Custom user model (`AUTH_USER_MODEL = 'restAPI.CustomUser'`)
  - JWT authentication and Clerk webhook integration
  - Core API views, serializers, and utilities
- **app/**: Directory containing feature-specific Django apps:
  - `tasks/`: Task management functionality
  - `todo/`: Todo list features
  - `blog/`: Blog-related functionality
  - `memo/`: Memo/note-taking features
  - `components/`: Reusable components
  - `jobb/`: Job-related functionality

### Key Technologies
- **Django 5.2.2** with Django REST Framework
- **JWT Authentication**: Using `djangorestframework_simplejwt`
- **Clerk Integration**: For user management and webhooks
- **Database**: SQLite for development, MySQL for production
- **Docker**: Gunicorn + Nginx deployment setup
- **API Documentation**: DRF Spectacular (OpenAPI/Swagger)

### Security & Access
- Admin interface and API docs restricted to local network via Nginx middleware
- CORS and CSRF protection configured
- JWT token blacklist support
- Environment variables in `.env` file (not committed)

### File Structure Notes
- Custom management commands may exist in `restAPI/management/`
- Static files served by Nginx in production
- Media files handled through volume mounts
- Database migrations tracked per app in `migrations/` directories

## Environment Setup

The project requires a `.env` file with:
- `SECRET_KEY`: Django secret key
- Database credentials (MySQL for production)
- `CLERK_SECRET_KEY` and `CLERK_WEBHOOK_KEY`: For Clerk integration
- Email configuration for notifications
- `CLAUDE_EMAIL`, `CLAUDE_PASSWORD`, `CLAUDE_TOKEN`: Claude authentication credentials

## Testing & Quality

- Use `python manage.py test` to run the Django test suite
- Use `python manage.py check` to validate configuration
- No specific linting tools configured in requirements.txt
