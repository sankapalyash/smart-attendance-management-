import cv2
import pickle
import face_recognition
import os

from utils.attendance_utils import mark_attendance
from utils.database_utils import get_connection

MODEL_PATH = "models/face_encodings.pkl"

camera_running = True


def recognize_faces(subject):

    global camera_running
    camera_running = True

    if not os.path.exists(MODEL_PATH):
        print("Model not trained.")
        return

    with open(MODEL_PATH, "rb") as f:
        data = pickle.load(f)

    known_encodings = data["encodings"]
    known_rolls = data["names"]

    video = cv2.VideoCapture(0)

    marked_students = set()

    while camera_running:

        ret, frame = video.read()

        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, boxes)

        for encoding, box in zip(encodings, boxes):

            matches = face_recognition.compare_faces(
                known_encodings,
                encoding
            )

            name = "Unknown"
            roll_no = None

            if True in matches:

                match_index = matches.index(True)

                roll_no = known_rolls[match_index]

                # Get student name from database
                conn = get_connection()

                student = conn.execute(
                    "SELECT name FROM students WHERE roll_no=?",
                    (roll_no,)
                ).fetchone()

                conn.close()

                if student:
                    name = student["name"]

                if roll_no not in marked_students:

                    mark_attendance(
                        roll_no,
                        name,
                        subject
                    )

                    marked_students.add(roll_no)

                label = f"{roll_no} - {name}"

            else:
                label = "Unknown"

            top, right, bottom, left = box

            cv2.rectangle(
                frame,
                (left, top),
                (right, bottom),
                (0,255,0),
                2
            )

            cv2.putText(
                frame,
                label,
                (left, top-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0,255,0),
                2
            )

        cv2.imshow("Smart Attendance System", frame)

        if cv2.waitKey(1) == 27:
            break

    video.release()
    cv2.destroyAllWindows()


def stop_camera():

    global camera_running
    camera_running = False