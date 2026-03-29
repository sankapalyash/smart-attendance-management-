import cv2
import os
from config import DATASET_PATH


def capture_images(student_name):

    student_path = os.path.join(DATASET_PATH, student_name)

    if not os.path.exists(student_path):
        os.makedirs(student_path)

    cam = cv2.VideoCapture(0)

    count = 0

    while True:

        ret, frame = cam.read()

        cv2.imshow("Capture Images", frame)

        file_path = os.path.join(student_path, f"{count}.jpg")

        cv2.imwrite(file_path, frame)

        count += 1

        if count >= 30:
            break

        if cv2.waitKey(1) == 27:
            break

    cam.release()
    cv2.destroyAllWindows()