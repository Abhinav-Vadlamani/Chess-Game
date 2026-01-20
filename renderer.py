import pygame
from constants import *

class Renderer:
    PIECE_SYMBOLS = {
        (Color.WHITE, PieceType.KING): '♔',
        (Color.WHITE, PieceType.QUEEN): '♕',
        (Color.WHITE, PieceType.ROOK): '♖',
        (Color.WHITE, PieceType.BISHOP): '♗',
        (Color.WHITE, PieceType.KNIGHT): '♘',
        (Color.WHITE, PieceType.PAWN): '♙',
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
    
    def draw_board(self, board, selected_square = None, valid_moves = None):
        """
        Draw the chess board

        Args:
            board: ChessBoard instance
            selected_square: Currently selected square or None
            valid_moves: List of valid moves
        """

        valid_moves = valid_moves or []
        
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE

                # Highlight selected square
                if selected_square == (row, col):
                    color = HIGHLIGHT_SELECTED

                # highlight valid moves
                elif (row, col) in valid_moves:
                    color = HIGHLIGHT_MOVE
                
                # Highlight king in check
                piece = board.get_piece(row, col)
                if piece and piece.piece_type == PieceType.KING and board.is_in_check(piece.color):
                    color = HIGHLIGHT_CHECK
                
                x = BOARD_OFFSET + col * SQUARE_SIZE
                y = BOARD_OFFSET + row * SQUARE_SIZE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    def draw_pieces(self, board):
        """
        Draw chess pieces on the board

        Args:
            board: ChessBoard instance
        """

        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    symbol = self.PIECE_SYMBOLS[(piece.color, piece.piece_type)]
                    text = self.piece_font.render(symbol, True,
                                            (255, 255, 255) if piece.color == Color.WHITE else (0, 0, 0))
                    x = BOARD_OFFSET + col * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2
                    y = BOARD_OFFSET + row * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_height() // 2
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

    def draw_game_ui(self, board, game_mode, game_over = False, winner = None):
        """
        Draw game UI elements

        Args:
            board: ChessBoard instance
            game_mode: Current game mode (pvp or pvb)
            game_over: Whether or not the game is over
            winner: Winner of the game
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

        # Controls
        controls_text = "ESC: Menu  |  R: Restart  |  Q: Quit"
        text = self.small_font.render(controls_text, True, TEXT_COLOR)

        x_pos = WINDOW_SIZE // 2 - text.get_width() // 2
        y_pos = BOARD_OFFSET + BOARD_SIZE + 35
        self.screen.blit(text, (x_pos, y_pos))
        
        # Game over message
        if game_over:
            self._draw_game_over_overlay(winner)

    def _draw_game_over_overlay(self, winner):
        """
        Draw game over overlay

        Args:
            winner: player that won
        """

        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        if winner:
            message = f"{winner} wins by checkmate!"
        else:
            message = "Stalemate - Draw!"
        
        text = self.font.render(message, True, TEXT_COLOR)
        self.screen.blit(text, (WINDOW_SIZE // 2 - text.get_width() // 2, WINDOW_SIZE // 2 - 50))
        
        restart_text = self.small_font.render("Press R to restart or Q to quit", True, TEXT_COLOR)
        self.screen.blit(restart_text, (WINDOW_SIZE // 2 - restart_text.get_width() // 2, 
                                       WINDOW_SIZE // 2 + 20))
        
    
    def draw_menu(self, game_mode = None):
        """
        Draw main menu or color selection menu

        Args:
            game_mode: Current game mode

        Returns:
            Tuple of buttons
        """

        self.screen.fill(BG_COLOR)

        if game_mode == 'pvb_color_select':
            return self._draw_color_selection_menu()
        elif game_mode == 'pvb_difficulty_select':
            return self._draw_difficulty_selection_menu()
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
        hard_text = self.small_font.render("Hard - Strategic", True, TEXT_COLOR)
        self.screen.blit(hard_text, (hard_button.centerx - hard_text.get_width() // 2, 
                                     hard_button.centery - hard_text.get_height() // 2))
        
        # Back Button
        back_color = (100, 100, 100) if back_button.collidepoint(mouse_pos) else (70, 70, 70)
        pygame.draw.rect(self.screen, back_color, back_button, border_radius=10)
        back_text = self.small_piece_font.render("← Back to Menu", True, TEXT_COLOR)
        self.screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2, 
                                     back_button.centery - back_text.get_height() // 2))
        
        return easy_button, medium_button, hard_button, back_button
                

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