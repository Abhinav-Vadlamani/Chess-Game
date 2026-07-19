"""Pseudo-legal move generation for each piece type.

These functions ignore whether a move leaves the king in check; the board layer
filters those out. Every function takes the raw 8x8 board array and a piece
position, and returns a list of reachable (row, col) squares.
"""

from constants import Color

BOARD_SIZE = 8


def _on_board(row, col):
    """Return True if (row, col) is inside the 8x8 board."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def get_pawn_moves(board, row, col, en_passant_target):
    """Return pawn moves: single/double advance, diagonal and en passant captures."""
    moves = []
    piece = board[row][col]
    direction = -1 if piece.color == Color.WHITE else 1
    new_row = row + direction

    # Forward advance (and the initial two-square move)
    if _on_board(new_row, col) and board[new_row][col] is None:
        moves.append((new_row, col))
        if not piece.has_moved and board[row + 2 * direction][col] is None:
            moves.append((row + 2 * direction, col))

    # Diagonal captures, including en passant
    for dc in (-1, 1):
        new_col = col + dc
        if not _on_board(new_row, new_col):
            continue
        target = board[new_row][new_col]
        if target and target.color != piece.color:
            moves.append((new_row, new_col))
        elif en_passant_target == (new_row, new_col):
            moves.append((new_row, new_col))
    return moves


def get_knight_moves(board, row, col):
    """Return the knight's L-shaped moves onto empty or enemy squares."""
    piece = board[row][col]
    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
               (1, -2), (1, 2), (2, -1), (2, 1)]

    moves = []
    for dr, dc in offsets:
        new_row, new_col = row + dr, col + dc
        if not _on_board(new_row, new_col):
            continue
        target = board[new_row][new_col]
        if not target or target.color != piece.color:
            moves.append((new_row, new_col))
    return moves


def get_sliding_moves(board, row, col, directions):
    """Return moves for a piece that slides until blocked, along each direction."""
    piece = board[row][col]

    moves = []
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        while _on_board(new_row, new_col):
            target = board[new_row][new_col]
            if not target:
                moves.append((new_row, new_col))
            else:
                if target.color != piece.color:
                    moves.append((new_row, new_col))  # capture, then stop
                break
            new_row, new_col = new_row + dr, new_col + dc
    return moves


def get_bishop_moves(board, row, col):
    """Return bishop moves (diagonal sliding)."""
    return get_sliding_moves(board, row, col, [(-1, -1), (-1, 1), (1, -1), (1, 1)])


def get_rook_moves(board, row, col):
    """Return rook moves (orthogonal sliding)."""
    return get_sliding_moves(board, row, col, [(-1, 0), (1, 0), (0, -1), (0, 1)])


def get_queen_moves(board, row, col):
    """Return queen moves (diagonal and orthogonal sliding)."""
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                  (0, 1), (1, -1), (1, 0), (1, 1)]
    return get_sliding_moves(board, row, col, directions)


def get_king_moves(board, row, col):
    """Return the king's one-square moves onto empty or enemy squares."""
    piece = board[row][col]

    moves = []
    for new_row, new_col in _adjacent_squares(row, col):
        target = board[new_row][new_col]
        if not target or target.color != piece.color:
            moves.append((new_row, new_col))
    return moves


def get_pawn_attack_squares(board, row, col):
    """Return the two diagonal squares a pawn attacks (regardless of occupancy)."""
    piece = board[row][col]
    direction = -1 if piece.color == Color.WHITE else 1
    new_row = row + direction
    return [(new_row, col + dc) for dc in (-1, 1) if _on_board(new_row, col + dc)]


def get_king_attack_squares(board, row, col):
    """Return every square adjacent to the king (regardless of occupancy)."""
    return _adjacent_squares(row, col)


def _adjacent_squares(row, col):
    """Return the on-board squares surrounding (row, col)."""
    squares = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            new_row, new_col = row + dr, col + dc
            if _on_board(new_row, new_col):
                squares.append((new_row, new_col))
    return squares
