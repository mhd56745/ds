import json
import platform
import subprocess
from datetime import datetime

def handler(request):
    """Service status endpoint"""
    try:
        # Get FFmpeg version
        try:
            ffmpeg_version = subprocess.check_output(
                ['ffmpeg', '-version'], 
                stderr=subprocess.STDOUT, 
                text=True
            ).split('\n')[0]
        except:
            ffmpeg_version = "Not available"
        
        status = {
            'status': 'online',
            'service': 'M3U8 to MPD Converter',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'platform': platform.platform(),
            'ffmpeg': ffmpeg_version,
            'endpoints': {
                'convert': '/api/convert',
                'status': '/api/status',
                'download': '/api/download/{id}/{filename}'
            },
            'limits': {
                'max_duration': '5 minutes',
                'max_file_size': '100MB',
                'conversion_timeout': '300 seconds'
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(status, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
