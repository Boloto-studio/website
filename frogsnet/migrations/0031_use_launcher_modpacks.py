# Step 3 of folding base.Modpack into modpacks.Modpack: drop the old links
# and take over their names.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("frogsnet", "0030_frog_modpacks_new_modpackstat_modpack_new"),
        ("modpacks", "0004_merge_base_modpacks"),
    ]

    operations = [
        migrations.RemoveField(model_name="frog", name="modpacks"),
        migrations.RemoveField(model_name="modpackstat", name="modpack"),
        migrations.RenameField(model_name="frog", old_name="modpacks_new", new_name="modpacks"),
        migrations.RenameField(model_name="modpackstat", old_name="modpack_new", new_name="modpack"),
        migrations.AlterField(
            model_name="modpackstat",
            name="modpack",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stats",
                to="modpacks.modpack",
            ),
        ),
    ]
