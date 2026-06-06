import pygame
from config import SCREEN_HEIGHT, GREEN, YELLOW, RED, BLUE, WHITE, PURPLE, ORANGE, GRAY, MAGENTA, PINK, CYAN, TIME_SLOW_COLOR, LIGHT_BLUE, BROWN, THEME_SPACE, THEME_NEBULA, THEME_ASTEROID, THEME_ALIEN, THEME_CYBER
import math
from utils import load_image_with_fallback, get_asset_manager

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, type, game=None):
        super().__init__()
        self.type = type
        self.game = game
        
        # Try to load power-up image, fallback to enhanced procedural graphics
        def draw_powerup(surface):
            # Clear surface with transparency
            surface.fill((0, 0, 0, 0))
            
            color = self._get_base_color()
            center = (25, 25)
            
            # Draw different shapes based on powerup type
            if self.type == 'rapid':
                # Triple lightning bolt symbol
                pygame.draw.polygon(surface, color, [(15, 10), (20, 5), (18, 15), (23, 10), (21, 20), (26, 15), (24, 25), (29, 20), (27, 30), (32, 25)])
            elif self.type == 'spread':
                # Spread shot - three arrows fanning out
                for i in range(3):
                    angle = -30 + i * 30
                    start_x = 25 + math.cos(math.radians(angle)) * 15
                    start_y = 25 + math.sin(math.radians(angle)) * 15
                    end_x = 25 + math.cos(math.radians(angle)) * 5
                    end_y = 25 + math.sin(math.radians(angle)) * 5
                    pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), 3)
                    # Arrowhead
                    pygame.draw.polygon(surface, color, [
                        (start_x, start_y),
                        (start_x - 2, start_y - 2), (start_x + 2, start_y - 2)
                    ])
            elif self.type == 'laser':
                # Laser beam symbol
                pygame.draw.rect(surface, color, (10, 20, 30, 4))
                pygame.draw.polygon(surface, color, [(40, 18), (45, 22), (40, 26)])
            elif self.type == 'shield':
                # Shield symbol
                pygame.draw.polygon(surface, color, [(25, 10), (15, 15), (15, 35), (25, 40), (35, 35), (35, 15)])
                pygame.draw.circle(surface, color, (25, 22), 3)
            elif self.type == 'ammo':
                # Battery/ammo symbol
                pygame.draw.rect(surface, color, (18, 15, 14, 20))
                pygame.draw.rect(surface, color, (15, 18, 20, 14))
                pygame.draw.line(surface, color, (20, 12), (20, 15), 2)
                pygame.draw.line(surface, color, (30, 12), (30, 15), 2)
            elif self.type == 'bomb':
                # Bomb symbol
                pygame.draw.circle(surface, color, center, 12)
                pygame.draw.line(surface, color, (25, 13), (25, 8), 2)
                pygame.draw.line(surface, color, (25, 8), (28, 8), 2)
                pygame.draw.circle(surface, (255, 255, 255), (23, 23), 2)
            elif self.type == 'homing':
                # Target with crosshairs
                pygame.draw.circle(surface, color, center, 15, 2)
                pygame.draw.line(surface, color, (10, 25), (40, 25), 2)
                pygame.draw.line(surface, color, (25, 10), (25, 40), 2)
                pygame.draw.circle(surface, color, center, 3)
            elif self.type == 'freeze':
                # Snowflake
                pygame.draw.circle(surface, color, center, 12, 1)
                for angle in range(0, 360, 60):
                    x = 25 + math.cos(math.radians(angle)) * 10
                    y = 25 + math.sin(math.radians(angle)) * 10
                    pygame.draw.line(surface, color, center, (x, y), 1)
                    # Smaller branches
                    bx = 25 + math.cos(math.radians(angle)) * 6
                    by = 25 + math.sin(math.radians(angle)) * 6
                    pygame.draw.line(surface, color, (bx, by), (bx + 2, by + 2), 1)
            elif self.type == 'invincibility':
                # Star symbol
                star_points = []
                for i in range(10):
                    angle = i * 36
                    radius = 8 if i % 2 == 0 else 15
                    x = 25 + math.cos(math.radians(angle)) * radius
                    y = 25 + math.sin(math.radians(angle)) * radius
                    star_points.append((x, y))
                pygame.draw.polygon(surface, color, star_points)
            elif self.type == 'health':
                # Heart symbol
                pygame.draw.polygon(surface, color, [(25, 35), (15, 25), (25, 15), (35, 25)])
                pygame.draw.circle(surface, color, (20, 20), 4)
                pygame.draw.circle(surface, color, (30, 20), 4)
            elif self.type == 'missile':
                # Rocket symbol
                pygame.draw.polygon(surface, color, [(15, 35), (25, 10), (35, 35), (25, 30)])
                pygame.draw.rect(surface, color, (23, 35, 4, 6))
                pygame.draw.polygon(surface, color, [(20, 35), (30, 35), (25, 40)])
            elif self.type == 'slow':
                # Clock symbol
                pygame.draw.circle(surface, color, center, 15, 2)
                pygame.draw.line(surface, color, center, (25, 15), 2)
                pygame.draw.line(surface, color, center, (30, 25), 2)
            elif self.type == 'plasma':
                # Plasma ball
                pygame.draw.circle(surface, color, center, 12)
                pygame.draw.circle(surface, (255, 255, 255), (22, 22), 3)
                pygame.draw.circle(surface, (255, 255, 255), (28, 20), 2)
            elif self.type == 'teleport':
                # Portal/swirl symbol
                pygame.draw.circle(surface, color, center, 15, 2)
                # Swirl pattern
                for i in range(3):
                    angle = i * 120
                    pygame.draw.arc(surface, color, (15, 15, 20, 20), 
                                   math.radians(angle), math.radians(angle + 90), 2)
            elif self.type == 'speed_boost':
                # Lightning bolt
                pygame.draw.polygon(surface, color, [(15, 10), (20, 10), (18, 20), (25, 15), (20, 25), (23, 35), (15, 30)])
            elif self.type == 'multishot':
                # Multi-bullet symbol
                for i in range(5):
                    x = 15 + i * 4
                    pygame.draw.rect(surface, color, (x, 20, 2, 10))
                    pygame.draw.polygon(surface, color, [(x, 20), (x-1, 17), (x+1, 17)])
            elif self.type == 'grenade':
                # Grenade pin and body
                pygame.draw.circle(surface, color, (25, 25), 8)
                pygame.draw.line(surface, color, (25, 17), (25, 12), 2)
                pygame.draw.line(surface, color, (25, 12), (28, 12), 2)
                pygame.draw.circle(surface, (255, 255, 255), (23, 23), 2)
            elif self.type == 'kamikaze':
                # Kamikaze symbol - explosion with arrows pointing inward
                pygame.draw.circle(surface, color, center, 12, 2)
                # Arrows pointing inward
                for angle in range(0, 360, 90):
                    start_x = 25 + math.cos(math.radians(angle)) * 15
                    start_y = 25 + math.sin(math.radians(angle)) * 15
                    end_x = 25 + math.cos(math.radians(angle)) * 8
                    end_y = 25 + math.sin(math.radians(angle)) * 8
                    pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), 2)
                    # Arrowhead pointing inward
                    pygame.draw.polygon(surface, color, [
                        (end_x, end_y),
                        (end_x - 2, end_y - 2), (end_x + 2, end_y - 2)
                    ])
            else:
                # Default colored circle with border
                pygame.draw.circle(surface, color, center, 20)
                pygame.draw.circle(surface, (255, 255, 255), center, 20, 2)
        
        assets = getattr(self.game, 'assets', None) or get_asset_manager()
        self.image = assets.load_image(f'powerup_{type}.png', (51, 51), draw_powerup)
        # Use the single high-quality upgraded powerup orb (v4 generated) for all types - it looks pro + bloom/particles sell the 'animation'
        try:
            g = assets.load_image('powerup_v4.png', (51, 51))
            if g and g.get_width() > 20:
                self.image = g
        except:
            pass
        
        # Apply theme-based color modification if using fallback
        if not self._image_loaded_successfully():
            self._set_color_based_on_theme()
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 1
        self.drift = -0.8  # Leftward drift
        self.upward_speed = 2.0  # Initial upward speed
        self.upward_decay = 0.05  # How quickly upward speed decreases
        self.min_upward_speed = -0.5  # Minimum upward speed (will start moving down)

    def _get_base_color(self):
        """Get the base color for this power-up type"""
        base_colors = {
            'rapid': GREEN,
            'spread': YELLOW,
            'laser': RED,
            'shield': BLUE,
            'ammo': WHITE,
            'bomb': PURPLE,
            'homing': ORANGE,
            'freeze': GRAY,
            'invincibility': MAGENTA,
            'health': PINK,
            'missile': LIGHT_BLUE,
            'slow': TIME_SLOW_COLOR,
            'plasma': CYAN,
            'teleport': BROWN,
            'speed_boost': (255, 215, 0),  # Gold
            'multishot': (255, 69, 0),  # Red-Orange
            'grenade': (0, 128, 0),  # Dark green
            'kamikaze': MAGENTA,  # Magenta for kamikaze
            'nuke': (0, 0, 0),  # Black
            'extra_life': (255, 20, 147),  # Deep pink
        }
        return base_colors.get(self.type, WHITE)

    def _image_loaded_successfully(self):
        """Check if the image was loaded from file (not fallback)"""
        # Simple check: if image is magenta, it means fallback was used
        return self.image.get_at((0, 0)) != (255, 0, 255, 255)

    def _set_color_based_on_theme(self):
        """Set power-up color based on current level theme"""
        theme = self.game.level_manager.level_theme if self.game else THEME_SPACE
        
        # Base colors for each power-up type
        base_colors = {
            'rapid': GREEN,
            'spread': YELLOW,
            'laser': RED,
            'shield': BLUE,
            'ammo': WHITE,
            'bomb': PURPLE,
            'homing': ORANGE,
            'freeze': GRAY,
            'invincibility': MAGENTA,
            'health': PINK,
            'missile': LIGHT_BLUE,
            'slow': TIME_SLOW_COLOR,
            'plasma': CYAN,
            'teleport': BROWN,
            'speed_boost': (255, 215, 0),  # Gold
            'multishot': (255, 69, 0),  # Red-Orange
            'grenade': (0, 128, 0),  # Dark green
            'kamikaze': MAGENTA,  # Magenta for kamikaze
            'nuke': (0, 0, 0),  # Black
            'extra_life': (255, 20, 147),  # Deep pink
        }
        
        color = base_colors.get(self.type, WHITE)
        
        # Apply theme modifications
        if theme == THEME_SPACE:
            # Default space theme - use base colors
            pass
        elif theme == THEME_NEBULA:
            # Nebula theme - shift towards purple/pink tones
            color = self._shift_color_towards(color, PURPLE, 0.3)
        elif theme == THEME_ASTEROID:
            # Asteroid theme - shift towards brown/gray tones
            color = self._shift_color_towards(color, BROWN, 0.4)
        elif theme == THEME_ALIEN:
            # Alien theme - shift towards green/cyan tones
            color = self._shift_color_towards(color, GREEN, 0.3)
        elif theme == THEME_CYBER:
            # Cyber theme - shift towards cyan/magenta tones
            color = self._shift_color_towards(color, CYAN, 0.3)
        
        self.image.fill(color)

    def _shift_color_towards(self, original_color, target_color, factor):
        """Shift a color towards another color by a given factor"""
        r1, g1, b1 = original_color
        r2, g2, b2 = target_color
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        return (r, g, b)

    def update(self):
        # Move up and left with decreasing upward speed
        self.rect.y -= self.upward_speed
        self.rect.x += self.drift
        
        # Gradually decrease upward speed (will eventually become negative for downward movement)
        self.upward_speed -= self.upward_decay
        if self.upward_speed < self.min_upward_speed:
            self.upward_speed = self.min_upward_speed
        
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()