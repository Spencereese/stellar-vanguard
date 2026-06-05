import pygame
import random
import math
from config import *
from projectiles import Bullet
from particles import Particle
from utils import load_image_with_fallback, get_asset_manager

enemy_pools = {
    1: ['normal'] * 6 + ['fast'] * 3 + ['big'] * 1,
    2: ['normal'] * 4 + ['fast'] * 2 + ['big'] * 1 + ['shooter'] * 2 + ['kamikaze'] * 1,
    3: ['normal'] * 3 + ['fast'] * 2 + ['big'] * 1 + ['shooter'] * 2 + ['kamikaze'] * 1 + ['elite'] * 1,
    4: ['normal'] * 2 + ['fast'] * 2 + ['big'] * 1 + ['shooter'] * 2 + ['kamikaze'] * 1 + ['elite'] * 1 + ['healer'] * 1,
    5: ['fast'] * 2 + ['big'] * 1 + ['shooter'] * 2 + ['kamikaze'] * 1 + ['elite'] * 1 + ['healer'] * 1 + ['teleporter'] * 1,
    6: ['tank'] * 2 + ['turret'] * 2 + ['bomber'] * 1 + ['zigzag'] * 1 + ['drone'] * 1 + ['shooter'] * 1 + ['kamikaze'] * 1 + ['swarmer'] * 2 + ['elite'] * 1 + ['healer'] * 1,
    7: ['tank'] * 2 + ['turret'] * 2 + ['bomber'] * 2 + ['zigzag'] * 2 + ['drone'] * 2 + ['shooter'] * 1 + ['kamikaze'] * 1 + ['big'] * 1 + ['fast'] * 1 + ['normal'] * 1 + ['swarmer'] * 2 + ['elite'] * 2 + ['healer'] * 1 + ['teleporter'] * 1,
    8: ['swarmer'] * 3 + ['elite'] * 2 + ['healer'] * 2 + ['teleporter'] * 1 + ['tank'] * 1 + ['turret'] * 1 + ['bomber'] * 1,
    9: ['swarmer'] * 4 + ['elite'] * 3 + ['healer'] * 2 + ['teleporter'] * 2 + ['tank'] * 1 + ['bomber'] * 1,
    10: ['swarmer'] * 5 + ['elite'] * 3 + ['healer'] * 3 + ['teleporter'] * 2 + ['tank'] * 2 + ['bomber'] * 1,
}

class Enemy(pygame.sprite.Sprite):
    def __init__(self, game, enemy_type=None):
        super().__init__()
        self.game = game
        # PR10/creative registries support (see registries.py)
        try:
            from registries import ENEMY_REGISTRY, get_enhanced_enemy_pool
            pool = enemy_pools.get(min(self.game.wave, MAX_LEVELS), enemy_pools[MAX_LEVELS])
            extra = get_enhanced_enemy_pool(self.game.wave)
            full_pool = pool + extra
            self.type = enemy_type if enemy_type else random.choice(full_pool)
            if self.type in ENEMY_REGISTRY:
                # Let the registry factory take over for new types (cloaker, splitter, ...)
                # We still set self.type so old code doesn't break
                pass
        except Exception:
            self.type = enemy_type if enemy_type else random.choice(enemy_pools.get(min(self.game.wave, MAX_LEVELS), enemy_pools[MAX_LEVELS]))
        speed_mult = 1.0
        if self.game.difficulty == 'easy':
            speed_mult = 0.8
        elif self.game.difficulty == 'hard':
            speed_mult = 1.2
        if self.type == 'normal':
            def draw_normal(surface):
                # Clear surface
                surface.fill((0, 0, 0, 0))
                
                # Main body - angular fighter design
                body_color = (200, 50, 50)  # Red
                accent_color = (255, 100, 100)  # Light red
                
                # Main hull
                hull_points = [(5, 40), (35, 5), (65, 40), (35, 30)]
                pygame.draw.polygon(surface, body_color, hull_points)
                
                # Wing structures
                pygame.draw.polygon(surface, accent_color, [(15, 25), (25, 15), (35, 25)])
                pygame.draw.polygon(surface, accent_color, [(35, 25), (45, 15), (55, 25)])
                
                # Cockpit
                pygame.draw.ellipse(surface, (255, 255, 255), (28, 10, 14, 8))
                pygame.draw.ellipse(surface, accent_color, (28, 10, 14, 8), 1)
                
                # Engine details
                pygame.draw.rect(surface, (150, 150, 150), (30, 35, 10, 8))
                pygame.draw.rect(surface, (255, 150, 150), (32, 38, 6, 3))
                
                # Weapon systems
                pygame.draw.rect(surface, (255, 255, 0), (32, 42, 6, 4))
            assets = getattr(self.game, 'assets', None) or get_asset_manager()
            self.image = assets.load_image('enemy_normal.png', (75, 56), draw_normal)
            self.health = 1
            self.speed = random.randint(2, 5) * speed_mult
        elif self.type == 'fast':
            def draw_fast(surface):
                # Clear surface
                surface.fill((0, 0, 0, 0))
                
                # Sleek interceptor design
                body_color = (200, 200, 50)  # Yellow
                accent_color = (255, 255, 100)  # Light yellow
                
                # Aerodynamic hull
                hull_points = [(3, 35), (30, 3), (57, 35), (30, 25)]
                pygame.draw.polygon(surface, body_color, hull_points)
                
                # Forward wings
                pygame.draw.polygon(surface, accent_color, [(12, 20), (20, 10), (28, 20)])
                pygame.draw.polygon(surface, accent_color, [(32, 20), (40, 10), (48, 20)])
                
                # Engine nacelles
                pygame.draw.ellipse(surface, (150, 150, 150), (8, 30, 8, 12))
                pygame.draw.ellipse(surface, (150, 150, 150), (45, 30, 8, 12))
                
                # Engine trails
                pygame.draw.ellipse(surface, (255, 200, 100), (10, 35, 4, 8))
                pygame.draw.ellipse(surface, (255, 200, 100), (47, 35, 4, 8))
                
                # Cockpit
                pygame.draw.ellipse(surface, (255, 255, 255), (25, 8, 10, 6))
                pygame.draw.ellipse(surface, accent_color, (25, 8, 10, 6), 1)
            self.image = load_image_with_fallback('enemy_fast.png', (65, 46), draw_fast)
            self.health = 1
            self.speed = random.randint(6, 9) * speed_mult
        elif self.type == 'big':
            def draw_big(surface):
                # Clear surface
                surface.fill((0, 0, 0, 0))
                
                # Heavy bomber design
                body_color = (150, 50, 150)  # Purple
                accent_color = (200, 100, 200)  # Light purple
                
                # Main hull - larger and more armored
                hull_points = [(5, 70), (50, 5), (95, 70), (50, 50)]
                pygame.draw.polygon(surface, body_color, hull_points)
                
                # Armor plating
                pygame.draw.polygon(surface, accent_color, [(20, 40), (35, 25), (50, 40)])
                pygame.draw.polygon(surface, accent_color, [(50, 40), (65, 25), (80, 40)])
                
                # Wing hardpoints
                pygame.draw.rect(surface, (100, 100, 100), (15, 45, 8, 15))
                pygame.draw.rect(surface, (100, 100, 100), (85, 45, 8, 15))
                
                # Cockpit
                pygame.draw.ellipse(surface, (255, 255, 255), (42, 15, 16, 10))
                pygame.draw.ellipse(surface, accent_color, (42, 15, 16, 10), 1)
                
                # Engine blocks
                pygame.draw.rect(surface, (120, 120, 120), (25, 65, 12, 10))
                pygame.draw.rect(surface, (120, 120, 120), (75, 65, 12, 10))
                
                # Engine glow
                pygame.draw.rect(surface, (255, 150, 150), (27, 68, 8, 5))
                pygame.draw.rect(surface, (255, 150, 150), (77, 68, 8, 5))
            self.image = load_image_with_fallback('enemy_big.png', (112, 83), draw_big)
            self.health = 2
            self.speed = random.randint(2, 4) * speed_mult
        elif self.type == 'shooter':
            def draw_shooter(surface):
                pygame.draw.polygon(surface, GREEN, [(0, 35), (22, 0), (45, 35), (22, 25)])
            self.image = load_image_with_fallback('enemy_shooter.png', (67, 52), draw_shooter)
            self.health = 1
            self.speed = random.randint(2, 5) * speed_mult
            self.shoot_timer = 0
        elif self.type == 'kamikaze':
            def draw_kamikaze(surface):
                pygame.draw.polygon(surface, ORANGE, [(0, 25), (15, 0), (30, 25), (15, 15)])
            self.image = load_image_with_fallback('enemy_kamikaze.png', (56, 46), draw_kamikaze)
            self.health = 1
            self.speed = random.randint(4, 7) * speed_mult
        elif self.type == 'tank':
            def draw_tank(surface):
                pygame.draw.polygon(surface, GRAY, [(0, 50), (35, 0), (70, 50), (35, 30)])
            self.image = load_image_with_fallback('enemy_tank.png', (131, 94), draw_tank)
            self.health = 8  # Increased from 3 to 8 for more challenge
            self.speed = random.randint(1, 3) * speed_mult
            self.shoot_timer = 0
        elif self.type == 'turret':
            def draw_turret(surface):
                pygame.draw.circle(surface, GREEN, (20, 20), 20)
            self.image = load_image_with_fallback('enemy_turret.png', (75, 75), draw_turret)
            self.health = 3
            self.speed = 0
            self.shoot_timer = 0
        elif self.type == 'bomber':
            def draw_bomber(surface):
                pygame.draw.polygon(surface, BROWN, [(0, 40), (25, 0), (50, 40), (25, 25)])
            self.image = load_image_with_fallback('enemy_bomber.png', (94, 75), draw_bomber)
            self.health = 1
            self.speed = random.randint(2, 4) * speed_mult
            self.drop_timer = 0
        elif self.type == 'drone':
            def draw_drone(surface):
                pygame.draw.polygon(surface, CYAN, [(0, 20), (12, 0), (25, 20), (12, 10)])
            self.image = load_image_with_fallback('enemy_drone.png', (46, 38), draw_drone)
            self.health = 1
            self.speed = random.randint(5, 8) * speed_mult
        elif self.type == 'zigzag':
            def draw_zigzag(surface):
                pygame.draw.polygon(surface, MAGENTA, [(0, 30), (20, 0), (40, 30), (20, 20)])
            self.image = load_image_with_fallback('enemy_zigzag.png', (75, 56), draw_zigzag)
            self.health = 1
            self.speed = random.randint(3, 5) * speed_mult
        elif self.type == ENEMY_SWARMER:
            # Placeholder - will be overridden by Swarmer class
            def draw_swarmer(surface):
                pygame.draw.circle(surface, CYAN, (10, 10), 10)
            self.image = load_image_with_fallback('enemy_swarmer.png', (38, 38), draw_swarmer)
            self.health = 1
            self.speed = random.randint(8, 12) * speed_mult
        elif self.type == ENEMY_ELITE:
            # Placeholder - will be overridden by Elite class
            def draw_elite(surface):
                pygame.draw.polygon(surface, GOLD, [(0, 40), (25, 0), (50, 40), (25, 25)])
            self.image = load_image_with_fallback('enemy_elite.png', (94, 75), draw_elite)
            self.health = 3
            self.speed = random.randint(3, 6) * speed_mult
            self.shoot_timer = 0
        elif self.type == ENEMY_HEALER:
            # Placeholder - will be overridden by Healer class
            def draw_healer(surface):
                pygame.draw.polygon(surface, GREEN, [(0, 35), (22, 0), (45, 35), (22, 25)])
                pygame.draw.circle(surface, LIGHT_BLUE, (22, 17), 25, 2)
            self.image = load_image_with_fallback('enemy_healer.png', (84, 65), draw_healer)
            self.health = 2
            self.speed = random.randint(2, 4) * speed_mult
        elif self.type == ENEMY_TELEPORTER:
            # Placeholder - will be overridden by Teleporter class
            def draw_teleporter(surface):
                pygame.draw.polygon(surface, MAGENTA, [(0, 30), (20, 0), (40, 30), (20, 20)])
            self.image = load_image_with_fallback('enemy_teleporter.png', (75, 56), draw_teleporter)
            self.health = 2
            self.speed = random.randint(4, 7) * speed_mult
        if self.type != 'turret':
            self.health = int(self.health * (1 + (self.game.wave - 1) * 0.1))
            self.speed *= (1 + (self.game.wave - 1) * 0.05)
        self.rect = self.image.get_rect()
        if self.type == 'turret':
            self.rect.x = SCREEN_WIDTH - 50
            self.rect.y = random.randint(50, SCREEN_HEIGHT - 50)
        else:
            self.rect.x = SCREEN_WIDTH + random.randint(0, 300)
            if self.type == 'bomber':
                # Bomber enemies only spawn in the top 1/3 of the screen
                self.rect.y = random.randint(0, SCREEN_HEIGHT // 3 - self.rect.height)
            else:
                self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)

    def update(self):
        if self.game.freeze_timer > 0:
            return
        # Skip general leftward movement for kamikaze enemies - they have their own movement logic
        if self.type != 'kamikaze':
            self.rect.x -= self.speed
        if self.type == 'shooter':
            self.shoot_timer += 1
            if self.shoot_timer > 180:  # Shoot every 3 seconds
                enemy_bullet = Bullet(self.rect.left, self.rect.centery, 180, is_enemy=True, game=self.game)
                self.game.all_sprites.add(enemy_bullet)
                self.game.enemy_bullets.add(enemy_bullet)
                self.shoot_timer = 0
        elif self.type == 'kamikaze' or hasattr(self, 'kamikaze') and self.kamikaze:
            # Kamikaze behavior - target either player or another enemy
            if hasattr(self, 'kamikaze') and self.kamikaze:
                # This enemy was made kamikaze by a kamikaze bullet - target closest enemy
                if self.kamikaze_target is None or not self.kamikaze_target.alive():
                    # Find closest enemy (excluding self)
                    closest_enemy = None
                    min_dist = float('inf')
                    for enemy in self.game.enemies:
                        if enemy != self:
                            dist = math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
                            if dist < min_dist:
                                min_dist = dist
                                closest_enemy = enemy
                    self.kamikaze_target = closest_enemy
                
                if self.kamikaze_target and self.kamikaze_target.alive():
                    # Target the enemy
                    dx = self.kamikaze_target.rect.centerx - self.rect.centerx
                    dy = self.kamikaze_target.rect.centery - self.rect.centery
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        self.rect.x += (dx / dist) * self.speed
                        self.rect.y += (dy / dist) * self.speed
                else:
                    # No target found, fall back to player targeting
                    dx = self.game.player.rect.centerx - self.rect.centerx
                    dy = self.game.player.rect.centery - self.rect.centery
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        self.rect.x += (dx / dist) * self.speed
                        self.rect.y += (dy / dist) * self.speed
            else:
                # Normal kamikaze enemy - target player
                dx = self.game.player.rect.centerx - self.rect.centerx
                dy = self.game.player.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    # Kamikaze enemies prioritize chasing the player over the general leftward flow
                    self.rect.x += (dx / dist) * self.speed
                    self.rect.y += (dy / dist) * self.speed
        elif self.type == 'tank':
            self.shoot_timer += 1
            if self.shoot_timer > 240:
                for angle in [-30, 0, 30]:
                    enemy_bullet = Bullet(self.rect.left, self.rect.centery, angle + 180, is_enemy=True, game=self.game)
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
                enemy_bullet = Bullet(self.rect.centerx, self.rect.centery, angle, is_enemy=True, game=self.game)
                self.game.all_sprites.add(enemy_bullet)
                self.game.enemy_bullets.add(enemy_bullet)
                self.shoot_timer = 0
        elif self.type == 'bomber':
            self.drop_timer += 1
            if self.drop_timer > 200:
                bomb = Bullet(self.rect.centerx, self.rect.bottom, 90, is_enemy=True, speed=3, game=self.game)
                self.game.all_sprites.add(bomb)
                self.game.enemy_bullets.add(bomb)
                self.drop_timer = 0
        elif self.type == 'drone':
            dx = self.game.player.rect.centerx - self.rect.centerx
            dy = self.game.player.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.rect.x += (dx / dist) * self.speed
                self.rect.y += (dy / dist) * self.speed
        elif self.type == 'zigzag':
            self.rect.y += math.sin(self.rect.x * 0.02) * 3
            self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - self.rect.height))
        if self.rect.right < 0:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        def draw_boss(surface):
            pygame.draw.polygon(surface, RED, [(0, 60), (40, 0), (80, 60), (40, 40)])
        self.image = load_image_with_fallback('boss.png', (150, 113), draw_boss)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH + 100
        self.rect.centery = SCREEN_HEIGHT // 2
        self.speed = 1
        # Significantly increased health for more challenge
        self.speed = 1
        # Significantly increased health for epic boss battles
        base_health = 50 + (self.game.wave * 10)  # Much higher base health
        self.health = int(base_health * (0.8 if self.game.difficulty == 'easy' else 1.2 if self.game.difficulty == 'hard' else 1.0))
        self.shoot_timer = 0
        self.special_timer = 0
        self.phase = 1
        self.max_health = self.health
        self.y_speed = 2
        self.direction = 1
        self.charge_timer = 0
        self.is_charging = False
        self.charge_speed = 8
        self.return_to_right = False
        self.is_boss = True  # Mark as boss so bombs don't damage it
        self.defeated = False  # Track if boss was properly defeated

    def update(self):
        if self.game.freeze_timer > 0:
            return

        # Boss stays on the right side unless charging
        if not self.is_charging and not self.return_to_right:
            # Keep boss on the right side of screen
            target_x = SCREEN_WIDTH - 100
            if self.rect.centerx > target_x:
                self.rect.x -= self.speed
            elif self.rect.centerx < target_x - 50:  # Allow some movement left but not too far
                self.rect.x += self.speed * 0.5
        elif self.is_charging:
            # Charge attack - move quickly left but don't go off-screen completely
            self.rect.x -= self.charge_speed
            self.charge_timer -= 1
            if self.charge_timer <= 0 or self.rect.right < 50:  # Stop charge if off-screen or timer expires
                self.is_charging = False
                self.return_to_right = True
        elif self.return_to_right:
            # Return to right side after charge
            target_x = SCREEN_WIDTH - 100
            if self.rect.centerx < target_x:
                self.rect.x += self.speed * 2  # Return faster
            else:
                self.return_to_right = False

        # Vertical movement (bouncing)
        self.rect.y += self.y_speed * self.direction
        if self.rect.top < 0 or self.rect.bottom > SCREEN_HEIGHT:
            self.direction *= -1

        # Phase changes
        if self.health <= self.max_health * 0.6 and self.phase == 1:
            self.phase = 2
            self.speed = 2
            self.shoot_timer = 0
        elif self.health <= self.max_health * 0.3 and self.phase == 2:
            self.phase = 3
            self.speed = 3
            self.shoot_timer = 0
        self.shoot_timer += 1
        self.special_timer += 1

        # Regular shooting
        shoot_interval = 120 - (self.phase - 1) * 30  # Phase 1: 120, 2: 90, 3: 60
        if self.shoot_timer > shoot_interval:
            enemy_bullet = Bullet(self.rect.left, self.rect.centery, 180, is_enemy=True, game=self.game)
            self.game.all_sprites.add(enemy_bullet)
            self.game.enemy_bullets.add(enemy_bullet)
            if self.phase >= 2:
                enemy_bullet2 = Bullet(self.rect.left, self.rect.centery - 20, 180, is_enemy=True, game=self.game)
                self.game.all_sprites.add(enemy_bullet2)
                self.game.enemy_bullets.add(enemy_bullet2)
            if self.phase == 3:
                enemy_bullet3 = Bullet(self.rect.left, self.rect.centery + 20, 180, is_enemy=True, game=self.game)
                self.game.all_sprites.add(enemy_bullet3)
                self.game.enemy_bullets.add(enemy_bullet3)
            self.shoot_timer = 0

        # Special attack: Spawn minions or charge attack
        special_interval = 300 - (self.phase - 1) * 60  # Phase 1: 300, 2: 240, 3: 180
        if self.special_timer > special_interval:
            if self.phase >= 2 and random.random() < 0.5:  # 50% chance for charge in phase 2+
                self.charge_attack()
            else:
                self.special_attack()
            self.special_timer = 0

        # Check if boss is defeated
        if self.health <= 0 and not self.defeated:
            self.defeated = True
            # Create explosion effect
            for _ in range(50):
                p = Particle(self.rect.centerx + random.randint(-50, 50), 
                           self.rect.centery + random.randint(-50, 50), RED, 'explosion')
                self.game.particles.append(p)
            # Set flags so Victory offers post-boss shop/claim reward, and future bosses can spawn
            # (decouples from level_data timing; covers both campaign level bosses and wave-triggered bosses)
            try:
                if hasattr(self.game, 'just_defeated_boss'):
                    self.game.just_defeated_boss = True
                if hasattr(self.game, 'boss_spawned'):
                    self.game.boss_spawned = False
            except Exception:
                pass
            # Kill boss after explosion effect
            self.kill()

        if self.rect.right < -200:  # Much further off-screen before killing
            self.kill()
            
    def special_attack(self):
        """Boss special attack - spawns themed enemies and projectiles"""
        if self.phase == 1:
            # Phase 1: Spawn elite guards
            for i in range(2):
                enemy = Elite(self.game)
                enemy.rect.x = self.rect.centerx + random.randint(-100, 100)
                enemy.rect.y = self.rect.centery + random.randint(-50, 50)
                self.game.enemies.add(enemy)
                self.game.all_sprites.add(enemy)
        elif self.phase == 2:
            # Phase 2: Spawn healer support and teleporters
            healer = Healer(self.game)
            healer.rect.x = self.rect.centerx - 80
            healer.rect.y = self.rect.centery
            self.game.enemies.add(healer)
            self.game.all_sprites.add(healer)
            
            teleporter = Teleporter(self.game)
            teleporter.rect.x = self.rect.centerx + 80
            teleporter.rect.y = self.rect.centery
            self.game.enemies.add(teleporter)
            self.game.all_sprites.add(teleporter)
        else:
            # Phase 3: Spawn swarmers and screen-wide attack
            for i in range(4):
                swarmer = Swarmer(self.game)
                swarmer.rect.x = self.rect.centerx + random.randint(-150, 150)
                swarmer.rect.y = self.rect.centery + random.randint(-100, 100)
                self.game.enemies.add(swarmer)
                self.game.all_sprites.add(swarmer)
            
            # Screen-wide bullet barrage
            for y in range(50, SCREEN_HEIGHT, 60):
                enemy_bullet = Bullet(self.rect.left, y, 180, is_enemy=True, game=self.game)
                self.game.all_sprites.add(enemy_bullet)
                self.game.enemy_bullets.add(enemy_bullet)
    
    def charge_attack(self):
        """Boss charge attack - rushes toward player then returns"""
        self.is_charging = True
        self.charge_timer = 120  # 2 seconds of charging
        # Visual effect for charge start
        for _ in range(15):
            p = Particle(self.rect.centerx, self.rect.centery, RED, 'explosion')
            self.game.particles.append(p)

class Swarmer(Enemy):
    """Fast, small enemy that moves in patterns"""
    def __init__(self, game):
        super().__init__(game, ENEMY_SWARMER)
        self.type = ENEMY_SWARMER
        def draw_swarmer(surface):
            pygame.draw.circle(surface, CYAN, (10, 10), 10)
        self.image = load_image_with_fallback('enemy_swarmer.png', (38, 38), draw_swarmer)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(0, 100)
        self.rect.y = random.randint(50, SCREEN_HEIGHT - 50)
        self.health = 1
        self.speed = random.randint(8, 12)
        self.angle = random.uniform(0, 2 * math.pi)
        self.wave_amplitude = random.randint(20, 40)
        self.wave_frequency = random.uniform(0.05, 0.1)
        self.base_y = self.rect.y

    def update(self):
        if self.game.freeze_timer > 0:
            return
        self.angle += self.wave_frequency
        self.rect.x -= self.speed
        self.rect.y = self.base_y + math.sin(self.angle) * self.wave_amplitude

        if self.rect.right < 0 or self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0:
            self.kill()

class Elite(Enemy):
    """Stronger enemy with shield"""
    def __init__(self, game):
        super().__init__(game, ENEMY_ELITE)
        self.type = ENEMY_ELITE
        def draw_elite(surface):
            pygame.draw.polygon(surface, GOLD, [(0, 40), (25, 0), (50, 40), (25, 25)])
        self.image = load_image_with_fallback('enemy_elite.png', (94, 75), draw_elite)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(0, 100)
        self.rect.y = random.randint(50, SCREEN_HEIGHT - 50)
        self.health = 3
        self.max_health = 3
        self.speed = random.randint(3, 6)
        self.shield = 2
        self.shoot_timer = 0

    def update(self):
        if self.game.freeze_timer > 0:
            return
        self.rect.x -= self.speed

        # Shooting logic
        self.shoot_timer += 1
        if self.shoot_timer >= 90:  # Shoot every 1.5 seconds
            bullet = Bullet(self.rect.left, self.rect.centery, angle=180, is_enemy=True)
            self.game.enemy_bullets.add(bullet)
            self.shoot_timer = 0

        if self.rect.right < 0:
            self.kill()

class Healer(Enemy):
    """Enemy that heals nearby enemies"""
    def __init__(self, game):
        super().__init__(game, ENEMY_HEALER)
        self.type = ENEMY_HEALER
        def draw_healer(surface):
            pygame.draw.polygon(surface, GREEN, [(0, 35), (22, 0), (45, 35), (22, 25)])
            pygame.draw.circle(surface, LIGHT_BLUE, (22, 17), 25, 2)
        self.image = load_image_with_fallback('enemy_healer.png', (84, 65), draw_healer)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(0, 100)
        self.rect.y = random.randint(50, SCREEN_HEIGHT - 50)
        self.health = 2
        self.speed = random.randint(2, 4)
        self.heal_timer = 0
        self.heal_range = 100

    def update(self):
        if self.game.freeze_timer > 0:
            return
        self.rect.x -= self.speed

        # Healing logic
        self.heal_timer += 1
        if self.heal_timer >= 180:  # Heal every 3 seconds
            for enemy in self.game.enemies:
                if enemy != self and math.hypot(enemy.rect.centerx - self.rect.centerx,
                                              enemy.rect.centery - self.rect.centery) <= self.heal_range:
                    if hasattr(enemy, 'health') and enemy.health < getattr(enemy, 'max_health', enemy.health):
                        enemy.health = min(enemy.health + 1, getattr(enemy, 'max_health', enemy.health))
                        # Create healing particle effect
                        for _ in range(3):
                            particle = Particle(self.rect.centerx, self.rect.centery, GREEN, 20)
                            self.game.particles.append(particle)
            self.heal_timer = 0

        if self.rect.right < 0:
            self.kill()

class Teleporter(Enemy):
    """Enemy that teleports around"""
    def __init__(self, game):
        super().__init__(game, ENEMY_TELEPORTER)
        self.type = ENEMY_TELEPORTER
        def draw_teleporter(surface):
            pygame.draw.polygon(surface, MAGENTA, [(0, 30), (20, 0), (40, 30), (20, 20)])
        self.image = load_image_with_fallback('enemy_teleporter.png', (75, 56), draw_teleporter)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(0, 100)
        self.rect.y = random.randint(50, SCREEN_HEIGHT - 50)
        self.health = 2
        self.speed = random.randint(4, 7)
        self.teleport_timer = 0
        self.teleport_cooldown = 120  # Teleport every 2 seconds

    def update(self):
        if self.game.freeze_timer > 0:
            return

        # Normal movement
        self.rect.x -= self.speed

        # Teleport logic
        self.teleport_timer += 1
        if self.teleport_timer >= self.teleport_cooldown:
            # Create teleport effect
            for _ in range(5):
                particle = Particle(self.rect.centerx, self.rect.centery, MAGENTA, 15)
                self.game.particles.append(particle)

            # Teleport to new position
            self.rect.x = random.randint(SCREEN_WIDTH // 2, SCREEN_WIDTH - 50)
            self.rect.y = random.randint(50, SCREEN_HEIGHT - 50)

            # More teleport particles at new location
            for _ in range(5):
                particle = Particle(self.rect.centerx, self.rect.centery, MAGENTA, 15)
                self.game.particles.append(particle)

            self.teleport_timer = 0

        if self.rect.right < 0:
            self.kill()

def draw_asteroid(surface):
    # Get the size from the surface dimensions
    size = surface.get_width()
    center = size // 2
    radius = size // 2 - 2
    
    # Draw a simple asteroid shape
    pygame.draw.circle(surface, BROWN, (center, center), radius)
    # Add some irregular edges based on size
    detail_size = max(1, size // 10)
    pygame.draw.circle(surface, DARK_RED, (center - radius//2, center - radius//2), detail_size)
    pygame.draw.circle(surface, DARK_RED, (center + radius//2, center - radius//3), detail_size)
    pygame.draw.circle(surface, DARK_RED, (center + radius//3, center + radius//2), detail_size)

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        
        # Randomly choose asteroid size (mostly small)
        size_choice = random.choices(['small', 'medium', 'large'], weights=[70, 25, 5])[0]
        
        if size_choice == 'small':
            self.size = random.randint(20, 35)
            self.health = 1
            self.speed = random.randint(2, 4)
        elif size_choice == 'medium':
            self.size = random.randint(36, 50)
            self.health = 2
            self.speed = random.randint(1, 3)
        else:  # large
            self.size = random.randint(51, 65)
            self.health = 3
            self.speed = random.randint(1, 2)
        
        self.image = load_image_with_fallback('asteroid.png', (self.size, self.size), draw_asteroid)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(0, 300)
        self.rect.y = random.randint(0, SCREEN_HEIGHT - self.size)

    def update(self):
        if self.game.freeze_timer > 0:
            return
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


# === Full creative classes for new registry enemies (PR10/11; proper inheritance vs. monkey-patch factories) ===
class Cloaker(Enemy):
    """Stealthy enemy that phases in/out of visibility (harder to hit when cloaked)."""
    def __init__(self, game, enemy_type=None):
        super().__init__(game, 'normal')  # base as normal, override
        self.type = 'cloaker'
        self.health = 1
        self.speed = 4.0
        self.cloak_timer = 0
        self.cloaked = False
        self.cloak_duration = 45  # frames cloaked
        self.uncloak_duration = 45

    def update(self):
        super().update()
        self.cloak_timer += 1
        if self.cloaked and self.cloak_timer > self.cloak_duration:
            self.cloaked = False
            self.cloak_timer = 0
        elif not self.cloaked and self.cloak_timer > self.uncloak_duration:
            self.cloaked = True
            self.cloak_timer = 0
        # visual alpha for stealth (works on fallback surfaces)
        try:
            alpha = 60 if self.cloaked else 255
            self.image.set_alpha(alpha)
        except:
            pass
        # when cloaked, slightly harder (dodge or speed)
        if self.cloaked:
            self.speed = 5.5
        else:
            self.speed = 4.0

class Splitter(Enemy):
    """Splits into fast children on death (area denial)."""
    def __init__(self, game, enemy_type=None):
        super().__init__(game, 'big')  # tanky base
        self.type = 'splitter'
        self.health = 2
        self.speed = 2.5

    def kill(self):
        # creative: spawn 2-3 fast children at location (use registry or direct for consistency)
        try:
            for _ in range(2):
                child = Enemy(self.game, 'fast')
                child.rect.center = self.rect.center
                if hasattr(self.game, 'session') and self.game.session:
                    self.game.session.enemies.add(child)
                    self.game.session.all_sprites.add(child)
                elif hasattr(self.game, 'enemies'):
                    self.game.enemies.add(child)
                    self.game.all_sprites.add(child)
        except Exception:
            pass
        super().kill()  # do the normal kill after spawns


# Register the full classes (update registries.py to prefer these over _make factories for cleanliness)
try:
    # re-register if registries loaded after
    import registries
    registries.register_enemy('cloaker', lambda g, t=None: Cloaker(g, t), base_health=1, base_speed=4, desc="Phases visibility; evades when cloaked.")
    registries.register_enemy('splitter', lambda g, t=None: Splitter(g, t), base_health=2, base_speed=2.5, desc="Splits on death into fast adds.")
except:
    pass