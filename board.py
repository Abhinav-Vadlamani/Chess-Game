from piece import Piece, Move
from constants import PieceType, Color
from moves import *

class ChessBoard:
    def __init__(self):
        """
        Initialize the chess board object
        """

        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.current_turn = Color.WHITE
        self.move_history = []
        self.en_passant_target = None
        self.setup_board()

    def setup_board(self):
        """
        Setup the initial chess position
        """
        # Pawns
        for i in range(8):
            self.board[1][i] = Piece(PieceType.PAWN, Color.BLACK)
            self.board[6][i] = Piece(PieceType.PAWN, Color.WHITE)
        
        # Rooks
        self.board[0][0] = Piece(PieceType.ROOK, Color.BLACK)
        self.board[0][7] = Piece(PieceType.ROOK, Color.BLACK)
        self.board[7][0] = Piece(PieceType.ROOK, Color.WHITE)
        self.board[7][7] = Piece(PieceType.ROOK, Color.WHITE)
        
        # Knights
        self.board[0][1] = Piece(PieceType.KNIGHT, Color.BLACK)
        self.board[0][6] = Piece(PieceType.KNIGHT, Color.BLACK)
        self.board[7][1] = Piece(PieceType.KNIGHT, Color.WHITE)
        self.board[7][6] = Piece(PieceType.KNIGHT, Color.WHITE)
        
        # Bishops
        self.board[0][2] = Piece(PieceType.BISHOP, Color.BLACK)
        self.board[0][5] = Piece(PieceType.BISHOP, Color.BLACK)
        self.board[7][2] = Piece(PieceType.BISHOP, Color.WHITE)
        self.board[7][5] = Piece(PieceType.BISHOP, Color.WHITE)
        
        # Queens
        self.board[0][3] = Piece(PieceType.QUEEN, Color.BLACK)
        self.board[7][3] = Piece(PieceType.QUEEN, Color.WHITE)
        
        # Kings
        self.board[0][4] = Piece(PieceType.KING, Color.BLACK)
        self.board[7][4] = Piece(PieceType.KING, Color.WHITE)

    def get_piece(self, row, col):
        """
        Return piece at a given position

        Args:
            row: row where piece is
            col: column where piece is
        
        Returns:
            piece at the position
        """

        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def get_valid_moves(self, row, col):
        """
        Returns all valid moves for the piece at the given position

        Args:
            row: row where piece is
            col: column where piece is

        Returns:
            list of all valid moves
        """

        piece = self.get_piece(row, col)
        if not piece or piece.color != self.current_turn:
            return []
        
        # return pseudo legal moves
        moves = self._get_pseudo_legal_moves(row, col)

        # filter out moves that leave king in check
        valid_moves = []
        for move in moves:
            if self._is_legal_move(row, col, move[0], move[1]):
                valid_moves.append(move)
        
        return valid_moves
    
    def _get_pseudo_legal_moves(self, row, col):
        """
        Return all legal moves without checking if king is in check

        Args:
            row: row where piece is
            col: column where piece is
        
        Returns:
            list of moves
        """

        piece = self.board[row][col]

        if piece.piece_type == PieceType.PAWN:
            moves = get_pawn_moves(self.board, row, col, self.en_passant_target)

        elif piece.piece_type == PieceType.KNIGHT:
            moves = get_knight_moves(self.board, row, col)

        elif piece.piece_type == PieceType.BISHOP:
            moves = get_bishop_moves(self.board, row, col)

        elif piece.piece_type == PieceType.ROOK:
            moves = get_rook_moves(self.board, row, col)

        elif piece.piece_type == PieceType.QUEEN:
            moves = get_queen_moves(self.board, row, col)

        elif piece.piece_type == PieceType.KING:
            moves = get_king_moves(self.board, row, col)

            # Add castling moves
            if not piece.has_moved and not self.is_in_check(piece.color):
                if self._can_castle_kingside(row, col):
                    moves.append((row, col + 2))
                if self._can_castle_queenside(row, col):
                    moves.append((row, col - 2))
        else:
            moves = []
        
        return moves
    
    def _can_castle_kingside(self, row, col):
        """
        Check if kingside castling is possible

        Args:
            row: current king row
            col: current king col
        
        Returns:
            True if kingside castling is possible, else false
        """

        rook = self.board[row][7]
        if not rook or rook.piece_type != PieceType.ROOK or rook.has_moved:
            return False
        
        # Check if squares are empty and not under attack
        for c in range(col + 1, 7):
            if self.board[row][c] is not None:
                return False
            if c <= col + 2 and self._is_square_attacked(row, c, self.current_turn):
                return False
            
        return True
    
    def _can_castle_queenside(self, row, col):
        """
        Check if queenside castling is possible

        Args:
            row: current king row
            col: current king col
        
        Returns:
            True if queenside castling is possible, else false
        """

        rook = self.board[row][0]
        if not rook or rook.piece_type != PieceType.ROOK or rook.has_moved:
            return False
        
        # Check if squares are empty and not under attack
        for c in range(1, col):
            if self.board[row][c] is not None:
                return False
            if c >= col - 2 and self._is_square_attacked(row, c, self.current_turn):
                return False
        
        return True
    
    def _is_square_attacked(self, row, col, by_color):
        """
        Check if square is attacked by opponent

        Args:
            row: row of the square
            col: column of the square
            by_color: current color
        
        Returns:
            True if square is attacked, else false
        """
        opponent_color = by_color.opposite()

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == opponent_color:
                    # Get attack squares for this piece
                    if piece.piece_type == PieceType.PAWN:
                        moves = get_pawn_attack_squares(self.board, r, c)

                    elif piece.piece_type == PieceType.KNIGHT:
                        moves = get_knight_moves(self.board, r, c)

                    elif piece.piece_type == PieceType.BISHOP:
                        moves = get_bishop_moves(self.board, r, c)

                    elif piece.piece_type == PieceType.ROOK:
                        moves = get_rook_moves(self.board, r, c)

                    elif piece.piece_type == PieceType.QUEEN:
                        moves = get_queen_moves(self.board, r, c)

                    elif piece.piece_type == PieceType.KING:
                        moves = get_king_attack_squares(self.board, r, c)

                    else:
                        moves = []
                    
                    if (row, col) in moves:
                        return True
        
        return False
    
    def _is_legal_move(self, from_row, from_col, to_row, to_col):
        """
        Check if move is legal (doesn't leave king in check)

        Args:
            from_row: starting row
            from_col: starting column
            to_row: ending row
            to_col: ending column

        Returns:
            True if the move is legal, else false
        """
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

    def is_in_check(self, color):
        """
        Check if king of given color is under check

        Args:
            color: color to check
        """
        
        king_pos = None
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.piece_type == PieceType.KING and piece.color == color:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
    
        return self._is_square_attacked(king_pos[0], king_pos[1], color)
    
    def make_move(self, from_row, from_col, to_row, to_col, promotion_piece=None):
        """
        Make a move on the board

        Args:
            from_row: starting row
            from_col: starting column
            to_row: ending row
            to_col: ending column
            promotion_piece: PieceType for pawn promotion (default: QUEEN)

        Returns:
            True if move was successful, else false
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
        """
        Check if a move would result in pawn promotion

        Args:
            from_row: starting row
            from_col: starting column
            to_row: ending row
            to_col: ending column

        Returns:
            True if the move is a pawn promotion
        """
        piece = self.get_piece(from_row, from_col)
        if piece and piece.piece_type == PieceType.PAWN:
            if (piece.color == Color.WHITE and to_row == 0) or \
               (piece.color == Color.BLACK and to_row == 7):
                return True
        return False

    def is_checkmate(self):
        """
        Checks if current player is checkmated
        """
        if not self.is_in_check(self.current_turn):
            return False

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == self.current_turn:
                    if len(self.get_valid_moves(r, c)) > 0:
                        return False
                    
        return True
    
    def is_stalemate(self):
        """
        Check if game is stalemate
        """
        if self.is_in_check(self.current_turn):
            return False

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == self.current_turn:
                    if len(self.get_valid_moves(r, c)) > 0:
                        return False
        return True

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
        """
        Check if the current position has occurred three times.
        """
        if len(self.move_history) < 8:
            return False

        current_position = self._get_position_key()
        count = 1

        # Check previous positions by replaying moves
        temp_board = ChessBoard()
        positions = [temp_board._get_position_key()]

        for move in self.move_history:
            from_row, from_col = move.from_position
            to_row, to_col = move.to_position
            promotion = move.promotion_piece.piece_type if move.promotion_piece else None
            temp_board.board[to_row][to_col] = temp_board.board[from_row][from_col]
            temp_board.board[from_row][from_col] = None

            # Handle castling
            if move.is_castling:
                if to_col > from_col:  # Kingside
                    temp_board.board[from_row][5] = temp_board.board[from_row][7]
                    temp_board.board[from_row][7] = None
                else:  # Queenside
                    temp_board.board[from_row][3] = temp_board.board[from_row][0]
                    temp_board.board[from_row][0] = None

            # Handle en passant
            if move.is_en_passant:
                temp_board.board[from_row][to_col] = None

            # Handle promotion
            if promotion:
                temp_board.board[to_row][to_col].piece_type = promotion

            temp_board.current_turn = temp_board.current_turn.opposite()
            positions.append(temp_board._get_position_key())

        # Count occurrences of current position
        count = positions.count(current_position)
        return count >= 3

    def _get_position_key(self):
        """
        Get a hashable key representing the current board position.
        """
        key = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece:
                    key.append((r, c, piece.piece_type.value, piece.color.value))
        key.append(self.current_turn.value)
        return tuple(key)

    def is_fifty_move_rule(self):
        """
        Check if 50 moves have been made without a pawn move or capture.
        """
        if len(self.move_history) < 100:  # 50 moves = 100 half-moves
            return False

        # Check last 100 half-moves (50 full moves)
        for move in self.move_history[-100:]:
            # Check for capture
            if move.captured_piece:
                return False
            # Check for pawn move
            from_row, from_col = move.from_position
            # We need to check what piece made the move - look at to_position
            to_row, to_col = move.to_position
            piece = self.board[to_row][to_col]
            if piece and piece.piece_type == PieceType.PAWN:
                return False
            # Also check promotion (which means a pawn moved)
            if move.promotion_piece:
                return False

        return True

    def get_all_valid_moves(self):
        """
        Returns list of all valid moves for the current player
        """

        all_moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == self.current_turn:
                    moves = self.get_valid_moves(r, c)
                    for move in moves:
                        all_moves.append(((r, c), move))
        return all_moves

    def make_move_with_undo(self, from_row, from_col, to_row, to_col):
        """
        Make a move and return undo information for unmake_move.
        This is used by the AI for fast move simulation without deep copying.

        Args:
            from_row: starting row
            from_col: starting column
            to_row: ending row
            to_col: ending column

        Returns:
            undo_info dict if move was made, None if invalid
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
        Get move history in algebraic notation.

        Returns:
            List of move strings in algebraic notation (e.g., ['e4', 'e5', 'Nf3', 'Nc6'])
        """
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

        piece_symbols = {
            PieceType.KING: 'K',
            PieceType.QUEEN: 'Q',
            PieceType.ROOK: 'R',
            PieceType.BISHOP: 'B',
            PieceType.KNIGHT: 'N',
            PieceType.PAWN: ''
        }

        notation_list = []

        for move in self.move_history:
            from_row, from_col = move.from_position
            to_row, to_col = move.to_position

            # Castling
            if move.is_castling:
                if to_col > from_col:
                    notation = 'O-O'  # Kingside
                else:
                    notation = 'O-O-O'  # Queenside
            else:
                # Get piece symbol (need to figure out what piece moved)
                # Since the piece has already moved, we need to look at the destination
                # But for promotions, piece_type changed. Use promotion_piece info.
                if move.promotion_piece:
                    piece_symbol = ''  # Pawn
                    promotion_symbol = piece_symbols.get(move.promotion_piece.piece_type, '')
                else:
                    # We need to reconstruct what piece was there
                    # Look at the piece that's currently at to_position after all moves
                    # This is tricky - let's track it differently
                    # For now, we'll replay to find piece types
                    piece_symbol = ''
                    promotion_symbol = ''

                to_square = files[to_col] + ranks[to_row]

                # Check for capture
                capture = 'x' if move.captured_piece else ''

                # For pawns capturing, include the file
                if piece_symbol == '' and capture:
                    from_file = files[from_col]
                    notation = f"{from_file}{capture}{to_square}"
                else:
                    notation = f"{piece_symbol}{capture}{to_square}"

                # Add promotion
                if move.promotion_piece:
                    notation += f"={piece_symbols.get(move.promotion_piece.piece_type, 'Q')}"

            notation_list.append(notation)

        # Now we need to add piece symbols - replay the game to track pieces
        # Let's do a proper implementation
        return self._get_proper_notation()

    def _get_proper_notation(self):
        """
        Get proper algebraic notation by replaying moves.
        """
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

        piece_symbols = {
            PieceType.KING: 'K',
            PieceType.QUEEN: 'Q',
            PieceType.ROOK: 'R',
            PieceType.BISHOP: 'B',
            PieceType.KNIGHT: 'N',
            PieceType.PAWN: ''
        }

        notation_list = []

        # Create a temporary board to replay
        temp_board = [[None for _ in range(8)] for _ in range(8)]

        # Setup initial position
        for i in range(8):
            temp_board[1][i] = Piece(PieceType.PAWN, Color.BLACK)
            temp_board[6][i] = Piece(PieceType.PAWN, Color.WHITE)

        temp_board[0][0] = Piece(PieceType.ROOK, Color.BLACK)
        temp_board[0][7] = Piece(PieceType.ROOK, Color.BLACK)
        temp_board[7][0] = Piece(PieceType.ROOK, Color.WHITE)
        temp_board[7][7] = Piece(PieceType.ROOK, Color.WHITE)

        temp_board[0][1] = Piece(PieceType.KNIGHT, Color.BLACK)
        temp_board[0][6] = Piece(PieceType.KNIGHT, Color.BLACK)
        temp_board[7][1] = Piece(PieceType.KNIGHT, Color.WHITE)
        temp_board[7][6] = Piece(PieceType.KNIGHT, Color.WHITE)

        temp_board[0][2] = Piece(PieceType.BISHOP, Color.BLACK)
        temp_board[0][5] = Piece(PieceType.BISHOP, Color.BLACK)
        temp_board[7][2] = Piece(PieceType.BISHOP, Color.WHITE)
        temp_board[7][5] = Piece(PieceType.BISHOP, Color.WHITE)

        temp_board[0][3] = Piece(PieceType.QUEEN, Color.BLACK)
        temp_board[7][3] = Piece(PieceType.QUEEN, Color.WHITE)

        temp_board[0][4] = Piece(PieceType.KING, Color.BLACK)
        temp_board[7][4] = Piece(PieceType.KING, Color.WHITE)

        for move in self.move_history:
            from_row, from_col = move.from_position
            to_row, to_col = move.to_position

            piece = temp_board[from_row][from_col]
            if not piece:
                notation_list.append("???")
                continue

            # Castling
            if move.is_castling:
                if to_col > from_col:
                    notation = 'O-O'
                else:
                    notation = 'O-O-O'
            else:
                piece_symbol = piece_symbols.get(piece.piece_type, '')
                to_square = files[to_col] + ranks[to_row]
                capture = 'x' if move.captured_piece else ''

                if piece.piece_type == PieceType.PAWN:
                    if capture:
                        notation = f"{files[from_col]}{capture}{to_square}"
                    else:
                        notation = to_square
                else:
                    notation = f"{piece_symbol}{capture}{to_square}"

                # Promotion
                if move.promotion_piece:
                    notation += f"={piece_symbols.get(move.promotion_piece.piece_type, 'Q')}"

            notation_list.append(notation)

            # Update temp board
            temp_board[to_row][to_col] = piece
            temp_board[from_row][from_col] = None

            # Handle castling rook movement
            if move.is_castling:
                if to_col > from_col:  # Kingside
                    temp_board[from_row][5] = temp_board[from_row][7]
                    temp_board[from_row][7] = None
                else:  # Queenside
                    temp_board[from_row][3] = temp_board[from_row][0]
                    temp_board[from_row][0] = None

            # Handle en passant
            if move.is_en_passant:
                temp_board[from_row][to_col] = None

            # Handle promotion
            if move.promotion_piece:
                temp_board[to_row][to_col].piece_type = move.promotion_piece.piece_type

        return notation_list