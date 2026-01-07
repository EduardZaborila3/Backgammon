import random
import tkinter as tk

WIDTH = 900
HEIGHT = 600
BORDER_WIDTH = 25
CENTER_BAR_WIDTH = 50
TRIANGLE_HEIGHT = 220
CHECKER_RADIUS = 24
DICE_SIZE = 50

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

class BackgammonLogic:
    def __init__(self):
        self.board = []
        for i in range(24):
            self.board.append([])
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
        # self.dice = [5, 5, 5, 5]
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
        dice_sum = 0
        if len(self.dice) == 4:
            die = self.dice[0]
            target_index = start_index
            for i in range(4):
                target_index = target_index + (die * direction)
                if 0 <= target_index <= 23:
                    target_point = self.board[target_index]
                    if (not target_point) or (target_point[0] == self.turn) or (len(target_point) == 1 and target_point[0] != self.turn):
                        moves.append((target_index, die))
                    else:
                        break
        else:
            for die in unique_dice:
                target_index = start_index + (die * direction)
                dice_sum += (die * direction)
                if 0 <= target_index <= 23:
                    target_point = self.board[target_index]
                    if (not target_point) or (target_point[0] == self.turn) or (len(target_point) == 1 and target_point[0] != self.turn):
                        moves.append((target_index, die))

        target_index = start_index + dice_sum
        if 0 <= target_index <= 23:
            target_point = self.board[target_index]
            if (not target_point) or (target_point[0] == self.turn) or (len(target_point) == 1 and target_point[0] != self.turn):
                moves.append((target_index, dice_sum))

        if not moves:
            print("No possible moves. Moving to next player.")
            self.dice = []
        for move in moves:
            print(f"Start: {start_index} -> {move[0]} [Die: {move[1]}]") 

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

class BackgammonUI:
    def __init__(self, root):
        self.game = BackgammonLogic()
        self.root = root
        
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BORDER_COLOR)
        self.canvas.pack()
        
        self.selected_point = None
        self.valid_moves = []
        
        self.draw_board()
        self.canvas.bind("<Button-1>", self.on_click)

    def draw_board(self):
        self.canvas.delete("all")
        
        self.canvas.create_rectangle(PLAY_AREA_START_X, PLAY_AREA_START_Y, LEFT_BOARD_END_X, PLAY_AREA_END_Y, fill=BOARD_COLOR, outline="black", width=2)
        self.canvas.create_rectangle(RIGHT_BOARD_START_X, PLAY_AREA_START_Y, PLAY_AREA_END_X, PLAY_AREA_END_Y, fill=BOARD_COLOR, outline="black", width=2)
        self.draw_dice()
        self.draw_roll_dice_button()

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
                direction = -1
            #sus 12-23
            else: 
                visual_col = 23 - i
                y_base = PLAY_AREA_START_Y
                y_tip = PLAY_AREA_START_Y + TRIANGLE_HEIGHT
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

    def draw_checkers(self, index, x, y_base, direction):
        pieces = self.game.board[index]
        if not pieces: 
            return
        
        if pieces[0] == 0:
            color = COLOR_PLAYER0
        else:
            color = COLOR_PLAYER1

        if pieces[0] == 0:
            outline_color = "black"
        else:
            outline_color = "white"
        
        for k in range(len(pieces)):
            if k > 4:
                if pieces[0] == 1:
                    self.canvas.create_text(x, y_curr, text=f"{len(pieces)}", fill="#00ccff", font=("Arial", 14, "bold"))
                else:
                    self.canvas.create_text(x, y_curr, text=f"{len(pieces)}", fill="blue", font=("Arial", 14, "bold"))
                break
                
            spacing = CHECKER_RADIUS * 2 
            if direction == -1: 
                y_curr = y_base - CHECKER_RADIUS - (k * spacing)
            else: 
                y_curr = y_base + CHECKER_RADIUS + (k * spacing)

            width = 1
            if self.selected_point == index and k == len(pieces) - 1:
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
            self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill="black")

    def draw_roll_dice_button(self):
        ROLL_DICE_BTN_RADIUS = 50
        y0 = HEIGHT / 2 + (ROLL_DICE_BTN_RADIUS / 2)
        y1 = HEIGHT / 2 - (ROLL_DICE_BTN_RADIUS / 2)
        self.canvas.create_oval(680, y0, 730, y1, fill="blue", outline="black", tags="btn_roll")
        self.canvas.create_text(705, y0 - 25, fill="white", text="ROLL", font=("Times New Roman", 10, "bold"), tags="btn_roll", activefill="#f08888")

    def on_click(self, event):
        clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item in clicked:
            if "btn_roll" in self.canvas.gettags(item):
                self.game.roll_dice()
                self.draw_board()
                return

        if not (PLAY_AREA_START_Y <= event.y <= PLAY_AREA_END_Y):
            self.reset_selection()
            return

        normalized_x = event.x - PLAY_AREA_START_X
        if event.x > RIGHT_BOARD_START_X: 
            normalized_x -= CENTER_BAR_WIDTH
        
        point_width = ((PLAY_AREA_END_X - PLAY_AREA_START_X) - CENTER_BAR_WIDTH) / 12
        col = int(normalized_x / point_width)
        visual_col = 11 - col
        visual_col = max(0, min(11, visual_col))

        if event.y > HEIGHT / 2: 
            clicked_index = visual_col
        else:                    
            clicked_index = 23 - visual_col
        
        if 0 <= clicked_index < 24:
            moves = self.game.get_valid_moves(clicked_index)
            if moves:
                self.selected_point = clicked_index
                self.valid_moves = moves
            else:
                self.reset_selection()
        else:
            self.reset_selection()
        
        self.draw_board()

    def reset_selection(self):
        self.selected_point = None
        self.valid_moves = []
        self.draw_board()

def print_console_board(game):
    print("\nState:")
    print(f"Bar (P0/P1): {game.bar}")
    print(f"Off (P0/P1): {game.off}")
    print("Board:", [f"{i}:{game.board[i]}" for i in range(0, 12)])
    print([f"{i}:{game.board[i]}" for i in range(12, 24)])

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Backgammon")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    app = BackgammonUI(root)
    root.mainloop()