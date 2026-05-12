import socketio
from aiohttp import web
from logic import BackgammonLogic
import uuid

sio = socketio.AsyncServer(cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

waiting_player = None
games = {}
players = {}

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

@sio.event
async def connect(sid, environ):
    print(f"[{sid}] connected to the server.")

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
async def play_again(sid):
    if sid not in players:
        return

    p_info = players[sid]
    room_id = p_info['room']
    game = games[room_id]

    game.reset_game()
    print(f"Game has been reset by player {p_info['color']} in room {room_id}. Starting a new match...")
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
    import os
    port = int(os.environ.get('PORT', 5555))
    print(f"Server started on port {port}...")
    web.run_app(app, host='0.0.0.0', port=port)

