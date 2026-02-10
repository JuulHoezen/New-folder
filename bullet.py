import pygame
import math
from constants import *


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
