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
    # يستخدم الاسم الصحيح للقالب
    return render_template('teacher_dashboard.html')


@app.route('/generate_qr')
def generate_qr():
    registration_url = url_for('register', _external=True)
    qr_img = qrcode.make(registration_url)
    qr_img.save(QR_CODE_FILENAME)
    # يستخدم الاسم الصحيح للقالب
    return render_template('qr_code.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        riyadh_tz = pytz.timezone(TIMEZONE)
        current_time = datetime.now(riyadh_tz).strftime('%Y-%m-%d %H:%M:%S')
        attendee_data = {'name': name, 'student_id': student_id, 'time': current_time}
        r.lpush(REDIS_KEY_ATTENDEES, json.dumps(attendee_data))
        return "<h1>تم تسجيل حضورك بنجاح ✅</h1>"
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