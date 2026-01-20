from constants import PieceType, Color
from piece import Piece

def get_pawn_moves(board, row, col, en_passant_target):
    """
    Generate moves for a pawn

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
        en_passant_target: target for en passant moves
    
    Returns:
        list of possble moves
    """

    moves = []
    piece = board[row][col]
    direction = -1 if piece.color == Color.WHITE else 1

    # forward moves
    new_row = row + direction
    if 0 <= new_row < 8 and board[new_row][col] is None:
        moves.append((new_row, col))

        # Double move
        if not piece.has_moved and board[row + 2 * direction][col] is None:
            moves.append((row + 2 * direction, col))
    
    # Captures
    for dir in [-1, 1]:
        new_col = col + dir
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target and target.color != piece.color:
                moves.append((new_row, new_col))
            
            # en passant
            elif en_passant_target == (new_row, new_col):
                moves.append((new_row, new_col))
    return moves
            
def get_knight_moves(board, row, col):
    """
    Generate moves for a knight

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
    
    Returns:
        list of possble moves
    """

    moves = []
    piece = board[row][col]
    directions = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1)]
    
    for dir in directions:
        new_row = dir[0] + row
        new_col = dir[1] + col
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if not target or target.color != piece.color:
                moves.append((new_row, new_col))
    return moves

def get_sliding_moves(board, row, col, directions):
    """
    Generate moves for any sliding pieces

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
        directions: what directions to travel
    
    Returns:
        list of possble moves
    """

    moves = []
    piece = board[row][col]

    for dir in directions:
        new_row = row + dir[0]
        new_col = col + dir[1]
        while 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if not target:
                moves.append((new_row, new_col))
            elif target.color != piece.color:
                moves.append((new_row, new_col))
                break
            else:
                break
            new_row += dir[0]
            new_col += dir[1]
    return moves

def get_bishop_moves(board, row, col):
    """
    Generate moves for bishop

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
    
    Returns:
        list of possble moves
    """

    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return get_sliding_moves(board, row, col, directions)

def get_rook_moves(board, row, col):
    """
    Generate moves for rook

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
    
    Returns:
        list of possble moves
    """

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return get_sliding_moves(board, row, col, directions)

def get_queen_moves(board, row, col):
    """
    Generate moves for queen

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
    
    Returns:
        list of possble moves
    """

    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), 
                      (0, 1), (1, -1), (1, 0), (1, 1)]
    return get_sliding_moves(board, row, col, directions)

def get_king_moves(board, row, col):
    """
    Generate moves for king

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
    
    Returns:
        list of possble moves
    """

    moves = []
    piece = board[row][col]

    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board[new_row][new_col]
                if not target or target.color != piece.color:
                    moves.append((new_row, new_col))
    
    return moves

def get_pawn_attack_squares(board, row, col):
    """
    Generate moves for king

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
    
    Returns:
        squares attacked by a pawn
    """

    piece = board[row][col]
    direction = -1 if piece.color == Color.WHITE else 1
    attacks = []

    for dc in [-1, 1]:
        new_row = row + direction
        new_col = col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            attacks.append((new_row, new_col))
    
    return attacks

def get_king_attack_squares(board, row, col):
    """
    Generate squares attacked by a king

    Args:
        board: array of the board state
        row: row where pawn is
        col: column where pawn is
    
    Returns:
        list of possble moves
    """
     
    attacks = []
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            new_row = row + dr
            new_col = col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                attacks.append((new_row, new_col))
    return attacks
    
