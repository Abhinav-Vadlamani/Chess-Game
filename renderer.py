import pygame
from constants import *

class Renderer:
    PIECE_SYMBOLS = {
        (Color.WHITE, PieceType.KING): '♚',
        (Color.WHITE, PieceType.QUEEN): '♛',
        (Color.WHITE, PieceType.ROOK): '♜',
        (Color.WHITE, PieceType.BISHOP): '♝',
        (Color.WHITE, PieceType.KNIGHT): '♞',
        (Color.WHITE, PieceType.PAWN): '♟',
        (Color.BLACK, PieceType.KING): '♚',
        (Color.BLACK, PieceType.QUEEN): '♛',
        (Color.BLACK, PieceType.ROOK): '♜',
        (Color.BLACK, PieceType.BISHOP): '♝',
        (Color.BLACK, PieceType.KNIGHT): '♞',
        (Color.BLACK, PieceType.PAWN): '♟',
    }

    def __init__(self, screen):
        """
        Initialize the renderer

        Args:
            screen: Pygame screen surface
        """
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.piece_font = pygame.font.SysFont('Apple Symbols', 60)
        self.small_piece_font = pygame.font.SysFont('Apple Symbols', 24)
    
    def draw_board(self, board, selected_square = None, valid_moves = None, last_move = None):
        """
        Draw the chess board

        Args:
            board: ChessBoard instance
            selected_square: Currently selected square or None
            valid_moves: List of valid moves
            last_move: Tuple of (from_square, to_square) for last move highlighting
        """

        valid_moves = valid_moves or []

        # Draw squares
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE

                # Highlight last move squares
                if last_move:
                    from_sq, to_sq = last_move
                    if (row, col) == from_sq or (row, col) == to_sq:
                        color = HIGHLIGHT_LAST_MOVE

                # Highlight selected square
                if selected_square == (row, col):
                    color = HIGHLIGHT_SELECTED

                # Highlight king in check
                piece = board.get_piece(row, col)
                if piece and piece.piece_type == PieceType.KING and board.is_in_check(piece.color):
                    color = HIGHLIGHT_CHECK

                x = BOARD_OFFSET + col * SQUARE_SIZE
                y = BOARD_OFFSET + row * SQUARE_SIZE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # Draw grey circles on valid move squares
        for row, col in valid_moves:
            center_x = BOARD_OFFSET + col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = BOARD_OFFSET + row * SQUARE_SIZE + SQUARE_SIZE // 2

            # Check if there's an enemy piece (capture move)
            piece = board.get_piece(row, col)
            if piece:
                # Draw ring for capture moves
                radius = SQUARE_SIZE // 2 - 4
                pygame.draw.circle(self.screen, (100, 100, 100), (center_x, center_y), radius, 4)
            else:
                # Draw filled circle for empty squares
                radius = SQUARE_SIZE // 6
                pygame.draw.circle(self.screen, (100, 100, 100), (center_x, center_y), radius)

    def draw_pieces(self, board, skip_square=None):
        """
        Draw chess pieces on the board

        Args:
            board: ChessBoard instance
            skip_square: (row, col) to skip drawing (for drag and drop)
        """

        for row in range(8):
            for col in range(8):
                # Skip the square being dragged
                if skip_square and skip_square == (row, col):
                    continue

                piece = board.get_piece(row, col)
                if piece:
                    symbol = self.PIECE_SYMBOLS[(piece.color, piece.piece_type)]
                    text = self.piece_font.render(symbol, True,
                                            (255, 255, 255) if piece.color == Color.WHITE else (0, 0, 0))
                    x = BOARD_OFFSET + col * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2
                    y = BOARD_OFFSET + row * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_height() // 2
                    self.screen.blit(text, (x, y))

    def draw_dragged_piece(self, piece, pos):
        """
        Draw a piece being dragged at the cursor position

        Args:
            piece: The piece being dragged
            pos: Current mouse position (x, y)
        """
        symbol = self.PIECE_SYMBOLS[(piece.color, piece.piece_type)]
        text = self.piece_font.render(symbol, True,
                                     (255, 255, 255) if piece.color == Color.WHITE else (0, 0, 0))
        # Center the piece on the cursor
        x = pos[0] - text.get_width() // 2
        y = pos[1] - text.get_height() // 2
        self.screen.blit(text, (x, y))

    def draw_coordinates(self):
        """
        Draw file and rank labels around board
        """

        for i, file in enumerate(FILES):
            text = self.small_font.render(file, True, TEXT_COLOR)
            x = BOARD_OFFSET + i * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2
            self.screen.blit(text, (x, BOARD_OFFSET + BOARD_SIZE + 10))
        
        for i, rank in enumerate(RANKS):
            text = self.small_font.render(rank, True, TEXT_COLOR)
            y = BOARD_OFFSET + i * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_height() // 2
            self.screen.blit(text, (20, y))

    def draw_game_ui(self, board, game_mode, game_over=False, winner=None, timer_info=None):
        """
        Draw game UI elements

        Args:
            board: ChessBoard instance
            game_mode: Current game mode (pvp or pvb)
            game_over: Whether or not the game is over
            winner: Winner of the game
            timer_info: Dict with 'white_time' and 'black_time' in milliseconds
        """

        # turn indicator
        turn_text = "White's turn" if board.current_turn == Color.WHITE else "Black's Turn"
        text = self.small_font.render(turn_text, True, TEXT_COLOR)
        self.screen.blit(text, (WINDOW_SIZE - 200, 20))

        # Check indicator
        if board.is_in_check(board.current_turn):
            check_text = self.small_font.render("CHECK!", True, (255, 100, 100))
            self.screen.blit(check_text, (WINDOW_SIZE - 200, 50))

        # Game mode indicator
        mode_text = "PvP" if game_mode == 'pvp' else "PvBot"
        text = self.small_font.render(mode_text, True, TEXT_COLOR)
        self.screen.blit(text, (20, 20))

        # Draw timers if active
        if timer_info:
            self._draw_timers(timer_info, board.current_turn)

        # Controls
        controls_text = "ESC: Menu  |  R: Restart  |  Q: Quit"
        text = self.small_font.render(controls_text, True, TEXT_COLOR)

        x_pos = WINDOW_SIZE // 2 - text.get_width() // 2
        y_pos = BOARD_OFFSET + BOARD_SIZE + 35
        self.screen.blit(text, (x_pos, y_pos))

        # Game over message
        if game_over:
            self._draw_game_over_overlay(winner, timer_info)

    def _draw_timers(self, timer_info, current_turn):
        """
        Draw chess clocks for both players

        Args:
            timer_info: Dict with 'white_time' and 'black_time' in milliseconds
            current_turn: Current player's turn
        """
        white_time = timer_info['white_time']
        black_time = timer_info['black_time']

        # Format time as MM:SS
        def format_time(ms):
            if ms < 0:
                ms = 0
            total_seconds = ms // 1000
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"

        # Timer box dimensions
        box_width = 100
        box_height = 40

        # Black timer (top right of board)
        black_box = pygame.Rect(BOARD_OFFSET + BOARD_SIZE + 10, BOARD_OFFSET, box_width, box_height)
        black_color = (60, 60, 60) if current_turn == Color.BLACK else (40, 40, 40)
        pygame.draw.rect(self.screen, black_color, black_box, border_radius=5)
        pygame.draw.rect(self.screen, (100, 100, 100), black_box, 2, border_radius=5)

        black_time_text = self.font.render(format_time(black_time), True, TEXT_COLOR)
        self.screen.blit(black_time_text, (black_box.centerx - black_time_text.get_width() // 2,
                                           black_box.centery - black_time_text.get_height() // 2))

        # White timer (bottom right of board)
        white_box = pygame.Rect(BOARD_OFFSET + BOARD_SIZE + 10, BOARD_OFFSET + BOARD_SIZE - box_height,
                                box_width, box_height)
        white_color = (80, 80, 80) if current_turn == Color.WHITE else (50, 50, 50)
        pygame.draw.rect(self.screen, white_color, white_box, border_radius=5)
        pygame.draw.rect(self.screen, (100, 100, 100), white_box, 2, border_radius=5)

        white_time_text = self.font.render(format_time(white_time), True, TEXT_COLOR)
        self.screen.blit(white_time_text, (white_box.centerx - white_time_text.get_width() // 2,
                                           white_box.centery - white_time_text.get_height() // 2))

    def _draw_game_over_overlay(self, winner, timer_info=None):
        """
        Draw game over overlay

        Args:
            winner: player that won
            timer_info: Timer info to detect timeout
        """

        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        if winner:
            # Check if it was a timeout
            if timer_info:
                if timer_info['white_time'] <= 0 or timer_info['black_time'] <= 0:
                    message = f"{winner} wins on time!"
                else:
                    message = f"{winner} wins by checkmate!"
            else:
                message = f"{winner} wins by checkmate!"
        else:
            message = "Stalemate - Draw!"

        text = self.font.render(message, True, TEXT_COLOR)
        self.screen.blit(text, (WINDOW_SIZE // 2 - text.get_width() // 2, WINDOW_SIZE // 2 - 50))

        restart_text = self.small_font.render("Press R to restart or Q to quit", True, TEXT_COLOR)
        self.screen.blit(restart_text, (WINDOW_SIZE // 2 - restart_text.get_width() // 2,
                                       WINDOW_SIZE // 2 + 20))
        
    
    def draw_menu(self, game_mode=None, time_input=None):
        """
        Draw main menu or selection menus

        Args:
            game_mode: Current game mode
            time_input: Time input state dict (for pvp_time_select)

        Returns:
            Tuple of buttons or dict with input rects
        """

        self.screen.fill(BG_COLOR)

        if game_mode == 'pvb_color_select':
            return self._draw_color_selection_menu()
        elif game_mode == 'pvb_difficulty_select':
            return self._draw_difficulty_selection_menu()
        elif game_mode == 'pvp_time_select':
            return self._draw_time_selection_menu(time_input)
        else:
            return self._draw_main_menu()
        
    def _draw_main_menu(self):
        """
        Draw main menu

        Returns:
            Tuple of buttons
        """

        # Title
        title = self.font.render("Chess Game", True, TEXT_COLOR)
        self.screen.blit(title, (WINDOW_SIZE // 2 - title.get_width() // 2, 100))
        
        # Buttons
        button_width = 300
        button_height = 60
        button_x = WINDOW_SIZE // 2 - button_width // 2
        
        pvp_button = pygame.Rect(button_x, 250, button_width, button_height)
        pvb_button = pygame.Rect(button_x, 350, button_width, button_height)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # PvP Button
        self._draw_button(pvp_button, "Player vs Player", mouse_pos)
        
        # PvB Button
        self._draw_button(pvb_button, "Player vs Bot", mouse_pos)
        
        # Instructions
        instructions = [
            "How to play:",
            "• Click a piece to select it",
            "• Click a highlighted square to move",
            "• Press ESC to return to menu",
            "• Press R to restart game",
            "• Press Q to quit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, TEXT_COLOR)
            self.screen.blit(text, (WINDOW_SIZE // 2 - text.get_width() // 2, 500 + i * 30))
        
        return pvp_button, pvb_button
    
    def _draw_color_selection_menu(self):
        """
        Draw the color selection menu

        Returns:
            Tuple of buttons
        """

        # Title
        title = self.font.render("Choose Your Color", True, TEXT_COLOR)
        self.screen.blit(title, (WINDOW_SIZE // 2 - title.get_width() // 2, 100))

        # Buttons
        button_width = 300
        button_height = 60
        button_x = WINDOW_SIZE // 2 - button_width // 2
        
        white_button = pygame.Rect(button_x, 250, button_width, button_height)
        black_button = pygame.Rect(button_x, 350, button_width, button_height)
        back_button = pygame.Rect(button_x, 470, button_width, button_height)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # White Button
        self._draw_button(white_button, "Play as White ♔", mouse_pos)
        
        # Black Button
        self._draw_button(black_button, "Play as Black ♚", mouse_pos)

        # Back Button (smaller, different color)
        back_color = (100, 100, 100) if back_button.collidepoint(mouse_pos) else (70, 70, 70)
        pygame.draw.rect(self.screen, back_color, back_button, border_radius=10)
        back_text = self.small_piece_font.render("← Back to Menu", True, TEXT_COLOR)
        self.screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2, 
                                     back_button.centery - back_text.get_height() // 2))
        
        return white_button, black_button, back_button
    
    def _draw_difficulty_selection_menu(self):
        # Title
        title = self.font.render("Choose Difficulty", True, TEXT_COLOR)
        self.screen.blit(title, (WINDOW_SIZE // 2 - title.get_width() // 2, 100))
        
        subtitle = self.small_font.render("Select AI difficulty level", True, TEXT_COLOR)
        self.screen.blit(subtitle, (WINDOW_SIZE // 2 - subtitle.get_width() // 2, 150))

        # Buttons
        button_width = 300
        button_height = 60
        button_x = WINDOW_SIZE // 2 - button_width // 2
        
        easy_button = pygame.Rect(button_x, 230, button_width, button_height)
        medium_button = pygame.Rect(button_x, 320, button_width, button_height)
        hard_button = pygame.Rect(button_x, 410, button_width, button_height)
        back_button = pygame.Rect(button_x, 500, button_width, button_height)
        
        mouse_pos = pygame.mouse.get_pos()

        # Easy Button (Green tint)
        easy_color = (120, 171, 105) if easy_button.collidepoint(mouse_pos) else (100, 151, 85)
        pygame.draw.rect(self.screen, easy_color, easy_button, border_radius=10)
        easy_text = self.small_font.render("Easy", True, TEXT_COLOR)
        self.screen.blit(easy_text, (easy_button.centerx - easy_text.get_width() // 2, 
                                     easy_button.centery - easy_text.get_height() // 2))
        
        # Medium Button (Yellow tint)
        medium_color = (171, 151, 85) if medium_button.collidepoint(mouse_pos) else (151, 131, 65)
        pygame.draw.rect(self.screen, medium_color, medium_button, border_radius=10)
        medium_text = self.small_font.render("Medium", True, TEXT_COLOR)
        self.screen.blit(medium_text, (medium_button.centerx - medium_text.get_width() // 2, 
                                       medium_button.centery - medium_text.get_height() // 2))
        
        # Hard Button (Red tint)
        hard_color = (171, 85, 85) if hard_button.collidepoint(mouse_pos) else (151, 65, 65)
        pygame.draw.rect(self.screen, hard_color, hard_button, border_radius=10)
        hard_text = self.small_font.render("Hard", True, TEXT_COLOR)
        self.screen.blit(hard_text, (hard_button.centerx - hard_text.get_width() // 2, 
                                     hard_button.centery - hard_text.get_height() // 2))
        
        # Back Button
        back_color = (100, 100, 100) if back_button.collidepoint(mouse_pos) else (70, 70, 70)
        pygame.draw.rect(self.screen, back_color, back_button, border_radius=10)
        back_text = self.small_piece_font.render("← Back to Menu", True, TEXT_COLOR)
        self.screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2, 
                                     back_button.centery - back_text.get_height() // 2))
        
        return easy_button, medium_button, hard_button, back_button

    def _draw_time_selection_menu(self, time_input):
        """
        Draw time control selection menu for PvP

        Args:
            time_input: Dict with time input values and active field

        Returns:
            Dict with input_rects, start_button, no_time_button, back_button
        """
        # Title
        title = self.font.render("Time Control", True, TEXT_COLOR)
        self.screen.blit(title, (WINDOW_SIZE // 2 - title.get_width() // 2, 80))

        subtitle = self.small_font.render("Set time for each player (or play without time)", True, TEXT_COLOR)
        self.screen.blit(subtitle, (WINDOW_SIZE // 2 - subtitle.get_width() // 2, 130))

        mouse_pos = pygame.mouse.get_pos()
        input_rects = {}

        # Input field dimensions
        field_width = 60
        field_height = 40
        label_offset = 150

        # White player time
        white_label = self.small_font.render("White:", True, TEXT_COLOR)
        self.screen.blit(white_label, (WINDOW_SIZE // 2 - label_offset, 190))

        # White minutes
        white_min_rect = pygame.Rect(WINDOW_SIZE // 2 - 50, 185, field_width, field_height)
        input_rects['white_minutes'] = white_min_rect
        self._draw_input_field(white_min_rect, time_input['white_minutes'],
                               time_input['active_field'] == 'white_minutes')

        colon1 = self.font.render(":", True, TEXT_COLOR)
        self.screen.blit(colon1, (WINDOW_SIZE // 2 + 15, 188))

        # White seconds
        white_sec_rect = pygame.Rect(WINDOW_SIZE // 2 + 30, 185, field_width, field_height)
        input_rects['white_seconds'] = white_sec_rect
        self._draw_input_field(white_sec_rect, time_input['white_seconds'],
                               time_input['active_field'] == 'white_seconds')

        min_label = self.small_font.render("min    sec", True, (150, 150, 150))
        self.screen.blit(min_label, (WINDOW_SIZE // 2 - 45, 230))

        # Black player time
        black_label = self.small_font.render("Black:", True, TEXT_COLOR)
        self.screen.blit(black_label, (WINDOW_SIZE // 2 - label_offset, 290))

        # Black minutes
        black_min_rect = pygame.Rect(WINDOW_SIZE // 2 - 50, 285, field_width, field_height)
        input_rects['black_minutes'] = black_min_rect
        self._draw_input_field(black_min_rect, time_input['black_minutes'],
                               time_input['active_field'] == 'black_minutes')

        colon2 = self.font.render(":", True, TEXT_COLOR)
        self.screen.blit(colon2, (WINDOW_SIZE // 2 + 15, 288))

        # Black seconds
        black_sec_rect = pygame.Rect(WINDOW_SIZE // 2 + 30, 285, field_width, field_height)
        input_rects['black_seconds'] = black_sec_rect
        self._draw_input_field(black_sec_rect, time_input['black_seconds'],
                               time_input['active_field'] == 'black_seconds')

        min_label2 = self.small_font.render("min    sec", True, (150, 150, 150))
        self.screen.blit(min_label2, (WINDOW_SIZE // 2 - 45, 330))

        # Buttons
        button_width = 300
        button_height = 50
        button_x = WINDOW_SIZE // 2 - button_width // 2

        # Start with time button
        start_button = pygame.Rect(button_x, 380, button_width, button_height)
        start_color = BUTTON_HOVER if start_button.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(self.screen, start_color, start_button, border_radius=10)
        start_text = self.small_font.render("Start with Time", True, TEXT_COLOR)
        self.screen.blit(start_text, (start_button.centerx - start_text.get_width() // 2,
                                      start_button.centery - start_text.get_height() // 2))

        # No time button
        no_time_button = pygame.Rect(button_x, 450, button_width, button_height)
        no_time_color = (100, 100, 100) if no_time_button.collidepoint(mouse_pos) else (70, 70, 70)
        pygame.draw.rect(self.screen, no_time_color, no_time_button, border_radius=10)
        no_time_text = self.small_font.render("Play without Time", True, TEXT_COLOR)
        self.screen.blit(no_time_text, (no_time_button.centerx - no_time_text.get_width() // 2,
                                        no_time_button.centery - no_time_text.get_height() // 2))

        # Back button
        back_button = pygame.Rect(button_x, 520, button_width, button_height)
        back_color = (80, 80, 80) if back_button.collidepoint(mouse_pos) else (60, 60, 60)
        pygame.draw.rect(self.screen, back_color, back_button, border_radius=10)
        back_text = self.small_font.render("← Back", True, TEXT_COLOR)
        self.screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2,
                                     back_button.centery - back_text.get_height() // 2))

        # Instructions
        hint = self.small_font.render("Click a field to edit, TAB to switch fields", True, (150, 150, 150))
        self.screen.blit(hint, (WINDOW_SIZE // 2 - hint.get_width() // 2, 600))

        return {
            'input_rects': input_rects,
            'start_button': start_button,
            'no_time_button': no_time_button,
            'back_button': back_button
        }

    def _draw_input_field(self, rect, value, is_active):
        """
        Draw a text input field

        Args:
            rect: pygame.Rect for the field
            value: Current value string
            is_active: Whether this field is currently active
        """
        # Background
        bg_color = (80, 80, 80) if is_active else (50, 50, 50)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)

        # Border
        border_color = (130, 151, 105) if is_active else (100, 100, 100)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)

        # Text
        display_text = value if value else "00"
        text = self.font.render(display_text, True, TEXT_COLOR if value else (100, 100, 100))
        self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                rect.centery - text.get_height() // 2))

    def _draw_button(self, rect, text, mouse_pos):
        """
        Draw a button with hover effect

        Args:
            rect: pygame rect object
            text: what text to put on button
            mouse_pos: mouse position
        """
        color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        
        text_surface = self.small_piece_font.render(text, True, TEXT_COLOR)
        self.screen.blit(text_surface, (rect.centerx - text_surface.get_width() // 2,
                                       rect.centery - text_surface.get_height() // 2))

    def get_promotion_rects(self, to_row, to_col, color):
        """
        Get the rectangles for promotion piece selection

        Args:
            to_row: destination row of the pawn
            to_col: destination column of the pawn
            color: color of the promoting pawn

        Returns:
            List of pygame.Rect for each piece option (Q, R, B, N)
        """
        # Position dialog above or below the promotion square
        x = BOARD_OFFSET + to_col * SQUARE_SIZE

        if color == Color.WHITE:
            # White promotes on row 0, show dialog going down
            start_y = BOARD_OFFSET
        else:
            # Black promotes on row 7, show dialog going up
            start_y = BOARD_OFFSET + (7 - 3) * SQUARE_SIZE

        rects = []
        for i in range(4):
            rect = pygame.Rect(x, start_y + i * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            rects.append(rect)

        return rects

    def draw_promotion_dialog(self, to_row, to_col, color):
        """
        Draw the promotion piece selection dialog

        Args:
            to_row: destination row of the pawn
            to_col: destination column of the pawn
            color: color of the promoting pawn
        """
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Get piece options based on color
        pieces = [
            (color, PieceType.QUEEN),
            (color, PieceType.ROOK),
            (color, PieceType.BISHOP),
            (color, PieceType.KNIGHT),
        ]

        rects = self.get_promotion_rects(to_row, to_col, color)
        mouse_pos = pygame.mouse.get_pos()

        for i, rect in enumerate(rects):
            # Draw background (highlight on hover)
            if rect.collidepoint(mouse_pos):
                bg_color = (100, 100, 100)
            else:
                bg_color = (70, 70, 70)

            pygame.draw.rect(self.screen, bg_color, rect)
            pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)  # Border

            # Draw piece symbol
            piece_color, piece_type = pieces[i]
            symbol = self.PIECE_SYMBOLS[(piece_color, piece_type)]
            text = self.piece_font.render(symbol, True,
                                         (255, 255, 255) if piece_color == Color.WHITE else (0, 0, 0))
            text_x = rect.centerx - text.get_width() // 2
            text_y = rect.centery - text.get_height() // 2
            self.screen.blit(text, (text_x, text_y))