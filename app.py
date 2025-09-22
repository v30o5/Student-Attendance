import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime
import pytz

# --- 1. App and Database Configuration ---
app = Flask(__name__)

# This line is crucial. It tells your app how to connect to the database.
# The URL comes from an Environment Variable on Render.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database extension
db = SQLAlchemy(app)


# --- 2. Database Model ---
# This Python class defines the structure of the 'attendance' table in your database.
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)
    # Store timestamps in UTC for consistency
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# --- 3. App Routes ---

# Main Dashboard Route
@app.route('/')
def dashboard():
    # Query the database to get stats (instead of reading a CSV)
    total_students = db.session.query(func.count(Attendance.student_id.distinct())).scalar()
    
    # Get today's attendance count based on Riyadh time
    riyadh_tz = pytz.timezone("Asia/Riyadh")
    today_start_utc = datetime.now(riyadh_tz).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.utc)
    attendance_today = Attendance.query.filter(Attendance.timestamp >= today_start_utc).count()
    
    # Get the 5 most recent attendance records
    recent_attendance = Attendance.query.order_by(Attendance.timestamp.desc()).limit(5).all()

    return render_template('dashboard.html', 
                           total_students=total_students,
                           attendance_today=attendance_today,
                           recent_attendance=recent_attendance)

# API Route for Chart Data (to be used by JavaScript)
@app.route('/api/monthly_attendance')
def monthly_attendance_data():
    # Query to count attendance grouped by month
    result = db.session.query(
        func.strftime('%Y-%m', Attendance.timestamp).label('month'),
        func.count(Attendance.id).label('count')
    ).group_by('month').order_by('month').all()
    
    # Format the data into a JSON object for Chart.js
    chart_data = {
        "labels": [row.month for row in result],
        "data": [row.count for row in result]
    }
    return jsonify(chart_data)

# Student Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        
        # Create a new attendance record object
        new_record = Attendance(
            name=name, 
            student_id=student_id,
            # Save the timestamp in UTC
            timestamp=datetime.now(pytz.utc)
        )
        
        # Add the new record to the database and save the changes
        db.session.add(new_record)
        db.session.commit()
        
        return "<h2 style='color:green;text-align:center;margin-top:50px;'>✅ تم تسجيل حضورك بنجاح</h2>"
        
    return render_template('register.html')

# This is a helper command to create the database tables the first time the app runs.
with app.app_context():
    db.create_all()