from flask import Flask, request, send_file
import openpyxl
import os
from datetime import datetime

app = Flask(__name__)
FILE_NAME = "attendance.xlsx"

# This function creates the Excel file with headers if it doesn't exist.
def init_excel():
    if not os.path.exists(FILE_NAME):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Attendance"
        ws.append(["Name", "Student ID", "Date", "Time"])
        wb.save(FILE_NAME)

@app.route('/', methods=['GET', 'POST'])
def index():
    # This part runs when a user submits the form (POST request)
    if request.method == 'POST':
        name = request.form.get("name")
        student_id = request.form.get("student_id")

        if name and student_id:
            # Open the existing Excel file and add the new data
            wb = openpyxl.load_workbook(FILE_NAME)
            ws = wb.active
            ws.append([name, student_id, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")])
            wb.save(FILE_NAME)
            return "تم تسجيل حضورك بنجاح ✅"

    # This part runs when a user visits the page for the first time (GET request)
    # It displays the HTML form.
    return '''
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>تسجيل الحضور</title>
        </head>
        <body>
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
        </body>
        </html>
    '''

@app.route("/download")
def download():
    return send_file(FILE_NAME, as_attachment=True)

# Create the Excel file when the application starts
init_excel()

# This part is for running the app locally on your computer
if __name__ == "__main__":
    app.run(debug=True)
