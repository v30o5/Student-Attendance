from flask import Flask, render_template, request, send_file
import openpyxl
import os
from datetime import datetime

app = Flask(__name__)
FILE_NAME = "attendance.xlsx"
# أضف هذا الكود لتعريف الصفحة الرئيسية
@app.route('/')
def home():
    return '<h1>Welcome to the Attendance Project</h1><p>The service is running.</p>'

def init_excel():
    if not os.path.exists(FILE_NAME):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Attendance"
        ws.append(["Name", "Student ID", "Date", "Time"])
        wb.save(FILE_NAME)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        student_id = request.form.get("student_id")
        if name and student_id:
            wb = openpyxl.load_workbook(FILE_NAME)
            ws = wb.active
            ws.append([name, student_id, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")])
            wb.save(FILE_NAME)
            return "تم تسجيل حضورك بنجاح ✅"
    return '''
        <h2>تسجيل الحضور</h2>
        <form method="post">
            <label>الاسم:</label><br>
            <input type="text" name="name" required><br><br>
            <label>الرقم الجامعي:</label><br>
            <input type="text" name="student_id" required><br><br>
            <button type="submit">تسجيل</button>
        </form>
        <br>
        <a href="/download">📥 تحميل ملف الحضور</a>
    '''

@app.route("/download")
def download():
    return send_file(FILE_NAME, as_attachment=True)

if __name__ == "__main__":
    init_excel()
    app.run(debug=True)
