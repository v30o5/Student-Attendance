import os
import redis
import json
from flask import Flask, render_template, request, url_for, redirect
from datetime import datetime
import qrcode
import pytz

# --- ضبط مسارات المجلدات ---
template_dir = os.path.abspath('./templates')
static_dir = os.path.abspath('./static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# --- الاتصال بقاعدة Redis ---
redis_url = os.getenv('REDIS_URL')
r = redis.from_url(redis_url)

# --- الصفحة الرئيسية: لوحة تحكم المدرس ---
@app.route('/')
def teacher_dashboard():
    return render_template('dashboard.html')

# --- توليد الباركود ---
@app.route('/generate_qr')
def generate_qr():
    registration_url = url_for('register', _external=True)
    qr_img = qrcode.make(registration_url)
    qr_img.save('static/attendance_qr.png')
    return render_template('qr.html')

# --- صفحة التسجيل ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        riyadh_tz = pytz.timezone("Asia/Riyadh")
        current_time = datetime.now(riyadh_tz).strftime('%Y-%m-%d %H:%M:%S')
        attendee_data = {'name': name, 'student_id': student_id, 'time': current_time}
        r.lpush('attendees', json.dumps(attendee_data))
        return "<h1>Your attendance has been successfully recorded ✅</h1>"
    return render_template('register.html')

# --- عرض قائمة الحضور ---
@app.route('/list')
def attendees_list():
    raw_data = r.lrange('attendees', 0, -1)
    attendees_data = [json.loads(item) for item in raw_data]
    return render_template('list.html', attendees=attendees_data)

# --- مسح الحضور ---
@app.route('/clear', methods=['POST'])
def clear_list():
    r.delete('attendees')
    return redirect(url_for('teacher_dashboard'))

# --- تشغيل السيرفر محليًا ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True
