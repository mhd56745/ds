from flask import Flask, request, Response
import requests
from datetime import datetime
import random

app = Flask(__name__)

# قائمة بمصادر M3U البديلة
MULTI_SOURCES = [
    "http://arabitv5.com:8000/netiptv2005/hgftfhft1245",
    # أضف مصادر إضافية هنا
    # "http://backup1.com:8000/path",
    # "http://backup2.com:8000/path",
]

# قائمة القنوات من ملف M3U الخاص بك
CHANNELS = {
    "7340": "BEIN SPORT GLOBAL",
    "7339": "BEIN SPORT NEWS",
    "39932": "BEIN SPORTS 1 HD",
    "41037": "BEIN SPORTS 2 HD",
    # أضف جميع القنوات هنا...
}

def create_multisource_url(channel_id, num_sources=1):
    """إنشاء روابط متعددة المصادر لقناة واحدة"""
    sources = []
    
    # استخدام المصادر المتاحة
    for source in MULTI_SOURCES[:min(num_sources, len(MULTI_SOURCES))]:
        url = f"{source}/{channel_id}"
        sources.append(url)
    
    return "|".join(sources)

def generate_m3u_playlist():
    """توليد قائمة تشغيل M3U كاملة"""
    m3u_content = ["#EXTM3U"]
    
    # إضافة رؤوس إضافية
    m3u_content.append("#EXTM3U x-tvg-url=\"http://example.com/epg.xml\"")
    m3u_content.append(f"#PLAYLIST Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    m3u_content.append("")
    
    # إضافة القنوات
    for channel_id, channel_name in CHANNELS.items():
        # معلومات القناة
        m3u_content.append(f'#EXTINF:-1 tvg-id="" tvg-name="{channel_name}" tvg-logo="" group-title="Sports",{channel_name}')
        
        # رابط متعدد المصادر
        stream_url = create_multisource_url(channel_id)
        m3u_content.append(stream_url)
        m3u_content.append("")
    
    return "\n".join(m3u_content)

@app.route('/')
def index():
    """الصفحة الرئيسية مع روابط مفيدة"""
    html = """
    <html>
    <head>
        <title>IPTV Proxy</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📺 IPTV Proxy Service</h1>
            
            <div class="endpoint">
                <h3>📋 M3U Playlist</h3>
                <p>Get complete M3U playlist:</p>
                <code><a href="/playlist.m3u">/playlist.m3u</a></code>
            </div>
            
            <div class="endpoint">
                <h3>📡 Single Channel</h3>
                <p>Get specific channel (replace CHANNEL_ID):</p>
                <code><a href="/channel/7340">/channel/CHANNEL_ID</a></code>
            </div>
            
            <div class="endpoint">
                <h3>⚙️ Health Check</h3>
                <p>Check service status:</p>
                <code><a href="/health">/health</a></code>
            </div>
            
            <div class="endpoint">
                <h3>📊 Statistics</h3>
                <p>Service statistics:</p>
                <code><a href="/stats">/stats</a></code>
            </div>
            
            <hr>
            <p><strong>Total Channels:</strong> {}</p>
            <p><strong>Available Sources:</strong> {}</p>
            <p><strong>Status:</strong> 🟢 Online</p>
        </div>
    </body>
    </html>
    """.format(len(CHANNELS), len(MULTI_SOURCES))
    
    return html

@app.route('/playlist.m3u')
def playlist():
    """إرجاع ملف M3U كامل"""
    try:
        m3u_content = generate_m3u_playlist()
        
        return Response(
            m3u_content,
            mimetype='audio/x-mpegurl',
            headers={
                'Content-Disposition': 'attachment; filename="playlist.m3u"',
                'Cache-Control': 'public, max-age=3600',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        return f"Error generating playlist: {str(e)}", 500

@app.route('/channel/<channel_id>')
def get_channel(channel_id):
    """الحصول على قناة محددة"""
    try:
        if channel_id not in CHANNELS:
            return f"Channel {channel_id} not found", 404
        
        # محاولة جلب القناة من المصدر الأول
        source = MULTI_SOURCES[0] if MULTI_SOURCES else ""
        if not source:
            return "No sources available", 503
        
        response = requests.get(f"{source}/{channel_id}", timeout=10)
        
        if response.status_code == 200:
            return Response(
                response.content,
                mimetype=response.headers.get('Content-Type', 'application/octet-stream'),
                headers={
                    'Cache-Control': 'public, max-age=300',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            return f"Error fetching channel: {response.status_code}", response.status_code
            
    except requests.exceptions.RequestException as e:
        return f"Error connecting to source: {str(e)}", 500
    except Exception as e:
        return f"Internal error: {str(e)}", 500

@app.route('/health')
def health_check():
    """فحص حالة الخدمة"""
    try:
        # اختبار الاتصال بالمصدر الأول
        test_channel = "7340"  # قناة اختبار
        source = MULTI_SOURCES[0] if MULTI_SOURCES else ""
        
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "channels_count": len(CHANNELS),
            "sources_count": len(MULTI_SOURCES),
            "test_channel": test_channel
        }
        
        if source:
            try:
                response = requests.get(f"{source}/{test_channel}", timeout=5)
                status["source_test"] = {
                    "url": f"{source}/{test_channel}",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                status["status"] = "degraded"
                status["source_test"] = {"error": str(e)}
        else:
            status["status"] = "no_sources"
        
        return status
    except Exception as e:
        return {"status": "error", "error": str(e)}, 500

@app.route('/stats')
def stats():
    """إحصائيات الخدمة"""
    return {
        "service": "IPTV Proxy",
        "version": "1.0.0",
        "uptime": datetime.now().isoformat(),
        "channels": {
            "total": len(CHANNELS),
            "categories": 1,  # يمكنك تعديل هذا
            "sports_channels": len([c for c in CHANNELS.values() if "SPORT" in c])
        },
        "sources": {
            "total": len(MULTI_SOURCES),
            "primary": MULTI_SOURCES[0] if MULTI_SOURCES else "None"
        },
        "endpoints": {
            "playlist": "/playlist.m3u",
            "channel": "/channel/{id}",
            "health": "/health",
            "stats": "/stats"
        }
    }

# هذا مهم لـ Vercel
if __name__ == '__main__':
    app.run(debug=True)
else:
    # هذا لـ Vercel
    application = app
