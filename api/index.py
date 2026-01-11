from flask import Flask, Response, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

# قائمة القنوات (مثال مختصر - أضف باقي القنوات)
CHANNELS = {
    "7340": "BEIN SPORT GLOBAL",
    "7339": "BEIN SPORT NEWS",
    "39932": "BEIN SPORTS 1 HD",
    "41037": "BEIN SPORTS 2 HD",
    "67546": "BEIN SPORTS 3 HD",
    "67548": "BEIN SPORTS 4 HD",
    "41034": "BEIN SPORTS 5 HD",
    "41033": "BEIN SPORTS 6 HD",
    "41032": "BEIN SPORTS 7 HD",
    "223613": "BEIN SPORTS 8 HD",
    "223614": "BEIN SPORTS 9 HD"
}

# المصدر الأساسي
BASE_SOURCE = "http://arabitv5.com:8000/netiptv2005/hgftfhft1245"

def generate_m3u():
    """توليد ملف M3U كامل"""
    lines = ["#EXTM3U"]
    
    for channel_id, channel_name in CHANNELS.items():
        # سطر معلومات القناة
        lines.append(f'#EXTINF:-1 tvg-id="" tvg-name="{channel_name}" tvg-logo="" group-title="beiN Sport",{channel_name}')
        # سطر رابط القناة
        lines.append(f"{BASE_SOURCE}/{channel_id}")
    
    return "\n".join(lines)

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IPTV Proxy Service</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }
            .endpoint {
                background: #f9f9f9;
                padding: 15px;
                margin: 15px 0;
                border-left: 4px solid #4CAF50;
                border-radius: 5px;
            }
            code {
                background: #e0e0e0;
                padding: 5px 10px;
                border-radius: 3px;
                font-family: monospace;
            }
            a {
                color: #4CAF50;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .stat-box {
                background: #4CAF50;
                color: white;
                padding: 20px;
                border-radius: 5px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📺 IPTV Proxy Service</h1>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>Total Channels</h3>
                    <p style="font-size: 24px; margin: 10px 0;">{}</p>
                </div>
                <div class="stat-box">
                    <h3>Status</h3>
                    <p style="font-size: 24px; margin: 10px 0;">🟢 Online</p>
                </div>
            </div>
            
            <h2>📋 Endpoints</h2>
            
            <div class="endpoint">
                <h3>Complete M3U Playlist</h3>
                <p>Get full IPTV playlist:</p>
                <p><code><a href="/playlist.m3u">/playlist.m3u</a></code></p>
                <p>Use this URL in your IPTV player</p>
            </div>
            
            <div class="endpoint">
                <h3>Individual Channel</h3>
                <p>Get specific channel stream:</p>
                <p><code>/channel/CHANNEL_ID</code></p>
                <p>Example: <code><a href="/channel/7340">/channel/7340</a></code></p>
            </div>
            
            <div class="endpoint">
                <h3>Health Check</h3>
                <p>Check service status:</p>
                <p><code><a href="/health">/health</a></code></p>
            </div>
            
            <div class="endpoint">
                <h3>Channel List</h3>
                <p>Get JSON list of all channels:</p>
                <p><code><a href="/channels">/channels</a></code></p>
            </div>
            
            <h2>📱 How to Use</h2>
            <ol>
                <li>Copy the playlist URL: <code>{}/playlist.m3u</code></li>
                <li>Add it to your IPTV player (VLC, IPTV Smarters, etc.)</li>
                <li>Enjoy streaming!</li>
            </ol>
            
            <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                <p>Generated on: {}</p>
                <p>Source: {}</p>
            </footer>
        </div>
    </body>
    </html>
    """.format(len(CHANNELS), request.host_url.rstrip('/'), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), BASE_SOURCE)

@app.route('/playlist.m3u')
def playlist():
    """إرجاع ملف M3U كامل"""
    m3u_content = generate_m3u()
    
    return Response(
        m3u_content,
        mimetype='audio/x-mpegurl',
        headers={
            'Content-Type': 'audio/x-mpegurl',
            'Content-Disposition': 'attachment; filename="iptv_playlist.m3u"',
            'Cache-Control': 'public, max-age=3600',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/channel/<channel_id>')
def get_channel(channel_id):
    """الحصول على قناة محددة"""
    if channel_id not in CHANNELS:
        return Response("Channel not found", status=404)
    
    try:
        # جلب القناة من المصدر
        url = f"{BASE_SOURCE}/{channel_id}"
        response = requests.get(url, stream=True, timeout=10)
        
        if response.status_code == 200:
            return Response(
                response.iter_content(chunk_size=8192),
                content_type=response.headers.get('Content-Type', 'video/mp2t'),
                headers={
                    'Cache-Control': 'public, max-age=300',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            return Response(f"Error: {response.status_code}", status=response.status_code)
            
    except requests.exceptions.RequestException as e:
        return Response(f"Error: {str(e)}", status=500)

@app.route('/health')
def health():
    """فحص حالة الخدمة"""
    try:
        # اختبار اتصال
        test_url = f"{BASE_SOURCE}/7340"
        response = requests.head(test_url, timeout=5)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "channels": len(CHANNELS),
            "source": BASE_SOURCE,
            "source_status": response.status_code if response else "unknown"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, 503

@app.route('/channels')
def channels_list():
    """قائمة جميع القنوات بتنسيق JSON"""
    channels_array = []
    
    for channel_id, channel_name in CHANNELS.items():
        channels_array.append({
            "id": channel_id,
            "name": channel_name,
            "url": f"{request.host_url.rstrip('/')}/channel/{channel_id}",
            "source_url": f"{BASE_SOURCE}/{channel_id}"
        })
    
    return {
        "channels": channels_array,
        "count": len(channels_array),
        "generated_at": datetime.now().isoformat()
    }

# هذا مهم لـ Vercel
if __name__ == '__main__':
    app.run(debug=True)
else:
    # هذا لـ Vercel
    application = app
