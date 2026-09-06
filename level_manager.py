import pygame
import random
import math
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, LIGHT_BLUE, CYAN, PURPLE, MAGENTA, PINK, 
                    GRAY, BROWN, ORANGE, GREEN, RED, BLUE, YELLOW, GOLD, SILVER, DARK_BLUE, DARK_RED,
                    THEME_SPACE, THEME_NEBULA, THEME_ASTEROID, THEME_ALIEN, THEME_CYBER,
                    THEME_COSMIC, THEME_VOID, THEME_CRYSTAL, THEME_PLASMA, THEME_STORM,
                    ENEMY_SWARMER, ENEMY_ELITE, ENEMY_HEALER, ENEMY_TELEPORTER,
                    MAX_LEVELS, MAX_ENEMIES, CAMERA_SHAKE_INTENSITY, SCREEN_SHAKE_DURATION)
from enemies import Boss

class LevelManager:
    def __init__(self, game):
        self.game = game
        self.current_level = 1
        self.level_data = self._generate_levels()
        self.level_theme = THEME_SPACE
        self.background_color = BLACK
        self.star_colors = [WHITE, LIGHT_BLUE, CYAN]
        self.particle_colors = [BLUE, PURPLE, CYAN]
        self.current_level_data = None

    def _generate_levels(self):
        """Generate level data for campaign mode - now procedural"""
        # For procedural generation, we'll generate levels on demand
        # This method can be simplified or removed
        return {}

    def _get_level_theme(self, level):
        """Determine theme based on level"""
        themes = [THEME_SPACE, THEME_NEBULA, THEME_ASTEROID, THEME_ALIEN, THEME_CYBER, 
                 THEME_COSMIC, THEME_VOID, THEME_CRYSTAL, THEME_PLASMA, THEME_STORM]
        return themes[(level - 1) % len(themes)]

    def _get_special_enemies(self, level):
        """Get special enemy types for this level"""
        special_enemies = []

        if level >= 3:
            special_enemies.append(ENEMY_SWARMER)
        if level >= 5:
            special_enemies.append(ENEMY_ELITE)
        if level >= 7:
            special_enemies.append(ENEMY_HEALER)
        if level >= 9:
            special_enemies.append(ENEMY_TELEPORTER)

        return special_enemies

    def _generate_level_data(self, level):
        """Procedurally generate level data"""
        # Base values
        base_enemies = 8
        enemy_increment = 2
        
        # Add some randomness to enemy count
        enemy_count = min(base_enemies + level * enemy_increment + random.randint(-2, 2), MAX_ENEMIES)
        
        # Boss levels - more frequent as game progresses
        boss_chance = min(0.1 + (level - 1) * 0.05, 0.4)  # Up to 40% chance
        boss_required = random.random() < boss_chance
        
        # Spawn rate - gets faster but with some variation
        base_spawn = 60
        spawn_decrement = 2
        spawn_variation = random.randint(-5, 5)
        spawn_rate = max(base_spawn - level * spawn_decrement + spawn_variation, 15)
        
        # Multipliers with some randomness
        health_mult = 1.0 + (level - 1) * 0.08 + random.uniform(-0.05, 0.05)
        speed_mult = 1.0 + (level - 1) * 0.04 + random.uniform(-0.03, 0.03)
        reward_mult = 1.0 + (level - 1) * 0.15 + random.uniform(-0.1, 0.1)
        
        # Special enemies
        special_enemies = self._get_special_enemies(level)
        
        # Add random special enemies
        extra_specials = []
        if level >= 10 and random.random() < 0.3:
            extra_specials.append(random.choice(['tank', 'shooter', 'bomber']))
        
        objective_type = self._get_random_objective(level)
        data = {
            'enemy_count': enemy_count,
            'boss_required': boss_required,
            'spawn_rate': spawn_rate,
            'enemy_health_multiplier': max(health_mult, 0.5),
            'enemy_speed_multiplier': max(speed_mult, 0.5),
            'reward_multiplier': max(reward_mult, 0.5),
            'theme': self.level_theme,
            'special_enemies': special_enemies + extra_specials,
            'objective_type': objective_type,
            'enemy_composition': self._get_enemy_composition(level),
        }
        data['secondary_objective'] = self._pick_secondary_objective(level, objective_type, data)
        return data

    def _get_enemy_composition(self, level):
        """Get enemy type distribution for this level"""
        composition = {'normal': 0.6}  # Base normal enemies
        
        if level >= 2:
            composition['fast'] = 0.2
        if level >= 4:
            composition['tank'] = 0.15
        if level >= 6:
            composition['shooter'] = 0.1
        if level >= 8:
            composition['bomber'] = 0.08
        if level >= 10:
            composition['elite'] = 0.05
        if level >= 12:
            composition['healer'] = 0.03
        if level >= 14:
            composition['teleporter'] = 0.02
            
        # Normalize probabilities
        total = sum(composition.values())
        for enemy_type in composition:
            composition[enemy_type] /= total
            
        return composition

    def get_random_enemy_type(self):
        """Get a random enemy type based on current level composition"""
        if not hasattr(self, 'current_level_data') or 'enemy_composition' not in self.current_level_data:
            return 'normal'
            
        composition = self.current_level_data['enemy_composition']
        rand = random.random()
        cumulative = 0.0
        
        for enemy_type, probability in composition.items():
            cumulative += probability
            if rand <= cumulative:
                return enemy_type
                
        return 'normal'  # Fallback

    def _get_random_objective(self, level):
        """Get a random objective type for variety"""
        objectives = ['kill_enemies']
        
        if level >= 5:
            objectives.append('survive_time')
        if level >= 10:
            objectives.append('collect_powerups')
        if level >= 15:
            objectives.append('no_damage')
            
        return random.choice(objectives)

    def _pick_secondary_objective(self, level, primary, data):
        """Optional secondary objective for Campaign depth (bonus, not required to clear).
        Avoids duplicating the primary type. Available from level 3+.
        """
        if level < 3:
            return None
        # Secondary catalog: type, label, target, bonus_mult
        pool = []
        if primary != 'no_damage':
            pool.append({
                'type': 'no_damage',
                'label': 'Zero damage',
                'target': 0,
                'bonus_mult': 1.35,
                'description': 'Take no damage this level',
            })
        if primary != 'collect_powerups':
            tgt = 3 if level < 10 else 5
            pool.append({
                'type': 'collect_powerups',
                'label': 'Salvage run',
                'target': tgt,
                'bonus_mult': 1.2,
                'description': f'Collect {tgt} power-ups',
            })
        if primary != 'survive_time':
            tgt = 45 if level < 8 else 60
            pool.append({
                'type': 'survive_time',
                'label': 'Hold the line',
                'target': tgt,
                'bonus_mult': 1.25,
                'description': f'Survive {tgt}s (bonus clock)',
            })
        # Extra kills always available as secondary (distinct from primary kill quota)
        extra = max(3, data.get('enemy_count', 8) // 4)
        pool.append({
            'type': 'extra_kills',
            'label': 'Overkill',
            'target': data.get('enemy_count', 8) + extra,
            'bonus_mult': 1.15,
            'description': f'Eliminate {data.get("enemy_count", 8) + extra} hostiles',
        })
        # Style rank secondary from midgame
        if level >= 6:
            pool.append({
                'type': 'style_rank',
                'label': 'Stylish clear',
                'target': 'B',
                'bonus_mult': 1.3,
                'description': 'Finish at style rank B or better',
            })
        if not pool:
            return None
        # ~70% chance to attach a secondary so early levels stay light
        if random.random() > 0.85 and level < 5:
            return None
        return random.choice(pool)

    def is_secondary_complete(self, sec=None):
        """Whether the optional secondary objective is currently satisfied."""
        if sec is None:
            data = getattr(self, 'current_level_data', None) or {}
            sec = data.get('secondary_objective')
        if not sec:
            return False
        st = sec.get('type')
        tgt = sec.get('target')
        if st == 'no_damage':
            return getattr(self.game, 'damage_taken_this_level', 0) == 0
        if st == 'collect_powerups':
            return getattr(self.game, 'powerups_collected_this_level', 0) >= int(tgt or 0)
        if st == 'survive_time':
            return int(getattr(self.game, 'survival_time', 0)) >= int(tgt or 0)
        if st == 'extra_kills':
            return getattr(self.game, 'enemies_killed_this_level', 0) >= int(tgt or 0)
        if st == 'style_rank':
            order = {'D': 0, 'C': 1, 'B': 2, 'A': 3, 'S': 4}
            cur = getattr(self.game, 'style_rank', 'D')
            need = str(tgt or 'B')
            return order.get(cur, 0) >= order.get(need, 2)
        return False

    def trigger_random_event(self):
        """Trigger a random level event"""
        if not hasattr(self, 'current_level_data'):
            return
            
        level = self.current_level
        events = []
        
        # Basic events
        events.append('meteor_shower')
        events.append('enemy_rush')
        
        if level >= 5:
            events.append('powerup_storm')
        if level >= 10:
            events.append('time_slow')
        if level >= 15:
            events.append('enemy_freeze')
            
        event = random.choice(events)
        self._execute_event(event)

    def _execute_event(self, event_type):
        """Execute the specified event"""
        if event_type == 'meteor_shower':
            # Spawn several asteroids
            for _ in range(5 + random.randint(0, 5)):
                # Use game's asteroid spawning if available
                if hasattr(self.game, 'asteroids'):
                    ast = self.game.create_asteroid() if hasattr(self.game, 'create_asteroid') else None
                    if ast:
                        self.game.all_sprites.add(ast)
                        self.game.asteroids.add(ast)
        elif event_type == 'enemy_rush':
            # Spawn a wave of enemies
            for _ in range(3 + random.randint(0, 3)):
                enemy = self.game.create_enemy()
                self.game.all_sprites.add(enemy)
                self.game.enemies.add(enemy)
        elif event_type == 'powerup_storm':
            # Spawn multiple power-ups - this would need PowerUp class, skip for now
            pass
        elif event_type == 'time_slow':
            # Temporary time slow
            self.game.time_slow_timer = 300  # 5 seconds
        elif event_type == 'enemy_freeze':
            # Freeze all enemies temporarily
            self.game.freeze_timer = 300  # 5 seconds

    def start_level(self, level):
        """Initialize level settings - now procedural"""
        self.current_level = level
        self.level_theme = self._get_level_theme(level)
        self._apply_theme_settings()

        # Generate procedural level data
        level_data = self._generate_level_data(level)
        
        # Reset level-specific variables
        self.game.wave = level
        self.game.enemies_killed_this_level = 0
        self.game.enemies_required = level_data['enemy_count']
        self.game.boss_fight = level_data['boss_required']
        self.game.boss_approach = 0.0  # reset progress toward boss for the bar
        # Reset mission counters
        self.game.survival_time = 0.0
        self.game.damage_taken_this_level = 0
        self.game.powerups_collected_this_level = 0

        # Store current level data for reference
        self.current_level_data = level_data

        return True

    def _apply_theme_settings(self):
        """Apply visual settings based on current theme"""
        if self.level_theme == THEME_SPACE:
            self.background_color = BLACK
            self.star_colors = [WHITE, LIGHT_BLUE]
            self.particle_colors = [BLUE, CYAN]
        elif self.level_theme == THEME_NEBULA:
            self.background_color = (20, 0, 40)
            self.star_colors = [PURPLE, MAGENTA, PINK]
            self.particle_colors = [PURPLE, MAGENTA, ORANGE]
        elif self.level_theme == THEME_ASTEROID:
            self.background_color = (30, 20, 10)
            self.star_colors = [GRAY, BROWN, ORANGE]
            self.particle_colors = [ORANGE, RED, YELLOW]
        elif self.level_theme == THEME_ALIEN:
            self.background_color = (0, 50, 20)
            self.star_colors = [GREEN, CYAN, LIGHT_BLUE]
            self.particle_colors = [GREEN, CYAN, YELLOW]
        elif self.level_theme == THEME_CYBER:
            self.background_color = (10, 10, 30)
            self.star_colors = [CYAN, MAGENTA, WHITE]
            self.particle_colors = [CYAN, MAGENTA, BLUE]
        elif self.level_theme == THEME_COSMIC:
            self.background_color = (5, 5, 15)
            self.star_colors = [WHITE, GOLD, SILVER]
            self.particle_colors = [GOLD, SILVER, WHITE]
        elif self.level_theme == THEME_VOID:
            self.background_color = (0, 0, 0)
            self.star_colors = [GRAY, DARK_BLUE, DARK_RED]
            self.particle_colors = [DARK_BLUE, DARK_RED, PURPLE]
        elif self.level_theme == THEME_CRYSTAL:
            self.background_color = (10, 20, 30)
            self.star_colors = [CYAN, LIGHT_BLUE, WHITE]
            self.particle_colors = [CYAN, LIGHT_BLUE, BLUE]
        elif self.level_theme == THEME_PLASMA:
            self.background_color = (40, 0, 20)
            self.star_colors = [MAGENTA, PINK, RED]
            self.particle_colors = [MAGENTA, PINK, ORANGE]
        elif self.level_theme == THEME_STORM:
            self.background_color = (15, 15, 25)
            self.star_colors = [CYAN, WHITE, GRAY]
            self.particle_colors = [CYAN, WHITE, BLUE]

    def get_level_info(self):
        """Get current level information"""
        return getattr(self, 'current_level_data', None)

    def is_level_complete(self):
        """Check if current level objectives are met"""
        if not hasattr(self, 'current_level_data'):
            return False

        data = self.current_level_data
        objective = data.get('objective_type', 'kill_enemies')
        
        if objective == 'kill_enemies':
            if data['boss_required']:
                # Boss level - check if boss is defeated
                return not any(isinstance(enemy, Boss) for enemy in self.game.enemies)
            else:
                # Regular level - check enemy count
                return self.game.enemies_killed_this_level >= data['enemy_count']
        elif objective == 'survive_time':
            # Survive for a certain time (e.g., 60 seconds)
            survival_time = getattr(self.game, 'survival_time', 0)
            return survival_time >= 60
        elif objective == 'collect_powerups':
            # Collect a certain number of power-ups
            powerups_collected = getattr(self.game, 'powerups_collected_this_level', 0)
            return powerups_collected >= 5
        elif objective == 'no_damage':
            # Complete hostiles/boss without taking damage (NO recursion — prior call re-entered self)
            dmg_ok = getattr(self.game, 'damage_taken_this_level', 0) == 0
            if data.get('boss_required'):
                clears = not any(isinstance(enemy, Boss) for enemy in getattr(self.game, 'enemies', []) or [])
            else:
                clears = getattr(self.game, 'enemies_killed_this_level', 0) >= data.get('enemy_count', 0)
            return dmg_ok and clears
        
        return False

    def get_level_reward(self):
        """Calculate reward for completing level"""
        if not hasattr(self, 'current_level_data'):
            return 0

        data = self.current_level_data
        base_reward = 100 * self.current_level
        multiplier = data['reward_multiplier']
        
        # Objective bonus
        objective_bonus = 1.0
        if data.get('objective_type') == 'no_damage':
            objective_bonus = 2.0
        elif data.get('objective_type') == 'survive_time':
            objective_bonus = 1.5
        elif data.get('objective_type') == 'collect_powerups':
            objective_bonus = 1.3
            
        # Performance bonuses
        performance_bonus = 1.0
        
        # Speed bonus - complete level quickly
        level_time = getattr(self.game, 'level_time', 0)
        if level_time > 0:
            expected_time = 60 + self.current_level * 10  # Rough estimate
            if level_time < expected_time * 0.8:
                performance_bonus *= 1.2  # 20% bonus for speed
                
        # Accuracy bonus - high hit ratio
        bullets_fired = getattr(self.game, 'bullets_fired', 0)
        enemies_killed = getattr(self.game, 'enemies_killed_this_level', 0)
        if bullets_fired > 0:
            accuracy = enemies_killed / bullets_fired
            if accuracy > 0.5:  # Better than 50% accuracy
                performance_bonus *= 1.1
                
        # No damage bonus (additional to objective)
        damage_taken = getattr(self.game, 'damage_taken_this_level', 0)
        if damage_taken == 0:
            performance_bonus *= 1.25

        # Optional secondary objective bonus (Campaign depth)
        secondary_bonus = 1.0
        sec = data.get('secondary_objective')
        if sec and self.is_secondary_complete(sec):
            secondary_bonus = float(sec.get('bonus_mult', 1.2))
            
        return int(base_reward * multiplier * objective_bonus * performance_bonus * secondary_bonus)

    def next_level(self):
        """Advance to next level - now infinite"""
        self.current_level += 1
        return self.start_level(self.current_level)

    def get_mission_description(self):
        """Human readable current mission for HUD / missions system."""
        if not hasattr(self, 'current_level_data') or not self.current_level_data:
            return "Survive the onslaught"
        data = self.current_level_data
        if data.get('boss_required'):
            return "PRIMARY: Defeat the Boss"
        obj = data.get('objective_type', 'kill_enemies')
        req = data.get('enemy_count', 0)
        killed = getattr(self.game, 'enemies_killed_this_level', 0)
        if obj == 'kill_enemies':
            return f"MISSION: Eliminate hostiles ({killed}/{req})"
        elif obj == 'survive_time':
            t = int(getattr(self.game, 'survival_time', 0))
            return f"MISSION: Survive assault ({t}s / 60s)"
        elif obj == 'collect_powerups':
            p = getattr(self.game, 'powerups_collected_this_level', 0)
            return f"MISSION: Collect power-ups ({p}/5)"
        elif obj == 'no_damage':
            return "MISSION: Zero damage run"
        return "MISSION: Complete objectives"

    def get_boss_approach(self):
        """0.0 to 1.0 - how close the player is to facing the boss.
        Used for the 'boss proximity' bar in HUD."""
        if not getattr(self.game, 'boss_fight', False):
            # For non-campaign or wave-based: approximate from wave
            wave = getattr(self.game, 'wave', 1)
            last = getattr(self.game, 'boss_wave', 3)
            if wave <= last:
                return 0.0
            return min(1.0, ((wave - last) % 3) / 3.0)
        data = getattr(self, 'current_level_data', {}) or {}
        killed = getattr(self.game, 'enemies_killed_this_level', 0)
        req = max(8, data.get('enemy_count', 20))
        # Boss usually spawns after significant progress ( ~70-80% of required kills or explicit trigger)
        return min(1.0, killed / float(req * 0.75))

    def get_mission_data(self):
        """Rich structured data for expanded mission panel.
        Returns dict with title, primary objective, trackers, bonuses, etc."""
        if not hasattr(self, 'current_level_data') or not self.current_level_data:
            return {
                'title': 'Survive',
                'description': 'Survive the onslaught',
                'progress': 0.0,
                'trackers': [],
                'is_boss': False,
                'estimated_reward': 100
            }

        data = self.current_level_data
        obj_type = data.get('objective_type', 'kill_enemies')
        is_boss = bool(data.get('boss_required', False))
        killed = getattr(self.game, 'enemies_killed_this_level', 0)
        req = data.get('enemy_count', 20)

        trackers = []
        progress = 0.0
        description = "Complete the objectives"

        if is_boss:
            description = "Defeat the Boss"
            progress = self.get_boss_approach()
            trackers.append({
                'name': 'Hostiles Eliminated',
                'current': killed,
                'target': req,
                'percent': min(1.0, killed / max(1, req))
            })
            trackers.append({
                'name': 'Boss Gauge',
                'current': int(progress * 100),
                'target': 100,
                'percent': progress,
                'unit': '%'
            })
        elif obj_type == 'kill_enemies':
            description = f"Eliminate {req} hostiles"
            progress = min(1.0, killed / max(1, req))
            trackers.append({
                'name': 'Enemies Destroyed',
                'current': killed,
                'target': req,
                'percent': progress
            })
        elif obj_type == 'survive_time':
            t = int(getattr(self.game, 'survival_time', 0))
            target_t = 60
            progress = min(1.0, t / target_t)
            description = f"Survive for {target_t}s"
            trackers.append({
                'name': 'Time Survived',
                'current': t,
                'target': target_t,
                'percent': progress,
                'unit': 's'
            })
        elif obj_type == 'collect_powerups':
            p = getattr(self.game, 'powerups_collected_this_level', 0)
            target_p = 5
            progress = min(1.0, p / target_p)
            description = f"Collect {target_p} power-ups"
            trackers.append({
                'name': 'Power-ups Collected',
                'current': p,
                'target': target_p,
                'percent': progress
            })
        elif obj_type == 'no_damage':
            dmg = getattr(self.game, 'damage_taken_this_level', 0)
            progress = 1.0 if dmg == 0 else 0.0
            description = "Complete with zero damage"
            trackers.append({
                'name': 'Damage Taken',
                'current': dmg,
                'target': 0,
                'percent': progress,
                'invert': True  # lower is better
            })

        # Add common trackers
        trackers.append({
            'name': 'Style Rank',
            'current': getattr(self.game, 'style_rank', 'D'),
            'target': 'S',
            'percent': {'S':1.0,'A':0.8,'B':0.6,'C':0.4,'D':0.2}.get(getattr(self.game, 'style_rank', 'D'), 0.2)
        })

        sec = data.get('secondary_objective')
        secondary = None
        if sec:
            st = sec.get('type')
            cur_val = 0
            tgt_val = sec.get('target', 0)
            perc = 0.0
            done = self.is_secondary_complete(sec)
            if st == 'no_damage':
                cur_val = getattr(self.game, 'damage_taken_this_level', 0)
                perc = 1.0 if cur_val == 0 else 0.0
            elif st == 'collect_powerups':
                cur_val = getattr(self.game, 'powerups_collected_this_level', 0)
                perc = min(1.0, cur_val / max(1, int(tgt_val or 1)))
            elif st == 'survive_time':
                cur_val = int(getattr(self.game, 'survival_time', 0))
                perc = min(1.0, cur_val / max(1, int(tgt_val or 1)))
            elif st == 'extra_kills':
                cur_val = getattr(self.game, 'enemies_killed_this_level', 0)
                perc = min(1.0, cur_val / max(1, int(tgt_val or 1)))
            elif st == 'style_rank':
                cur_val = getattr(self.game, 'style_rank', 'D')
                order = {'D': 0.2, 'C': 0.4, 'B': 0.6, 'A': 0.8, 'S': 1.0}
                perc = order.get(str(cur_val), 0.2)
            secondary = {
                'type': st,
                'label': sec.get('label', 'Secondary'),
                'description': sec.get('description', ''),
                'current': cur_val,
                'target': tgt_val,
                'percent': perc,
                'complete': done,
                'bonus_mult': sec.get('bonus_mult', 1.2),
                'invert': st == 'no_damage',
            }

        return {
            'title': f"Level {self.current_level} - {data.get('theme', 'Space').title()}",
            'description': description,
            'progress': progress,
            'trackers': trackers,
            'is_boss': is_boss,
            'objective_type': obj_type,
            'secondary': secondary,
            'estimated_reward': self.get_level_reward()
        }

class Camera:
    def __init__(self, game):
        self.game = game
        self.shake_intensity = 0
        self.shake_duration = 0
        self.offset_x = 0
        self.offset_y = 0

    def shake(self, intensity=CAMERA_SHAKE_INTENSITY, duration=SCREEN_SHAKE_DURATION):
        """Start camera shake effect"""
        self.shake_intensity = intensity
        self.shake_duration = duration

    def update(self):
        """Update camera shake"""
        if self.shake_duration > 0:
            self.shake_duration -= 1
            self.offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            self.offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
        else:
            self.offset_x = 0
            self.offset_y = 0

    def apply(self, rect):
        """Apply camera offset to a rectangle"""
        return pygame.Rect(rect.x + self.offset_x, rect.y + self.offset_y, rect.width, rect.height)