import random
import numpy as np

def get_board_vector(game, player_id):
    """Transforms the game state in a standard list for ONNX"""
    board_features = []
    for i in range(24):
        actual_index = i if player_id == 1 else 23 - i

        point = game.board[actual_index]
        my_checkers = len(point) if point and point[0] == player_id else 0
        opp_checkers = len(point) if point and point[0] == 1 - player_id else 0

        board_features.extend([
            1 if my_checkers >= 1 else 0,
            1 if my_checkers >= 2 else 0,
            1 if my_checkers >= 3 else 0,
            (my_checkers - 3) / 2.0 if my_checkers > 3 else 0
        ])

        board_features.extend([
            1 if opp_checkers >= 1 else 0,
            1 if opp_checkers >= 2 else 0,
            1 if opp_checkers >= 3 else 0,
            (opp_checkers - 3) / 2.0 if opp_checkers > 3 else 0
        ])

    board_features.append(game.bar[player_id] / 2.0)
    board_features.append(game.bar[1 - player_id] / 2.0)
    board_features.append(game.off[player_id] / 2.0)
    board_features.append(game.off[1 - player_id] / 2.0)
    board_features.append(1.0 if game.turn == player_id else 0.0)
    board_features.append(1.0 if game.turn != player_id else 0.0)

    return board_features

def calculate_best_move(game, model):
    """Find the best move using ONNX inference"""
    possible_moves = []
    current_player = game.turn

    if game.bar[current_player] > 0:
        start_idx = 24 if current_player == 0 else -1
        moves = game.get_valid_moves(start_idx)
        for target, path in moves:
            possible_moves.append((start_idx, target, path))
    else:
        for i in range(24):
            if game.board[i] and game.board[i][0] == current_player:
                moves = game.get_valid_moves(i)
                for target, path in moves:
                    possible_moves.append((i, target, path))

    if not possible_moves:
        return None

    if model is None:
        return random.choice(possible_moves)

    board_lists = []
    valid_moves_list = []

    for start, target, path in possible_moves:
        cloned_game = game.clone_state()
        cloned_game.move_piece(start, target, path)

        board_lists.append(get_board_vector(cloned_game, current_player))
        valid_moves_list.append((start, target, path))

    if not board_lists:
        return random.choice(possible_moves)

    batch_array = np.array(board_lists, dtype=np.float32)
    ort_inputs = {model.get_inputs()[0].name: batch_array}
    values = model.run(None, ort_inputs)[0]
    best_index = np.argmax(values)
    return valid_moves_list[best_index]