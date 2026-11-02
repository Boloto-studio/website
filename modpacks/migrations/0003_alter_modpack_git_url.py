from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("modpacks", "0002_remove_keyredemption_unique_key_per_client_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="modpack",
            name="git_url",
            field=models.URLField(
                blank=True,
                help_text="Repository the launcher pulls the pack from. Required before publishing.",
                max_length=500,
            ),
        ),
    ]
