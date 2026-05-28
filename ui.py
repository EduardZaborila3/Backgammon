import tkinter as tk

from auth import is_new_player
from logic import BackgammonLogic
import random
from constants import *
import json
from tkinter import messagebox
import os
import auth

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
    def __init__(self, root, auth_callback=None):
        """Initializes the UI components and binds event listeners."""
        self.game = BackgammonLogic()
        self.root = root

        self.auth_callback = auth_callback

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
        self.ai_difficulty = "hard"

        self.show_split_dice = False
        self._multiplayer_split_done = False

        if is_new_player():
            self.auth_screen = True
            self.menu = False
            self.draw_auth_menu()
        else:
            self.auth_screen = False
            self.menu = True
            self.draw_menu()
            if self.auth_callback:
                self.auth_callback("guest")

        self.waiting_for_skip = False

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def draw_auth_menu(self):
        """Draws the initial authentication screen"""
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#994f0a")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 150, text="Welcome to Backgammon", fill="#CDCDCD",
                                font=("Arial", 36, "bold"))

        # Guest btn
        self.canvas.create_rectangle(WIDTH / 2 - 150, HEIGHT / 2 - 50, WIDTH / 2 + 150, HEIGHT / 2 + 10, fill="#3f1405",
                                     outline="white", width=2, tags="auth_guest")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text="Play as Guest", fill="white", activefill="#f9fc4f",
                                font=("Arial", 16, "bold"), tags="auth_guest")

        # Account btn
        self.canvas.create_rectangle(WIDTH / 2 - 150, HEIGHT / 2 + 40, WIDTH / 2 + 150, HEIGHT / 2 + 100,
                                     fill="#1c5c16", outline="white", width=2, tags="auth_account")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 70, text="Login / Register", fill="white", activefill="#f9fc4f",
                                font=("Arial", 16, "bold"), tags="auth_account")

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

    def draw_difficulty_menu(self):
        """Draws the sub-menu for AI difficulty selection"""
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#994f0a")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 200, text="Select AI Difficulty", fill="#CDCDCD",
                                font=("Arial", 36, "bold"))

        # Easy btn
        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2 - 100, WIDTH / 2 + 100, HEIGHT / 2 - 50,
                                     fill="#24A524", outline="white", width=2, tags="btn_diff_easy")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 75, text="Easy", fill="white", activefill="black",
                                font=("Arial", 16, "bold"), tags="btn_diff_easy")

        # Medium btn
        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2 - 25, WIDTH / 2 + 100, HEIGHT / 2 + 25,
                                     fill="#d1a102", outline="white", width=2, tags="btn_diff_medium")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2, text="Medium", fill="white", activefill="black",
                                font=("Arial", 16, "bold"), tags="btn_diff_medium")

        # hard btn
        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2 + 50, WIDTH / 2 + 100, HEIGHT / 2 + 100,
                                     fill="#a52424", outline="white", width=2, tags="btn_diff_hard")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 75, text="Hard", fill="white", activefill="black",
                                font=("Arial", 16, "bold"), tags="btn_diff_hard")

        # back btn
        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2 + 150, WIDTH / 2 + 100, HEIGHT / 2 + 200,
                                     fill="#3f1405", outline="white", width=2, tags="btn_diff_back")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 175, text="Back to Menu", fill="#aaaaaa",
                                activefill="#f9fc4f", font=("Arial", 16, "bold"), tags="btn_diff_back")

    def start_game(self, ai_mode = False, ai_difficulty = "hard"):
        """
        Starts the game
        Args:
            ai_mode: A flag that indicates if the game is PvP or PvAI
        """
        self.menu = False
        self.ai_match = ai_mode
        self.ai_difficulty = ai_difficulty
        print(f"Game starting in ai mode: {ai_mode}")
        self.game = BackgammonLogic()
        self.ai_model = None

        if ai_mode:
            if self.sio and getattr(self.sio, 'connected', False):
                self.sio.emit('start_ai_match')
            else:
                messagebox.showerror("Error", "You have to be connected to the server to play with AI")
                self.menu = True
                self.draw_menu()
                return

        self.show_split_dice = True
        self.draw_board()
        self.root.after(3000, self.end_split_dice)

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

        is_opening_roll = not self.game.history and not state.get('history', []) and sum(self.game.off) == 0 and sum(self.game.bar) == 0 and self.game.has_rolled

        if is_opening_roll and not self._multiplayer_split_done:
            self.show_split_dice = True
            self._multiplayer_split_done = True
            self.root.after(3000, self.end_split_dice)

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
                self.draw_game_over(self.game.winner, win_conditions="normal")
                self.sio.emit('game_over', {'winner': self.game.winner})

    def end_split_dice(self):
        """Ends dice splitting and brings the dice side by side in the starting player side of the table"""
        if self.menu:
            return
        self.show_split_dice = False
        self.draw_board()
        if self.ai_match and self.game.turn == 1:
            self.root.after(500, self.ai_perform_move)

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

        for visual_index in range(24):
            server_index = self.get_server_index(visual_index)

            if visual_index < 12:
                visual_col = visual_index
                y_base = PLAY_AREA_END_Y
                y_tip = PLAY_AREA_END_Y - TRIANGLE_HEIGHT
                direction = -1
            else:
                visual_col = 23 - visual_index
                y_base = PLAY_AREA_START_Y
                y_tip = PLAY_AREA_START_Y + TRIANGLE_HEIGHT
                direction = 1

            x_base = PLAY_AREA_END_X - (visual_col * point_width) - (point_width / 2)
            if visual_col >= 6:
                x_base -= CENTER_BAR_WIDTH

            if server_index in valid_destinations:
                if len(self.game.board[server_index]) == 1:
                    color = HINT_HIGHLIGHT_COLOR
                else:
                    color = HIGHLIGHT_COLOR
            elif visual_index % 2 == 0:
                color = POINT_COLOR_BLACK
            else:
                color = POINT_COLOR_RED

            coords = [x_base - point_width / 2, y_base, x_base + point_width / 2, y_base, x_base, y_tip]
            self.canvas.create_polygon(coords, fill=color)

            self.draw_checkers(server_index, x_base, y_base, direction)

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
        """Draws the dice. Handles left/right positioning and opening roll split."""
        if not self.game.dice:
            return

        y0 = HEIGHT / 2 + (DICE_SIZE / 2)
        y1 = HEIGHT / 2 - (DICE_SIZE / 2)
        center_y = HEIGHT / 2

        my_id = self.my_player_id if self.is_multiplayer else 0
        opp_id = 1 - my_id

        if self.show_split_dice and len(self.game.dice) == 2:
            winner = self.game.turn
            winner_die = self.game.dice[0]
            loser_die = self.game.dice[1]

            if winner == my_id:
                my_die = winner_die
                opp_die = loser_die
            else:
                my_die = loser_die
                opp_die = winner_die

            opp_x0 = 160
            self.canvas.create_rectangle(opp_x0, y0, opp_x0 + DICE_SIZE, y1, fill="white", outline="black")
            self.draw_dice_dots(opp_x0 + (DICE_SIZE / 2), center_y, opp_die)

            my_x0 = 740
            self.canvas.create_rectangle(my_x0, y0, my_x0 + DICE_SIZE, y1, fill="white", outline="black")
            self.draw_dice_dots(my_x0 + (DICE_SIZE / 2), center_y, my_die)

        else:
            if self.game.turn == my_id:
                base_x = 740
            else:
                base_x = 90

            num_dice_to_draw = min(2, len(self.game.dice))

            for i in range(num_dice_to_draw):
                x0 = base_x + i * 60
                self.canvas.create_rectangle(x0, y0, x0 + DICE_SIZE, y1, fill="white", outline="black")
                self.draw_dice_dots(x0 + (DICE_SIZE / 2), center_y, self.game.dice[i])

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
        if self.game.game_over:
            return
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return
        if not self.is_multiplayer and self.ai_match and self.game.turn == 1:
            return

        ROLL_DICE_BTN_RADIUS = 50
        y0 = HEIGHT / 2 - (ROLL_DICE_BTN_RADIUS / 2)
        y1 = HEIGHT / 2 + (ROLL_DICE_BTN_RADIUS / 2)

        self.canvas.create_oval(680, y0, 730, y1, fill="blue", outline="black", tags="btn_roll")
        self.canvas.create_text(705, HEIGHT / 2, fill="white", text="ROLL", font=("Arial", 10, "bold"), tags="btn_roll",
                                activefill="#f08888")

    def draw_double_button(self):
        """Draws the button that triggers doubling the prize"""
        if self.game.game_over:
            return
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return
        if not self.is_multiplayer and self.ai_match and self.game.turn == 1:
            return
        if self.game.has_rolled:
            return
        if self.game.cube_owner != -1 and self.game.cube_owner != self.game.turn:
            return

        x0 = WIDTH - 70
        x1 = WIDTH - 20
        y0 = HEIGHT / 2 - 25
        y1 = HEIGHT / 2 + 25

        self.canvas.create_oval(x0, y0, x1, y1, fill="orange", outline="black", tags="btn_double")
        self.canvas.create_text((x0 + x1) / 2, HEIGHT / 2, text="2x", fill="black", activefill="#f63d84",
                                font=("Arial", 14, "bold"), tags="btn_double")

    def draw_done_button(self):
        """Draws the button that triggers the end of current turn"""
        if self.game.game_over:
            return
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return
        if not self.is_multiplayer and self.ai_match and self.game.turn == 1:
            return

        y0 = HEIGHT / 2 - (DONE_BUTTON_SIZE / 2)
        y1 = HEIGHT / 2 + (DONE_BUTTON_SIZE / 2)
        done_btn_x0 = 680
        done_btn_x1 = 730

        self.canvas.create_rectangle(done_btn_x0, y0, done_btn_x1, y1, fill="#24A524", outline="black", tags="btn_done")
        self.canvas.create_text((done_btn_x0 + done_btn_x1) / 2, HEIGHT / 2, text="DONE", fill="white",
                                font=("Arial", 10, "bold"), tags="btn_done", activefill="#f08888")

    def draw_undo_button(self):
        """Draws the button that triggers undo move"""
        if self.game.game_over:
            return
        if self.is_multiplayer and self.game.turn != self.my_player_id:
            return
        if not self.is_multiplayer and self.ai_match and self.game.turn == 1:
            return

        y0 = HEIGHT / 2 - (DONE_BUTTON_SIZE / 2)
        y1 = HEIGHT / 2 + (DONE_BUTTON_SIZE / 2)
        undo_btn_x0 = 600
        undo_btn_x1 = 660

        self.canvas.create_oval(undo_btn_x0, y0, undo_btn_x1, y1, fill="#d1d1d1", outline="black", tags="btn_undo")
        self.canvas.create_text((undo_btn_x0 + undo_btn_x1) / 2, HEIGHT / 2, text="Undo", activefill="#b77145",
                                font=("Arial", 10, "bold"), tags="btn_undo")

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

        self.canvas.create_rectangle(center_x - width, center_y - height, center_x + width, center_y + height,
                                     fill="#7A711C", outline="black")

        if self.waiting_for_skip:
            self.canvas.create_text(center_x, center_y, text="No moves", font=("Arial", 14, "bold"), fill="red")
        else:
            if self.is_multiplayer:
                if self.game.turn == self.my_player_id:
                    text_color = "white" if self.my_player_id == 0 else "black"
                    self.canvas.create_text(center_x, center_y, text="Your Turn", font=("Arial", 14, "bold"),
                                            fill=text_color)
                else:
                    text_color = "black" if self.my_player_id == 0 else "white"
                    self.canvas.create_text(center_x, center_y, text="Opponent's Turn", font=("Arial", 14, "bold"),
                                            fill=text_color)

            elif self.ai_match:
                if self.game.turn == 0:
                    self.canvas.create_text(center_x, center_y, text="Your Turn", font=("Arial", 14, "bold"),
                                            fill="white")
                else:
                    self.canvas.create_text(center_x, center_y, text="AI's Turn", font=("Arial", 14, "bold"),
                                            fill="black")

            else:
                if self.game.turn == 0:
                    self.canvas.create_text(center_x, center_y, text="Turn: White", font=("Arial", 14, "bold"),
                                            fill="white")
                else:
                    self.canvas.create_text(center_x, center_y, text="Turn: Black", font=("Arial", 14, "bold"),
                                            fill="black")

        my_id = self.my_player_id if self.is_multiplayer else 0
        opp_id = 1 - my_id

        # opponent bar always up
        y_pos_opp = center_y - 100
        for k in range(self.game.bar[opp_id]):
            color = COLOR_PLAYER0 if opp_id == 0 else COLOR_PLAYER1
            outline = "black" if opp_id == 0 else "white"
            self.canvas.create_oval(center_x - CHECKER_RADIUS, y_pos_opp - CHECKER_RADIUS, center_x + CHECKER_RADIUS,
                                    y_pos_opp + CHECKER_RADIUS, fill=color, outline=outline)
        if self.game.bar[opp_id] > 0:
            self.canvas.create_text(center_x, y_pos_opp, text=f"{self.game.bar[opp_id]}", fill="red",
                                    font=("Arial", 14, "bold"))

        # my bar always down
        y_pos_my = center_y + 100
        for k in range(self.game.bar[my_id]):
            color = COLOR_PLAYER0 if my_id == 0 else COLOR_PLAYER1
            outline = "black" if my_id == 0 else "white"
            self.canvas.create_oval(center_x - CHECKER_RADIUS, y_pos_my - CHECKER_RADIUS, center_x + CHECKER_RADIUS,
                                    y_pos_my + CHECKER_RADIUS, fill=color, outline=outline)
        if self.game.bar[my_id] > 0:
            self.canvas.create_text(center_x, y_pos_my, text=f"{self.game.bar[my_id]}", fill="red",
                                    font=("Arial", 14, "bold"))

        # opponent house up
        if self.game.off[opp_id] > 0:
            y_pos_opp_off = 100
            color = COLOR_PLAYER0 if opp_id == 0 else COLOR_PLAYER1
            outline = "black" if opp_id == 0 else "white"
            text_fill = "black" if opp_id == 0 else "#ffffff"
            self.canvas.create_text(center_x, y_pos_opp_off - 40, text="OFF:", fill="black", font=("Arial", 14, "bold"))
            self.canvas.create_oval(center_x - CHECKER_RADIUS, y_pos_opp_off - CHECKER_RADIUS,
                                    center_x + CHECKER_RADIUS, y_pos_opp_off + CHECKER_RADIUS, fill=color,
                                    outline=outline, width=2)
            self.canvas.create_text(center_x, y_pos_opp_off, text=f"{self.game.off[opp_id]}", fill=text_fill,
                                    font=("Arial", 18, "bold"))

        # my house down
        if self.game.off[my_id] > 0:
            y_pos_my_off = HEIGHT - 70
            color = COLOR_PLAYER0 if my_id == 0 else COLOR_PLAYER1
            outline = "black" if my_id == 0 else "white"
            text_fill = "black" if my_id == 0 else "#ffffff"
            self.canvas.create_text(center_x, y_pos_my_off - 40, text="OFF:", fill="black", font=("Arial", 14, "bold"))
            self.canvas.create_oval(center_x - CHECKER_RADIUS, y_pos_my_off - CHECKER_RADIUS, center_x + CHECKER_RADIUS,
                                    y_pos_my_off + CHECKER_RADIUS, fill=color, outline=outline, width=2)
            self.canvas.create_text(center_x, y_pos_my_off, text=f"{self.game.off[my_id]}", fill=text_fill,
                                    font=("Arial", 18, "bold"))

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
            my_id = self.my_player_id
        else:
            my_id = 0
        opp_id = 1 - my_id

        if self.is_multiplayer:
            did_i_win = (winner == self.my_player_id)
            win_text = "You win!"
            lose_text = "You lose!"
        else:
            did_i_win = (winner == 0)
            win_text = "You win!"
            lose_text = "You lose!"

        if did_i_win:
            game_over_text = win_text
            winner_color = "#6aff8a"
        else:
            game_over_text = lose_text
            winner_color = "#ff5656"

        self.canvas.create_rectangle(WIDTH / 2 - 220, HEIGHT / 2 - 120, WIDTH / 2 + 220, HEIGHT / 2 + 120, fill=winner_color, outline="black", width=2)
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 60, text=f"{game_over_text}", fill="black", font=("Arial", 36, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 15, text="Score", fill="#00095e", font=("Arial", 18, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 20, text=f"{self.game.match_score[my_id]} - {self.game.match_score[opp_id]}", fill="#00095e", font=("Arial", 18, "bold"))
        if self.game.winner == my_id:
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 55,
                                    text=f"You reached 5 points! The match is over", fill="black",
                                    font=("Arial", 14, "bold"))
        else:
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 55,
                                    text=f"Opponent reached 5 points! The match is over", fill="black",
                                    font=("Arial", 14, "bold"))

        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 90, text="Go back to menu", fill="black", activefill="#ff1f1f", font=("Arial", 18, "bold"), tags="menu_btn")

    def handle_double_offer(self, data):
        """Outputs the doubling offer from the opponent cleanly"""

        def display_popup():
            new_value = data['new_value']

            accepted = messagebox.askyesno(
                "Double Offered",
                f"Your opponent offered to double the stakes to {new_value}.\n\n"
                f"YES = Continue game with stakes x{new_value}\n"
                f"NO = Resign game and lose {self.game.cube_value} points",
                parent=self.root
            )
            self.root.update()
            self.sio.emit('respond_double', {'accept': accepted})
        self.root.after(10, display_popup)

    def draw_game_over(self, winner, win_conditions="normal"):
        """Draws the pop-ups that announces the final of the game"""
        if self.is_multiplayer:
            my_id = self.my_player_id
        else:
            my_id = 0
        opp_id = 1 - my_id

        if self.is_multiplayer:
            did_i_win = (winner == self.my_player_id)
            win_text = "You win!"
            lose_text = "You lose!"
        else:
            did_i_win = (winner == 0)
            win_text = "You win!"
            lose_text = "You lose!"

        if did_i_win:
            game_over_text = win_text
            winner_color = "#6aff8a"
        else:
            game_over_text = lose_text
            winner_color = "#ff5656"
            
        self.canvas.create_rectangle(WIDTH / 2 - 130, HEIGHT / 2 - 120, WIDTH / 2 + 130, HEIGHT / 2 + 120, fill=winner_color, outline="black", width=2)
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 60, text=f"{game_over_text}", fill="black", font=("Arial", 36, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 15, text="Score", fill="#00095e", font=("Arial", 18, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 20, text=f"{self.game.match_score[my_id]} - {self.game.match_score[opp_id]}", fill="#00095e", font=("Arial", 18, "bold"))
        if win_conditions != "leave":
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 60, text="Play Again", fill="black", activefill="#ff1f1f",
                                    font=("Arial", 18, "bold"), tags="play_again")
        else:
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 60, text="Opponent disconnected", fill="red", font=("Arial", 16, "bold"))

    def draw_doubling_cube(self):
        """Draws the doubling cube"""
        x_pos = 21
        my_id = self.my_player_id if self.is_multiplayer else 0

        if self.game.cube_owner == -1:
            y_pos = HEIGHT / 2
        elif self.game.cube_owner == my_id:
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
        my_id = self.my_player_id if self.is_multiplayer else 0
        opp_id = 1 - my_id

        if LEFT_BOARD_END_X < x < RIGHT_BOARD_START_X:
            center_x = WIDTH / 2

            if y > HEIGHT - 150:
                if self.game.turn == my_id:
                    return -2 if my_id == 0 else 25

            if y < 150:
                if self.game.turn == opp_id:
                    return -2 if opp_id == 0 else 25

            if self.game.bar[self.game.turn] > 0:
                if self.game.turn == my_id:
                    piece_y = HEIGHT / 2 + 100
                    bar_index = 24 if my_id == 0 else -1
                else:
                    piece_y = HEIGHT / 2 - 100
                    bar_index = 24 if opp_id == 0 else -1

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
            visual_index = visual_col
        else:
            visual_index = 23 - visual_col

        return self.get_server_index(visual_index)

    def on_press(self, event):
        """
        Handles mouse button press events.

        Detects clicks on:
        - Menu buttons (PvP, AI, Load)
        - Game controls (Roll, Done, Undo, Save, Double)
        - Checkers (to initiate a drag or select a piece)
        """
        if self.auth_screen:
            clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item in clicked:
                tags = self.canvas.gettags(item)
                if "auth_guest" in tags:
                    self.auth_screen = False
                    self.menu = True
                    self.draw_menu()
                    if self.auth_callback:
                        self.auth_callback("guest")
                    return
                elif "auth_account" in tags:
                    messagebox.showinfo("Info", "Auth logic is going to be implemented!")
            return

        if self.menu:
            clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item in clicked:
                tags = self.canvas.gettags(item)
                if "menu_pvp" in tags:
                    self.start_game(ai_mode = False)
                    return
                elif "menu_ai" in tags:
                    self.draw_difficulty_menu()
                    return
                elif "btn_diff_easy" in tags:
                    self.start_game(ai_mode=True, ai_difficulty="easy")
                    return
                elif "btn_diff_medium" in tags:
                    self.start_game(ai_mode=True, ai_difficulty="medium")
                    return
                elif "btn_diff_hard" in tags:
                    self.start_game(ai_mode=True, ai_difficulty="hard")
                    return
                elif "btn_diff_back" in tags:
                    self.draw_menu()
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

        clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        #ignor click urile mele daca e tura ai ului
        for item in clicked:
            tags = self.canvas.gettags(item)
            if "menu_btn" in tags:
                if self.is_multiplayer:
                    if self.game.game_over:
                        self.is_multiplayer = False
                        self.menu = True
                        self.draw_menu()
                    else:
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

        if not self.game.game_over:
            if self.ai_match and self.game.turn == 1:
                return
            if self.is_multiplayer and self.game.turn != self.my_player_id:
                return
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
                    self._multiplayer_split_done = False
                    self.canvas.delete("play_again")
                    self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 60, text="Waiting for opponent...", fill="yellow",
                                            font=("Arial", 16, "bold"), tags="waiting_text")
                    self.root.update()
                    self.sio.emit("request_play_again")
                else:
                    self.game.reset_game()
                    self.reset_selection()
                    self.show_split_dice = True
                    self.draw_board()
                    self.root.after(2000, self.end_split_dice)
                    return

            elif "btn_accept_play" in tags:
                self._multiplayer_split_done = False
                self.canvas.delete("play_again_popup")
                self.sio.emit('respond_play_again', {'accept': True})
                return

            elif "btn_decline_play" in tags:
                self.canvas.delete("play_again_popup")
                self.sio.emit('respond_play_again', {'accept': False})
                self.is_multiplayer = False
                self.menu = True
                self.draw_menu()
                return

            elif "btn_ok_declined" in tags:
                self.canvas.delete("declined_popup")
                self.is_multiplayer = False
                self.menu = True
                self.draw_menu()
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
                    self.canvas.delete("btn_double")
                    self.canvas.delete("btn_roll")
                    self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 60, text="Waiting for opponent...", fill="yellow",
                                            font=("Arial", 14, "bold"), tags="double_wait_text")
                    self.root.update()

                    self.sio.emit('offer_double')
                    return
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

        if self.game.game_over:
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
                    if not self.is_multiplayer and self.game.game_over:
                        if self.game.match_score[0] >= 5 or self.game.match_score[1] >= 5:
                            self.draw_final_of_the_match(self.game.winner)
                        else:
                            self.draw_game_over(self.game.winner)

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
                                self.drag_start_index = None
                                return
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
        if self.menu:
            return
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
            """Gets a move for AI from the server"""
            if self.menu:
                return
            if not self.sio or not getattr(self.sio, 'connected', False):
                # Fallback if disconnected: random move
                move = self.game.get_ai_move()
                self._execute_ai_move_locally(move)
                return

                # Sends current state of the table to the server to check
            state = self.game.get_state()
            state['difficulty'] = self.ai_difficulty
            print(f"Sending move to server (Difficulty -> {self.ai_difficulty})")
            self.sio.emit('request_ai_move', state)

    def apply_ai_move_from_server(self, data):
        """
        Receives the move from the server and visually represents it. Continues AI turn if there are dice.
        """
        if self.menu:
            return
        move = data.get('move')

        if move:
            start, target, path = move
            print(f"Server moves: {start} -> {target}")
            dice_before = len(self.game.dice)

            self.game.move_piece(start, target, path)
            self.draw_board()

            # Check if the move ends the game
            if self.game.game_over:
                if self.game.match_score[0] >= 5 or self.game.match_score[1] >= 5:
                    self.draw_final_of_the_match(self.game.winner)
                else:
                    self.draw_game_over(self.game.winner)
                return

            dice_after = len(self.game.dice)
            if dice_before == dice_after:
                print("Safety Trigger: Move did not consume any dice. Ending turn to prevent infinite loop!")
                self.root.after(1000, self.ai_end_turn)
                return

            if self.game.dice and self.game.any_valid_moves():
                self.root.after(800, self.ai_perform_move)
            else:
                self.root.after(1000, self.ai_end_turn)
        else:
            print("Server sais that there are no more moves. Ending turn")
            self.root.after(1000, self.ai_end_turn)

    def _execute_ai_move_locally(self, move):
        """
        Executes an AI move locally (used as a fallback when disconnected).
        This mimics the logic that previously existed in ai_perform_move.
        """
        if move:
            start, target, path = move
            print(f"Fallback AI moves locally from {start} to {target}")
            self.game.move_piece(start, target, path)
            self.draw_board()

            # Check win condition
            if self.game.game_over:
                if self.game.match_score[0] >= 5 or self.game.match_score[1] >= 5:
                    self.draw_final_of_the_match(self.game.winner)
                else:
                    self.draw_game_over(self.game.winner)
                return

            # Continue turn if dice and moves remain
            if self.game.dice and self.game.any_valid_moves():
                self.root.after(800, self.ai_perform_move)
            else:
                self.root.after(1000, self.ai_end_turn)
        else:
            print("No valid moves for local AI fallback. Next turn.")
            self.root.after(1000, self.ai_end_turn)

    def ai_end_turn(self):
        """Ends AI turn by automatically switching it and calls the draw_board() method"""
        if self.menu:
            return
        self.game.switch_turn()
        self.draw_board()

    def get_server_index(self, visual_index):
        if self.is_multiplayer:
            my_id = self.my_player_id
        else:
            my_id = 0

        if my_id == 1:
            if 0 <= visual_index <= 23:
                return 23 - visual_index
        return visual_index

    def handle_play_again_request(self):
        """Handles the play again request and draws the pop-up"""
        self.canvas.delete("play_again")
        center_x = WIDTH / 2
        center_y = HEIGHT / 2

        self.canvas.create_rectangle(center_x - 200, center_y - 100, center_x + 200, center_y + 100,
                                     fill="#f0e68c", outline="black", width=3, tags="play_again_popup")
        self.canvas.create_text(center_x, center_y - 40, text="Opponent wants to play again.\nDo you accept?",
                                fill="black", font=("Arial", 16, "bold"), justify="center", tags="play_again_popup")

        # yes btn
        self.canvas.create_rectangle(center_x - 120, center_y + 20, center_x - 20, center_y + 60,
                                     fill="#24A524", outline="black", width=2,
                                     tags=("play_again_popup", "btn_accept_play"))
        self.canvas.create_text(center_x - 70, center_y + 40, text="YES", fill="white", font=("Arial", 14, "bold"),
                                tags=("play_again_popup", "btn_accept_play"))

        # no btn
        self.canvas.create_rectangle(center_x + 20, center_y + 20, center_x + 120, center_y + 60,
                                     fill="#ff5656", outline="black", width=2,
                                     tags=("play_again_popup", "btn_decline_play"))
        self.canvas.create_text(center_x + 70, center_y + 40, text="NO", fill="white", font=("Arial", 14, "bold"),
                                tags=("play_again_popup", "btn_decline_play"))

    def handle_play_again_declined(self):
        """Handles the play again request declined by the opponent"""
        self.canvas.delete("waiting_text")

        center_x = WIDTH / 2
        center_y = HEIGHT / 2

        self.canvas.create_rectangle(center_x - 200, center_y - 80, center_x + 200, center_y + 80,
                                     fill="#ff5656", outline="black", width=3, tags="declined_popup")
        self.canvas.create_text(center_x, center_y - 20, text="Opponent declined to play again.",
                                fill="black", font=("Arial", 16, "bold"), tags="declined_popup")

        self.canvas.create_rectangle(center_x - 60, center_y + 20, center_x + 60, center_y + 60,
                                     fill="#3f1405", outline="white", width=2,
                                     tags=("declined_popup", "btn_ok_declined"))
        self.canvas.create_text(center_x, center_y + 40, text="OK", fill="white", font=("Arial", 14, "bold"),
                                tags=("declined_popup", "btn_ok_declined"))