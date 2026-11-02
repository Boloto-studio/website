# Step 1 of making friendships Frog<->Frog: new columns next to the old ones,
# filled in by 0034.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("frogsnet", "0032_alter_modpackstat_playtime"),
    ]

    operations = [
        migrations.AddField(
            model_name="frog",
            name="friends_new",
            field=models.ManyToManyField(blank=True, to="frogsnet.frog"),
        ),
        migrations.AddField(
            model_name="friendrequest",
            name="from_frog",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="frogsnet.frog"
            ),
        ),
        migrations.AddField(
            model_name="friendrequest",
            name="to_frog",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="frogsnet.frog"
            ),
        ),
    ]
