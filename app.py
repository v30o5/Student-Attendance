# -*- coding: utf-8 -*-

import os
import redis
import json
import qrcode
import pytz
from flask import Flask, render_template, request, url_for, redirect
from datetime import datetime

# --- إعدادات أساسية ---
template_dir = os.path.abspath('./templates')
static_dir = os.path.abspath('./static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# --- ثوابت التطبيق ---
TIMEZONE = "Asia/Riyadh"
REDIS_KEY_ATTENDEES = 'attendees'
QR_CODE_FILENAME = 'static/attendance_qr.png'

# --- الاتصال بقاعدة بيانات Redis ---
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError("متغير REDIS_URL غير موجود.")
r = redis.from_url(redis_url, decode_responses=True)

# --- صفحات التطبيق (Routes) ---

@app.route('/')
def teacher_dashboard():
    # جلب عدد الحضور لعرضه في لوحة التحكم
    attendee_count = r.llen(REDIS_KEY_ATTENDEES)
    return render_template('teacher_dashboard.html', attendee_count=attendee_count)

@app.route('/generate_qr')
def generate_qr():
    registration_url = url_for('register', _external=True)
    qr_img = qrcode.make(registration_url)
    qr_img.save(QR_CODE_FILENAME)
    return render_template('qr_code.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # صفحة مستقلة للطلاب
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        riyadh_tz = pytz.timezone(TIMEZONE)
        current_time = datetime.now(riyadh_tz).strftime('%Y-%m-%d %H:%M:%S')
        attendee_data = {'name': name, 'student_id': student_id, 'time': current_time}
        r.lpush(REDIS_KEY_ATTENDEES, json.dumps(attendee_data))
        return """
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>تم التسجيل</title>
                <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
                <style>
                    body { font-family: 'Cairo', sans-serif; background-color: #f9f9f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; text-align: center; }
                    .message-card { padding: 40px; background: #fff; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.06); }
                    h1 { color: #6b5f4c; }
                </style>
            </head>
            <body>
                <div class="message-card">
                    <h1>تم تسجيل حضورك بنجاح ✅</h1>
                </div>
            </body>
            </html>
        """
    return render_template('register.html')

@app.route('/list')
def attendees_list():
    raw_data = r.lrange(REDIS_KEY_ATTENDEES, 0, -1)
    attendees_data = [json.loads(item) for item in raw_data]
    return render_template('list.html', attendees=attendees_data)

@app.route('/clear', methods=['POST'])
def clear_list():
    r.delete(REDIS_KEY_ATTENDEES)
    return redirect(url_for('teacher_dashboard'))

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    app.run(debug=True)