from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from base.models import Event
from base.services.youtube_service import YouTubeService
from datetime import datetime
import os


class Command(BaseCommand):
    help = 'Sync YouTube upcoming streams with Event model'

    def handle(self, *args, **options):
        youtube_service = YouTubeService()

        if not youtube_service.api_key:
            self.stdout.write(
                self.style.ERROR(
                    'No YouTube API key found. Set YOUTUBE_API_KEY in environment variables.')
            )
            return

        if not youtube_service.channel_id:
            self.stdout.write(
                self.style.ERROR(
                    'No YouTube channel ID found. Set YOUTUBE_CHANNEL_ID in environment variables.')
            )
            return

        self.sync_upcoming_streams(youtube_service)

    def sync_upcoming_streams(self, youtube_service):
        """Sync upcoming scheduled streams"""
        self.stdout.write('Syncing upcoming streams...')

        videos = youtube_service.get_upcoming_streams()

        if not videos:
            self.stdout.write('No upcoming streams found.')
            return

        for video in videos:
            video_id = video['id']['videoId']
            video_details = youtube_service.get_video_details(video_id)

            if not video_details:
                continue

            # Decode HTML entities in title and description
            decoded_title = youtube_service.decode_html_entities(
                video['snippet']['title'])
            decoded_description = youtube_service.decode_html_entities(
                video['snippet']['description'])

            # Check if event already exists
            event, created = Event.objects.get_or_create(
                youtube_video_id=video_id,
                defaults={
                    'title': decoded_title,
                    'description': decoded_description,
                    'type': 'stream',
                    'link': f"https://www.youtube.com/watch?v={video_id}",
                    'date': timezone.now(),  # Default date, will be updated below
                }
            )

            # Update with live streaming details if available
            live_details = video_details.get('liveStreamingDetails', {})
            if 'scheduledStartTime' in live_details:
                scheduled_time = datetime.fromisoformat(
                    live_details['scheduledStartTime'].replace('Z', '+00:00')
                )
                event.scheduled_start_time = scheduled_time
                event.date = scheduled_time

            if not created:
                # Update existing event with decoded HTML entities
                event.title = decoded_title
                event.description = decoded_description

            event.save()

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created new event: {event.title}')
                )
            else:
                self.stdout.write(f'Updated event: {event.title}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Sync completed. Processed {len(videos)} videos.')
        )
