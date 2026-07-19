from enum import Enum

# Window and board dimensions
WINDOW_SIZE = 800
BOARD_SIZE = 640
BOARD_OFFSET = 80
SQUARE_SIZE = BOARD_SIZE // 8
FPS = 60

# Colors
# Classic blue board theme, inspired by traditional tournament diagrams.
LIGHT_SQUARE = (238, 239, 241)
DARK_SQUARE = (119, 143, 188)
HIGHLIGHT_MOVE = (141, 174, 111)
HIGHLIGHT_SELECTED = (244, 207, 104)
HIGHLIGHT_CHECK = (221, 103, 96)
HIGHLIGHT_LAST_MOVE = (174, 193, 119)
BG_COLOR = (244, 246, 250)
TEXT_COLOR = (39, 47, 61)
BUTTON_COLOR = (89, 116, 163)
BUTTON_HOVER = (111, 140, 190)

# Board coordinates
FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
RANKS = ['8', '7', '6', '5', '4', '3', '2', '1']

# AI Configuration
AI_DIFFICULTY_DEPTHS = {
    'easy': 1,
    'medium': 3,
    'hard': 3,  # unused - hard uses Sunfish engine
    'impossible': 20  # Stockfish controls its own UCI search depth
}

# Piece values
PIECE_VALUES = {
    'p': 100,   # Pawn
    'n': 320,   # Knight
    'b': 330,   # Bishop
    'r': 500,   # Rook
    'q': 900,   # Queen
    'k': 20000  # King
}

class PieceType(Enum):
    """Types of chess pieces"""
    PAWN = 'p'
    KNIGHT = 'n'
    BISHOP = 'b'
    ROOK = 'r'
    QUEEN = 'q'
    KING = 'k'

class Color(Enum):
    """Player colors"""
    WHITE = 'w'
    BLACK = 'b'
    
    def opposite(self):
        """Return the opposite color"""
        return Color.BLACK if self == Color.WHITE else Color.WHITE
