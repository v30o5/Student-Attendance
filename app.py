import os
import redis
import json
from flask import Flask, render_template, request, url_for
from datetime import datetime
import qrcode

app = Flask(__name__)

# --- Connect to Redis Database ---
redis_url = os.getenv('REDIS_URL')
r = redis.from_url(redis_url)
# ------------------------------------

# --- Ensure the static folder exists ---
if not os.path.exists('static'):
    os.makedirs('static')
# ------------------------------------

@app.route('/')
def teacher_dashboard():
    return render_template('teacher.html')

@app.route('/generate_qr')
def generate_qr():
    registration_url = url_for('register', _external=True)
    qr_img = qrcode.make(registration_url)
    qr_img.save('static/attendance_qr.png')
    return render_template('qr_code.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        attendee_data = {
            'name': name,
            'student_id': student_id,
            'time': current_time
        }

        # --- DEBUG PRINT STATEMENT ---
        print(f"DEBUG: Received data: {attendee_data}", flush=True)
        # -----------------------------

        r.lpush('attendees', json.dumps(attendee_data))
        return "<h1>Your attendance has been successfully recorded ✅</h1>"

    return render_template('register.html')

@app.route('/list')
def attendees_list():
    raw_data = r.lrange('attendees', 0, -1)

    # --- DEBUG PRINT STATEMENT ---
    print(f"DEBUG: Data read from Redis: {raw_data}", flush=True)
    # -----------------------------

    attendees_data = [json.loads(item) for item in raw_data]
    return render_template('list.html', attendees=attendees_data)