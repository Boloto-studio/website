# Step 2 of making friendships Frog<->Frog: copy the data.
#
# Old friendships were Frog->User rows that the views wrote in both
# directions. Only pairs present in both directions are kept; one-sided rows
# (half-removed friendships, or swapped-ID rows left by the old
# symmetrical=True bug) are dropped. Friend requests move to Frog->Frog;
# requests to yourself, to a user without a profile, or to someone you're
# already friends with are dropped.
from django.db import migrations


def copy(apps, schema_editor):
    Frog = apps.get_model("frogsnet", "Frog")
    FriendRequest = apps.get_model("frogsnet", "FriendRequest")
    OldFriends = Frog.friends.through  # frog_id, user_id
    NewFriends = Frog.friends_new.through  # from_frog_id, to_frog_id

    frog_by_user = dict(Frog.objects.values_list("user_id", "id"))
    user_by_frog = {frog: user for user, frog in frog_by_user.items()}

    old_rows = set(OldFriends.objects.values_list("frog_id", "user_id"))
    friendships = set()
    for frog_id, user_id in old_rows:
        other = frog_by_user.get(user_id)
        if other is None or other == frog_id:
            continue
        if (other, user_by_frog.get(frog_id)) in old_rows:
            friendships.add((frog_id, other))
            friendships.add((other, frog_id))
    NewFriends.objects.bulk_create(
        NewFriends(from_frog_id=a, to_frog_id=b) for a, b in sorted(friendships)
    )

    for request in FriendRequest.objects.all():
        to_frog = frog_by_user.get(request.to_user_id)
        if to_frog is None or to_frog == request.from_user_id or (request.from_user_id, to_frog) in friendships:
            request.delete()
            continue
        request.from_frog_id = request.from_user_id
        request.to_frog_id = to_frog
        request.save(update_fields=["from_frog", "to_frog"])


class Migration(migrations.Migration):

    dependencies = [
        ("frogsnet", "0033_frog_friends_new_friendrequest_frogs"),
    ]

    operations = [
        migrations.RunPython(copy, migrations.RunPython.noop),
    ]
