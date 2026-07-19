# Chess Game w/ AI bot

A fully functional chess game built with Python and Pygame

## 📁 Project Structure

```
chess_game/
├── main.py              # Entry point for the application
├── game.py              # Main game controller and logic
├── board.py             # Chess board representation and rules
├── piece.py             # Piece and Move classes
├── moves.py             # Per-piece move generation logic
├── ai.py                # AI opponent implementation
├── sunfish.py           # Vendored Sunfish engine (used by the hard bot)
├── renderer.py          # All rendering/drawing logic
├── constants.py         # Game constants and configuration
└── README.md            # This file
```

## 🎯 Features

### Game Modes
- **Player vs Player (PvP)**: Play against a friend on the same computer
- **Player vs Bot (PvBot)**: Challenge an AI opponent

### Complete Chess Implementation with AI features
- **Full features (Checks, Checkmates, Stalemate, Draw, 50 move rule, etc)**
- **Weighted opening book**: The bot plays varied, established opening moves before falling back to its selected search strategy when the book line ends or the opponent deviates.
- **Easy, Medium, Hard, Impossible AI bots**: Easy bot uses random play outside the opening book, medium bot uses minimax, hard bot uses Sunfish, and Impossible uses a local Stockfish engine directly.
- **Post-game analysis**: Open the review workspace after a game to replay every move and inspect Stockfish's top three principal variations for each position.
- **Timer**: Timer available for User vs User play
- **UI**: Easy to use UI with moves list, highlighting for moves, and dragging pieces around

### Stockfish (Impossible difficulty)

The Impossible button unlocks when Stockfish is installed and available on your
`PATH`. On macOS with Homebrew, run `brew install stockfish`; alternatively set
`STOCKFISH_PATH` to the executable's full path before launching the game.

## 🚀 Installation

### Prerequisites
- Python 3.6 or higher
- pip (Python package manager)

### Setup

1. **Clone or download the project**
```bash
git clone https://github.com/Abhinav-Vadlamani/Chess-Game.git
cd chess_game
```

2. **Install pygame**
```bash
pip install pygame
```

3. **Run file through main.py**
