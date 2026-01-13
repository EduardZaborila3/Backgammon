import random
import json
from tkinter import messagebox
import os
import copy

class BackgammonLogic:
    """
    Manages the core logic, state, and rules of the Backgammon game.

    Attributes:
        board (list): A list of 24 lists representing the points on the board.
        history (list): A stack of previous board states for Undo move functionality.
        match_score (list): Current match score [Player0, Player1].
        bar (list): Count of checkers on the bar for each player [P0, P1].
        off (list): Count of checkers borne off for each player [P0, P1].
        turn (int): Current player turn 0/1.
        dice (list): Current dice values ([3, 5] or [4, 4, 4, 4])
        cube_value (int): Current value of the doubling cube.
        cube_owner (int): Owner of the cube (-1 default).
    """
    def __init__(self):
        """Initializes the game state, ressetting board, dice and score."""
        self.board = []
        for i in range(24):
            self.board.append([])
        
        self.history = []
        self.match_score = [0, 0]
        self.bar = [0, 0]
        self.off = [0, 0]
        self.turn = 0
        self.dice = []
        self.has_rolled = False
        self.game_over = False
        self.winner = -1
        self.cube_value = 1
        # initial nu are nimeni cubul
        self.cube_owner = -1
        self.init_board()

    def init_board(self):
        """Sets up the initial checker positions."""
        setup = [
            (23, 0, 2), (12, 0, 5), (7, 0, 3), (5, 0, 5),
            (0, 1, 2), (11, 1, 5), (16, 1, 3), (18, 1, 5)
        ]
        # setup = [
        #     (23, 1, 2), (22, 1, 2), (21, 1, 2), (20, 1, 3), (19, 1, 3), (18, 1, 3),
        #     (5, 0, 3), (4, 0, 3), (3, 0, 3), (2, 0, 2), (1, 0, 2), (0, 0, 2)
        # ]
        self.board = []
        for i in range(24):
            self.board.append([])
        for index, player_id, count in setup:
            self.board[index] = [player_id] * count
        print("Board Initialized")

    def roll_dice(self):
        """
        Generates random dice rolls.
        Handles double logic and resets history when new turn.
        """
        if self.dice:
            return
        self.has_rolled = True
        self.history = []
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        if d1 == d2:
            self.dice = [d1, d1, d1, d1]
        else:
            self.dice = [d1, d2]
        print(f"Player {self.turn} rolled the dice: {self.dice}")

        # if not self.any_valid_moves():
        #     print(f"No valid moves for Player {self.turn}. Switching turn...")
        #     self.dice = []
        #     # self.switch_turn()

    def any_valid_moves(self):
        """Checks for any valid moves from every point"""
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
        """
        Calculates all legal moves for a specific checker
        Args: 
            start_index (int): The board index (0 - 23), Bar (-1 or 24)

        Returns:
            list: List of tuples containing (target_index, used_dce_path)
                Returns an empty list if no moves are possible.
        """
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
        """
        Executes a move, updating the board state.
        This method handles:
        1. Moves the checker (with hit and bear-off)
        2. Removes the used dice values.
        3. Checks for win conditions.
        4. Saves the current state to history. (for undo)

        Args:
            start_index (int): Start point index
            target_index (int): Destination point index
            used_dice (list): The specific dice values used to make this move
        """
        self.save_board_state()
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
            def delay_dice_cleanup():
                self.dice = []
            self.root.after(1500, delay_dice_cleanup)
            return

        if (self.off[0] == 3 or self.off[1] == 3) and not self.dice:
            if self.check_special_win() > -1:
                self.winner = self.check_special_win()
                self.end_game()

        if self.off[self.turn] == 15:
            self.winner = self.turn
            self.end_game()

    def get_ai_move(self):
        """
        Finds all possible moves and choses a random one to execute.
        """
        possible_moves = []

        if self.bar[1] > 0:
            #daca are piese pe bara e obligat sa le mute primele, daca are pozitii permise
            moves = self.get_valid_moves(-1) 
            for target, path in moves:
                possible_moves.append((-1, target, path))
        else:
            #daca nu are piese pe bara, atunci verific mutarile de pe tabla
            for i in range(24):
                if self.board[i] and self.board[i][0] == 1:
                    moves = self.get_valid_moves(i)
                    for target, path in moves:
                        possible_moves.append((i, target, path))

        #ai ul face o mutare random din cele permise gasite
        if possible_moves:
            return random.choice(possible_moves)
        return None

    def can_bear_off(self, player_id):
        """
        Checks if a player is allowed to bear off bt checking the bar and if all of his checkers are in the house.
        """
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
        """Gets the position of the dots on the die by value"""
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
        """Checks for special rule: if a player has all of his checkers in the house and they are 2 on every point, he wins before bearing-off all of his pieces."""
        if not(self.bar[self.turn] == 0 and self.off[self.turn] == 3):
            return -1
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

    def calculate_points(self):
        """
        Calculates the points generated by a win depending on the win type:
        1. 1 point if the loser sent off at least one piece
        2. 2 points if the loser hasn't sent off any pieces
        3. 3 points if loser has at least one piece on the bar or in the winner's house
        """
        loser = 1 - self.winner
        piece_in_winner_home = False
        points = 1

        # daca cel care pierde nu a apucat sa scoata vreo piesa e marti
        if self.off[loser] == 0:
            if self.winner == 0:
                winner_home = range(0, 6)
            else:
                winner_home = range(18, 24)
            # verific daca loser ul are piese in casa adversa
            for i in winner_home:
                if self.board[i] and self.board[i][0] == loser:
                    piece_in_winner_home = True  

            if self.bar[loser] > 0 or piece_in_winner_home:
                points = 3
            points = 2
        points = 1

        return points * self.cube_value
    
    def reset_game(self):
        """Resets game and score"""
        current_score = self.match_score
        self.__init__()
        self.match_score = current_score

    def end_game(self):
        """Ends game and score"""
        self.game_over = True
        points = self.calculate_points()
        self.match_score[self.winner] += points
        if self.turn == 0:
            print("You won the match!")
        else:
            print("You lost the match!")

    def save_game(self, filepath, ai_match):
        """
        Serializes the current game into a JSON file
        Args:
            filepath (str): The path to the output JSON file
            ai_match (bool): Flag indicating if the current game is against AI
        Returns:
            bool: True if save was successful, False if an error occurred
        """
        state = {
            "board": self.board,
            "match_score": self.match_score,
            "bar": self.bar,
            "off": self.off,
            "turn": self.turn,
            "dice": self.dice,
            "has_rolled": self.has_rolled,
            "game_over": self.game_over,
            "winner": self.winner,
            "ai_match": ai_match,
            "cube_value": self.cube_value,
            "cube_owner": self.cube_owner
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=4)
            print("Game was successfully saved")
            return True
        except Exception as e:
            print(f"Error while saving the game: {e}")
            return False
        
    def load_game(self, filepath):
        """Converts the containing of the file into a dictionary to reload the game state"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            self.board = state["board"]
            self.match_score = state["match_score"]
            self.bar = state["bar"]
            self.off = state["off"]
            self.turn = state["turn"]
            self.dice = state["dice"]
            self.has_rolled = state["has_rolled"]
            self.game_over = state["game_over"]
            self.winner = state["winner"]
            self.cube_value = state.get("cube_value", 1)
            self.cube_owner = state.get("cube_owner", -1)
            if self.game_over:
                self.reset_game()
            return state.get("ai_match", False)
        except Exception as e:
            print(f"Error while loading the game: {e}")
            return None
        
    def save_board_state(self):
        """
        Creates a deep copy of the current game attributes.
        Appends the snapshot to self.history to allow the undo_move method to revert changes within the current turn
        """
        board_snapshot = {
            "board": copy.deepcopy(self.board),
            "bar": copy.deepcopy(self.bar),
            "off": copy.deepcopy(self.off),
            "dice": copy.deepcopy(self.dice),
            "winner": self.winner,
            "game_over": self.game_over
        }
        self.history.append(board_snapshot)

    def undo_move(self):
        """
        Reverts the game to the previous state in the history stack.

        Returns:
            bool: True if undo was successful, False if history was empty.
        """
        if not self.history:
            return False
        
        last_state = self.history.pop()
        self.board = last_state["board"]
        self.bar = last_state["bar"]
        self.off = last_state["off"]
        self.dice = last_state["dice"]
        self.winner = last_state["winner"]
        self.game_over = last_state["game_over"]
        print("Undo performed")
        return True