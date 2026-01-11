import tkinter as tk
from logic import BackgammonLogic
import random
from constants import *

class BackgammonUI:
    def __init__(self, root):
        self.game = BackgammonLogic()
        self.root = root
        
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

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def draw_menu(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#994f0a")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 200, text="Backgammon", fill="#CDCDCD", font=("Arial", 36, "bold"))
        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2 - 75, WIDTH / 2 + 100, HEIGHT / 2 - 25, fill="#3f1405", outline="white", width=2, tags="menu_pvp")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 50, text="2 players game", fill="#aaaaaa", activefill="#f9fc4f", font=("Arial", 16, "bold"))
        self.canvas.create_rectangle(WIDTH / 2 - 100, HEIGHT / 2, WIDTH / 2 + 100, HEIGHT / 2 + 50, fill="#3f1405", outline="white", width=2, tags="menu_ai")
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 25, text="Play vs AI", fill="#aaaaaa", activefill="#f9fc4f", font=("Arial", 16, "bold"))

    def start_game(self, ai_mode = False):
        self.menu = False
        self.ai_match = ai_mode
        print(f"Game starting in mode ai mode: {ai_mode}")
        self.game.init_board()
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        
        self.canvas.create_rectangle(PLAY_AREA_START_X, PLAY_AREA_START_Y, LEFT_BOARD_END_X, PLAY_AREA_END_Y, fill=BOARD_COLOR, outline="black", width=2)
        self.canvas.create_rectangle(RIGHT_BOARD_START_X, PLAY_AREA_START_Y, PLAY_AREA_END_X, PLAY_AREA_END_Y, fill=BOARD_COLOR, outline="black", width=2)
        self.draw_dice()

        if not self.game.has_rolled:
            if not (self.ai_match and self.game.turn == 1):
                self.draw_roll_dice_button()
        
        if self.game.has_rolled and not self.game.dice and not self.game.game_over:
            if not (self.ai_match and self.game.turn == 1):
                self.draw_done_button()

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
                color = HIGHLIGHT_COLOR
            elif i % 2 == 0:
                color = POINT_COLOR_BLACK
            else:
                color = POINT_COLOR_RED
            
            coords = [x_base - point_width / 2, y_base, x_base + point_width / 2, y_base, x_base, y_tip]
            self.canvas.create_polygon(coords, fill=color)
            self.draw_checkers(i, x_base, y_base, direction)
            self.draw_info_and_bars()

    def draw_checkers(self, index, x, y_base, direction):
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
        dot_offset = DICE_SIZE / 4
        radius = 4
        for px, py in self.game.get_dice_dots(value):
            x = cx + (px * dot_offset)
            y = cy + (py * dot_offset)
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="black")

    def draw_roll_dice_button(self):
        ROLL_DICE_BTN_RADIUS = 50
        y0 = HEIGHT / 2 + (ROLL_DICE_BTN_RADIUS / 2)
        y1 = HEIGHT / 2 - (ROLL_DICE_BTN_RADIUS / 2)
        self.canvas.create_oval(680, y0, 730, y1, fill="blue", outline="black", tags="btn_roll")
        self.canvas.create_text(705, y0 - 25, fill="white", text="ROLL", font=("Arial", 10, "bold"), tags="btn_roll", activefill="#f08888")

    def draw_done_button(self):
        y0 = HEIGHT / 2 + (DONE_BUTTON_SIZE / 2)
        y1 = HEIGHT / 2 - (DONE_BUTTON_SIZE / 2)
        done_btn_x0 = 680
        done_btn_x1 = 730
        self.canvas.create_rectangle(done_btn_x0, y0, done_btn_x1, y1, fill="#24A524", outline="black", tags="btn_done")
        self.canvas.create_text((done_btn_x0 + done_btn_x1)/2, HEIGHT/2, text="DONE", fill="white", font=("Arial", 10, "bold"), tags="btn_done", activefill="#f08888")

    def draw_info_and_bars(self):
        center_x =  WIDTH / 2
        center_y = HEIGHT / 2
        width = 100
        height = 15
        
        if self.game.turn == 0:
            turn_text = "White (P0)"
        else:
            turn_text = "Black (P1)"
        self.canvas.create_rectangle(center_x-width, center_y-height, center_x+width, center_y+height, fill="#7A711C", outline="black")
        if self.game.turn == 0:
            self.canvas.create_text(center_x, center_y, text=f"Turn: White", font=("Arial", 14, "bold"), fill="white")
        else:
            self.canvas.create_text(center_x, center_y, text=f"Turn: Black", font=("Arial", 14, "bold"), fill="black")

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

    def draw_game_over(self, winner):
        if winner == 0:
            game_over_text = "You win!"
            winner_color = "#6aff8a"
        else:
            winner_color = "#ff5656"
            game_over_text = "You lose!"
        self.canvas.create_rectangle(WIDTH / 2 - 120, HEIGHT / 2 - 30, WIDTH / 2 + 120, HEIGHT / 2 + 30, fill=winner_color, outline="black", width=2)
        self.canvas.create_text(WIDTH / 2, HEIGHT / 2, text=f"{game_over_text}", fill="black", font=("Arial", 36, "bold"))

    def get_index_from_coords(self, x, y):
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
        if self.game.game_over:
            return
        
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
            return
        
        #ignor click urile mele daca e tura ai ului
        if self.ai_match and self.game.turn == 1:
            return

        clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item in clicked:
            tags = self.canvas.gettags(item)
            if "btn_roll" in tags:
                self.game.roll_dice()
                self.draw_board()
                return
            if "btn_done" in tags:
                self.game.switch_turn()
                self.draw_board()
                if self.ai_match and self.game.turn == 1:
                    self.root.after(1000, self.run_ai_turn)
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
        #ignor click urile mele daca e tura ai ului
        if self.ai_match and self.game.turn == 1:
            return

        if self.dragged_piece_id:
            self.canvas.delete(self.dragged_piece_id)
            self.dragged_piece_id = None
            
            target_index = self.get_index_from_coords(event.x, event.y)
            move_executed = False
            if target_index is not None and target_index != self.drag_start_index:
                for move in self.valid_moves:
                    if move[0] == target_index:
                        self.game.move_piece(self.drag_start_index, target_index, move[1])
                        move_executed = True
                        self.reset_selection()
                        break
            
            self.drag_start_index = None
            self.draw_board()
            if self.game.game_over:
                self.draw_game_over(self.game.winner)

    def reset_selection(self):
        self.selected_point = None
        self.valid_moves = []
        self.draw_board()

    def run_ai_turn(self):
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
        possible_moves = []

        if self.game.bar[1] > 0:
            #daca are piese pe bara e obligat sa le mute primele, daca are pozitii permise
            moves = self.game.get_valid_moves(-1) 
            for target, path in moves:
                possible_moves.append((-1, target, path))
        else:
            #daca nu are piese pe bara, atunci verific mutarile de pe tabla
            for i in range(24):
                if self.game.board[i] and self.game.board[i][0] == 1:
                    moves = self.game.get_valid_moves(i)
                    for target, path in moves:
                        possible_moves.append((i, target, path))

        #ai ul face o mutare random din cele permise gasite
        if possible_moves:
            move_to_execute = random.choice(possible_moves)
            start, target, path = move_to_execute
            print(f"AI moves from {start} to {target}")
            self.game.move_piece(start, target, path)
            self.draw_board()

            if self.game.dice and self.game.any_valid_moves():
                self.root.after(800, self.ai_perform_move)
            else:
                self.root.after(1000, self.ai_end_turn)
        else:
            print(f"No valid moves for Ai. Next turn")
            self.root.after(1000, self.ai_end_turn)

    def ai_end_turn(self):
        self.game.switch_turn()
        self.draw_board()