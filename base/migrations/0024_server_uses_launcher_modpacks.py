# Step 3 of folding base.Modpack into modpacks.Modpack: drop the old link and
# the old model.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0023_server_modpack_new"),
        ("modpacks", "0004_merge_base_modpacks"),
        ("frogsnet", "0031_use_launcher_modpacks"),
    ]

    operations = [
        migrations.RemoveField(model_name="server", name="modpack"),
        migrations.RenameField(model_name="server", old_name="modpack_new", new_name="modpack"),
        migrations.AlterField(
            model_name="server",
            name="modpack",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="servers",
                to="modpacks.modpack",
            ),
        ),
        migrations.DeleteModel(name="Modpack"),
    ]
