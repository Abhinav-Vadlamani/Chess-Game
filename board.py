import copy
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
        Check if move is legal

        Args:
            from_row: starting row
            from_col: starting column
            to_row: ending row
            to_col: ending column
        
        Returns:
            True if the move is legal, else false
        """
        temp_board = copy.deepcopy(self)
        temp_board._make_move_unchecked(from_row, from_col, to_row, to_col)
        return not temp_board.is_in_check(self.current_turn)
    
    def _make_move_unchecked(self, from_row, from_col, to_row, to_col):
        """
        Simulate move

        Args:
            from_row: starting row
            from_col: starting column
            to_row: ending row
            to_col: ending column
        """

        piece = self.board[from_row][from_col]
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None

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
    
    def make_move(self, from_row, from_col, to_row, to_col):
        """
        Make a move on the board

        Args:
            from_row: starting row
            from_col: starting column
            to_row: ending row
            to_col: ending column
        
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
            piece.piece_type = PieceType.QUEEN  # Auto-promote to queen
            promoted = True

        
        # Record move
        move = Move(from_position=(from_row, from_col), to_position=(to_row, to_col),
                   captured_piece=captured_piece, is_castling=is_castling,
                   is_en_passant=is_en_passant, promotion_piece = piece if promoted else None)
        self.move_history.append(move)
        
        # Switch turns
        self.current_turn = self.current_turn.opposite()
        
        return True
    
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