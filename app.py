# -*- coding: utf-8 -*-

import os
import redis
import json
import qrcode
import pytz
from flask import Flask, render_template, request, url_for, redirect
from datetime import datetime

# --- إعدادات أساسية ---

# تعريف المسارات لمجلدات القوالب والملفات الثابتة
template_dir = os.path.abspath('./templates')
static_dir = os.path.abspath('./static')

# تهيئة تطبيق فلاسك مع تحديد المجلدات الصحيحة
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# --- ثوابت التطبيق ---
TIMEZONE = "Asia/Radh"              # المنطقة الزمنية لتسجيل الحضور
REDIS_KEY_ATTENDEES = 'attendees'     # اسم المفتاح في قاعدة بيانات Redis لتخزين الحضور
QR_CODE_FILENAME = 'static/attendance_qr.png' # مسار واسم ملف صورة الـ QR Code

# --- الاتصال بقاعدة بيانات Redis ---
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError("متغير REDIS_URL غير موجود. لا يمكن الاتصال بقاعدة البيانات.")

# إنشاء اتصال مع قاعدة البيانات (تم حذف السطر المكرر)
r = redis.from_url(redis_url, decode_responses=True)

# ------------------------------------
# --- صفحات التطبيق (Routes) ---
# ------------------------------------

@app.route('/')
def teacher_dashboard():
    """
    الصفحة الرئيسية، وهي الآن لوحة تحكم المعلم.
    """
    # تم حذف سطر return الخاطئ والإبقاء على الصحيح فقط
    return render_template('teacher_dashboard.html')


@app.route('/generate_qr')
def generate_qr():
    """
    هذه الصفحة تقوم بإنشاء وعرض رمز الاستجابة السريعة (QR Code).
    """
    registration_url = url_for('register', _external=True)
    qr_img = qrcode.make(registration_url)
    qr_img.save(QR_CODE_FILENAME)
    return render_template('qr_code.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    صفحة تسجيل الحضور التي يراها الطالب بعد مسح الرمز.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')

        riyadh_tz = pytz.timezone(TIMEZONE)
        current_time = datetime.now(riyadh_tz).strftime('%Y-%m-%d %H:%M:%S')

        attendee_data = {
            'name': name,
            'student_id': student_id,
            'time': current_time
        }
        
        r.lpush(REDIS_KEY_ATTENDEES, json.dumps(attendee_data))
        return "<h1>تم تسجيل حضورك بنجاح ✅</h1>"

    return render_template('register.html')


@app.route('/list')
def attendees_list():
    """
    هذه الصفحة تعرض قائمة الطلاب الذين سجلوا حضورهم.
    """
    raw_data = r.lrange(REDIS_KEY_ATTENDEES, 0, -1)
    attendees_data = [json.loads(item) for item in raw_data]
    return render_template('list.html', attendees=attendees_data)


@app.route('/clear', methods=['POST'])
def clear_list():
    """
    دالة لحذف جميع سجلات الحضور من قاعدة البيانات.
    """
    r.delete(REDIS_KEY_ATTENDEES)
    return redirect(url_for('teacher_dashboard'))


# --- تشغيل التطبيق ---
if __name__ == '__main__':
    app.run(debug=True)