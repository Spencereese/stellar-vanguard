import pygame
import math
import random
from config import BLUE, SCREEN_WIDTH, SCREEN_HEIGHT, WEAPON_SHOTGUN, WEAPON_FLAMETHROWER, WEAPON_LIGHTNING, WEAPON_BLACKHOLE, WEAPON_FREEZE, WEAPON_RAILGUN
from projectiles import Bullet, Laser, Missile, Plasma, Grenade, ShotgunBullet, Flamethrower, Lightning, BlackHole, FreezeBeam, PiercingBullet, KamikazeBullet, Railgun
from utils import load_image_with_fallback, get_asset_manager

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        
        # Try to load player image, fallback to enhanced drawing
        def draw_player(surface):
            # Clear surface with transparency
            surface.fill((0, 0, 0, 0))
            
            # Main body - sleek spaceship design
            body_color = (100, 150, 255)  # Bright blue
            accent_color = (150, 200, 255)  # Lighter blue
            engine_color = (255, 100, 100)  # Red-orange for engines
            
            # Main hull - aerodynamic shape
            hull_points = [(5, 45), (25, 5), (45, 45), (25, 35)]
            pygame.draw.polygon(surface, body_color, hull_points)
            
            # Cockpit canopy
            canopy_points = [(20, 15), (30, 15), (28, 25), (22, 25)]
            pygame.draw.polygon(surface, (200, 220, 255, 180), canopy_points)
            pygame.draw.polygon(surface, accent_color, canopy_points, 1)
            
            # Wing details
            pygame.draw.polygon(surface, accent_color, [(10, 35), (15, 25), (20, 35)])
            pygame.draw.polygon(surface, accent_color, [(30, 35), (35, 25), (40, 35)])
            
            # Engine exhaust ports
            pygame.draw.rect(surface, engine_color, (8, 42, 6, 8))
            pygame.draw.rect(surface, engine_color, (36, 42, 6, 8))
            
            # Engine glow effects
            pygame.draw.rect(surface, (255, 150, 150), (9, 46, 4, 4))
            pygame.draw.rect(surface, (255, 150, 150), (37, 46, 4, 4))
            
            # Weapon ports
            pygame.draw.rect(surface, (255, 255, 100), (23, 40, 4, 6))
            
            # Armor plating details
            pygame.draw.line(surface, accent_color, (15, 30), (35, 30), 2)
            pygame.draw.line(surface, accent_color, (20, 20), (30, 20), 1)
        
        # Use game.assets when available (PR1+), fall back to module helper for compat.
        assets = getattr(self.game, 'assets', None) or get_asset_manager()
        self.image = assets.load_image('player.png', (94, 56), draw_player)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 4  # Start in middle of left side
        self.rect.centery = SCREEN_HEIGHT // 2  # Start in middle vertically
        
        # Create a separate hitbox that's skinnier than the visual sprite
        # Cut top and bottom 25% off the hitbox (use middle 50% of height)
        self.hitbox = pygame.Rect(0, 0, self.rect.width, int(self.rect.height * 0.5))
        self.hitbox.centerx = self.rect.centerx
        self.hitbox.centery = self.rect.centery
        self.speed = self.game.player_speed
        self.lives = 3 + self.game.extra_lives
        self.active_powerups = set()  # Changed from single power_up to set of active powerups
        self.powerup_timers = {}  # Changed from single power_timer to dict of timers
        self.shield = False
        self.shield_timer = 0
        self.ammo = self.game.max_ammo
        self.energy = self.game.max_ammo  # Energy replaces ammo
        self.energy_regen_rate = 0.5  # Energy per frame
        self.max_energy = self.game.max_ammo
        self.bombs = 0
        self.missile_count = 0
        self.shield_duration = self.game.shield_duration
        self.invincibility = False
        self.invincibility_timer = 0
        self.weapon = 'normal'
        self.weapon_timer = 0
        self.max_health = self.game.max_health
        self.health = self.max_health
        self.dash_cooldown = 0
        self.dash_speed = self.speed * 3
        self.dash_duration = 10  # frames
        self.dashing = False
        self.dash_timer = 0
        self.speed_multiplier = 1.0
        self.change_x = 0
        self.change_y = 0
        # For live animation on upgraded art (bank lean + thrust pulse)
        self._base_image = None
        self._visual_lean = 0.0
        self._visual_scale = 1.0

    def update(self):
        # During death animation, just handle visual effects, no movement
        if self.game.death_animation_timer > 0:
            # Maybe add some visual effect here later
            return
            
        keys = pygame.key.get_pressed()
        # Movement
        if self.game.joystick:
            # Use analog sticks
            self.rect.x += self.change_x
            self.rect.y += self.change_y
        else:
            # Use keyboard
            effective_speed = getattr(self, 'speed', 5) * getattr(self, 'speed_multiplier', 1.0)
            self.change_x = 0
            self.change_y = 0
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.rect.left > 0:
                self.rect.x -= effective_speed
                self.change_x = -effective_speed
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.rect.right < SCREEN_WIDTH:
                self.rect.x += effective_speed
                self.change_x = effective_speed
            if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.rect.top > 0:
                self.rect.y -= effective_speed
                self.change_y = -effective_speed
            if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.rect.bottom < SCREEN_HEIGHT:
                self.rect.y += effective_speed
                self.change_y = effective_speed
        # Clamp position
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - self.rect.height))
        
        # Update hitbox position to match rect
        self.hitbox.centerx = self.rect.centerx
        self.hitbox.centery = self.rect.centery

        # --- Technically impressive engine thrust trail (always when moving) ---
        speed_sq = (self.change_x or 0)**2 + (self.change_y or 0)**2
        if speed_sq > 0.5 or (hasattr(self, 'dashing') and self.dashing):
            from particles import emit_thrust
            # Emit from approximate engine ports (rear of ship)
            ex = self.rect.centerx - 18
            ey = self.rect.centery + random.randint(-4, 4)
            vx = getattr(self, 'change_x', 0) or 0
            vy = getattr(self, 'change_y', 0) or 0
            emit_thrust(self.game.particles, ex, ey, vx, vy, count=2 if not getattr(self,'dashing',False) else 5)

        # Live animation on the (upgraded v4 or procedural) ship image: banking lean when moving vertically + scale pulse on boost/dash.
        # This makes even static PNG assets feel fully animated and responsive.
        try:
            if self._base_image is None:
                self._base_image = self.image.copy()
            lean = getattr(self, '_visual_lean', 0.0) * 0.65 + float(getattr(self, 'change_y', 0) or 0) * -0.55
            self._visual_lean = lean
            boost = 1.0 + (0.09 if getattr(self, 'dashing', False) else 0.025 if abs(getattr(self, 'change_x', 0) or 0) > 1.5 else 0.0)
            self._visual_scale = boost
            if abs(lean) > 0.8 or self._visual_scale > 1.01:
                transformed = pygame.transform.rotozoom(self._base_image, lean * 0.55, self._visual_scale)
                old_center = self.rect.center
                self.image = transformed
                self.rect = self.image.get_rect(center=old_center)
                self.hitbox.center = self.rect.center
        except Exception:
            pass
        # Dash logic
        if keys[pygame.K_LSHIFT] and self.dash_cooldown == 0 and not self.dashing:
            self.dashing = True
            self.dash_timer = self.dash_duration
            self.dash_cooldown = 120  # 2 seconds cooldown
        if self.dashing:
            dx = self.change_x
            dy = self.change_y
            if self.game.joystick:
                if dx != 0 or dy != 0:
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        dx /= dist
                        dy /= dist
            else:
                dx = 0
                dy = 0
                if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -1
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = 1
                if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -1
                if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = 1
                if dx != 0 or dy != 0:
                    dist = math.hypot(dx, dy)
                    dx /= dist
                    dy /= dist
            if dx != 0 or dy != 0:
                self.rect.x += dx * self.dash_speed
                self.rect.y += dy * self.dash_speed
                # Clamp position
                self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
                self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - self.rect.height))
                # Add spark particle trail
                from particles import Particle
                p = Particle(self.rect.centerx, self.rect.centery, BLUE, 'spark')
                self.game.particles.append(p)
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        # Power-ups now run on ammo consumption rather than timers
        # Shield now lasts until it takes a hit (no timer deactivation)
        if self.shield_timer > 0:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield = False
                if 'shield' in self.active_powerups:
                    self.active_powerups.discard('shield')
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
        else:
            self.invincibility = False
        if self.game.freeze_timer > 0:
            self.game.freeze_timer -= 1
            
        # Decrement powerup timers and remove expired powerups
        expired_powerups = []
        for powerup, timer in self.powerup_timers.items():
            self.powerup_timers[powerup] -= 1
            if self.powerup_timers[powerup] <= 0:
                expired_powerups.append(powerup)
        for powerup in expired_powerups:
            self.active_powerups.discard(powerup)
            del self.powerup_timers[powerup]
            # Handle powerup expiration effects
            if powerup == 'speed_boost':
                self.speed_multiplier = 1.0
                self.dash_speed = getattr(self, 'speed', 5) * 3

        # Energy regeneration
        if self.energy < self.max_energy:
            self.energy = min(self.energy + self.energy_regen_rate, self.max_energy)

    def shoot(self):
        # Check if current weapon has enough energy, otherwise switch to normal
        if self.weapon == WEAPON_SHOTGUN and self.energy < 3:
            self.weapon = 'normal'
        elif self.weapon == WEAPON_FLAMETHROWER and self.energy < 1:
            self.weapon = 'normal'
        elif self.weapon == WEAPON_LIGHTNING and self.energy < 4:
            self.weapon = 'normal'
        elif self.weapon == WEAPON_BLACKHOLE and self.energy < 5:
            self.weapon = 'normal'
        elif self.weapon == WEAPON_FREEZE and self.energy < 2:
            self.weapon = 'normal'
        elif self.weapon == WEAPON_RAILGUN and self.energy < 5:
            self.weapon = 'normal'
        
        if self.energy > 0 or self.weapon == 'normal':
            # Muzzle flash + impressive FX at business end of ship (technically rich)
            try:
                from particles import emit_muzzle, emit_thrust
                mx = self.rect.right + 4
                my = self.rect.centery + random.randint(-2, 2)
                emit_muzzle(self.game.particles, mx, my, count=3)
                # small backward kick particles for weight
                emit_thrust(self.game.particles, self.rect.centerx - 8, self.rect.centery, -3, 0, count=1)
            except Exception:
                pass

            # Check for kamikaze powerup - overrides normal shooting
            if 'kamikaze' in self.active_powerups:
                if self.energy >= 2:
                    kamikaze_bullet = KamikazeBullet(self.rect.right, self.rect.centery, game=self.game)
                    self.game.all_sprites.add(kamikaze_bullet)
                    self.game.bullets.add(kamikaze_bullet)
                    self.game.bullets_fired += 1
                    self.energy -= 2
                    # Remove kamikaze powerup after use (one-shot effect)
                    self.active_powerups.discard('kamikaze')
                    if 'kamikaze' in self.powerup_timers:
                        del self.powerup_timers['kamikaze']
                else:
                    # Not enough energy, fall back to normal weapon
                    bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                    self.game.all_sprites.add(bullet)
                    self.game.bullets.add(bullet)
                    self.game.bullets_fired += 1
                    self.energy -= 1
            # Handle different weapon types
            if self.weapon == WEAPON_SHOTGUN:
                if self.energy >= 3:
                    for angle in [-15, -5, 0, 5, 15]:
                        bullet = ShotgunBullet(self.rect.right, self.rect.centery, angle, game=self.game)
                        self.game.all_sprites.add(bullet)
                        self.game.bullets.add(bullet)
                        self.game.bullets_fired += 1
                    self.energy -= 3
            elif self.weapon == WEAPON_FLAMETHROWER:
                if self.energy >= 1:
                    flame = Flamethrower(self.rect.right, self.rect.centery, game=self.game)
                    self.game.all_sprites.add(flame)
                    self.game.bullets.add(flame)
                    self.game.bullets_fired += 1
                    self.energy -= 1
            elif self.weapon == WEAPON_LIGHTNING:
                if self.energy >= 4:
                    lightning = Lightning(self.rect.right, self.rect.centery, game=self.game)
                    self.game.all_sprites.add(lightning)
                    self.game.bullets.add(lightning)
                    self.game.bullets_fired += 1
                    self.energy -= 4
            elif self.weapon == WEAPON_BLACKHOLE:
                if self.energy >= 5:
                    blackhole = BlackHole(self.rect.right, self.rect.centery, game=self.game)
                    self.game.all_sprites.add(blackhole)
                    self.game.bombs.add(blackhole)
                    self.game.bullets_fired += 1
                    self.energy -= 5
            elif self.weapon == WEAPON_FREEZE:
                if self.energy >= 2:
                    freeze_beam = FreezeBeam(self.rect.right, self.rect.centery, game=self.game)
                    self.game.all_sprites.add(freeze_beam)
                    self.game.bullets.add(freeze_beam)
                    self.game.bullets_fired += 1
                    self.energy -= 2
            elif self.weapon == WEAPON_RAILGUN:
                if self.energy >= 5:
                    rail = Railgun(self.rect.right, self.rect.centery, game=self.game)
                    self.game.all_sprites.add(rail)
                    self.game.bullets.add(rail)
                    self.game.bullets_fired += 1
                    self.energy -= 5
            else:
                # Default weapon logic with power-ups - now supports synergies
                weapon_powerups = {'rapid', 'spread', 'laser', 'homing', 'plasma', 'multishot', 'grenade'}
                active_weapon_powerups = set()
                for powerup in weapon_powerups:
                    if powerup in self.active_powerups:
                        active_weapon_powerups.add(powerup)
                
                # Check for synergies and apply them
                if 'homing' in active_weapon_powerups and 'grenade' in active_weapon_powerups:
                    # Homing Grenade synergy
                    if self.energy >= 2:
                        grenade = Grenade(self.rect.right, self.rect.centery, angle=-45, game=self.game, homing=True)
                        self.game.all_sprites.add(grenade)
                        self.game.grenades.add(grenade)
                        self.energy -= 2
                    else:
                        # Fallback to normal weapon if not enough energy
                        bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                        self.game.all_sprites.add(bullet)
                        self.game.bullets.add(bullet)
                        self.game.bullets_fired += 1
                        self.energy -= 1
                elif 'homing' in active_weapon_powerups and 'spread' in active_weapon_powerups:
                    # Homing Spread synergy
                    if self.energy >= 2:
                        for angle in [-20, -10, 0, 10, 20]:
                            bullet = Bullet(self.rect.right, self.rect.centery, angle, game=self.game, homing=True)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                        self.energy -= 2
                    else:
                        # Fallback to normal weapon if not enough energy
                        bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                        self.game.all_sprites.add(bullet)
                        self.game.bullets.add(bullet)
                        self.game.bullets_fired += 1
                        self.energy -= 1
                elif 'homing' in active_weapon_powerups and 'multishot' in active_weapon_powerups:
                    # Homing Multishot synergy
                    if self.energy >= 4:
                        angles = [-45, -30, -15, 0, 15, 30, 45]
                        for angle in angles:
                            bullet = Bullet(self.rect.right, self.rect.centery, angle, game=self.game, homing=True)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                        self.energy -= 4
                    else:
                        # Fallback to normal weapon if not enough energy
                        bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                        self.game.all_sprites.add(bullet)
                        self.game.bullets.add(bullet)
                        self.game.bullets_fired += 1
                        self.energy -= 1
                elif 'plasma' in active_weapon_powerups and 'freeze' in self.active_powerups:
                    # Freezing Plasma synergy (freeze is a utility powerup, not weapon)
                    if self.energy >= 1:
                        plasma = Plasma(self.rect.right, self.rect.centery, game=self.game, freezing=True)
                        self.game.all_sprites.add(plasma)
                        self.game.plasmas.add(plasma)
                        self.game.bullets_fired += 1
                        self.energy -= 1
                elif active_weapon_powerups:
                    # Single weapon powerup logic (no synergy)
                    active_weapon_powerup = next(iter(active_weapon_powerups))  # Get first one
                    
                    if active_weapon_powerup == 'rapid':
                        if self.energy >= 4:
                            for i in range(4):
                                bullet = Bullet(self.rect.right, self.rect.centery + i*5 - 7.5, game=self.game)
                                self.game.all_sprites.add(bullet)
                                self.game.bullets.add(bullet)
                                self.game.bullets_fired += 1
                            self.energy -= 4
                        else:
                            # Fallback to normal weapon if not enough energy for rapid fire
                            bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                            self.energy -= 1
                    elif active_weapon_powerup == 'spread':
                        if self.energy >= 2:
                            for angle in [-20, -10, 0, 10, 20]:
                                bullet = Bullet(self.rect.right, self.rect.centery, angle, game=self.game, spread_homing=True)
                                self.game.all_sprites.add(bullet)
                                self.game.bullets.add(bullet)
                                self.game.bullets_fired += 1
                            self.energy -= 2
                        else:
                            # Fallback to normal weapon if not enough energy for spread
                            bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                            self.energy -= 1
                    elif active_weapon_powerup == 'laser':
                        if self.energy >= 4:
                            bullet = Laser(self.rect.right, self.rect.centery, game=self.game)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                            self.energy -= 4
                        else:
                            # Fallback to normal weapon if not enough energy for laser
                            bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                            self.energy -= 1
                    elif active_weapon_powerup == 'homing':
                        if self.energy >= 1:
                            bullet = Bullet(self.rect.right, self.rect.centery, homing=True, game=self.game)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                            self.energy -= 1
                        else:
                            # Fallback to normal weapon if not enough energy for homing
                            bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                            self.energy -= 1
                    elif active_weapon_powerup == 'plasma':
                        if self.energy >= 1:
                            plasma = Plasma(self.rect.right, self.rect.centery, game=self.game)
                            self.game.all_sprites.add(plasma)
                            self.game.plasmas.add(plasma)
                            self.game.bullets_fired += 1
                            self.energy -= 1
                    elif active_weapon_powerup == 'multishot':
                        if self.energy >= 4:
                            angles = [-45, -30, -15, 0, 15, 30, 45]
                            for i, angle in enumerate(angles):
                                # Outer bullets (first 2 and last 2) pierce through enemies
                                if i < 2 or i > 4:  # -45, -30, 30, 45 degrees
                                    bullet = PiercingBullet(self.rect.right, self.rect.centery, angle, game=self.game)
                                else:  # Center bullets (-15, 0, 15 degrees) are normal
                                    bullet = Bullet(self.rect.right, self.rect.centery, angle, game=self.game)
                                self.game.all_sprites.add(bullet)
                                self.game.bullets.add(bullet)
                                self.game.bullets_fired += 1
                            self.energy -= 4
                        else:
                            # Fallback to normal weapon if not enough energy for multishot
                            bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                            self.energy -= 1
                    elif active_weapon_powerup == 'grenade':
                        if self.energy >= 2:
                            grenade = Grenade(self.rect.right, self.rect.centery, angle=-45, game=self.game)  # Throw up and to the right
                            self.game.all_sprites.add(grenade)
                            self.game.grenades.add(grenade)
                            self.energy -= 2
                        else:
                            # Fallback to normal weapon if not enough energy for grenade
                            bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
                            self.game.bullets_fired += 1
                            self.energy -= 1
                else:
                    # Basic normal weapon - always available
                    bullet = Bullet(self.rect.right, self.rect.centery, game=self.game)
                    self.game.all_sprites.add(bullet)
                    self.game.bullets.add(bullet)
                    self.game.bullets_fired += 1
                    self.energy -= 1

            if self.game.shoot_sound:
                self.game.shoot_sound.play()

            # Polish: small muzzle flash / smoke particles on every shot for animation juice
            if hasattr(self.game, 'particles'):
                for _ in range(3):
                    from particles import Particle
                    px = self.rect.right + random.randint(0, 8)
                    py = self.rect.centery + random.randint(-3, 3)
                    p = Particle(px, py, (255, 220, 100), 'fire', random.randint(2,4))
                    p.vel_x = random.randint(2, 6)
                    p.life = random.randint(8, 15)
                    self.game.particles.append(p)

    def fire_missile(self):
        if self.missile_count > 0:
            self.missile_count -= 1
            missile = Missile(self.rect.right, self.rect.centery, game=self.game)
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