import pygame
import random
import sys
import math
import json
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

from particles import Particle
from projectiles import Bullet, Laser, Missile, Bomb, Plasma
from enemies import Enemy, Boss, Asteroid
from powerups import PowerUp
from config import *

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()

# Load high scores
try:
    with open('highscores.json', 'r') as f:
        high_scores = json.load(f)
except FileNotFoundError:
    high_scores = [0] * 5

# Upgrades class
class Upgrades:
    def __init__(self):
        self.load()

    def load(self):
        try:
            with open('upgrades.json', 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {'max_ammo': 100, 'player_speed': 5, 'shield_duration': 300, 'max_health': 100}

    def save(self):
        with open('upgrades.json', 'w') as f:
            json.dump(self.data, f)

    def get(self, key):
        return self.data.get(key, 0)

    def set(self, key, value):
        self.data[key] = value
        self.save()

# Global upgrades instance
upgrades = Upgrades()

# Achievements
achievements = {
    'kill_100': False,
    'reach_level_10': False,
    'combo_10': False,
    'boss_defeated': False
}

# Global upgrades
extra_lives = 0
difficulty = 'normal'  # 'easy', 'normal', 'hard'

# Create stars for space background
stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(150)]

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((50, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, BLUE, [(0, 0), (50, 15), (0, 30), (20, 15)])
        self.rect = self.image.get_rect()
        self.rect.centerx = 100
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = self.game.player_speed
        self.lives = 3 + self.game.extra_lives
        self.power_up = None
        self.power_timer = 0
        self.shield = False
        self.shield_timer = 0
        self.ammo = self.game.max_ammo
        self.bombs = 0
        self.missile_count = 0
        self.shield_duration = self.game.shield_duration
        self.invincibility = False
        self.invincibility_timer = 0
        self.weapon = 'normal'
        self.weapon_timer = 0
        self.max_health = self.game.max_health
        self.health = self.max_health

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed
        if self.power_timer > 0:
            self.power_timer -= 1
        else:
            self.power_up = None
        if self.shield_timer > 0:
            self.shield_timer -= 1
        else:
            self.shield = False
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
        else:
            self.invincibility = False
        if self.game.freeze_timer > 0:
            self.game.freeze_timer -= 1

    def shoot(self):
        if self.ammo > 0:
            if self.power_up == 'rapid':
                if self.ammo >= 3:
                    for i in range(3):
                        bullet = Bullet(self.rect.right, self.rect.centery + i*5 - 5)
                        self.game.all_sprites.add(bullet)
                        self.game.bullets.add(bullet)
                        self.game.bullets_fired += 1
                    self.ammo -= 3
            elif self.power_up == 'spread':
                if self.ammo >= 3:
                    for angle in [-15, 0, 15]:
                        bullet = Bullet(self.rect.right, self.rect.centery, angle)
                        self.game.all_sprites.add(bullet)
                        self.game.bullets.add(bullet)
                        self.game.bullets_fired += 1
                    self.ammo -= 3
            elif self.power_up == 'laser':
                if self.ammo >= 5:
                    bullet = Laser(self.rect.right, self.rect.centery)
                    self.game.all_sprites.add(bullet)
                    self.game.bullets.add(bullet)
                    self.game.bullets_fired += 1
                    self.ammo -= 5
            elif self.power_up == 'homing':
                if self.ammo >= 2:
                    bullet = Bullet(self.rect.right, self.rect.centery, homing=True)
                    self.game.all_sprites.add(bullet)
                    self.game.bullets.add(bullet)
                    self.game.bullets_fired += 1
                    self.ammo -= 2
            elif self.power_up == 'plasma':
                if self.ammo >= 2:
                    plasma = Plasma(self.rect.right, self.rect.centery)
                    self.game.all_sprites.add(plasma)
                    self.game.plasmas.add(plasma)
                    self.game.bullets_fired += 1
                    self.ammo -= 2
            else:
                bullet = Bullet(self.rect.right, self.rect.centery)
                self.game.all_sprites.add(bullet)
                self.game.bullets.add(bullet)
                self.game.bullets_fired += 1
                self.ammo -= 1
            if self.game.shoot_sound:
                self.game.shoot_sound.play()

    def fire_missile(self):
        if self.missile_count > 0:
            self.missile_count -= 1
            missile = Missile(self.rect.right, self.rect.centery)
            self.game.all_sprites.add(missile)
            self.game.missiles.add(missile)
            # Find target
            closest_enemy = None
            min_dist = float('inf')
            for enemy in self.game.enemies:
                dist = math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
            if closest_enemy:
                missile.target = closest_enemy

# Game class
class Game:
    def __init__(self):
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.missiles = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.plasmas = pygame.sprite.Group()

        # Game variables
        self.score = 0
        self.enemies_killed = 0
        self.bullets_fired = 0
        self.level = 1
        self.combo = 0
        self.combo_timer = 0
        self.freeze_timer = 0
        self.bg_x = 0
        self.game_state = 'menu'
        self.boss_spawned = False
        self.paused = False
        self.running = True
        self.enemy_timer = 0
        self.time_slow_timer = 0
        self.slow_factor = 1.0

        # Menu selection
        self.menu_options = ['Start Game', 'Options', 'Tutorial', 'Leaderboard', 'Settings', 'Credits']
        self.selected_option = 0

        # Menu selection
        self.selected_setting = 0
        self.setting_options = ["Music Volume", "SFX Volume", "Back"]
        self.music_volume = 1.0
        self.sfx_volume = 1.0

        # Font
        self.font = pygame.font.SysFont('arial', 48, bold=True)
        self.small_font = pygame.font.SysFont('arial', 24, bold=True)
        self.tiny_font = pygame.font.SysFont('arial', 18)

        self.difficulty = difficulty
        self.high_scores = high_scores
        self.achievements = achievements.copy()
        self.shop_items = [
            {"name": "Extra Life", "cost": 500, "effect": lambda: setattr(self.player, 'lives', self.player.lives + 1)},
            {"name": "Max Ammo +50", "cost": 200, "effect": self.buy_max_ammo},
            {"name": "Speed +1", "cost": 300, "effect": self.buy_speed},
            {"name": "Shield Duration +1s", "cost": 400, "effect": self.buy_shield_duration},
            {"name": "Bomb +1", "cost": 300, "effect": lambda: setattr(self.player, 'bombs', self.player.bombs + 1)},
            {"name": "Health Boost", "cost": 400, "effect": lambda: setattr(self.player, 'health', min(self.player.max_health, self.player.health + 50))},
            {"name": "Missiles +10", "cost": 300, "effect": lambda: setattr(self.player, 'missile_count', self.player.missile_count + 10)},
            {"name": "Max Health +50", "cost": 600, "effect": self.buy_max_health},
        ]
        self.stars = stars
        self.star_speed = 0.5
        self.max_ammo = upgrades.get('max_ammo')
        self.player_speed = upgrades.get('player_speed')
        self.extra_lives = extra_lives
        self.shield_duration = upgrades.get('shield_duration')
        self.max_health = upgrades.get('max_health')
        self.menu_timer = 0
        self.game_over_timer = 0
        self.continue_timer = 0

        # Sound effects
        self.shoot_sound = None
        self.explosion_sound = None
        self.powerup_sound = None
        try:
            self.shoot_sound = pygame.mixer.Sound('shoot.wav')
        except:
            pass
        try:
            self.explosion_sound = pygame.mixer.Sound('explosion.wav')
        except:
            pass
        try:
            self.powerup_sound = pygame.mixer.Sound('powerup.wav')
        except:
            pass
        self.hit_sound = None
        try:
            self.hit_sound = pygame.mixer.Sound('hit.wav')
        except:
            pass
        self.boss_sound = None
        try:
            self.boss_sound = pygame.mixer.Sound('boss.wav')
        except:
            pass
        try:
            pygame.mixer.music.load('background.ogg')
            pygame.mixer.music.play(-1)
        except:
            pass

        pygame.mixer.music.set_volume(self.music_volume)
        if self.shoot_sound: self.shoot_sound.set_volume(self.sfx_volume)
        if self.explosion_sound: self.explosion_sound.set_volume(self.sfx_volume)
        if self.powerup_sound: self.powerup_sound.set_volume(self.sfx_volume)
        if self.hit_sound: self.hit_sound.set_volume(self.sfx_volume)
        if self.boss_sound: self.boss_sound.set_volume(self.sfx_volume)

        # God mode
        self.god_mode = False

        # Create player
        self.player = Player(self)
        self.all_sprites.add(self.player)
        self.apply_difficulty()

    def render_shadowed_text(self, text, color, font):
        shadow = font.render(text, True, BLACK)
        main = font.render(text, True, color)
        surface = pygame.Surface((main.get_width() + 2, main.get_height() + 2), pygame.SRCALPHA)
        surface.blit(shadow, (2, 2))
        surface.blit(main, (0, 0))
        return surface

    def apply_difficulty(self):
        if self.difficulty == 'easy':
            self.extra_lives = 2
            self.player_speed = 6
        elif self.difficulty == 'normal':
            self.extra_lives = 0
            self.player_speed = 5
        elif self.difficulty == 'hard':
            self.extra_lives = -1
            self.player_speed = 4
        self.player.speed = self.player_speed
        self.player.lives = 3 + self.extra_lives

    def reset_game(self):
        self.score = 0
        self.enemies_killed = 0
        self.bullets_fired = 0
        self.level = 1
        self.combo = 0
        self.combo_timer = 0
        self.player.lives = 3 + self.extra_lives
        self.player.power_up = None
        self.player.power_timer = 0
        self.player.shield = False
        self.player.shield_timer = 0
        self.player.ammo = self.max_ammo
        self.player.rect.centerx = 100
        self.player.rect.bottom = SCREEN_HEIGHT - 10
        self.player.health = self.player.max_health
        self.all_sprites.empty()
        self.bullets.empty()
        self.enemies.empty()
        self.powerups.empty()
        self.enemy_bullets.empty()
        self.particles.empty()
        self.asteroids.empty()
        self.plasmas.empty()
        self.all_sprites.add(self.player)
        self.boss_spawned = False
        self.freeze_timer = 0
        self.bg_x = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_state == 'menu':
                    if event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                    elif event.key == pygame.K_RETURN:
                        if self.selected_option == 0:
                            self.game_state = 'playing'
                        elif self.selected_option == 1:
                            self.game_state = 'options'
                        elif self.selected_option == 2:
                            self.game_state = 'tutorial'
                        elif self.selected_option == 3:
                            self.game_state = 'leaderboard'
                        elif self.selected_option == 4:
                            self.game_state = 'settings'
                        elif self.selected_option == 5:
                            self.game_state = 'credits'
                elif self.game_state == 'options':
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'menu'
                    elif event.key == pygame.K_1:
                        self.difficulty = 'easy'
                        self.apply_difficulty()
                    elif event.key == pygame.K_2:
                        self.difficulty = 'normal'
                        self.apply_difficulty()
                    elif event.key == pygame.K_3:
                        self.difficulty = 'hard'
                        self.apply_difficulty()
                elif self.game_state == 'tutorial':
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'menu'
                elif self.game_state == 'leaderboard':
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'menu'
                elif self.game_state == 'settings':
                    if event.key == pygame.K_UP:
                        self.selected_setting = (self.selected_setting - 1) % len(self.setting_options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_setting = (self.selected_setting + 1) % len(self.setting_options)
                    elif event.key == pygame.K_LEFT:
                        if self.selected_setting == 0:
                            self.music_volume = max(0, self.music_volume - 0.1)
                            pygame.mixer.music.set_volume(self.music_volume)
                        elif self.selected_setting == 1:
                            self.sfx_volume = max(0, self.sfx_volume - 0.1)
                            if self.shoot_sound: self.shoot_sound.set_volume(self.sfx_volume)
                            if self.explosion_sound: self.explosion_sound.set_volume(self.sfx_volume)
                            if self.powerup_sound: self.powerup_sound.set_volume(self.sfx_volume)
                            if self.hit_sound: self.hit_sound.set_volume(self.sfx_volume)
                            if self.boss_sound: self.boss_sound.set_volume(self.sfx_volume)
                    elif event.key == pygame.K_RIGHT:
                        if self.selected_setting == 0:
                            self.music_volume = min(1, self.music_volume + 0.1)
                            pygame.mixer.music.set_volume(self.music_volume)
                        elif self.selected_setting == 1:
                            self.sfx_volume = min(1, self.sfx_volume + 0.1)
                            if self.shoot_sound: self.shoot_sound.set_volume(self.sfx_volume)
                            if self.explosion_sound: self.explosion_sound.set_volume(self.sfx_volume)
                            if self.powerup_sound: self.powerup_sound.set_volume(self.sfx_volume)
                            if self.hit_sound: self.hit_sound.set_volume(self.sfx_volume)
                            if self.boss_sound: self.boss_sound.set_volume(self.sfx_volume)
                    elif event.key == pygame.K_RETURN:
                        if self.selected_setting == 2:
                            self.game_state = 'menu'
                elif self.game_state == 'credits':
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'menu'
                elif self.game_state == 'game_over':
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.game_state = 'playing'
                    elif event.key == pygame.K_s:
                        self.game_state = 'shop'
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                elif self.game_state == 'shop':
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = 'game_over'
                    elif event.key == pygame.K_1 and self.score >= self.shop_items[0]["cost"]:
                        self.score -= self.shop_items[0]["cost"]
                        self.shop_items[0]["effect"]()
                    elif event.key == pygame.K_2 and self.score >= self.shop_items[1]["cost"]:
                        self.score -= self.shop_items[1]["cost"]
                        self.shop_items[1]["effect"]()
                    elif event.key == pygame.K_3 and self.score >= self.shop_items[2]["cost"]:
                        self.score -= self.shop_items[2]["cost"]
                        self.shop_items[2]["effect"]()
                    elif event.key == pygame.K_4 and self.score >= self.shop_items[3]["cost"]:
                        self.score -= self.shop_items[3]["cost"]
                        self.shop_items[3]["effect"]()
                    elif event.key == pygame.K_5 and self.score >= self.shop_items[4]["cost"]:
                        self.score -= self.shop_items[4]["cost"]
                        self.shop_items[4]["effect"]()
                    elif event.key == pygame.K_6 and self.score >= self.shop_items[5]["cost"]:
                        self.score -= self.shop_items[5]["cost"]
                        self.shop_items[5]["effect"]()
                    elif event.key == pygame.K_7 and self.score >= self.shop_items[6]["cost"]:
                        self.score -= self.shop_items[6]["cost"]
                        self.shop_items[6]["effect"]()
                    elif event.key == pygame.K_8 and self.score >= self.shop_items[7]["cost"]:
                        self.score -= self.shop_items[7]["cost"]
                        self.shop_items[7]["effect"]()
                elif self.game_state == 'playing':
                    if event.key == pygame.K_SPACE:
                        self.player.shoot()
                    elif event.key == pygame.K_b:
                        if self.player.bombs > 0:
                            bomb = Bomb(self.player.rect.right, self.player.rect.centery)
                            self.all_sprites.add(bomb)
                            self.bombs.add(bomb)
                            self.player.bombs -= 1
                    elif event.key == pygame.K_m:
                        self.player.fire_missile()
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_g:
                        self.god_mode = not self.god_mode
                elif self.game_state == 'pause_menu':
                    if event.key == pygame.K_r:
                        self.paused = False
                        self.game_state = 'playing'
                    elif event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_n:
                        self.reset_game()
                        self.paused = False
                        self.game_state = 'playing'
                elif self.game_state == 'continue_prompt':
                    if event.key == pygame.K_SPACE:
                        self.game_state = 'playing'
                        # Reset player position
                        self.player.rect.centerx = 100
                        self.player.rect.bottom = SCREEN_HEIGHT - 10
                        self.player.invincibility = True
                        self.player.invincibility_timer = 120  # 2 seconds invincibility

    def update_playing(self):
        # Level progression
        if self.score >= self.level * 100:
            self.level += 1

        # Spawn enemies
        self.enemy_timer += 1
        spawn_rate = max(30, 45 - self.level * 5)
        if self.enemy_timer > spawn_rate:
            enemy = Enemy(self)
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)
            self.enemy_timer = 0

        # Spawn asteroids
        if random.random() < 0.3:
            ast = Asteroid(self)
            self.all_sprites.add(ast)
            self.asteroids.add(ast)

        # Spawn boss
        if self.score > 500 and not self.boss_spawned:
            boss = Boss(self)
            self.all_sprites.add(boss)
            self.enemies.add(boss)
            self.boss_spawned = True

        # Update
        self.all_sprites.update()
        self.particles.update()

        # Combo timer
        if self.combo > 0:
            self.combo_timer += 1
            if self.combo_timer > 120:
                self.combo = 0
                self.combo_timer = 0

        if self.time_slow_timer > 0:
            self.time_slow_timer -= 1
            self.slow_factor = 0.5
        else:
            self.slow_factor = 1.0

        # Check achievements
        if self.enemies_killed >= 100 and not self.achievements['kill_100']:
            self.achievements['kill_100'] = True
            self.score += 1000
        if self.level >= 10 and not self.achievements['reach_level_10']:
            self.achievements['reach_level_10'] = True
            self.score += 500
        if self.combo >= 10 and not self.achievements['combo_10']:
            self.achievements['combo_10'] = True
            self.score += 200
        if self.boss_spawned and not any(isinstance(e, Boss) for e in self.enemies) and not self.achievements['boss_defeated']:
            self.achievements['boss_defeated'] = True
            self.score += 2000

        # Collisions
        if not self.god_mode and not self.player.shield and not self.player.invincibility and (pygame.sprite.spritecollideany(self.player, self.enemies) or pygame.sprite.spritecollideany(self.player, self.enemy_bullets) or pygame.sprite.spritecollideany(self.player, self.asteroids)):
            self.player.health -= 20
            if self.player.health <= 0:
                self.player.lives -= 1
                self.player.health = self.player.max_health
                if self.player.lives > 0:
                    self.game_state = 'continue_prompt'
                    self.continue_timer = 0
                else:
                    self.game_state = 'game_over'
                    # Update high scores
                    if self.score > min(self.high_scores):
                        self.high_scores.append(self.score)
                        self.high_scores.sort(reverse=True)
                        self.high_scores = self.high_scores[:5]
                        with open('highscores.json', 'w') as f:
                            json.dump(self.high_scores, f)
        else:
            self.player.shield = False
            self.player.shield_timer = 0

        # Bullet-enemy collisions
        bullet_hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, False)
        for bullet, enemy_list in bullet_hits.items():
            for enemy in enemy_list:
                enemy.health -= 1
                if enemy.health <= 0:
                    enemy.kill()
                    self.combo_timer = 0
                    self.combo += 1
                    self.score += 10 * self.combo
                    self.enemies_killed += 1
                    # Explosion particles
                    for _ in range(10):
                        p = Particle(enemy.rect.centerx, enemy.rect.centery, RED)
                        self.particles.add(p)
                    if random.random() < 0.3:
                        pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport'])
                        pu = PowerUp(enemy.rect.centerx, enemy.rect.centery, pu_type)
                        self.all_sprites.add(pu)
                        self.powerups.add(pu)
                    if self.explosion_sound:
                        self.explosion_sound.play()

        # Missile-enemy collisions
        missile_hits = pygame.sprite.groupcollide(self.missiles, self.enemies, True, False)
        for missile, enemy_list in missile_hits.items():
            for enemy in enemy_list:
                enemy.health -= 2  # missiles do more damage
                if enemy.health <= 0:
                    enemy.kill()
                    self.combo_timer = 0
                    self.combo += 1
                    self.score += 10 * self.combo
                    self.enemies_killed += 1
                    # Explosion particles
                    for _ in range(10):
                        p = Particle(enemy.rect.centerx, enemy.rect.centery, RED)
                        self.particles.add(p)
                    if random.random() < 0.3:
                        pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport'])
                        pu = PowerUp(enemy.rect.centerx, enemy.rect.centery, pu_type)
                        self.all_sprites.add(pu)
                        self.powerups.add(pu)
                    if self.explosion_sound:
                        self.explosion_sound.play()

        # Bullet-asteroid collisions
        asteroid_hits = pygame.sprite.groupcollide(self.bullets, self.asteroids, True, False)
        for bullet, ast_list in asteroid_hits.items():
            for ast in ast_list:
                ast.health -= 1
                if ast.health <= 0:
                    ast.kill()
                    self.score += 5
                    # particles
                    for _ in range(5):
                        p = Particle(ast.rect.centerx, ast.rect.centery, BROWN)
                        self.particles.add(p)

        # Plasma-enemy collisions
        plasma_hits = pygame.sprite.groupcollide(self.plasmas, self.enemies, False, False)
        for plasma, enemy_list in plasma_hits.items():
            for enemy in enemy_list:
                enemy.health -= 1
                if enemy.health <= 0:
                    enemy.kill()
                    self.combo_timer = 0
                    self.combo += 1
                    self.score += 10 * self.combo
                    self.enemies_killed += 1
                    # Explosion particles
                    for _ in range(10):
                        p = Particle(enemy.rect.centerx, enemy.rect.centery, RED)
                        self.particles.add(p)
                    if random.random() < 0.3:
                        pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport', 'plasma'])
                        pu = PowerUp(enemy.rect.centerx, enemy.rect.centery, pu_type)
                        self.all_sprites.add(pu)
                        self.powerups.add(pu)
                    if self.explosion_sound:
                        self.explosion_sound.play()

        # Player-powerup collision
        pu_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for pu in pu_hits:
            if pu.type == 'shield':
                self.player.shield = True
                self.player.shield_timer = self.player.shield_duration
            elif pu.type == 'ammo':
                self.player.ammo = min(self.max_ammo, self.player.ammo + 50)
            elif pu.type == 'bomb':
                self.player.bombs += 1
            elif pu.type == 'missile':
                self.player.missile_count += 10
            elif pu.type == 'freeze':
                self.freeze_timer = 300
            elif pu.type == 'invincibility':
                self.player.invincibility = True
                self.player.invincibility_timer = 300
            elif pu.type == 'health':
                self.player.health = min(self.player.max_health, self.player.health + 50)
            elif pu.type == 'slow':
                self.time_slow_timer = 300
                self.slow_factor = 0.5
            elif pu.type == 'teleport':
                self.player.rect.centerx = random.randint(50, SCREEN_WIDTH-50)
                self.player.rect.centery = random.randint(50, SCREEN_HEIGHT-50)
            else:
                self.player.power_up = pu.type
                self.player.power_timer = 300
        if self.powerup_sound:
            self.powerup_sound.play()

    def draw_menu(self):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(self.stars)):
            self.stars[i] = ((self.stars[i][0] - self.star_speed) % SCREEN_WIDTH, self.stars[i][1])
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        self.menu_timer += 1
        color_value = int(128 + 127 * math.sin(self.menu_timer * 0.05))
        title_color = (255, color_value, 255)
        title = self.render_shadowed_text("Space Shooter", title_color, self.font)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        subtitle = self.render_shadowed_text("Defend the Galaxy!", (200, 200, 255), self.small_font)
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 230))
        high_score_text = self.render_shadowed_text(f"High Score: {self.high_scores[0]}", GREEN, self.small_font)
        screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, 260))
        for i, option in enumerate(self.menu_options):
            color = GREEN if i == self.selected_option else WHITE
            option_text = self.render_shadowed_text(option, color, self.small_font)
            screen.blit(option_text, (SCREEN_WIDTH//2 - option_text.get_width()//2, 310 + i * 30))
        hint_text = self.render_shadowed_text("Use UP/DOWN to select, ENTER to choose", WHITE, self.tiny_font)
        screen.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, 450))
        version_text = self.render_shadowed_text("Version 1.0", (150, 150, 150), self.small_font)
        screen.blit(version_text, (SCREEN_WIDTH//2 - version_text.get_width()//2, SCREEN_HEIGHT - 50))
        pygame.display.flip()

    def draw_options(self):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(self.stars)):
            self.stars[i] = ((self.stars[i][0] - self.star_speed) % SCREEN_WIDTH, self.stars[i][1])
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        options_title = self.render_shadowed_text("Difficulty Options", WHITE, self.font)
        screen.blit(options_title, (SCREEN_WIDTH//2 - options_title.get_width()//2, 100))
        easy_text = self.render_shadowed_text("1. Easy (More lives, slower enemies)", GREEN if self.difficulty == 'easy' else WHITE, self.small_font)
        screen.blit(easy_text, (SCREEN_WIDTH//2 - easy_text.get_width()//2, 200))
        normal_text = self.render_shadowed_text("2. Normal", GREEN if self.difficulty == 'normal' else WHITE, self.small_font)
        screen.blit(normal_text, (SCREEN_WIDTH//2 - normal_text.get_width()//2, 250))
        hard_text = self.render_shadowed_text("3. Hard (Fewer lives, faster enemies)", GREEN if self.difficulty == 'hard' else WHITE, self.small_font)
        screen.blit(hard_text, (SCREEN_WIDTH//2 - hard_text.get_width()//2, 300))
        back_text = self.render_shadowed_text("Press ESC to go back", WHITE, self.small_font)
        screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 400))
        pygame.display.flip()

    def draw_tutorial(self):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(self.stars)):
            self.stars[i] = ((self.stars[i][0] - self.star_speed) % SCREEN_WIDTH, self.stars[i][1])
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        tutorial_title = self.render_shadowed_text("Tutorial", WHITE, self.font)
        screen.blit(tutorial_title, (SCREEN_WIDTH//2 - tutorial_title.get_width()//2, 50))
        lines = [
            "Use arrow keys to move your ship.",
            "Press SPACE to shoot. Watch your ammo!",
            "Press B to drop a bomb that explodes and damages nearby enemies.",
            "Collect power-ups: Green=Rapid, Yellow=Spread, Red=Laser, Blue=Shield, White=Ammo, Purple=Bomb, Orange=Homing, Light Blue=Missile, Gray=Freeze, Magenta=Invincibility, Pink=Health, Light Green=Time Slow, Cyan=Plasma, Brown=Teleport.",
            "Watch out for asteroids! They can damage you and block your shots.",
            "Avoid enemies and their bullets. Shield protects for 5 seconds. Invincibility makes you immune for 5 seconds. Freeze stops enemies for 5 seconds. Time Slow slows down enemies and asteroids for 5 seconds.",
            "Build combos for bonus points. Pause with P.",
            "Reach higher levels for more challenges.",
            "Defeat the boss for glory!"
        ]
        for i, line in enumerate(lines):
            text = self.render_shadowed_text(line, WHITE, self.small_font)
            screen.blit(text, (50, 100 + i*30))
        back_text = self.render_shadowed_text("Press ESC to go back", WHITE, self.small_font)
        screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 500))
        pygame.display.flip()

    def draw_leaderboard(self):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(self.stars)):
            self.stars[i] = ((self.stars[i][0] - self.star_speed) % SCREEN_WIDTH, self.stars[i][1])
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        leaderboard_title = self.render_shadowed_text("Leaderboard", WHITE, self.font)
        screen.blit(leaderboard_title, (SCREEN_WIDTH//2 - leaderboard_title.get_width()//2, 50))
        for i, hs in enumerate(self.high_scores):
            text = self.render_shadowed_text(f"{i+1}. {hs}", GREEN, self.small_font)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 100 + i*30))
        back_text = self.render_shadowed_text("Press ESC to go back", WHITE, self.small_font)
        screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 500))
        pygame.display.flip()

    def draw_playing(self):
        screen.fill(BLACK)
        # Draw stars
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        # Scrolling nebula background
        pygame.draw.rect(screen, (20, 0, 40), (self.bg_x, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(screen, (20, 0, 40), (self.bg_x + SCREEN_WIDTH, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.bg_x -= 1
        if self.bg_x <= -SCREEN_WIDTH:
            self.bg_x = 0

        self.all_sprites.draw(screen)
        # Draw particles
        for p in self.particles:
            pygame.draw.circle(screen, p.color, (int(p.x), int(p.y)), 2)
        # Draw shield
        if self.player.shield:
            pygame.draw.circle(screen, BLUE, self.player.rect.center, 30, 2)
        if self.player.invincibility:
            pygame.draw.circle(screen, MAGENTA, self.player.rect.center, 35, 2)
        # Draw boss health bar
        if self.boss_spawned:
            for e in self.enemies:
                if isinstance(e, Boss):
                    bar_width = 200
                    bar_height = 20
                    bar_x = SCREEN_WIDTH - bar_width - 10
                    bar_y = 10
                    pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
                    health_width = (e.health / (7 if self.difficulty == 'hard' else 5 if self.difficulty == 'normal' else 4)) * bar_width
                    pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))
                    pygame.draw.rect(screen, WHITE, (bar_x-2, bar_y-2, bar_width+4, bar_height+4), 2)
                    break
        # Draw mini-map
        mini_map_size = 100
        mini_x = SCREEN_WIDTH - mini_map_size - 10
        mini_y = SCREEN_HEIGHT - mini_map_size - 10
        pygame.draw.rect(screen, BLACK, (mini_x, mini_y, mini_map_size, mini_map_size))
        pygame.draw.rect(screen, WHITE, (mini_x, mini_y, mini_map_size, mini_map_size), 1)
        scale = mini_map_size / SCREEN_WIDTH
        for enemy in self.enemies:
            ex = mini_x + enemy.rect.centerx * scale
            ey = mini_y + enemy.rect.centery * scale
            pygame.draw.circle(screen, RED, (int(ex), int(ey)), 2)
        for pu in self.powerups:
            px = mini_x + pu.rect.centerx * scale
            py = mini_y + pu.rect.centery * scale
            pygame.draw.circle(screen, YELLOW, (int(px), int(py)), 1)
        for eb in self.enemy_bullets:
            bx = mini_x + eb.rect.centerx * scale
            by = mini_y + eb.rect.centery * scale
            pygame.draw.circle(screen, RED, (int(bx), int(by)), 1)
        for ast in self.asteroids:
            ax = mini_x + ast.rect.centerx * scale
            ay = mini_y + ast.rect.centery * scale
            pygame.draw.circle(screen, GRAY, (int(ax), int(ay)), 2)
        px = mini_x + self.player.rect.centerx * scale
        py = mini_y + self.player.rect.centery * scale
        pygame.draw.circle(screen, BLUE, (int(px), int(py)), 3)

        # Draw score, lives, power-up, level, ammo, combo
        score_text = self.render_shadowed_text(f"Score: {self.score}", WHITE, self.small_font)
        screen.blit(score_text, (10, 10))
        lives_text = self.render_shadowed_text(f"Lives: {self.player.lives}", GREEN, self.small_font)
        screen.blit(lives_text, (10, 35))
        power_text = self.render_shadowed_text(f"Power: {self.player.power_up or 'None'}", WHITE, self.small_font)
        screen.blit(power_text, (10, 60))
        level_text = self.render_shadowed_text(f"Level: {self.level}", YELLOW, self.small_font)
        screen.blit(level_text, (10, 85))
        ammo_text = self.render_shadowed_text(f"Ammo: {self.player.ammo}", WHITE, self.small_font)
        screen.blit(ammo_text, (10, 110))
        combo_text = self.render_shadowed_text(f"Combo: {self.combo}", RED, self.small_font)
        screen.blit(combo_text, (10, 135))
        bombs_text = self.render_shadowed_text(f"Bombs: {self.player.bombs}", WHITE, self.small_font)
        screen.blit(bombs_text, (10, 160))
        # Health bar
        bar_width = 200
        bar_height = 10
        bar_x = 10
        bar_y = 270
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = (self.player.health / self.player.max_health) * bar_width
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x-2, bar_y-2, bar_width+4, bar_height+4), 2)

        pygame.display.flip()

    def draw_pause_menu(self):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(self.stars)):
            self.stars[i] = ((self.stars[i][0] - self.star_speed) % SCREEN_WIDTH, self.stars[i][1])
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        pause_title = self.render_shadowed_text("Paused", WHITE, self.font)
        screen.blit(pause_title, (SCREEN_WIDTH//2 - pause_title.get_width()//2, 150))
        resume_text = self.render_shadowed_text("Press P to Resume", GREEN, self.small_font)
        screen.blit(resume_text, (SCREEN_WIDTH//2 - resume_text.get_width()//2, 250))
        quit_text = self.render_shadowed_text("Press Q to Quit", RED, self.small_font)
        screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, 300))
        pygame.display.flip()

    def draw_continue_prompt(self):
        # Draw the current game state
        self.draw_playing()
        # Overlay continue prompt
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        screen.blit(overlay, (0, 0))
        continue_text = self.render_shadowed_text("Continue?", WHITE, self.font)
        screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        press_space_text = self.render_shadowed_text("Press SPACE to continue", GREEN, self.small_font)
        screen.blit(press_space_text, (SCREEN_WIDTH//2 - press_space_text.get_width()//2, SCREEN_HEIGHT//2))
        remaining_time = max(0, (600 - self.continue_timer) // 60)
        time_text = self.render_shadowed_text(f"Time left: {remaining_time}", YELLOW, self.small_font)
        screen.blit(time_text, (SCREEN_WIDTH//2 - time_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
        pygame.display.flip()

    def draw_game_over(self):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = 0
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Draw stars
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        self.game_over_timer += 1
        color_value = int(128 + 127 * math.sin(self.game_over_timer * 0.05))
        game_over_color = (255, color_value, color_value)
        game_over_text = self.render_shadowed_text("Game Over", game_over_color, self.font)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 150))
        final_score_text = self.render_shadowed_text(f"Final Score: {self.score}", WHITE, self.small_font)
        screen.blit(final_score_text, (SCREEN_WIDTH//2 - final_score_text.get_width()//2, 200))
        enemies_text = self.render_shadowed_text(f"Enemies Killed: {self.enemies_killed}", WHITE, self.small_font)
        screen.blit(enemies_text, (SCREEN_WIDTH//2 - enemies_text.get_width()//2, 250))
        bullets_text = self.render_shadowed_text(f"Bullets Fired: {self.bullets_fired}", WHITE, self.small_font)
        screen.blit(bullets_text, (SCREEN_WIDTH//2 - bullets_text.get_width()//2, 300))
        level_text = self.render_shadowed_text(f"Level Reached: {self.level}", YELLOW, self.small_font)
        screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, 350))
        achievements_text = self.render_shadowed_text("Achievements Unlocked:", GREEN, self.small_font)
        screen.blit(achievements_text, (SCREEN_WIDTH//2 - achievements_text.get_width()//2, 375))
        ach_list = [k for k, v in self.achievements.items() if v]
        for i, ach in enumerate(ach_list):
            ach_text = self.render_shadowed_text(ach.replace('_', ' ').title(), GREEN, self.small_font)
            screen.blit(ach_text, (SCREEN_WIDTH//2 - ach_text.get_width()//2, 400 + i*25))
        shop_text = self.render_shadowed_text("Press S for Shop or SPACE to Restart", WHITE, self.small_font)
        screen.blit(shop_text, (SCREEN_WIDTH//2 - shop_text.get_width()//2, 500))
        pygame.display.flip()

    def draw_shop(self):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = 0
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Draw stars
        for star in self.stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        shop_title = self.render_shadowed_text("Upgrade Shop", WHITE, self.font)
        screen.blit(shop_title, (SCREEN_WIDTH//2 - shop_title.get_width()//2, 100))
        score_text = self.render_shadowed_text(f"Score: {self.score}", WHITE, self.small_font)
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
        for i, item in enumerate(self.shop_items):
            item_text = self.render_shadowed_text(f"{i+1}. {item['name']} - {item['cost']} pts", GREEN if self.score >= item['cost'] else RED, self.small_font)
            screen.blit(item_text, (SCREEN_WIDTH//2 - item_text.get_width()//2, 200 + i*50))
        back_text = self.render_shadowed_text("Press ESC to go back", WHITE, self.small_font)
        screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 450))
        pygame.display.flip()

    def buy_max_ammo(self):
        self.upgrades.set('max_ammo', self.upgrades.get('max_ammo') + 50)
        self.max_ammo = self.upgrades.get('max_ammo')

    def buy_speed(self):
        self.upgrades.set('player_speed', self.upgrades.get('player_speed') + 1)
        self.player_speed = self.upgrades.get('player_speed')
        self.player.speed = self.player_speed

    def buy_shield_duration(self):
        self.upgrades.set('shield_duration', self.upgrades.get('shield_duration') + 60)
        self.shield_duration = self.upgrades.get('shield_duration')
        self.player.shield_duration = self.shield_duration

    def buy_max_health(self):
        self.upgrades.set('max_health', self.upgrades.get('max_health') + 50)
        self.max_health = self.upgrades.get('max_health')
        self.player.max_health = self.max_health

    def update_continue_prompt(self):
        self.continue_timer += 1
        if self.continue_timer > 600:  # 10 seconds at 60 FPS
            self.game_state = 'game_over'
            # Update high scores
            if self.score > min(self.high_scores):
                self.high_scores.append(self.score)
                self.high_scores.sort(reverse=True)
                self.high_scores = self.high_scores[:5]
                with open('highscores.json', 'w') as f:
                    json.dump(self.high_scores, f)

    def run(self):
        while self.running:
            clock.tick(FPS)
            self.handle_events()
            if self.game_state == 'menu':
                self.draw_menu()
            elif self.game_state == 'options':
                self.draw_options()
            elif self.game_state == 'tutorial':
                self.draw_tutorial()
            elif self.game_state == 'leaderboard':
                self.draw_leaderboard()
            elif self.game_state == 'playing':
                if self.paused:
                    self.game_state = 'pause_menu'
                    continue
                self.update_playing()
                self.draw_playing()
            elif self.game_state == 'pause_menu':
                self.draw_pause_menu()
            elif self.game_state == 'game_over':
                self.draw_game_over()
            elif self.game_state == 'shop':
                self.draw_shop()
            elif self.game_state == 'continue_prompt':
                self.update_continue_prompt()
                self.draw_continue_prompt()
        pygame.quit()
        sys.exit()

# Main game loop
game = Game()
game.run()