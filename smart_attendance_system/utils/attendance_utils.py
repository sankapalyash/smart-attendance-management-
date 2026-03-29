import pandas as pd
import os
from datetime import datetime

ATTENDANCE_FOLDER = "attendance"


def mark_attendance(roll_no, name, subject):

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if not os.path.exists(ATTENDANCE_FOLDER):
        os.makedirs(ATTENDANCE_FOLDER)

    file_name = f"{date}.xlsx"
    file_path = os.path.join(ATTENDANCE_FOLDER, file_name)

    new_record = {
        "Roll No": roll_no,
        "Student Name": name,
        "Subject": subject,
        "Date": date,
        "Time": time
    }

    # If file does not exist create new file
    if not os.path.exists(file_path):

        df = pd.DataFrame([new_record])
        df.to_excel(file_path, index=False)
        return

    # If file exists read it
    df = pd.read_excel(file_path)

    # Prevent duplicate attendance
    if ((df["Roll No"] == roll_no) & (df["Subject"] == subject)).any():
        return

    # Convert new record to DataFrame
    new_df = pd.DataFrame([new_record])

    # Use concat instead of append
    df = pd.concat([df, new_df], ignore_index=True)

    df.to_excel(file_path, index=False)

    print(f"Attendance marked for {name}")