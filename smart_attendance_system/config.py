import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_PATH = os.path.join(BASE_DIR, "database", "database.db")

DATASET_PATH = os.path.join(BASE_DIR, "dataset")

MODEL_PATH = os.path.join(BASE_DIR, "models", "face_encodings.pkl")

ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance", "attendance.xlsx")