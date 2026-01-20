#!/usr/bin/env python3
"""
Quick Test Script for Renderer
Tests rendering functionality without needing the full game
"""

import pygame
import sys
from constants import PieceType, Color
from piece import Piece
from board import ChessBoard
from renderer import Renderer
from constants import WINDOW_SIZE, FPS


def test_renderer():
    """Test renderer functionality"""
    
    print("🎨 Testing Renderer...\n")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Renderer Test")
    clock = pygame.time.Clock()
    
    # Create renderer and board
    renderer = Renderer(screen)
    board = ChessBoard()
    
    # Test sequence
    tests = [
        ("Main Menu", "main_menu"),
        ("Difficulty Selection", "difficulty_select"),
        ("Color Selection", "color_select"),
        ("Empty Board", "empty_board"),
        ("Initial Board", "initial_board"),
        ("Highlighted Squares", "highlights"),
        ("Check Highlight", "check"),
        ("Game Over - Checkmate", "checkmate"),
        ("Game Over - Stalemate", "stalemate"),
    ]
    
    print("Visual tests - Press ENTER to advance through each test\n")
    
    test_index = 0
    running = True
    waiting_for_enter = True
    
    while running and test_index < len(tests):
        test_name, test_type = tests[test_index]
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Advance to next test
                    print(f"  ✅ {test_name}")
                    test_index += 1
                    waiting_for_enter = True
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
        
        # Clear screen
        screen.fill((49, 46, 43))
        
        # Render based on test type
        if test_type == "main_menu":
            renderer.draw_menu(None)
            
        elif test_type == "difficulty_select":
            renderer.draw_menu('pvb_difficulty_select')
            
        elif test_type == "color_select":
            renderer.draw_menu('pvb_color_select')
            
        elif test_type == "empty_board":
            # Clear board
            board.board = [[None for _ in range(8)] for _ in range(8)]
            renderer.draw_board(board)
            renderer.draw_coordinates()
            
        elif test_type == "initial_board":
            # Reset board
            board = ChessBoard()
            renderer.draw_board(board)
            renderer.draw_pieces(board)
            renderer.draw_coordinates()
            renderer.draw_game_ui(board, 'pvp', False, None)
            
        elif test_type == "highlights":
            # Show highlights
            selected = (6, 4)  # e2
            valid_moves = [(5, 4), (4, 4)]
            renderer.draw_board(board, selected, valid_moves)
            renderer.draw_pieces(board)
            renderer.draw_coordinates()
            
        elif test_type == "check":
            # Create check situation
            test_board = ChessBoard()
            test_board.board = [[None for _ in range(8)] for _ in range(8)]
            test_board.board[4][4] = Piece(PieceType.KING, Color.WHITE)
            test_board.board[4][0] = Piece(PieceType.ROOK, Color.BLACK)
            test_board.board[0][7] = Piece(PieceType.KING, Color.BLACK)
            renderer.draw_board(test_board)
            renderer.draw_pieces(test_board)
            renderer.draw_coordinates()
            
        elif test_type == "checkmate":
            renderer.draw_board(board)
            renderer.draw_pieces(board)
            renderer.draw_coordinates()
            renderer.draw_game_ui(board, 'pvp', True, "White")
            
        elif test_type == "stalemate":
            renderer.draw_board(board)
            renderer.draw_pieces(board)
            renderer.draw_coordinates()
            renderer.draw_game_ui(board, 'pvp', True, None)
        
        # Show test info at top
        font = pygame.font.Font(None, 28)
        title_text = font.render(f"Test {test_index + 1}/{len(tests)}: {test_name}", 
                                 True, (255, 255, 100))
        # Black background for better visibility
        title_bg = pygame.Surface((title_text.get_width() + 20, title_text.get_height() + 10))
        title_bg.fill((0, 0, 0))
        title_bg.set_alpha(180)
        screen.blit(title_bg, (10, 5))
        screen.blit(title_text, (20, 10))
        
        # Show instructions at bottom
        small_font = pygame.font.Font(None, 24)
        instruction_text = small_font.render("Press ENTER to continue | ESC to quit", 
                                            True, (255, 255, 255))
        inst_bg = pygame.Surface((instruction_text.get_width() + 20, instruction_text.get_height() + 10))
        inst_bg.fill((0, 0, 0))
        inst_bg.set_alpha(180)
        screen.blit(inst_bg, (10, WINDOW_SIZE - 35))
        screen.blit(instruction_text, (20, WINDOW_SIZE - 30))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    
    if test_index >= len(tests):
        print("\n" + "=" * 50)
        print("🎉 All Renderer Tests Passed!")
        print("=" * 50)
        print("\nThe renderer is working correctly!")
        return True
    else:
        print("\n⚠️  Tests interrupted")
        return False


def test_renderer_methods():
    """Test renderer methods programmatically"""
    
    print("🔬 Testing Renderer Methods...\n")
    
    try:
        # Initialize
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        renderer = Renderer(screen)
        board = ChessBoard()
        
        # Test 1: Renderer creation
        assert renderer is not None
        assert renderer.screen is not None
        assert renderer.font is not None
        print("  ✅ Renderer initialized")
        
        # Test 2: Piece symbols exist
        assert len(renderer.PIECE_SYMBOLS) == 12
        print("  ✅ All 12 piece symbols defined")
        
        # Test 3: Draw menu returns buttons
        buttons = renderer.draw_menu(None)
        assert len(buttons) == 2  # PvP and PvB buttons
        print("  ✅ Main menu returns 2 buttons")
        
        # Test 4: Draw difficulty selection returns 4 buttons
        buttons = renderer.draw_menu('pvb_difficulty_select')
        assert len(buttons) == 4  # Easy, Medium, Hard, and Back buttons
        print("  ✅ Difficulty selection returns 4 buttons")
        
        # Test 5: Draw color selection returns 3 buttons
        buttons = renderer.draw_menu('pvb_color_select')
        assert len(buttons) == 3  # White, Black, and Back buttons
        print("  ✅ Color selection returns 3 buttons")
        
        # Test 6: Draw board doesn't crash
        renderer.draw_board(board)
        print("  ✅ Board drawing works")
        
        # Test 7: Draw pieces doesn't crash
        renderer.draw_pieces(board)
        print("  ✅ Piece drawing works")
        
        # Test 8: Draw coordinates doesn't crash
        renderer.draw_coordinates()
        print("  ✅ Coordinate drawing works")
        
        # Test 9: Draw UI doesn't crash
        renderer.draw_game_ui(board, 'pvp', False, None)
        print("  ✅ UI drawing works")
        
        # Test 10: Draw game over overlay doesn't crash
        renderer.draw_game_ui(board, 'pvp', True, "White")
        print("  ✅ Game over overlay works")
        
        pygame.quit()
        
        print("\n" + "=" * 50)
        print("✅ All Method Tests Passed!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("RENDERER TEST SUITE")
    print("=" * 50)
    print()
    
    # Test 1: Method tests (no window needed)
    success1 = test_renderer_methods()
    
    if not success1:
        print("\n⚠️  Method tests failed. Fix errors before visual tests.")
        return False
    
    print("\n")
    input("Press ENTER to start visual tests (or Ctrl+C to quit)...")
    print()
    
    # Test 2: Visual tests
    success2 = test_renderer()
    
    return success1 and success2


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)