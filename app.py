import os
import redis
import json
from flask import Flask, render_template, request, url_for, redirect
from datetime import datetime
import qrcode
import pytz

# تحديد المسارات
template_dir = os.path.abspath('./templates')
static_dir = os.path.abspath('./static')

# تعريف التطبيق
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# --- اتصال Redis ---
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    redis_url = "redis://localhost:6379/0"  # تشغيل محلي إذا ما فيه متغير بيئة
r = redis.from_url(redis_url)

# --- الصفحة الرئيسية (لوحة التحكم للمعلم) ---
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# --- توليد باركود ---
@app.route('/generate_qr')
def generate_qr():
    # رابط تسجيل الحضور
    registration_url = url_for('register', _external=True)

    # إنشاء باركود
    qr_img = qrcode.make(registration_url)
    qr_path = os.path.join(static_dir, 'attendance_qr.png')
    qr_img.save(qr_path)

    return render_template('qr.html')

# --- تسجيل حضور الطلاب ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']

        # الوقت بتوقيت الرياض
        riyadh_tz = pytz.timezone("Asia/Riyadh")
        current_time = datetime.now(riyadh_tz).strftime('%Y-%m-%d %H:%M:%S')

        # تخزين البيانات
        attendee_data = {
            'name': name,
            'student_id': student_id,
            'time': current_time
        }
        r.lpush('attendees', json.dumps(attendee_data))

        return "<h2 style='color:green;text-align:center;margin-top:50px;'>✅ تم تسجيل حضورك بنجاح</h2>"

    return render_template('register.html')

# --- قائمة الحضور ---
@app.route('/list')
def attendees_list():
    raw_data = r.lrange('attendees', 0, -1)
    attendees_data = [json.loads(item) for item in raw_data]
    return render_template('list.html', attendees=attendees_data)

# --- مسح القائمة ---
@app.route('/clear', methods=['POST'])
def clear_list():
    r.delete('attendees')
    return redirect(url_for('dashboard'))

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
