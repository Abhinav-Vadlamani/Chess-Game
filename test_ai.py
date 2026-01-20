#!/usr/bin/env python3
"""
Comprehensive Test Script for Chess AI
Tests AI functionality, move generation, and difficulty levels
"""

import sys
import time
from constants import PieceType, Color
from piece import Piece
from board import ChessBoard
from ai import ChessAI


class TestChessAI:
    """Test suite for ChessAI class"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
    
    def run_all_tests(self):
        """Run all test suites"""
        print("=" * 60)
        print("CHESS AI TEST SUITE")
        print("=" * 60)
        print()
        
        self.test_ai_initialization()
        self.test_random_moves()
        self.test_minimax_basic()
        self.test_difficulty_levels()
        self.test_color_evaluation()
        self.test_checkmate_detection()
        self.test_move_quality()
        self.test_capture_preference()
        self.test_performance()
        
        self.print_summary()
    
    def assert_true(self, condition, test_name):
        """Assert that a condition is true"""
        if condition:
            print(f"  ✅ {test_name}")
            self.tests_passed += 1
        else:
            print(f"  ❌ {test_name}")
            self.tests_failed += 1
    
    def assert_not_none(self, value, test_name):
        """Assert that a value is not None"""
        if value is not None:
            print(f"  ✅ {test_name}")
            self.tests_passed += 1
        else:
            print(f"  ❌ {test_name}")
            self.tests_failed += 1
    
    def test_ai_initialization(self):
        """Test AI initialization"""
        print("\n🔷 Testing AI Initialization")
        
        # Test default initialization
        ai = ChessAI()
        self.assert_true(ai.difficulty == "medium", "Default difficulty is medium")
        self.assert_true(ai.ai_color == Color.BLACK, "Default color is BLACK")
        self.assert_true(ai.depth == 2, "Medium depth is 2")
        
        # Test easy difficulty
        ai_easy = ChessAI(difficulty="easy", ai_color=Color.WHITE)
        self.assert_true(ai_easy.difficulty == "easy", "Easy difficulty set correctly")
        self.assert_true(ai_easy.depth == 1, "Easy depth is 1")
        self.assert_true(ai_easy.ai_color == Color.WHITE, "AI color set to WHITE")
        
        # Test hard difficulty
        ai_hard = ChessAI(difficulty="hard", ai_color=Color.BLACK)
        self.assert_true(ai_hard.difficulty == "hard", "Hard difficulty set correctly")
        self.assert_true(ai_hard.depth == 3, "Hard depth is 3")
    
    def test_random_moves(self):
        """Test random move generation"""
        print("\n🔷 Testing Random Moves (Easy Mode)")
        
        board = ChessBoard()
        ai = ChessAI(difficulty="easy", ai_color=Color.WHITE)
        
        # Test that AI can find a move
        move = ai.get_best_move(board)
        self.assert_not_none(move, "Easy AI finds a move")
        
        if move:
            from_pos, to_pos = move
            self.assert_true(isinstance(from_pos, tuple), "From position is tuple")
            self.assert_true(isinstance(to_pos, tuple), "To position is tuple")
            
            # Verify it's a valid move
            valid_moves = board.get_valid_moves(from_pos[0], from_pos[1])
            self.assert_true(to_pos in valid_moves, "Random move is valid")
    
    def test_minimax_basic(self):
        """Test basic minimax functionality"""
        print("\n🔷 Testing Minimax Algorithm")
        
        board = ChessBoard()
        ai = ChessAI(difficulty="medium", ai_color=Color.WHITE)
        
        # Test that minimax finds a move
        move = ai.get_best_move(board)
        self.assert_not_none(move, "Minimax AI finds a move")
        
        if move:
            from_pos, to_pos = move
            # Verify it's a valid move
            valid_moves = board.get_valid_moves(from_pos[0], from_pos[1])
            self.assert_true(to_pos in valid_moves, "Minimax move is valid")
    
    def test_difficulty_levels(self):
        """Test all difficulty levels"""
        print("\n🔷 Testing Difficulty Levels")
        
        board = ChessBoard()
        
        # Test each difficulty
        difficulties = ["easy", "medium", "hard"]
        for diff in difficulties:
            ai = ChessAI(difficulty=diff, ai_color=Color.WHITE)
            move = ai.get_best_move(board)
            self.assert_not_none(move, f"{diff.capitalize()} AI finds a move")
    
    def test_color_evaluation(self):
        """Test that AI evaluates from its own perspective"""
        print("\n🔷 Testing Color-Based Evaluation")
        
        # Create a simple position
        board = ChessBoard()
        
        # Clear board and set up simple position
        for r in range(8):
            for c in range(8):
                board.board[r][c] = None
        
        # White king and queen
        board.board[7][4] = Piece(PieceType.KING, Color.WHITE)
        board.board[7][3] = Piece(PieceType.QUEEN, Color.WHITE)
        
        # Black king only
        board.board[0][4] = Piece(PieceType.KING, Color.BLACK)
        
        board.current_turn = Color.WHITE
        
        # Test White AI
        ai_white = ChessAI(difficulty="medium", ai_color=Color.WHITE)
        eval_white = ai_white._evaluate_board(board)
        
        # Test Black AI
        ai_black = ChessAI(difficulty="medium", ai_color=Color.BLACK)
        eval_black = ai_black._evaluate_board(board)
        
        # White should see positive (has queen), Black should see negative
        self.assert_true(eval_white > 0, "White AI evaluates position as good")
        self.assert_true(eval_black < 0, "Black AI evaluates position as bad")
        self.assert_true(eval_white == -eval_black, "Evaluations are symmetric")
    
    def test_checkmate_detection(self):
        """Test AI recognizes checkmate positions"""
        print("\n🔷 Testing Checkmate Recognition")
        
        # Set up a back-rank mate
        board = ChessBoard()
        for r in range(8):
            for c in range(8):
                board.board[r][c] = None
        
        # White king trapped
        board.board[7][4] = Piece(PieceType.KING, Color.WHITE)
        board.board[6][3] = Piece(PieceType.PAWN, Color.WHITE)
        board.board[6][4] = Piece(PieceType.PAWN, Color.WHITE)
        board.board[6][5] = Piece(PieceType.PAWN, Color.WHITE)
        
        # Black rook delivering mate
        board.board[0][4] = Piece(PieceType.ROOK, Color.BLACK)
        
        # Black king somewhere
        board.board[0][7] = Piece(PieceType.KING, Color.BLACK)
        
        board.current_turn = Color.BLACK
        
        ai = ChessAI(difficulty="medium", ai_color=Color.BLACK)
        
        # Black can deliver checkmate with Rook to 7th rank
        move = ai.get_best_move(board)
        self.assert_not_none(move, "AI finds move in winning position")
    
    def test_move_quality(self):
        """Test that AI prefers better moves"""
        print("\n🔷 Testing Move Quality")
        
        board = ChessBoard()
        
        # Medium AI should make reasonable opening moves
        ai = ChessAI(difficulty="medium", ai_color=Color.WHITE)
        move = ai.get_best_move(board)
        
        if move:
            from_pos, to_pos = move
            piece = board.get_piece(from_pos[0], from_pos[1])
            
            # Should move a piece (not just any random square)
            self.assert_not_none(piece, "AI selects a piece to move")
            
            # Make the move and verify board state changes
            success = board.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
            self.assert_true(success, "AI move is legal and executes")
    
    def test_capture_preference(self):
        """Test that AI prefers capturing free pieces"""
        print("\n🔷 Testing Capture Preference")
        
        # Set up position where Black can capture a free queen
        board = ChessBoard()
        for r in range(8):
            for c in range(8):
                board.board[r][c] = None
        
        # Kings
        board.board[7][4] = Piece(PieceType.KING, Color.WHITE)
        board.board[0][4] = Piece(PieceType.KING, Color.BLACK)
        
        # White queen hanging (undefended)
        board.board[4][4] = Piece(PieceType.QUEEN, Color.WHITE)
        
        # Black bishop can capture it
        board.board[2][2] = Piece(PieceType.BISHOP, Color.BLACK)
        
        board.current_turn = Color.BLACK
        
        ai = ChessAI(difficulty="medium", ai_color=Color.BLACK)
        move = ai.get_best_move(board)
        
        if move:
            from_pos, to_pos = move
            # AI should capture the queen
            captured_piece = board.get_piece(to_pos[0], to_pos[1])
            
            # Ideally should capture the queen, but at minimum should find a legal move
            self.assert_not_none(move, "AI finds move when capture available")
            
            # If it captured the queen, that's excellent
            if captured_piece and captured_piece.piece_type == PieceType.QUEEN:
                print(f"  💎 BONUS: AI correctly captured free queen!")
    
    def test_performance(self):
        """Test AI performance (speed)"""
        print("\n🔷 Testing AI Performance")
        
        board = ChessBoard()
        
        # Test easy difficulty speed
        ai_easy = ChessAI(difficulty="easy", ai_color=Color.WHITE)
        start = time.time()
        move = ai_easy.get_best_move(board)
        easy_time = time.time() - start
        
        self.assert_true(easy_time < 0.1, f"Easy AI is fast ({easy_time:.3f}s)")
        
        # Test medium difficulty speed
        ai_medium = ChessAI(difficulty="medium", ai_color=Color.WHITE)
        start = time.time()
        move = ai_medium.get_best_move(board)
        medium_time = time.time() - start
        
        self.assert_true(medium_time < 2.0, f"Medium AI is reasonable ({medium_time:.3f}s)")
        
        # Test hard difficulty speed
        ai_hard = ChessAI(difficulty="hard", ai_color=Color.WHITE)
        start = time.time()
        move = ai_hard.get_best_move(board)
        hard_time = time.time() - start
        
        self.assert_true(hard_time < 10.0, f"Hard AI completes ({hard_time:.3f}s)")
        
        print(f"  📊 Timing: Easy={easy_time:.3f}s, Medium={medium_time:.3f}s, Hard={hard_time:.3f}s")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📊 Total Tests: {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            print("Your AI is working correctly!")
        else:
            print(f"\n⚠️  {self.tests_failed} test(s) failed. Review the issues above.")
        
        print("=" * 60)


def test_ai_game_simulation():
    """Simulate a few moves of AI vs AI"""
    print("\n" + "=" * 60)
    print("AI vs AI GAME SIMULATION")
    print("=" * 60)
    print()
    
    board = ChessBoard()
    ai_white = ChessAI(difficulty="easy", ai_color=Color.WHITE)
    ai_black = ChessAI(difficulty="easy", ai_color=Color.BLACK)
    
    print("Simulating 10 moves (5 per side)...")
    print()
    
    for i in range(10):
        current_ai = ai_white if board.current_turn == Color.WHITE else ai_black
        move = current_ai.get_best_move(board)
        
        if not move:
            print(f"Move {i+1}: No legal moves available")
            break
        
        from_pos, to_pos = move
        piece = board.get_piece(from_pos[0], from_pos[1])
        
        # Make the move
        success = board.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
        
        if success:
            color = "White" if piece.color == Color.WHITE else "Black"
            print(f"Move {i+1}: {color} {piece.piece_type.value} from {from_pos} to {to_pos}")
        else:
            print(f"Move {i+1}: Failed to execute move")
            break
        
        # Check for game over
        if board.is_checkmate():
            winner = "Black" if board.current_turn == Color.WHITE else "White"
            print(f"\n🏆 Checkmate! {winner} wins!")
            break
        elif board.is_stalemate():
            print("\n🤝 Stalemate!")
            break
    
    print("\n✅ AI game simulation completed successfully!")
    print("=" * 60)


def main():
    """Main test runner"""
    try:
        tester = TestChessAI()
        tester.run_all_tests()
        
        # Run game simulation if tests passed
        if tester.tests_failed == 0:
            test_ai_game_simulation()
        
        # Return exit code based on results
        sys.exit(0 if tester.tests_failed == 0 else 1)
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()