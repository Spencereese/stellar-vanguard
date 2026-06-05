import pygame
import random
from config import *

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, particle_type='default', size=2):
        super().__init__()
        self.x = x
        self.y = y
        self.color = color
        self.particle_type = particle_type
        self.size = size
        self.alpha = 255
        self.rotation = 0
        self.rotation_speed = 0
        
        if self.particle_type == 'explosion':
            self.vel_x = random.randint(-10, 10)
            self.vel_y = random.randint(-10, 10)
            self.life = 20
            self.size = random.randint(2, 6)
            self.rotation_speed = random.randint(-10, 10)
        elif self.particle_type == 'smoke':
            self.vel_x = random.randint(-2, 2)
            self.vel_y = random.randint(-3, -1)  # Rise up
            self.life = 60
            self.size = random.randint(4, 8)
            self.color = (100, 100, 100)
            self.alpha_decay = 4
        elif self.particle_type == 'spark':
            self.vel_x = random.randint(-8, 8)
            self.vel_y = random.randint(-12, -2)  # Upward arc
            self.life = 40
            self.size = random.randint(1, 3)
            self.gravity = 0.3
            self.trail = []  # Spark trail effect
        elif self.particle_type == 'plasma':
            self.vel_x = random.randint(-5, 5)
            self.vel_y = random.randint(-5, 5)
            self.life = 25
            self.size = random.randint(3, 5)
            self.color = (100, 200, 255)  # Electric blue
            self.rotation_speed = random.randint(-15, 15)
        elif self.particle_type == 'fire':
            self.vel_x = random.randint(-3, 3)
            self.vel_y = random.randint(-8, -2)  # Rise up
            self.life = 35
            self.size = random.randint(2, 5)
            self.color = random.choice([(255, 100, 50), (255, 150, 50), (255, 200, 100)])  # Fire colors
        elif self.particle_type == 'electric':
            self.vel_x = random.randint(-12, 12)
            self.vel_y = random.randint(-12, 12)
            self.life = 15
            self.size = 2
            self.color = (200, 255, 255)
            self.lightning_branches = []  # For chain lightning effect
        elif self.particle_type == 'star':
            self.vel_x = 0
            self.vel_y = random.randint(-1, 1)
            self.life = 120
            self.size = random.randint(1, 2)
            self.twinkle_speed = random.uniform(0.05, 0.15)
            self.brightness = 1.0
        else:  # default
            self.vel_x = random.randint(-5, 5)
            self.vel_y = random.randint(-5, 5)
            self.life = 30

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Apply gravity to affected particles
        if hasattr(self, 'gravity'):
            self.vel_y += self.gravity
            
        # Update rotation
        if hasattr(self, 'rotation_speed'):
            self.rotation += self.rotation_speed
            
        # Special effects for different particle types
        if self.particle_type == 'spark' and hasattr(self, 'trail'):
            # Add current position to trail
            self.trail.append((self.x, self.y))
            if len(self.trail) > 8:  # Limit trail length
                self.trail.pop(0)
                
        elif self.particle_type == 'star':
            # Twinkle effect
            self.brightness += self.twinkle_speed
            if self.brightness > 1.5 or self.brightness < 0.5:
                self.twinkle_speed *= -1
                
        elif self.particle_type == 'electric':
            # Chain lightning effect - create branching particles
            if random.random() < 0.1 and len(self.lightning_branches) < 3:
                branch = Particle(self.x, self.y, (150, 255, 255), 'electric', 1)
                branch.vel_x = random.randint(-8, 8)
                branch.vel_y = random.randint(-8, 8)
                branch.life = 10
                self.lightning_branches.append(branch)
        
        self.life -= 1
        
        # Alpha decay
        if hasattr(self, 'alpha_decay'):
            self.alpha = max(0, self.alpha - self.alpha_decay)
        else:
            self.alpha = max(0, self.alpha - (255 // max(1, self.life)) if self.life > 0 else 0)
            
        if self.life <= 0:
            self.kill()