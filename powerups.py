import pygame
from config import SCREEN_HEIGHT, GREEN, YELLOW, RED, BLUE, WHITE, PURPLE, ORANGE, GRAY, MAGENTA, PINK, CYAN, TIME_SLOW_COLOR, LIGHT_BLUE, BROWN

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.type = type
        self.image = pygame.Surface((20, 20))
        if type == 'rapid':
            self.image.fill(GREEN)
        elif type == 'spread':
            self.image.fill(YELLOW)
        elif type == 'laser':
            self.image.fill(RED)
        elif type == 'shield':
            self.image.fill(BLUE)
        elif type == 'ammo':
            self.image.fill(WHITE)
        elif type == 'bomb':
            self.image.fill(PURPLE)
        elif type == 'homing':
            self.image.fill(ORANGE)
        elif type == 'freeze':
            self.image.fill(GRAY)
        elif type == 'invincibility':
            self.image.fill(MAGENTA)
        elif type == 'health':
            self.image.fill(PINK)
        elif type == 'missile':
            self.image.fill(LIGHT_BLUE)
        elif type == 'slow':
            self.image.fill(TIME_SLOW_COLOR)
        elif type == 'plasma':
            self.image.fill(CYAN)
        elif type == 'teleport':
            self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 2

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()