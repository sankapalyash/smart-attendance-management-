import face_recognition
import os
import pickle

DATASET_PATH = "dataset"
MODEL_PATH = "models/face_encodings.pkl"


def train_model():

    print("Starting model training...")

    encodings = []
    names = []

    if not os.path.exists(DATASET_PATH):
        print("Dataset folder not found.")
        return

    # loop through each student folder
    for student_name in os.listdir(DATASET_PATH):

        student_folder = os.path.join(DATASET_PATH, student_name)

        if not os.path.isdir(student_folder):
            continue

        print(f"Processing student: {student_name}")

        # loop through images of that student
        for image_name in os.listdir(student_folder):

            image_path = os.path.join(student_folder, image_name)

            # skip non-image files
            if not image_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            try:

                image = face_recognition.load_image_file(image_path)

                face_encodings = face_recognition.face_encodings(image)

                if len(face_encodings) > 0:

                    encodings.append(face_encodings[0])
                    names.append(student_name)

                else:
                    print(f"No face detected in {image_path}")

            except Exception as e:
                print(f"Error processing {image_path}: {e}")

    data = {
        "encodings": encodings,
        "names": names
    }

    # create models folder if not exists
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(data, f)

    print("Model trained successfully.")
    print(f"Total faces encoded: {len(encodings)}")


# allow running file directly
if __name__ == "__main__":
    train_model()