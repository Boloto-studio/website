from django.db import models
from django.utils import timezone

# Create your models here.

EVENT_TYPES = [
    ("stream", "Live stream"),
    ("trailer", "Trailer drop"),
]

class HeroSlide(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.URLField(help_text="URL of the background image")
    link = models.URLField(blank=True, null=True)
    link_text = models.CharField(
        max_length=100, blank=True, default="Learn More")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vertical_align = models.CharField(max_length=20, choices=[
        ("top", "Top"),
        ("center", "Center"),
        ("bottom", "Bottom"),
    ], default="center")
    horizontal_align = models.CharField(max_length=20, choices=[
        ("left", "Left"),
        ("center", "Center"),
        ("right", "Right"),
    ], default="center")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', '-created_at']


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=100, choices=EVENT_TYPES)
    link = models.URLField(blank=True, null=True)

    # YouTube integration fields
    youtube_video_id = models.CharField(
        max_length=50, blank=True, null=True, unique=True)
    scheduled_start_time = models.DateTimeField(blank=True, null=True)

    # Sync tracking
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date']

    def is_upcoming(self):
        return self.date >= timezone.now()


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class StaffMember(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='staff_profile')
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    bio = models.TextField(blank=True, max_length=200)
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    discord_url = models.URLField(blank=True, null=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name