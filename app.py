from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import qrcode
from datetime import datetime
import os
import matplotlib.pyplot as plt

app = Flask(__name__)

DATA_FILE = 'data/attendance.csv'

# تأكد من وجود ملف البيانات
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=['name', 'student_id', 'date', 'time'])
    df.to_csv(DATA_FILE, index=False)

# إنشاء QR Code تلقائياً
def generate_qr():
    qr_data = "https://your-university-attendance-link.com"
    qr_img = qrcode.make(qr_data)
    qr_img.save('static/attendance_qr.png')

generate_qr()

# الصفحة الرئيسية - لوحة التحكم
@app.route('/')
def dashboard():
    df = pd.read_csv(DATA_FILE)
    total_students = df['student_id'].nunique()
    today = datetime.today().strftime('%Y-%m-%d')
    attendance_today = df[df['date'] == today].shape[0]
    recent_attendance = df.sort_values(by='date', ascending=False).head(5).to_dict(orient='records')
    
    # رسم بياني للحضور الشهري
    df['date_only'] = pd.to_datetime(df['date'])
    monthly_counts = df.groupby(df['date_only'].dt.to_period('M')).size()
    monthly_counts.plot(kind='bar', color='#004080')
    plt.title('عدد الحضور الشهري')
    plt.tight_layout()
    plt.savefig('static/monthly_attendance.png')
    plt.close()
    
    return render_template('dashboard.html', total_students=total_students,
                           attendance_today=attendance_today,
                           recent_attendance=recent_attendance)

# صفحة تسجيل الطلاب
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        date_now = datetime.today().strftime('%Y-%m-%d')
        time_now = datetime.today().strftime('%H:%M:%S')
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, pd.DataFrame([{'name': name, 'student_id': student_id, 'date': date_now, 'time': time_now}])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

# صفحة عرض QR Code
@app.route('/qr')
def qr():
    return render_template('qr.html')

if __name__ == '__main__':
    app.run(debug=True)


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
