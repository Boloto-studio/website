from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frogsnet', '0024_alter_frog_show_real_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumpost',
            name='is_open',
            field=models.BooleanField(default=True, help_text='If this post is open for responses. If false, no new responses can be added.'),
        ),
    ]
