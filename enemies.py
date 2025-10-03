import pygame
import random
import math
from config import *
from projectiles import Bullet

class Enemy(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.type = random.choice(['normal', 'fast', 'big', 'shooter', 'kamikaze', 'tank', 'turret', 'bomber'])
        speed_mult = 1.0
        if self.game.difficulty == 'easy':
            speed_mult = 0.8
        elif self.game.difficulty == 'hard':
            speed_mult = 1.2
        if self.type == 'normal':
            self.image = pygame.Surface((40, 30), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [(0, 30), (20, 0), (40, 30), (20, 20)])
            self.health = 1
            self.speed = random.randint(3, 6) * speed_mult
        elif self.type == 'fast':
            self.image = pygame.Surface((35, 25), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, YELLOW, [(0, 25), (17, 0), (35, 25), (17, 15)])
            self.health = 1
            self.speed = random.randint(6, 9) * speed_mult
        elif self.type == 'big':
            self.image = pygame.Surface((60, 45), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, PURPLE, [(0, 45), (30, 0), (60, 45), (30, 30)])
            self.health = 2
            self.speed = random.randint(2, 4) * speed_mult
        elif self.type == 'shooter':
            self.image = pygame.Surface((45, 35), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, GREEN, [(0, 35), (22, 0), (45, 35), (22, 25)])
            self.health = 1
            self.speed = random.randint(2, 5) * speed_mult
            self.shoot_timer = 0
        elif self.type == 'kamikaze':
            self.image = pygame.Surface((30, 25), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, ORANGE, [(0, 25), (15, 0), (30, 25), (15, 15)])
            self.health = 1
            self.speed = random.randint(4, 7) * speed_mult
        elif self.type == 'tank':
            self.image = pygame.Surface((70, 50), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, GRAY, [(0, 50), (35, 0), (70, 50), (35, 30)])
            self.health = 3
            self.speed = random.randint(1, 3) * speed_mult
            self.shoot_timer = 0
        elif self.type == 'turret':
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(self.image, GREEN, (20, 20), 20)
            self.health = 3
            self.speed = 0
            self.shoot_timer = 0
        elif self.type == 'bomber':
            self.image = pygame.Surface((50, 40), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, BROWN, [(0, 40), (25, 0), (50, 40), (25, 25)])
            self.health = 1
            self.speed = random.randint(2, 4) * speed_mult
            self.drop_timer = 0
        self.rect = self.image.get_rect()
        if self.type == 'turret':
            self.rect.x = SCREEN_WIDTH - 50
            self.rect.y = random.randint(50, SCREEN_HEIGHT - 50)
        else:
            self.rect.x = SCREEN_WIDTH + random.randint(0, 300)
            self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)

    def update(self):
        if self.game.freeze_timer > 0:
            return
        self.rect.x -= self.speed
        if self.type == 'shooter':
            self.shoot_timer += 1
            if self.shoot_timer > 180:  # Shoot every 3 seconds
                enemy_bullet = Bullet(self.rect.left, self.rect.centery, 180, is_enemy=True)
                self.game.all_sprites.add(enemy_bullet)
                self.game.enemy_bullets.add(enemy_bullet)
                self.shoot_timer = 0
        elif self.type == 'kamikaze':
            dx = self.game.player.rect.centerx - self.rect.centerx
            dy = self.game.player.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.rect.x += (dx / dist) * self.speed
                self.rect.y += (dy / dist) * self.speed
        elif self.type == 'tank':
            self.shoot_timer += 1
            if self.shoot_timer > 240:
                for angle in [-30, 0, 30]:
                    enemy_bullet = Bullet(self.rect.left, self.rect.centery, angle + 180, is_enemy=True)
                    self.game.all_sprites.add(enemy_bullet)
                    self.game.enemy_bullets.add(enemy_bullet)
                self.shoot_timer = 0
        elif self.type == 'turret':
            self.shoot_timer += 1
            if self.shoot_timer >= 60:
                dx = self.game.player.rect.centerx - self.rect.centerx
                dy = self.game.player.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    dx /= dist
                    dy /= dist
                angle = math.degrees(math.atan2(dy, dx))
                enemy_bullet = Bullet(self.rect.centerx, self.rect.centery, angle, is_enemy=True)
                self.game.all_sprites.add(enemy_bullet)
                self.game.enemy_bullets.add(enemy_bullet)
                self.shoot_timer = 0
        elif self.type == 'bomber':
            self.drop_timer += 1
            if self.drop_timer > 200:
                bomb = Bullet(self.rect.centerx, self.rect.bottom, 90, is_enemy=True, speed=3)
                self.game.all_sprites.add(bomb)
                self.game.enemy_bullets.add(bomb)
                self.drop_timer = 0
        if self.rect.right < 0:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((80, 60), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, RED, [(0, 60), (40, 0), (80, 60), (40, 40)])
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH + 100
        self.rect.centery = SCREEN_HEIGHT // 2
        self.speed = 1
        self.health = 5
        if self.game.difficulty == 'hard':
            self.health = 7
        elif self.game.difficulty == 'easy':
            self.health = 4
        self.shoot_timer = 0

    def update(self):
        if self.game.freeze_timer > 0:
            return
        self.rect.x -= self.speed
        self.shoot_timer += 1
        if self.shoot_timer > 120:  # Shoot every 2 seconds
            enemy_bullet = Bullet(self.rect.left, self.rect.centery, 180, is_enemy=True)  # Leftward
            self.game.all_sprites.add(enemy_bullet)
            self.game.enemy_bullets.add(enemy_bullet)
            self.shoot_timer = 0
        if self.rect.right < 0:
            self.kill()

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((30, 30))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(0, 300)
        self.rect.y = random.randint(0, SCREEN_HEIGHT - 30)
        self.speed = random.randint(1, 3)
        self.health = 2

    def update(self):
        if self.game.freeze_timer > 0:
            return
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()