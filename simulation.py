"""SimulationWorld / PlaySession (PR2 - core of the Stellar Vanguard sequel).

This module is the authoritative owner of live gameplay simulation for v3+.
It was extracted from the monolithic Game class to enable:
- Cleaner separation (Game = coordinator + UI state + persistence + renderer host)
- Easier testing of rules in isolation
- Future extensibility (loadouts, modifiers, style engine, roguelite all plug in here)
- Data-driven content via registries (see content work)

See DESIGN_STELLAR_VANGUARD_v3.md PR2 section for full spec, Concrete Starting Point,
inventory of groups/timers/logic from original game.py, Post-PR2 checkpoint, and
integration notes with PlayingState / level_manager / player.

Creative notes (main + delegated work): Clean private helpers, dt-aware where
possible while preserving original frame-based timers for simplicity during
transition, hooks for new pillars (on_kill for style, apply_loadout_modifiers,
apply_modifier, etc.). All new enemies/weapons from content work should be
spawnable here.

The game must remain runnable after every step of the extraction.
"""

import pygame
import random
import math
from config import *
from particles import Particle
from enemies import Enemy, Boss, Asteroid
from powerups import PowerUp
from projectiles import Bullet, Laser, Missile, Bomb, Plasma, Grenade, PiercingBullet, ShotgunBullet, Flamethrower, Lightning, BlackHole, FreezeBeam, KamikazeBullet  # for type checks in collisions
from modifiers import get_random_modifiers, Modifier
# Particle imported lazily or when needed to avoid circulars during transition
# from particles import Particle


class SimulationWorld:
    """Owns ALL the live simulation state and rules.

    Groups, particles, timers, spawning, collisions, powerups, scoring helpers,
    wave/boss progression, slow/freeze effects, etc. live here.

    Game and states interact via a small, clean API.
    """

    def __init__(self, game, mode=None, upgrades=None):
        self.game = game
        self.mode = mode or getattr(game, 'game_mode', MODE_ARCADE)
        self.upgrades = upgrades or getattr(game, 'upgrades', None)

        # === GROUPS (full inventory from original game.py:172-183 + remote) ===
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.remote_bullets = pygame.sprite.Group()  # MP support
        self.missiles = pygame.sprite.Group()
        self.plasmas = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.grenades = pygame.sprite.Group()
        self.particles = []  # Particle instances (not always sprites)

        # === CORE SIM TIMERS & STATE (from game.py update_game_logic + __init__ timers) ===
        self.enemy_timer = 0
        self.combo_timer = 0
        self.combo = 0
        self.max_combo = 0
        self.style_points = 0
        self.style_rank = "D"  # D, C, B, A, S for creative style system (PR6/7)
        # mirror game.xxx = self.xxx 
        if hasattr(self.game, 'combo'):
            self.game.combo = self.combo
        if hasattr(self.game, 'combo_timer'):
            self.game.combo_timer = self.combo_timer
        if hasattr(self.game, 'max_combo'):
            self.game.max_combo = self.max_combo
        if hasattr(self.game, 'style_points'):
            self.game.style_points = self.style_points
        if hasattr(self.game, 'style_rank'):
            self.game.style_rank = self.style_rank
        self.time_slow_timer = 0
        self.slow_factor = 1.0
        self.freeze_timer = 0
        self.wave = 1
        self.boss_spawned = False
        self.enemies_killed_this_wave = 0   # for level/campaign objectives
        self.score = 0                      # sim can own or mirror; keep in sync with game for now
        self.coins_earned_this_run = 0

        # Player (set after creation; sim drives most of its interactions)
        self.player = None

        # Future pillar hooks (creative extensibility)
        self.active_modifiers = []          # from roguelite PR7
        # clear on reset for new run
        self.current_loadout = None         # from PR6
        self.style_engine = None            # from PR6 combo/style (later)

        # Camera / world bounds (light coupling to level_manager.camera if present)
        self.world_width = SCREEN_WIDTH * 2 if 'SCREEN_WIDTH' in globals() else 1600
        self.world_height = SCREEN_HEIGHT

    # ------------------------------------------------------------------
    # LIFECYCLE & PLAYER
    # ------------------------------------------------------------------
    def set_player(self, player):
        """Attach the player (called by Game after Player(self) creation). Creative: apply default loadout."""
        self.player = player
        if player and player not in self.all_sprites:
            self.all_sprites.add(player)
        try:
            from loadouts import Loadout
            # Prefer an already-selected session loadout (LoadoutSelect -> Playing).
            # Only default to scout when nothing was chosen yet.
            if self.current_loadout is not None:
                self.current_loadout.apply_to_player(player, game=self.game)
            elif player and not getattr(player, 'current_loadout', None):
                ld = Loadout("scout")
                ld.apply_to_player(player, game=self.game)
                self.current_loadout = ld
            elif player and getattr(player, 'current_loadout', None) and self.current_loadout is None:
                self.current_loadout = player.current_loadout
                self.current_loadout.apply_to_player(player, game=self.game)
        except Exception as ex:
            print("Loadout apply note:", ex)  # non-fatal
            pass

    def reset_for_new_run(self, **kwargs):
        """Full clear for new arcade run or new campaign level.
        Called from Game / states when starting fresh.
        """
        self.combo = 0
        self.max_combo = 0
        self.style_points = 0
        self.style_rank = "D"
        self.combo_timer = 0
        self.active_modifiers = []  # clear for new run (PR7/8)
        # R2: keep self.current_loadout (selected in LoadoutSelect) across reset
        for g in (self.all_sprites, self.enemies, self.powerups, self.asteroids,
                  self.enemy_bullets, self.bullets, self.remote_bullets,
                  self.missiles, self.plasmas, self.bombs, self.grenades):
            g.empty()
        self.particles.clear()

        # Clear sim-owned combo/style/rank for full reset (delegated from Game.reset_game)
        self.combo = 0
        self.max_combo = 0
        self.style_points = 0
        self.style_rank = "D"
        self.combo_timer = 0
        # mirror game.xxx = self.xxx at end of reset
        if hasattr(self.game, 'combo'):
            self.game.combo = self.combo
        if hasattr(self.game, 'combo_timer'):
            self.game.combo_timer = self.combo_timer
        if hasattr(self.game, 'max_combo'):
            self.game.max_combo = self.max_combo
        if hasattr(self.game, 'style_rank'):
            self.game.style_rank = self.style_rank
        if hasattr(self.game, 'style_points'):
            self.game.style_points = self.style_points

        self.enemy_timer = 0
        self.time_slow_timer = 0
        self.slow_factor = 1.0
        self.freeze_timer = 0
        self.wave = kwargs.get('wave', 1)
        self.boss_spawned = False
        self.enemies_killed_this_wave = 0
        self.score = kwargs.get('score', 0)
        self.coins_earned_this_run = 0

        # Re-attach player if provided
        if 'player' in kwargs:
            self.set_player(kwargs['player'])
        elif self.player:
            self.all_sprites.add(self.player)

        # Apply any active loadout / modifiers (creative hooks)
        self._apply_loadout_and_modifiers()

        # Hook modifiers (PR7/8): choose 1 random for demo; full choose-1-of-3 in PlayingState
        if not self.active_modifiers:
            try:
                mods = get_random_modifiers(1)
                self.active_modifiers.extend(mods)
                for m in mods:
                    m.apply(self)
            except:
                pass
        # ensure cleared for new runs (called from game reset)
        # (the if above applies for ongoing; for full new run clear before)

    # ------------------------------------------------------------------
    # MAIN UPDATE (the heart - will contain the old update_game_logic body)
    # ------------------------------------------------------------------
    def update(self, dt=1.0 / 60.0):
        """Advance one simulation step. This is what PlayingState calls.

        Creative: dt-aware for future, but many original timers are frame counts.
        We scale the important ones by slow_factor and clamp.
        Currently does real basic work (group updates + particles + timers + simple spawning)
        so the session is not a pure no-op even during transition. Full collision/spawn
        logic will be moved by the PR2 subagent.
        """
        effective_dt = dt * self.slow_factor

        # 1. Update all sprite groups (they have their own .update())
        self.all_sprites.update()
        # Note: many custom projectiles/enemies override update

        # 2. Particles (list-based in v2)
        self._update_particles(effective_dt)

        # 3. Timers (scaled by slow/freeze where appropriate)
        self._update_timers(effective_dt)

        # 4. Spawning (enemies, asteroids, powerups) - basic version now; rich version coming
        self._update_spawning()

        # 5. Collisions (ported and expanded for all weapons/powerups)
        self.handle_collisions()

        # 6. Wave / boss / level progression hooks (stub)
        self._update_progression()

        # 7. Powerup / effect application over time (freeze, slow, etc.)
        self._update_effects()

        # 8. Future pillar updates (style, modifiers, abilities)
        if self.style_engine:
            self.style_engine.update(self, dt)
        for mod in self.active_modifiers:
            if hasattr(mod, 'update'):
                mod.update(self, dt)

        # 9. Cleanup dead things
        self._cleanup()

    # ------------------------------------------------------------------
    # CREATIVE / MOVED HELPERS (stubs that will be filled with real logic from game.py)
    # ------------------------------------------------------------------
    def _update_particles(self, dt):
        """Update and age particles. Original particles were updated in game loop. Creative: hybrid perf LOD cull for high count (PR12)."""
        alive = []
        for p in self.particles:
            if hasattr(p, 'update'):
                p.update()
            # Simple lifetime if present
            if not hasattr(p, 'life') or getattr(p, 'life', 10) > 0:
                alive.append(p)
            # else drop
        self.particles = alive[:PARTICLE_LIMIT] if 'PARTICLE_LIMIT' in globals() else alive[:200]
        # hybrid perf LOD: if too many, cull (simple; real would use fps or distance)
        if len(self.particles) > 80:
            self.particles = self.particles[::2]  # drop half for perf when busy
        if len(self.particles) > 150:
            self.particles = self.particles[::2]

    def _update_timers(self, dt):
        """All the frame counters from original Game. Creative: combo/style decay."""
        # Scale some by slow_factor already applied via effective_dt in caller
        self.enemy_timer += 1
        if self.combo > 0:
            self.combo_timer += 1
            if self.combo_timer > 130:
                self.combo = 0
                self.style_rank = "D"
                self.style_points = 0
                self.combo_timer = 0
                # sync to game for HUD/renderer (prevents desync post-decay) -- mirror game.xxx = self.xxx
                if hasattr(self.game, 'combo'):
                    self.game.combo = self.combo
                if hasattr(self.game, 'style_rank'):
                    self.game.style_rank = self.style_rank
                if hasattr(self.game, 'style_points'):
                    self.game.style_points = self.style_points
                if hasattr(self.game, 'combo_timer'):
                    self.game.combo_timer = self.combo_timer
        else:
            self.combo_timer = 0
        if self.time_slow_timer > 0:
            self.time_slow_timer -= 1
        if self.freeze_timer > 0:
            self.freeze_timer -= 1

    def _update_spawning(self):
        """Spawning logic ported + adapted from game.py ~374 (creative cleanup: use registries where possible, respect modes, add smoke via particles).
        """
        if not self.boss_spawned:
            self.enemy_timer += 1
            if self.game.survival if hasattr(self.game, 'survival') else False:
                spawn_rate = max(10, 45 - (pygame.time.get_ticks() // 30000))
            else:
                spawn_rate = max(20, 60 - self.wave * 5)
            if self.enemy_timer > spawn_rate:
                enemy = self.spawn_enemy()
                if enemy:
                    for _ in range(10):
                        p = Particle(enemy.rect.centerx, enemy.rect.centery, (128,128,128), 'smoke')
                        self.particles.append(p)
                self.enemy_timer = 0
        elif self.boss_spawned:
            self.enemy_timer += 1
            spawn_rate = 90
            if self.enemy_timer > spawn_rate:
                boss_enemy_types = ['tank', 'shooter', 'bomber']
                enemy_type = random.choice(boss_enemy_types)
                enemy = self.spawn_enemy(enemy_type)
                if enemy:
                    for _ in range(10):
                        p = Particle(enemy.rect.centerx, enemy.rect.centery, (128,0,128), 'smoke')
                        self.particles.append(p)
                self.enemy_timer = 0

        # Asteroids
        if not self.boss_spawned and random.random() < 0.02 + self.wave * 0.005:
            try:
                ast = Asteroid(self.game)
                self.all_sprites.add(ast)
                self.asteroids.add(ast)
                for _ in range(5):
                    p = Particle(ast.rect.centerx, ast.rect.centery, (139,69,19), 'smoke')
                    self.particles.append(p)
            except Exception:
                pass

        # Boss trigger (high level, state change may happen via game callback)
        # Improved: also respect campaign boss_fight + progress bar
        triggered = False
        if getattr(self.game, 'boss_fight', False) and not getattr(self.game, 'boss_spawned', False):
            prog = 0.0
            try:
                if hasattr(self.game, 'level_manager') and self.game.level_manager:
                    prog = self.game.level_manager.get_boss_approach()
            except:
                killed = getattr(self.game, 'enemies_killed_this_level', 0)
                req = max(10, getattr(self.game, 'enemies_required', 20))
                prog = min(1.0, killed / float(req))
            if prog >= 0.82:  # close enough per the bar
                triggered = True
        if not triggered and not (getattr(self.game, 'survival', False)) and self.wave > getattr(self.game, 'boss_wave', 3) and self.wave % 3 == 0:
            triggered = True

        if triggered and not getattr(self.game, 'boss_spawned', False):
            if hasattr(self.game, 'change_state'):
                from game_states import BossIncomingState
                self.game.change_state(BossIncomingState(self.game))
            if hasattr(self.game, 'boss_wave'):
                self.game.boss_wave = self.wave

    def spawn_enemy(self, enemy_type=None):
        """Factory using registries if available, else direct. Creative: supports new types from registries.py."""
        if enemy_type is None:
            try:
                from enemies import enemy_pools
                pool = enemy_pools.get(min(self.wave, 10), enemy_pools[10])
                # Mix in registered new types
                try:
                    from registries import get_enhanced_enemy_pool
                    pool = pool + get_enhanced_enemy_pool(self.wave)
                except:
                    pass
                enemy_type = random.choice(pool)
            except:
                enemy_type = 'normal'
        try:
            from registries import ENEMY_REGISTRY, create_enemy_from_registry
            if enemy_type in ENEMY_REGISTRY:
                e = create_enemy_from_registry(self.game, enemy_type)
            else:
                e = Enemy(self.game, enemy_type)
            self.enemies.add(e)
            self.all_sprites.add(e)
            return e
        except Exception as ex:
            print(f"Simulation spawn fallback for {enemy_type}: {ex}")
            return None

    def handle_collisions(self):
        """Ported + creatively refactored collision logic from game.py ~494- (player_hitbox, groupcollides).
        Delegates damage calc, death handling, powerup apply to methods here.
        Supports new registry content. Expanded with more special cases for full feel with all weapons/powerups.
        """
        if not self.player or getattr(self.game, 'death_animation_timer', 0) > 0 or getattr(self.game, 'god_mode', False) or getattr(self.player, 'invincibility', False):
            return

        def player_hitbox_collide(group):
            for sprite in group:
                if getattr(self.player, 'hitbox', self.player.rect).colliderect(sprite.rect):
                    return True
            return False

        # Player hit by enemies/bullets/asteroids
        if player_hitbox_collide(self.enemies) or player_hitbox_collide(self.enemy_bullets) or player_hitbox_collide(self.asteroids):
            if getattr(self.player, 'shield', False):
                self.player.shield = False
                self.player.shield_timer = 0
                self.player.invincibility = True
                self.player.invincibility_timer = 60
                for _ in range(30):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.randint(20, 50)
                    x = self.player.rect.centerx + math.cos(angle) * distance
                    y = self.player.rect.centery + math.sin(angle) * distance
                    p = Particle(x, y, (0,0,255), 'explosion')
                    self.particles.append(p)
                if hasattr(self.game, 'damage_flash_timer'):
                    self.game.damage_flash_timer = 15
            else:
                dmg = 20
                self.player.health -= dmg
                if self.game.game_mode == MODE_CAMPAIGN:
                    self.game.damage_taken_this_level = getattr(self.game, 'damage_taken_this_level', 0) + dmg
                if hasattr(self.game, 'damage_flash_timer'):
                    self.game.damage_flash_timer = 10
                if self.player.health <= 0:
                    for _ in range(80):
                        angle = random.uniform(0, 2 * math.pi)
                        distance = random.randint(5, 80)
                        x = self.player.rect.centerx + math.cos(angle) * distance
                        y = self.player.rect.centery + math.sin(angle) * distance
                        col = random.choice( [(255,0,0), (255,100,0), (255,200,50), (255,255,200)] )
                        p = Particle(x, y, col, 'explosion', random.randint(3,8))
                        p.vel_x *= 1.5
                        p.vel_y *= 1.5
                        self.particles.append(p)
                    self.player.health = self.player.max_health
                    if hasattr(self.game, 'death_animation_timer'):
                        self.game.death_animation_timer = 45  # slightly longer for better anim visibility

        # Bullet-enemy (expanded special cases ported from original for gameplay completeness)
        bullet_hits = pygame.sprite.groupcollide(self.bullets, self.enemies, False, False)
        for bullet, enemy_list in bullet_hits.items():
            if isinstance(bullet, Flamethrower):
                continue  # Flamethrower does its own area damage + deaths in update() to avoid double dmg/death and for bypass consistency with Laser trail/Bomb/etc.
            for enemy in list(enemy_list):
                wtype = getattr(bullet, 'weapon_type', 'bullet')
                dmg = self.calculate_damage(getattr(self.game, 'damage', 1), wtype)
                enemy.health -= dmg
                if enemy.health <= 0:
                    self.handle_enemy_death(enemy)
                if hasattr(bullet, 'pierce_count'):
                    bullet.pierce_count += 1
                    if bullet.pierce_count >= getattr(bullet, 'max_pierce', 1):
                        bullet.kill()
                        break
                else:
                    bullet.kill()
                    break

        # Missile-enemy collisions
        missile_hits = pygame.sprite.groupcollide(self.missiles, self.enemies, True, False)
        for missile, enemy_list in missile_hits.items():
            for enemy in enemy_list:
                dmg = self.calculate_damage(2 * getattr(self.game, 'damage', 1), 'missile')
                enemy.health -= dmg
                if enemy.health <= 0:
                    self.handle_enemy_death(enemy)

        # Additional projectile groups for full port (shotgun, laser, freeze, lightning, grenade, bomb, remote, kamikaze etc)
        # Laser (piercing support via max_pierce on Railgun/Laser subclasses)
        laser_hits = pygame.sprite.groupcollide(self.bullets, self.enemies, False, False)  # bullets include some lasers? separate if needed
        # (note: main bullets loop above already handles Laser pierce via if isinstance in broader sense; keep for coverage)
        for laser, enemy_list in list(laser_hits.items()) if False else []:  # avoid double; main bullet loop covers
            pass

        # Grenades (area on impact)
        grenade_hits = pygame.sprite.groupcollide(self.grenades, self.enemies, True, False)
        for grenade, enemy_list in grenade_hits.items():
            for enemy in enemy_list:
                dmg = self.calculate_damage(3, 'grenade')
                enemy.health -= dmg
                if enemy.health <= 0:
                    self.handle_enemy_death(enemy)

        # Bombs already explode in their class; catch any direct
        bomb_hits = pygame.sprite.groupcollide(self.bombs, self.enemies, False, False)
        for bomb, enemy_list in bomb_hits.items():
            if hasattr(bomb, 'explode'):
                bomb.explode()
            else:
                for e in enemy_list:
                    e.health -= self.calculate_damage(5, 'bomb')
                    if e.health <= 0:
                        self.handle_enemy_death(e)

        # Remote bullets (MP legacy + special)
        remote_hits = pygame.sprite.groupcollide(self.remote_bullets, self.enemies, True, False)
        for rb, el in remote_hits.items():
            for e in el:
                e.health -= self.calculate_damage(1, 'remote')
                if e.health <= 0:
                    self.handle_enemy_death(e)

        # Bullet-asteroid collisions + mineable yield (PR9 creative: resources from destructibles; theme aware)
        asteroid_hits = pygame.sprite.groupcollide(self.bullets, self.asteroids, False, False)
        for bullet, ast_list in asteroid_hits.items():
            if isinstance(bullet, Laser):
                bullet.kill()
                for ast in ast_list:
                    ast.kill()
                    if hasattr(self.game, 'score'):
                        self.game.score += 5
                    if hasattr(self.game, 'coins'):
                        self.game.coins += 1  # mineable yield
                    if random.random() < 0.2:
                        # ammo yield
                        if self.player:
                            self.player.energy = min(self.player.energy + 10, getattr(self.player, 'max_energy', 100))
                    for _ in range(5):
                        p = Particle(ast.rect.centerx, ast.rect.centery, (139,69,19), 'explosion')
                        self.particles.append(p)
            else:
                bullet.kill()
                for ast in ast_list:
                    ast.health -= getattr(self.game, 'damage', 1)
                    if ast.health <= 0:
                        ast.kill()
                        if hasattr(self.game, 'score'):
                            self.game.score += 5
                        if hasattr(self.game, 'coins'):
                            self.game.coins += 1
                        if random.random() < 0.2 and self.player:
                            self.player.energy = min(self.player.energy + 10, getattr(self.player, 'max_energy', 100))
                        for _ in range(5):
                            p = Particle(ast.rect.centerx, ast.rect.centery, (139,69,19), 'explosion')
                            self.particles.append(p)

        # Plasma-enemy collisions -- trigger explode() for proper area blast damage (was previously broken/unused)
        plasma_hits = pygame.sprite.groupcollide(self.plasmas, self.enemies, False, False)
        for plasma, enemy_list in plasma_hits.items():
            if enemy_list and not getattr(plasma, 'has_exploded', False):
                plasma.explode()
                # explode() now uses session.handle_enemy_death for any kills (combo/rank/score consistency); handles freezing inside too
                continue
            # direct fallback (rare)
            for enemy in enemy_list:
                dmg = self.calculate_damage(getattr(self.game, 'damage', 1), 'plasma')
                enemy.health -= dmg
                if hasattr(plasma, 'freezing') and plasma.freezing:
                    enemy.frozen_timer = 300
                    enemy.frozen = True
                if enemy.health <= 0:
                    self.handle_enemy_death(enemy)

        # Powerups - full list ported
        pu_hits = [pu for pu in self.powerups if self.player.hitbox.colliderect(pu.rect)]
        for pu in pu_hits:
            pu.kill()
            # Track for missions / objectives
            if self.game.game_mode == MODE_CAMPAIGN:
                if not hasattr(self.game, 'powerups_collected_this_level'):
                    self.game.powerups_collected_this_level = 0
                self.game.powerups_collected_this_level += 1
            self.apply_powerup(pu)

    def handle_enemy_death(self, enemy):
        """Ported from game.py:816, adapted for session ownership. Creative: uses registries for future drops. Combo/style integrated.
        Authoritative on self.* ; mirror cleanly to game.* at end to avoid desyncs/inflation.
        """
        enemy.kill()
        # self only (no early game. writes; no use of game.combo in calcs)
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self.combo_timer = 0  # reset decay on kill
        # set rank from new combo first (thresholds)
        if self.combo >= 10:
            self.style_rank = "S"
        elif self.combo >= 7:
            self.style_rank = "A"
        elif self.combo >= 5:
            self.style_rank = "B"
        elif self.combo >= 3:
            self.style_rank = "C"
        base_style = 10
        rank_mult = 1.0
        if self.style_rank == "S": rank_mult = 2.0
        elif self.style_rank == "A": rank_mult = 1.5
        elif self.style_rank == "B": rank_mult = 1.2
        self.style_points += int(base_style * rank_mult)
        # Clean mirror to game.* at end (game.xxx = self.xxx)
        if hasattr(self.game, 'combo'):
            self.game.combo = self.combo
        if hasattr(self.game, 'max_combo'):
            self.game.max_combo = self.max_combo
        if hasattr(self.game, 'combo_timer'):
            self.game.combo_timer = self.combo_timer
        if hasattr(self.game, 'style_points'):
            self.game.style_points = self.style_points
        if hasattr(self.game, 'style_rank'):
            self.game.style_rank = self.style_rank
        if hasattr(self.game, 'score'):
            mult = rank_mult
            self.game.score += int(10 * self.combo * getattr(self.game, 'exp_multiplier', 1) * mult)
        if hasattr(self.game, 'coins'):
            self.game.coins += int(1 * getattr(self.game, 'coin_multiplier', 1))
        if hasattr(self.game, 'enemies_killed'):
            self.game.enemies_killed += 1
        if hasattr(self.game, 'enemies_killed_this_level'):
            self.game.enemies_killed_this_level += 1
        # Rich impressive death FX
        try:
            from particles import emit_explosion
            intensity = 1.0 + min(1.0, getattr(enemy, 'health', 1) / 3.0)  # bigger for tankier enemies
            emit_explosion(self.particles, enemy.rect.centerx, enemy.rect.centery, intensity=intensity)
        except Exception:
            for _ in range(10):
                p = Particle(enemy.rect.centerx, enemy.rect.centery, (255,0,0), 'explosion')
                self.particles.append(p)
        if random.random() < 0.3:
            try:
                from powerups import PowerUp
                pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'plasma', 'speed_boost', 'nuke', 'teleport', 'grenade', 'kamikaze', 'multishot', 'extra_life'])
                spawn_x = max(50, min(SCREEN_WIDTH - 50, enemy.rect.centerx))
                spawn_y = max(50, min(SCREEN_HEIGHT - 50, enemy.rect.centery))
                pu = PowerUp(spawn_x, spawn_y, pu_type, self.game)
                self.all_sprites.add(pu)
                self.powerups.add(pu)
            except:
                pass
        if getattr(self.game, 'explosion_sound', None):
            self.game.explosion_sound.play()

    def calculate_damage(self, base_damage, weapon_type=None):
        """Ported from game.py:840, uses game upgrades."""
        dmg = base_damage * getattr(self.game, 'damage', 1) * getattr(self.game, 'weapon_damage', 1)
        if weapon_type:
            multis = {
                'shotgun': getattr(self.game, 'upgrades', None).get('shotgun_damage', 1.0) if getattr(self.game, 'upgrades', None) else 1.0,
                # ... add others as needed
            }
            dmg *= multis.get(weapon_type, 1.0)
        if random.random() < getattr(self.game, 'crit_chance', 0):
            dmg *= getattr(self.game, 'crit_damage', 1.5)
        return dmg



    def create_powerup(self, x, y, ptype=None):
        """Moved powerup drop logic."""
        # from powerups import PowerUp
        # pu = PowerUp(x, y, ptype or random.choice(...))
        # self.powerups.add(pu)
        # self.all_sprites.add(pu)
        pass

    def apply_powerup(self, powerup):
        """Full ported + adapted powerup application from game.py. Sets effects on player/game, triggers particles/sound, handles special like teleport/nuke. Now fully functional: active/timers for timed, shield/health/flag, instant for nuke/teleport/ammo/etc, and delegates deaths for combo/rank/score/particles/sound consistency (no dupes)."""
        player = self.player
        if not player:
            return
        game = self.game
        if powerup.type == 'shield':
            player.shield = True
            duration = getattr(player, 'shield_duration', 300)
            player.shield_timer = duration
            player.active_powerups.add('shield')
            player.powerup_timers['shield'] = duration
            protection_effects = {'invincibility'}  # shield self already added; clear only others
            for effect in protection_effects:
                if effect in player.active_powerups:
                    player.active_powerups.discard(effect)
                    if effect in getattr(player, 'powerup_timers', {}):
                        del player.powerup_timers[effect]
        elif powerup.type == 'invincibility':
            player.invincibility = True
            player.invincibility_timer = 600
            player.active_powerups.add(powerup.type)
            player.powerup_timers[powerup.type] = 600
        elif powerup.type in ('rapid', 'spread', 'laser', 'homing', 'plasma', 'speed_boost', 'multishot', 'grenade', 'kamikaze'):
            player.active_powerups.add(powerup.type)
            player.powerup_timers[powerup.type] = 600
            if powerup.type == 'speed_boost':
                player.speed_multiplier = 1.5
                player.dash_speed = player.speed * 3 * 1.5
        elif powerup.type == 'ammo':
            player.energy = min(player.energy + 30, getattr(player, 'max_energy', 100))
        elif powerup.type == 'bomb':
            player.bombs += 2
        elif powerup.type == 'missile':
            player.missile_count += 10
        elif powerup.type == 'freeze':
            self.freeze_timer = 600
        elif powerup.type == 'health':
            player.health = min(player.health + 25, player.max_health)
        elif powerup.type == 'slow':
            self.time_slow_timer = 600
        elif powerup.type == 'teleport':
            old_x, old_y = player.rect.centerx, player.rect.centery
            player.rect.centerx = random.randint(50, SCREEN_WIDTH - 50)
            player.rect.centery = random.randint(50, SCREEN_HEIGHT - 50)
            blast_radius = 150
            explosion_damage = 50
            if hasattr(game, 'trigger_screen_shake'):
                game.trigger_screen_shake(8, 20)
            for e in list(self.enemies):
                if not getattr(e, 'is_boss', False):
                    if math.hypot(e.rect.centerx - player.rect.centerx, e.rect.centery - player.rect.centery) < blast_radius:
                        e.health -= explosion_damage
                        if e.health <= 0:
                            if self.game.session:
                                self.game.session.handle_enemy_death(e)
                            else:
                                e.kill()
                                game.combo_timer = 0
                                game.combo = getattr(game, 'combo', 0) + 1
                                if not hasattr(game, 'max_combo'):
                                    game.max_combo = 0
                                game.max_combo = max(game.max_combo, game.combo)
                                if not hasattr(game, 'style_points'):
                                    game.style_points = 0
                                c = game.combo
                                game.style_rank = "S" if c>=10 else ("A" if c>=7 else ("B" if c>=5 else ("C" if c>=3 else "D")))
                                mult = 1.0
                                sr = getattr(game, 'style_rank', 'D')
                                if sr == "S": mult = 2.0
                                elif sr == "A": mult = 1.5
                                elif sr == "B": mult = 1.2
                                game.style_points += int(10 * mult)
                                if hasattr(game, 'score'):
                                    game.score += int(10 * game.combo * getattr(game, 'exp_multiplier', 1) * mult)
                                if hasattr(game, 'enemies_killed'):
                                    game.enemies_killed += 1
                            # extra blast viz particles (handle provides the kill explosion)
                            for _ in range(8):
                                p = Particle(e.rect.centerx, e.rect.centery, (255,165,0))
                                self.particles.append(p)
            for ast in list(self.asteroids):
                if math.hypot(ast.rect.centerx - player.rect.centerx, ast.rect.centery - player.rect.centery) < blast_radius:
                    ast.kill()
                    for _ in range(5):
                        p = Particle(ast.rect.centerx, ast.rect.centery, (139,69,19))
                        self.particles.append(p)
                    if hasattr(game, 'score'):
                        game.score += 10
                    if hasattr(game, 'coins'):
                        game.coins += 1
            for _ in range(20):
                p = Particle(player.rect.centerx + random.randint(-30, 30), player.rect.centery + random.randint(-30, 30), (255,165,0), 'explosion')
                self.particles.append(p)
            player.invincibility = True
            player.invincibility_timer = 60
        elif powerup.type == 'nuke':
            enemy_count = len(self.enemies)
            asteroid_count = len(self.asteroids)
            for enemy in list(self.enemies):
                # Delegate to get full combo/rank/score/particles/pu chance/sound per kill consistency
                self.handle_enemy_death(enemy)
            for ast in list(self.asteroids):
                ast.kill()
                for _ in range(5):
                    p = Particle(ast.rect.centerx, ast.rect.centery, (139,69,19), 'explosion')
                    self.particles.append(p)
            # Ast bonus still manual; enemy awards now come from delegated handle_enemy_death (includes combo ramp + style mult)
            if hasattr(game, 'score'):
                game.score += int((asteroid_count * 10) * getattr(game, 'exp_multiplier', 1))
            if hasattr(game, 'coins'):
                game.coins += int((asteroid_count) * getattr(game, 'coin_multiplier', 1))
            if getattr(game, 'explosion_sound', None):
                game.explosion_sound.play()
        elif powerup.type == 'extra_life':
            player.lives += 1
        if getattr(self.game, 'powerup_sound', None):
            self.game.powerup_sound.play()

    def _update_progression(self):
        """Wave increment, boss checks, campaign level complete conditions.
        Originally mixed in game.update_game_logic and level_manager.
        """
        # Respect MODE_CAMPAIGN vs ARCADE (use self.game.level_manager if present)
        pass

    def _update_effects(self):
        """Slow, freeze, screen shake hooks, etc. + theme hazards (PR9: nebula slow, crystal reflect stub)."""
        # nebula hazard: slow all
        theme = getattr(getattr(self.game, 'level_manager', None), 'level_theme', '') or ''
        if 'nebula' in theme.lower() or 'void' in theme.lower():
            self.slow_factor = min(self.slow_factor, 0.6)
        # crystal reflect stub (shots may bounce - simple in bullet update or here; for now slow + note)
        if 'crystal' in theme.lower() or 'plasma' in theme.lower():
            self.slow_factor = min(self.slow_factor, 0.8)  # slight drag
        pass  # reflect would reverse bullet vel in collisions or bullet update

    def _cleanup(self):
        """Remove dead sprites that weren't auto-killed."""
        pass

    def _apply_loadout_and_modifiers(self):
        """Creative hook for PR6 + PR7. Re-apply selected loadout from absolute bases."""
        if self.player and self.current_loadout:
            try:
                self.current_loadout.apply_to_player(self.player, game=self.game)
            except Exception as ex:
                print("Loadout re-apply note:", ex)
        elif self.player and getattr(self.player, 'current_loadout', None):
            self.current_loadout = self.player.current_loadout
            try:
                self.current_loadout.apply_to_player(self.player, game=self.game)
            except Exception as ex:
                print("Loadout re-apply note:", ex)
        for mod in self.active_modifiers:
            if hasattr(mod, 'apply'):
                mod.apply(self)

    # ------------------------------------------------------------------
    # PUBLIC API FOR STATES / RENDERER / FUTURE SYSTEMS (keep small & stable)
    # ------------------------------------------------------------------
    def get_all_drawables(self):
        """For renderer: returns main groups + particles in a convenient way."""
        return {
            'all_sprites': self.all_sprites,
            'particles': self.particles,
            # remote_bullets etc. if separate pass
        }

    def add_particle(self, particle):
        self.particles.append(particle)

    def on_enemy_killed(self, enemy, killer=None):
        """Hook for style/combo/achievements/coins. Called from handle_collisions."""
        self.enemies_killed_this_wave += 1
        # TODO: game.coins += ..., style points, etc.
        pass

    # ... many more small focused methods will appear during the real extraction ...

    def __repr__(self):
        return f"<SimulationWorld mode={self.mode} wave={self.wave} enemies={len(self.enemies)}>"


# Alias for any old references during transition
PlaySession = SimulationWorld


# Convenience alias if some code prefers the older name
PlaySession = SimulationWorld
