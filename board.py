from piece import Piece, Move
from constants import PieceType, Color, FILES, RANKS
from moves import (get_pawn_moves, get_knight_moves, get_bishop_moves,
                   get_rook_moves, get_queen_moves, get_king_moves,
                   get_pawn_attack_squares, get_king_attack_squares)

# Letters used for each piece in algebraic notation (pawns have none).
_ALGEBRAIC_SYMBOLS = {
    PieceType.KING: 'K',
    PieceType.QUEEN: 'Q',
    PieceType.ROOK: 'R',
    PieceType.BISHOP: 'B',
    PieceType.KNIGHT: 'N',
    PieceType.PAWN: '',
}

# Move generators for pieces that move the same way whether attacking or not.
# Pawns and kings are handled separately because their attack and move patterns
# differ (pawns push forward but capture diagonally; kings can castle).
_SLIDING_AND_KNIGHT = {
    PieceType.KNIGHT: get_knight_moves,
    PieceType.BISHOP: get_bishop_moves,
    PieceType.ROOK: get_rook_moves,
    PieceType.QUEEN: get_queen_moves,
}

# Back-rank piece layout, left to right, shared by both colors.
_BACK_RANK = [PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
              PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK]


def create_starting_board():
    """Return a fresh 8x8 board array set up in the standard starting position."""
    board = [[None for _ in range(8)] for _ in range(8)]
    for col, piece_type in enumerate(_BACK_RANK):
        board[0][col] = Piece(piece_type, Color.BLACK)
        board[1][col] = Piece(PieceType.PAWN, Color.BLACK)
        board[6][col] = Piece(PieceType.PAWN, Color.WHITE)
        board[7][col] = Piece(piece_type, Color.WHITE)
    return board


def _apply_move_to_array(board, move):
    """Replay one recorded move onto a raw 8x8 board array (used for replays)."""
    from_row, from_col = move.from_position
    to_row, to_col = move.to_position

    board[to_row][to_col] = board[from_row][from_col]
    board[from_row][from_col] = None

    if move.is_castling:
        if to_col > from_col:  # Kingside: rook jumps from h-file to f-file
            board[from_row][5] = board[from_row][7]
            board[from_row][7] = None
        else:  # Queenside: rook jumps from a-file to d-file
            board[from_row][3] = board[from_row][0]
            board[from_row][0] = None

    if move.is_en_passant:
        board[from_row][to_col] = None

    if move.promotion_piece:
        board[to_row][to_col].piece_type = move.promotion_piece.piece_type


class ChessBoard:
    def __init__(self):
        self.board = create_starting_board()
        self.current_turn = Color.WHITE
        self.move_history = []
        self.en_passant_target = None

    def get_piece(self, row, col):
        """Return the piece at (row, col), or None if empty or off-board."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def get_valid_moves(self, row, col):
        """Return the legal moves for the current player's piece at (row, col)."""
        piece = self.get_piece(row, col)
        if not piece or piece.color != self.current_turn:
            return []

        # Keep only pseudo-legal moves that don't leave our own king in check.
        return [(to_row, to_col)
                for to_row, to_col in self._get_pseudo_legal_moves(row, col)
                if self._is_legal_move(row, col, to_row, to_col)]
    
    def _get_pseudo_legal_moves(self, row, col):
        """Return the piece's moves, ignoring king safety but including castling."""
        piece = self.board[row][col]

        if piece.piece_type == PieceType.PAWN:
            return get_pawn_moves(self.board, row, col, self.en_passant_target)

        if piece.piece_type == PieceType.KING:
            moves = get_king_moves(self.board, row, col)
            if not piece.has_moved and not self.is_in_check(piece.color):
                if self._can_castle_kingside(row, col):
                    moves.append((row, col + 2))
                if self._can_castle_queenside(row, col):
                    moves.append((row, col - 2))
            return moves

        return _SLIDING_AND_KNIGHT[piece.piece_type](self.board, row, col)

    def _can_castle_kingside(self, row, col):
        """Return True if the king at (row, col) may castle kingside."""
        rook = self.board[row][7]
        if not rook or rook.piece_type != PieceType.ROOK or rook.has_moved:
            return False
        
        # The king's square and the two it crosses must be empty and unattacked.
        for c in range(col + 1, 7):
            if self.board[row][c] is not None:
                return False
            if c <= col + 2 and self._is_square_attacked(row, c, self.current_turn):
                return False

        return True

    def _can_castle_queenside(self, row, col):
        """Return True if the king at (row, col) may castle queenside."""
        rook = self.board[row][0]
        if not rook or rook.piece_type != PieceType.ROOK or rook.has_moved:
            return False

        # The king's square and the two it crosses must be empty and unattacked.
        for c in range(1, col):
            if self.board[row][c] is not None:
                return False
            if c >= col - 2 and self._is_square_attacked(row, c, self.current_turn):
                return False

        return True

    def _attack_squares(self, row, col):
        """Return the squares the piece at (row, col) attacks."""
        piece_type = self.board[row][col].piece_type
        if piece_type == PieceType.PAWN:
            return get_pawn_attack_squares(self.board, row, col)
        if piece_type == PieceType.KING:
            return get_king_attack_squares(self.board, row, col)
        return _SLIDING_AND_KNIGHT[piece_type](self.board, row, col)

    def _is_square_attacked(self, row, col, by_color):
        """Return True if (row, col) is attacked by any piece opposing by_color."""
        opponent_color = by_color.opposite()

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == opponent_color:
                    if (row, col) in self._attack_squares(r, c):
                        return True

        return False

    def _is_legal_move(self, from_row, from_col, to_row, to_col):
        """Return True if making this move would not leave our own king in check."""
        piece = self.board[from_row][from_col]
        captured = self.board[to_row][to_col]

        # Handle en passant capture
        ep_captured = None
        ep_pos = None
        if piece.piece_type == PieceType.PAWN and self.en_passant_target == (to_row, to_col):
            ep_pos = (from_row, to_col)
            ep_captured = self.board[from_row][to_col]
            self.board[from_row][to_col] = None

        # Make the move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None

        # Check if king is in check
        in_check = self.is_in_check(self.current_turn)

        # Unmake the move
        self.board[from_row][from_col] = piece
        self.board[to_row][to_col] = captured

        # Restore en passant captured piece
        if ep_captured is not None:
            self.board[ep_pos[0]][ep_pos[1]] = ep_captured

        return not in_check

    def _find_king(self, color):
        """Return the (row, col) of the given color's king, or None if absent."""
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.piece_type == PieceType.KING and piece.color == color:
                    return (r, c)
        return None

    def is_in_check(self, color):
        """Return True if the given color's king is currently attacked."""
        king_pos = self._find_king(color)
        if not king_pos:
            return False
        return self._is_square_attacked(king_pos[0], king_pos[1], color)

    def make_move(self, from_row, from_col, to_row, to_col, promotion_piece=None):
        """
        Play a move if it is legal, updating history, castling rights and turn.

        Args:
            promotion_piece: piece type to promote a pawn to (defaults to QUEEN)

        Returns:
            True if the move was legal and played, else False.
        """
        valid_moves = self.get_valid_moves(from_row, from_col)

        if (to_row, to_col) not in valid_moves:
            return False

        piece = self.board[from_row][from_col]
        captured_piece = self.board[to_row][to_col]
        is_castling = False
        is_en_passant = False

        # Handle castling
        if piece.piece_type == PieceType.KING and abs(to_col - from_col) == 2:
            is_castling = True
            if to_col > from_col:  # Kingside
                rook = self.board[from_row][7]
                self.board[from_row][5] = rook
                self.board[from_row][7] = None
                rook.has_moved = True
            else:  # Queenside
                rook = self.board[from_row][0]
                self.board[from_row][3] = rook
                self.board[from_row][0] = None
                rook.has_moved = True

        # Handle en passant
        if piece.piece_type == PieceType.PAWN and self.en_passant_target == (to_row, to_col):
            is_en_passant = True
            captured_row = from_row
            captured_piece = self.board[captured_row][to_col]
            self.board[captured_row][to_col] = None

        # Make the move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.has_moved = True

        # Set en passant target
        self.en_passant_target = None
        if piece.piece_type == PieceType.PAWN and abs(to_row - from_row) == 2:
            self.en_passant_target = ((from_row + to_row) // 2, to_col)

        # Handle pawn promotion
        promoted = False
        if piece.piece_type == PieceType.PAWN and (to_row == 0 or to_row == 7):
            piece.piece_type = promotion_piece if promotion_piece else PieceType.QUEEN
            promoted = True

        # Record move
        move = Move(from_position=(from_row, from_col), to_position=(to_row, to_col),
                   captured_piece=captured_piece, is_castling=is_castling,
                   is_en_passant=is_en_passant, promotion_piece=piece if promoted else None)
        self.move_history.append(move)

        # Switch turns
        self.current_turn = self.current_turn.opposite()

        return True
    
    def is_promotion_move(self, from_row, from_col, to_row, to_col):
        """Return True if moving this pawn to (to_row, to_col) would promote it."""
        piece = self.get_piece(from_row, from_col)
        if not piece or piece.piece_type != PieceType.PAWN:
            return False
        return ((piece.color == Color.WHITE and to_row == 0) or
                (piece.color == Color.BLACK and to_row == 7))

    def _current_player_has_moves(self):
        """Return True if the current player has at least one legal move."""
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == self.current_turn:
                    if self.get_valid_moves(r, c):
                        return True
        return False

    def is_checkmate(self):
        """Return True if the current player is in check with no legal moves."""
        return self.is_in_check(self.current_turn) and not self._current_player_has_moves()

    def is_stalemate(self):
        """Return True if the current player is not in check but has no legal moves."""
        return not self.is_in_check(self.current_turn) and not self._current_player_has_moves()

    def is_insufficient_material(self):
        """
        Check if there is insufficient material to checkmate.
        Draw conditions:
        - King vs King
        - King + Bishop vs King
        - King + Knight vs King
        - King + Bishop vs King + Bishop (same color squares)
        """
        pieces = {'white': [], 'black': []}

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece:
                    if piece.color == Color.WHITE:
                        pieces['white'].append((piece.piece_type, r, c))
                    else:
                        pieces['black'].append((piece.piece_type, r, c))

        white_types = set(p[0] for p in pieces['white'])
        black_types = set(p[0] for p in pieces['black'])
        white_count = len(pieces['white'])
        black_count = len(pieces['black'])

        # King vs King
        if white_count == 1 and black_count == 1:
            return True

        # King + Bishop vs King
        if white_count == 2 and white_types == {PieceType.KING, PieceType.BISHOP} and black_count == 1:
            return True
        if black_count == 2 and black_types == {PieceType.KING, PieceType.BISHOP} and white_count == 1:
            return True

        # King + Knight vs King
        if white_count == 2 and white_types == {PieceType.KING, PieceType.KNIGHT} and black_count == 1:
            return True
        if black_count == 2 and black_types == {PieceType.KING, PieceType.KNIGHT} and white_count == 1:
            return True

        # King + Bishop vs King + Bishop (same color squares)
        if (white_count == 2 and white_types == {PieceType.KING, PieceType.BISHOP} and
            black_count == 2 and black_types == {PieceType.KING, PieceType.BISHOP}):
            # Find bishop positions
            white_bishop_pos = next((r, c) for pt, r, c in pieces['white'] if pt == PieceType.BISHOP)
            black_bishop_pos = next((r, c) for pt, r, c in pieces['black'] if pt == PieceType.BISHOP)
            # Same color square if sum of coordinates has same parity
            if (white_bishop_pos[0] + white_bishop_pos[1]) % 2 == (black_bishop_pos[0] + black_bishop_pos[1]) % 2:
                return True

        return False

    def is_threefold_repetition(self):
        """Return True if the current position has occurred three times."""
        if len(self.move_history) < 8:
            return False

        current_position = self._get_position_key()

        # Rebuild every past position by replaying the game from the start.
        temp_board = ChessBoard()
        positions = [temp_board._get_position_key()]
        for move in self.move_history:
            _apply_move_to_array(temp_board.board, move)
            temp_board.current_turn = temp_board.current_turn.opposite()
            positions.append(temp_board._get_position_key())

        return positions.count(current_position) >= 3

    def _get_position_key(self):
        """Return a hashable key identifying the current position and side to move."""
        key = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece:
                    key.append((r, c, piece.piece_type.value, piece.color.value))
        key.append(self.current_turn.value)
        return tuple(key)

    def is_fifty_move_rule(self):
        """Return True if the last 50 full moves had no capture and no pawn move."""
        if len(self.move_history) < 100:  # 50 full moves = 100 half-moves
            return False

        for move in self.move_history[-100:]:
            if move.captured_piece:
                return False
            # The moved piece now sits on the destination square.
            to_row, to_col = move.to_position
            piece = self.board[to_row][to_col]
            if piece and piece.piece_type == PieceType.PAWN:
                return False
            if move.promotion_piece:  # a promotion means a pawn moved
                return False

        return True

    def get_all_valid_moves(self):
        """Return [((from_row, from_col), (to_row, to_col)), ...] for the current player."""
        all_moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == self.current_turn:
                    for move in self.get_valid_moves(r, c):
                        all_moves.append(((r, c), move))
        return all_moves

    def make_move_with_undo(self, from_row, from_col, to_row, to_col):
        """
        Play a move and return undo info, or None if the move is illegal.

        Used by the AI to search moves without deep-copying the board; pass the
        returned dict to unmake_move to restore the previous position.
        """
        valid_moves = self.get_valid_moves(from_row, from_col)

        if (to_row, to_col) not in valid_moves:
            return None

        piece = self.board[from_row][from_col]
        captured_piece = self.board[to_row][to_col]

        # Store undo information
        undo_info = {
            'from_row': from_row,
            'from_col': from_col,
            'to_row': to_row,
            'to_col': to_col,
            'piece': piece,
            'captured_piece': captured_piece,
            'prev_has_moved': piece.has_moved,
            'prev_en_passant': self.en_passant_target,
            'is_castling': False,
            'is_en_passant': False,
            'is_promotion': False,
            'prev_piece_type': piece.piece_type,
            'rook_from': None,
            'rook_to': None,
            'rook': None,
            'rook_prev_has_moved': None,
            'ep_captured_pos': None,
            'ep_captured_piece': None,
        }

        # Handle castling
        if piece.piece_type == PieceType.KING and abs(to_col - from_col) == 2:
            undo_info['is_castling'] = True
            if to_col > from_col:  # Kingside
                rook = self.board[from_row][7]
                undo_info['rook'] = rook
                undo_info['rook_from'] = (from_row, 7)
                undo_info['rook_to'] = (from_row, 5)
                undo_info['rook_prev_has_moved'] = rook.has_moved
                self.board[from_row][5] = rook
                self.board[from_row][7] = None
                rook.has_moved = True
            else:  # Queenside
                rook = self.board[from_row][0]
                undo_info['rook'] = rook
                undo_info['rook_from'] = (from_row, 0)
                undo_info['rook_to'] = (from_row, 3)
                undo_info['rook_prev_has_moved'] = rook.has_moved
                self.board[from_row][3] = rook
                self.board[from_row][0] = None
                rook.has_moved = True

        # Handle en passant
        if piece.piece_type == PieceType.PAWN and self.en_passant_target == (to_row, to_col):
            undo_info['is_en_passant'] = True
            undo_info['ep_captured_pos'] = (from_row, to_col)
            undo_info['ep_captured_piece'] = self.board[from_row][to_col]
            self.board[from_row][to_col] = None

        # Make the move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.has_moved = True

        # Set en passant target
        self.en_passant_target = None
        if piece.piece_type == PieceType.PAWN and abs(to_row - from_row) == 2:
            self.en_passant_target = ((from_row + to_row) // 2, to_col)

        # Handle pawn promotion
        if piece.piece_type == PieceType.PAWN and (to_row == 0 or to_row == 7):
            undo_info['is_promotion'] = True
            piece.piece_type = PieceType.QUEEN

        # Switch turns
        self.current_turn = self.current_turn.opposite()

        return undo_info

    def unmake_move(self, undo_info):
        """
        Unmake a move using the undo information from make_move_with_undo.

        Args:
            undo_info: dict returned by make_move_with_undo
        """
        # Switch turns back
        self.current_turn = self.current_turn.opposite()

        from_row = undo_info['from_row']
        from_col = undo_info['from_col']
        to_row = undo_info['to_row']
        to_col = undo_info['to_col']
        piece = undo_info['piece']

        # Undo promotion
        if undo_info['is_promotion']:
            piece.piece_type = undo_info['prev_piece_type']

        # Move piece back
        self.board[from_row][from_col] = piece
        self.board[to_row][to_col] = undo_info['captured_piece']
        piece.has_moved = undo_info['prev_has_moved']

        # Restore en passant target
        self.en_passant_target = undo_info['prev_en_passant']

        # Undo castling
        if undo_info['is_castling']:
            rook = undo_info['rook']
            rook_from = undo_info['rook_from']
            rook_to = undo_info['rook_to']
            self.board[rook_from[0]][rook_from[1]] = rook
            self.board[rook_to[0]][rook_to[1]] = None
            rook.has_moved = undo_info['rook_prev_has_moved']

        # Undo en passant capture
        if undo_info['is_en_passant']:
            ep_pos = undo_info['ep_captured_pos']
            self.board[ep_pos[0]][ep_pos[1]] = undo_info['ep_captured_piece']

    def get_captured_pieces(self):
        """
        Get all captured pieces grouped by which player captured them.

        Returns:
            dict with 'white' and 'black' keys, each containing a list of captured Piece objects.
            'white' = pieces captured by white (black pieces)
            'black' = pieces captured by black (white pieces)
        """
        captured = {'white': [], 'black': []}

        for i, move in enumerate(self.move_history):
            if move.captured_piece:
                # Even moves (0, 2, 4...) are white's moves, odd are black's
                if i % 2 == 0:
                    captured['white'].append(move.captured_piece)
                else:
                    captured['black'].append(move.captured_piece)

        return captured

    def get_move_history_notation(self):
        """
        Return the move history in algebraic notation, e.g. ['e4', 'e5', 'Nf3'].

        The game is replayed from the start so each move is named using the piece
        that actually stood on the from-square at that point.
        """
        notation_list = []
        replay = create_starting_board()

        for move in self.move_history:
            from_row, from_col = move.from_position
            piece = replay[from_row][from_col]
            if not piece:
                notation_list.append("???")
                continue
            notation_list.append(self._move_to_notation(move, piece))
            _apply_move_to_array(replay, move)

        return notation_list

    @staticmethod
    def _move_to_notation(move, piece):
        """Render a single move as an algebraic notation string."""
        from_row, from_col = move.from_position
        to_row, to_col = move.to_position

        if move.is_castling:
            return 'O-O' if to_col > from_col else 'O-O-O'

        to_square = FILES[to_col] + RANKS[to_row]
        capture = 'x' if move.captured_piece else ''

        if piece.piece_type == PieceType.PAWN:
            # Pawn captures are written with the origin file, e.g. "exd5".
            notation = f"{FILES[from_col]}{capture}{to_square}" if capture else to_square
        else:
            notation = f"{_ALGEBRAIC_SYMBOLS[piece.piece_type]}{capture}{to_square}"

        if move.promotion_piece:
            notation += f"={_ALGEBRAIC_SYMBOLS.get(move.promotion_piece.piece_type, 'Q')}"
        return notation