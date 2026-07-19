import random
import time
import os
import select
import shutil
import subprocess
from constants import Color, PIECE_VALUES, AI_DIFFICULTY_DEPTHS, PieceType, FILES, RANKS
import sunfish


# Weighted opening book in coordinate notation.  Each key is the complete line
# played so far; each value contains (reply, relative frequency) pairs.  The
# weights deliberately permit sound variations instead of repeating one line.
OPENING_BOOK = {
    (): (('e2e4', 45), ('d2d4', 35), ('c2c4', 12), ('g1f3', 8)),
    ('e2e4',): (('e7e5', 40), ('c7c5', 24), ('e7e6', 14), ('c7c6', 10), ('d7d6', 8), ('g7g6', 4)),
    ('d2d4',): (('d7d5', 39), ('g8f6', 31), ('e7e6', 16), ('g7g6', 7), ('f7f5', 4), ('c7c5', 3)),
    ('c2c4',): (('e7e5', 38), ('g8f6', 32), ('c7c5', 18), ('e7e6', 12)),
    ('g1f3',): (('d7d5', 30), ('g8f6', 28), ('c7c5', 24), ('d7d6', 18)),

    # Open Game / Ruy Lopez
    ('e2e4', 'e7e5'): (('g1f3', 60), ('f1c4', 17), ('b1c3', 12), ('f2f4', 11)),
    ('e2e4', 'e7e5', 'g1f3'): (('b8c6', 70), ('g8f6', 20), ('d7d6', 10)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6'): (('f1b5', 52), ('f1c4', 30), ('d2d4', 18)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5'): (('a7a6', 72), ('g8f6', 18), ('f8c5', 10)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6'): (('b5a4', 85), ('b5c4', 15)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6', 'b5a4'): (('g8f6', 75), ('f8c5', 25)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6', 'b5a4', 'g8f6'): (('e1g1', 88), ('d2d3', 12)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6', 'b5a4', 'g8f6', 'e1g1'): (('f8e7', 82), ('b7b5', 18)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6', 'b5a4', 'g8f6', 'e1g1', 'f8e7'): (('f1e1', 80), ('d2d3', 20)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6', 'b5a4', 'g8f6', 'e1g1', 'f8e7', 'f1e1'): (('b7b5', 72), ('d7d6', 28)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6', 'b5a4', 'g8f6', 'e1g1', 'f8e7', 'f1e1', 'b7b5'): (('a4b3', 100),),

    # Sicilian Defence, Open Sicilian
    ('e2e4', 'c7c5'): (('g1f3', 72), ('c2c3', 16), ('c2c4', 12)),
    ('e2e4', 'c7c5', 'g1f3'): (('d7d6', 50), ('b8c6', 34), ('g7g6', 8), ('e7e6', 8)),
    ('e2e4', 'c7c5', 'g1f3', 'd7d6'): (('d2d4', 84), ('f1b5', 16)),
    ('e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4'): (('c5d4', 92), ('g8f6', 8)),
    ('e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4', 'c5d4'): (('f3d4', 90), ('d1d4', 10)),
    ('e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4', 'c5d4', 'f3d4'): (('g8f6', 82), ('b8c6', 18)),
    ('e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4', 'c5d4', 'f3d4', 'g8f6'): (('b1c3', 90), ('f2f3', 10)),
    ('e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4', 'c5d4', 'f3d4', 'g8f6', 'b1c3'): (('a7a6', 68), ('g7g6', 20), ('e7e6', 12)),
    ('e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4', 'c5d4', 'f3d4', 'g8f6', 'b1c3', 'a7a6'): (('c1e3', 62), ('f2f3', 38)),

    # French Defence, Classical structure
    ('e2e4', 'e7e6'): (('d2d4', 84), ('g1f3', 16)),
    ('e2e4', 'e7e6', 'd2d4'): (('d7d5', 88), ('g8f6', 12)),
    ('e2e4', 'e7e6', 'd2d4', 'd7d5'): (('b1c3', 66), ('e4e5', 34)),
    ('e2e4', 'e7e6', 'd2d4', 'd7d5', 'b1c3'): (('g8f6', 75), ('f8b4', 25)),
    ('e2e4', 'e7e6', 'd2d4', 'd7d5', 'b1c3', 'g8f6'): (('e4e5', 78), ('e4d5', 22)),
    ('e2e4', 'e7e6', 'd2d4', 'd7d5', 'b1c3', 'g8f6', 'e4e5'): (('f6d7', 82), ('f6g8', 18)),

    # Caro-Kann Defence, Classical Variation
    ('e2e4', 'c7c6'): (('d2d4', 86), ('g1f3', 14)),
    ('e2e4', 'c7c6', 'd2d4'): (('d7d5', 90), ('g8f6', 10)),
    ('e2e4', 'c7c6', 'd2d4', 'd7d5'): (('b1c3', 76), ('b1d2', 24)),
    ('e2e4', 'c7c6', 'd2d4', 'd7d5', 'b1c3'): (('d5e4', 86), ('g8f6', 14)),
    ('e2e4', 'c7c6', 'd2d4', 'd7d5', 'b1c3', 'd5e4'): (('c3e4', 94), ('c3d5', 6)),
    ('e2e4', 'c7c6', 'd2d4', 'd7d5', 'b1c3', 'd5e4', 'c3e4'): (('c8f5', 74), ('g8f6', 26)),

    # Scandinavian and Pirc Defences
    ('e2e4', 'd7d5'): (('e4d5', 86), ('b1c3', 14)),
    ('e2e4', 'd7d5', 'e4d5'): (('d8d5', 72), ('g8f6', 28)),
    ('e2e4', 'd7d5', 'e4d5', 'd8d5'): (('b1c3', 88), ('g1f3', 12)),
    ('e2e4', 'd7d6'): (('d2d4', 76), ('g1f3', 24)),
    ('e2e4', 'd7d6', 'd2d4'): (('g8f6', 76), ('g7g6', 24)),
    ('e2e4', 'd7d6', 'd2d4', 'g8f6'): (('b1c3', 82), ('f2f3', 18)),
    ('e2e4', 'd7d6', 'd2d4', 'g8f6', 'b1c3'): (('g7g6', 82), ('e7e5', 18)),

    # Queen's Gambit Declined
    ('d2d4', 'd7d5'): (('c2c4', 78), ('g1f3', 22)),
    ('d2d4', 'd7d5', 'c2c4'): (('e7e6', 64), ('c7c6', 22), ('d5c4', 14)),
    ('d2d4', 'd7d5', 'c2c4', 'e7e6'): (('b1c3', 66), ('g1f3', 34)),
    ('d2d4', 'd7d5', 'c2c4', 'e7e6', 'b1c3'): (('g8f6', 78), ('f8e7', 22)),
    ('d2d4', 'd7d5', 'c2c4', 'e7e6', 'b1c3', 'g8f6'): (('c1g5', 52), ('g1f3', 48)),
    ('d2d4', 'd7d5', 'c2c4', 'e7e6', 'b1c3', 'g8f6', 'g1f3'): (('f8e7', 66), ('f8b4', 34)),
    ('d2d4', 'd7d5', 'c2c4', 'e7e6', 'b1c3', 'g8f6', 'g1f3', 'f8e7'): (('e2e3', 82), ('c1f4', 18)),
    ('d2d4', 'd7d5', 'c2c4', 'e7e6', 'b1c3', 'g8f6', 'g1f3', 'f8e7', 'e2e3'): (('e8g8', 86), ('b8d7', 14)),
    ('d2d4', 'd7d5', 'c2c4', 'c7c6'): (('b1c3', 74), ('g1f3', 26)),
    ('d2d4', 'd7d5', 'c2c4', 'c7c6', 'b1c3'): (('g8f6', 78), ('e7e6', 22)),

    # Indian Defence structure
    ('d2d4', 'g8f6'): (('c2c4', 76), ('g1f3', 24)),
    ('d2d4', 'g8f6', 'c2c4'): (('g7g6', 52), ('e7e6', 30), ('c7c5', 18)),
    ('d2d4', 'g8f6', 'c2c4', 'g7g6'): (('b1c3', 74), ('g1f3', 26)),
    ('d2d4', 'g8f6', 'c2c4', 'g7g6', 'b1c3'): (('f8g7', 85), ('d7d5', 15)),
    ('d2d4', 'g8f6', 'c2c4', 'g7g6', 'b1c3', 'f8g7'): (('e2e4', 78), ('g1f3', 22)),
    ('d2d4', 'g8f6', 'c2c4', 'g7g6', 'b1c3', 'f8g7', 'e2e4'): (('d7d6', 54), ('e8g8', 32), ('d7d5', 14)),

    # English Opening, Reversed Sicilian
    ('c2c4', 'e7e5'): (('b1c3', 76), ('g2g3', 24)),
    ('c2c4', 'e7e5', 'b1c3'): (('g8f6', 78), ('b8c6', 22)),
    ('c2c4', 'e7e5', 'b1c3', 'g8f6'): (('g2g3', 72), ('g1f3', 28)),
    ('c2c4', 'e7e5', 'b1c3', 'g8f6', 'g2g3'): (('d7d5', 68), ('c7c6', 32)),
    ('c2c4', 'e7e5', 'b1c3', 'g8f6', 'g2g3', 'd7d5'): (('c4d5', 70), ('c3d5', 30)),
    ('c2c4', 'e7e5', 'b1c3', 'g8f6', 'g2g3', 'd7d5', 'c4d5'): (('f6d5', 88), ('c7c6', 12)),

    # Italian Game, Vienna Game, and King's Gambit
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4'): (('f8c5', 66), ('g8f6', 34)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'f8c5'): (('c2c3', 62), ('d2d3', 38)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'f8c5', 'c2c3'): (('g8f6', 78), ('d7d6', 22)),
    ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'f8c5', 'c2c3', 'g8f6'): (('d2d3', 82), ('e1g1', 18)),
    ('e2e4', 'e7e5', 'b1c3'): (('g8f6', 65), ('b8c6', 35)),
    ('e2e4', 'e7e5', 'b1c3', 'g8f6'): (('f2f4', 72), ('g1f3', 28)),
    ('e2e4', 'e7e5', 'b1c3', 'g8f6', 'f2f4'): (('d7d5', 68), ('e5f4', 32)),
    ('e2e4', 'e7e5', 'f2f4'): (('e5f4', 84), ('d7d5', 16)),
    ('e2e4', 'e7e5', 'f2f4', 'e5f4'): (('g1f3', 88), ('f1c4', 12)),
    ('e2e4', 'e7e5', 'f2f4', 'e5f4', 'g1f3'): (('g7g5', 48), ('g8f6', 38), ('d7d5', 14)),

    # Sicilian Defence: Classical, Kan, and Alapin systems
    ('e2e4', 'c7c5', 'g1f3', 'b8c6'): (('d2d4', 76), ('f1b5', 24)),
    ('e2e4', 'c7c5', 'g1f3', 'b8c6', 'd2d4'): (('c5d4', 90), ('e7e6', 10)),
    ('e2e4', 'c7c5', 'g1f3', 'b8c6', 'd2d4', 'c5d4'): (('f3d4', 92), ('d1d4', 8)),
    ('e2e4', 'c7c5', 'g1f3', 'b8c6', 'd2d4', 'c5d4', 'f3d4'): (('g8f6', 74), ('e7e6', 26)),
    ('e2e4', 'c7c5', 'c2c3'): (('d7d5', 68), ('g8f6', 32)),
    ('e2e4', 'c7c5', 'c2c3', 'd7d5'): (('e4d5', 86), ('e4e5', 14)),
    ('e2e4', 'c7c5', 'c2c3', 'd7d5', 'e4d5'): (('d8d5', 72), ('g8f6', 28)),

    # Nimzo-Indian and Dutch Defences
    ('d2d4', 'g8f6', 'c2c4', 'e7e6'): (('b1c3', 76), ('g1f3', 24)),
    ('d2d4', 'g8f6', 'c2c4', 'e7e6', 'b1c3'): (('f8b4', 74), ('d7d5', 26)),
    ('d2d4', 'g8f6', 'c2c4', 'e7e6', 'b1c3', 'f8b4'): (('d1c2', 62), ('e2e3', 38)),
    ('d2d4', 'g8f6', 'c2c4', 'e7e6', 'b1c3', 'f8b4', 'd1c2'): (('e8g8', 72), ('d7d5', 28)),
    ('d2d4', 'f7f5'): (('c2c4', 66), ('g1f3', 22), ('g2g3', 12)),
    ('d2d4', 'f7f5', 'c2c4'): (('g8f6', 76), ('e7e6', 24)),
    ('d2d4', 'f7f5', 'c2c4', 'g8f6'): (('g2g3', 72), ('b1c3', 28)),
    ('d2d4', 'f7f5', 'c2c4', 'g8f6', 'g2g3'): (('e7e6', 74), ('g7g6', 26)),

    # London System and further English development
    ('d2d4', 'd7d5', 'c1f4'): (('g8f6', 68), ('e7e6', 32)),
    ('d2d4', 'd7d5', 'c1f4', 'g8f6'): (('e2e3', 78), ('g1f3', 22)),
    ('d2d4', 'd7d5', 'c1f4', 'g8f6', 'e2e3'): (('e7e6', 76), ('c7c5', 24)),
    ('c2c4', 'g8f6'): (('g1f3', 52), ('b1c3', 30), ('g2g3', 18)),
    ('c2c4', 'g8f6', 'g1f3'): (('c7c5', 44), ('e7e6', 36), ('g7g6', 20)),
    ('c2c4', 'g8f6', 'g1f3', 'c7c5'): (('b1c3', 72), ('g2g3', 28)),
    ('c2c4', 'g8f6', 'g1f3', 'c7c5', 'b1c3'): (('b8c6', 70), ('e7e6', 30)),
}


# Representative main lines for the broader opening families. They are folded
# into OPENING_BOOK below, retaining the existing hand-tuned weights whenever a
# reply already exists while extending the book deeper into each variation.
OPENING_VARIATION_LINES = {
    'Ruy Lopez: Berlin Defense': 'e2e4 e7e5 g1f3 b8c6 f1b5 g8f6 e1g1 f6e4 f1e1',
    'Ruy Lopez: Marshall Attack': 'e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5 a4b3 e8g8 c2c3 d7d5',
    'Ruy Lopez: Exchange Variation': 'e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5c6 d7c6 e1g1',
    'Italian Game: Evans Gambit': 'e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 b2b4 c5b4 c2c3 b4a5 d2d4',
    'Italian Game: Two Knights Defense': 'e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 f3g5 d7d5 e4d5 c6a5',
    'Scotch Game': 'e2e4 e7e5 g1f3 b8c6 d2d4 e5d4 f3d4 g8f6',
    'Scotch Gambit': 'e2e4 e7e5 g1f3 b8c6 d2d4 e5d4 f1c4',
    'Four Knights Game': 'e2e4 e7e5 g1f3 b8c6 b1c3 g8f6',
    'Ponziani Opening': 'e2e4 e7e5 g1f3 b8c6 c2c3',
    'Kings Gambit Accepted': 'e2e4 e7e5 f2f4 e5f4 g1f3 g7g5 h2h4 g5g4',
    'Kings Gambit Declined': 'e2e4 e7e5 f2f4 f8c5',
    'Kings Gambit: Fischer Defense': 'e2e4 e7e5 f2f4 d7d6',
    'Sicilian: Najdorf': 'e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6',
    'Sicilian: Dragon': 'e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6',
    'Sicilian: Accelerated Dragon': 'e2e4 c7c5 g1f3 b8c6 d2d4 c5d4 f3d4 g7g6',
    'Sicilian: Sveshnikov': 'e2e4 c7c5 g1f3 b8c6 d2d4 c5d4 f3d4 g8f6 b1c3 e7e5',
    'Sicilian: Taimanov': 'e2e4 c7c5 g1f3 e7e6 d2d4 c5d4 f3d4 b8c6',
    'Sicilian: Kan': 'e2e4 c7c5 g1f3 e7e6 d2d4 c5d4 f3d4 a7a6',
    'Sicilian: Rossolimo': 'e2e4 c7c5 g1f3 b8c6 f1b5',
    'French: Winawer': 'e2e4 e7e6 d2d4 d7d5 b1c3 f8b4',
    'French: Advance Variation': 'e2e4 e7e6 d2d4 d7d5 e4e5',
    'French: Tarrasch Variation': 'e2e4 e7e6 d2d4 d7d5 b1d2',
    'French: Exchange Variation': 'e2e4 e7e6 d2d4 d7d5 e4d5 e6d5',
    'Caro-Kann: Advance Variation': 'e2e4 c7c6 d2d4 d7d5 e4e5',
    'Caro-Kann: Panov Attack': 'e2e4 c7c6 d2d4 d7d5 e4d5 c6d5 c2c4',
    'Caro-Kann: Two Knights Variation': 'e2e4 c7c6 d2d4 d7d5 b1c3 g8f6',
    'Alekhine Defense': 'e2e4 g8f6 e4e5 f6d5 d2d4 d7d6',
    'Modern Defense': 'e2e4 g7g6 d2d4 f8g7 b1c3 d7d6',
    'Queens Gambit Accepted': 'd2d4 d7d5 c2c4 d5c4 g1f3',
    'Slav Defense': 'd2d4 d7d5 c2c4 c7c6 b1c3 g8f6',
    'Semi-Slav Defense': 'd2d4 d7d5 c2c4 c7c6 b1c3 g8f6 g1f3 e7e6',
    'Kings Indian: Classical Variation': 'd2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4 d7d6 g1f3 e8g8 f1e2 e7e5',
    'Kings Indian: Samisch Variation': 'd2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4 d7d6 f2f3',
    'Kings Indian: Fianchetto Variation': 'd2d4 g8f6 c2c4 g7g6 b1c3 f8g7 g2g3',
    'Grunfeld Defense': 'd2d4 g8f6 c2c4 g7g6 b1c3 d7d5',
    'Benoni Defense': 'd2d4 g8f6 c2c4 c7c5 d4d5 e7e6',
    'Benko Gambit': 'd2d4 g8f6 c2c4 c7c5 d4d5 b7b5',
    'Nimzo-Indian: Classical Variation': 'd2d4 g8f6 c2c4 e7e6 b1c3 f8b4 d1c2',
    'Nimzo-Indian: Rubinstein Variation': 'd2d4 g8f6 c2c4 e7e6 b1c3 f8b4 e2e3',
    'Nimzo-Indian: Samisch Variation': 'd2d4 g8f6 c2c4 e7e6 b1c3 f8b4 a2a3',
    'Catalan Opening': 'd2d4 g8f6 c2c4 e7e6 g2g3 d7d5 f1g2',
    'Trompowsky Attack': 'd2d4 g8f6 c1g5',
    'London System': 'd2d4 d7d5 c1f4 g8f6 e2e3 e7e6 g1f3',
    'Reti Opening': 'g1f3 d7d5 c2c4',
    'English: Symmetrical Variation': 'c2c4 c7c5 b1c3 b8c6 g2g3',
    'English: Agincourt Defense': 'c2c4 g8f6 b1c3 d7d5',
    'English: Botvinnik Setup': 'c2c4 e7e5 b1c3 g8f6 g2g3 d7d5 c4d5 f6d5 f1g2',
    'Bird Opening': 'f2f4 d7d5 g1f3',
    'Colle System': 'd2d4 d7d5 g1f3 g8f6 e2e3 e7e6 f1d3',
    'Stonewall Attack': 'd2d4 d7d5 e2e3 g8f6 f2f4',
}


def _add_opening_variation(line, weight=18):
    """Extend the book without overriding hand-tuned replies already present."""
    moves = tuple(line.split())
    for index, move in enumerate(moves):
        history = moves[:index]
        choices = list(OPENING_BOOK.get(history, ()))
        if not any(existing_move == move for existing_move, _ in choices):
            choices.append((move, weight))
            OPENING_BOOK[history] = tuple(choices)


for _variation_line in OPENING_VARIATION_LINES.values():
    _add_opening_variation(_variation_line)


class ChessAI:
    """Picks a move for the computer player, using a strategy chosen by difficulty."""

    STOCKFISH_MOVE_TIME_MS = 3000

    def __init__(self, difficulty="medium", ai_color=Color.BLACK):
        self.difficulty = difficulty
        self.depth = AI_DIFFICULTY_DEPTHS.get(difficulty, 2)
        self.ai_color = ai_color

    def get_best_move(self, board):
        """Return the AI's chosen move ((from), (to)), or None if it has none."""
        if self.difficulty == "impossible":
            return self._get_stockfish_move(board)

        book_move = self._get_opening_book_move(board)
        if book_move:
            return book_move
        if self.difficulty == "easy":
            return self._get_random_move(board)
        if self.difficulty == "hard":
            return self._get_sunfish_move(board)
        return self._get_minimax_move(board)

    @staticmethod
    def stockfish_path():
        """Find Stockfish from an explicit path, PATH, or common local installs."""
        candidates = [
            os.environ.get('STOCKFISH_PATH'),
            shutil.which('stockfish'),
            '/opt/homebrew/bin/stockfish',
            '/usr/local/bin/stockfish',
        ]
        return next((path for path in candidates if path and os.path.isfile(path) and os.access(path, os.X_OK)), None)

    @classmethod
    def stockfish_available(cls):
        """Return whether a runnable Stockfish executable is available to the game."""
        return cls.stockfish_path() is not None

    def _board_to_fen(self, board):
        """Serialize the current board to FEN for Stockfish's UCI position command."""
        piece_chars = {
            PieceType.PAWN: 'p', PieceType.KNIGHT: 'n', PieceType.BISHOP: 'b',
            PieceType.ROOK: 'r', PieceType.QUEEN: 'q', PieceType.KING: 'k',
        }
        rows = []
        for row in range(8):
            empty, fen_row = 0, ''
            for col in range(8):
                piece = board.get_piece(row, col)
                if not piece:
                    empty += 1
                    continue
                if empty:
                    fen_row += str(empty)
                    empty = 0
                char = piece_chars[piece.piece_type]
                fen_row += char.upper() if piece.color == Color.WHITE else char
            rows.append(fen_row + (str(empty) if empty else ''))

        def castle_ready(color, king_row, rook_col):
            king = board.get_piece(king_row, 4)
            rook = board.get_piece(king_row, rook_col)
            return (king and rook and king.color == color and rook.color == color
                    and king.piece_type == PieceType.KING and rook.piece_type == PieceType.ROOK
                    and not king.has_moved and not rook.has_moved)

        castling = ''
        castling += 'K' if castle_ready(Color.WHITE, 7, 7) else ''
        castling += 'Q' if castle_ready(Color.WHITE, 7, 0) else ''
        castling += 'k' if castle_ready(Color.BLACK, 0, 7) else ''
        castling += 'q' if castle_ready(Color.BLACK, 0, 0) else ''
        ep = '-'
        if board.en_passant_target:
            row, col = board.en_passant_target
            ep = f'{FILES[col]}{RANKS[row]}'
        turn = 'w' if board.current_turn == Color.WHITE else 'b'
        return f"{'/'.join(rows)} {turn} {castling or '-'} {ep} 0 {max(1, len(board.move_history) // 2 + 1)}"

    def _get_stockfish_move(self, board):
        """Ask local Stockfish for a strong move within a predictable time budget."""
        engine_path = self.stockfish_path()
        if not engine_path:
            return self._get_sunfish_move(board)

        try:
            process = subprocess.Popen(
                [engine_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            commands = (f"uci\nisready\nposition fen {self._board_to_fen(board)}\n"
                        f"go movetime {self.STOCKFISH_MOVE_TIME_MS}\n")
            process.stdin.write(commands.encode())
            process.stdin.flush()

            # Do not send `quit` until Stockfish has completed its requested
            # search. Sending it in the same command batch interrupts `go` and
            # can produce a very shallow, uncharacteristically weak move.
            deadline = time.monotonic() + self.STOCKFISH_MOVE_TIME_MS / 1000 + 3
            notation = None
            pending = b''
            while time.monotonic() < deadline:
                ready, _, _ = select.select([process.stdout], [], [], deadline - time.monotonic())
                if not ready:
                    break
                pending += os.read(process.stdout.fileno(), 4096)
                lines = pending.split(b'\n')
                pending = lines.pop()
                for raw_line in lines:
                    line = raw_line.decode(errors='replace').strip()
                    if line.startswith('bestmove '):
                        notation = line.split()[1]
                        break
                if notation:
                    break
            process.stdin.write(b'quit\n')
            process.stdin.flush()
            process.wait(timeout=2)
            if not notation:
                return self._get_sunfish_move(board)
            if notation == '(none)' or len(notation) < 4:
                return None
            move = ((RANKS.index(notation[1]), FILES.index(notation[0])),
                    (RANKS.index(notation[3]), FILES.index(notation[2])))
            if move not in board.get_all_valid_moves():
                return self._get_sunfish_move(board)
            promotion_types = {
                'q': PieceType.QUEEN, 'r': PieceType.ROOK,
                'b': PieceType.BISHOP, 'n': PieceType.KNIGHT,
            }
            return (*move, promotion_types[notation[4]]) if len(notation) > 4 and notation[4] in promotion_types else move
        except (OSError, subprocess.SubprocessError, ValueError):
            if 'process' in locals() and process.poll() is None:
                process.kill()
            return self._get_sunfish_move(board)

    def get_stockfish_lines(self, board, line_count=3, time_ms=1200):
        """Return Stockfish's top principal variations for a position.

        Each result contains a rank, a human-readable score, and UCI moves. The
        caller owns threading so the Pygame event loop is never blocked.
        """
        engine_path = self.stockfish_path()
        if not engine_path:
            return []

        process = None
        try:
            process = subprocess.Popen(
                [engine_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            commands = (
                f"uci\nsetoption name MultiPV value {line_count}\nisready\n"
                f"position fen {self._board_to_fen(board)}\ngo movetime {time_ms}\n"
            )
            process.stdin.write(commands.encode())
            process.stdin.flush()

            deadline = time.monotonic() + time_ms / 1000 + 3
            pending, variations = b'', {}
            while time.monotonic() < deadline:
                ready, _, _ = select.select([process.stdout], [], [], deadline - time.monotonic())
                if not ready:
                    break
                pending += os.read(process.stdout.fileno(), 4096)
                lines = pending.split(b'\n')
                pending = lines.pop()
                for raw_line in lines:
                    fields = raw_line.decode(errors='replace').split()
                    if fields[:1] == ['bestmove']:
                        deadline = 0
                        break
                    if 'multipv' not in fields or 'score' not in fields or 'pv' not in fields:
                        continue
                    rank = int(fields[fields.index('multipv') + 1])
                    score_type = fields[fields.index('score') + 1]
                    score_value = int(fields[fields.index('score') + 2])
                    pv = fields[fields.index('pv') + 1:]
                    # UCI reports scores from the side-to-move perspective.  Analysis
                    # is clearer when every line, and the evaluation bar, use White's
                    # perspective consistently.
                    white_factor = 1 if board.current_turn == Color.WHITE else -1
                    white_score = score_value * white_factor
                    if score_type == 'mate':
                        score = f"M{white_score}"
                        evaluation = {'white_mate': white_score}
                    else:
                        score = f"{white_score / 100:+.2f}"
                        evaluation = {'white_score_cp': white_score}
                    variations[rank] = {
                        'rank': rank, 'score': score, 'pv': pv[:8], **evaluation,
                    }
                if deadline == 0:
                    break
            process.stdin.write(b'quit\n')
            process.stdin.flush()
            process.wait(timeout=2)
            return [variations[rank] for rank in sorted(variations)[:line_count]]
        except (OSError, subprocess.SubprocessError, ValueError, IndexError):
            return []
        finally:
            if process and process.poll() is None:
                process.kill()

    @staticmethod
    def _move_to_book_key(move):
        """Convert a recorded move into compact coordinate notation, e.g. e2e4."""
        from_row, from_col = move.from_position
        to_row, to_col = move.to_position
        return f"{FILES[from_col]}{RANKS[from_row]}{FILES[to_col]}{RANKS[to_row]}"

    def _get_opening_book_move(self, board):
        """Return a weighted legal book reply, or None when normal search should take over."""
        history = tuple(self._move_to_book_key(move) for move in board.move_history)
        candidates = OPENING_BOOK.get(history)
        if not candidates:
            return None

        legal_moves = set(board.get_all_valid_moves())
        weighted_moves = []
        weights = []
        for notation, weight in candidates:
            from_col = FILES.index(notation[0])
            from_row = RANKS.index(notation[1])
            to_col = FILES.index(notation[2])
            to_row = RANKS.index(notation[3])
            move = ((from_row, from_col), (to_row, to_col))
            if move in legal_moves:
                weighted_moves.append(move)
                weights.append(weight)

        return random.choices(weighted_moves, weights=weights, k=1)[0] if weighted_moves else None

    def _get_random_move(self, board):
        """Return a random legal move (used for the easy level)."""
        all_moves = board.get_all_valid_moves()
        return random.choice(all_moves) if all_moves else None

    # Letters Sunfish uses for each piece type (uppercase = white).
    _SUNFISH_PIECE_CHARS = {
        PieceType.PAWN: 'P',
        PieceType.KNIGHT: 'N',
        PieceType.BISHOP: 'B',
        PieceType.ROOK: 'R',
        PieceType.QUEEN: 'Q',
        PieceType.KING: 'K',
    }

    @staticmethod
    def _castling_rights(king, queenside_rook, kingside_rook):
        """Return (queenside_ok, kingside_ok) for a color, given its key pieces."""
        def rook_ready(rook):
            return rook and rook.piece_type == PieceType.ROOK and not rook.has_moved

        king_ready = king and not king.has_moved
        return (bool(king_ready and rook_ready(queenside_rook)),
                bool(king_ready and rook_ready(kingside_rook)))

    def _board_to_sunfish_position(self, board):
        """Convert our ChessBoard into a Sunfish Position for the engine to search."""
        # Sunfish stores the board as a 120-char string: 2 padding rows, the 8
        # board rows (each a padding space + 8 squares + newline), then 2 more.
        board_str = "         \n" * 2  # Top padding

        for row in range(8):
            board_str += " "  # Left padding
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece is None:
                    board_str += "."
                else:
                    char = self._SUNFISH_PIECE_CHARS[piece.piece_type]
                    board_str += char if piece.color == Color.WHITE else char.lower()
            board_str += "\n"

        board_str += "         \n" * 2  # Bottom padding

        # Position score from white's perspective (black pieces use a mirrored index).
        score = 0
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    idx = sunfish.board_to_sunfish_index(row, col)
                    char = self._SUNFISH_PIECE_CHARS[piece.piece_type]
                    if piece.color == Color.WHITE:
                        score += sunfish.pst[char][idx]
                    else:
                        score -= sunfish.pst[char][119 - idx]

        # Castling rights as (queenside, kingside) for each color.
        wc = self._castling_rights(board.get_piece(7, 4), board.get_piece(7, 0), board.get_piece(7, 7))
        bc = self._castling_rights(board.get_piece(0, 4), board.get_piece(0, 0), board.get_piece(0, 7))

        # En passant target square (0 if none); king-passant is unused here.
        ep = 0
        if board.en_passant_target:
            ep_row, ep_col = board.en_passant_target
            ep = sunfish.board_to_sunfish_index(ep_row, ep_col)
        kp = 0

        pos = sunfish.Position(board_str, score, wc, bc, ep, kp)

        # Sunfish always plays as white (uppercase), so if it's black's turn,
        # we need to rotate the position
        if board.current_turn == Color.BLACK:
            pos = pos.rotate()

        return pos

    def _get_sunfish_move(self, board):
        """Return the best move ((from), (to)) from the Sunfish engine (hard level)."""
        pos = self._board_to_sunfish_position(board)

        searcher = sunfish.Searcher()

        # Search until the engine has thought for about one second.
        start_time = time.time()
        think_time = 1.0

        best_move = None
        for depth, gamma, score, move in searcher.search([pos]):
            if score >= gamma and move:
                best_move = move
            if time.time() - start_time > think_time:
                break

        if not best_move:
            # Fallback to random move if Sunfish fails
            return self._get_random_move(board)

        # Convert Sunfish move back to our format
        i, j, prom = best_move

        # If it was black's turn, the position was rotated, so we need to un-rotate the move
        if board.current_turn == Color.BLACK:
            i = 119 - i
            j = 119 - j

        from_row, from_col = sunfish.sunfish_index_to_board(i)
        to_row, to_col = sunfish.sunfish_index_to_board(j)

        return ((from_row, from_col), (to_row, to_col))

    def _get_minimax_move(self, board):
        """Return the best move ((from), (to)) from a minimax search (medium level)."""
        best_move = None
        best_value = float('-inf')

        for from_pos, to_pos in board.get_all_valid_moves():
            # Try the move, score the resulting position, then undo it.
            undo_info = board.make_move_with_undo(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
            value = self._minimax(board, self.depth - 1, float('-inf'), float('inf'), False)
            board.unmake_move(undo_info)

            if value > best_value:
                best_value = value
                best_move = (from_pos, to_pos)
        return best_move

    def _minimax(self, board, depth, alpha, beta, maximizing):
        """
        Score a position with minimax and alpha-beta pruning.

        Args:
            depth: remaining plies to search
            alpha, beta: current pruning bounds
            maximizing: True when it is the AI's turn to move

        Returns:
            The position's evaluation score.
        """
        if depth == 0 or board.is_checkmate() or board.is_stalemate():
            return self._evaluate_board(board)

        all_moves = board.get_all_valid_moves()

        if maximizing:
            max_eval = float('-inf')
            for from_pos, to_pos in all_moves:
                undo_info = board.make_move_with_undo(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                eval_score = self._minimax(board, depth - 1, alpha, beta, False)
                board.unmake_move(undo_info)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for from_pos, to_pos in all_moves:
                undo_info = board.make_move_with_undo(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                eval_score = self._minimax(board, depth - 1, alpha, beta, True)
                board.unmake_move(undo_info)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval

    def _evaluate_board(self, board):
        """Score the position from the AI's point of view (higher is better for it)."""
        if board.is_checkmate():
            # Checkmate on the AI's turn means the AI is mated (lost).
            return float('-inf') if board.current_turn == self.ai_color else float('inf')

        if board.is_stalemate():
            return 0

        # Otherwise, sum material: AI's pieces count positively, the opponent's negatively.
        score = 0
        for r in range(8):
            for c in range(8):
                piece = board.get_piece(r, c)
                if piece:
                    value = PIECE_VALUES[piece.piece_type.value]
                    score += value if piece.color == self.ai_color else -value

        return score
