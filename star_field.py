import random
import pygame
from constants import *


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
