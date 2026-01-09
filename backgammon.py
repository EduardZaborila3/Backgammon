import random
import tkinter as tk

WIDTH = 900
HEIGHT = 600
BORDER_WIDTH = 25
CENTER_BAR_WIDTH = 50
TRIANGLE_HEIGHT = 220
CHECKER_RADIUS = 24
DICE_SIZE = 50
DONE_BUTTON_SIZE = 40

PLAY_AREA_START_X = BORDER_WIDTH
PLAY_AREA_END_X = WIDTH - BORDER_WIDTH
PLAY_AREA_START_Y = BORDER_WIDTH
PLAY_AREA_END_Y = HEIGHT - BORDER_WIDTH
LEFT_BOARD_END_X = WIDTH / 2 - CENTER_BAR_WIDTH / 2
RIGHT_BOARD_START_X = WIDTH / 2 + CENTER_BAR_WIDTH / 2

BOARD_COLOR = "#F0E68C"
BORDER_COLOR = "#8B4513"
POINT_COLOR_BLACK = "#171717"
POINT_COLOR_RED = "#A52A2A"
COLOR_PLAYER0 = "#FFFFFF"
COLOR_PLAYER1 = "#1E1E1E"
HIGHLIGHT_COLOR = "#24A524"
#TODO SA IMPLEMENTEZ REGULA DE MARTI TEHNIC
#numai eu stiu de ea xD

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
        self.init_board()

    def init_board(self):
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
            self.switch_turn()

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

        if self.dice and not self.any_valid_moves():
            print(f"No valid moves for player {self.turn}. Dice lost")
            self.dice = []

        # if not self.dice:
        #     print(f"All dice used. Waiting for player {self.turn} to end turn")

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

        self.draw_board()

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def draw_board(self):
        self.canvas.delete("all")
        
        self.canvas.create_rectangle(PLAY_AREA_START_X, PLAY_AREA_START_Y, LEFT_BOARD_END_X, PLAY_AREA_END_Y, fill=BOARD_COLOR, outline="black", width=2)
        self.canvas.create_rectangle(RIGHT_BOARD_START_X, PLAY_AREA_START_Y, PLAY_AREA_END_X, PLAY_AREA_END_Y, fill=BOARD_COLOR, outline="black", width=2)
        self.draw_dice()

        if not self.game.has_rolled:
            self.draw_roll_dice_button()

        if self.game.has_rolled and not self.game.dice:
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

    def reset_selection(self):
        self.selected_point = None
        self.valid_moves = []
        self.draw_board()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Backgammon")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    app = BackgammonUI(root)
    root.mainloop()