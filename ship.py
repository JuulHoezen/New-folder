import pygame
import random
from constants import *
from particle import Particle


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
