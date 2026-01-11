import os
import json
import tempfile
import subprocess
from datetime import datetime
from urllib.parse import urlparse, unquote
import uuid

# Vercel requires specific handler
def handler(request):
    """Main API handler for Vercel"""
    try:
        if request.method == 'POST':
            return convert_m3u8_to_mpd(request)
        elif request.method == 'GET':
            return show_form()
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def show_form():
    """Show conversion form"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>M3U8 to MPD Converter</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: bold;
            }
            input[type="url"], select {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input[type="url"]:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
                transition: transform 0.3s;
            }
            button:hover {
                transform: translateY(-2px);
            }
            .result {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                display: none;
            }
            .loading {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .notification {
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                display: none;
            }
            .success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 M3U8 to MPD Converter</h1>
            
            <div id="notification" class="notification"></div>
            
            <form id="convertForm">
                <div class="form-group">
                    <label for="m3u8_url">M3U8 URL:</label>
                    <input type="url" id="m3u8_url" required 
                           placeholder="https://example.com/video.m3u8">
                </div>
                
                <div class="form-group">
                    <label for="quality">Quality:</label>
                    <select id="quality">
                        <option value="copy">Copy (No re-encode)</option>
                        <option value="720p">720p (HD)</option>
                        <option value="480p">480p (SD)</option>
                        <option value="360p">360p (Mobile)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="segment_duration">Segment Duration (seconds):</label>
                    <select id="segment_duration">
                        <option value="4">4 seconds</option>
                        <option value="6" selected>6 seconds</option>
                        <option value="10">10 seconds</option>
                    </select>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Converting... This may take a few minutes</p>
                </div>
                
                <button type="submit">Convert to MPD</button>
            </form>
            
            <div class="result" id="result">
                <h3>✅ Conversion Complete!</h3>
                <p>Your MPD file is ready for download:</p>
                <div id="downloadLinks"></div>
                <p><strong>Note:</strong> Files are stored temporarily and will be deleted after 1 hour.</p>
            </div>
        </div>
        
        <script>
        document.getElementById('convertForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const url = document.getElementById('m3u8_url').value;
            const quality = document.getElementById('quality').value;
            const segmentDuration = document.getElementById('segment_duration').value;
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            hideNotification();
            
            try {
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        url: url,
                        quality: quality,
                        segment_duration: segmentDuration
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess('Conversion successful!');
                    
                    // Show download links
                    const downloadLinks = document.getElementById('downloadLinks');
                    downloadLinks.innerHTML = `
                        <p><a href="${result.download_url}" class="download-btn" style="
                            display: inline-block;
                            background: #28a745;
                            color: white;
                            padding: 12px 24px;
                            border-radius: 6px;
                            text-decoration: none;
                            font-weight: bold;
                            margin: 10px 0;
                        ">📥 Download MPD File</a></p>
                        
                        ${result.segments_url ? `
                        <p><a href="${result.segments_url}" style="color: #007bff; text-decoration: underline;">
                            Download all segments (ZIP)
                        </a></p>
                        ` : ''}
                        
                        <p><strong>Direct MPD URL:</strong><br>
                        <code style="background: #f8f9fa; padding: 5px; border-radius: 4px; word-break: break-all;">
                            ${result.download_url}
                        </code></p>
                    `;
                    
                    document.getElementById('result').style.display = 'block';
                } else {
                    showError(result.error || 'Conversion failed');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        });
        
        function showSuccess(message) {
            const notification = document.getElementById('notification');
            notification.className = 'notification success';
            notification.textContent = message;
            notification.style.display = 'block';
        }
        
        function showError(message) {
            const notification = document.getElementById('notification');
            notification.className = 'notification error';
            notification.textContent = message;
            notification.style.display = 'block';
        }
        
        function hideNotification() {
            document.getElementById('notification').style.display = 'none';
        }
        
        // Auto-focus URL input
        document.getElementById('m3u8_url').focus();
        </script>
    </body>
    </html>
    """
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': html
    }

def convert_m3u8_to_mpd(request):
    """Convert M3U8 to MPD"""
    try:
        # Parse request body
        body = json.loads(request.body)
        m3u8_url = body.get('url')
        
        if not m3u8_url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'M3U8 URL is required'})
            }
        
        # Generate unique ID for this conversion
        conversion_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix=f'mpd_{conversion_id}_')
        
        # Output filename
        output_name = f'converted_{timestamp}'
        mpd_file = os.path.join(temp_dir, f'{output_name}.mpd')
        
        # Get conversion parameters
        quality = body.get('quality', 'copy')
        segment_duration = body.get('segment_duration', '6')
        
        # Build FFmpeg command
        if quality == 'copy':
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', m3u8_url,
                '-c', 'copy',
                '-f', 'dash',
                '-use_timeline', '1',
                '-use_template', '1',
                '-seg_duration', segment_duration,
                '-window_size', '5',
                '-remove_at_exit', '0',
                mpd_file
            ]
        else:
            # Re-encode with specific quality
            if quality == '720p':
                video_bitrate = '2000k'
                resolution = '1280x720'
            elif quality == '480p':
                video_bitrate = '1000k'
                resolution = '854x480'
            else:  # 360p
                video_bitrate = '500k'
                resolution = '640x360'
            
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', m3u8_url,
                '-c:v', 'libx264',
                '-b:v', video_bitrate,
                '-maxrate', f'{int(video_bitrate[:-1]) * 1.5}k',
                '-bufsize', f'{int(video_bitrate[:-1]) * 2}k',
                '-preset', 'fast',
                '-s', resolution,
                '-c:a', 'aac',
                '-b:a', '128k',
                '-f', 'dash',
                '-use_timeline', '1',
                '-use_template', '1',
                '-seg_duration', segment_duration,
                '-window_size', '5',
                '-remove_at_exit', '0',
                mpd_file
            ]
        
        # Run FFmpeg
        process = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if process.returncode != 0:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': f'FFmpeg failed: {process.stderr[:500]}',
                    'success': False
                })
            }
        
        # Check if MPD file was created
        if not os.path.exists(mpd_file):
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'MPD file not generated',
                    'success': False
                })
            }
        
        # In Vercel, we can't serve files directly from temp directory
        # So we return the file content in base64 (for small files)
        # For production, use S3 or similar storage
        
        with open(mpd_file, 'r', encoding='utf-8') as f:
            mpd_content = f.read()
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Generate a temporary download URL
        # In production, upload to S3 and return that URL
        download_url = f"/api/download/{conversion_id}/{output_name}.mpd"
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': True,
                'conversion_id': conversion_id,
                'download_url': download_url,
                'filename': f'{output_name}.mpd',
                'message': 'Conversion successful',
                'mpd_content': mpd_content[:5000] + '...' if len(mpd_content) > 5000 else mpd_content
            })
        }
        
    except subprocess.TimeoutExpired:
        return {
            'statusCode': 408,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Conversion timed out (5 minutes)',
                'success': False
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': f'Conversion error: {str(e)}',
                'success': False
            })
        }
