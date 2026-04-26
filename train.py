import torch
import torch.nn as nn
import torch.optim as optim
from logic import BackgammonLogic
from ai import *

def train_ai():
    EPISODES = 2000
    LEARNING_RATE = 0.01

    model = TGGammonNetwork()
    optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()

    print("Starting training...")

    for episode in range(EPISODES):
        game = BackgammonLogic()
        prev_board_tensor = None
        prev_player = None

        while not game.game_over:
            if not game.has_rolled:
                game.roll_dice()
            if not game.any_valid_moves():
                game.dice = []
                game.switch_turn()
                continue
            current_player = game.turn
            move = game.get_ai_move(model)

            if move:
                start, target, path = move
                game.move_piece(start, target, path)
                board_tensor = game.get_board_vector(player_id=current_player)
                current_prediction = model(board_tensor)

                if prev_board_tensor is not None:
                    prediction = model(prev_board_tensor)

                    with torch.no_grad():
                        current_prediction = model(board_tensor)
                    if current_player == prev_player:
                        target = current_prediction.detach()
                    else:
                        target = 1.0 - current_prediction.detach()

                    loss = criterion(prediction, target)
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                prev_board_tensor = board_tensor
                prev_player = current_player

            if game.dice and game.any_valid_moves():
                continue
            else:
                game.dice = []
                game.switch_turn()

        if prev_board_tensor is not None:
            prediction = model(prev_board_tensor)
            if game.winner == prev_player:
                final_target = torch.tensor([1.0], dtype=torch.float32)
            else:
                final_target = torch.tensor([0.0], dtype=torch.float32)
            loss = criterion(prediction, final_target)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        if (episode + 1) % 100 == 0:
            print(f"Episode: {episode + 1}, last winner: {game.winner}")

        if (episode + 1) % 1000 == 0:
            torch.save(model.state_dict(), f"models/ai_{episode + 1}.pth")
            print(f"Model saved for the game {episode + 1}!")

    print("Finished training.")
if __name__ == "__main__":
    train_ai()

