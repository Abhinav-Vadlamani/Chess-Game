import pygame
import copy
import threading
from board import ChessBoard
from ai import ChessAI
from renderer import Renderer
from constants import (Color, PieceType, WINDOW_SIZE, BOARD_OFFSET, BOARD_SIZE,
                       SQUARE_SIZE, FPS, BG_COLOR)

class ChessGame:
    # Game modes in which the menu (rather than the board) is shown.
    MENU_MODES = [None, 'pvb_difficulty_select', 'pvb_color_select', 'pvp_time_select']

    def __init__(self):
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
        # Move coordinates plus the optional drag-drop pixel position for a smooth handoff.
        self.pending_promotion = None
        self.game_mode = None  # 'pvp' or 'pvb'
        self.player_color = None  # Color.WHITE or Color.BLACK (for PvBot mode)
        self.ai_difficulty = None  # 'easy', 'medium', 'hard', or 'impossible'
        self.stockfish_available = ChessAI.stockfish_available()
        self.ai = None
        self.ai_thinking = False
        self.ai_result = None
        self.ai_result_ready = False
        self.ai_request_id = 0
        self.analysis_active = False
        self.analysis_positions = []
        self.analysis_index = 0
        self.analysis_lines = []
        self.analysis_thinking = False
        self.analysis_result_ready = False
        self.analysis_request_id = 0
        self.game_over = False
        self.winner = None
        self.draw_reason = None
        self.resigned_by = None
        self.move_animation = None
        self.game_end_started_at = None
        self.ai_move_pending = False

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

        # Time input state for the time-control menu.
        self._reset_time_input()

        # Move history panel state
        self.show_move_history = False

    def run(self):
        """Run the main loop: process input, update the timer, and redraw each frame."""
        running = True

        while running:
            self.clock.tick(FPS)
            self._advance_animations()
            self._update_timer()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    running = self._handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self._handle_mouse_up(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self._handle_mouse_motion(event.pos)
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_keypress(event.key)
                elif event.type == pygame.TEXTINPUT:
                    self._handle_text_input(event.text)

            self._render()
            pygame.display.flip()

        pygame.quit()

    def _update_timer(self):
        """Deduct elapsed time from the active player's clock; flag a loss on timeout."""
        if (not self.use_timer or self.game_over or self.game_mode != 'pvp'
                or self.move_animation):
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
                self._set_game_over("Black")  # White ran out of time
        else:
            self.black_time -= elapsed
            if self.black_time <= 0:
                self.black_time = 0
                self._set_game_over("White")  # Black ran out of time

    def _handle_text_input(self, text):
        """Append a typed digit to the active time field (max 2 for seconds, 3 for minutes)."""
        if self.game_mode != 'pvp_time_select':
            return

        active = self.time_input['active_field']
        if active is None or not text.isdigit():
            return

        current = self.time_input[active]
        max_len = 2 if 'seconds' in active else 3
        if len(current) < max_len:
            self.time_input[active] = current + text
    
    def _handle_mouse_down(self, pos):
        """
        Handle a mouse press on the menu or the board.

        Returns:
            True to keep the game running.
        """
        if self.game_mode in self.MENU_MODES:
            return self._handle_menu_click(pos)
        self._handle_board_mouse_down(pos)
        return True

    def _handle_mouse_up(self, pos):
        """Finish a drag when the mouse button is released."""
        if self.dragging:
            self._handle_drag_end(pos)

    def _handle_mouse_motion(self, pos):
        """Track the cursor while a piece is being dragged."""
        if self.dragging:
            self.drag_pos = pos

    def _handle_menu_click(self, pos):
        """Route a menu click to the button it hit; return True to keep running."""
        buttons = self.renderer.draw_menu(self.game_mode, self.time_input, self.stockfish_available)

        if self.game_mode is None:
            # Main menu: choose the game mode.
            pvp_button, pvb_button = buttons
            if pvp_button.collidepoint(pos):
                self.game_mode = 'pvp_time_select'
                self._reset_time_input()
            elif pvb_button.collidepoint(pos):
                self.game_mode = 'pvb_difficulty_select'

        elif self.game_mode == 'pvp_time_select':
            input_rects = buttons['input_rects']
            start_button = buttons['start_button']
            no_time_button = buttons['no_time_button']
            back_button = buttons['back_button']

            # Clicking a field selects it for typing.
            for field_name, rect in input_rects.items():
                if rect.collidepoint(pos):
                    self.time_input['active_field'] = field_name
                    return True

            if start_button.collidepoint(pos):
                # Only start with a clock if both players have time > 0.
                if self._time_input_seconds('white') > 0 and self._time_input_seconds('black') > 0:
                    self.game_mode = 'pvp'
                    self.player_color = None
                    self.use_timer = True
                    self._reset_timer_for_game()
                    self.reset_game()
            elif no_time_button.collidepoint(pos):
                self.game_mode = 'pvp'
                self.player_color = None
                self.use_timer = False
                self.reset_game()
            elif back_button.collidepoint(pos):
                self.game_mode = None
                self._reset_time_input()

        elif self.game_mode == 'pvb_difficulty_select':
            # Difficulty selection menu for PvBot
            easy_button, medium_button, hard_button, impossible_button, back_button = buttons
            
            if easy_button.collidepoint(pos):
                self.ai_difficulty = 'easy'
                self.game_mode = 'pvb_color_select'
            elif medium_button.collidepoint(pos):
                self.ai_difficulty = 'medium'
                self.game_mode = 'pvb_color_select'
            elif hard_button.collidepoint(pos):
                self.ai_difficulty = 'hard'
                self.game_mode = 'pvb_color_select'
            elif impossible_button.collidepoint(pos) and self.stockfish_available:
                self.ai_difficulty = 'impossible'
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
        if self.analysis_active:
            self._handle_analysis_click(pos)
            return

        if self.game_over and self.renderer.get_analysis_button_rect().collidepoint(pos):
            self._open_analysis()
            return

        if not self.game_over and self.renderer.get_resign_button_rect().collidepoint(pos):
            self._resign_current_player()
            return

        # Check for history button click
        history_button = self.renderer.get_history_button_rect()
        if history_button.collidepoint(pos):
            self.show_move_history = not self.show_move_history
            return

        if self.game_over or self.move_animation or self.ai_thinking:
            return

        # If move history panel is open, close it on any click outside
        if self.show_move_history:
            self.show_move_history = False
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

    def _clear_drag(self):
        """Reset all drag-and-drop state."""
        self.dragging = False
        self.drag_piece = None
        self.drag_start = None
        self.drag_pos = None

    def _handle_drag_end(self, pos):
        """Drop a dragged piece: play the move if the target square is legal."""
        if not self.dragging:
            return

        square = self._get_square_from_mouse(pos)
        if square and square != self.drag_start and square in self.valid_moves:
            from_row, from_col = self.drag_start
            to_row, to_col = square
            if self.board.is_promotion_move(from_row, from_col, to_row, to_col):
                self.pending_promotion = (from_row, from_col, to_row, to_col, pos)
            else:
                self._complete_move(from_row, from_col, to_row, to_col, animation_start_pos=pos)

        # Either way the drag is over; the selection stays for click-to-move.
        self._clear_drag()

    def _try_make_move(self, to_row, to_col):
        """Handle a click on (to_row, to_col) after a piece was already selected."""
        from_row, from_col = self.selected_square

        # Clicking a non-target square reselects (own piece) or clears the selection.
        if (to_row, to_col) not in self.valid_moves:
            piece = self.board.get_piece(to_row, to_col)
            if piece and piece.color == self.board.current_turn:
                self._select_piece(to_row, to_col)
            else:
                self.selected_square = None
                self.valid_moves = []
            return

        if self.board.is_promotion_move(from_row, from_col, to_row, to_col):
            self.pending_promotion = (from_row, from_col, to_row, to_col, None)
            return

        self._complete_move(from_row, from_col, to_row, to_col)

    def _complete_move(self, from_row, from_col, to_row, to_col, promotion_piece=None,
                       animation_start_pos=None):
        """Play a (possibly promoting) move, update state, and let the AI reply if needed."""
        moving_piece = self.board.get_piece(from_row, from_col)
        moving_piece_type = moving_piece.piece_type if moving_piece else None
        if self.board.make_move(from_row, from_col, to_row, to_col, promotion_piece):
            self.last_move = ((from_row, from_col), (to_row, to_col))
            self.selected_square = None
            self.valid_moves = []
            self.pending_promotion = None
            self._start_move_animation(self.board.move_history[-1], moving_piece, moving_piece_type,
                                       animation_start_pos)
            self._check_game_over()

            if self.game_mode == 'pvb' and self.board.current_turn != self.player_color and not self.game_over:
                self.ai_move_pending = True

    def _select_piece(self, row, col):
        """Select the current player's piece at (row, col) and cache its legal moves."""
        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.board.current_turn:
            self.selected_square = (row, col)
            self.valid_moves = self.board.get_valid_moves(row, col)

    def _handle_promotion_click(self, pos):
        """Apply the promotion piece the player clicked, or cancel if they clicked away."""
        from_row, from_col, to_row, to_col, animation_start_pos = self.pending_promotion

        piece_rects = self.renderer.get_promotion_rects(to_row, to_col, self.board.current_turn)
        promotion_pieces = [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]

        for rect, promotion_piece in zip(piece_rects, promotion_pieces):
            if rect.collidepoint(pos):
                self._complete_move(from_row, from_col, to_row, to_col, promotion_piece,
                                    animation_start_pos)
                return

        # Clicked outside the dialog: cancel the promotion.
        self.pending_promotion = None
        self.selected_square = None
        self.valid_moves = []

    def _make_ai_move(self):
        """Start calculating an AI reply without blocking Pygame's event loop."""
        if self.ai_thinking or not self.ai:
            return
        self.ai_thinking = True
        self.ai_result = None
        self.ai_result_ready = False
        self.ai_request_id += 1
        request_id = self.ai_request_id
        board_snapshot = copy.deepcopy(self.board)

        def calculate_move():
            try:
                result = self.ai.get_best_move(board_snapshot)
            except Exception:
                result = None
            if request_id == self.ai_request_id:
                self.ai_result = result
                self.ai_result_ready = True

        threading.Thread(target=calculate_move, daemon=True).start()

    def _play_ai_move(self, ai_move):
        """Apply a completed background AI result on the main game thread."""
        if ai_move:
            from_pos, to_pos, *promotion = ai_move
            self._complete_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1],
                                promotion[0] if promotion else None)

    def _open_analysis(self):
        """Build replay positions for the finished game and open the analysis workspace."""
        replay = ChessBoard()
        self.analysis_positions = [copy.deepcopy(replay)]
        for move in self.board.move_history:
            promotion = move.promotion_piece.piece_type if move.promotion_piece else None
            replay.make_move(*move.from_position, *move.to_position, promotion)
            self.analysis_positions.append(copy.deepcopy(replay))
        self.analysis_active = True
        self._set_analysis_index(len(self.analysis_positions) - 1)

    def _set_analysis_index(self, index):
        """Select a replay position and ask Stockfish for fresh principal variations."""
        if not self.analysis_positions:
            return
        index = max(0, min(index, len(self.analysis_positions) - 1))
        if index == self.analysis_index and self.analysis_thinking:
            return
        self.analysis_index = index
        self.analysis_lines = []
        self.analysis_result_ready = False
        self.analysis_request_id += 1
        request_id = self.analysis_request_id
        if not self.stockfish_available:
            self.analysis_thinking = False
            return
        self.analysis_thinking = True
        board_snapshot = copy.deepcopy(self.analysis_positions[index])

        def calculate_lines():
            lines = ChessAI(difficulty='impossible').get_stockfish_lines(board_snapshot)
            if request_id == self.analysis_request_id and self.analysis_active:
                self.analysis_lines = lines
                self.analysis_result_ready = True

        threading.Thread(target=calculate_lines, daemon=True).start()

    def _handle_analysis_click(self, pos):
        """Navigate or close the post-game replay workspace."""
        if self.renderer.get_analysis_close_rect().collidepoint(pos):
            self.analysis_active = False
            self.analysis_request_id += 1
        elif self.renderer.get_analysis_previous_rect().collidepoint(pos):
            self._set_analysis_index(self.analysis_index - 1)
        elif self.renderer.get_analysis_next_rect().collidepoint(pos):
            self._set_analysis_index(self.analysis_index + 1)

    def _start_move_animation(self, move, moving_piece, moving_piece_type, animation_start_pos=None):
        """Build a visual-only move record after the board has accepted a move."""
        rook_animation = None
        if move.is_castling:
            row, from_col = move.from_position
            rook_from_col, rook_to_col = (7, 5) if move.to_position[1] > from_col else (0, 3)
            rook_animation = {
                'piece': self.board.get_piece(row, rook_to_col),
                'from': (row, rook_from_col),
                'to': (row, rook_to_col),
            }
        self.move_animation = {
            'started_at': pygame.time.get_ticks(),
            'duration': 440 if move.is_castling else (500 if move.promotion_piece else
                        (180 if animation_start_pos else 280)),
            'piece': moving_piece,
            'moving_piece_type': moving_piece_type,
            'from': move.from_position,
            'to': move.to_position,
            'from_pixel': animation_start_pos,
            'is_capture': bool(move.captured_piece),
            'rook': rook_animation,
            'promotion_piece': move.promotion_piece.piece_type if move.promotion_piece else None,
        }

    def _advance_animations(self):
        """Retire completed animation records and let a queued AI turn begin."""
        if self.move_animation:
            elapsed = pygame.time.get_ticks() - self.move_animation['started_at']
            if elapsed >= self.move_animation['duration']:
                self.move_animation = None
        if self.ai_move_pending and not self.move_animation and not self.game_over:
            self.ai_move_pending = False
            self._make_ai_move()
        if self.ai_thinking and self.ai_result_ready:
            self.ai_thinking = False
            self.ai_result_ready = False
            self._play_ai_move(self.ai_result)
        if self.analysis_thinking and self.analysis_result_ready:
            self.analysis_thinking = False
            self.analysis_result_ready = False

    def _handle_keypress(self, key):
        """Handle a key press; return False only when the player asks to quit."""
        if self.analysis_active:
            if key == pygame.K_ESCAPE:
                self.analysis_active = False
            elif key in (pygame.K_LEFT, pygame.K_a):
                self._set_analysis_index(self.analysis_index - 1)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self._set_analysis_index(self.analysis_index + 1)
            return True

        # In the time-control menu, keys edit the input fields.
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
        """Clear the time-control input fields."""
        self.time_input = {
            'white_minutes': '',
            'black_minutes': '',
            'white_seconds': '',
            'black_seconds': '',
            'active_field': None
        }

    def _time_input_seconds(self, player):
        """Return the entered starting time for 'white' or 'black', in seconds."""
        minutes = int(self.time_input[f'{player}_minutes'] or '0')
        seconds = int(self.time_input[f'{player}_seconds'] or '0')
        return minutes * 60 + seconds

    def _reset_timer_for_game(self):
        """Load each player's clock from the entered time (stored in milliseconds)."""
        self.white_time = self._time_input_seconds('white') * 1000
        self.black_time = self._time_input_seconds('black') * 1000
        self.last_tick = None

    def _get_square_from_mouse(self, pos):
        """Return the (row, col) under the mouse, or None if it's off the board."""
        x, y = pos
        if BOARD_OFFSET <= x < BOARD_OFFSET + BOARD_SIZE and BOARD_OFFSET <= y < BOARD_OFFSET + BOARD_SIZE:
            col = (x - BOARD_OFFSET) // SQUARE_SIZE
            row = (y - BOARD_OFFSET) // SQUARE_SIZE
            return (row, col)
        return None
    
    def _check_game_over(self):
        """Detect checkmate or any draw condition and record the result."""
        if self.board.is_checkmate():
            self._set_game_over("Black" if self.board.current_turn == Color.WHITE else "White")
            return

        draw_conditions = [
            (self.board.is_stalemate, "Stalemate"),
            (self.board.is_insufficient_material, "Insufficient material"),
            (self.board.is_threefold_repetition, "Threefold repetition"),
            (self.board.is_fifty_move_rule, "Fifty-move rule"),
        ]
        for is_draw, reason in draw_conditions:
            if is_draw():
                self._set_game_over("Draw")
                self.draw_reason = reason
                return

    def _set_game_over(self, winner):
        """Record the result and start the one-time end-of-game presentation."""
        self.game_over = True
        self.winner = winner
        self.game_end_started_at = pygame.time.get_ticks()

    def _resign_current_player(self):
        """End the game with the side to move resigning."""
        self.resigned_by = "White" if self.board.current_turn == Color.WHITE else "Black"
        self._set_game_over("Black" if self.resigned_by == "White" else "White")

    def reset_game(self):
        """Start a new game, keeping the AI and player color for PvBot mode."""
        self.board = ChessBoard()
        self.selected_square = None
        self.valid_moves = []
        self.last_move = None
        self.pending_promotion = None
        self.game_over = False
        self.winner = None
        self.draw_reason = None
        self.resigned_by = None
        self.move_animation = None
        self.game_end_started_at = None
        self.ai_move_pending = False
        self.ai_request_id += 1  # Ignore any result from a previous board state.
        self.ai_thinking = False
        self.ai_result = None
        self.ai_result_ready = False
        self.analysis_active = False
        self.analysis_positions = []
        self.analysis_lines = []
        self.analysis_thinking = False
        self.analysis_result_ready = False
        self.analysis_request_id += 1
        self.show_move_history = False
        self._clear_drag()

        # In PvBot mode there should already be an AI; recreate one if it's missing.
        if self.game_mode == 'pvb' and not self.ai:
            self.ai = ChessAI(difficulty="medium", ai_color=Color.BLACK)
            self.player_color = Color.WHITE

    def _render(self):
        """Draw the current frame: either a menu or the board and its UI."""
        if self.game_mode in self.MENU_MODES:
            self.renderer.draw_menu(self.game_mode, self.time_input, self.stockfish_available)
            return

        if self.analysis_active:
            board = self.analysis_positions[self.analysis_index]
            notation = None if self.analysis_index == 0 else self.board.get_move_history_notation()[self.analysis_index - 1]
            last_move = None if self.analysis_index == 0 else self.board.move_history[self.analysis_index - 1]
            self.renderer.draw_analysis_workspace(
                board, self.analysis_index, len(self.analysis_positions) - 1, notation, last_move,
                self.analysis_lines, self.analysis_thinking, self.stockfish_available,
            )
            return

        self.screen.fill(BG_COLOR)
        self.renderer.draw_board(self.board, self.selected_square, self.valid_moves, self.last_move)
        animation_squares = []
        if self.move_animation:
            animation_squares.append(self.move_animation['to'])
            if self.move_animation.get('rook'):
                animation_squares.append(self.move_animation['rook']['to'])
        self.renderer.draw_pieces(self.board, self.drag_start if self.dragging else None, animation_squares)
        if self.move_animation:
            self.renderer.draw_move_animation(self.move_animation)
        self.renderer.draw_coordinates()

        timer_info = None
        if self.use_timer and self.game_mode == 'pvp':
            timer_info = {'white_time': self.white_time, 'black_time': self.black_time}

        self.renderer.draw_game_ui(self.board, self.game_mode, self.game_over, self.winner,
                                   timer_info, self.draw_reason, self.show_move_history,
                                   self.game_end_started_at, self.resigned_by)
        self.renderer.draw_history_button(self.show_move_history)
        if not self.game_over:
            self.renderer.draw_resign_button()

        if self.dragging and self.drag_piece and self.drag_pos:
            self.renderer.draw_dragged_piece(self.drag_piece, self.drag_pos)

        if self.pending_promotion:
            _, _, to_row, to_col, _ = self.pending_promotion
            self.renderer.draw_promotion_dialog(to_row, to_col, self.board.current_turn)
