from flask import Flask, request, Response
import requests

app = Flask(__name__)

# الرابط الأصلي لملف M3U8 الذي تريد عمل بروكسي له
TARGET_URL = "http://e9f411eb.ottolok.net/iptv/YDFRWUQHUKMN2V/6124/index.m3u8"

@app.route('/')
def proxy_m3u8():
    try:
        # إرسال طلب للحصول على محتوى ملف M3U8 الأصلي
        response = requests.get(TARGET_URL, stream=True)
        
        # التأكد من أن الطلب نجح
        if response.status_code == 200:
            # قراءة المحتوى النصي لملف M3U8
            content = response.text
            
            # استخراج الرابط الأساسي للملفات المقطعة (TS files)
            base_url = TARGET_URL.rsplit('/', 1)[0] + '/'
            
            # تعديل المحتوى: استبدال الروابط النسبية بالروابط المطلقة
            new_content = []
            for line in content.splitlines():
                # إذا كان السطر يبدأ بعلامة # فهو وسم (tag) ولا يحتاج إلى تعديل
                if line.startswith('#'):
                    new_content.append(line)
                # إذا كان السطر رابطاً وليس فارغاً ولا يبدأ بـ http (أي رابط نسبي)
                elif line.strip() and not line.startswith('http'):
                    # هذا هو رابط ملف TS نسبي، نجعله مطلقاً
                    new_content.append(base_url + line.strip())
                else:
                    # رابط مطلق أو سطر فارغ
                    new_content.append(line)
            
            final_content = "\n".join(new_content)
            
            # إنشاء استجابة مع المحتوى المعدل
            return Response(
                final_content,
                mimetype=response.headers.get('Content-Type', 'application/vnd.apple.mpegurl'),
                status=response.status_code
            )
        else:
            # إذا فشل الطلب على الرابط الأصلي
            return f"Error: Could not fetch M3U8 file. Status code: {response.status_code}", response.status_code

    except requests.exceptions.RequestException as e:
        return f"Error connecting to target URL: {e}", 500

# هذا سطر مهم لـ Vercel - لا تحذفه
if __name__ == '__main__':
    app.run()
