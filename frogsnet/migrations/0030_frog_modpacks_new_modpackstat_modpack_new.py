# Step 1 of folding base.Modpack into modpacks.Modpack: temporary links to
# the launcher model, filled in by modpacks.0004.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("frogsnet", "0029_symmetrize_friendships"),
        ("modpacks", "0003_alter_modpack_git_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="frog",
            name="modpacks_new",
            field=models.ManyToManyField(blank=True, related_name="players", to="modpacks.modpack"),
        ),
        migrations.AddField(
            model_name="modpackstat",
            name="modpack_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stats",
                to="modpacks.modpack",
            ),
        ),
    ]
