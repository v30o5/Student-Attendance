import os
import redis
import json
from flask import Flask, render_template, request, url_for, redirect
from datetime import datetime
import qrcode
import pytz

# Define paths for templates and static folders
template_dir = os.path.abspath('./templates')
static_dir = os.path.abspath('./static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Connect to Redis Database
redis_url = os.getenv('REDIS_URL')
r = redis.from_url(redis_url)


@app.route('/')
def teacher_dashboard():
    """Homepage: teacher dashboard"""
    return render_template('dashboard.html')


@app.route('/generate_qr')
def generate_qr():
    """Generate and display QR code"""
    registration_url = url_for('register', _external=True)
    qr_img = qrcode.make(registration_url)

    # Save QR code in the static folder
    qr_path = os.path.join(static_dir, 'attendance_qr.png')
    qr_img.save(qr_path)

    # Render the QR page
    return render_template('qr.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Attendance registration page"""
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']

        # Convert time to Riyadh timezone
        riyadh_tz = pytz.timezone("Asia/Riyadh")
        current_time = datetime.now(riyadh_tz).strftime('%Y-%m-%d %H:%M:%S')

        attendee_data = {
            'name': name,
            'student_id': student_id,
            'time': current_time
        }

        r.lpush('attendees', json.dumps(attendee_data))
        return "<h1>Your attendance has been successfully recorded ✅</h1>"

    return render_template('register.html')


@app.route('/list')
def attendees_list():
    """Display list of attendees"""
    raw_data = r.lrange('attendees', 0, -1)
    attendees_data = [json.loads(item) for item in raw_data]
    return render_template('list.html', attendees=attendees_data)


@app.route('/clear', methods=['POST'])
def clear_list():
    """Delete all attendees"""
    r.delete('attendees')
    return redirect(url_for('teacher_dashboard'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
