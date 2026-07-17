import requests
import config

# The hardcoded users from your original code
legacy_faculties = {
    "prof_sonali": "sonali_it",
    "prof_twinkle": "twinkle_it",
    "prof_simran": "simran_it",
    "prof_swarang": "swarang_it"
}

print("Migrating users to Firebase...")

# 1. Migrate HOD
print("Adding HOD (hod_it)...")
requests.put(f"{config.FIREBASE_URL}/users/hod/hod_it.json", json={
    "password": "hod_it",
    "branch": "IT"
})

# 2. Migrate Faculties
for username, password in legacy_faculties.items():
    print(f"Adding Faculty ({username})...")
    requests.put(f"{config.FIREBASE_URL}/users/faculty/{username}.json", json={
        "password": password,
        "branch": "IT",
        "status": "approved"  # Pre-approved since they are legacy users
    })

print("Migration Complete! You can now remove the hardcoded USERS dictionary from app.py.")