import os
import redis
import json
from flask import Flask, render_template, request, url_for
from datetime import datetime
import qrcode

app = Flask(__name__)

# --- الاتصال بقاعدة بيانات Redis ---
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
r = redis.from_url(redis_url)
# ------------------------------------

# --- التأكد من وجود مجلد للصور الثابتة ---
if not os.path.exists('static'):
    os.makedirs('static')
# ------------------------------------

@app.route('/')
def teacher_dashboard():
    """هذه هي الصفحة الرئيسية الجديدة، وهي الآن لوحة تحكم المدرس."""
    return render_template('teacher.html')

@app.route('/generate_qr')
def generate_qr():
    """هذه الصفحة تقوم بإنشاء وعرض الباركود."""
    # إنشاء الرابط الكامل لصفحة التسجيل التي سيشير إليها الباركود.
    registration_url = url_for('register', _external=True)
    
    # إنشاء صورة الباركود وحفظها في مجلد 'static'.
    qr_img = qrcode.make(registration_url)
    qr_img.save('static/attendance_qr.png')
    
    # عرض الصفحة التي تعرض الباركود.
    return render_template('qr_code.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """هذه هي صفحة تسجيل الحضور التي سيراها الطلاب بعد مسح الكود."""
    if request.method == 'POST':
        # أخذ البيانات من النموذج.
        name = request.form['name']
        student_id = request.form['student_id']
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # تجهيز البيانات ليتم حفظها.
        attendee_data = {
            'name': name,
            'student_id': student_id,
            'time': current_time
        }
        
        # حفظ البيانات في قاعدة بيانات Redis.
        r.lpush('attendees', json.dumps(attendee_data))
        
        # إظهار رسالة نجاح.
        return "<h1>تم تسجيل حضورك بنجاح ✅</h1>"
        
    # إذا قام المستخدم بزيارة الصفحة فقط، قم بعرض نموذج التسجيل.
    return render_template('register.html')

@app.route('/list')
def attendees_list():
    """هذه الصفحة تعرض قائمة الحضور (نفس التصميم السابق)."""
    raw_data = r.lrange('attendees', 0, -1)
    attendees_data = [json.loads(item) for item in raw_data]
    # السطر الأخير المضاف لإرسال البيانات إلى واجهة العرض
    return render_template('list.html', attendees=attendees_data)