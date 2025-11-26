# Copilot Instructions for Boloto Studio Website

This is a Django web application for Boloto Studio, featuring YouTube livestream integration and multi-language support.

## Tech Stack

- **Python**: 3.12
- **Framework**: Django 4.2.14
- **Database**: PostgreSQL
- **Static Files**: WhiteNoise
- **Task Scheduling**: APScheduler / django-apscheduler
- **Containerization**: Docker, Docker Compose
- **Web Server**: Gunicorn (production)

## Project Structure

```
├── boloto_studio_web/    # Django project settings
│   ├── settings.py       # Main configuration
│   ├── urls.py           # Root URL configuration
│   └── wsgi.py           # WSGI application
├── base/                 # Main Django app
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── urls.py           # App URL routing
│   ├── templates/        # HTML templates
│   ├── static/           # Static assets
│   ├── services/         # Business logic services
│   └── management/       # Custom management commands
├── echoes_untamed/       # Secondary Django app
├── locale/               # Translation files (EN, UK)
├── manage.py             # Django management script
└── requirements.txt      # Python dependencies
```

## Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start development server
python manage.py runserver

# Run tests
python manage.py test

# Collect static files
python manage.py collectstatic --noinput

# Create translations
python manage.py makemessages -l uk
python manage.py compilemessages
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

## Code Style

- Follow PEP 8 style guidelines for Python code
- Use Django's coding conventions and patterns
- Prefer class-based views for complex views, function-based for simple ones
- Keep views thin, move business logic to services in `services/` directory
- Use Django's ORM for database queries; avoid raw SQL unless necessary
- Use Django's built-in form validation and model validators

## Testing

- Write tests in each app's `tests.py` file
- Use Django's `TestCase` class for database-dependent tests
- Use `SimpleTestCase` for tests not requiring database
- Test views, models, and services separately
- Run tests with `python manage.py test`

## Database

- PostgreSQL is the database of choice
- Always create migrations for model changes with `python manage.py makemigrations`
- Apply migrations with `python manage.py migrate`
- Never modify existing migrations; create new ones instead

## Environment Variables

Required environment variables (see `.env.example`):

- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Database connection
- `DB_STRING` - Alternative database connection string
- `ENVIRONMENT` - Set to `development` for debug mode
- `YOUTUBE_API_KEY` - YouTube Data API v3 key
- `YOUTUBE_CHANNEL_ID` - YouTube channel ID for sync

## Internationalization

- Supports English (`en`) and Ukrainian (`uk`)
- Use `gettext_lazy` (aliased as `_`) for translatable strings in Python
- Use `{% trans %}` and `{% blocktrans %}` in templates
- Translation files are in `locale/` directory

## Boundaries

- Never commit secrets, API keys, or credentials
- Do not modify `.env` files (they are gitignored)
- Keep `settings.py` changes minimal; use environment variables for configuration
- Do not directly modify migrations that have already been applied
- Avoid adding new dependencies unless absolutely necessary
- Test all changes before committing
