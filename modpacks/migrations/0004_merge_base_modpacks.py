# Step 2 of folding base.Modpack into modpacks.Modpack: copy every old pack
# into the launcher model and repoint servers and frogs.net profiles.
#
# An old pack is matched to an existing top-level launcher pack by name (or
# slug); otherwise it is created as an unpublished launcher pack, so nothing
# appears in the launcher until it gets a git repo and is published.
from django.db import migrations
from django.utils.text import slugify


def _unique_slug(Modpack, name):
    base = slugify(name)[:45] or "modpack"
    slug, n = base, 2
    while Modpack.objects.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def merge(apps, schema_editor):
    OldModpack = apps.get_model("base", "Modpack")
    Modpack = apps.get_model("modpacks", "Modpack")
    Server = apps.get_model("base", "Server")
    Frog = apps.get_model("frogsnet", "Frog")
    ModpackStat = apps.get_model("frogsnet", "ModpackStat")

    mapping = {}
    for old in OldModpack.objects.all():
        top_level = Modpack.objects.filter(parent__isnull=True)
        new = (
            top_level.filter(name__iexact=old.name).first()
            or top_level.filter(slug=slugify(old.name)).first()
        )
        if new is None:
            new = Modpack.objects.create(
                name=old.name,
                slug=_unique_slug(Modpack, old.name),
                description=old.description,
                is_published=False,
            )
        elif not new.description and old.description:
            new.description = old.description
            new.save(update_fields=["description"])
        mapping[old.pk] = new.pk

    for old_pk, new_pk in mapping.items():
        Server.objects.filter(modpack_id=old_pk).update(modpack_new_id=new_pk)
        ModpackStat.objects.filter(modpack_id=old_pk).update(modpack_new_id=new_pk)

    OldThrough = Frog.modpacks.through
    NewThrough = Frog.modpacks_new.through
    NewThrough.objects.bulk_create(
        {
            (row.frog_id, mapping[row.modpack_id]): NewThrough(frog_id=row.frog_id, modpack_id=mapping[row.modpack_id])
            for row in OldThrough.objects.all()
        }.values()
    )


class Migration(migrations.Migration):

    dependencies = [
        ("modpacks", "0003_alter_modpack_git_url"),
        ("base", "0023_server_modpack_new"),
        ("frogsnet", "0030_frog_modpacks_new_modpackstat_modpack_new"),
    ]

    operations = [
        migrations.RunPython(merge, migrations.RunPython.noop),
    ]
