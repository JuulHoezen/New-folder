import random
import pygame
from constants import *


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
