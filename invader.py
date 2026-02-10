import pygame
import math
import random
from constants import *


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
