from enum import Enum

# Window and board dimensions
WINDOW_SIZE = 800
BOARD_SIZE = 640
BOARD_OFFSET = 80
SQUARE_SIZE = BOARD_SIZE // 8
FPS = 60

# Colors
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_MOVE = (186, 202, 68)
HIGHLIGHT_SELECTED = (246, 246, 130)
HIGHLIGHT_CHECK = (255, 100, 100)
HIGHLIGHT_LAST_MOVE = (205, 210, 106)
BG_COLOR = (49, 46, 43)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (130, 151, 105)
BUTTON_HOVER = (150, 171, 125)

# Board coordinates
FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
RANKS = ['8', '7', '6', '5', '4', '3', '2', '1']

# AI Configuration
AI_DIFFICULTY_DEPTHS = {
    'easy': 1,
    'medium': 3,
    'hard': 3  # unused - hard uses Sunfish engine
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