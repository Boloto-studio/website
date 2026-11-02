---
description: "Use when editing Django Python files, routes, models, forms, services, or management commands in the Boloto Studio website. Covers app ownership, service-layer usage, defensive database access, migrations, i18n, and focused validation."
name: "Boloto Django Python"
applyTo:
  - "manage.py"
  - "boloto_studio_web/**/*.py"
  - "base/**/*.py"
  - "frogsnet/**/*.py"
  - "echoes_untamed/**/*.py"
---

# Django Python Workflow

- Put public-site pages, content models, contact flow, and YouTube sync work in `base`.
- Put frogs.net forum, auth, profile, friends, and server-list work in `frogsnet`.
- Treat `echoes_untamed` as scaffolded unless the task explicitly extends it.
- Match the existing function-based view style in `base/views.py` and `frogsnet/views.py`.
- If a `base` page depends on optional tables or seed data, preserve the fallback pattern that catches `OperationalError` and `ProgrammingError` so the page still renders in fresh or partially migrated environments.
- Prefer `ModelForm` and built-in auth form patterns over ad hoc request parsing. Keep widget or save customization inside the form class when possible.
- For external APIs or reusable transformations, prefer `base/services/` and keep the view focused on orchestration.
- Management commands should validate required environment variables, report through `self.stdout` or `self.stderr`, and delegate core work to a service.
- Add new migrations normally; never rewrite applied migrations.
- Start verification with the smallest Django command that matches the change. For public-site work, `python manage.py test base` is the default first check.
- If full SQLite migrations fail for unrelated repo reasons, document that and fall back to focused route, form, or model validation instead of unrelated migration fixes.
- See [YOUTUBE_INTEGRATION.md](../../YOUTUBE_INTEGRATION.md) for sync behavior and environment requirements.