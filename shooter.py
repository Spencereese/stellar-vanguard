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
from upgrades import Upgrades
from config import *

from player import Player
from game import Game

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Shooter: Stellar Vanguard (v3.4)")
clock = pygame.time.Clock()

# Load high scores via PR3 persistence (deduped, evolvable)
try:
    from persistence import get_persistence
    pers = get_persistence()
    pers.migrate_if_needed()
    high_scores = pers.load_highscores()
except Exception:
    high_scores = [0] * 5

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

# Main game loop
game = Game()
game.run()