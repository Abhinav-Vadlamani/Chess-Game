import pygame
import math
from pathlib import Path
from piece import Piece
from constants import (PieceType, Color, WINDOW_SIZE, BOARD_SIZE, BOARD_OFFSET,
                       SQUARE_SIZE, LIGHT_SQUARE, DARK_SQUARE, HIGHLIGHT_SELECTED,
                       HIGHLIGHT_CHECK, HIGHLIGHT_LAST_MOVE, BG_COLOR, TEXT_COLOR,
                       BUTTON_COLOR, BUTTON_HOVER, FILES, RANKS)

PANEL_TEXT_COLOR = (248, 249, 252)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.small_piece_font = pygame.font.SysFont('Apple Symbols', 24)
        self.piece_sprites, self.captured_sprites = self._load_piece_sprites()
        self.analysis_sprites = {
            key: pygame.transform.smoothscale(sprite, (56, 56))
            for key, sprite in self.piece_sprites.items()
        }

    @staticmethod
    def _sprite_path(color, piece_type):
        """Return the high-resolution CBurnett sprite matching a chess piece."""
        color_code = 'w' if color == Color.WHITE else 'b'
        type_code = {
            PieceType.KING: 'K', PieceType.QUEEN: 'Q', PieceType.ROOK: 'R',
            PieceType.BISHOP: 'B', PieceType.KNIGHT: 'N', PieceType.PAWN: 'P',
        }[piece_type]
        return (Path(__file__).resolve().parent / 'assets' / 'pieces' / 'cburnett'
                / f'{color_code}{type_code}.png')

    def _load_piece_sprites(self):
        """Load each piece once so play and animation reuse sharp, stable surfaces."""
        full_size, captured_size = 74, 23
        sprites, captured = {}, {}
        for color in Color:
            for piece_type in PieceType:
                image = pygame.image.load(str(self._sprite_path(color, piece_type))).convert_alpha()
                key = (color, piece_type)
                sprites[key] = pygame.transform.smoothscale(image, (full_size, full_size))
                captured[key] = pygame.transform.smoothscale(image, (captured_size, captured_size))
        return sprites, captured

    def _piece_surface(self, piece, piece_type=None):
        """Return a bundled raster sprite instead of rendering a Unicode glyph."""
        return self.piece_sprites[(piece.color, piece_type or piece.piece_type)]

    def draw_board(self, board, selected_square=None, valid_moves=None, last_move=None):
        """Draw the squares, highlights, and valid-move markers (but not the pieces)."""
        valid_moves = valid_moves or []

        # Fine graphite frame: a quiet, printed-board detail borrowed from the reference.
        board_rect = pygame.Rect(BOARD_OFFSET - 2, BOARD_OFFSET - 2,
                                 BOARD_SIZE + 4, BOARD_SIZE + 4)
        pygame.draw.rect(self.screen, (61, 69, 83), board_rect, border_radius=1)

        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE

                # Highlights, from lowest to highest priority.
                if last_move and (row, col) in last_move:
                    color = HIGHLIGHT_LAST_MOVE
                if selected_square == (row, col):
                    color = HIGHLIGHT_SELECTED
                piece = board.get_piece(row, col)
                if piece and piece.piece_type == PieceType.KING and board.is_in_check(piece.color):
                    color = HIGHLIGHT_CHECK

                x = BOARD_OFFSET + col * SQUARE_SIZE
                y = BOARD_OFFSET + row * SQUARE_SIZE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # Mark each valid destination: a ring over captures, a dot over empty squares.
        for row, col in valid_moves:
            center_x = BOARD_OFFSET + col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = BOARD_OFFSET + row * SQUARE_SIZE + SQUARE_SIZE // 2
            if board.get_piece(row, col):
                pygame.draw.circle(self.screen, (100, 100, 100), (center_x, center_y), SQUARE_SIZE // 2 - 4, 4)
            else:
                pygame.draw.circle(self.screen, (100, 100, 100), (center_x, center_y), SQUARE_SIZE // 6)

    def draw_pieces(self, board, skip_square=None, skip_squares=None):
        """Draw all pieces, optionally omitting squares managed by an animation."""
        skipped = set(skip_squares or [])
        if skip_square:
            skipped.add(skip_square)
        for row in range(8):
            for col in range(8):
                if (row, col) in skipped:
                    continue
                piece = board.get_piece(row, col)
                if piece:
                    text = self._piece_surface(piece)
                    x = BOARD_OFFSET + col * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2
                    y = BOARD_OFFSET + row * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_height() // 2
                    self.screen.blit(text, (x, y))

    def draw_move_animation(self, animation):
        """Draw a moving piece plus capture, castling, and promotion effects."""
        elapsed = pygame.time.get_ticks() - animation['started_at']
        progress = min(1.0, elapsed / animation['duration'])
        eased = 1 - (1 - progress) ** 3

        if animation['is_capture']:
            self._draw_capture_effect(animation['to'], progress)

        self._draw_animated_piece(animation['piece'], animation['from'], animation['to'], eased,
                                  animation.get('moving_piece_type'),
                                  from_pixel=animation.get('from_pixel'))

        if animation.get('rook'):
            rook = animation['rook']
            self._draw_animated_piece(rook['piece'], rook['from'], rook['to'], eased)

        if animation.get('promotion_piece'):
            self._draw_promotion_effect(animation, progress)

    def _draw_animated_piece(self, piece, from_square, to_square, progress, piece_type=None,
                             scale=1.0, alpha=255, from_pixel=None):
        """Draw one piece interpolated between two board squares."""
        from_row, from_col = from_square
        to_row, to_col = to_square
        start = from_pixel or (BOARD_OFFSET + from_col * SQUARE_SIZE + SQUARE_SIZE / 2,
                               BOARD_OFFSET + from_row * SQUARE_SIZE + SQUARE_SIZE / 2)
        end = (BOARD_OFFSET + to_col * SQUARE_SIZE + SQUARE_SIZE / 2,
               BOARD_OFFSET + to_row * SQUARE_SIZE + SQUARE_SIZE / 2)
        center = (start[0] + (end[0] - start[0]) * progress,
                  start[1] + (end[1] - start[1]) * progress)
        # Animation adjusts alpha/scale, so work on a copy rather than mutating
        # the cached sprite used by every other piece on the board.
        surface = self._piece_surface(piece, piece_type).copy()
        if scale != 1.0:
            surface = pygame.transform.smoothscale(surface,
                (max(1, int(surface.get_width() * scale)), max(1, int(surface.get_height() * scale))))
        if alpha != 255:
            surface.set_alpha(max(0, min(255, alpha)))
        self.screen.blit(surface, (int(center[0] - surface.get_width() / 2),
                                   int(center[1] - surface.get_height() / 2)))

    def _draw_capture_effect(self, square, progress):
        """A brief, restrained burst marks the square where material was taken."""
        if progress < 0.55:
            return
        impact = (progress - 0.55) / 0.45
        row, col = square
        center = (BOARD_OFFSET + col * SQUARE_SIZE + SQUARE_SIZE // 2,
                  BOARD_OFFSET + row * SQUARE_SIZE + SQUARE_SIZE // 2)
        intensity = int(190 * (1 - impact))
        radius = int(SQUARE_SIZE * (0.18 + 0.32 * impact))
        glow = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 204, 96, intensity), (SQUARE_SIZE // 2, SQUARE_SIZE // 2), radius, 3)
        self.screen.blit(glow, (center[0] - SQUARE_SIZE // 2, center[1] - SQUARE_SIZE // 2))
        for index in range(6):
            angle = index * math.tau / 6 + impact * 2
            distance = radius + 8
            point = (int(center[0] + math.cos(angle) * distance),
                     int(center[1] + math.sin(angle) * distance))
            pygame.draw.circle(self.screen, (255, 220, 130), point, max(1, int(3 * (1 - impact))))

    def _draw_promotion_effect(self, animation, progress):
        """Morph the arriving pawn into its selected promotion piece."""
        if progress < 0.58:
            return
        morph = (progress - 0.58) / 0.42
        square = animation['to']
        self._draw_animated_piece(animation['piece'], square, square, 1, animation['moving_piece_type'],
                                  1 - 0.25 * morph, int(255 * (1 - morph)))
        self._draw_animated_piece(animation['piece'], square, square, 1, animation['promotion_piece'],
                                  0.75 + 0.25 * morph, int(255 * morph))
        row, col = square
        center = (BOARD_OFFSET + col * SQUARE_SIZE + SQUARE_SIZE // 2,
                  BOARD_OFFSET + row * SQUARE_SIZE + SQUARE_SIZE // 2)
        pygame.draw.circle(self.screen, (255, 224, 119), center, int(20 + 24 * morph), 2)

    def draw_dragged_piece(self, piece, pos):
        """Draw a piece centered on the cursor while it is being dragged."""
        text = self._piece_surface(piece)
        x = pos[0] - text.get_width() // 2
        y = pos[1] - text.get_height() // 2
        self.screen.blit(text, (x, y))

    def draw_coordinates(self):
        """Draw the file letters below the board and rank numbers to its left."""
        for i, file in enumerate(FILES):
            text = self.small_font.render(file, True, TEXT_COLOR)
            x = BOARD_OFFSET + i * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2
            self.screen.blit(text, (x, BOARD_OFFSET + BOARD_SIZE + 10))
        
        for i, rank in enumerate(RANKS):
            text = self.small_font.render(rank, True, TEXT_COLOR)
            y = BOARD_OFFSET + i * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_height() // 2
            self.screen.blit(text, (20, y))

    def draw_game_ui(self, board, game_mode, game_over=False, winner=None, timer_info=None,
                     draw_reason=None, show_move_history=False, game_end_started_at=None,
                     resigned_by=None):
        """Draw the side panel: turn/check/mode labels, timers, captures, controls, overlays."""
        turn_text = "White's turn" if board.current_turn == Color.WHITE else "Black's Turn"
        self.screen.blit(self.small_font.render(turn_text, True, TEXT_COLOR), (WINDOW_SIZE - 200, 20))

        if board.is_in_check(board.current_turn):
            check_text = self.small_font.render("CHECK!", True, (255, 100, 100))
            self.screen.blit(check_text, (WINDOW_SIZE - 200, 50))

        mode_text = "PvP" if game_mode == 'pvp' else "PvBot"
        self.screen.blit(self.small_font.render(mode_text, True, TEXT_COLOR), (20, 20))

        if timer_info:
            self._draw_timers(timer_info, board.current_turn)
        self._draw_captured_pieces(board)

        controls = self.small_font.render("ESC: Menu  |  R: Restart  |  Q: Quit", True, TEXT_COLOR)
        self.screen.blit(controls, (WINDOW_SIZE // 2 - controls.get_width() // 2,
                                    BOARD_OFFSET + BOARD_SIZE + 35))

        if show_move_history:
            self._draw_move_history_panel(board)
        if game_over:
            self._draw_game_over_overlay(winner, timer_info, draw_reason, game_end_started_at,
                                         resigned_by)

    @staticmethod
    def _format_time(ms):
        """Format a millisecond duration as MM:SS (clamped at zero)."""
        total_seconds = max(0, ms) // 1000
        return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"

    def _draw_clock(self, box, time_ms, fill):
        """Draw one player's clock box, filled with the given color."""
        pygame.draw.rect(self.screen, fill, box, border_radius=5)
        pygame.draw.rect(self.screen, (100, 100, 100), box, 2, border_radius=5)
        text = self.font.render(self._format_time(time_ms), True, PANEL_TEXT_COLOR)
        self.screen.blit(text, (box.centerx - text.get_width() // 2,
                                box.centery - text.get_height() // 2))

    def _draw_timers(self, timer_info, current_turn):
        """Draw both players' chess clocks beside the board (active player is brighter)."""
        box_width, box_height = 65, 40
        right_x = BOARD_OFFSET + BOARD_SIZE + 5
        black_box = pygame.Rect(right_x, BOARD_OFFSET, box_width, box_height)
        black_fill = (60, 60, 60) if current_turn == Color.BLACK else (40, 40, 40)
        self._draw_clock(black_box, timer_info['black_time'], black_fill)

        white_box = pygame.Rect(right_x, BOARD_OFFSET + BOARD_SIZE - box_height, box_width, box_height)
        white_fill = (80, 80, 80) if current_turn == Color.WHITE else (50, 50, 50)
        self._draw_clock(white_box, timer_info['white_time'], white_fill)

    def _draw_captured_pieces(self, board):
        """Draw each side's captured pieces and the material advantage, chess.com style."""
        captured = board.get_captured_pieces()

        # Piece order by value (high to low)
        piece_order = [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT, PieceType.PAWN]
        piece_values = {
            PieceType.QUEEN: 9, PieceType.ROOK: 5, PieceType.BISHOP: 3,
            PieceType.KNIGHT: 3, PieceType.PAWN: 1
        }

        def sort_pieces(pieces):
            """Sort pieces by value (highest first)"""
            return sorted(pieces, key=lambda p: piece_order.index(p.piece_type))

        def calc_material(pieces):
            """Calculate total material value"""
            return sum(piece_values.get(p.piece_type, 0) for p in pieces)

        # Calculate material advantage
        white_material = calc_material(captured['white'])
        black_material = calc_material(captured['black'])
        advantage = white_material - black_material

        # Position settings
        start_x = BOARD_OFFSET + BOARD_SIZE + 5
        piece_spacing = 16
        black_captured = sort_pieces(captured['black'])
        y_start_black = BOARD_OFFSET + 45
        y = y_start_black
        for piece in black_captured:
            self.screen.blit(self.captured_sprites[(piece.color, piece.piece_type)], (start_x, y))
            y += piece_spacing

        # Show material advantage for black next to first piece
        if advantage < 0 and black_captured:
            adv_text = self.small_font.render(f"+{-advantage}", True, (150, 150, 150))
            self.screen.blit(adv_text, (start_x + 20, y_start_black + 2))

        white_captured = sort_pieces(captured['white'])
        y_start_white = BOARD_OFFSET + BOARD_SIZE - 60
        y = y_start_white
        for piece in white_captured:
            self.screen.blit(self.captured_sprites[(piece.color, piece.piece_type)], (start_x, y))
            y -= piece_spacing

        # Show material advantage for white next to first piece
        if advantage > 0 and white_captured:
            adv_text = self.small_font.render(f"+{advantage}", True, (150, 150, 150))
            self.screen.blit(adv_text, (start_x + 20, y_start_white + 2))

    def get_history_button_rect(self):
        """Return the clickable rectangle for the move-history toggle button."""
        return pygame.Rect(WINDOW_SIZE - 75, 45, 65, 25)

    def draw_history_button(self, show_move_history):
        """Draw the move-history toggle button (labeled Hide when the panel is open)."""
        button = self.get_history_button_rect()
        color = (100, 100, 100) if button.collidepoint(pygame.mouse.get_pos()) else (70, 70, 70)
        pygame.draw.rect(self.screen, color, button, border_radius=5)

        btn_text = "Hide" if show_move_history else "Moves"
        text = self.small_font.render(btn_text, True, PANEL_TEXT_COLOR)
        self.screen.blit(text, (button.centerx - text.get_width() // 2,
                                button.centery - text.get_height() // 2))

    @staticmethod
    def get_resign_button_rect():
        """Return the clickable rectangle for the active-game resign button."""
        return pygame.Rect(WINDOW_SIZE - 75, 80, 65, 25)

    def draw_resign_button(self):
        """Draw a compact, clearly destructive action without overpowering the board."""
        button = self.get_resign_button_rect()
        color = (157, 73, 70) if button.collidepoint(pygame.mouse.get_pos()) else (124, 57, 55)
        pygame.draw.rect(self.screen, color, button, border_radius=5)
        text = self.small_font.render("Resign", True, PANEL_TEXT_COLOR)
        self.screen.blit(text, (button.centerx - text.get_width() // 2,
                                button.centery - text.get_height() // 2))

    def _draw_move_history_panel(self, board):
        """Draw the move-history overlay: numbered rows of white and black moves."""
        panel_width = 200
        panel_height = 400
        panel_x = WINDOW_SIZE // 2 - panel_width // 2
        panel_y = WINDOW_SIZE // 2 - panel_height // 2

        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (40, 40, 40), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 2, border_radius=10)

        # Title
        title = self.font.render("Move History", True, PANEL_TEXT_COLOR)
        self.screen.blit(title, (panel_x + panel_width // 2 - title.get_width() // 2, panel_y + 10))

        # Get move notation
        moves = board.get_move_history_notation()

        # Draw moves in two columns (white and black)
        start_y = panel_y + 50
        row_height = 22
        max_rows = (panel_height - 70) // row_height

        # Scroll offset based on number of moves
        total_move_pairs = (len(moves) + 1) // 2
        scroll_offset = max(0, total_move_pairs - max_rows)

        for i in range(scroll_offset, total_move_pairs):
            row = i - scroll_offset
            if row >= max_rows:
                break

            y = start_y + row * row_height
            move_num = i + 1

            # Move number
            num_text = self.small_font.render(f"{move_num}.", True, (150, 150, 150))
            self.screen.blit(num_text, (panel_x + 10, y))

            # White's move
            white_idx = i * 2
            if white_idx < len(moves):
                white_move = self.small_font.render(moves[white_idx], True, PANEL_TEXT_COLOR)
                self.screen.blit(white_move, (panel_x + 40, y))

            # Black's move
            black_idx = i * 2 + 1
            if black_idx < len(moves):
                black_move = self.small_font.render(moves[black_idx], True, PANEL_TEXT_COLOR)
                self.screen.blit(black_move, (panel_x + 110, y))

        # Show hint to close
        hint = self.small_font.render("Click 'Hide' to close", True, (120, 120, 120))
        self.screen.blit(hint, (panel_x + panel_width // 2 - hint.get_width() // 2,
                                panel_y + panel_height - 25))

    def _draw_game_over_overlay(self, winner, timer_info=None, draw_reason=None, started_at=None,
                                resigned_by=None):
        """Dim the board and reveal the result with a short, ceremonial entrance."""
        elapsed = pygame.time.get_ticks() - started_at if started_at else 500
        progress = min(1.0, elapsed / 500)
        eased = 1 - (1 - progress) ** 3
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.set_alpha(int(200 * eased))
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        if winner == "Draw":
            message = f"Draw - {draw_reason}!" if draw_reason else "Draw!"
        elif resigned_by:
            message = f"{resigned_by} resigned - {winner} wins!"
        elif winner:
            timed_out = timer_info and (timer_info['white_time'] <= 0 or timer_info['black_time'] <= 0)
            message = f"{winner} wins on time!" if timed_out else f"{winner} wins by checkmate!"
        else:
            message = "Draw!"

        # A small amber halo makes the result feel distinct without obscuring the board.
        halo = pygame.Surface((260, 150), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (222, 176, 80, int(55 * eased)), halo.get_rect())
        self.screen.blit(halo, (WINDOW_SIZE // 2 - 130, WINDOW_SIZE // 2 - 105))

        text = self.font.render(message, True, PANEL_TEXT_COLOR)
        text.set_alpha(int(255 * eased))
        y = WINDOW_SIZE // 2 - 50 - int((1 - eased) * 18)
        self.screen.blit(text, (WINDOW_SIZE // 2 - text.get_width() // 2, y))

        restart_text = self.small_font.render("Press R to restart or Q to quit", True, PANEL_TEXT_COLOR)
        restart_text.set_alpha(int(255 * max(0, (progress - 0.25) / 0.75)))
        self.screen.blit(restart_text, (WINDOW_SIZE // 2 - restart_text.get_width() // 2,
                                       WINDOW_SIZE // 2 + 20))

        analysis_button = self.get_analysis_button_rect()
        button_color = (79, 108, 158) if analysis_button.collidepoint(pygame.mouse.get_pos()) else (61, 83, 123)
        pygame.draw.rect(self.screen, button_color, analysis_button, border_radius=6)
        label = self.small_font.render("Review game", True, PANEL_TEXT_COLOR)
        self.screen.blit(label, (analysis_button.centerx - label.get_width() // 2,
                                 analysis_button.centery - label.get_height() // 2))

    @staticmethod
    def get_analysis_button_rect():
        """Return the end-screen button that opens the replay and engine analysis."""
        return pygame.Rect(WINDOW_SIZE // 2 - 75, WINDOW_SIZE // 2 + 60, 150, 36)

    @staticmethod
    def get_analysis_previous_rect():
        return pygame.Rect(570, 720, 70, 38)

    @staticmethod
    def get_analysis_next_rect():
        return pygame.Rect(650, 720, 70, 38)

    @staticmethod
    def get_analysis_close_rect():
        return pygame.Rect(690, 25, 80, 34)

    def draw_analysis_workspace(self, board, index, total, played_move, last_move,
                                engine_lines, thinking, stockfish_available):
        """Draw a focused post-game replay board and Stockfish MultiPV rail."""
        self.screen.fill(BG_COLOR)
        title = self.font.render("Game analysis", True, TEXT_COLOR)
        self.screen.blit(title, (30, 25))
        subtitle = self.small_font.render("Replay the game • use Left / Right to navigate", True, (94, 104, 122))
        self.screen.blit(subtitle, (30, 58))

        close = self.get_analysis_close_rect()
        pygame.draw.rect(self.screen, (68, 73, 84), close, border_radius=6)
        close_text = self.small_font.render("Close", True, PANEL_TEXT_COLOR)
        self.screen.blit(close_text, (close.centerx - close_text.get_width() // 2,
                                      close.centery - close_text.get_height() // 2))

        board_rect = pygame.Rect(40, 110, 432, 432)
        self._draw_analysis_board(board, board_rect, last_move)
        evaluation_label = self._draw_evaluation_meter(
            pygame.Rect(board_rect.right + 10, board_rect.y, 18, board_rect.height), engine_lines, thinking,
        )

        details = pygame.Rect(530, 110, 245, 180)
        pygame.draw.rect(self.screen, (42, 48, 61), details, border_radius=10)
        pygame.draw.rect(self.screen, (87, 99, 122), details, 1, border_radius=10)
        detail_title = self.font.render("Position", True, PANEL_TEXT_COLOR)
        self.screen.blit(detail_title, (details.x + 18, details.y + 18))
        stockfish_label = self.small_font.render("Stockfish evaluation", True, (166, 187, 224))
        self.screen.blit(stockfish_label, (details.x + 18, details.y + 50))

        evaluation_text = self.small_font.render(f"Eval: {evaluation_label}", True, (239, 211, 129))
        self.screen.blit(evaluation_text, (details.x + 18, details.y + 82))

        move_label = "Starting position" if index == 0 else f"Played: {played_move}"
        move_text = self.small_font.render(move_label, True, (239, 211, 129))
        self.screen.blit(move_text, (details.x + 18, details.y + 112))
        progress = self.small_font.render(f"Move {index} of {total}", True, (169, 177, 192))
        self.screen.blit(progress, (details.x + 18, details.y + 140))

        lines_panel = pygame.Rect(30, 575, 745, 130)
        pygame.draw.rect(self.screen, (42, 48, 61), lines_panel, border_radius=10)
        pygame.draw.rect(self.screen, (87, 99, 122), lines_panel, 1, border_radius=10)
        lines_title = self.small_font.render("Engine lines", True, PANEL_TEXT_COLOR)
        self.screen.blit(lines_title, (lines_panel.x + 14, lines_panel.y + 10))
        top_three = self.small_font.render("Top 3", True, (166, 187, 224))
        self.screen.blit(top_three, (lines_panel.right - 14 - top_three.get_width(), lines_panel.y + 10))

        if not stockfish_available:
            unavailable = self.small_font.render("Stockfish is unavailable.", True, (226, 157, 150))
            self.screen.blit(unavailable, (lines_panel.x + 16, lines_panel.y + 48))
        elif thinking:
            waiting = self.small_font.render("Evaluating position…", True, (198, 211, 236))
            self.screen.blit(waiting, (lines_panel.x + 16, lines_panel.y + 48))
        elif not engine_lines:
            empty = self.small_font.render("No engine line returned.", True, (198, 177, 169))
            self.screen.blit(empty, (lines_panel.x + 16, lines_panel.y + 48))
        else:
            for row, line in enumerate(engine_lines):
                y = lines_panel.y + 35 + row * 28
                pygame.draw.rect(self.screen, (54, 62, 78),
                                 (lines_panel.x + 10, y, lines_panel.width - 20, 24), border_radius=4)
                rank = self.small_font.render(f"{line['rank']}", True, (170, 197, 246))
                score = self.small_font.render(line['score'], True, PANEL_TEXT_COLOR)
                self.screen.blit(rank, (lines_panel.x + 22, y + 3))
                self.screen.blit(score, (lines_panel.x + 52, y + 3))
                pv = self._format_principal_variation(line['pv'])
                pv_text = self.small_font.render(pv, True, (221, 225, 233))
                self.screen.blit(pv_text, (lines_panel.x + 120, y + 3))

        previous = self.get_analysis_previous_rect()
        next_button = self.get_analysis_next_rect()
        self._draw_labeled_button(previous, "Previous", (72, 80, 96), (92, 104, 127), pygame.mouse.get_pos())
        self._draw_labeled_button(next_button, "Next", (79, 108, 158), (101, 134, 190), pygame.mouse.get_pos())

    def _draw_evaluation_meter(self, rect, engine_lines, thinking):
        """Draw the analysis evaluation bar and return its human-readable label."""
        white_share = 0.5
        label = "Equal 0.00"
        if thinking:
            label = "Analyzing"
        elif engine_lines:
            line = engine_lines[0]
            mate = line.get('white_mate')
            score_cp = line.get('white_score_cp')
            if mate is not None:
                white_share = 1.0 if mate > 0 else 0.0
                label = f"White M{mate}" if mate > 0 else f"Black M{abs(mate)}"
            elif score_cp is not None:
                # A logistic curve keeps ordinary advantages readable while allowing
                # clearly winning positions to approach either end of the meter.
                bounded_score = max(-1200, min(1200, score_cp))
                white_share = 1 / (1 + math.pow(10, -bounded_score / 400))
                advantage = abs(score_cp) / 100
                if score_cp > 0:
                    label = f"White +{advantage:.2f}"
                elif score_cp < 0:
                    label = f"Black +{advantage:.2f}"

        pygame.draw.rect(self.screen, (31, 36, 45), rect, border_radius=3)
        white_height = round(rect.height * white_share)
        if white_height:
            white_rect = pygame.Rect(rect.x, rect.bottom - white_height, rect.width, white_height)
            pygame.draw.rect(self.screen, (239, 241, 244), white_rect, border_radius=3)
        pygame.draw.rect(self.screen, (93, 104, 124), rect, 1, border_radius=3)
        return label

    def _draw_analysis_board(self, board, rect, last_move):
        """Draw the smaller replay board used by the analysis workspace."""
        square = rect.width // 8
        pygame.draw.rect(self.screen, (55, 63, 78), rect.inflate(4, 4), border_radius=1)
        last_squares = ()
        if last_move:
            last_squares = (last_move.from_position, last_move.to_position)
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                if (row, col) in last_squares:
                    color = HIGHLIGHT_LAST_MOVE
                square_rect = pygame.Rect(rect.x + col * square, rect.y + row * square, square, square)
                pygame.draw.rect(self.screen, color, square_rect)
                piece = board.get_piece(row, col)
                if piece:
                    sprite = self.analysis_sprites[(piece.color, piece.piece_type)]
                    self.screen.blit(sprite, (square_rect.centerx - sprite.get_width() // 2,
                                               square_rect.centery - sprite.get_height() // 2))
        for col, file in enumerate(FILES):
            text = self.small_font.render(file, True, TEXT_COLOR)
            self.screen.blit(text, (rect.x + col * square + square // 2 - text.get_width() // 2, rect.bottom + 6))
        for row, rank in enumerate(RANKS):
            text = self.small_font.render(rank, True, TEXT_COLOR)
            self.screen.blit(text, (rect.x - 17, rect.y + row * square + square // 2 - text.get_height() // 2))

    @staticmethod
    def _format_principal_variation(moves):
        """Make a short UCI principal variation readable in the compact side rail."""
        formatted = [f"{move[:2]}–{move[2:4]}" for move in moves[:4]]
        return "  ".join(formatted)

    def draw_menu(self, game_mode=None, time_input=None, stockfish_available=True):
        """
        Draw the menu for the current mode and return its clickable widgets.

        Returns a tuple of buttons for most menus, or a dict of rects for the
        time-control menu. The caller matches clicks against what it returns.
        """
        self.screen.fill(BG_COLOR)

        if game_mode == 'pvb_color_select':
            return self._draw_color_selection_menu()
        if game_mode == 'pvb_difficulty_select':
            return self._draw_difficulty_selection_menu(stockfish_available)
        if game_mode == 'pvp_time_select':
            return self._draw_time_selection_menu(time_input)
        return self._draw_main_menu()

    def _draw_title(self, text, y=100):
        """Draw a centered menu title at height y."""
        title = self.font.render(text, True, TEXT_COLOR)
        self.screen.blit(title, (WINDOW_SIZE // 2 - title.get_width() // 2, y))

    def _draw_main_menu(self):
        """Draw the mode-selection menu; return (pvp_button, pvb_button)."""
        self._draw_title("Chess Game")

        button_width, button_height = 300, 60
        button_x = WINDOW_SIZE // 2 - button_width // 2
        pvp_button = pygame.Rect(button_x, 250, button_width, button_height)
        pvb_button = pygame.Rect(button_x, 350, button_width, button_height)

        mouse_pos = pygame.mouse.get_pos()
        self._draw_button(pvp_button, "Player vs Player", mouse_pos)
        self._draw_button(pvb_button, "Player vs Bot", mouse_pos)

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
        """Draw the color-choice menu; return (white_button, black_button, back_button)."""
        self._draw_title("Choose Your Color")

        button_width, button_height = 300, 60
        button_x = WINDOW_SIZE // 2 - button_width // 2
        white_button = pygame.Rect(button_x, 250, button_width, button_height)
        black_button = pygame.Rect(button_x, 350, button_width, button_height)
        back_button = pygame.Rect(button_x, 470, button_width, button_height)

        mouse_pos = pygame.mouse.get_pos()
        self._draw_button(white_button, "Play as White ♔", mouse_pos)
        self._draw_button(black_button, "Play as Black ♚", mouse_pos)
        self._draw_back_button(back_button, mouse_pos)

        return white_button, black_button, back_button

    def _draw_difficulty_selection_menu(self, stockfish_available):
        """Draw difficulty choices, including Stockfish when a local engine is installed."""
        self._draw_title("Choose Difficulty", y=55)
        subtitle = self.small_font.render("Select AI difficulty level", True, TEXT_COLOR)
        self.screen.blit(subtitle, (WINDOW_SIZE // 2 - subtitle.get_width() // 2, 105))

        button_width, button_height = 300, 60
        button_x = WINDOW_SIZE // 2 - button_width // 2
        easy_button = pygame.Rect(button_x, 155, button_width, button_height)
        medium_button = pygame.Rect(button_x, 235, button_width, button_height)
        hard_button = pygame.Rect(button_x, 315, button_width, button_height)
        impossible_button = pygame.Rect(button_x, 395, button_width, button_height)
        back_button = pygame.Rect(button_x, 505, button_width, button_height)

        mouse_pos = pygame.mouse.get_pos()
        # Each level has a green/yellow/red tint (base color, hover color).
        self._draw_labeled_button(easy_button, "Easy", (100, 151, 85), (120, 171, 105), mouse_pos)
        self._draw_labeled_button(medium_button, "Medium", (151, 131, 65), (171, 151, 85), mouse_pos)
        self._draw_labeled_button(hard_button, "Hard", (151, 65, 65), (171, 85, 85), mouse_pos)
        if stockfish_available:
            self._draw_labeled_button(impossible_button, "Impossible",
                                      (53, 58, 82), (76, 83, 116), mouse_pos)
        else:
            self._draw_labeled_button(impossible_button, "Impossible",
                                      (105, 108, 116), (105, 108, 116), mouse_pos,
                                      text_color=(185, 188, 195))
            hint = self.small_font.render("Install Stockfish to unlock", True, (110, 74, 74))
            self.screen.blit(hint, (WINDOW_SIZE // 2 - hint.get_width() // 2, 462))
        self._draw_back_button(back_button, mouse_pos)

        return easy_button, medium_button, hard_button, impossible_button, back_button

    def _draw_time_selection_menu(self, time_input):
        """Draw the PvP time-control menu; return its input rects and buttons as a dict."""
        self._draw_title("Time Control", y=80)

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

        # Both players must have time > 0 before the timed game can start.
        def field_seconds(player):
            minutes = int(time_input[f'{player}_minutes'] or '0')
            seconds = int(time_input[f'{player}_seconds'] or '0')
            return minutes * 60 + seconds

        time_valid = field_seconds('white') > 0 and field_seconds('black') > 0

        button_width, button_height = 300, 50
        button_x = WINDOW_SIZE // 2 - button_width // 2

        # Start button: green when valid, greyed out otherwise.
        start_button = pygame.Rect(button_x, 380, button_width, button_height)
        if time_valid:
            start_color = BUTTON_HOVER if start_button.collidepoint(mouse_pos) else BUTTON_COLOR
        else:
            start_color = (80, 80, 80)
        pygame.draw.rect(self.screen, start_color, start_button, border_radius=10)
        start_text = self.small_font.render("Start with Time", True, PANEL_TEXT_COLOR if time_valid else (120, 120, 120))
        self.screen.blit(start_text, (start_button.centerx - start_text.get_width() // 2,
                                      start_button.centery - start_text.get_height() // 2))

        if not time_valid:
            hint_text = self.small_font.render("(Enter time > 0 for both players)", True, (180, 100, 100))
            self.screen.blit(hint_text, (WINDOW_SIZE // 2 - hint_text.get_width() // 2, 432))

        # The remaining buttons shift down to make room for the hint when shown.
        no_time_button = pygame.Rect(button_x, 460 if not time_valid else 450, button_width, button_height)
        self._draw_labeled_button(no_time_button, "Play without Time", (70, 70, 70), (100, 100, 100), mouse_pos)

        back_button = pygame.Rect(button_x, 530 if not time_valid else 520, button_width, button_height)
        self._draw_labeled_button(back_button, "← Back", (60, 60, 60), (80, 80, 80), mouse_pos,
                                  font=self.small_piece_font)

        hint = self.small_font.render("Click a field to edit, TAB to switch fields", True, (150, 150, 150))
        self.screen.blit(hint, (WINDOW_SIZE // 2 - hint.get_width() // 2, 600))

        return {
            'input_rects': input_rects,
            'start_button': start_button,
            'no_time_button': no_time_button,
            'back_button': back_button
        }

    def _draw_input_field(self, rect, value, is_active):
        """Draw a time-entry field; the active field is brighter and shows a placeholder."""
        bg_color = (80, 80, 80) if is_active else (50, 50, 50)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)

        border_color = (130, 151, 105) if is_active else (100, 100, 100)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)

        display_text = value if value else "00"
        text = self.font.render(display_text, True, PANEL_TEXT_COLOR if value else (150, 156, 168))
        self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                rect.centery - text.get_height() // 2))

    def _draw_labeled_button(self, rect, text, base_color, hover_color, mouse_pos,
                             font=None, text_color=PANEL_TEXT_COLOR):
        """Draw a rounded button with centered text, brightening on hover."""
        color = hover_color if rect.collidepoint(mouse_pos) else base_color
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        surface = (font or self.small_font).render(text, True, text_color)
        self.screen.blit(surface, (rect.centerx - surface.get_width() // 2,
                                   rect.centery - surface.get_height() // 2))

    def _draw_button(self, rect, text, mouse_pos):
        """Draw a primary menu button in the standard green with the piece font."""
        self._draw_labeled_button(rect, text, BUTTON_COLOR, BUTTON_HOVER, mouse_pos,
                                  font=self.small_piece_font)

    def _draw_back_button(self, rect, mouse_pos, text="← Back to Menu"):
        """Draw the standard grey 'back' button used across the menus."""
        self._draw_labeled_button(rect, text, (70, 70, 70), (100, 100, 100), mouse_pos,
                                  font=self.small_piece_font)

    # Promotion choices, top to bottom in the dialog.
    PROMOTION_OPTIONS = [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]

    def get_promotion_rects(self, to_row, to_col, color):
        """Return the four stacked square rects for the promotion dialog (Q, R, B, N)."""
        x = BOARD_OFFSET + to_col * SQUARE_SIZE
        # Grow the dialog down from the top for white, and from row 4 for black,
        # so it always stays on the board next to the promoting pawn.
        start_y = BOARD_OFFSET if color == Color.WHITE else BOARD_OFFSET + 4 * SQUARE_SIZE
        return [pygame.Rect(x, start_y + i * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                for i in range(4)]

    def draw_promotion_dialog(self, to_row, to_col, color):
        """Dim the board and draw the four promotion choices for the player to click."""
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        rects = self.get_promotion_rects(to_row, to_col, color)
        mouse_pos = pygame.mouse.get_pos()

        for rect, piece_type in zip(rects, self.PROMOTION_OPTIONS):
            bg_color = (100, 100, 100) if rect.collidepoint(mouse_pos) else (70, 70, 70)
            pygame.draw.rect(self.screen, bg_color, rect)
            pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)  # Border

            text = self._piece_surface(Piece(piece_type, color))
            self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                    rect.centery - text.get_height() // 2))
