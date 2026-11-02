# The site uses Django's database cache (CACHES in settings.py), whose table
# is not created by migrations on its own. Create it here so `migrate` is
# enough on a fresh or existing database. Safe to re-run: existing tables
# are skipped.
from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    call_command("createcachetable", database=schema_editor.connection.alias, verbosity=0)


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0024_server_uses_launcher_modpacks"),
    ]

    operations = [
        migrations.RunPython(create_cache_table, migrations.RunPython.noop),
    ]
