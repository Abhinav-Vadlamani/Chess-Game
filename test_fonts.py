#!/usr/bin/env python3
"""
Quick Font Test Script
Tests which system fonts can render Unicode chess symbols
"""

import pygame
import sys

pygame.init()

# Create small window
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Chess Font Test")

# Test fonts
test_fonts = [
    'segoeuisymbol',
    'Segoe UI Symbol',
    'Apple Symbols',
    'AppleSymbols',
    'Symbola',
    'DejaVu Sans',
    'DejaVuSans',
    'Arial Unicode MS',
    'Noto Sans Symbols',
    'FreeSans',
    'Liberation Sans',
    'Helvetica',
    'Arial',
]

# Chess symbols to test
test_symbols = '♔♕♖♗♘♙♚♛♜♝♞♟'

print("=" * 60)
print("TESTING FONTS FOR CHESS SYMBOL SUPPORT")
print("=" * 60)
print()

working_fonts = []
failed_fonts = []

for font_name in test_fonts:
    try:
        font = pygame.font.SysFont(font_name, 60)
        # Try to render a chess piece
        test_surface = font.render('♔', True, (255, 255, 255))
        
        # Check if it actually rendered something (not just a missing glyph box)
        # Missing glyphs often have specific dimensions
        if test_surface.get_width() > 5 and test_surface.get_height() > 5:
            print(f"✅ {font_name:25} - Works!")
            working_fonts.append((font_name, font))
        else:
            print(f"⚠️  {font_name:25} - Loaded but glyphs may be missing")
            failed_fonts.append(font_name)
    except Exception as e:
        print(f"❌ {font_name:25} - Not available")
        failed_fonts.append(font_name)

print()
print("=" * 60)
print(f"RESULTS: {len(working_fonts)} working fonts found")
print("=" * 60)
print()

if working_fonts:
    print("Working fonts:")
    for font_name, _ in working_fonts:
        print(f"  • {font_name}")
    print()
    
    # Visual test
    print("Close the window or press any key to cycle through fonts...")
    print("Press Q or ESC to quit")
    print()
    
    font_index = 0
    running = True
    clock = pygame.time.Clock()
    
    while running and font_index < len(working_fonts):
        font_name, font = working_fonts[font_index]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    # Any other key advances to next font
                    font_index += 1
                    if font_index >= len(working_fonts):
                        running = False
        
        # Clear screen
        screen.fill((49, 46, 43))
        
        # Title
        title_font = pygame.font.Font(None, 36)
        title = title_font.render(f"Font: {font_name} ({font_index + 1}/{len(working_fonts)})", True, (255, 255, 100))
        screen.blit(title, (20, 20))
        
        # Instructions
        inst_font = pygame.font.Font(None, 24)
        inst = inst_font.render("Press any key for next font | Q/ESC to quit", True, (200, 200, 200))
        screen.blit(inst, (20, 60))
        
        # Draw all chess symbols
        y = 120
        spacing = 70
        
        # White pieces
        label = inst_font.render("White pieces:", True, (255, 255, 255))
        screen.blit(label, (20, y))
        x = 200
        for symbol in '♔♕♖♗♘♙':
            text = font.render(symbol, True, (255, 255, 255))
            screen.blit(text, (x, y - 10))
            x += spacing
        
        y += 100
        
        # Black pieces
        label = inst_font.render("Black pieces:", True, (255, 255, 255))
        screen.blit(label, (20, y))
        x = 200
        for symbol in '♚♛♜♝♞♟':
            text = font.render(symbol, True, (0, 0, 0))
            # Draw white background for black pieces
            bg = pygame.Surface((60, 60))
            bg.fill((240, 217, 181))
            screen.blit(bg, (x - 5, y - 15))
            screen.blit(text, (x, y - 10))
            x += spacing
        
        # Show on chessboard colors
        y += 120
        label = inst_font.render("On chess board:", True, (255, 255, 255))
        screen.blit(label, (20, y))
        
        x = 200
        board_colors = [(240, 217, 181), (181, 136, 99)]
        pieces = ['♔', '♕', '♖', '♗', '♘', '♙', '♚', '♛', '♜', '♝', '♞', '♟']
        piece_colors = [(255, 255, 255)] * 6 + [(0, 0, 0)] * 6
        
        for i, (symbol, piece_color) in enumerate(zip(pieces, piece_colors)):
            bg_color = board_colors[i % 2]
            bg = pygame.Surface((60, 60))
            bg.fill(bg_color)
            screen.blit(bg, (x - 5, y - 15))
            
            text = font.render(symbol, True, piece_color)
            screen.blit(text, (x, y - 10))
            
            x += 60
            if x > 700:
                x = 200
                y += 70
        
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()
    
    print()
    print("=" * 60)
    print("RECOMMENDATION:")
    print("=" * 60)
    if working_fonts:
        print(f"Use: '{working_fonts[0][0]}' in your renderer")
        print()
        print("Example code:")
        print(f"  self.piece_font = pygame.font.SysFont('{working_fonts[0][0]}', 60)")
    print("=" * 60)
    
else:
    print("❌ No working fonts found!")
    print()
    print("Your system may not have fonts with chess symbol support.")
    print("You may need to:")
    print("  1. Install a font with Unicode support (DejaVu Sans, Noto Sans)")
    print("  2. Use chess piece images instead of Unicode symbols")
    pygame.quit()

print()
print("Test complete!")