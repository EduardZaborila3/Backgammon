import random

class BackgammonLogic:
    def __init__(self):
        self.board = []
        for i in range(24):
            self.board.append([])
        self.bar = [0, 0]
        self.off = [0, 0]
        self.turn = 0
        self.dice = []
        self.has_rolled = False
        self.game_over = False
        self.winner = -1
        self.init_board()

    def init_board(self):
        # setup = [
        #     (23, 0, 2), (12, 0, 5), (7, 0, 3), (5, 0, 5),
        #     (0, 1, 2), (11, 1, 5), (16, 1, 3), (18, 1, 5)
        # ]
        setup = [
            (23, 1, 2), (22, 1, 2), (21, 1, 2), (20, 1, 3), (19, 1, 3), (18, 1, 3),
            (5, 0, 3), (4, 0, 3), (3, 0, 3), (2, 0, 2), (1, 0, 2), (0, 0, 2)
        ]
        self.board = []
        for i in range(24):
            self.board.append([])
        for index, player_id, count in setup:
            self.board[index] = [player_id] * count
        print("Board Initialized")

    def roll_dice(self):
        if self.dice:
            return
        self.has_rolled = True
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        if d1 == d2:
            self.dice = [d1, d1, d1, d1]
        else:
            self.dice = [d1, d2]
        print(f"Player {self.turn} rolled the dice: {self.dice}")

        if not self.any_valid_moves():
            print(f"No valid moves for Player {self.turn}. Switching turn...")
            self.dice = []
            # self.switch_turn()

    def any_valid_moves(self):
        # sunt obligat sa mut piesa scoasa inapoi in joc
        if self.bar[self.turn] > 0:
            if self.turn == 0:
                # daca s cu alb incep inapoi de sus
                bar_start_index = 24
            else:
                # pt negru incep de jos
                bar_start_index = -1
            return len(self.get_valid_moves(bar_start_index)) > 0
        for i in range(24):
            if self.board[i] and self.board[i][0] == self.turn:
                if len(self.get_valid_moves(i)) > 0:
                    return True
        return False

    def get_valid_moves(self, start_index):
        moves = {}

        is_bar_entry = False
        if start_index == 24 or start_index == -1:
            is_bar_entry = True
        if self.bar[self.turn] > 0:
            if not is_bar_entry:
                return []
            if self.turn == 0:
                correct_bar_index = 24
            else:
                correct_bar_index = -1
            if start_index != correct_bar_index:
                return []
            
        if not is_bar_entry:
            if not (0 <= start_index < 24):
                return []
            point = self.board[start_index]
            if not point or point[0] != self.turn:
                return []
        
        if self.turn == 0:
            direction = -1
            #iau index in afara jocului pt piesele scoase (beared-off) la alb
            off_target = -2
        else:
            direction = 1
            #index in afara pt piesele scoase la negru
            off_target = 25
        can_bear = self.can_bear_off(self.turn)

        def find_paths(current_index, available_dice, used_dice_path):
            unique_dice = set(available_dice)
            for die in unique_dice:
                target = current_index + (die * direction)
                valid_move = False
                if 0 <= target <= 23:
                    target_point = self.board[target]
                    if not target_point or target_point[0] == self.turn or (len(target_point) == 1 and target_point[0] != self.turn):
                        valid_move = True
                    
                    if valid_move:
                        new_path = used_dice_path + [die]
                        if target not in moves:
                            moves[target] = new_path
                        elif len(new_path) < len(moves[target]):
                            moves[target] = new_path
                        can_continue = (not target_point) or (target_point[0] == self.turn)

                        if can_continue:
                            remaining_dice = list(available_dice)
                            remaining_dice.remove(die)
                            if remaining_dice:
                                find_paths(target, remaining_dice, new_path)
                # verific daca pot scoate piese din casa
                elif can_bear:
                    exact_die = False
                    if self.turn == 0:
                        if target == -1:
                            exact_die = True
                        elif target < -1:
                            highest_piece = True
                            for k in range(current_index + 1, 6):
                                if self.board[k] and self.board[k][0] == 0:
                                    highest_piece = False
                                    break
                            if highest_piece:
                                exact_die = True
                    else:
                        if target == 24:
                            exact_die = True
                        elif target > 24:
                            highest_piece = True
                            for k in range(18, current_index):
                                if self.board[k] and self.board[k][0] == 1:
                                    highest_piece = False
                                    break
                            if highest_piece:
                                exact_die = True
                    
                    if exact_die:
                        new_path = used_dice_path + [die]
                        moves[off_target] = new_path
            
        find_paths(start_index, self.dice, [])
        return list(moves.items())
    
    def move_piece(self, start_index, target_index, used_dice):
        if start_index == 24 or start_index == -1:
            self.bar[self.turn] -= 1
            print(f"Player {self.turn} entered from bar")
            p_id = self.turn
        else:
            p_id = self.board[start_index].pop()
        if target_index == -2 or target_index == 25:
            self.off[p_id] += 1
            print(f"Player {p_id} sent a piece off. Total off: {self.off[p_id]}")
            
        else:
            target_point = self.board[target_index]
            if target_point and target_point[0] != p_id:
                #daca mut peste o singura piesa adversa, o scot (pe bara)
                hit_piece = target_point.pop()
                self.bar[1 - p_id] += 1
                print(f"Player {1-p_id} piece was sent to bar")
                
            self.board[target_index].append(p_id)
        
        for die in used_dice:
            if die in self.dice:
                self.dice.remove(die)

        if self.dice and not self.any_valid_moves() and self.off[self.turn] < 15:
            print(f"No valid moves for player {self.turn}. Dice lost")
            self.dice = []

        if self.off[0] == 3 or self.off[1] == 3 and not self.dice:
            if self.check_special_win() > -1:
                self.winner = self.check_special_win()
                self.end_game()

        if self.off[self.turn] == 15:
            self.winner = self.turn
            self.end_game()

    def can_bear_off(self, player_id):
        if self.bar[player_id] > 0:
            return False
        
        if player_id == 0:
            for i in range(6, 24):
                if self.board[i] and self.board[i][0] == player_id:
                    return False
        else:
            for i in range (0, 18):
                if self.board[i] and self.board[i][0] == player_id:
                    return False
                
        return True

    def get_dice_dots(self, value):
        dots_map = {
            1: [(0, 0)],
            2: [(-1, -1), (1, 1)],
            3: [(-1, -1), (0, 0), (1, 1)],
            4: [(1, -1), (-1, -1), (-1, 1), (1, 1)],
            5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
            6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]
        }
        return dots_map.get(value, [])
    
    def switch_turn(self):
        self.turn = 1 - self.turn
        self.dice = []
        self.has_rolled = False
        print(f"Turn switched. Now player {self.turn}")

    # regula pt marti tehnic
    def check_special_win(self):
        if self.bar[self.turn] == 0 and self.off[self.turn] == 3:
            if self.turn == 0:
                home_base_range = range(0, 6)
            else:
                home_base_range = range(18,24)
            is_perfect = True

            for i in home_base_range:
                if self.board[i] and self.board[i][0] == self.turn:
                    if len(self.board[i]) != 2:
                        is_perfect = False
                        break
        
        if is_perfect:
            return self.turn
        
        return -1


    def end_game(self):
        self.game_over = True
        if self.turn == 0:
            print("You won the match!")
        else:
            print("You lost the match!")