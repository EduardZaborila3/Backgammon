import os
import json

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

def get_saved_token():
    """Reads and reuturns the Supabase token if exsits, otherwise returns None"""
    file_path = get_token_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get('supabase_token')
        except Exception as e:
            print(f"Error while reading token: {e}")

    return None

def save_token(token):
    """Saves the Supabase JWT token to the local file after a successful login/register"""
    file_path = get_token_path()
    try:
        with open(file_path, "w") as f:
            json.dump({"supabase_token": token}, f)
    except Exception as e:
        print(f"Error while saving token: {e}")

def delete_local_token():
    """Deletes the expired/invalid local token file"""
    file_path = get_token_path()
    if os.path.exists(file_path):
        os.remove(file_path)