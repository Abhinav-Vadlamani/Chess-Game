import pygame
from board import ChessBoard
from ai import ChessAI
from renderer import Renderer
from constants import Color, WINDOW_SIZE, BOARD_OFFSET, BOARD_SIZE, SQUARE_SIZE, FPS

class ChessGame:
    def __init__(self):
        """
        Initialize the chess game
        """

        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Chess Game")
        self.clock = pygame.time.Clock()

        # Game state
        self.board = ChessBoard()
        self.renderer = Renderer(self.screen)
        self.selected_square = None
        self.valid_moves = []
        self.game_mode = None  # 'pvp' or 'pvb'
        self.player_color = None  # Color.WHITE or Color.BLACK (for PvBot mode)
        self.ai_difficulty = None  # 'easy', 'medium', or 'hard'
        self.ai = None
        self.game_over = False
        self.winner = None

    def run(self):
        """
        Main game loop
        """
        running = True

        while running:
            self.clock.tick(FPS)

            # event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    running = self._handle_mouse_click(event.pos)
                
                if event.type == pygame.KEYDOWN:
                    running = self._handle_keypress(event.key)
            self._render()
            pygame.display.flip()

        pygame.quit()
    
    def _handle_mouse_click(self, pos):
        """
        Handle mouse click events

        Args:
            pos: Mouse position
        
        Returns:
            True to continue running, else false
        """

        if self.game_mode is None or self.game_mode == 'pvb_difficulty_select' or self.game_mode == 'pvb_color_select':
            # Handle menu clicks
            return self._handle_menu_click(pos)
        else:
            # Handle game board clicks
            self._handle_board_click(pos)
            return True
        
    def _handle_menu_click(self, pos):
        """
        Handle menu click events

        Args:
            pos: Mouse position
        
        Returns:
            True to continue running, else false
        """

        buttons = self.renderer.draw_menu(self.game_mode)

        # Unpack buttons based on game mode
        if self.game_mode is None:
            # Main menu: mode selection
            pvp_button, pvb_button = buttons
            
            if pvp_button.collidepoint(pos):
                self.game_mode = 'pvp'
                self.player_color = None  # Both players are human
                self.reset_game()
            elif pvb_button.collidepoint(pos):
                self.game_mode = 'pvb_difficulty_select'
                # Show difficulty selection next

        elif self.game_mode == 'pvb_difficulty_select':
            # Difficulty selection menu for PvBot
            easy_button, medium_button, hard_button, back_button = buttons
            
            if easy_button.collidepoint(pos):
                self.ai_difficulty = 'easy'
                self.game_mode = 'pvb_color_select'
            elif medium_button.collidepoint(pos):
                self.ai_difficulty = 'medium'
                self.game_mode = 'pvb_color_select'
            elif hard_button.collidepoint(pos):
                self.ai_difficulty = 'hard'
                self.game_mode = 'pvb_color_select'
            elif back_button.collidepoint(pos):
                self.game_mode = None
                self.ai_difficulty = None

        elif self.game_mode == 'pvb_color_select':
            # Color selection menu for PvBot
            white_button, black_button, back_button = buttons
            
            if white_button.collidepoint(pos):
                self.game_mode = 'pvb'
                self.player_color = Color.WHITE
                ai_color = Color.BLACK
                self.ai = ChessAI(difficulty=self.ai_difficulty, ai_color=ai_color)
                self.reset_game()
            elif black_button.collidepoint(pos):
                self.game_mode = 'pvb'
                self.player_color = Color.BLACK
                ai_color = Color.WHITE
                self.ai = ChessAI(difficulty=self.ai_difficulty, ai_color=ai_color)
                self.reset_game()
                # AI makes first move
                if ai_color == Color.WHITE:
                    self._make_ai_move()
            elif back_button.collidepoint(pos):
                self.game_mode = 'pvb_difficulty_select'
        
        return True
    
    def _handle_board_click(self, pos):
        """
        Handle clicks on the chess board

        Args:
            pos: mouse position
        """

        if self.game_over:
            return

        # In PvBot mode, only allow moves on player's turn
        if self.game_mode == 'pvb' and self.board.current_turn != self.player_color:
            return
        
        square = self._get_square_from_mouse(pos)
        if not square:
            return
        
        row, col = square

        if self.selected_square:
            # Try to make a move
            self._try_make_move(row, col)
        else:
            # Select a piece
            self._select_piece(row, col)

    def _try_make_move(self, to_row, to_col):
        """
        Try to make a move from the selected square

        Args:
            to_row: row to move to
            to_col: col to move to
        """

        from_row, from_col = self.selected_square
        
        if self.board.make_move(from_row, from_col, to_row, to_col):
            # Move successful
            self.selected_square = None
            self.valid_moves = []
            self._check_game_over()
            
            # AI move (if playing against bot and it's AI's turn)
            if self.game_mode == 'pvb' and self.board.current_turn != self.player_color and not self.game_over:
                self._make_ai_move()
        else:
            # Invalid move, try selecting new piece
            piece = self.board.get_piece(to_row, to_col)
            if piece and piece.color == self.board.current_turn:
                self._select_piece(to_row, to_col)
            else:
                self.selected_square = None
                self.valid_moves = []

    def _select_piece(self, row, col):
        """
        Select a piece at the given position

        Args:
            row: row of the piece
            col: column of the piece
        """

        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.board.current_turn:
            self.selected_square = (row, col)
            self.valid_moves = self.board.get_valid_moves(row, col)

    def _make_ai_move(self):
        """
        Make the AI's move
        """

        pygame.time.wait(300)  # Small delay for better UX
        ai_move = self.ai.get_best_move(self.board)
        
        if ai_move:
            from_pos, to_pos = ai_move
            self.board.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
            self._check_game_over()

    def _handle_keypress(self, key):
        """
        Handle keyboard events

        Args:
            key: pygame key constant
        
        Returns:
            True to continue running, else false
        """

        if key == pygame.K_r:
            # Restart game
            self.reset_game()
            # If AI plays white, make first move
            if self.game_mode == 'pvb' and self.ai and self.ai.ai_color == Color.WHITE:
                self._make_ai_move()
        elif key == pygame.K_q:
            # Quit
            return False
        elif key == pygame.K_ESCAPE:
            # Return to menu
            self.game_mode = None
            self.player_color = None
            self.ai = None
            self.reset_game()
        
        return True
    
    def _get_square_from_mouse(self, pos):
        """
        Convert mouse position to board square

        Args:
            pos: Mouse position
        
        Returns:
            tuple of the square
        """

        x, y = pos
        if BOARD_OFFSET <= x < BOARD_OFFSET + BOARD_SIZE and BOARD_OFFSET <= y < BOARD_OFFSET + BOARD_SIZE:
            col = (x - BOARD_OFFSET) // SQUARE_SIZE
            row = (y - BOARD_OFFSET) // SQUARE_SIZE
            return (row, col)
        return None
    
    def _check_game_over(self):
        """
        Check if the game is over
        """

        # checkmate
        if self.board.is_checkmate():
            self.game_over = True
            self.winner = "Black" if self.board.current_turn == Color.WHITE else "White"
        
        # stalemate
        elif self.board.is_stalemate():
            self.game_over = True
            self.winner = None
    
    def reset_game(self):
        """
        Reset the game to initial state
        """

        # reset constants
        self.board = ChessBoard()
        self.selected_square = None
        self.valid_moves = []
        self.game_over = False
        self.winner = None
        
        # Preserve AI and player color for PvBot mode
        if self.game_mode == 'pvb' and self.ai:
            # AI already exists with correct color, keep it
            pass
        elif self.game_mode == 'pvb':
            # Shouldn't happen, but safety check
            self.ai = ChessAI(difficulty="medium", ai_color=Color.BLACK)
            self.player_color = Color.WHITE

    def _render(self):
        """
        Render the current game state
        """

        if self.game_mode is None or self.game_mode == 'pvb_difficulty_select' or self.game_mode == 'pvb_color_select':
            # Draw menu (main menu, difficulty selection, or color selection)
            self.renderer.draw_menu(self.game_mode)

        else:
            # Draw game
            self.screen.fill((49, 46, 43))  # BG_COLOR
            self.renderer.draw_board(self.board, self.selected_square, self.valid_moves)
            self.renderer.draw_pieces(self.board)
            self.renderer.draw_coordinates()
            self.renderer.draw_game_ui(self.board, self.game_mode, self.game_over, self.winner)

