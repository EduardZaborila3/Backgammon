import os
import psycopg2
import socketio
from aiohttp import web
from dotenv import load_dotenv
from sympy.codegen.fnodes import use_rename

from logic import BackgammonLogic
import uuid
from ai import TDGammonNetwork, calculate_best_move
import torch
import asyncio

load_dotenv()
connected_users = {}

def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Critical error: Cant connect to the database. Details: {e}")
        return None

conn = get_db_connection()
if conn:
    print("Success: Connected to Supabase PostgreSQL!")

sio = socketio.AsyncServer(cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

waiting_player = None
games = {}
players = {}

ai_model_medium = TDGammonNetwork()
try:
    ai_model_medium.load_state_dict(torch.load("models/ai_20000.pth", weights_only=True))
    ai_model_medium.eval()
    print("Medium AI Model (20k) loaded successfully!")
except Exception as e:
    print(f"Error loading medium AI model: {e}")
    ai_model_medium = None

ai_model_hard = TDGammonNetwork()
try:
    ai_model_hard.load_state_dict(torch.load("models/ai_100000.pth", weights_only=True))
    ai_model_hard.eval()
    print("Hard AI Model (100k) loaded successfully!")
except Exception as e:
    print(f"Error loading hard AI model: {e}")
    ai_model_hard = None

def get_game_state(game):
    return {
        'board': game.board,
        'bar': game.bar,
        'off': game.off,
        'turn': game.turn,
        'dice': game.dice,
        'match_score': game.match_score,
        'game_over': game.game_over,
        'winner': game.winner,
        'cube_value': game.cube_value,
        'cube_owner': game.cube_owner,
        'history': game.history,
        'has_rolled': game.has_rolled
    }

def db_authenticate_user(token):
    """Searches the token in the database. If the token exists, then the user is free to play the game.
     If the token can't be found in the database, this means a new user has to be created."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username FROM users WHERE device_token = CAST(%s AS uuid)", (token,))
            row = cursor.fetchone()

            if row:
                if row[1]:
                    username = row[1]
                else:
                    username = f"Guest_{row[0]}"
                    return {'id': row[0], 'username': username}
                print(f"User {username} is online!")
            else:
                cursor.execute("INSERT INTO users (device_token) VALUES (CAST %s AS uuid) RETURNING id", (token,))
                new_id = cursor.fetchone()[0]
                new_username = cursor.fetchone()[1]
                print(f"Created new user in the database: ID {new_id}")
                return {'id': new_id, 'username': new_username}
    except Exception as err:
        print(f"Database authentication error: {err}")
        return None


@sio.event
async def connect(sid, environ, auth):
    if not auth or 'device_token' not in auth:
        print(f"[{sid}] Connection rejected: No device token provided")
        raise socketio.exceptions.ConnectionRefusedError('Missing token')
    token = auth['device_token']
    print(f"[{sid}] connected to the server with token: {token}")

    user_data = await asyncio.to_thread(db_authenticate_user, token)

    if not user_data:
        raise socketio.exceptions.ConnectionRefusedError('Database error')

    connected_users[sid] = {'token': token, 'username': f"Guest_{sid[:4]}"}
    print(f"[{sid}] Authenticated successfully!")

@sio.event
async def disconnect(sid):
    global waiting_player
    print(f"[{sid}] disconnected from the server.")

    if waiting_player == sid:
        waiting_player = None

    if sid in players:
        room_id = players[sid]['room']
        await sio.emit('Opponent disconnected', room=room_id, skip_sid = sid)
        if room_id in games:
            del games[room_id]
        del players[sid]

@sio.event
async def join_matchmaking(sid):
    global waiting_player

    if waiting_player is None:
        waiting_player = sid
        print(f"[{sid}] is waiting for an opponent...")
        await sio.emit('Waiting for opponent...', to=sid)
    else:
        if waiting_player == sid:
            return

        room_id = str(uuid.uuid4())
        p1_sid = waiting_player
        p2_sid = sid
        waiting_player = None

        await sio.enter_room(p1_sid, room_id)
        await sio.enter_room(p2_sid, room_id)

        games[room_id] = BackgammonLogic()
        players[p1_sid] = {'room': room_id, 'color': 0}
        players[p2_sid] = {'room': room_id, 'color': 1}
        print(f"Game started between [{p1_sid}] and [{p2_sid}] in room {room_id}.")

        await sio.emit('assign_player', {'player_id': 0}, to=p1_sid)
        await sio.emit('assign_player', {'player_id': 1}, to=p2_sid)

        state = get_game_state(games[room_id])
        await sio.emit('game_state_update', state, room=room_id)

@sio.event
async def roll_dice(sid):
    if sid not in players: return
    p_info = players[sid]
    game = games[p_info['room']]

    if game.turn == p_info.get('color'):
        game.roll_dice()
        await sio.emit('game_state_update', get_game_state(game), room=p_info['room'])

@sio.event
async def skip_turn(sid, data):
    print(f"Server received a 'skip_turn' request from [{sid}]")
    if sid not in players:
        return
    p_info = players[sid]
    game = games[p_info['room']]

    if game.turn == p_info.get('color'):
        if game.dice and not game.any_valid_moves():
            print(f"Player {p_info.get('color')} has no valid moves. Switching turn...")
            game.dice = []
            game.switch_turn()
            await sio.emit('game_state_update', get_game_state(game), room=p_info['room'])
        else:
            print(f"Player {p_info.get('color')} cannot skip turn. Valid moves are available.")
    else:
        print(f"Player {p_info.get('color')} cannot skip turn. It's not their turn.")


@sio.event
async def request_ai_move(sid, state_data):
    difficulty = state_data.get('difficulty', 'hard')
    print(f"[{sid}] Server is calculating AI move...")

    temp_game = BackgammonLogic()
    temp_game.board = state_data['board']
    temp_game.bar = state_data['bar']
    temp_game.off = state_data['off']
    temp_game.turn = state_data['turn']
    temp_game.dice = state_data['dice']

    match difficulty:
        case "easy":
            chosen_model = None
        case "medium":
            chosen_model = ai_model_medium
        case "hard":
            chosen_model = ai_model_hard

    best_move = calculate_best_move(temp_game, chosen_model)

    await sio.emit('ai_move_response', {'move': best_move}, to=sid)

@sio.event
async def make_move(sid, data):
    if sid not in players: return
    p_info = players[sid]
    game = games[p_info['room']]

    print(f"[{p_info.get('color')}] sent move: {data['start']} -> {data['target']}")

    if game.turn == p_info.get('color'):
        game.move_piece(data['start'], data['target'], data['used_dice'])
        print(f"Move executed on the server! Sending new game state to the players...")
        await sio.emit('game_state_update', get_game_state(game), room=p_info['room'])
    else:
        print(f"Move denied! It is not players's {p_info.get('color')} turn")

@sio.event
async def end_turn(sid):
    if sid not in players: return
    p_info = players[sid]
    game = games[p_info['room']]

    if game.turn == p_info['color']:
        game.switch_turn()
        await sio.emit('game_state_update', get_game_state(game), room=p_info['room'])

@sio.event
async def undo_move(sid):
    if sid not in players: return
    p_info = players[sid]
    game = games[p_info['room']]

    if game.turn == p_info['color']:
        game.undo_move()
        await sio.emit('game_state_update', get_game_state(game), room=p_info['room'])

@sio.event
async def request_play_again(sid):
    if sid not in players:
        return

    p_info = players[sid]
    room_id = p_info['room']

    await sio.emit('receive_play_again_request', {}, room=room_id, skip_sid=sid)

@sio.event
async def respond_play_again(sid, data):
    if sid not in players: return
    p_info = players[sid]
    room_id = p_info['room']

    accepted = data.get('accept')
    if accepted:
        game = games[room_id]
        game.reset_game()
        print(f"Play again accepted in room {room_id}. Starting new game...")
        await sio.emit('game_state_update', get_game_state(game), room=room_id)
    else:
        await sio.emit('play_again_declined', {}, room=room_id, skip_sid=sid)
        print(f"Play again declined. Destroying room {room_id}...")
        if room_id in games:
            del games[room_id]

        sids_to_remove = [k for k, v in players.items() if v['room'] == room_id]
        for s in sids_to_remove:
            del players[s]
            await sio.leave_room(s, room_id)

@sio.event
async def offer_double(sid):
    if sid not in players: return
    p_info = players[sid]
    room_id = p_info['room']
    game = games[room_id]

    if game.turn == p_info['color']:
        new_value = game.cube_value * 2
        await sio.emit('receive_double_offer', {'new_value': new_value}, room=room_id, skip_sid=sid)


@sio.event
async def respond_double(sid, data):
    if sid not in players: return
    p_info = players[sid]
    room_id = p_info['room']
    game = games[room_id]

    accepted = data.get('accept')

    if accepted:
        game.cube_value *= 2
        game.cube_owner = p_info['color']
        await sio.emit('game_state_update', get_game_state(game), room=room_id)
    else:
        game.winner = 1 - p_info['color']
        game.end_game()
        await sio.emit('game_state_update', get_game_state(game), room=room_id)

@sio.event
async def leave_match(sid):
    if sid in players:
        room_id = players[sid]['room']
        await sio.emit('opponent_disconnected', room=room_id, skip_sid=sid)
        if room_id in games:
            del games[room_id]
        del players[sid]
        await sio.leave_room(sid, room_id)

if __name__ == '__main__':
    # print("Server started on port 5555...")
    # web.run_app(app, port=5555)
    import os
    port = int(os.environ.get('PORT', 5555))
    print(f"Server started on port {port}...")
    web.run_app(app, host='0.0.0.0', port=port)

