# Chess Game w/ AI bot

A fully functional chess game built with Python and Pygame

## 📁 Project Structure

```
chess_game/
├── main.py              # Entry point for the application
├── game.py              # Main game controller and logic
├── board.py             # Chess board representation and rules
├── piece.py             # Piece and Move classes
├── move_generator.py    # Move generation logic
├── ai.py                # AI opponent implementation
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
- **Easy, Medium, Hard AI bots**: Easy bot randomly picks a move, medium bot uses minimax algorithm, and hardbot uses sunfish algorithm + book of openings
- **Timer**: Timer available for User vs User play

## 🚀 Installation

### Prerequisites
- Python 3.6 or higher
- pip (Python package manager)

### Setup

1. **Clone or download the project**
```bash
cd chess_game
```

2. **Install pygame**
```bash
pip install pygame
```

3. **Run file through main.py**

## 🚀 Future Enhancements
- [ ] Draw Conditions (50-move rule, three fold repition, insufficient material)
- [ ] Fix time box on screen
- [ ] Move history panel
- [ ] Flip board when user is black against bot