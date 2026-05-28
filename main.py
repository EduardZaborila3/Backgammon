import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import threading
import queue
import socketio

from auth import get_or_create_device_token
from ui import BackgammonUI
from constants import *
import auth
import sys
import uuid

SERVER_URL = "http://64.225.109.232:5555"

message_queue = queue.Queue()

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to the server!")

@sio.event
def connect_error(data):
    message_queue.put(("connection error", data))

@sio.event
def disconnect():
    print("Disconnected from the server.")


@sio.on('assign_player')
def on_assign_player(data):
    message_queue.put(("assign", data))

@sio.on('ai_move_response')
def on_ai_move_response(data):
    message_queue.put(("ai_move", data))


@sio.on('game_state_update')
def on_state_update(data):
    message_queue.put(("update", data))


@sio.on('opponent_disconnected')
def on_opponent_disconnect():
    message_queue.put(("disconnect", None))

@sio.on('receive_double_offer')
def on_receive_double_offer(data):
    message_queue.put(("receive_double_offer", data))

@sio.on('receive_play_again_request')
def on_receive_play_again_request(data):
    message_queue.put(("receive_play_again_request", None))

@sio.on('play_again_declined')
def on_play_again_declined(data):
    message_queue.put(("play_again_declined", None))

@sio.on('profile_data_update')
def on_profile_data_update(data):
    message_queue.put(("profile_update", data))


def start_server_connection(auth_type):
    """Function called by the UI after the user chooses how to connect"""
    if auth_type == "guest":
        token = get_or_create_device_token()
        t = threading.Thread(target=network_thread, args=(SERVER_URL, token), daemon=True)
        t.start()

    elif auth_type == "account":
        # email / passsword logic
        pass


def network_thread(server_address, token):
    """Connects to server with token"""
    try:
        if not server_address.startswith("http"):
            server_address = "http://" + server_address

        print(f"Trying to connect to the server with token: {token}")
        sio.connect(server_address, auth={"device_token": token})
        sio.wait()
    except socketio.exceptions.ConnectionError:
        pass
    except Exception as e:
        message_queue.put(("connection error", e))


def process_messages(root, app):
    try:
        while True:
            msg_type, data = message_queue.get_nowait()

            if msg_type == "assign":
                app.my_player_id = data['player_id']
                color = "White (0)" if app.my_player_id == 0 else "Black (1)"
                root.title(f"BACKGAMMON - PLAYER: {color}")

            elif msg_type == "update":
                app.sync_state_from_server(data)

            elif msg_type == "disconnect":
                app.game.game_over = True
                app.game.winner = app.my_player_id
                app.draw_game_over(winner=app.my_player_id, win_conditions="leave")

            elif msg_type == "connection error":
                error_msg = str(data)

                if "Account already active" in error_msg:
                    messagebox.showerror("Acces Denied", "This account is already active in another window or device. \nThe game will close.")
                    root.destroy()
                    exit()
                else:
                    messagebox.showerror("Connection Error", f"Failed to connect to the server. \nReason: {error_msg}")
                    app.is_multiplayer = False
                    app.menu = True
                    app.draw_menu()

            elif msg_type == "game_state_update":
                app.sync_state_from_server(data)

            elif msg_type == "ai_move":
                app.apply_ai_move_from_server(data)

            elif msg_type == "receive_double_offer":
                app.handle_double_offer(data)

            elif msg_type == "receive_play_again_request":
                app.handle_play_again_request()

            elif msg_type == "play_again_declined":
                app.handle_play_again_declined()

            elif msg_type == "profile_update":
                app.username = data['username']
                app.games_played = data['games_played']
                app.games_won = data['games_won']

                if app.profile_screen:
                    app.draw_profile_menu()

    except queue.Empty:
        pass

    root.after(50, lambda: process_messages(root, app))

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    address = SERVER_URL
    if not address:
        root.destroy()
        exit()

    root.deiconify()
    root.title("Backgammon")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    root.resizable(False, False)

    app = BackgammonUI(root, auth_callback=start_server_connection)
    app.sio = sio

    process_messages(root, app)

    root.mainloop()