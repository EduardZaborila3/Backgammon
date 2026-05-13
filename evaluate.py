import torch
from logic import BackgammonLogic
from ai import TDGammonNetwork

def test_ai(model_path_a, model_path_b, nr_games=100):
    print(f"Loading Model A(Player 0): {model_path_a}")
    model_a = TDGammonNetwork()
    model_a.load_state_dict(torch.load(model_path_a, weights_only=True))
    model_a.eval()

    print(f"Loading Model B(Player 1): {model_path_b}")
    model_b = TDGammonNetwork()
    model_b.load_state_dict(torch.load(model_path_b, weights_only=True))
    model_b.eval()

    wins_a = 0
    wins_b = 0
    print("The test is starting")
    for i in range(nr_games):
        game = BackgammonLogic()
        while not game.game_over:
            if not game.has_rolled:
                game.roll_dice()

            if not game.any_valid_moves():
                game.dice = []
                game.switch_turn()
                continue

            if game.turn == 0:
                move = game.get_ai_move(model_a)
            else:
                move = game.get_ai_move(model_b)

            if move:
                start, target, path = move
                game.move_piece(start, target, path)

            if game.dice and game.any_valid_moves():
                continue
            else:
                game.dice = []
                game.switch_turn()

        if game.winner == 0:
            wins_a += 1
        else:
            wins_b += 1

        if (i + 1) % 10 == 0:
            print(f"Game {i + 1} finished.. Score: Model 20k -> {wins_a} | Model 2k -> {wins_b}")

    print("FINAL RESULTS")
    print(f"Model A ({model_path_a}) won: {wins_a} games ({wins_a/nr_games * 100:.1f}%)")
    print(f"Model B ({model_path_b}) won: {wins_b} games ({wins_b/nr_games * 100:.1f}%)")

if __name__ == "__main__":
    MODEL_20K = "models/ai_20000.pth"
    MODEL_2K = "models/ai_2000.pth"

    test_ai(MODEL_20K, MODEL_2K, nr_games=100)

