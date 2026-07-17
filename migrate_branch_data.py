import requests
import config

print("Starting database migration...")

# 1. Fetch current root data
exam_structure = requests.get(f"{config.FIREBASE_URL}/exam_structure.json").json()
students = requests.get(f"{config.FIREBASE_URL}/students.json").json()

# 2. Move data to IT branch
if exam_structure and "IT" not in exam_structure:
    print("Moving Exam Structures to IT branch...")
    requests.put(f"{config.FIREBASE_URL}/exam_structure/IT.json", json=exam_structure)

if students and "IT" not in students:
    print("Moving Student Database to IT branch...")
    requests.put(f"{config.FIREBASE_URL}/students/IT.json", json=students)

print("Migration Complete! Your legacy data is now safely under the IT section.")
# Note: You can manually delete the old duplicate semester folders at the root 
# of your Firebase console once you verify everything is working.