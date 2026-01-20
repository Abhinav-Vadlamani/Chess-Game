from constants import PieceType, Color
from typing import Optional

class Piece:
    def __init__(self, piece_type, color):
        """
        Initialize a chess piece

        Args:
            piece_type: The type of the piece
            color: Which color/team the piece belongs to
        """

        self.piece_type = piece_type
        self.color = color
        self.has_moved = False
    
    def __repr__(self):
        return f"{self.color.value}{self.piece_type.value}"
    
    def __str__(self):
        return self.__repr__()
    
class Move:
    def __init__(self, from_position, to_position, is_castling, is_en_passant, captured_piece, promotion_piece):
        """
        Initialize a move

        Args:
            from_position: (row, col) of the position where the piece is from
            to_position: (row, col) of the position where the piece is going to
            is_castling: Whether the move is catling
            is_en_passant: Whether the move is a en passant
            captured_piece: Piece being captured
            promotion_piece: Piece type for pawn promotion
        """

        self.from_position = from_position
        self.to_position = to_position
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
        self.captured_piece = captured_piece
        self.promotion_piece = promotion_piece
    
    def __repr__(self):
        return f"Move({self.from_position} -> {self.to_position})"

    def __str__(self):
        return self.__repr__()