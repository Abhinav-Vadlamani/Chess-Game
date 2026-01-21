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
        self.last_move = None  # (from_square, to_square) for highlighting
        self.pending_promotion = None  # (from_row, from_col, to_row, to_col) awaiting piece selection
        self.game_mode = None  # 'pvp' or 'pvb'
        self.player_color = None  # Color.WHITE or Color.BLACK (for PvBot mode)
        self.ai_difficulty = None  # 'easy', 'medium', or 'hard'
        self.ai = None
        self.game_over = False
        self.winner = None

        # Drag and drop state
        self.dragging = False
        self.drag_piece = None  # The piece being dragged
        self.drag_start = None  # (row, col) where drag started
        self.drag_pos = None  # Current mouse position while dragging

        # Timer state
        self.use_timer = False
        self.white_time = 0  # Time in milliseconds
        self.black_time = 0
        self.last_tick = None  # Last time we updated the timer

        # Time input state (for menu)
        self.time_input = {
            'white_minutes': '',
            'black_minutes': '',
            'white_seconds': '',
            'black_seconds': '',
            'active_field': None  # Which field is being edited
        }

    def run(self):
        """
        Main game loop
        """
        running = True

        while running:
            self.clock.tick(FPS)

            # Update timer if game is active
            self._update_timer()

            # event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    running = self._handle_mouse_down(event.pos)

                if event.type == pygame.MOUSEBUTTONUP:
                    self._handle_mouse_up(event.pos)

                if event.type == pygame.MOUSEMOTION:
                    self._handle_mouse_motion(event.pos)

                if event.type == pygame.KEYDOWN:
                    running = self._handle_keypress(event.key)

                # Handle text input for time control menu
                if event.type == pygame.TEXTINPUT:
                    self._handle_text_input(event.text)

            self._render()
            pygame.display.flip()

        pygame.quit()

    def _update_timer(self):
        """
        Update the active player's timer
        """
        if not self.use_timer or self.game_over or self.game_mode != 'pvp':
            return

        if self.last_tick is None:
            self.last_tick = pygame.time.get_ticks()
            return

        current_tick = pygame.time.get_ticks()
        elapsed = current_tick - self.last_tick
        self.last_tick = current_tick

        # Subtract from current player's time
        if self.board.current_turn == Color.WHITE:
            self.white_time -= elapsed
            if self.white_time <= 0:
                self.white_time = 0
                self.game_over = True
                self.winner = "Black"  # White ran out of time
        else:
            self.black_time -= elapsed
            if self.black_time <= 0:
                self.black_time = 0
                self.game_over = True
                self.winner = "White"  # Black ran out of time

    def _handle_text_input(self, text):
        """
        Handle text input for time control fields

        Args:
            text: The text that was input
        """
        if self.game_mode != 'pvp_time_select':
            return

        active = self.time_input['active_field']
        if active is None:
            return

        # Only allow digits
        if text.isdigit():
            current = self.time_input[active]
            # Limit to 2 digits for seconds, 3 for minutes
            max_len = 2 if 'seconds' in active else 3
            if len(current) < max_len:
                self.time_input[active] = current + text
    
    def _handle_mouse_down(self, pos):
        """
        Handle mouse button down events

        Args:
            pos: Mouse position

        Returns:
            True to continue running, else false
        """

        menu_modes = [None, 'pvb_difficulty_select', 'pvb_color_select', 'pvp_time_select']
        if self.game_mode in menu_modes:
            # Handle menu clicks
            return self._handle_menu_click(pos)
        else:
            # Handle game board clicks / start drag
            self._handle_board_mouse_down(pos)
            return True

    def _handle_mouse_up(self, pos):
        """
        Handle mouse button up events (end drag)

        Args:
            pos: Mouse position
        """
        if self.dragging:
            self._handle_drag_end(pos)
        elif self.pending_promotion:
            # Promotion dialog uses click (down+up on same spot)
            pass

    def _handle_mouse_motion(self, pos):
        """
        Handle mouse motion events (drag piece)

        Args:
            pos: Mouse position
        """
        if self.dragging:
            self.drag_pos = pos
        
    def _handle_menu_click(self, pos):
        """
        Handle menu click events

        Args:
            pos: Mouse position
        
        Returns:
            True to continue running, else false
        """

        buttons = self.renderer.draw_menu(self.game_mode, self.time_input)

        # Unpack buttons based on game mode
        if self.game_mode is None:
            # Main menu: mode selection
            pvp_button, pvb_button = buttons

            if pvp_button.collidepoint(pos):
                self.game_mode = 'pvp_time_select'
                self._reset_time_input()
            elif pvb_button.collidepoint(pos):
                self.game_mode = 'pvb_difficulty_select'
                # Show difficulty selection next

        elif self.game_mode == 'pvp_time_select':
            # Time control selection for PvP
            result = buttons  # This is a dict with input rects and buttons
            input_rects = result['input_rects']
            start_button = result['start_button']
            no_time_button = result['no_time_button']
            back_button = result['back_button']

            # Check input field clicks
            for field_name, rect in input_rects.items():
                if rect.collidepoint(pos):
                    self.time_input['active_field'] = field_name
                    return True

            if start_button.collidepoint(pos):
                # Start game with time control
                self.game_mode = 'pvp'
                self.player_color = None
                self.use_timer = True
                self._reset_timer_for_game()
                self.reset_game()
            elif no_time_button.collidepoint(pos):
                # Start game without time control
                self.game_mode = 'pvp'
                self.player_color = None
                self.use_timer = False
                self.reset_game()
            elif back_button.collidepoint(pos):
                self.game_mode = None
                self._reset_time_input()

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
    
    def _handle_board_mouse_down(self, pos):
        """
        Handle mouse down on the chess board (start drag or select)

        Args:
            pos: mouse position
        """

        if self.game_over:
            return

        # Handle promotion dialog clicks
        if self.pending_promotion:
            self._handle_promotion_click(pos)
            return

        # In PvBot mode, only allow moves on player's turn
        if self.game_mode == 'pvb' and self.board.current_turn != self.player_color:
            return

        square = self._get_square_from_mouse(pos)
        if not square:
            return

        row, col = square
        piece = self.board.get_piece(row, col)

        # If clicking on own piece, start drag
        if piece and piece.color == self.board.current_turn:
            self.dragging = True
            self.drag_piece = piece
            self.drag_start = (row, col)
            self.drag_pos = pos
            self.selected_square = (row, col)
            self.valid_moves = self.board.get_valid_moves(row, col)
        elif self.selected_square:
            # Try to make a move (click-to-move fallback)
            self._try_make_move(row, col)

    def _handle_drag_end(self, pos):
        """
        Handle end of drag (drop piece)

        Args:
            pos: mouse position
        """
        if not self.dragging:
            return

        square = self._get_square_from_mouse(pos)

        if square and square != self.drag_start:
            to_row, to_col = square
            # Try to make the move
            if square in self.valid_moves:
                from_row, from_col = self.drag_start
                # Check if this is a promotion move
                if self.board.is_promotion_move(from_row, from_col, to_row, to_col):
                    self.pending_promotion = (from_row, from_col, to_row, to_col)
                else:
                    self._complete_move(from_row, from_col, to_row, to_col)
                # Clear drag state but keep selection cleared
                self.dragging = False
                self.drag_piece = None
                self.drag_start = None
                self.drag_pos = None
                return

        # Invalid drop or same square - cancel drag but keep piece selected
        self.dragging = False
        self.drag_piece = None
        self.drag_pos = None
        # Keep selected_square and valid_moves for click-to-move

    def _try_make_move(self, to_row, to_col):
        """
        Try to make a move from the selected square

        Args:
            to_row: row to move to
            to_col: col to move to
        """

        from_row, from_col = self.selected_square

        # Check if this is a valid move
        if (to_row, to_col) not in self.valid_moves:
            # Invalid move, try selecting new piece
            piece = self.board.get_piece(to_row, to_col)
            if piece and piece.color == self.board.current_turn:
                self._select_piece(to_row, to_col)
            else:
                self.selected_square = None
                self.valid_moves = []
            return

        # Check if this is a promotion move
        if self.board.is_promotion_move(from_row, from_col, to_row, to_col):
            # Store pending promotion and show dialog
            self.pending_promotion = (from_row, from_col, to_row, to_col)
            return

        # Make the move
        self._complete_move(from_row, from_col, to_row, to_col)

    def _complete_move(self, from_row, from_col, to_row, to_col, promotion_piece=None):
        """
        Complete a move (called after promotion selection if needed)

        Args:
            from_row: starting row
            from_col: starting column
            to_row: ending row
            to_col: ending column
            promotion_piece: PieceType for promotion (optional)
        """
        if self.board.make_move(from_row, from_col, to_row, to_col, promotion_piece):
            # Move successful
            self.last_move = ((from_row, from_col), (to_row, to_col))
            self.selected_square = None
            self.valid_moves = []
            self.pending_promotion = None
            self._check_game_over()

            # AI move (if playing against bot and it's AI's turn)
            if self.game_mode == 'pvb' and self.board.current_turn != self.player_color and not self.game_over:
                # Render the player's move before AI thinks
                self._render()
                pygame.display.flip()
                self._make_ai_move()

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

    def _handle_promotion_click(self, pos):
        """
        Handle click during promotion dialog

        Args:
            pos: mouse position
        """
        from constants import PieceType

        from_row, from_col, to_row, to_col = self.pending_promotion

        # Get promotion dialog rectangles from renderer
        piece_rects = self.renderer.get_promotion_rects(to_row, to_col, self.board.current_turn)

        promotion_pieces = [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]

        for i, rect in enumerate(piece_rects):
            if rect.collidepoint(pos):
                # Complete the move with selected piece
                self._complete_move(from_row, from_col, to_row, to_col, promotion_pieces[i])
                return

        # Click outside dialog - cancel promotion
        self.pending_promotion = None
        self.selected_square = None
        self.valid_moves = []

    def _make_ai_move(self):
        """
        Make the AI's move
        """

        pygame.time.wait(300)  # Small delay for better UX
        ai_move = self.ai.get_best_move(self.board)

        if ai_move:
            from_pos, to_pos = ai_move
            self.board.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
            self.last_move = (from_pos, to_pos)
            self._check_game_over()

    def _handle_keypress(self, key):
        """
        Handle keyboard events

        Args:
            key: pygame key constant

        Returns:
            True to continue running, else false
        """

        # Handle backspace for time input
        if self.game_mode == 'pvp_time_select':
            if key == pygame.K_BACKSPACE:
                active = self.time_input['active_field']
                if active and self.time_input[active]:
                    self.time_input[active] = self.time_input[active][:-1]
            elif key == pygame.K_TAB:
                # Cycle through input fields
                fields = ['white_minutes', 'white_seconds', 'black_minutes', 'black_seconds']
                active = self.time_input['active_field']
                if active in fields:
                    idx = (fields.index(active) + 1) % len(fields)
                    self.time_input['active_field'] = fields[idx]
            elif key == pygame.K_ESCAPE:
                # Go back to main menu
                self.game_mode = None
                self._reset_time_input()
            return True

        if key == pygame.K_r:
            # Restart game
            self.reset_game()
            # Reset timer
            if self.use_timer:
                self._reset_timer_for_game()
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
            self.use_timer = False
            self.reset_game()

        return True

    def _reset_time_input(self):
        """Reset time input fields"""
        self.time_input = {
            'white_minutes': '',
            'black_minutes': '',
            'white_seconds': '',
            'black_seconds': '',
            'active_field': None
        }

    def _reset_timer_for_game(self):
        """Reset timers to initial values for a new game"""
        # Parse time input and convert to milliseconds
        white_min = int(self.time_input['white_minutes'] or '0')
        white_sec = int(self.time_input['white_seconds'] or '0')
        black_min = int(self.time_input['black_minutes'] or '0')
        black_sec = int(self.time_input['black_seconds'] or '0')

        self.white_time = (white_min * 60 + white_sec) * 1000
        self.black_time = (black_min * 60 + black_sec) * 1000
        self.last_tick = None
    
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
        self.last_move = None
        self.pending_promotion = None
        self.game_over = False
        self.winner = None

        # Reset drag state
        self.dragging = False
        self.drag_piece = None
        self.drag_start = None
        self.drag_pos = None
        
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

        menu_modes = [None, 'pvb_difficulty_select', 'pvb_color_select', 'pvp_time_select']
        if self.game_mode in menu_modes:
            # Draw menu (main menu, difficulty selection, color selection, or time selection)
            self.renderer.draw_menu(self.game_mode, self.time_input)

        else:
            # Draw game
            self.screen.fill((49, 46, 43))  # BG_COLOR
            self.renderer.draw_board(self.board, self.selected_square, self.valid_moves, self.last_move)
            self.renderer.draw_pieces(self.board, self.drag_start if self.dragging else None)
            self.renderer.draw_coordinates()

            # Prepare timer info
            timer_info = None
            if self.use_timer and self.game_mode == 'pvp':
                timer_info = {
                    'white_time': self.white_time,
                    'black_time': self.black_time
                }

            self.renderer.draw_game_ui(self.board, self.game_mode, self.game_over, self.winner, timer_info)

            # Draw dragged piece at cursor
            if self.dragging and self.drag_piece and self.drag_pos:
                self.renderer.draw_dragged_piece(self.drag_piece, self.drag_pos)

            # Draw promotion dialog if active
            if self.pending_promotion:
                _, _, to_row, to_col = self.pending_promotion
                self.renderer.draw_promotion_dialog(to_row, to_col, self.board.current_turn)

