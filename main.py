"""
Space Invaders - Hand Gesture Controlled
==========================================
Controls (via webcam hand tracking):
  👈 Open hand (left side)   → Move ship LEFT
  👉 Open hand (right side)  → Move ship RIGHT
  ☝️  Index finger up         → Single shot
  ✌️  Peace sign (2 fingers)  → 3-round burst
  🖐️ All 5 fingers spread    → Shotgun blast
  ✊ Closed fist              → Idle (no action)

Requires: pygame, mediapipe, opencv-python, numpy
"""

from game import Game
import io
import sys


def main():
    # Handle Unicode output on Windows
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 50)
    print("  SPACE INVADERS - Hand Gesture Controlled")
    print("=" * 50)
    print()
    print("  CONTROLS (show to webcam):")
    print("  " + "-" * 31)
    print("  Hand position  -> Move ship left/right")
    print("  Index finger   -> Single shot")
    print("  Peace sign     -> 3-round burst")
    print("  Open hand      -> Shotgun blast")
    print("  Closed fist    -> Idle")
    print()
    print("  Press ESC to quit")
    print("=" * 50)

    game = Game()
    game.run()


if __name__ == "__main__":
    main()
