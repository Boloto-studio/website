# YouTube Integration

This Django application includes simplified YouTube livestream integration that automatically syncs your YouTube channel's upcoming streams with the Event model.

## Features

- **Upcoming Stream Detection**: Detects and syncs scheduled streams from your YouTube channel
- **Automatic Event Creation**: Creates Event records for upcoming streams
- **Scheduled Syncing**: Automatically syncs every 15 minutes via APScheduler
- **Manual Sync**: Run sync manually via management command
- **Single Channel**: Configured for one YouTube channel only

## Setup

1. **Get YouTube API Key**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable YouTube Data API v3
   - Create credentials (API Key)

2. **Find Your Channel ID**
   - Go to your YouTube channel
   - Channel ID is in the URL: `https://www.youtube.com/channel/YOUR_CHANNEL_ID`

3. **Set Environment Variables**
   ```bash
   export YOUTUBE_API_KEY="your_api_key_here"
   export YOUTUBE_CHANNEL_ID="your_channel_id_here"
   ```

4. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Usage

### Manual Sync
```bash
# Sync upcoming streams from your configured channel
python manage.py sync_youtube
```

### Automatic Sync
The scheduler automatically runs the sync every 15 minutes when the Django application is running.

## Model Fields

The `Event` model includes these YouTube-specific fields:

- `youtube_video_id`: Unique YouTube video ID
- `scheduled_start_time`: When the stream is scheduled to start
- `last_synced`: Last time the event was synced with YouTube
- `created_at`: When the event was first created
- `updated_at`: When the event was last updated

## How It Works

1. **Upcoming Streams**: Fetches scheduled streams from your YouTube channel and creates Event records
2. **Event Updates**: Updates existing events with latest information from YouTube
3. **Simple Sync**: Only tracks upcoming streams, no complex status management

## Troubleshooting

- **API Quota**: YouTube API has daily quota limits. Monitor your usage in Google Cloud Console
- **Channel ID**: Make sure your channel ID is correct (starts with UC...)
- **API Key**: Ensure your API key has YouTube Data API v3 enabled
- **Permissions**: API key should have access to public YouTube data

## Files

- `base/models.py`: Event model with simplified YouTube fields
- `base/services/youtube_service.py`: YouTube API interaction service (simplified)
- `base/management/commands/sync_youtube.py`: Simple sync management command
- `base/jobs.py`: Scheduled job for automatic syncing
