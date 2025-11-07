from django.db import models
from django.utils import timezone

# Create your models here.

EVENT_TYPES = [
    ("stream", "Live stream"),
    ("trailer", "Trailer drop"),
]


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
