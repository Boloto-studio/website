from django.db import migrations


def symmetrize(apps, schema_editor):
    Frog = apps.get_model('frogsnet', 'Frog')
    Through = Frog.friends.through
    for row in list(Through.objects.select_related('frog__user').all()):
        other = Frog.objects.filter(user_id=row.user_id).first()
        if other:
            Through.objects.get_or_create(frog_id=other.id, user_id=row.frog.user_id)


class Migration(migrations.Migration):

    dependencies = [
        ('frogsnet', '0028_frog_last_activity'),
    ]

    operations = [
        migrations.RunPython(symmetrize, migrations.RunPython.noop),
    ]
