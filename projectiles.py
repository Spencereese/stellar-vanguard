import pygame
import math
import random
from config import *
from particles import Particle
from powerups import PowerUp

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle=0, homing=False, is_enemy=False, game=None, speed=18, spread_homing=False):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((10, 5))
        # Color bullets: red for enemies, orange for homing player bullets, yellow for normal player bullets
        if is_enemy:
            self.image.fill(RED)
        elif homing:
            self.image.fill(ORANGE)
        else:
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.centery = y
        self.speed = speed
        self.angle = angle
        self.vel_x = self.speed * math.cos(math.radians(angle))
        self.vel_y = self.speed * math.sin(math.radians(angle))
        self.trail_timer = 0
        self.homing = homing
        self.is_enemy = is_enemy
        self.spread_homing = spread_homing  # Slight homing for spread shots

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
        elif self.spread_homing:
            # Slight homing for spread shots
            closest_enemy = None
            min_dist = float('inf')
            for enemy in self.game.enemies:
                dist = math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
                if dist < min_dist and dist < 120:  # Only home if enemy is reasonably close
                    min_dist = dist
                    closest_enemy = enemy
            if closest_enemy:
                dx = closest_enemy.rect.centerx - self.rect.centerx
                dy = closest_enemy.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    # Gently adjust velocity toward enemy
                    homing_strength = 0.03
                    self.vel_x += (dx / dist) * homing_strength * self.speed
                    self.vel_y += (dy / dist) * homing_strength * self.speed
                    # Normalize speed to maintain consistent velocity
                    current_speed = math.hypot(self.vel_x, self.vel_y)
                    if current_speed > 0:
                        self.vel_x = (self.vel_x / current_speed) * self.speed
                        self.vel_y = (self.vel_y / current_speed) * self.speed
        
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.trail_timer += 1
        if self.trail_timer > 5:
            # Enhanced particle trail effects
            if self.is_enemy:
                particle_color = RED
                particle_type = 'spark'
            elif self.homing:
                particle_color = ORANGE
                particle_type = 'fire'
            else:
                particle_color = YELLOW
                particle_type = 'spark'
            
            # Create multiple trail particles for more visual impact
            for _ in range(random.randint(1, 3)):
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                p = Particle(self.rect.centerx + offset_x, self.rect.centery + offset_y, 
                           particle_color, particle_type, random.randint(1, 2))
                self.game.particles.append(p)
            self.trail_timer = 0
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class PiercingBullet(Bullet):
    """Bullet that can pierce through multiple enemies (for multishot)"""
    def __init__(self, x, y, angle=0, game=None, speed=18):
        super().__init__(x, y, angle, False, False, game, speed)
        self.image.fill((255, 165, 0))  # Orange color for piercing bullets
        self.pierce_count = 0
        self.max_pierce = 2  # Can pierce through 2 enemies
        self.has_pierced = False

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.trail_timer += 1
        if self.trail_timer > 5:
            p = Particle(self.rect.centerx, self.rect.centery, (255, 165, 0))
            self.game.particles.append(p)
            self.trail_timer = 0
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, game=None):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((60, 8))  # Wider and taller beam
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.centery = y
        self.speed = 15
        self.vel_x = self.speed
        self.vel_y = 0
        self.trail_timer = 0
        self.pierce_count = 0  # Track how many enemies pierced
        self.max_pierce = 3   # Can pierce through 3 enemies
        self.damage_trail = []  # Store trail positions for damage over time

    def update(self):
        # Store current position for trail damage
        self.damage_trail.append((self.rect.centerx, self.rect.centery))
        if len(self.damage_trail) > 30:  # Keep last 30 positions
            self.damage_trail.pop(0)
        
        self.rect.x += self.vel_x
        self.trail_timer += 1
        if self.trail_timer > 2:  # More frequent particles
            # Enhanced laser trail with multiple particle types
            for _ in range(3):  # Multiple particles per trail
                offset_x = random.randint(-3, 3)
                offset_y = random.randint(-2, 2)
                if isinstance(self, FreezeBeam):
                    particle_color = (100, 200, 255)  # Ice blue
                    particle_type = 'plasma'
                elif isinstance(self, Lightning):
                    particle_color = (200, 255, 255)  # Electric white
                    particle_type = 'electric'
                else:
                    particle_color = RED
                    particle_type = 'fire'
                
                p = Particle(self.rect.centerx + offset_x, self.rect.centery + offset_y, 
                           particle_color, particle_type, random.randint(1, 3))
                self.game.particles.append(p)
            self.trail_timer = 0
            
            # Damage enemies near the trail
            weapon_type = 'freeze' if isinstance(self, FreezeBeam) else 'laser'
            for trail_pos in self.damage_trail[-5:]:  # Check last 5 trail positions
                for enemy in list(self.game.enemies):
                    if math.hypot(enemy.rect.centerx - trail_pos[0], enemy.rect.centery - trail_pos[1]) < 25:
                        damage = self.game.calculate_damage(0.5, weapon_type)
                        enemy.health -= damage
                        if hasattr(self, "game") and self.game and hasattr(self.game, "spawn_damage_number"):
                            self.game.spawn_damage_number(enemy.rect.centerx, enemy.rect.centery - 12, damage, False)
                        if enemy.health <= 0:
                            if self.game.session:
                                self.game.session.handle_enemy_death(enemy)
                            else:
                                enemy.kill()
                                self.game.combo_timer = 0
                                self.game.combo += 1
                                if not hasattr(self.game, 'max_combo'):
                                    self.game.max_combo = 0
                                self.game.max_combo = max(self.game.max_combo, self.game.combo)
                                if not hasattr(self.game, 'style_points'):
                                    self.game.style_points = 0
                                c = self.game.combo
                                self.game.style_rank = "S" if c >= 10 else ("A" if c >= 7 else ("B" if c >= 5 else ("C" if c >= 3 else "D")))
                                mult = 1.0
                                sr = getattr(self.game, 'style_rank', 'D')
                                if sr == "S": mult = 2.0
                                elif sr == "A": mult = 1.5
                                elif sr == "B": mult = 1.2
                                self.game.style_points += int(10 * mult)
                                self.game.score += int(10 * self.game.combo * getattr(self.game, 'exp_multiplier', 1) * mult)
                                if hasattr(self.game, 'coins'):
                                    self.game.coins += int(1 * getattr(self.game, 'coin_multiplier', 1))
                                if hasattr(self.game, 'enemies_killed'):
                                    self.game.enemies_killed += 1
                                if hasattr(self.game, 'enemies_killed_this_level'):
                                    self.game.enemies_killed_this_level += 1
                                for _ in range(10):
                                    p = Particle(enemy.rect.centerx, enemy.rect.centery, RED, 'explosion')
                                    self.game.particles.append(p)
                                if random.random() < 0.3:
                                    pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport', 'plasma', 'speed_boost', 'multishot', 'grenade', 'nuke', 'extra_life'])
                                    spawn_x = max(50, min(SCREEN_WIDTH - 50, enemy.rect.centerx))
                                    spawn_y = max(50, min(SCREEN_HEIGHT - 50, enemy.rect.centery))
                                    pu = PowerUp(spawn_x, spawn_y, pu_type, self.game)
                                    self.game.all_sprites.add(pu)
                                    self.game.powerups.add(pu)
                                if getattr(self.game, 'explosion_sound', None):
                                    self.game.explosion_sound.play()
        
        if self.rect.left > SCREEN_WIDTH:
            self.kill()

class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y, game=None):
        super().__init__()
        self.game = game
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
    def __init__(self, x, y, game=None):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.timer = 120  # 2 seconds

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            # Explode - larger blast radius (200 instead of 100)
            blast_radius = 200
            
            # Damage enemies (but not bosses)
            for e in list(self.game.enemies):
                if not hasattr(e, 'is_boss') or not e.is_boss:  # Don't damage bosses
                    if math.hypot(e.rect.centerx - self.rect.centerx, e.rect.centery - self.rect.centery) < blast_radius:
                        damage = self.game.calculate_damage(1, 'bomb')
                        e.health -= damage
                        if hasattr(self, "game") and self.game and hasattr(self.game, "spawn_damage_number"):
                            self.game.spawn_damage_number(e.rect.centerx, e.rect.centery - 12, damage, False)
                        if e.health <= 0:
                            if self.game.session:
                                self.game.session.handle_enemy_death(e)
                            else:
                                e.kill()
                                self.game.combo_timer = 0
                                self.game.combo += 1
                                if not hasattr(self.game, 'max_combo'):
                                    self.game.max_combo = 0
                                self.game.max_combo = max(self.game.max_combo, self.game.combo)
                                if not hasattr(self.game, 'style_points'):
                                    self.game.style_points = 0
                                c = self.game.combo
                                self.game.style_rank = "S" if c >= 10 else ("A" if c >= 7 else ("B" if c >= 5 else ("C" if c >= 3 else "D")))
                                mult = 1.0
                                sr = getattr(self.game, 'style_rank', 'D')
                                if sr == "S": mult = 2.0
                                elif sr == "A": mult = 1.5
                                elif sr == "B": mult = 1.2
                                self.game.style_points += int(10 * mult)
                                self.game.score += int(10 * self.game.combo * getattr(self.game, 'exp_multiplier', 1) * mult)
                                if hasattr(self.game, 'coins'):
                                    self.game.coins += int(1 * getattr(self.game, 'coin_multiplier', 1))
                                if hasattr(self.game, 'enemies_killed'):
                                    self.game.enemies_killed += 1
                                if hasattr(self.game, 'enemies_killed_this_level'):
                                    self.game.enemies_killed_this_level += 1
                                for _ in range(10):
                                    p = Particle(e.rect.centerx, e.rect.centery, RED, 'explosion')
                                    self.game.particles.append(p)
                                if random.random() < 0.3:
                                    pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport', 'plasma', 'speed_boost', 'multishot', 'grenade', 'nuke', 'extra_life'])
                                    spawn_x = max(50, min(SCREEN_WIDTH - 50, e.rect.centerx))
                                    spawn_y = max(50, min(SCREEN_HEIGHT - 50, e.rect.centery))
                                    pu = PowerUp(spawn_x, spawn_y, pu_type, self.game)
                                    self.game.all_sprites.add(pu)
                                    self.game.powerups.add(pu)
                                if getattr(self.game, 'explosion_sound', None):
                                    self.game.explosion_sound.play()
            
            # Damage asteroids
            for ast in self.game.asteroids:
                if math.hypot(ast.rect.centerx - self.rect.centerx, ast.rect.centery - self.rect.centery) < blast_radius:
                    ast.kill()
                    # Explosion particles for asteroids
                    for _ in range(5):
                        p = Particle(ast.rect.centerx, ast.rect.centery, BROWN)
                        self.game.particles.append(p)
                    # Bonus score and coins for destroyed asteroids
                    self.game.score += 10
                    self.game.coins += 1  # Earn 1 coin per asteroid destroyed
            
            # More explosion particles for larger blast
            for _ in range(30):
                p = Particle(self.rect.centerx + random.randint(-blast_radius//2, blast_radius//2), 
                           self.rect.centery + random.randint(-blast_radius//2, blast_radius//2), RED)
                self.game.particles.append(p)
            self.game.shake_timer = 15
            self.game.shake_intensity = 8
            self.kill()

class Plasma(pygame.sprite.Sprite):
    def __init__(self, x, y, game=None, freezing=False):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((12, 7))  # Slightly larger
        if freezing:
            self.image.fill((0, 255, 255))  # Cyan for freezing plasma
        else:
            self.image.fill((0, 255, 255))  # Cyan
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.centery = y
        self.speed = 12
        self.vel_x = self.speed
        self.vel_y = 0
        self.trail_timer = 0
        self.has_exploded = False
        self.freezing = freezing

    def update(self):
        if not self.has_exploded:
            self.rect.x += self.vel_x
            self.trail_timer += 1
            if self.trail_timer > 5:
                p = Particle(self.rect.centerx, self.rect.centery, (0, 255, 255))
                self.game.particles.append(p)
                self.trail_timer = 0
            if self.rect.left > SCREEN_WIDTH:
                self.kill()
        else:
            # Explosion animation
            self.trail_timer += 1
            if self.trail_timer > 10:
                self.kill()
    
    def explode(self):
        """Plasma explodes on impact with area damage"""
        if not self.has_exploded:
            self.has_exploded = True
            blast_radius = 60  # Area damage radius
            
            # Damage all enemies in blast radius
            for enemy in list(self.game.enemies):
                if math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery) < blast_radius:
                    damage = self.game.calculate_damage(2, 'plasma')
                    enemy.health -= damage
                    if hasattr(self, 'freezing') and self.freezing:
                        enemy.frozen_timer = 300
                        enemy.frozen = True
                    if enemy.health <= 0:
                        if self.game.session:
                            self.game.session.handle_enemy_death(enemy)
                        else:
                            enemy.kill()
                            self.game.combo_timer = 0
                            self.game.combo += 1
                            if not hasattr(self.game, 'max_combo'):
                                self.game.max_combo = 0
                            self.game.max_combo = max(self.game.max_combo, self.game.combo)
                            if not hasattr(self.game, 'style_points'):
                                self.game.style_points = 0
                            c = self.game.combo
                            self.game.style_rank = "S" if c >= 10 else ("A" if c >= 7 else ("B" if c >= 5 else ("C" if c >= 3 else "D")))
                            mult = 1.0
                            sr = getattr(self.game, 'style_rank', 'D')
                            if sr == "S": mult = 2.0
                            elif sr == "A": mult = 1.5
                            elif sr == "B": mult = 1.2
                            self.game.style_points += int(10 * mult)
                            self.game.score += int(10 * self.game.combo * getattr(self.game, 'exp_multiplier', 1) * mult)
                            if hasattr(self.game, 'coins'):
                                self.game.coins += int(1 * getattr(self.game, 'coin_multiplier', 1))
                            if hasattr(self.game, 'enemies_killed'):
                                self.game.enemies_killed += 1
                            if hasattr(self.game, 'enemies_killed_this_level'):
                                self.game.enemies_killed_this_level += 1
                            for _ in range(10):
                                p = Particle(enemy.rect.centerx, enemy.rect.centery, (0, 255, 255), 'explosion')
                                self.game.particles.append(p)
                            if random.random() < 0.3:
                                pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport', 'plasma', 'speed_boost', 'multishot', 'grenade', 'nuke', 'extra_life'])
                                spawn_x = max(50, min(SCREEN_WIDTH - 50, enemy.rect.centerx))
                                spawn_y = max(50, min(SCREEN_HEIGHT - 50, enemy.rect.centery))
                                pu = PowerUp(spawn_x, spawn_y, pu_type, self.game)
                                self.game.all_sprites.add(pu)
                                self.game.powerups.add(pu)
                            if getattr(self.game, 'explosion_sound', None):
                                self.game.explosion_sound.play()
            
            # Visual explosion effect
            for _ in range(15):
                p = Particle(self.rect.centerx + random.randint(-blast_radius//2, blast_radius//2), 
                           self.rect.centery + random.randint(-blast_radius//2, blast_radius//2), (0, 255, 255))
                self.game.particles.append(p)
            
            self.game.shake_timer = 8
            self.game.shake_intensity = 4

class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, angle=0, game=None, homing=False):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((15, 15))
        self.image.fill((0, 128, 0))  # Dark green
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 8
        self.vel_x = self.speed * math.cos(math.radians(angle))
        self.vel_y = self.speed * math.sin(math.radians(angle))
        self.timer = 180  # 3 seconds
        self.bounces = 3
        self.homing = homing

    def update(self):
        if self.homing:
            # Homing logic for grenades
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
                # Slower turning for grenades
                turn_speed = 2
                if abs(angle_diff) < turn_speed:
                    current_angle = target_angle
                else:
                    current_angle += turn_speed if angle_diff > 0 else -turn_speed
                current_angle = current_angle % 360
                speed = math.hypot(self.vel_x, self.vel_y)
                self.vel_x = speed * math.cos(math.radians(current_angle))
                self.vel_y = speed * math.sin(math.radians(current_angle))
        
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.vel_y += 0.5  # Gravity
        # Bounce off edges
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.vel_x = -self.vel_x
            self.bounces -= 1
        if self.rect.top < 0 or self.rect.bottom > SCREEN_HEIGHT:
            self.vel_y = -self.vel_y
            self.bounces -= 1
        
        # Check for enemy collision - explode on impact
        enemy_hit = pygame.sprite.spritecollideany(self, self.game.enemies)
        if enemy_hit:
            # Explode immediately on enemy contact
            self.explode()
            return
        
        self.timer -= 1
        if self.timer <= 0 or self.bounces <= 0:
            self.explode()

    def explode(self):
        # Explode - damage enemies in radius
        for e in list(self.game.enemies):
            if math.hypot(e.rect.centerx - self.rect.centerx, e.rect.centery - self.rect.centery) < 80:
                damage = self.game.calculate_damage(2, 'grenade')
                e.health -= damage
                if hasattr(self, "game") and self.game and hasattr(self.game, "spawn_damage_number"):
                    self.game.spawn_damage_number(e.rect.centerx, e.rect.centery - 12, damage, False)
                if e.health <= 0:
                    if self.game.session:
                        self.game.session.handle_enemy_death(e)
                    else:
                        e.kill()
                        self.game.combo_timer = 0
                        self.game.combo += 1
                        if not hasattr(self.game, 'max_combo'):
                            self.game.max_combo = 0
                        self.game.max_combo = max(self.game.max_combo, self.game.combo)
                        if not hasattr(self.game, 'style_points'):
                            self.game.style_points = 0
                        c = self.game.combo
                        self.game.style_rank = "S" if c >= 10 else ("A" if c >= 7 else ("B" if c >= 5 else ("C" if c >= 3 else "D")))
                        mult = 1.0
                        sr = getattr(self.game, 'style_rank', 'D')
                        if sr == "S": mult = 2.0
                        elif sr == "A": mult = 1.5
                        elif sr == "B": mult = 1.2
                        self.game.style_points += int(10 * mult)
                        self.game.score += int(10 * self.game.combo * getattr(self.game, 'exp_multiplier', 1) * mult)
                        if hasattr(self.game, 'coins'):
                            self.game.coins += int(1 * getattr(self.game, 'coin_multiplier', 1))
                        if hasattr(self.game, 'enemies_killed'):
                            self.game.enemies_killed += 1
                        if hasattr(self.game, 'enemies_killed_this_level'):
                            self.game.enemies_killed_this_level += 1
                        for _ in range(10):
                            p = Particle(e.rect.centerx, e.rect.centery, (0, 128, 0), 'explosion')
                            self.game.particles.append(p)
                        if random.random() < 0.3:
                            pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport', 'plasma', 'speed_boost', 'multishot', 'grenade', 'nuke', 'extra_life'])
                            spawn_x = max(50, min(SCREEN_WIDTH - 50, e.rect.centerx))
                            spawn_y = max(50, min(SCREEN_HEIGHT - 50, e.rect.centery))
                            pu = PowerUp(spawn_x, spawn_y, pu_type, self.game)
                            self.game.all_sprites.add(pu)
                            self.game.powerups.add(pu)
                        if getattr(self.game, 'explosion_sound', None):
                            self.game.explosion_sound.play()
        # Grenade explosion particles
        for _ in range(15):
            p = Particle(self.rect.centerx, self.rect.centery, (0, 128, 0))
            self.game.particles.append(p)
        self.game.shake_timer = 10
        self.game.shake_intensity = 5
        self.kill()

class ShotgunBullet(Bullet):
    """Shotgun spread bullet"""
    def __init__(self, x, y, angle=0, homing=False, is_enemy=False, game=None, speed=12):
        super().__init__(x, y, angle, homing, is_enemy, game, speed)
        self.image = pygame.Surface((8, 6))
        self.image.fill(RED if is_enemy else ORANGE)
        self.damage = 0.5  # Less damage per pellet

class Flamethrower(Bullet):
    """Flamethrower projectile with area damage"""
    def __init__(self, x, y, angle=0, homing=False, is_enemy=False, game=None, speed=8):
        super().__init__(x, y, angle, homing, is_enemy, game, speed)
        self.image = pygame.Surface((12, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, RED if is_enemy else ORANGE, (0, 0, 12, 8))
        self.damage = 0.3
        self.lifetime = 30  # Short lifetime

    def update(self):
        super().update()
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

        # Damage nearby enemies
        for enemy in list(self.game.enemies):
            if math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery) < 20:
                damage = self.game.calculate_damage(self.damage, 'flamethrower')
                enemy.health -= damage
                if hasattr(self, "game") and self.game and hasattr(self.game, "spawn_damage_number"):
                    self.game.spawn_damage_number(enemy.rect.centerx, enemy.rect.centery - 12, damage, False)
                if enemy.health <= 0:
                    if self.game.session:
                        self.game.session.handle_enemy_death(enemy)
                    else:
                        enemy.kill()
                        self.game.combo_timer = 0
                        self.game.combo += 1
                        if not hasattr(self.game, 'max_combo'):
                            self.game.max_combo = 0
                        self.game.max_combo = max(self.game.max_combo, self.game.combo)
                        if not hasattr(self.game, 'style_points'):
                            self.game.style_points = 0
                        c = self.game.combo
                        self.game.style_rank = "S" if c >= 10 else ("A" if c >= 7 else ("B" if c >= 5 else ("C" if c >= 3 else "D")))
                        mult = 1.0
                        sr = getattr(self.game, 'style_rank', 'D')
                        if sr == "S": mult = 2.0
                        elif sr == "A": mult = 1.5
                        elif sr == "B": mult = 1.2
                        self.game.style_points += int(10 * mult)
                        self.game.score += int(10 * self.game.combo * getattr(self.game, 'exp_multiplier', 1) * mult)
                        if hasattr(self.game, 'coins'):
                            self.game.coins += int(1 * getattr(self.game, 'coin_multiplier', 1))
                        if hasattr(self.game, 'enemies_killed'):
                            self.game.enemies_killed += 1
                        if hasattr(self.game, 'enemies_killed_this_level'):
                            self.game.enemies_killed_this_level += 1
                        for _ in range(10):
                            p = Particle(enemy.rect.centerx, enemy.rect.centery, RED, 'explosion')
                            self.game.particles.append(p)
                        if random.random() < 0.3:
                            pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport', 'plasma', 'speed_boost', 'multishot', 'grenade', 'nuke', 'extra_life'])
                            spawn_x = max(50, min(SCREEN_WIDTH - 50, enemy.rect.centerx))
                            spawn_y = max(50, min(SCREEN_HEIGHT - 50, enemy.rect.centery))
                            pu = PowerUp(spawn_x, spawn_y, pu_type, self.game)
                            self.game.all_sprites.add(pu)
                            self.game.powerups.add(pu)
                        if getattr(self.game, 'explosion_sound', None):
                            self.game.explosion_sound.play()

class Lightning(Laser):
    """Lightning weapon that chains between enemies"""
    def __init__(self, x, y, angle=0, homing=False, is_enemy=False, game=None, speed=20):
        super().__init__(x, y, angle, homing, is_enemy, game, speed)
        self.image = pygame.Surface((4, 20), pygame.SRCALPHA)
        pygame.draw.line(self.image, CYAN, (2, 0), (2, 20), 4)
        self.damage = 1.5
        self.chain_count = 3
        self.chain_range = 80

    def update(self):
        super().update()

        # Chain to nearby enemies
        if self.chain_count > 0:
            closest_enemy = None
            min_dist = float('inf')
            for enemy in self.game.enemies:
                if enemy != getattr(self, 'last_hit', None):
                    dist = math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
                    if dist < min_dist and dist <= self.chain_range:
                        min_dist = dist
                        closest_enemy = enemy

            if closest_enemy:
                # Create chain lightning
                chain_lightning = Lightning(closest_enemy.rect.centerx, closest_enemy.rect.centery,
                                          self.angle, False, False, self.game, self.speed)
                chain_lightning.chain_count = self.chain_count - 1
                chain_lightning.last_hit = closest_enemy
                self.game.bullets.add(chain_lightning)
                _ld = self.game.calculate_damage(self.damage, 'lightning')
                closest_enemy.health -= _ld
                if hasattr(self.game, 'spawn_damage_number'):
                    self.game.spawn_damage_number(closest_enemy.rect.centerx, closest_enemy.rect.centery - 12, _ld, False)

class BlackHole(Bomb):
    """Black hole that pulls in enemies"""
    def __init__(self, x, y, angle=0, homing=False, is_enemy=False, game=None, speed=6):
        super().__init__(x, y, angle, homing, is_enemy, game, speed)
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PURPLE, (15, 15), 15)
        pygame.draw.circle(self.image, BLACK, (15, 15), 8)
        self.pull_strength = 2
        self.lifetime = 180  # 3 seconds

    def update(self):
        super().update()
        self.lifetime -= 1

        if self.lifetime <= 0:
            self.kill()
            return

        # Pull nearby enemies
        for enemy in self.game.enemies:
            dx = self.rect.centerx - enemy.rect.centerx
            dy = self.rect.centery - enemy.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 100 and dist > 0:
                pull_x = (dx / dist) * self.pull_strength
                pull_y = (dy / dist) * self.pull_strength
                enemy.rect.x += pull_x
                enemy.rect.y += pull_y

class FreezeBeam(Laser):
    """Freeze beam that slows enemies"""
    def __init__(self, x, y, angle=0, homing=False, is_enemy=False, game=None, speed=15):
        super().__init__(x, y, angle, homing, is_enemy, game, speed)
        self.image = pygame.Surface((6, 25), pygame.SRCALPHA)
        pygame.draw.line(self.image, CYAN, (3, 0), (3, 25), 6)
        self.damage = 0.8
        self.freeze_duration = 60  # 1 second freeze


class RemoteBullet(pygame.sprite.Sprite):
    """Bullet from another player - for visual representation only"""
    def __init__(self, x, y, vel_x, vel_y, angle=0, homing=False, is_enemy=False, bullet_type="Bullet"):
        super().__init__()
        self.image = pygame.Surface((10, 5))
        # Color based on type: red for enemies, orange for homing, yellow for normal
        if is_enemy:
            self.image.fill(RED)
        elif homing:
            self.image.fill(ORANGE)
        else:
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.angle = angle
        self.homing = homing
        self.is_enemy = is_enemy
        self.bullet_type = bullet_type
        self.lifetime = 300  # 5 seconds max lifetime

    def update(self):
        # Move the bullet
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Remove if off screen or lifetime expired
        self.lifetime -= 1
        if self.lifetime <= 0 or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class KamikazeBullet(Bullet):
    def __init__(self, x, y, angle=0, game=None, speed=18):
        super().__init__(x, y, angle, False, False, game, speed)
        # Override color to purple/magenta for kamikaze bullets
        self.image.fill(MAGENTA)


class Railgun(Laser):
    """Slow-firing, high-damage piercing rail (registered in registries for shop/player). Creative: slow speed=6, high dmg=4, long pierce=5, bright trail."""
    def __init__(self, x, y, game=None):
        super().__init__(x, y, game)
        # override for rail properties after super (Laser hardcodes speed/vel/pierce)
        self.image = pygame.Surface((14, 5), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (180, 200, 255), (0, 0, 14, 5))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 6  # slow
        self.vel_x = self.speed
        self.vel_y = 0
        self.damage = 4.0
        self.pierce_count = 0
        self.max_pierce = 5
        self.weapon_type = 'railgun'

    def update(self):
        super().update()
        # creative extra bright trail particles
        if self.game and random.random() < 0.4:
            p = Particle(self.rect.centerx, self.rect.centery, (200, 220, 255), 'smoke')
            if hasattr(self.game, 'session') and self.game.session:
                self.game.session.particles.append(p)
            else:
                self.game.particles.append(p)