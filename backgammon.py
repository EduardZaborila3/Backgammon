import random

class BackgammonLogic:
    def __init__(self):
        self.board = [[] for _ in range(24)]
        self.bar = [0, 0]
        self.off = [0, 0]
        self.turn = 0
        self.dice = []
        self.init_board()

    def init_board(self):
        setup = [
            (23, 0, 2), (12, 0, 5), (7, 0, 3), (5, 0, 5),
            (0, 1, 2), (11, 1, 5), (16, 1, 3), (18, 1, 5)
        ]
        self.board = []
        for i in range(24):
            self.board.append([])
        for index, player_id, count in setup:
            self.board[index] = [player_id] * count
        print("Board Initialized.")

    def roll_dice(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        if d1 == d2:
            self.dice = [d1, d1, d1, d1]
        else:
            self.dice = [d1, d2]
        print(f"Player {self.turn} rolled the dice: {self.dice}")

    def get_valid_moves(self, start_index):
        moves = []
        point = self.board[start_index]
        
        if not point or point[0] != self.turn:
            return []


        if self.bar[self.turn]:
            return []

        if self.turn == 0:
            direction = -1
        else:
            direction = 1
        unique_dice = set(self.dice) 
        for die in unique_dice:
            target_index = start_index + (die * direction)
            
            if 0 <= target_index <= 23:
                target_point = self.board[target_index]
                
                if (not target_point) or (target_point[0] == self.turn) or (len(target_point) == 1 and target_point[0] != self.turn):
                    moves.append((target_index, die))
        return moves

    def move_piece(self, start_index, target_index, die_value):
        p_id = self.board[start_index].pop()
        target_point = self.board[target_index]
        
        if target_point and target_point[0] != p_id:
            hit_piece = target_point.pop()
            self.bar[1 - p_id] += 1
            print(f"Player {1-p_id} piece was sent to bar")
            
        self.board[target_index].append(p_id)
        
        if die_value in self.dice:
            self.dice.remove(die_value)
            
        if not self.dice:
            self.turn = 1 - self.turn
            print(f"Turn Ends. Now Player {self.turn} moves")

def print_console_board(game):
    print("\nState:")
    print(f"Bar (P0/P1): {game.bar}")
    print(f"Off (P0/P1): {game.off}")
    print("Board:", [f"{i}:{game.board[i]}" for i in range(0, 12)])
    print([f"{i}:{game.board[i]}" for i in range(12, 24)])

if __name__ == "__main__":
    game = BackgammonLogic()
    print_console_board(game)

    while True:
        game.roll_dice()

        while len(game.dice) > 0:
            print(f"Available dice: {game.dice}")
            possible_moves = []
            for i in range(24):
                if game.board[i] and game.board[i][0] == game.turn:
                    moves = game.get_valid_moves(i)
                    for target, die in moves:
                        possible_moves.append((i, target, die))
            
            print(f"Valid moves for player {game.turn}: ")
            if not possible_moves:
                print("No possible moves. Moving to next player.")
                game.dice = []
                game.turn = 1 - game.turn
                break
            for move in possible_moves:
                print(f"Start: {move[0]} -> {move[1]} [Die: {move[2]}]")

            if possible_moves:
                selected_move = random.choice(possible_moves)
                start_pos, target, die = selected_move
                print(f"Executing move from {start_pos} to {target} using die {die}")
                game.move_piece(start_pos, target, die)
                print_console_board(game)
            else:
                print("Player can't move. Switching turn...")
        
        input("Press ENTER for next turn")