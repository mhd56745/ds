from flask import Flask, request, Response
import requests
from datetime import datetime
import random

app = Flask(__name__)

# قائمة بمصادر M3U البديلة
MULTI_SOURCES = [
    "http://arabitv5.com:8000/netiptv2005/hgftfhft1245",
   
    # أضف مصادر إضافية هنا
]

def create_multisource_url(channel_id, num_sources=2):
    """إنشاء روابط متعددة المصادر لقناة واحدة"""
    sources = []
    
    # اختر مصادر عشوائية من القائمة
    selected_sources = random.sample(MULTI_SOURCES, min(num_sources, len(MULTI_SOURCES)))
    
    for source in selected_sources:
        # افترض أن بنية الرابط هي: base_url/channel_id
        if source.endswith('/'):
            url = f"{source}{channel_id}"
        else:
            url = f"{source}/{channel_id}"
        sources.append(url)
    
    # إرجاع روابط متعددة مفصولة بعلامة |
    return "|".join(sources)

def parse_m3u_content(content):
    """تحليل محتوى M3U وإضافة مصادر متعددة"""
    lines = content.splitlines()
    new_content = []
    
    current_channel_info = None
    current_channel_id = None
    
    for line in lines:
        if line.startswith('#EXTINF:'):
            # حفظ معلومات القناة
            current_channel_info = line
            
            # استخراج ID القناة من الرابط السابق (إذا كان هناك)
            # أو من الاسم في EXTINF
            parts = line.split('"')
            if len(parts) > 1:
                channel_name = parts[-2]
                # يمكنك تعديل هذا المنطق لاستخراج ID بشكل أفضل
                current_channel_id = channel_name.replace(" ", "_").upper()
            
            new_content.append(line)
        
        elif line.startswith('http://') or line.startswith('https://'):
            # استخراج channel_id من الرابط
            if current_channel_id:
                # استخراج آخر جزء من الرابط (الرقم)
                parts = line.split('/')
                if parts:
                    channel_id = parts[-1]
                    
                    # إنشاء روابط متعددة للمصدر
                    multisource_url = create_multisource_url(channel_id, num_sources=2)
                    
                    # إضافة معلومات failover
                    new_content.append(f"#EXTVLCOPT:program={channel_id}")
                    new_content.append(f"#EXTVLCOPT:network-caching=1000")
                    
                    # إضافة الرابط متعدد المصادر
                    new_content.append(multisource_url)
            else:
                new_content.append(line)
            
            # إعادة تعيين القناة الحالية
            current_channel_info = None
            current_channel_id = None
        
        elif line.startswith('#'):
            # الاحتفاظ بجميع التعليقات الأخرى
            new_content.append(line)
        else:
            # الاحتفاظ بالأسطر الأخرى
            new_content.append(line)
    
    return "\n".join(new_content)

def add_multisource_headers(response, original_content):
    """إضافة رؤوس HTTP لتحسين الأداء"""
    headers = {
        'Content-Type': 'audio/x-mpegurl',
        'Cache-Control': 'public, max-age=3600',
        'Access-Control-Allow-Origin': '*',
        'X-M3U-Multisource': 'enabled',
        'X-M3U-Sources-Count': str(len(MULTI_SOURCES)),
        'X-M3U-Generated-At': datetime.now().isoformat()
    }
    
    # إذا كان المحتوى الأصلي يحتوي على معلومات EXT-X-STREAM-INF
    if '#EXT-X-STREAM-INF' in original_content:
        headers['Content-Type'] = 'application/vnd.apple.mpegurl'
    
    return headers

@app.route('/')
def proxy_m3u():
    try:
        # قم بجلب الملف من المصدر الأول (أو أي مصدر تختاره)
        response = requests.get(f"{MULTI_SOURCES[0]}/playlist.m3u8", timeout=10)
        
        if response.status_code == 200:
            original_content = response.text
            
            # تحليل المحتوى وإضافة مصادر متعددة
            modified_content = parse_m3u_content(original_content)
            
            # إضافة رأس M3U
            final_content = "#EXTM3U\n"
            final_content += f"#EXTM3U-url-tvg=\"http://example.com/epg.xml\"\n"
            final_content += f"#EXTM3U-x-tvg-url=\"http://example.com/epg.xml\"\n"
            final_content += f"#PLAYLIST:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            final_content += modified_content
            
            # إضافة رؤوس HTTP
            headers = add_multisource_headers(response, original_content)
            
            return Response(
                final_content,
                mimetype=headers['Content-Type'],
                headers=headers,
                status=response.status_code
            )
        else:
            return f"Error: Could not fetch M3U file. Status code: {response.status_code}", response.status_code
            
    except requests.exceptions.RequestException as e:
        return f"Error connecting to source: {e}", 500

@app.route('/m3u/<path:channel_id>')
def get_channel_m3u(channel_id):
    """حصول على M3U لقناة محددة مع مصادر متعددة"""
    try:
        # اختر مصدر عشوائي
        source = random.choice(MULTI_SOURCES)
        
        # جلب القناة من المصدر المختار
        response = requests.get(f"{source}/{channel_id}", timeout=10)
        
        if response.status_code == 200:
            # إذا كان الملف M3U8، قم بمعالجته
            if response.headers.get('Content-Type', '').lower() in ['application/vnd.apple.mpegurl', 'audio/x-mpegurl']:
                content = response.text
                
                # إذا كان ملف M3U8 (قوائم تشغيل HLS)
                if '#EXT-X-STREAM-INF' in content or '#EXTINF' in content:
                    # استبدال الروابط النسبية بمطلقة
                    base_url = source.rsplit('/', 1)[0] if '/' in source else source
                    modified_lines = []
                    
                    for line in content.splitlines():
                        if line.startswith('#') or not line.strip():
                            modified_lines.append(line)
                        elif not line.startswith('http') and not line.startswith('rtmp'):
                            # ربط مسار نسبي بالمسار الأساسي
                            if not line.startswith('/'):
                                line = '/' + line
                            modified_lines.append(f"{base_url}{line}")
                        else:
                            modified_lines.append(line)
                    
                    content = "\n".join(modified_lines)
            
            headers = {
                'Content-Type': response.headers.get('Content-Type', 'application/octet-stream'),
                'Cache-Control': 'public, max-age=300',
                'X-M3U-Source': source,
                'X-M3U-Backup-Sources': "|".join([s for s in MULTI_SOURCES if s != source]),
                'Access-Control-Allow-Origin': '*'
            }
            
            return Response(
                content,
                mimetype=headers['Content-Type'],
                headers=headers,
                status=response.status_code
            )
        else:
            # محاولة مصدر آخر
            for backup_source in MULTI_SOURCES:
                if backup_source != source:
                    try:
                        backup_response = requests.get(f"{backup_source}/{channel_id}", timeout=5)
                        if backup_response.status_code == 200:
                            headers = {
                                'Content-Type': backup_response.headers.get('Content-Type', 'application/octet-stream'),
                                'Cache-Control': 'public, max-age=300',
                                'X-M3U-Fallback': 'used',
                                'X-M3U-Primary-Source': 'failed',
                                'Access-Control-Allow-Origin': '*'
                            }
                            return Response(
                                backup_response.content,
                                mimetype=headers['Content-Type'],
                                headers=headers,
                                status=backup_response.status_code
                            )
                    except:
                        continue
            
            return f"Error: All sources failed for channel {channel_id}", 503
            
    except requests.exceptions.RequestException as e:
        return f"Error: {e}", 500

@app.route('/health')
def health_check():
    """فحص حالة جميع المصادر"""
    status = {}
    
    for i, source in enumerate(MULTI_SOURCES):
        try:
            response = requests.get(f"{source}/", timeout=5)
            status[source] = {
                "status": "online" if response.status_code < 500 else "error",
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
        except Exception as e:
            status[source] = {
                "status": "offline",
                "error": str(e)
            }
    
    online_count = sum(1 for s in status.values() if s.get("status") == "online")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_sources": len(MULTI_SOURCES),
        "online_sources": online_count,
        "status": "healthy" if online_count > 0 else "unhealthy",
        "sources": status
    }

@app.route('/sources')
def list_sources():
    """عرض قائمة المصادر المتاحة"""
    return {
        "sources": MULTI_SOURCES,
        "count": len(MULTI_SOURCES),
        "default_multisource_count": 2
    }

if __name__ == '__main__':
    # إعدادات للتشغيل المحلي
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True  # لمعالجة طلبات متعددة في نفس الوقت
    )
