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
        
        return {
            'enemy_count': enemy_count,
            'boss_required': boss_required,
            'spawn_rate': spawn_rate,
            'enemy_health_multiplier': max(health_mult, 0.5),
            'enemy_speed_multiplier': max(speed_mult, 0.5),
            'reward_multiplier': max(reward_mult, 0.5),
            'theme': self.level_theme,
            'special_enemies': special_enemies + extra_specials,
            'objective_type': self._get_random_objective(level),
            'enemy_composition': self._get_enemy_composition(level)
        }

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
            # Complete level without taking damage
            return getattr(self.game, 'damage_taken_this_level', 0) == 0 and self.is_level_complete()  # Fallback to kill enemies
        
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
            
        return int(base_reward * multiplier * objective_bonus * performance_bonus)

    def next_level(self):
        """Advance to next level - now infinite"""
        self.current_level += 1
        return self.start_level(self.current_level)

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