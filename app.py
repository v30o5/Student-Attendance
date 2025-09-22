from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import qrcode
from datetime import datetime
import os
import matplotlib.pyplot as plt
import barcode
from barcode.writer import ImageWriter

app = Flask(__name__)

DATA_FILE = 'data/attendance.csv'

# تأكد من وجود ملف البيانات
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=['name', 'student_id', 'date', 'time'])
    df.to_csv(DATA_FILE, index=False)

# إنشاء QR Code وBarcode تلقائياً
def generate_codes():
    qr_data = "https://your-university-attendance-link.com"
    qr_img = qrcode.make(qr_data)
    qr_img.save('static/attendance_qr.png')

    code128 = barcode.get('code128', '1234567890', writer=ImageWriter())
    code128.save('static/attendance_barcode')

generate_codes()

# لوحة التحكم
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

# تسجيل الطلاب
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

# صفحة QR / Barcode
@app.route('/qr')
def qr():
    return render_template('qr.html')

if __name__ == '__main__':
    app.run(debug=True)
