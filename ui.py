import tkinter as tk
from logic import BackgammonLogic
import random
from constants import *
import json
from tkinter import messagebox
import os
import torch
from ai import *

class BackgammonUI:
    """
    Manages the Graphical User Interface using Tkinter.
    This class handles drawing the board, processing mouse events (clicks, drags), rendering animations, and managing UI state (menus, popups).
    Attributes:
        root (tk.Tk): The main Tkinter window instance
        game (BackgammonLogic): The instance of the game logic
        canvas (tk.Canvas): The drawing area for the board
        valid_moves (list): Cache of valid moves for the currently selected piece
        ai_match (bool): True if playing against the CPU, False for PvP
    """
    def __init__(self, root):
        """Initializes the UI components and binds event listeners."""
        self.game = BackgammonLogic()
        self.root = root

        self.sio = None
        self.my_player_id = None
        self.is_multiplayer = False
        
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BORDER_COLOR)
        self.canvas.pack()
        
        self.selected_point = None
        self.valid_moves = []
        
        self.dragged_piece_id = None
        self.drag_start_index = None

        self.menu = True
        self.ai_match = False

        self.draw_menu()
        # self.draw_board()

        self.waiting_for_skip = False

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def draw_menu(self):
        """Draws the menu with game options"""
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#994f0a")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 200, text="Backgammon", fill="#CDCDCD", font=("Arial", 36, "bold"))

        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2 - 75, WIDTH / 2 + 100, HEIGHT / 2 - 25, fill="#3f1405", outline="white", width=2, tags="menu_pvp")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 50, text="2 players game", fill="#aaaaaa", activefill="#f9fc4f", font=("Arial", 16, "bold"))

        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2, WIDTH / 2 + 100, HEIGHT / 2 + 50, fill="#3f1405", outline="white", width=2, tags="menu_ai")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 25, text="Play vs AI", fill="#aaaaaa", activefill="#f9fc4f", font=("Arial", 16, "bold"))

        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2 + 75, WIDTH / 2 + 100, HEIGHT / 2 + 125, fill="#3f1405", outline="white", width=2, tags="menu_load")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 100, text="Load Game", fill="#aaaaaa", activefill="#f9fc4f", font=("Arial", 16, "bold"), tags="menu_load")

        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2 + 150, WIDTH / 2 + 100, HEIGHT / 2 + 200,
                                     fill="#1c5c16", outline="white", width=2, tags="menu_online")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 175, text="Play Online", fill="#aaaaaa", activefill="#f9fc4f",
                                font=("Arial", 16, "bold"), tags="menu_online")

    def start_game(self, ai_mode = False):
        """
        Starts the game
        Args:
            ai_mode: A flag that indicates if the game is PvP or PvAI
        """
        self.menu = False
        self.ai_match = ai_mode
        print(f"Game starting in ai mode: {ai_mode}")
        self.game = BackgammonLogic()

        if ai_mode:
            try:
                self.ai_model = TDGammonNetwork()
                model_path = "models/ai_2000.pth"
                self.ai_model.load_state_dict(torch.load(model_path, weights_only=True))
                self.ai_model.eval()
                print(f"AI Model '{model_path}' was successfully loaded!")
            except Exception as e:
                print(f"Error loading AI model: {e}")
                print("Fallback! AI will move random.")
                self.ai_model = None
        else:
            self.ai_model = None

        self.draw_board()

    def sync_state_from_server(self, state):
        self.game.board = state['board']
        self.game.bar = state['bar']
        self.game.off = state['off']
        self.game.turn = state['turn']
        self.game.dice = state['dice']
        self.game.match_score = state['match_score']
        self.game.game_over = state.get('game_over', False)
        self.game.winner = state.get('winner', -1)
        self.game.cube_value = state.get('cube_value', 1)
        self.game.cube_owner = state.get('cube_owner', -1)
        self.game.history = state.get('history', [])
        self.game.has_rolled = state.get('has_rolled', False)

        self.draw_board()

        if self.is_multiplayer and self.game.turn == self.my_player_id:
            if self.game.dice and not self.game.any_valid_moves():
                if not self.waiting_for_skip:
                    self.waiting_for_skip = True
                    print("No moves possible. Switching turn...")

                    def skip_turn():
                        print("1.5 sec passed. Sending 'skip_turn' to the server...")
                        self.sio.emit('skip_turn', {'player': self.my_player_id})
                        self.waiting_for_skip = False

                    self.root.after(1500, skip_turn)
            else:
                self.waiting_for_skip = False

        if self.game.game_over:
            if self.game.match_score[0] >= 5 or self.game.match_score[1] >= 5:
                self.draw_final_of_the_match(self.game.winner)
            else:
                self.draw_game_over(self.game.winner)
                self.sio.emit('game_over', {'winner': self.game.winner})

    def draw_board(self):
        """
        Clears and redraws the entire game board.

        This includes the triangles(points), checkers, dice, buttons (Roll, Undo, Done), and scoreboards based on the current self.game state.
        Highlights valid destination triangles if a piece is selected.
        """
        self.canvas.delete("all")
        
        self.canvas.create_rectangle(PLAY_AREA_START_X, PLAY_AREA_START_Y, LEFT_BOARD_END_X, PLAY_AREA_END_Y, fill=BOARD_COLOR, outline="black", width=2)
        self.canvas.create_rectangle(RIGHT_BOARD_START_X, PLAY_AREA_START_Y, PLAY_AREA_END_X, PLAY_AREA_END_Y, fill=BOARD_COLOR, outline="black", width=2)
        self.draw_doubling_cube()
        self.draw_dice()

        if self.game.has_rolled and not self.game.dice and not self.game.game_over:
            if not (self.ai_match and self.game.turn == 1):
                self.draw_done_button()

        if self.game.has_rolled and self.game.history and not self.game.game_over:
            if not (self.ai_match and self.game.turn == 1):
                self.draw_undo_button()

        valid_destinations = []
        for move in self.valid_moves:
            valid_destinations.append(move[0])

        available_width = (PLAY_AREA_END_X - PLAY_AREA_START_X) - CENTER_BAR_WIDTH
        point_width = available_width / 12
        
        for i in range(24):
            #jos 0-11
            if i < 12:
                visual_col = i
                y_base = PLAY_AREA_END_Y
                y_tip = PLAY_AREA_END_Y - TRIANGLE_HEIGHT
                # albu descreste
                direction = -1
            #sus 12-23
            else: 
                visual_col = 23 - i
                y_base = PLAY_AREA_START_Y
                y_tip = PLAY_AREA_START_Y + TRIANGLE_HEIGHT
                #negru creste
                direction = 1
            
            x_base = PLAY_AREA_END_X - (visual_col * point_width) - (point_width / 2)
            if visual_col >= 6: 
                x_base -= CENTER_BAR_WIDTH
            
            if i in valid_destinations:
                if len(self.game.board[i]) == 1:
                    color = HINT_HIGHLIGHT_COLOR
                else:
                    color = HIGHLIGHT_COLOR
            elif i % 2 == 0:
                color = POINT_COLOR_BLACK
            else:
                color = POINT_COLOR_RED
            
            coords = [x_base - point_width / 2, y_base, x_base + point_width / 2, y_base, x_base, y_tip]
            self.canvas.create_polygon(coords, fill=color)
            self.draw_checkers(i, x_base, y_base, direction)
            self.draw_info_and_bars()

            if not self.game.has_rolled:
                if not (self.ai_match and self.game.turn == 1):
                    self.draw_roll_dice_button()
                    if self.game.cube_value < 64:
                        self.draw_double_button()

    def draw_checkers(self, index, x, y_base, direction):
        """Draws checkers on the board in the initial state"""
        checkers = self.game.board[index]
        if not checkers: 
            return
        
        if checkers[0] == 0:
            color = COLOR_PLAYER0
        else:
            color = COLOR_PLAYER1

        if checkers[0] == 0:
            outline_color = "black"
        else:
            outline_color = "white"
        
        for k in range(len(checkers)):
            if k > 4:
                if checkers[0] == 1:
                    self.canvas.create_text(x, y_curr, text=f"{len(checkers)}", fill="#00ccff", font=("Arial", 14, "bold"))
                else:
                    self.canvas.create_text(x, y_curr, text=f"{len(checkers)}", fill="blue", font=("Arial", 14, "bold"))
                break
                
            diametru = CHECKER_RADIUS * 2 
            if direction == -1: 
                y_curr = y_base - CHECKER_RADIUS - (k * diametru)
            else: 
                y_curr = y_base + CHECKER_RADIUS + (k * diametru)

            width = 1
            if self.selected_point == index and k == len(checkers) - 1:
                outline_color = HIGHLIGHT_COLOR
                width = 3

            self.canvas.create_oval(x - CHECKER_RADIUS, y_curr - CHECKER_RADIUS, x + CHECKER_RADIUS, y_curr + CHECKER_RADIUS, fill=color, outline=outline_color, width=width)

    def draw_dice(self):
        """Draws the dice calling the draw_dice_dots function"""
        y0 = HEIGHT / 2 + (DICE_SIZE / 2)
        y1 = HEIGHT / 2 - (DICE_SIZE / 2)
        center_y = HEIGHT / 2
        first_dice_x0 = 740
        first_dice_x1 = 790
        second_dice_x0 = 800
        second_dice_x1 = 850

        self.canvas.create_rectangle(first_dice_x0, y0, first_dice_x1, y1, fill="white", outline="black")
        self.canvas.create_rectangle(second_dice_x0, y0, second_dice_x1, y1, fill="white", outline="black")

        if not self.game.dice:
            return

        first_dice_center = first_dice_x0 + (first_dice_x1 - first_dice_x0) / 2
        second_dice_center = second_dice_x0 + (second_dice_x1 - second_dice_x0) / 2

        if len(self.game.dice) >= 1:
            self.draw_dice_dots(first_dice_center, center_y, self.game.dice[0])

        if len(self.game.dice) >= 2:
            self.draw_dice_dots(second_dice_center, center_y, self.game.dice[1])

    def draw_dice_dots(self, cx, cy, value):
        """Draws the dots on the dices by calling the get_dice_dots function from logic.py"""
        # if self.game.turn == self.my_player_id:
        dot_offset = DICE_SIZE / 4
        radius = 4
        for px, py in self.game.get_dice_dots(value):
            x = cx + (px * dot_offset)
            y = cy + (py * dot_offset)
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="black")

    def draw_roll_dice_button(self):
        """Draws the button that triggers the dice roll"""
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return
        ROLL_DICE_BTN_RADIUS = 50
        y0 = HEIGHT / 2 + (ROLL_DICE_BTN_RADIUS / 2)
        y1 = HEIGHT / 2 - (ROLL_DICE_BTN_RADIUS / 2)
        self.canvas.create_oval(680, y0, 730, y1, fill="blue", outline="black", tags="btn_roll")
        self.canvas.create_text(705, y0 - 25, fill="white", text="ROLL", font=("Arial", 10, "bold"), tags="btn_roll", activefill="#f08888")

    def draw_double_button(self):
        """Draws the button that triggers doubling the prize"""
        if self.game.turn == self.my_player_id:
            if self.game.has_rolled:
                return

            if self.game.cube_owner != -1 and self.game.cube_owner != self.game.turn:
                return
            if self.ai_match and self.game.turn == 1:
                return

            x0 = WIDTH - 70
            y0 = HEIGHT / 2 + 25
            x1 = WIDTH - 20
            y1 = HEIGHT / 2 - 25

            self.canvas.create_oval(x0, y0, x1, y1, fill="orange", outline="black", tags="btn_double")
            self.canvas.create_text((x0+x1)/2, HEIGHT/2, text="2x", fill="black", activefill="#f63d84", font=("Arial", 14, "bold"), tags="btn_double")

    def draw_done_button(self):
        """Draws the button that triggers the end of current turn"""
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return
        y0 = HEIGHT / 2 + (DONE_BUTTON_SIZE / 2)
        y1 = HEIGHT / 2 - (DONE_BUTTON_SIZE / 2)
        done_btn_x0 = 680
        done_btn_x1 = 730
        self.canvas.create_rectangle(done_btn_x0, y0, done_btn_x1, y1, fill="#24A524", outline="black", tags="btn_done")
        self.canvas.create_text((done_btn_x0 + done_btn_x1)/2, HEIGHT/2, text="DONE", fill="white", font=("Arial", 10, "bold"), tags="btn_done", activefill="#f08888")

    def draw_undo_button(self):
        """Draws the button that triggers undo move"""
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return

        y0 = HEIGHT / 2 + (DONE_BUTTON_SIZE / 2)
        y1 = HEIGHT / 2 - (DONE_BUTTON_SIZE / 2)
        undo_btn_x0 = 600
        undo_btn_x1 = 660

        self.canvas.create_oval(undo_btn_x0, y0, undo_btn_x1, y1, fill="#d1d1d1", outline="black", tags="btn_undo")
        self.canvas.create_text((undo_btn_x0 + undo_btn_x1) / 2, (y0 + y1) /2, text="Undo", activefill="#b77145", font=("Arial", 10, "bold"), tags="btn_undo")

    def draw_save_button(self):
        """Draws the button that triggers storing the game"""
        if not self.is_multiplayer:
            self.canvas.create_rectangle(WIDTH - 110, BORDER_WIDTH / 2 - 15, WIDTH - 40, BORDER_WIDTH / 2 + 15, fill="green")
            self.canvas.create_text(WIDTH - 75, BORDER_WIDTH / 2, text="SAVE", fill="white", activefill="gray", font=("Arial", 14, "bold"), tags="save_btn")

    def draw_menu_button(self):
        """Draws the button that leads you back to the menu"""
        self.canvas.create_rectangle(110, 5, 40, 35, fill="blue")
        self.canvas.create_text(75, BORDER_WIDTH / 2, text="MENU", fill="white", activefill="gray", font=("Arial", 14, "bold"), tags="menu_btn")

    def draw_info_and_bars(self):
        """Draws pop-up with info about the current turn and players that have checkers on the bar"""
        center_x =  WIDTH / 2
        center_y = HEIGHT / 2
        width = 100
        height = 15
        
        if self.game.turn == 0:
            turn_text = "White (P0)"
        else:
            turn_text = "Black (P1)"
        # self.canvas.create_rectangle(center_x-width, center_y-height, center_x+width, center_y+height, fill="#7A711C", outline="black")
        # if self.game.turn == 0:
        #     self.canvas.create_text(center_x, center_y, text=f"Turn: White", font=("Arial", 14, "bold"), fill="white")
        # else:
        #     self.canvas.create_text(center_x, center_y, text=f"Turn: Black", font=("Arial", 14, "bold"), fill="black")

        is_my_turn = (self.is_multiplayer and self.game.turn == self.my_player_id) or (not self.is_multiplayer and self.game.turn == 0)
        if is_my_turn:
            self.canvas.create_rectangle(center_x - width, center_y - height, center_x + width, center_y + height,
                                         fill="#7A711C", outline="black")
            if self.waiting_for_skip:
                    self.canvas.create_text(center_x, center_y, text=f"No moves", font=("Arial", 14, "bold"), fill="red")
                    return
            if self.my_player_id == 0:
                self.canvas.create_text(center_x, center_y, text=f"Your Turn", font=("Arial", 14, "bold"), fill="white")
            else:
                self.canvas.create_text(center_x, center_y, text=f"Your Turn", font=("Arial", 14, "bold"), fill="black")

        for k in range(self.game.bar[0]):
            y_pos = center_y - 100
            self.canvas.create_oval(center_x - CHECKER_RADIUS, y_pos - CHECKER_RADIUS, center_x + CHECKER_RADIUS, y_pos + CHECKER_RADIUS, fill=COLOR_PLAYER0, outline="black")
        if self.game.bar[0] > 0:
            self.canvas.create_text(center_x, center_y - 100, text=f"{self.game.bar[0]}", fill="red", font=("Arial", 14, "bold"))
        for k in range(self.game.bar[1]):
            y_pos = center_y + 100
            self.canvas.create_oval(center_x-CHECKER_RADIUS, y_pos-CHECKER_RADIUS, center_x+CHECKER_RADIUS, y_pos+CHECKER_RADIUS, fill=COLOR_PLAYER1, outline="white")
        if self.game.bar[1] > 0:
            self.canvas.create_text(center_x, center_y + 100, text=f"{self.game.bar[1]}", fill="red", font=("Arial", 14, "bold"))

        if self.game.off[0] > 0:
            y_pos = HEIGHT - 70
            self.canvas.create_text(center_x, y_pos - 40, text="OFF:", fill="black", font=("Arial", 14, "bold"))
            self.canvas.create_oval(center_x - CHECKER_RADIUS, y_pos - CHECKER_RADIUS, center_x + CHECKER_RADIUS, y_pos + CHECKER_RADIUS, 
                fill=COLOR_PLAYER0, outline="black", width=2)
            self.canvas.create_text(center_x, y_pos, text=f"{self.game.off[0]}", fill="black", font=("Arial", 18, "bold"))
        
        if self.game.off[1] > 0:
            y_pos = 100
            self.canvas.create_text(center_x, y_pos - 40, text="OFF:", fill="black", font=("Arial", 14, "bold"))
            self.canvas.create_oval(center_x - CHECKER_RADIUS, y_pos - CHECKER_RADIUS, center_x + CHECKER_RADIUS, y_pos + CHECKER_RADIUS, 
                fill=COLOR_PLAYER1, outline="white", width=2)
            self.canvas.create_text(center_x, y_pos, text=f"{self.game.off[1]}", fill="#ffffff", font=("Arial", 18, "bold"))

        self.draw_score()
        self.draw_save_button()
        self.draw_menu_button()

    def draw_score(self):
        """Draws score on the top border"""
        self.canvas.create_text(WIDTH / 3 + 50, BORDER_WIDTH / 2, text=f"Player 0 (White) - {self.game.match_score[0]}", fill="white", font=("Arial", 14, "bold"))
        self.canvas.create_text(WIDTH / 2 + 105, BORDER_WIDTH / 2, text=f"{self.game.match_score[1]} - Player 1 (Black)", fill="white", font=("Arial", 14, "bold"))

    def draw_final_of_the_match(self, winner):
        """Draws the pop-up that announces the final of the match"""
        if self.is_multiplayer:
            did_i_win = (winner == self.my_player_id)
            win_text = "You win!"
            lose_text = "You lose!"
        else:
            did_i_win = (winner == 0)
            win_text = "You lose!"
            lose_text = "You win!"

        if did_i_win:
            game_over_text = win_text
            winner_color = "#6aff8a"
        else:
            game_over_text = lose_text
            winner_color = "#ff5656"

        self.canvas.create_rectangle(WIDTH / 2 - 220, HEIGHT / 2 - 120, WIDTH / 2 + 220, HEIGHT / 2 + 120, fill=winner_color, outline="black", width=2)
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 60, text=f"{game_over_text}", fill="black", font=("Arial", 36, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 15, text="Score", fill="#00095e", font=("Arial", 18, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 20, text=f"{self.game.match_score[0]} - {self.game.match_score[1]}", fill="#00095e", font=("Arial", 18, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 55, text=f"Player {self.game.winner} reached 5 points! The match is over", fill="black", font=("Arial", 14, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 90, text="Go back to menu", fill="black", activefill="#ff1f1f", font=("Arial", 18, "bold"), tags="menu_btn")

    def draw_game_over(self, winner):
        """Draws the pop-ups that announces the final of the game"""
        if self.is_multiplayer:
            did_i_win = (winner == self.my_player_id)
            win_text = "You win!"
            lose_text = "You lose!"
        else:
            did_i_win = (winner == 0)
            win_text = "You lose!"
            lose_text = "You win!"

        if did_i_win:
            game_over_text = win_text
            winner_color = "#6aff8a"
        else:
            game_over_text = lose_text
            winner_color = "#ff5656"
            
        self.canvas.create_rectangle(WIDTH / 2 - 130, HEIGHT / 2 - 120, WIDTH / 2 + 130, HEIGHT / 2 + 120, fill=winner_color, outline="black", width=2)
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 60, text=f"{game_over_text}", fill="black", font=("Arial", 36, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 15, text="Score", fill="#00095e", font=("Arial", 18, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 20, text=f"{self.game.match_score[0]} - {self.game.match_score[1]}", fill="#00095e", font=("Arial", 18, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 60, text="Play Again", fill="black", activefill="#ff1f1f", font=("Arial", 18, "bold"), tags="play_again")

    def draw_doubling_cube(self):
        """Draws the doubling cube"""
        x_pos = 21
        
        if self.game.cube_owner == -1:
            y_pos = HEIGHT / 2  
        elif self.game.cube_owner == 0: 
            y_pos = HEIGHT - 100
        else: 
            y_pos = 100
        size = 18
        
        self.canvas.create_rectangle(x_pos - size, y_pos - size, x_pos + size, y_pos + size, fill="#f0e68c", outline="black", width=3, tags="cube_visual")
        self.canvas.create_text(x_pos, y_pos, text=str(self.game.cube_value), font=("Arial", 20, "bold"), fill="black", tags="cube_visual")

    def get_index_from_coords(self, x, y):
        """
        Translates pixel coordinates (x, y) into a logical board index.
        Returns:
            int or None: The board index (0-23), Bar, Off, or None if out of bounds.
        """
        if LEFT_BOARD_END_X < x < RIGHT_BOARD_START_X:
            center_x = WIDTH / 2
            #verific daca alb incearca sa scoata piese
            if y > HEIGHT - 150:
                if self.game.turn == 0:
                    return -2
            #verific daca negru incearca sa scoata piese
            if y < 150:
                if self.game.turn == 1:
                    return 25
            if self.game.bar[self.game.turn] > 0:
                if self.game.turn == 0:
                    piece_y = HEIGHT / 2 - 100
                    bar_index = 24
                else:
                    piece_y = HEIGHT / 2 + 100
                    bar_index = -1
                
                if abs(x - center_x) <= CHECKER_RADIUS and abs(y - piece_y) <= CHECKER_RADIUS:
                    return bar_index
            return None

        if not (PLAY_AREA_START_Y <= y <= PLAY_AREA_END_Y):
            return None
        
        if x < PLAY_AREA_START_X or x > PLAY_AREA_END_X:
            return None

        normalized_x = x - PLAY_AREA_START_X
        if x > RIGHT_BOARD_START_X: 
            normalized_x = normalized_x - CENTER_BAR_WIDTH
        elif x > LEFT_BOARD_END_X:
            return None

        point_width = ((PLAY_AREA_END_X - PLAY_AREA_START_X) - CENTER_BAR_WIDTH) / 12
        col = int(normalized_x / point_width)
        col = max(0, min(11, col))
        visual_col = 11 - col

        if y > HEIGHT / 2: 
            return visual_col
        else:                    
            return 23 - visual_col

    def on_press(self, event):
        """
        Handles mouse button press events.

        Detects clicks on:
        - Menu buttons (PvP, AI, Load)
        - Game controls (Roll, Done, Undo, Save, Double)
        - Checkers (to initiate a drag or select a piece)
        """
        if self.menu:
            clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item in clicked:
                tags = self.canvas.gettags(item)
                if "menu_pvp" in tags:
                    self.start_game(ai_mode = False)
                    return
                elif "menu_ai" in tags:
                    self.start_game(ai_mode = True)
                    return
                elif "menu_load" in tags:
                    filename = "last_game.json"
                    if not os.path.exists(filename):
                        messagebox.showerror("No saved game was found")
                        return
                    ai_status = self.game.load_game(filename)
                    if ai_status is not None:
                        self.menu = False
                        self.ai_match = ai_status
                        self.draw_board()
                        messagebox.showinfo("Success", "Last game session restored")
                    else:
                        messagebox.showerror("Error", "Corrupted save file")
                    return
                elif "menu_online" in tags:
                    if not self.sio or not getattr(self.sio, 'connected', False):
                        messagebox.showerror("Connection Error", "Unable to connect to the server for online play. Please check your connection and try again.")
                        return
                    self.menu = False
                    self.is_multiplayer = True
                    self.ai_match = False
                    if self.sio:
                        self.sio.emit('join_matchmaking')
                    self.canvas.delete("all")
                    self.canvas.create_text(WIDTH / 2, HEIGHT / 2, text="Waiting for opponent...", fill="white",
                                            font=("Arial", 24))
                    return
            return
        
        #ignor click urile mele daca e tura ai ului
        if self.ai_match and self.game.turn == 1:
            return
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return

        clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item in clicked:
            tags = self.canvas.gettags(item)
            if "btn_roll" in tags:
                if self.is_multiplayer:
                    self.sio.emit('roll_dice')
                else:
                    self.game.roll_dice()
                    self.draw_board()
                    if not self.game.any_valid_moves():
                        print("No moves possible. Waiting 1.5s...")

                        def handle_stuck_player():
                            self.game.dice = []
                            self.game.switch_turn()
                            self.draw_board()

                            if self.ai_match and self.game.turn == 1:
                                self.root.after(1000, self.run_ai_turn)

                        self.root.after(1500, handle_stuck_player)
                    return

            elif "btn_done" in tags:
                if self.is_multiplayer:
                    self.sio.emit('end_turn')
                else:
                    self.game.switch_turn()
                    self.draw_board()
                    if self.ai_match and self.game.turn == 1:
                        self.root.after(1000, self.run_ai_turn)
                    return

            elif "play_again" in tags:
                if self.is_multiplayer:
                    self.sio.emit("play_again")
                else:
                    self.game.reset_game()
                    self.reset_selection()
                    return

            elif "save_btn" in tags:
                if self.is_multiplayer:
                    messagebox.showinfo("Info", "You cannot save online matches.")
                    return

                confirm = messagebox.askyesno("Confirm Save", "Are you sure you want to save this game? Maybe you'll want to continue later.")
                if confirm:
                    success = self.game.save_game("last_game.json", self.ai_match)
                    if success:
                        messagebox.showinfo("Saved", "Game state saved")
                        self.menu = True
                        self.draw_menu()
                    else:
                        messagebox.showerror("Error", "Could not save the game")
                return
            elif "menu_btn" in tags:
                if self.is_multiplayer:
                    confirm = messagebox.askyesno("Leave Match",
                                                  "Are you sure you want to leave? You will forfeit the current online match.")
                    if confirm:
                        self.sio.emit('leave_match')
                        self.is_multiplayer = False
                        self.menu = True
                        self.draw_menu()
                else:
                    if not self.game.game_over:
                        confirm = messagebox.askyesno("Navigate to menu",
                                                      "Are you sure you want to go to the menu? If you want to continue the game later, you must save it first.")
                        if confirm:
                            self.menu = True
                            self.draw_menu()
                    else:
                        self.menu = True
                        self.draw_menu()
                    return
            elif "btn_double" in tags:
                if self.is_multiplayer:
                    self.sio.emit('offer_double')
                else:
                    current_player = self.game.turn
                    opponent = 1 - current_player
                    new_cube_value = self.game.cube_value * 2

                    if self.ai_match and current_player == 0:
                        # ai ul accepta mereu dublajul
                        messagebox.showinfo("Double Offered", f"AI accepts the double offer")
                        accepted = True
                    else:
                        accepted = messagebox.askyesno("Double Offered", f"Player {opponent}, do you accept the double to {new_cube_value}?\n\n"f"YES = Continue game with stakes x{new_cube_value}\n"f"NO = Resign game and lose {self.game.cube_value} points")

                    if accepted:
                        self.game.cube_value = new_cube_value
                        self.game.cube_owner = opponent
                        self.draw_board()
                    else:
                        self.game.winner = current_player
                        self.game.end_game()
                        if self.game.match_score[0] >= 5 or self.game.match_score[1] >= 5:
                            self.draw_final_of_the_match(self.game.winner)
                        else:
                            self.draw_game_over(self.game.winner)

                    return
            elif "btn_undo" in tags:
                if self.is_multiplayer:
                    self.sio.emit('undo_move')
                else:
                    if self.game.undo_move():
                        self.reset_selection()
                        self.draw_board()
                    return

        index = self.get_index_from_coords(event.x, event.y)

        if index is None:
            self.reset_selection()
            return
        
        if self.selected_point is not None and index is not None:
            for move in self.valid_moves:
                if move[0] == index:
                    self.game.move_piece(self.selected_point, index, move[1])
                    self.reset_selection()
                    self.draw_board()
                    return

        if index is not None:
            moves = self.game.get_valid_moves(index)
            if moves:
                self.selected_point = index
                self.drag_start_index = index
                self.valid_moves = moves

                start_x = event.x
                start_y = event.y

                if index == 24 or index == -1:
                    start_x = WIDTH / 2
                    if index == 24:
                        start_y = HEIGHT / 2 - 100
                    else:
                        start_y = HEIGHT / 2 + 100
                
                if self.game.turn == 0:
                    color = COLOR_PLAYER0
                else:
                    color = COLOR_PLAYER1
                self.dragged_piece_id = self.canvas.create_oval(event.x - CHECKER_RADIUS, event.y - CHECKER_RADIUS, event.x + CHECKER_RADIUS, event.y + CHECKER_RADIUS,
                    fill=color, outline="gold", width=2, tag="drag_piece")
                self.canvas.tag_raise("drag_piece")
                
                self.draw_board()
                self.dragged_piece_id = self.canvas.create_oval(
                    event.x - CHECKER_RADIUS, event.y - CHECKER_RADIUS, event.x + CHECKER_RADIUS, event.y + CHECKER_RADIUS, fill=color, outline="gold", width=2, tag="drag_piece")
            else:
                self.reset_selection()

    def on_drag(self, event):
        if self.dragged_piece_id:
            self.canvas.coords(self.dragged_piece_id, event.x - CHECKER_RADIUS, event.y - CHECKER_RADIUS, event.x + CHECKER_RADIUS, event.y + CHECKER_RADIUS)

    def on_release(self, event):
        if self.menu:
            return

        if self.ai_match and self.game.turn == 1:
            return
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return

        if self.dragged_piece_id:
            self.canvas.delete(self.dragged_piece_id)
            self.dragged_piece_id = None

            target_index = self.get_index_from_coords(event.x, event.y)

            if target_index is not None and target_index != self.drag_start_index:
                for move in self.valid_moves:
                    if move[0] == target_index:
                        if self.is_multiplayer:
                            print(f"Sending move to the server: {self.drag_start_index} -> {target_index}")
                            self.sio.emit('make_move', {
                                'start': self.drag_start_index,
                                'target': target_index,
                                'used_dice': move[1]
                            })
                            self.reset_selection()
                        else:
                            self.game.move_piece(self.drag_start_index, target_index, move[1])
                            self.reset_selection()
                            self.draw_board()

                            if self.game.game_over:
                                if self.game.match_score[0] >= 5 or self.game.match_score[1] >= 5:
                                    self.draw_final_of_the_match(self.game.winner)
                                else:
                                    self.draw_game_over(self.game.winner)
                        break

            self.drag_start_index = None

            if not self.is_multiplayer:
                self.draw_board()

    def reset_selection(self):
        """Resets the current selection"""
        self.selected_point = None
        self.valid_moves = []
        self.draw_board()

    def run_ai_turn(self):
        """
        Runs the AI turn:
        1. Rolls dice.
        2. Choses and performs a random move
        4. Chains multiple moves if dice remain
        """
        #verific daca e tura ai
        if self.game.turn != 1:
            return
        
        if not self.game.has_rolled:
            self.game.roll_dice()
            self.draw_board()
            #freeze ca sa vada playeru ce zar a dat ai ul
            self.root.after(1000, self.ai_perform_move)
        else:
            self.ai_perform_move()

    def ai_perform_move(self):
            """Performs move chosen by get_ai_move() function from logic"""
            move = self.game.get_ai_move(self.ai_model)
            if move:
                start, target, path = move
                print(f"AI moves from {start} to {target}")
                self.game.move_piece(start, target, path)
                self.draw_board()

                if self.game.game_over:
                    if self.game.match_score[0] >= 5 or self.game.match_score[1] >= 5:
                        self.draw_final_of_the_match(self.game.winner)
                    else:
                        self.draw_game_over(self.game.winner)

                if self.game.dice and self.game.any_valid_moves():
                    self.root.after(800, self.ai_perform_move)
                else:
                    self.root.after(1000, self.ai_end_turn)
            else:
                print(f"No valid moves for AI. Next turn")
                self.root.after(1000, self.ai_end_turn)

    def ai_end_turn(self):
        """Ends AI turn by automatically switching it and calls the draw_board() method"""
        self.game.switch_turn()
        self.draw_board()