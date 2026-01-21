import random
import time
from constants import Color, PIECE_VALUES, AI_DIFFICULTY_DEPTHS, PieceType
import sunfish

class ChessAI:
    def __init__(self, difficulty = "medium", ai_color = Color.BLACK):
        """
        Initialize Chess AI

        Args:
            difficulty: players selected difficulty
            ai_color: color the AI plays
        """

        self.difficulty = difficulty
        self.depth = AI_DIFFICULTY_DEPTHS.get(difficulty, 2)
        self.ai_color = ai_color

    def get_best_move(self, board):
        """
        Get the best move given the current position

        Args:
            board: ChessBoard instance

        Returns:
            Move if move available
        """

        if self.difficulty == "easy":
            return self._get_random_move(board)
        elif self.difficulty == "hard":
            return self._get_sunfish_move(board)
        else:
            return self._get_minimax_move(board)

    def _get_random_move(self, board):
        """
        Get a random valid move:

        Args:
            board: ChessBoard instance
        """

        all_moves = board.get_all_valid_moves()
        return random.choice(all_moves) if all_moves else None

    def _board_to_sunfish_position(self, board):
        """
        Convert ChessBoard to Sunfish Position

        Args:
            board: ChessBoard instance

        Returns:
            Sunfish Position object
        """
        # Build the 120-char board string
        # Sunfish board layout: 2 padding rows, 8 board rows, 2 padding rows
        # Each row: 1 padding char + 8 squares + newline = 10 chars

        board_str = "         \n" * 2  # Top padding

        piece_map = {
            PieceType.PAWN: 'P',
            PieceType.KNIGHT: 'N',
            PieceType.BISHOP: 'B',
            PieceType.ROOK: 'R',
            PieceType.QUEEN: 'Q',
            PieceType.KING: 'K',
        }

        for row in range(8):
            board_str += " "  # Left padding
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece is None:
                    board_str += "."
                else:
                    char = piece_map[piece.piece_type]
                    if piece.color == Color.BLACK:
                        char = char.lower()
                    board_str += char
            board_str += "\n"

        board_str += "         \n" * 2  # Bottom padding

        # Calculate score from white's perspective
        score = 0
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    idx = sunfish.board_to_sunfish_index(row, col)
                    char = piece_map[piece.piece_type]
                    if piece.color == Color.WHITE:
                        score += sunfish.pst[char][idx]
                    else:
                        # For black pieces, use mirrored index
                        score -= sunfish.pst[char][119 - idx]

        # Determine castling rights
        # White castling (wc): [queenside, kingside]
        white_king = board.get_piece(7, 4)
        white_qrook = board.get_piece(7, 0)
        white_krook = board.get_piece(7, 7)
        wc_queenside = (white_king and not white_king.has_moved and
                        white_qrook and white_qrook.piece_type == PieceType.ROOK and
                        not white_qrook.has_moved)
        wc_kingside = (white_king and not white_king.has_moved and
                       white_krook and white_krook.piece_type == PieceType.ROOK and
                       not white_krook.has_moved)

        # Black castling (bc): [queenside, kingside]
        black_king = board.get_piece(0, 4)
        black_qrook = board.get_piece(0, 0)
        black_krook = board.get_piece(0, 7)
        bc_queenside = (black_king and not black_king.has_moved and
                        black_qrook and black_qrook.piece_type == PieceType.ROOK and
                        not black_qrook.has_moved)
        bc_kingside = (black_king and not black_king.has_moved and
                       black_krook and black_krook.piece_type == PieceType.ROOK and
                       not black_krook.has_moved)

        wc = (wc_queenside, wc_kingside)
        bc = (bc_queenside, bc_kingside)

        # En passant square
        ep = 0
        if board.en_passant_target:
            ep_row, ep_col = board.en_passant_target
            ep = sunfish.board_to_sunfish_index(ep_row, ep_col)

        # King passant (for detecting castling through check) - set to 0 for now
        kp = 0

        pos = sunfish.Position(board_str, score, wc, bc, ep, kp)

        # Sunfish always plays as white (uppercase), so if it's black's turn,
        # we need to rotate the position
        if board.current_turn == Color.BLACK:
            pos = pos.rotate()

        return pos

    def _get_sunfish_move(self, board):
        """
        Get best move using Sunfish engine

        Args:
            board: ChessBoard instance

        Returns:
            Move tuple ((from_row, from_col), (to_row, to_col))
        """
        pos = self._board_to_sunfish_position(board)

        searcher = sunfish.Searcher()

        # Search with time limit
        start_time = time.time()
        think_time = 1.0  # Think for 1 second

        best_move = None
        for depth, gamma, score, move in searcher.search([pos]):
            if score >= gamma and move:
                best_move = move
            if time.time() - start_time > think_time:
                break

        if not best_move:
            # Fallback to random move if Sunfish fails
            return self._get_random_move(board)

        # Convert Sunfish move back to our format
        i, j, prom = best_move

        # If it was black's turn, the position was rotated, so we need to un-rotate the move
        if board.current_turn == Color.BLACK:
            i = 119 - i
            j = 119 - j

        from_row, from_col = sunfish.sunfish_index_to_board(i)
        to_row, to_col = sunfish.sunfish_index_to_board(j)

        return ((from_row, from_col), (to_row, to_col))

    def _get_minimax_move(self, board):
        """
        Get best move based on minimax algorithm

        Args:
            board: ChessBoard instance
        """

        best_move = None
        best_value = float('-inf')

        all_moves = board.get_all_valid_moves()

        for move in all_moves:
            from_pos = move[0]
            to_pos = move[1]

            # Make move, evaluate, then unmake (no deep copy needed)
            undo_info = board.make_move_with_undo(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
            value = self._minimax(board, self.depth - 1, float('-inf'), float('inf'), False)
            board.unmake_move(undo_info)

            if value > best_value:
                best_value = value
                best_move = (from_pos, to_pos)
        return best_move

    def _minimax(self, board, depth, alpha, beta, maximizing):
        """
        Minimax algorithm with alpha-beta pruning

        Args:
            board: ChessBoard instance
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing: True if maximizing player, else False

        Returns:
            Evaluation score
        """

        if depth == 0 or board.is_checkmate() or board.is_stalemate():
            return self._evaluate_board(board)

        all_moves = board.get_all_valid_moves()

        if maximizing:
            max_eval = float('-inf')
            for from_pos, to_pos in all_moves:
                undo_info = board.make_move_with_undo(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                eval_score = self._minimax(board, depth - 1, alpha, beta, False)
                board.unmake_move(undo_info)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for from_pos, to_pos in all_moves:
                undo_info = board.make_move_with_undo(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                eval_score = self._minimax(board, depth - 1, alpha, beta, True)
                board.unmake_move(undo_info)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval

    def _evaluate_board(self, board):
        """
        Evaluate board's position

        Args:
            board: ChessBoard instance

        Returns:
            AI's position's score
        """

        # Checkmate evaluation
        if board.is_checkmate():
            # If it's AI's turn and checkmate, AI lost (very negative)
            if board.current_turn == self.ai_color:
                return float('-inf')
            # If it's opponent's turn and checkmate, AI won (very positive)
            else:
                return float('inf')

        # Stalemate evaluation
        if board.is_stalemate():
            return 0

        # Material evaluation
        score = 0
        for r in range(8):
            for c in range(8):
                piece = board.get_piece(r, c)
                if piece:
                    value = PIECE_VALUES[piece.piece_type.value]
                    if piece.color == self.ai_color:
                        score += value  # Good for AI
                    else:
                        score -= value  # Bad for AI

        return score
