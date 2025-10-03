import pygame
import math
import random
from config import *

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle=0, homing=False, is_enemy=False):
        super().__init__()
        self.image = pygame.Surface((10, 5))
        self.image.fill(ORANGE if homing else YELLOW)
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.centery = y
        self.speed = 10
        self.angle = angle
        self.vel_x = self.speed * math.cos(math.radians(angle))
        self.vel_y = self.speed * math.sin(math.radians(angle))
        self.trail_timer = 0
        self.homing = homing
        self.is_enemy = is_enemy

    def update(self):
        if self.homing:
            closest_enemy = None
            min_dist = float('inf')
            for enemy in self.game.enemies:
                dist = math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
            if closest_enemy:
                target_x = closest_enemy.rect.centerx
                target_y = closest_enemy.rect.centery
                dx = target_x - self.rect.centerx
                dy = target_y - self.rect.centery
                target_angle = math.degrees(math.atan2(dy, dx))
                current_angle = math.degrees(math.atan2(self.vel_y, self.vel_x))
                angle_diff = (target_angle - current_angle) % 360
                if angle_diff > 180:
                    angle_diff -= 360
                turn_rate = 5  # degrees per frame
                if angle_diff > 0:
                    current_angle += min(turn_rate, angle_diff)
                else:
                    current_angle -= min(turn_rate, -angle_diff)
                self.vel_x = self.speed * math.cos(math.radians(current_angle))
                self.vel_y = self.speed * math.sin(math.radians(current_angle))
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.trail_timer += 1
        if self.trail_timer > 5:
            p = Particle(self.rect.centerx, self.rect.centery, ORANGE if self.homing else YELLOW)
            self.game.particles.add(p)
            self.trail_timer = 0
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((50, 5))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.centery = y
        self.speed = 15
        self.vel_x = self.speed
        self.vel_y = 0
        self.trail_timer = 0

    def update(self):
        self.rect.x += self.vel_x
        self.trail_timer += 1
        if self.trail_timer > 3:
            p = Particle(self.rect.centerx, self.rect.centery, RED)
            self.game.particles.add(p)
            self.trail_timer = 0
        if self.rect.left > SCREEN_WIDTH:
            self.kill()

class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 20))
        self.image.fill(CYAN)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 5
        self.target = None

    def update(self):
        if self.target and self.target.alive():
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.rect.x += (dx / dist) * self.speed
                self.rect.y += (dy / dist) * self.speed
        else:
            self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

class Bomb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.timer = 120  # 2 seconds

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            # Explode
            for e in self.game.enemies:
                if math.hypot(e.rect.centerx - self.rect.centerx, e.rect.centery - self.rect.centery) < 100:
                    e.health -= 1
                    if e.health <= 0:
                        e.kill()
                        self.game.combo_timer = 0
                        self.game.combo += 1
                        self.game.score += 10 * self.game.combo
                        self.game.enemies_killed += 1
                        # Explosion particles
                        for _ in range(10):
                            p = Particle(e.rect.centerx, e.rect.centery, RED)
                            self.game.particles.add(p)
                        if random.random() < 0.3:
                            pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow'])
                            pu = PowerUp(e.rect.centerx, e.rect.centery, pu_type)
                            self.game.all_sprites.add(pu)
                            self.game.powerups.add(pu)
            # Particles
            for _ in range(20):
                p = Particle(self.rect.centerx, self.rect.centery, RED)
                self.game.particles.add(p)
            self.kill()

class Plasma(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 5))
        self.image.fill((0, 255, 255))  # Cyan
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.centery = y
        self.speed = 12
        self.vel_x = self.speed
        self.vel_y = 0
        self.trail_timer = 0

    def update(self):
        self.rect.x += self.vel_x
        self.trail_timer += 1
        if self.trail_timer > 5:
            p = Particle(self.rect.centerx, self.rect.centery, (0, 255, 255))
            self.game.particles.add(p)
            self.trail_timer = 0
        if self.rect.left > SCREEN_WIDTH:
            self.kill()