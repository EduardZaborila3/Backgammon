import tkinter as tk
from logic import BackgammonLogic
from ui import BackgammonUI
from constants import *

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Backgammon")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    app = BackgammonUI(root)
    root.mainloop()