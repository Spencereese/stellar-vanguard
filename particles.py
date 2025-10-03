import pygame
import random
from config import *

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = random.randint(-5, 5)
        self.vel_y = random.randint(-5, 5)
        self.life = 30

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.life -= 1
        if self.life <= 0:
            self.kill()