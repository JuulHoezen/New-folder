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

import pygame
import cv2
import mediapipe as mp
import numpy as np
import math
import random
import time
import sys

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


# ─── Hand Gesture Detector ───────────────────────────────────────────────────
class HandGestureDetector:
    """Detects hand gestures using MediaPipe Hands."""

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("ERROR: Cannot open webcam!")
            sys.exit(1)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.hand_x = 0.5          # normalized 0..1 (mirrored)
        self.gesture = "none"      # none | single | burst | shotgun
        self.hand_detected = False
        self.frame_rgb = None      # latest camera frame for PiP
        self.landmarks = None      # latest landmarks for drawing

    def _is_finger_extended(self, lm, tip_id, pip_id, mcp_id):
        """Check if a finger is extended by comparing tip-to-mcp vs pip-to-mcp distances."""
        tip = lm[tip_id]
        pip_ = lm[pip_id]
        mcp = lm[mcp_id]
        # Finger is extended if tip is farther from wrist than pip
        tip_dist = math.hypot(tip.x - lm[0].x, tip.y - lm[0].y)
        pip_dist = math.hypot(pip_.x - lm[0].x, pip_.y - lm[0].y)
        return tip_dist > pip_dist

    def _is_thumb_extended(self, lm):
        """Thumb check using x-distance from palm center."""
        thumb_tip = lm[4]
        thumb_ip = lm[3]
        index_mcp = lm[5]
        # Thumb is extended if tip is farther from index mcp than ip is
        tip_dist = math.hypot(thumb_tip.x - index_mcp.x, thumb_tip.y - index_mcp.y)
        ip_dist = math.hypot(thumb_ip.x - index_mcp.x, thumb_ip.y - index_mcp.y)
        return tip_dist > ip_dist

    def _classify_gesture(self, lm):
        """Classify gesture based on which fingers are extended."""
        thumb = self._is_thumb_extended(lm)
        index = self._is_finger_extended(lm, 8, 6, 5)
        middle = self._is_finger_extended(lm, 12, 10, 9)
        ring = self._is_finger_extended(lm, 16, 14, 13)
        pinky = self._is_finger_extended(lm, 20, 18, 17)

        extended = [thumb, index, middle, ring, pinky]
        count = sum(extended)

        # All 5 fingers spread → shotgun
        if count >= 5:
            return "shotgun"

        # Peace sign: index + middle extended, others closed
        if index and middle and not ring and not pinky:
            return "burst"

        # Index only → single shot
        if index and not middle and not ring and not pinky:
            return "single"

        # Fist or other → no action
        return "none"

    def update(self):
        """Read frame from webcam and process hand detection."""
        ret, frame = self.cap.read()
        if not ret:
            return

        # Mirror the frame so movements feel natural
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        self.frame_rgb = rgb
        self.hand_detected = False
        self.gesture = "none"
        self.landmarks = None

        if results.multi_hand_landmarks:
            hand_lm = results.multi_hand_landmarks[0]
            lm = hand_lm.landmark
            self.landmarks = lm
            self.hand_detected = True

            # Hand X position (use wrist landmark 0) — already mirrored
            self.hand_x = lm[0].x

            # Classify gesture
            self.gesture = self._classify_gesture(lm)

    def get_pip_surface(self):
        """Return a pygame surface of the camera feed with hand overlay."""
        if self.frame_rgb is None:
            surf = pygame.Surface((PIP_W, PIP_H))
            surf.fill((30, 30, 30))
            return surf

        # Resize for PiP
        small = cv2.resize(self.frame_rgb, (PIP_W, PIP_H))

        # Draw landmarks if detected
        if self.landmarks is not None:
            h, w = PIP_H, PIP_W
            lm = self.landmarks
            # Draw connections
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),        # thumb
                (0, 5), (5, 6), (6, 7), (7, 8),        # index
                (0, 9), (9, 10), (10, 11), (11, 12),   # middle
                (0, 13), (13, 14), (14, 15), (15, 16), # ring
                (0, 17), (17, 18), (18, 19), (19, 20), # pinky
                (5, 9), (9, 13), (13, 17),              # palm
            ]
            for (a, b) in connections:
                x1, y1 = int(lm[a].x * w), int(lm[a].y * h)
                x2, y2 = int(lm[b].x * w), int(lm[b].y * h)
                cv2.line(small, (x1, y1), (x2, y2), (0, 255, 100), 1)
            for i in range(21):
                cx, cy = int(lm[i].x * w), int(lm[i].y * h)
                cv2.circle(small, (cx, cy), 2, (255, 255, 255), -1)

        # Convert to pygame surface
        surf = pygame.image.frombuffer(small.tobytes(), (PIP_W, PIP_H), "RGB")
        return surf

    def release(self):
        self.cap.release()
        self.hands.close()


# ─── Particle System ─────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, dx=None, dy=None, life=30):
        self.x, self.y = x, y
        self.color = color
        self.dx = dx if dx is not None else random.uniform(-3, 3)
        self.dy = dy if dy is not None else random.uniform(-4, 1)
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.05  # gravity
        self.life -= 1

    def draw(self, surface):
        alpha = max(0, self.life / self.max_life)
        r, g, b = self.color
        color = (int(r * alpha), int(g * alpha), int(b * alpha))
        size = max(1, int(3 * alpha))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)


# ─── Star Background ─────────────────────────────────────────────────────────
class StarField:
    def __init__(self):
        self.stars = []
        for _ in range(120):
            x = random.randint(0, SCREEN_W)
            y = random.randint(0, SCREEN_H)
            speed = random.uniform(0.2, 1.5)
            brightness = random.randint(80, 255)
            size = random.choice([1, 1, 1, 2])
            self.stars.append([x, y, speed, brightness, size])

    def update(self):
        for s in self.stars:
            s[1] += s[2]
            if s[1] > SCREEN_H:
                s[1] = 0
                s[0] = random.randint(0, SCREEN_W)

    def draw(self, surface):
        for x, y, _, b, size in self.stars:
            color = (b, b, b)
            if size == 1:
                surface.set_at((int(x), int(y)), color)
            else:
                pygame.draw.circle(surface, color, (int(x), int(y)), size)


# ─── Bullet ──────────────────────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, dx=0, dy=-BULLET_SPEED, color=CYAN, is_enemy=False):
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy
        self.color = color
        self.is_enemy = is_enemy
        self.alive = True
        self.w, self.h = 4, 10

    def update(self):
        self.x += self.dx
        self.y += self.dy
        if self.y < -20 or self.y > SCREEN_H + 20 or self.x < -20 or self.x > SCREEN_W + 20:
            self.alive = False

    def draw(self, surface):
        # Glow effect
        glow_surf = pygame.Surface((12, 20), pygame.SRCALPHA)
        r, g, b = self.color
        pygame.draw.ellipse(glow_surf, (r, g, b, 60), (0, 0, 12, 20))
        surface.blit(glow_surf, (int(self.x) - 6, int(self.y) - 10))
        # Core
        pygame.draw.rect(surface, self.color, (int(self.x) - 2, int(self.y) - 5, 4, 10))

    def get_rect(self):
        return pygame.Rect(int(self.x) - 2, int(self.y) - 5, self.w, self.h)


# ─── Invader ─────────────────────────────────────────────────────────────────
class Invader:
    COLORS_BY_ROW = [MAGENTA, RED, ORANGE, YELLOW]

    def __init__(self, x, y, row):
        self.x, self.y = x, y
        self.row = row
        self.alive = True
        self.color = self.COLORS_BY_ROW[row % len(self.COLORS_BY_ROW)]
        self.anim_offset = random.uniform(0, math.pi * 2)
        self.hit_flash = 0

    def draw(self, surface, tick):
        if not self.alive:
            return
        # Slight bob animation
        bob = math.sin(tick * 0.05 + self.anim_offset) * 2

        x, y = int(self.x), int(self.y + bob)
        w, h = INVADER_W, INVADER_H
        color = WHITE if self.hit_flash > 0 else self.color

        # Body
        pygame.draw.rect(surface, color, (x - w // 2 + 4, y - h // 2, w - 8, h))
        # Top bumps
        pygame.draw.rect(surface, color, (x - w // 2, y - h // 2 + 4, w, h - 8))
        # Eyes
        eye_color = BLACK if self.hit_flash == 0 else RED
        pygame.draw.rect(surface, eye_color, (x - 7, y - 3, 5, 5))
        pygame.draw.rect(surface, eye_color, (x + 3, y - 3, 5, 5))
        # Legs (alternate based on tick)
        leg_phase = (tick // 20) % 2
        if leg_phase == 0:
            pygame.draw.rect(surface, color, (x - w // 2 - 2, y + h // 2 - 2, 6, 6))
            pygame.draw.rect(surface, color, (x + w // 2 - 4, y + h // 2 - 2, 6, 6))
        else:
            pygame.draw.rect(surface, color, (x - w // 2 + 2, y + h // 2 - 2, 6, 6))
            pygame.draw.rect(surface, color, (x + w // 2 - 8, y + h // 2 - 2, 6, 6))

        if self.hit_flash > 0:
            self.hit_flash -= 1

    def get_rect(self):
        return pygame.Rect(
            int(self.x) - INVADER_W // 2,
            int(self.y) - INVADER_H // 2,
            INVADER_W,
            INVADER_H,
        )


# ─── Player Ship ─────────────────────────────────────────────────────────────
class Ship:
    def __init__(self):
        self.x = SCREEN_W // 2
        self.y = SHIP_Y
        self.target_x = self.x
        self.lives = 3
        self.invincible_until = 0
        self.engine_particles = []

    def set_target(self, normalized_x):
        """Set target x from normalized hand position (0..1)."""
        margin = 30
        self.target_x = margin + normalized_x * (SCREEN_W - 2 * margin)

    def update(self):
        # Smooth movement towards target
        diff = self.target_x - self.x
        self.x += diff * 0.15
        self.x = max(SHIP_W // 2, min(SCREEN_W - SHIP_W // 2, self.x))

        # Engine particles
        if random.random() < 0.6:
            self.engine_particles.append(
                Particle(
                    self.x + random.uniform(-8, 8),
                    self.y + SHIP_H // 2,
                    random.choice([CYAN, (100, 180, 255), WHITE]),
                    dx=random.uniform(-0.5, 0.5),
                    dy=random.uniform(1, 3),
                    life=random.randint(10, 20),
                )
            )

        for p in self.engine_particles:
            p.update()
        self.engine_particles = [p for p in self.engine_particles if p.life > 0]

    def draw(self, surface, tick):
        # Engine particles (behind ship)
        for p in self.engine_particles:
            p.draw(surface)

        # Blinking during invincibility
        now = pygame.time.get_ticks()
        if now < self.invincible_until and (tick // 4) % 2 == 0:
            return

        x, y = int(self.x), int(self.y)

        # Ship body - sleek triangle shape
        points = [
            (x, y - SHIP_H // 2),           # nose
            (x - SHIP_W // 2, y + SHIP_H // 2),   # left wing
            (x + SHIP_W // 2, y + SHIP_H // 2),   # right wing
        ]
        pygame.draw.polygon(surface, CYAN, points)

        # Cockpit
        pygame.draw.polygon(surface, WHITE, [
            (x, y - SHIP_H // 2 + 5),
            (x - 6, y + 4),
            (x + 6, y + 4),
        ])

        # Wing accents
        pygame.draw.line(surface, WHITE, (x - 5, y + 2), (x - SHIP_W // 2 + 2, y + SHIP_H // 2 - 2), 2)
        pygame.draw.line(surface, WHITE, (x + 5, y + 2), (x + SHIP_W // 2 - 2, y + SHIP_H // 2 - 2), 2)

    def get_rect(self):
        return pygame.Rect(
            int(self.x) - SHIP_W // 2,
            int(self.y) - SHIP_H // 2,
            SHIP_W,
            SHIP_H,
        )


# ─── Main Game ───────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Space Invaders 👋 Hand Controlled")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.font_big = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_sm = pygame.font.SysFont("consolas", 14)

        # Hand detector
        self.detector = HandGestureDetector()

        # Game objects
        self.stars = StarField()
        self.ship = Ship()
        self.bullets = []
        self.enemy_bullets = []
        self.particles = []
        self.invaders = []

        # State
        self.score = 0
        self.wave = 0
        self.tick = 0
        self.state = "playing"  # playing | gameover | victory
        self.invader_dir = 1    # 1 = right, -1 = left
        self.invader_speed = 1.0
        self.last_single_shot = 0
        self.last_burst_shot = 0
        self.last_shotgun_shot = 0
        self.burst_queue = []   # (time_to_fire, x, y)

        # Gesture display
        self.gesture_display = "none"
        self.gesture_display_time = 0

        self._spawn_wave()

    def _spawn_wave(self):
        self.wave += 1
        self.invaders.clear()
        self.enemy_bullets.clear()
        self.invader_dir = 1
        self.invader_speed = 1.0 + self.wave * 0.2

        start_x = (SCREEN_W - (INVADER_COLS * (INVADER_W + INVADER_PAD_X))) // 2
        start_y = 60

        for row in range(INVADER_ROWS):
            for col in range(INVADER_COLS):
                x = start_x + col * (INVADER_W + INVADER_PAD_X) + INVADER_W // 2
                y = start_y + row * (INVADER_H + INVADER_PAD_Y) + INVADER_H // 2
                self.invaders.append(Invader(x, y, row))

    def _fire_single(self):
        now = pygame.time.get_ticks()
        if now - self.last_single_shot < SINGLE_SHOT_CD:
            return
        self.last_single_shot = now
        self.bullets.append(Bullet(self.ship.x, self.ship.y - SHIP_H // 2, color=CYAN))
        self._set_gesture_display("☝️ SINGLE")

    def _fire_burst(self):
        now = pygame.time.get_ticks()
        if now - self.last_burst_shot < BURST_CD:
            return
        self.last_burst_shot = now
        # Queue 3 shots with delay
        for i in range(3):
            fire_time = now + i * BURST_DELAY
            self.burst_queue.append((fire_time, self.ship.x, self.ship.y - SHIP_H // 2))
        self._set_gesture_display("✌️ BURST x3")

    def _fire_shotgun(self):
        now = pygame.time.get_ticks()
        if now - self.last_shotgun_shot < SHOTGUN_CD:
            return
        self.last_shotgun_shot = now
        # Fan of 7 bullets
        base_angle = -math.pi / 2  # straight up
        num_pellets = 7
        for i in range(num_pellets):
            angle = base_angle + SHOTGUN_SPREAD * (i - num_pellets // 2) / (num_pellets // 2)
            dx = math.cos(angle) * BULLET_SPEED
            dy = math.sin(angle) * BULLET_SPEED
            self.bullets.append(
                Bullet(self.ship.x, self.ship.y - SHIP_H // 2, dx=dx, dy=dy, color=YELLOW)
            )
        self._set_gesture_display("🖐️ SHOTGUN")

    def _set_gesture_display(self, text):
        self.gesture_display = text
        self.gesture_display_time = pygame.time.get_ticks()

    def _process_burst_queue(self):
        now = pygame.time.get_ticks()
        remaining = []
        for fire_time, x, y in self.burst_queue:
            if now >= fire_time:
                self.bullets.append(Bullet(x, y, color=GREEN))
            else:
                remaining.append((fire_time, x, y))
        self.burst_queue = remaining

    def _invader_shooting(self):
        alive = [inv for inv in self.invaders if inv.alive]
        for inv in alive:
            if random.random() < INVADER_SHOOT_CHANCE:
                self.enemy_bullets.append(
                    Bullet(inv.x, inv.y + INVADER_H // 2, dy=4, color=RED, is_enemy=True)
                )

    def _move_invaders(self):
        alive = [inv for inv in self.invaders if inv.alive]
        if not alive:
            return

        # Check edges
        hit_edge = False
        for inv in alive:
            if inv.x + INVADER_W // 2 >= SCREEN_W - 10 and self.invader_dir > 0:
                hit_edge = True
                break
            if inv.x - INVADER_W // 2 <= 10 and self.invader_dir < 0:
                hit_edge = True
                break

        if hit_edge:
            self.invader_dir *= -1
            for inv in alive:
                inv.y += INVADER_DROP

        for inv in alive:
            inv.x += self.invader_speed * self.invader_dir

        # Check if invaders reached the ship
        for inv in alive:
            if inv.y + INVADER_H // 2 >= SHIP_Y - SHIP_H:
                self.state = "gameover"

    def _check_collisions(self):
        ship_rect = self.ship.get_rect()
        now = pygame.time.get_ticks()

        # Player bullets vs invaders
        for bullet in self.bullets:
            if not bullet.alive or bullet.is_enemy:
                continue
            brect = bullet.get_rect()
            for inv in self.invaders:
                if not inv.alive:
                    continue
                if brect.colliderect(inv.get_rect()):
                    bullet.alive = False
                    inv.alive = False
                    self.score += 10 * (INVADER_ROWS - inv.row)
                    # Explosion particles
                    for _ in range(15):
                        self.particles.append(
                            Particle(inv.x, inv.y, inv.color, life=random.randint(15, 35))
                        )
                    break

        # Enemy bullets vs ship
        if now >= self.ship.invincible_until:
            for bullet in self.enemy_bullets:
                if not bullet.alive:
                    continue
                if bullet.get_rect().colliderect(ship_rect):
                    bullet.alive = False
                    self.ship.lives -= 1
                    self.ship.invincible_until = now + 2000
                    # Hit particles
                    for _ in range(20):
                        self.particles.append(
                            Particle(self.ship.x, self.ship.y, RED, life=random.randint(15, 30))
                        )
                    if self.ship.lives <= 0:
                        self.state = "gameover"
                    break

    def _check_wave_clear(self):
        alive = [inv for inv in self.invaders if inv.alive]
        if not alive and self.state == "playing":
            self._spawn_wave()
            # Speed up!
            self.invader_speed = min(4.0, self.invader_speed + 0.3)

    def _draw_hud(self):
        # Score
        score_text = self.font.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_text, (15, 10))

        # Wave
        wave_text = self.font.render(f"WAVE: {self.wave}", True, YELLOW)
        self.screen.blit(wave_text, (15, 35))

        # Lives
        lives_text = self.font.render(f"LIVES: ", True, WHITE)
        self.screen.blit(lives_text, (15, 60))
        for i in range(self.ship.lives):
            lx = 100 + i * 25
            points = [(lx, 62), (lx - 8, 78), (lx + 8, 78)]
            pygame.draw.polygon(self.screen, CYAN, points)

        # Gesture indicator
        now = pygame.time.get_ticks()
        if now - self.gesture_display_time < 800:
            alpha = max(0, 1.0 - (now - self.gesture_display_time) / 800)
            gesture_text = self.font.render(self.gesture_display, True,
                                            (int(255 * alpha), int(255 * alpha), int(50 * alpha)))
            text_rect = gesture_text.get_rect(center=(SCREEN_W // 2, SHIP_Y + 40))
            self.screen.blit(gesture_text, text_rect)

        # Hand status
        if self.detector.hand_detected:
            status_color = GREEN
            status_text = "HAND DETECTED"
        else:
            status_color = RED
            status_text = "NO HAND - SHOW YOUR HAND"

        status_surf = self.font_sm.render(status_text, True, status_color)
        self.screen.blit(status_surf, (PIP_X, PIP_Y + PIP_H + 5))

        # Current gesture name
        gesture_names = {
            "none": "✊ IDLE",
            "single": "☝️ SINGLE",
            "burst": "✌️ BURST",
            "shotgun": "🖐️ SHOTGUN",
        }
        gname = gesture_names.get(self.detector.gesture, "???")
        gsurf = self.font_sm.render(f"Gesture: {gname}", True, WHITE)
        self.screen.blit(gsurf, (PIP_X, PIP_Y + PIP_H + 22))

    def _draw_pip(self):
        """Draw picture-in-picture camera feed."""
        pip_surf = self.detector.get_pip_surface()
        # Border
        pygame.draw.rect(self.screen, WHITE, (PIP_X - 2, PIP_Y - 2, PIP_W + 4, PIP_H + 4), 2)
        self.screen.blit(pip_surf, (PIP_X, PIP_Y))

    def _draw_gameover(self):
        # Darken
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        go_text = self.font_big.render("GAME OVER", True, RED)
        rect = go_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 30))
        self.screen.blit(go_text, rect)

        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        rect2 = score_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20))
        self.screen.blit(score_text, rect2)

        restart_text = self.font.render("Press SPACE or show ✊ fist to restart", True, YELLOW)
        rect3 = restart_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 60))
        self.screen.blit(restart_text, rect3)

    def _draw_controls_help(self):
        """Small help text at bottom."""
        help_lines = [
            "☝️ Index=Shot  ✌️ Peace=Burst  🖐️ Spread=Shotgun  Hand position=Move"
        ]
        for i, line in enumerate(help_lines):
            surf = self.font_sm.render(line, True, (120, 120, 150))
            self.screen.blit(surf, (15, SCREEN_H - 25 + i * 16))

    def _restart(self):
        self.score = 0
        self.wave = 0
        self.ship = Ship()
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.particles.clear()
        self.burst_queue.clear()
        self.state = "playing"
        self._spawn_wave()

    def run(self):
        running = True
        while running:
            self.tick += 1

            # ── Events ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_SPACE and self.state == "gameover":
                        self._restart()

            # ── Hand detection ──
            self.detector.update()

            if self.state == "playing":
                # Movement from hand position
                if self.detector.hand_detected:
                    self.ship.set_target(self.detector.hand_x)

                # Shooting from gestures
                gesture = self.detector.gesture
                if gesture == "single":
                    self._fire_single()
                elif gesture == "burst":
                    self._fire_burst()
                elif gesture == "shotgun":
                    self._fire_shotgun()

                # Process burst queue
                self._process_burst_queue()

                # Update game objects
                self.ship.update()
                self._move_invaders()
                self._invader_shooting()

                for b in self.bullets:
                    b.update()
                for b in self.enemy_bullets:
                    b.update()
                for p in self.particles:
                    p.update()

                self.bullets = [b for b in self.bullets if b.alive]
                self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
                self.particles = [p for p in self.particles if p.life > 0]

                self._check_collisions()
                self._check_wave_clear()

            elif self.state == "gameover":
                # Allow restart with fist gesture after a delay
                pass

            # ── Draw ──
            self.stars.update()
            self.screen.fill(DARK_BG)
            self.stars.draw(self.screen)

            if self.state == "playing":
                for inv in self.invaders:
                    inv.draw(self.screen, self.tick)
                for b in self.bullets:
                    b.draw(self.screen)
                for b in self.enemy_bullets:
                    b.draw(self.screen)
                for p in self.particles:
                    p.draw(self.screen)
                self.ship.draw(self.screen, self.tick)

            self._draw_hud()
            self._draw_pip()
            self._draw_controls_help()

            if self.state == "gameover":
                self._draw_gameover()

            pygame.display.flip()
            self.clock.tick(FPS)

        self.detector.release()
        pygame.quit()


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  SPACE INVADERS - Hand Gesture Controlled")
    print("=" * 50)
    print()
    print("  CONTROLS (show to webcam):")
    print("  ─────────────────────────────────")
    print("  Hand position  → Move ship left/right")
    print("  ☝️  Index finger  → Single shot")
    print("  ✌️  Peace sign    → 3-round burst")
    print("  🖐️ Open hand     → Shotgun blast")
    print("  ✊ Closed fist   → Idle")
    print()
    print("  Press ESC to quit")
    print("=" * 50)

    game = Game()
    game.run()