import os
import requests
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import html


class YouTubeService:
    def __init__(self):
        self.api_key = getattr(settings, 'YOUTUBE_API_KEY',
                               os.getenv('YOUTUBE_API_KEY'))
        self.channel_id = getattr(
            settings, 'YOUTUBE_CHANNEL_ID', os.getenv('YOUTUBE_CHANNEL_ID'))
        self.base_url = 'https://www.googleapis.com/youtube/v3'

    def get_upcoming_streams(self, max_results=10):
        """Get upcoming scheduled streams from the configured channel"""
        url = f"{self.base_url}/search"
        params = {
            'key': self.api_key,
            'channelId': self.channel_id,
            'part': 'snippet',
            'type': 'video',
            'eventType': 'upcoming',
            'maxResults': max_results,
            'order': 'date'
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        return []

    def get_video_details(self, video_id):
        """Get detailed information about a specific video"""
        url = f"{self.base_url}/videos"
        params = {
            'key': self.api_key,
            'id': video_id,
            'part': 'snippet,liveStreamingDetails,status'
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('items', [])
            return data[0] if data else None
        return None

    def decode_html_entities(self, text):
        """Decode HTML entities in text (e.g., &quot; -> ")"""
        if text:
            return html.unescape(text)
        return text
