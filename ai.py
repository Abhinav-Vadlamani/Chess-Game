import copy
import random
from constants import Color, PIECE_VALUES, AI_DIFFICULTY_DEPTHS

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

            # simulate move
            temp_board = copy.deepcopy(board)
            temp_board.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])

            value = self._minimax(temp_board, self.depth - 1, float('-inf'), float('inf'), False)

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
                temp_board = copy.deepcopy(board)
                temp_board.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                eval_score = self._minimax(temp_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for from_pos, to_pos in all_moves:
                temp_board = copy.deepcopy(board)
                temp_board.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                eval_score = self._minimax(temp_board, depth - 1, alpha, beta, True)
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

    
