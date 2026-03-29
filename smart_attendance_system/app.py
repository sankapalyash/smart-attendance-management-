from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import pandas as pd
import cv2
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client

from utils.database_utils import init_db, get_connection
from face_module.recognize_faces import recognize_faces, stop_camera
from face_module.train_model import train_model

app = Flask(__name__)
app.secret_key = "smartattendance"

init_db()

ATTENDANCE_FOLDER = "attendance"


# ---------------- SMS FUNCTION ---------------- #

def send_sms(number, message):

    try:

        account_sid = "YOUR_TWILIO_SID"
        auth_token = "YOUR_TWILIO_TOKEN"

        client = Client(account_sid, auth_token)

        client.messages.create(
            body=message,
            from_="+1234567890",
            to=number
        )

    except Exception as e:
        print("SMS not sent:", e)


# ---------------- EMAIL FUNCTION ---------------- #

def send_email(to_email, student_name, percentage):

    try:

        sender_email = "your_email@gmail.com"
        sender_password = "your_app_password"

        subject = "Attendance Warning"

        body = f"""
Dear {student_name},

Your attendance is {percentage}% which is below the required 75%.

Please attend classes regularly.

Smart Attendance System
"""

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        print("Email sent to", to_email)

    except Exception as e:
        print("Email not sent:", e)


# ---------------- LOGIN ---------------- #

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        role = request.form["role"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        if role == "admin":

            cur.execute(
                "SELECT * FROM admin WHERE username=? AND password=?",
                (username,password)
            )

            admin = cur.fetchone()

            if admin:
                session["role"] = "admin"
                return redirect("/admin")

        elif role == "teacher":

            cur.execute(
                "SELECT * FROM teachers WHERE username=? AND password=?",
                (username,password)
            )

            teacher = cur.fetchone()

            if teacher:
                session["role"] = "teacher"
                return redirect("/teacher")

        elif role == "student":

            cur.execute(
                "SELECT * FROM students WHERE username=? AND password=?",
                (username,password)
            )

            student = cur.fetchone()

            if student:
                session["role"] = "student"
                session["student_name"] = student["name"]
                return redirect("/student")

    return render_template("login.html")


# ---------------- ADMIN ---------------- #

@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_connection()

    teachers = conn.execute(
        "SELECT * FROM teachers"
    ).fetchall()

    conn.close()

    return render_template("admin_dashboard.html", teachers=teachers)


# ---------------- ADD TEACHER ---------------- #

@app.route("/add_teacher", methods=["POST"])
def add_teacher():

    username = request.form["username"]
    password = request.form["password"]

    conn = get_connection()

    conn.execute(
        "INSERT INTO teachers (username,password) VALUES (?,?)",
        (username,password)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------------- DELETE TEACHER ---------------- #

@app.route("/delete_teacher/<int:id>")
def delete_teacher(id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM teachers WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------------- TEACHER DASHBOARD ---------------- #

@app.route("/teacher")
def teacher():

    if session.get("role") != "teacher":
        return redirect("/")

    return render_template("teacher_dashboard.html")


# ---------------- START ATTENDANCE ---------------- #

@app.route("/take_attendance", methods=["POST"])
def take_attendance():

    subject = request.form["subject"]

    recognize_faces(subject)

    return redirect("/teacher")


# ---------------- STOP CAMERA ---------------- #

@app.route("/stop_camera")
def stop_camera_route():

    stop_camera()

    return redirect("/teacher")


# ---------------- VIEW ATTENDANCE ---------------- #

@app.route("/view_attendance")
def view_attendance():

    files = []

    if os.path.exists(ATTENDANCE_FOLDER):
        files = os.listdir(ATTENDANCE_FOLDER)

    return render_template("view_attendance.html", files=files)


# ---------------- DOWNLOAD ATTENDANCE ---------------- #

@app.route("/download_attendance/<filename>")
def download_attendance(filename):

    return send_from_directory(ATTENDANCE_FOLDER, filename)


# ---------------- ATTENDANCE ANALYTICS ---------------- #

@app.route("/attendance_analytics")
def attendance_analytics():

    student_present = {}
    total_classes = 0

    if os.path.exists(ATTENDANCE_FOLDER):

        for file in os.listdir(ATTENDANCE_FOLDER):

            if file.endswith(".xlsx"):

                path = os.path.join(ATTENDANCE_FOLDER,file)

                df = pd.read_excel(path)

                if "Student Name" not in df.columns:
                    continue

                total_classes += 1

                for name in df["Student Name"]:
                    student_present[name] = student_present.get(name,0) + 1

    students = []
    percentages = []

    for student in student_present:

        present = student_present[student]

        percent = (present/total_classes)*100 if total_classes > 0 else 0

        students.append(student)
        percentages.append(round(percent,2))

    overall = round(sum(percentages)/len(percentages),2) if percentages else 0

    return render_template(
        "attendance_analytics.html",
        students=students,
        percentages=percentages,
        overall=overall
    )


# ---------------- MANAGE STUDENTS ---------------- #

@app.route("/manage_students")
def manage_students():

    conn = get_connection()

    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    conn.close()

    return render_template("manage_students.html", students=students)


# ---------------- ADD STUDENT ---------------- #

@app.route("/add_student", methods=["POST"])
def add_student():

    roll_no = request.form.get("roll_no")
    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")
    mobile = request.form.get("mobile","")
    email = request.form.get("email","")

    conn = get_connection()

    conn.execute(
        "INSERT INTO students (roll_no,name,username,password,mobile,email) VALUES (?,?,?,?,?,?)",
        (roll_no,name,username,password,mobile,email)
    )

    conn.commit()
    conn.close()

    dataset_path = os.path.join("dataset", roll_no)

    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    cam = cv2.VideoCapture(0)

    count = 0

    while True:

        ret, frame = cam.read()

        if not ret:
            break

        cv2.imshow("Capturing Student Face", frame)

        img_path = os.path.join(dataset_path,f"{count}.jpg")

        cv2.imwrite(img_path,frame)

        count += 1

        if count >= 30:
            break

        if cv2.waitKey(1) == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

    train_model()

    return redirect("/manage_students")


# ---------------- DELETE STUDENT ---------------- #

@app.route("/delete_student/<int:id>")
def delete_student(id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM students WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/manage_students")


# ---------------- STUDENT DASHBOARD ---------------- #

@app.route("/student")
def student():

    if session.get("role") != "student":
        return redirect("/")

    name = session.get("student_name")

    subjects = []
    percentages = []
    present_list = []
    total_list = []

    if os.path.exists(ATTENDANCE_FOLDER):

        subject_present = {}
        subject_total = {}

        for file in os.listdir(ATTENDANCE_FOLDER):

            if file.endswith(".xlsx"):

                path = os.path.join(ATTENDANCE_FOLDER,file)

                df = pd.read_excel(path)

                if "Student Name" not in df.columns or "Subject" not in df.columns:
                    continue

                for subject in df["Subject"].unique():

                    total = len(df[df["Subject"] == subject])

                    present = len(
                        df[
                            (df["Student Name"] == name) &
                            (df["Subject"] == subject)
                        ]
                    )

                    subject_total[subject] = subject_total.get(subject,0) + total
                    subject_present[subject] = subject_present.get(subject,0) + present

        for subject in subject_total:

            subjects.append(subject)

            present = subject_present[subject]
            total = subject_total[subject]

            present_list.append(present)
            total_list.append(total)

            percent = (present/total)*100 if total > 0 else 0
            percentages.append(round(percent,2))

    return render_template(
        "student_dashboard.html",
        name=name,
        subjects=subjects,
        percentages=percentages,
        present_list=present_list,
        total_list=total_list
    )


# ---------------- DEFAULTER DETECTION ---------------- #

def get_defaulters():

    conn = get_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    defaulters = []

    for student in students:

        name = student["name"]
        roll = student["roll_no"]
        mobile = student["mobile"]
        email = student["email"]

        total = 0
        present = 0

        if os.path.exists(ATTENDANCE_FOLDER):

            for file in os.listdir(ATTENDANCE_FOLDER):

                if file.endswith(".xlsx"):

                    path = os.path.join(ATTENDANCE_FOLDER,file)

                    df = pd.read_excel(path)

                    if "Student Name" not in df.columns:
                        continue

                    total += len(df)
                    present += len(df[df["Student Name"] == name])

        if total > 0:

            percentage = (present/total)*100

            if percentage < 75:

                defaulters.append({
                    "roll":roll,
                    "name":name,
                    "mobile":mobile,
                    "email":email,
                    "percentage":round(percentage,2)
                })

    return defaulters


# ---------------- DEFAULTER PAGE ---------------- #

@app.route("/defaulters")
def defaulters():

    students = get_defaulters()

    for s in students:

        if s["mobile"]:
            send_sms(
                s["mobile"],
                f"Warning! Your attendance is {s['percentage']}%. It is below 75%."
            )

        if s["email"]:
            send_email(
                s["email"],
                s["name"],
                s["percentage"]
            )

    return render_template("defaulters.html", students=students)


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)