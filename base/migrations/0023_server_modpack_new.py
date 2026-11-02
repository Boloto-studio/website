# Step 1 of folding base.Modpack into modpacks.Modpack: a temporary link to
# the launcher model, filled in by modpacks.0004.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0022_alter_server_world_size"),
        ("modpacks", "0003_alter_modpack_git_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="server",
            name="modpack_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="servers",
                to="modpacks.modpack",
            ),
        ),
    ]
