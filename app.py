import os
import redis
import json
from flask import Flask, render_template, request, url_for, redirect
from datetime import datetime
import qrcode
import pytz

# Define the paths for static and template folders
template_dir = os.path.abspath('./templates')
static_dir = os.path.abspath('./static')

# Ensure Flask uses the correct folders
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


# --- Connect to Redis Database ---
redis_url = os.getenv('REDIS_URL')
r = redis.from_url(redis_url)
# ------------------------------------


@app.route('/')
def teacher_dashboard():
    """This is the new homepage, which is now the teacher's dashboard."""
    return render_template('teacher.html')

@app.route('/generate_qr')
def generate_qr():
    """This page generates and displays the QR code."""
    # Create the full URL for the registration page that the QR code will point to.
    registration_url = url_for('register', _external=True)
    
    # Create the QR code image and save it in the 'static' folder.
    qr_img = qrcode.make(registration_url)
    qr_img.save('static/attendance_qr.png')
    
    # Show the page that displays the QR code.
    return render_template('qr_code.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """This is the attendance registration page that students will see after scanning the code."""
    if request.method == 'POST':
        # Get data from the form.
        name = request.form['name']
        student_id = request.form['student_id']
        
        # --- Convert time to Riyadh timezone ---
        riyadh_tz = pytz.timezone("Asia/Riyadh") 
        current_time = datetime.now(riyadh_tz).strftime('%Y-%m-%d %H:%M:%S')

        # Prepare the data to be saved.
        attendee_data = {
            'name': name,
            'student_id': student_id,
            'time': current_time
        }
        
        # Save the data to the Redis database.
        r.lpush('attendees', json.dumps(attendee_data))
        
        # Show a success message.
        return "<h1>Your attendance has been successfully recorded ✅</h1>"
        
    # If a user just visits the page, show them the registration form.
    return render_template('register.html')

@app.route('/list')
def attendees_list():
    """This page displays the list of attendees."""
    raw_data = r.lrange('attendees', 0, -1)
    attendees_data = [json.loads(item) for item in raw_data]
    return render_template('list.html', attendees=attendees_data)

@app.route('/clear', methods=['POST'])
def clear_list():
    """Function to delete all attendees from the database."""
    r.delete('attendees')
    return redirect(url_for('teacher_dashboard'))