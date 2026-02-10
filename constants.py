# ─── Constants ───────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 900, 700
FPS = 60

# Colors
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
GREEN   = (0, 255, 100)
RED     = (255, 60, 60)
YELLOW  = (255, 220, 50)
CYAN    = (0, 220, 255)
MAGENTA = (255, 50, 200)
ORANGE  = (255, 160, 40)
DARK_BG = (10, 10, 30)
HUD_BG  = (20, 20, 50, 180)

# PiP camera settings
PIP_W, PIP_H = 240, 180
PIP_X, PIP_Y = SCREEN_W - PIP_W - 10, 10

# Ship
SHIP_W, SHIP_H = 50, 35
SHIP_SPEED = 6
SHIP_Y = SCREEN_H - 70

# Bullets
BULLET_SPEED = 10
BURST_DELAY = 80        # ms between burst shots
SHOTGUN_SPREAD = 0.25   # radians spread

# Invaders
INVADER_ROWS = 4
INVADER_COLS = 10
INVADER_W, INVADER_H = 36, 28
INVADER_PAD_X, INVADER_PAD_Y = 14, 12
INVADER_DROP = 20
INVADER_SHOOT_CHANCE = 0.003

# Gesture cooldowns (ms)
SINGLE_SHOT_CD = 350
BURST_CD = 700
SHOTGUN_CD = 1000

# Gesture detection thresholds
FINGER_EXTENDED_THRESHOLD = 0.06  # relative to hand size
