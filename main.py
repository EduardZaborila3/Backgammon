import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import threading
import queue
import socketio

from auth import get_or_create_device_token
from ui import BackgammonUI
from constants import *
# import auth

SERVER_URL = "http://64.225.109.232:5555"

message_queue = queue.Queue()

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to the server!")


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
def on_receive_play_again_request():
    message_queue.put(("receive_play_again_request", None))

@sio.on('play_again_declined')
def on_play_again_declined():
    message_queue.put(("play_again_declined", None))

def network_thread(server_address):
    try:
        if not server_address.startswith("http"):
            server_address = "http://" + server_address

        # device_token = get_or_create_device_token()
        # print(f"Trying to connect to the server at {server_address}...")
        # sio.connect(server_address, auth={"device_token": device_token})
        sio.connect(server_address)
        sio.wait()
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
                messagebox.showerror("Connection Error", f"Failed to connect to the server. \n Reason: {data}")
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
    root.title("Backgammon - Menu")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    root.resizable(False, False)

    app = BackgammonUI(root)

    app.sio = sio

    t = threading.Thread(target=network_thread, args=(address,), daemon=True)
    t.start()

    process_messages(root, app)

    root.mainloop()