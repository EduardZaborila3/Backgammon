# Python Backgammon

A full-featured, GUI-based Backgammon desktop application built with Python and Tkinter, featuring a robust logic engine, a custom-trained neural network opponent, and real-time online multiplayer.

## Features
- **Multiple Game Modes:** Local PvP, Player vs AI, and Online Multiplayer.
- **Adaptive AI:** Play against an intelligent opponent powered by a custom-trained Deep Learning model (PyTorch) with varying difficulty levels (Medium, Hard).
- **Real-Time Online Multiplayer:** Connect and play with opponents over the internet using a low-latency WebSockets architecture.
- **Advanced Rules Validation:** Fully supports standard backgammon rules, including bearing off, hitting checkers, and special win conditions (gammon/backgammon).
- **Doubling Cube:** Full mechanics to offer, accept, or refuse to double the match stakes.
- **Undo Move:** Revert moves smoothly during your current turn before finalizing them.
- **Save/Load System:** Serialize the current local game state to a JSON file and resume playing later.

## Tech Stack
- **GUI:** `Tkinter` (Python standard library)
- **Networking:** `python-socketio`, `aiohttp` (for the server-client architecture)
- **Machine Learning:** `PyTorch` (for evaluating board states and making AI decisions)
- **Data Management:** `json` (serialization), `threading`, `queue` (for non-blocking UI and network tasks)

## Architecture & Logic
The application is built upon a highly modular architecture that prioritizes strict logic and practical functionality:
- **Core Logic Engine (`logic.py`):** Operates entirely independently of the GUI. It mathematically calculates valid moves, enforces strict game rules, manages the board state, and handles point scoring.
- **Asynchronous UI (`ui.py` & `main.py`):** Uses an event-driven queue system to communicate with the server. This ensures the graphical interface remains responsive and fluid, without freezing during network requests or AI calculations.
- **Authoritative Server (`server.py`):** In online matches, the server maintains its own instance of the logic engine to validate moves, process doubling cube requests, and keep clients perfectly synchronized, preventing local tampering.

### Prerequisites
1. Ensure you have Python 3.10+ installed.
2. Clone the repository to your local machine.
3. Install the required dependencies (highly recommended to use a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```

## How to Run
**Option 1**
```bash
python main.py
```

**Option 2: Build a standalone executable**
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build the executable:
   ```bash
   pyinstaller main.py --onefile --noconsole
   ```
   This will create a standalone executable in the `dist` folder. You can simply double-click it to start the game.

### Running the Multiplayer Server (Optional)
If you wish to host your own matchmaking server instead of using the default deployed one:
1. Navigate to the server directory.
2. Run the server script:
   ```bash
   python server.py
   ```
3. Update the SERVER_URL variable in main.py to point to your local machine (e.g., http://localhost:5555)

