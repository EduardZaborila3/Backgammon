import os
import json
import uuid

PROFILE_FILE = "profile.json"

def get_or_create_device_token():
    """Checks if the user already has a profile saved on the device. If it doesn't, the app generates a unique token and saves it."""
    if not is_new_player():
        with open(PROFILE_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("device_token")
            except json.JSONDecodeError:
                pass

    new_token = str(uuid.uuid4())
    with open(PROFILE_FILE, "w") as f:
        try:
            json.dump({"device_token": new_token}, f)
        except json.JSONDecodeError as e:
            print(f"Could not create profile: {e}")

    return new_token

def is_new_player():
    if os.path.exists(PROFILE_FILE):
        return False
    return True