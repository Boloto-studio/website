# Step 3 of making friendships Frog<->Frog: drop the old columns and take
# over their names.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("frogsnet", "0034_copy_friendships_to_frogs"),
    ]

    operations = [
        migrations.AlterUniqueTogether(name="friendrequest", unique_together=set()),
        migrations.RemoveField(model_name="friendrequest", name="from_user"),
        migrations.RemoveField(model_name="friendrequest", name="to_user"),
        migrations.AlterField(
            model_name="friendrequest",
            name="from_frog",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sent_friend_requests",
                to="frogsnet.frog",
            ),
        ),
        migrations.AlterField(
            model_name="friendrequest",
            name="to_frog",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="received_friend_requests",
                to="frogsnet.frog",
            ),
        ),
        migrations.AlterUniqueTogether(name="friendrequest", unique_together={("from_frog", "to_frog")}),
        migrations.RemoveField(model_name="frog", name="friends"),
        migrations.RenameField(model_name="frog", old_name="friends_new", new_name="friends"),
    ]
