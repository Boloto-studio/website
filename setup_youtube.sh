#!/bin/bash

# YouTube Integration Setup Script
echo "Setting up YouTube Integration for Boloto Studio Website"
echo "======================================================="

# Check if environment variables are set
if [ -z "$YOUTUBE_API_KEY" ]; then
    echo "⚠️  YOUTUBE_API_KEY is not set!"
    echo "   Get your API key from: https://console.cloud.google.com/apis/credentials"
    echo "   Then run: export YOUTUBE_API_KEY='your_api_key_here'"
    echo ""
fi

if [ -z "$YOUTUBE_CHANNEL_ID" ]; then
    echo "⚠️  YOUTUBE_CHANNEL_ID is not set!"
    echo "   Find your channel ID and run: export YOUTUBE_CHANNEL_ID='your_channel_id_here'"
    echo ""
fi

# Test the sync command
echo "Testing YouTube sync command..."
python manage.py help sync_youtube

if [ $? -eq 0 ]; then
    echo "✅ YouTube sync command is available"
else
    echo "❌ YouTube sync command failed"
fi

echo ""
echo "Setup Instructions:"
echo "==================="
echo "1. Get a YouTube Data API v3 key from Google Cloud Console"
echo "2. Set environment variables:"
echo "   export YOUTUBE_API_KEY='your_api_key_here'"
echo "   export YOUTUBE_CHANNEL_ID='your_channel_id_here'"
echo ""
echo "3. Test the sync manually:"
echo "   python manage.py sync_youtube"
echo ""
echo "4. The sync will automatically run every 15 minutes via the scheduler"
echo ""
echo "For more help, check the management command:"
echo "   python manage.py help sync_youtube"
