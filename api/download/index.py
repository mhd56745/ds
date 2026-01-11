import os
import json
import base64
from datetime import datetime, timedelta

# Simple in-memory storage for demo
# In production, use S3, Redis, or database
conversion_store = {}

def handler(request):
    """Handle file download requests"""
    try:
        # Extract filename from path
        path = request.path
        parts = path.split('/')
        
        if len(parts) < 4:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'File not found'})
            }
        
        conversion_id = parts[2]
        filename = parts[3]
        
        # Check if conversion exists in store
        if conversion_id in conversion_store:
            data = conversion_store[conversion_id]
            
            # Check if expired (1 hour)
            if datetime.now() - data['timestamp'] > timedelta(hours=1):
                del conversion_store[conversion_id]
                return {
                    'statusCode': 410,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'File expired'})
                }
            
            # Return file content
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/dash+xml',
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Cache-Control': 'no-cache'
                },
                'body': data['content']
            }
        
        # For this example, we'll return a sample MPD
        # In production, you would fetch from storage
        sample_mpd = """<?xml version="1.0" encoding="UTF-8"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" type="static" mediaPresentationDuration="PT30S">
  <Period duration="PT30S">
    <AdaptationSet mimeType="video/mp4" codecs="avc1.42c01e">
      <SegmentTemplate media="video_$Number$.m4s" initialization="video_init.mp4"/>
      <Representation bandwidth="500000" width="640" height="360"/>
    </AdaptationSet>
  </Period>
</MPD>"""
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/dash+xml',
                'Content-Disposition': f'attachment; filename="sample.mpd"'
            },
            'body': sample_mpd
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
