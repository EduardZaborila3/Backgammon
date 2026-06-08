import os
import json
import uuid

PROFILE_FILE = "profile.json"

def get_app_data_dir():
    """Finds the AppData directory and creates a folder for the game"""
    base_dir = os.getenv('APPDATA')
    app_dir = os.path.join(base_dir, 'BackgammonGame')

    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    return app_dir

def get_token_path():
    """Returns the path to the token file"""
    return os.path.join(get_app_data_dir(), "profile.json")

def get_or_create_device_token():
    """Checks if the user already has a profile saved on the device. If it doesn't, the app generates a unique token and saves it."""
    file_path = os.path.join(get_app_data_dir(), "profile.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get('device_token')
        except Exception as e:
            print(f"Error while reading token: {e}")

    new_token = str(uuid.uuid4())
    with open(file_path, "w") as f:
        json.dump({"device_token": new_token}, f)

    return new_token

def is_new_player():
    """Checks the existance of the file in the path"""
    if os.path.exists(PROFILE_FILE):
        return False
    return True

def delete_local_token():
    """Deletes the expired/invalid local token file"""
    file_path = get_token_path()
    if os.path.exists(file_path):
        os.remove(file_path)