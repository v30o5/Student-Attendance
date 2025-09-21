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
TIMEZONE = "Asia/Riyadh"              # المنطقة الزمنية لتسجيل الحضور
REDIS_KEY_ATTENDEES = 'attendees'     # اسم المفتاح في قاعدة بيانات Redis لتخزين الحضور
QR_CODE_FILENAME = 'static/attendance_qr.png' # مسار واسم ملف صورة الـ QR Code

# --- الاتصال بقاعدة بيانات Redis ---
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError("متغير REDIS_URL غير موجود. لا يمكن الاتصال بقاعدة البيانات.")

# إنشاء اتصال مع قاعدة البيانات
r = redis.from_url(redis_url, decode_responses=True) # decode_responses=True لتحويل البيانات تلقائياً من bytes إلى string

# ------------------------------------
# --- صفحات التطبيق (Routes) ---
# ------------------------------------

@app.route('/')
def teacher_dashboard():
    """
    الصفحة الرئيسية، وهي الآن لوحة تحكم المعلم.
    """
    return render_template('teacher.html')


@app.route('/generate_qr')
def generate_qr():
    """
    هذه الصفحة تقوم بإنشاء وعرض رمز الاستجابة السريعة (QR Code).
    """
    # إنشاء الرابط الكامل لصفحة تسجيل الحضور الذي سيشير إليه الـ QR Code
    registration_url = url_for('register', _external=True)

    # إنشاء صورة الـ QR Code وحفظها في مجلد 'static'
    qr_img = qrcode.make(registration_url)
    qr_img.save(QR_CODE_FILENAME)

    # عرض الصفحة التي تحتوي على صورة الـ QR Code
    return render_template('qr_code.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    صفحة تسجيل الحضور التي يراها الطالب بعد مسح الرمز.
    تتعامل مع عرض النموذج (GET) واستقبال البيانات (POST).
    """
    # في حال قام الطالب بإرسال بياناته عبر النموذج
    if request.method == 'POST':
        # الحصول على البيانات من النموذج
        name = request.form.get('name')
        student_id = request.form.get('student_id')

        # الحصول على الوقت الحالي بتوقيت الرياض
        riyadh_tz = pytz.timezone(TIMEZONE)
        current_time = datetime.now(riyadh_tz).strftime('%Y-%m-%d %H:%M:%S')

        # تجهيز بيانات الطالب للحفظ
        attendee_data = {
            'name': name,
            'student_id': student_id,
            'time': current_time
        }

        # حفظ البيانات في قاعدة Redis عن طريق إضافتها إلى بداية القائمة
        # استخدام json.dumps لتحويل القاموس إلى نص من نوع JSON
        r.lpush(REDIS_KEY_ATTENDEES, json.dumps(attendee_data))

        # عرض رسالة نجاح للطالب
        return "<h1>تم تسجيل حضورك بنجاح ✅</h1>"

    # في حال قام المستخدم بزيارة الصفحة فقط (GET)، يتم عرض نموذج التسجيل
    return render_template('register.html')


@app.route('/list')
def attendees_list():
    """
    هذه الصفحة تعرض قائمة الطلاب الذين سجلوا حضورهم.
    """
    # جلب جميع بيانات الحضور من قاعدة Redis (من العنصر 0 إلى الأخير)
    raw_data = r.lrange(REDIS_KEY_ATTENDEES, 0, -1)
    
    # تحويل كل عنصر من نص JSON إلى قاموس Python
    attendees_data = [json.loads(item) for item in raw_data]

    # عرض صفحة القائمة مع تمرير بيانات الحضور إليها
    return render_template('list.html', attendees=attendees_data)


@app.route('/clear', methods=['POST'])
def clear_list():
    """
    دالة لحذف جميع سجلات الحضور من قاعدة البيانات.
    يتم الوصول إليها عبر طلب POST فقط لزيادة الأمان.
    """
    # حذف المفتاح 'attendees' وكل ما فيه من بيانات
    r.delete(REDIS_KEY_ATTENDEES)
    
    # إعادة توجيه المستخدم إلى لوحة تحكم المعلم
    return redirect(url_for('teacher_dashboard'))


# --- تشغيل التطبيق ---
if __name__ == '__main__':
    # تشغيل التطبيق في وضع التطوير (Debug Mode)
    # هذا الوضع يعرض الأخطاء التفصيلية في المتصفح ويعيد تشغيل الخادم تلقائياً عند كل تغيير
    app.run(debug=True)