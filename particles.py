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
        elif self.particle_type == 'thrust':
            # Player/enemy engine exhaust - bright, fast decay, slight spread
            self.vel_x = random.uniform(-1.5, 1.5) + (vx if 'vx' in dir() else 0) * -0.3
            self.vel_y = random.uniform(-1.5, 1.5) + (vy if 'vy' in dir() else 0) * -0.3
            self.life = random.randint(8, 18)
            self.size = random.randint(2, 5)
            self.color = random.choice([(80, 180, 255), (100, 220, 255), (255, 140, 60), (200, 230, 255)])
            self.alpha_decay = 18
        elif self.particle_type == 'muzzle':
            # Weapon muzzle flash - short bright burst
            self.vel_x = random.uniform(-2, 2)
            self.vel_y = random.uniform(-2, 2)
            self.life = 6
            self.size = random.randint(3, 7)
            self.color = random.choice([(255, 255, 220), (255, 240, 150), (180, 220, 255)])
            self.alpha_decay = 45
        elif self.particle_type == 'debris':
            # Chunk of metal/rock that spins and tumbles
            self.vel_x = random.uniform(-6, 6)
            self.vel_y = random.uniform(-6, 6)
            self.life = random.randint(25, 55)
            self.size = random.randint(2, 5)
            self.rotation_speed = random.uniform(-18, 18)
            self.color = random.choice([(180, 180, 190), (120, 120, 130), (80, 70, 60)])
            self.gravity = 0.08
        elif self.particle_type == 'ring':
            # Expanding shockwave / impact ring
            self.vel_x = 0
            self.vel_y = 0
            self.life = 18
            self.size = 4
            self.max_size = random.randint(22, 38)
            self.color = (255, 220, 120)
            self.alpha_decay = 14
        elif self.particle_type == 'ghost':
            # Afterimage / cloaking echo
            self.vel_x = random.uniform(-0.3, 0.3)
            self.vel_y = random.uniform(-0.3, 0.3)
            self.life = random.randint(12, 28)
            self.size = random.randint(3, 6)
            self.alpha_decay = 8
            self.color = (120, 180, 255)
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
        elif self.particle_type == 'ring':
            # Expand the ring
            grow = (self.max_size - self.size) * 0.18
            self.size += max(0.8, grow)
        elif self.particle_type == 'thrust' or self.particle_type == 'muzzle':
            # Slight drag for exhaust
            self.vel_x *= 0.92
            self.vel_y *= 0.92
        
        self.life -= 1
        
        # Alpha decay
        if hasattr(self, 'alpha_decay'):
            self.alpha = max(0, self.alpha - self.alpha_decay)
        else:
            self.alpha = max(0, self.alpha - (255 // max(1, self.life)) if self.life > 0 else 0)
            
        if self.life <= 0:
            self.kill()


# --- Emitter helpers for technically impressive FX (called from player, enemies, sim) ---
def emit_thrust(particles_list, x, y, vel_x=0, vel_y=0, count=4, color=None):
    for _ in range(count):
        p = Particle(x + random.uniform(-3,3), y + random.uniform(-3,3), color or (100,200,255), 'thrust', 3)
        # bias backward relative to velocity
        p.vel_x += -vel_x * random.uniform(0.2, 0.6) + random.uniform(-1.2, 1.2)
        p.vel_y += -vel_y * random.uniform(0.2, 0.6) + random.uniform(-1.2, 1.2)
        particles_list.append(p)

def emit_muzzle(particles_list, x, y, count=5):
    for _ in range(count):
        p = Particle(x, y, (255,255,200), 'muzzle', random.randint(2,5))
        particles_list.append(p)

def emit_hit_sparks(particles_list, x, y, count=6):
    for _ in range(count):
        p = Particle(x, y, (255, 240, 120), 'spark', 2)
        p.vel_x = random.uniform(-7, 7)
        p.vel_y = random.uniform(-7, 7)
        particles_list.append(p)

def emit_explosion(particles_list, x, y, intensity=1.0):
    n = int(8 * intensity)
    for _ in range(n):
        p = Particle(x, y, (255, 180, 40), 'explosion', random.randint(3,8))
        p.vel_x *= 1.1 * intensity
        p.vel_y *= 1.1 * intensity
        particles_list.append(p)
    # debris
    for _ in range(int(5 * intensity)):
        p = Particle(x, y, (200,200,210), 'debris', 3)
        particles_list.append(p)
    # shock ring
    if intensity > 0.6:
        r = Particle(x, y, (255,220,140), 'ring', 5)
        r.max_size = int(18 + 20 * intensity)
        particles_list.append(r)

def emit_debris(particles_list, x, y, count=4):
    for _ in range(count):
        p = Particle(x, y, (160,160,170), 'debris', random.randint(2,4))
        particles_list.append(p)

def emit_ghost_trail(particles_list, x, y, count=2):
    for _ in range(count):
        p = Particle(x, y, (140, 190, 255), 'ghost', 4)
        particles_list.append(p)