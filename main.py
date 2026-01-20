import sys
from game import ChessGame

def main():
    try:
        game = ChessGame()
        game.run()
    except Exception as e:
        print(f"Error running chess game: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()