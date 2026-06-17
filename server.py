from torch.fx.passes.infra.pass_manager import pass_result_wrapper
import os
import psycopg2
import socketio
from aiohttp import web
from dotenv import load_dotenv
from logic import BackgammonLogic
import uuid
from ai import calculate_best_move
import onnxruntime as ort
import asyncio
import random
from supabase import create_async_client, AsyncClient

ai_lock = asyncio.Lock()

load_dotenv()
connected_users = {}

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE = os.environ.get("SUPABASE_SERVICE_ROLE")

supabase: AsyncClient = create_async_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin: AsyncClient = create_async_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)



def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
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

try:
    ai_model_medium = ort.InferenceSession("models/ai_20000.onnx")
    print("Medium AI Model (20k) ONNX loaded successfully!")
except Exception as e:
    print(f"Error loading medium AI model: {e}")
    ai_model_medium = None

try:
    ai_model_hard = ort.InferenceSession("models/ai_100000.onnx")
    print("Hard AI Model (100k) ONNX loaded successfully!")
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

def fetch_users_stats(user_id):
    """Receives the public data of the user based on Supabase Auth ID"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT username, games_played, games_won, email FROM users WHERE id=%s", (user_id,))
            row = cursor.fetchone()
            if row:
                return{
                    'username': row[0],
                    'games_played': row[1],
                    'games_won': row[2],
                    'has_credentials': True if row[3] else False
                }
            return None
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return None

@sio.event
async def connect(sid, environ, auth):
    print(f"[{sid}] connected tot the server")
    connected_users[sid] = {'token': None, 'username': 'Guest', 'id': None, 'games_played': 0, 'games_won': 0, 'has_credentials': False}
    if auth and 'token' in auth:
        token = auth['token']
        try:
            res = await asyncio.to_thread(supabase.auth.get_user, token)
            user_id = res.user.id
            stats = await asyncio.to_thread(fetch_users_stats, user_id)
            if stats:
                connected_users[sid].update({
                    'token': token,
                    'id': user_id,
                    'username': stats['username'],
                    'games_played': stats['games_played'],
                    'games_won': stats['games_won'],
                    'has_credentials': stats['has_credentials']
                })
                print(f"[{sid}] connected automatically as {stats['username']}")
                await sio.emit('profile_data_update', stats, to=sid)
        except Exception as e:
            print(f"[{sid}] Invalid token: {e}")

@sio.event
async def guest_login(sid):
    """Creates an anonymous account in Supabase (Play as Guest)"""
    try:
        res = await asyncio.to_thread(supabase.auth.sign_in_anonymously)
        token = res.session.access_token
        user_id = res.user.id
        await asyncio.sleep(0.5)
        stats = await asyncio.to_thread(fetch_users_stats, user_id)

        if stats:
            connected_users[sid].update({
                'token': token,
                'id': user_id,
                'username': stats['username'],
                'games_played': 0,
                'games_won': 0,
                'has_credentials': False
            })
            await sio.emit('profile_data_update', stats, to=sid)
            await sio.emit('auth_success', {'token': token, 'message': 'New Guest account created!'}, to=sid)
    except Exception as e:
        await sio.emit('auth_error', {'message': str(e)}, to=sid)

@sio.event
async def register_account(sid, data):
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        await sio.emit('auth_error', {'message': 'Fill in all fields!'}, to=sid)
        return

    try:
        res = await asyncio.to_thread(supabase.auth.sign_up, {
            "email": email,
            "password": password,
            "options": {"data": {"username": username}}
        })
        token = res.session.access_token
        user_id = res.user.id

        await asyncio.sleep(0.5)
        stats = await asyncio.to_thread(fetch_users_stats, user_id)
        connected_users[sid].update({
            'token': token,
            'id': user_id,
            'username': stats['username'],
            'games_played': 0,
            'games_won': 0,
            'has_credentials': True
        })

        await sio.emit('profile_data_update', stats, to=sid)
        await sio.emit('auth_success', {'token': token, 'message': 'Account successfully created!'}, to=sid)
    except Exception as e:
        print(f"Register error: {e}")
        await sio.emit('auth_error', {'message': 'Register error. Already used email?'}, to=sid)
        return

async def login_account(sid, data):
    email = data.get('email')
    password = data.get('password')

    try:
        res = await asyncio.to_thread(supabase.auth.sign_in_with_password, {"email": email, "password": password})
        token = res.session.access_token
        user_id = res.user.id
        stats = await asyncio.to_thread(fetch_users_stats, user_id)
        if stats:
            connected_users[sid].update({
                'token': token,
                'id': user_id,
                'username': stats['username'],
                'games_played': stats['games_played'],
                'games_won': stats['games_won'],
                'has_credentials': True
            })
            await sio.emit('profile_data_update', stats, to=sid)
            await sio.emit('auth_success', {'token': token, 'message': 'Logged in successfully!'}, to=sid)
    except Exception as e:
        print(f"Login error: {e}")
        await sio.emit('auth_error', {'message': 'Wrong email or password!'}, to=sid)

@sio.event
async def register_credentials(sid, data):
    if sid not in connected_users: return
    email = data.get('email')
    password = data.get('password')
    user_id = connected_users[sid].get('id')
    if not email or not password or not user_id: return
    try:
        await asyncio.to_thread(supabase_admin.auth.admin.update_user_by_id, user_id, email=email, password=password)
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET email=%s WHERE id=%s", (email, user_id))
            conn.commit()
        connected_users[sid]['has_credentials'] = True
        stats = {
            'username': connected_users[sid]['username'],
            'games_played': connected_users[sid]['games_played'],
            'games_won': connected_users[sid]['games_won'],
            'has_credentials': True
        }
        await sio.emit('profile_data_update', stats, to=sid)
        print(f"[{sid}] successfully update credentials!")
    except Exception as e:
        print(f"Error saving credentials: {e}")

@sio.event
async def db_update_username(sid, data):
    """Updates the user's name in the database and active memory"""
    if sid not in connected_users:
        return

    new_name = data.get('new_username')
    if not new_name:
        return
    user_id = connected_users[sid].get('id')
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET username = %s WHERE id = %s", (new_name, user_id))
        conn.commit()
        connected_users[sid]['username'] = new_name
        print(f"[{sid}] changed his name in {new_name}")
        await sio.emit('profile_data_update', {
            'username': connected_users[sid]['username'],
            'games_played': connected_users[sid]['games_played'],
            'games_won': connected_users[sid]['games_won']
        }, to=sid)
    except Exception as e:
        print(f"Error updating the name: {e}")

def db_update_stats(db_id, is_winner):
    """Updates in the database played and won games"""
    try:
        with conn.cursor() as cursor:
            if is_winner:
                cursor.execute("UPDATE users SET games_played = games_played + 1, games_won = games_won + 1 WHERE id = %s", (db_id,))
            else:
                cursor.execute("UPDATE users SET games_played = games_played + 1 WHERE id = %s", (db_id,))
            conn.commit()
            print(f"Updated games played for DB_ID {db_id}")
    except Exception as err:
        print(f"Database update error: {err}")

async def process_game_end(room_id, game, disconnected_sid=None):
    """Updates once per game, also when a player leaves the game"""
    if getattr(game, 'stats_saved', False):
        return
    game.stats_saved = True

    for p_sid, p_data in players.items():
        if p_data['room'] == room_id:
            user_db_id = connected_users[p_sid].get('id')
            if disconnected_sid:
                is_win = (p_sid != disconnected_sid)
            else:
                is_win = (p_data['color'] == game.winner)
            if user_db_id:
                await asyncio.to_thread(db_update_stats, user_db_id, is_win)
                connected_users[p_sid]['games_played'] += 1
                if is_win:
                    connected_users[p_sid]['games_won'] += 1

                await sio.emit('profile_data_update', {
                    'username': connected_users[p_sid]['username'],
                    'games_played': connected_users[p_sid]['games_played'],
                    'games_won': connected_users[p_sid]['games_won']
                }, to=p_sid)

@sio.event
async def disconnect(sid):
    global waiting_player
    print(f"[{sid}] disconnected from the server.")

    if waiting_player == sid:
        waiting_player = None

    if sid in connected_users:
        del connected_users[sid]

    if sid in players:
        room_id = players[sid]['room']

        game = games.get(room_id)
        if game and not game.game_over:
            game.game_over = True
            await process_game_end(room_id, game, disconnected_sid=sid)
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
        p1_color = random.choice([0, 1])
        p2_color = 1 - p1_color
        players[p1_sid] = {'room': room_id, 'color': p1_color}
        players[p2_sid] = {'room': room_id, 'color': p2_color}
        print(f"Game started between [{p1_sid}] and [{p2_sid}] in room {room_id}.")
        print(f"[{p1_sid}] is color {p1_color}, [{p2_sid}] is color {p2_color}.")

        p1_username = connected_users[p1_sid]['username']
        p2_username = connected_users[p2_sid]['username']
        if p1_color == 0:
            p0_name = p1_username
            p1_name = p2_username
        else:
            p0_name = p2_username
            p1_name = p1_username

        await sio.emit('assign_player', {'player_id': p1_color, 'p0_name': p0_name, 'p1_name': p1_name}, to=p1_sid)
        await sio.emit('assign_player', {'player_id': p2_color, 'p0_name': p0_name, 'p1_name': p1_name}, to=p2_sid)

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

    async with ai_lock:
        print(f"Server is calculating AI move...")
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
        try:
            best_move = await asyncio.to_thread(calculate_best_move, temp_game, chosen_model)
            await sio.emit('ai_move_response', {'move': best_move}, to=sid)
        except Exception as e:
            print(f"[{sid}] Error during AI calculation: {e}")
            await sio.emit('ai_move_response', {'move': None}, to=sid)

@sio.event
async def make_move(sid, data):
    if sid not in players: return
    p_info = players[sid]
    game = games[p_info['room']]
    if not game: return
    try:
        print(f"[{p_info.get('color')}] sent move: {data['start']} -> {data['target']}")

        if game.turn == p_info.get('color'):
            game.move_piece(data['start'], data['target'], data['used_dice'])
            print(f"Move executed on the server!")
            await sio.emit('game_state_update', get_game_state(game), room=p_info['room'])
        else:
            print(f"Move denied! It is not players's {p_info.get('color')} turn")

        if game.game_over:
            await process_game_end(p_info['room'], game)

    except Exception as e:
        print(f"CRITICAL LOGIC ERROR in make_move: {e}")
        if game:
            await sio.emit('game_state_update', get_game_state(game), room=p_info['room'])

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
        await process_game_end(room_id, game)

@sio.event
async def leave_match(sid):
    if sid in players:
        room_id = players[sid]['room']
        game = games.get(room_id)
        if game and not game.game_over:
            game.game_over = True
            await process_game_end(room_id, game, disconnected_sid=sid)
        await sio.emit('opponent_disconnected', room=room_id, skip_sid=sid)
        if room_id in games:
            del games[room_id]
        del players[sid]
        await sio.leave_room(sid, room_id)

@sio.event
async def skip_turn_closed_board(sid):
    if sid not in players:
        return
    p_info = players[sid]
    game = games.get(p_info['room'])
    if game.turn == p_info.get('color'):
        if game.bar[game.turn] > 0 and game.is_entry_blocked(game.turn):
            print(f"Player {game.turn} has entry blocked. Switching turn...")
            game.dice = []
            game.switch_turn()
            await sio.emit('game_state_update', get_game_state(game), room=p_info['room'])

if __name__ == '__main__':
    # print("Server started on port 5555...")
    # web.run_app(app, port=5555)
    import os
    port = int(os.environ.get('PORT', 5555))
    print(f"Server started on port {port}...")
    web.run_app(app, host='0.0.0.0', port=port)

