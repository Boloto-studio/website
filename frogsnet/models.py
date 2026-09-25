from django.db import models
from django.contrib.auth.models import User
from base.models import AbstractPost
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timesince import timesince
from django.utils.translation import gettext as _


class Frog(models.Model):
    
    tier_choices = [
        ('frog', 'Frog'),
        ('scavenger', 'Scavenger'),
        ('operative', 'Operative'),
        ('overseer', 'Overseer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='frog')
    bio = models.TextField(blank=True, max_length=256)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    last_active = models.DateTimeField(auto_now=True)
    minecraft_username = models.CharField(max_length=255, blank=True)
    friends = models.ManyToManyField(User, blank=True, symmetrical=True, related_name='friends_with')
    tier = models.CharField(max_length=255, blank=True, choices=tier_choices, default='frog')
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    in_game_status = models.CharField(max_length=255, blank=True)
    modpacks = models.ManyToManyField('base.Modpack', blank=True, related_name='players')
    location = models.CharField(max_length=255, blank=True)
    show_real_name = models.CharField(max_length=20, choices=[('public', _('PUBLIC')), ('squad_only', _('SQUAD_ONLY')), ('classified', _('CLASSIFIED'))], default='public')
    show_active_modpacks = models.BooleanField(default=True)
    show_last_played_server = models.BooleanField(default=True)
    allow_friend_requests = models.BooleanField(default=True)
    show_achievements = models.BooleanField(default=True)
    allow_external_wall_posts = models.BooleanField(default=True)

    @property
    def status(self):
        last = self.last_active
        now = timezone.now()
        is_active = False
        last_online_display = None
        in_game = self.in_game_status or ''

        if last:
            delta = now - last
            # active if less than 15 minutes
            if delta.total_seconds() <= 15 * 60:
                is_active = True
                last_online_display = 'just now'
            else:
                # format last seen in the most sensible unit
                # timesince returns strings like '4 minutes', '2 hours'
                last_online_display = f"{timesince(last, now)} ago"

        if in_game:
            string_status = _(f"Playing: {in_game}")
        elif is_active:
            string_status = _("Active")
        else:
            string_status = _(f"Last seen: {last_online_display}")
        return {
            'is_active': is_active,
            'last_online_display': last_online_display,
            'in_game_status': in_game,
            'string_status': string_status
        }

    def __str__(self):
        return self.user.username

class FriendRequest(models.Model):
    from_user = models.ForeignKey(Frog, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.user.username} -> {self.to_user.username}"

class ModpackStat(models.Model):
    modpack = models.ForeignKey('base.Modpack', on_delete=models.CASCADE, related_name='stats')
    frog = models.ForeignKey(Frog, on_delete=models.CASCADE, related_name='modpack_stats')
    playtime = models.DurationField(default=0)
    last_played = models.DateTimeField(null=True, blank=True)

    @property
    def hours_played(self):
        return self.playtime.total_seconds() / 3600

    def __str__(self):
        return f"{self.frog.user.username} - {self.modpack.name}"

class ForumPost(AbstractPost):
    author = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="forum_posts",
        null=True,
        blank=True,
    )
    upvotes = models.ManyToManyField("auth.User", related_name="upvoted_posts", blank=True)
    response_to = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="responses")
    topic = models.ForeignKey("ForumTopic", on_delete=models.CASCADE, related_name="posts", null=True, blank=True)
    is_open = models.BooleanField(default=True, help_text="If this post is open for responses. If false, no new responses can be added.")

    @property
    def is_wall_post(self):
        return self.topic and self.topic.owner_if_wall is not None

    @property
    def display_title(self):
        title = (self.title or '').strip()
        if not title:
            return title

        lowered = title.lower()
        if lowered.startswith('reply'):
            remainder = title[5:].strip()
            if remainder.startswith('#'):
                return f"Reply {remainder}"
            if remainder:
                return f"Reply #{remainder}"
            return 'Reply'

        return title

    def __str__(self):
        return f"{self.author}: {self.title}"

class ForumTopic(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_topic = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="subtopics")
    owner_if_wall = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="wall", null=True, blank=True, help_text="If this is a user wall, the owner of the wall. Using OneToOne so `user.wall` returns a single topic.")
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.owner_if_wall:
            self.title = f"{self.owner_if_wall.username}'s Wall"
        return super().save(*args, **kwargs)

# auto create / save profile and topic for each user
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Frog.objects.create(user=instance)
        ForumTopic.objects.create(owner_if_wall=instance)
    instance.frog.save()
    instance.wall.save()