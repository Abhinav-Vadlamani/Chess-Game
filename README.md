# Chess Game

A local two-player and player-vs-bot chess game built with Python and Pygame.
It includes rule-complete play, animated CBurnett-style piece sprites, a weighted
opening book, and optional Stockfish-powered analysis.

## Features

- Player vs Player, with optional independent clocks
- Player vs Bot with Easy, Medium, Hard (Sunfish), and optional Impossible
  (Stockfish) difficulties
- Legal move handling, including castling, en passant, promotion, checkmate,
  stalemate, insufficient material, threefold repetition, and the fifty-move rule
- A weighted opening book so bots play varied, recognizable opening lines
- Smooth move, capture, castling, promotion, and game-end effects
- High-resolution piece sprites and drag-and-drop or click-to-move controls
- Move history and a Resign button; resignations correctly award the win to the
  other side
- Post-game review: replay the game, inspect the top three Stockfish lines, and
  view an evaluation bar and score from White's perspective

## Requirements

- Python 3.10 or newer
- Pygame 2
- Optional: Stockfish for Impossible difficulty and engine analysis

All piece artwork required by the game is already included in
`assets/pieces/cburnett/`.

## Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/Abhinav-Vadlamani/Chess-Game.git
cd Chess-Game
```

Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the game dependency:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install pygame
```

Run the game from the repository root:

```bash
python3 main.py
```

On Windows, use `python main.py` if `python3` is not available.

## Optional: Stockfish

Stockfish unlocks the **Impossible** bot difficulty and enables post-game engine
lines and the evaluation bar. The rest of the game works without it.

Install Stockfish using your platform's package manager, for example:

```bash
# macOS (Homebrew)
brew install stockfish

# Debian/Ubuntu
sudo apt install stockfish
```

If the executable is not on your `PATH`, point the game to it before launching:

```bash
export STOCKFISH_PATH="/full/path/to/stockfish"
python3 main.py
```

In Windows PowerShell:

```powershell
$env:STOCKFISH_PATH = "C:\full\path\to\stockfish.exe"
python main.py
```

## How to play

- Choose **Player vs Player** or **Player vs Bot** from the main menu.
- Move pieces by dragging them or by clicking a piece and then its destination.
- Use **Moves** to toggle the move-history panel.
- Use **Resign** to resign for the side currently to move.
- Press `R` to restart the current game, `Q` to quit, or `Esc` to return to the
  menu.
- After a game ends, choose **Review game**. Use the Previous/Next buttons or
  the Left/Right arrow keys to step through positions.

## Project structure

```text
Chess-Game/
├── assets/pieces/cburnett/  # Bundled raster chess pieces
├── main.py                  # Application entry point
├── game.py                  # Game flow, input, animation, and analysis state
├── board.py                 # Board state, move validation, and game rules
├── piece.py                 # Piece and move models
├── moves.py                 # Per-piece move generation
├── ai.py                    # Opening book, bot logic, and Stockfish integration
├── sunfish.py               # Bundled Sunfish engine for Hard difficulty
├── renderer.py              # Pygame board, controls, and analysis UI
└── constants.py             # Shared configuration and game constants
```
