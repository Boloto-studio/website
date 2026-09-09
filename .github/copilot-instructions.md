# Copilot Instructions for Boloto Studio Website

This repository is a Django 4.2 site with two active product surfaces and one scaffolded app:

- `base`: the public Boloto Studio site, contact flow, blog and event content, staff pages, and YouTube sync.
- `frogsnet`: the forum, auth, profile, friends, and server-list experience.
- `echoes_untamed`: scaffold only; do not assume live routes, models, or views unless the task explicitly targets it.

## Working Areas

- Project settings and root routing live in `boloto_studio_web/`.
- Shared public-site templates and styles live in `base/templates/base/` and `base/static/base/`.
- YouTube sync lives in `base/services/youtube_service.py`, `base/jobs.py`, and `base/management/commands/sync_youtube.py`.
- Locale files live in `locale/`; user-facing copy should stay translation-ready.

## Runtime and Validation

- Install dependencies with `pip install -r requirements.txt`.
- Run `python manage.py migrate` before local runs, then `python manage.py runserver`.
- The app supports either `DB_STRING` or the `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` environment variables.
- The deployment image currently pins Python 3.11 in `Dockerfile`; keep backend changes compatible with Python 3.11 unless the runtime is updated.
- Start validation with the narrowest command that covers the change. For public-site work, `python manage.py test base` is the default first check.
- Full SQLite migration or test runs can fail because of existing repo issues unrelated to the current change. When Postgres is unavailable, prefer focused validation over broad migration churn.

## Project Conventions

- Match the existing function-based view style unless there is a strong reason to introduce a class-based view.
- Keep views thin. Move reusable logic and external API work into `base/services/` when that pattern already fits the change.
- Preserve the defensive fallback pattern in `base/views.py`: pages that depend on optional database content should continue to handle `OperationalError` and `ProgrammingError` gracefully during fresh or partially migrated setups.
- Wrap new user-facing strings in `_()` in Python and `{% trans %}` or `{% blocktrans %}` in templates.
- Never edit applied migrations; add a new migration instead.
- Keep `settings.py` changes minimal and environment-driven.

## Reference Docs

- Frontend direction and visual language: [DESIGN.md](../DESIGN.md)
- YouTube sync setup and behavior: [YOUTUBE_INTEGRATION.md](../YOUTUBE_INTEGRATION.md)
