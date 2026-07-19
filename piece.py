class Piece:
    """A chess piece: its type, color, and whether it has moved (for castling/pawns)."""

    def __init__(self, piece_type, color):
        self.piece_type = piece_type
        self.color = color
        self.has_moved = False

    def __repr__(self):
        return f"{self.color.value}{self.piece_type.value}"


class Move:
    """A record of a played move, kept in the board's history."""

    def __init__(self, from_position, to_position, is_castling, is_en_passant,
                 captured_piece, promotion_piece):
        """
        Args:
            from_position: (row, col) the piece moved from
            to_position: (row, col) the piece moved to
            is_castling: whether the move was a castle
            is_en_passant: whether the move was an en passant capture
            captured_piece: the piece captured, or None
            promotion_piece: the promoted piece, or None
        """
        self.from_position = from_position
        self.to_position = to_position
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
        self.captured_piece = captured_piece
        self.promotion_piece = promotion_piece

    def __repr__(self):
        return f"Move({self.from_position} -> {self.to_position})"
