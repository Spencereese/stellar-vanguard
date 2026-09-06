import pygame

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
PINK = (255, 192, 203)
TIME_SLOW_COLOR = (0, 255, 128)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
DARK_RED = (139, 0, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)
FPS = 60

# V2 Constants
VERSION = "3.2"
MAX_LEVELS = 10
PARTICLE_LIMIT = 200
MAX_ENEMIES = 50
CAMERA_SHAKE_INTENSITY = 5
SCREEN_SHAKE_DURATION = 15

# Game Modes
MODE_CAMPAIGN = "campaign"
MODE_ARCADE = "arcade"
MODE_SURVIVAL = "survival"
MODE_CHALLENGE = "challenge"
MODE_MULTIPLAYER = "multiplayer"

# Multiplayer Constants
DEFAULT_SERVER_HOST = "localhost"
DEFAULT_SERVER_PORT = 5555
MAX_PLAYERS = 4
NETWORK_UPDATE_RATE = 30  # Updates per second
CLIENT_TIMEOUT = 5000  # milliseconds
PLAYER_SYNC_DISTANCE = 5  # pixels for position correction
INTERPOLATION_TIME = 0.1  # seconds for smooth movement

# Network Message Types
MSG_CONNECT = "connect"
MSG_DISCONNECT = "disconnect"
MSG_PLAYER_UPDATE = "player_update"
MSG_GAME_STATE = "game_state"
MSG_SHOOT = "shoot"
MSG_POWERUP_COLLECT = "powerup_collect"
MSG_ENEMY_KILL = "enemy_kill"
MSG_CHAT = "chat"
MSG_PROJECTILE_UPDATE = "projectile_update"
MSG_ENEMY_UPDATE = "enemy_update"
MSG_SCORE_UPDATE = "score_update"

# Level Themes
THEME_SPACE = "space"
THEME_NEBULA = "nebula"
THEME_ASTEROID = "asteroid"
THEME_ALIEN = "alien"
THEME_CYBER = "cyber"
THEME_COSMIC = "cosmic"
THEME_VOID = "void"
THEME_CRYSTAL = "crystal"
THEME_PLASMA = "plasma"
THEME_STORM = "storm"

# New Enemy Types
ENEMY_SWARMER = "swarmer"
ENEMY_ELITE = "elite"
ENEMY_HEALER = "healer"
ENEMY_TELEPORTER = "teleporter"
ENEMY_SHIELD = "shield"

# New Weapon Types
WEAPON_SHOTGUN = "shotgun"
WEAPON_FLAMETHROWER = "flamethrower"
WEAPON_LIGHTNING = "lightning"
WEAPON_BLACKHOLE = "blackhole"
WEAPON_FREEZE = "freeze"
WEAPON_RAILGUN = "railgun"

# Power-up Types
POWERUP_MULTISHOT = "multishot"
POWERUP_PIERCING = "piercing"
POWERUP_HOMING = "homing"
POWERUP_EXPLOSIVE = "explosive"
POWERUP_CHAIN = "chain"

# Achievement Types
ACHIEVEMENT_FIRST_KILL = "first_kill"
ACHIEVEMENT_LEVEL_MASTER = "level_master"
ACHIEVEMENT_WEAPON_MASTER = "weapon_master"
ACHIEVEMENT_SURVIVOR = "survivor"
ACHIEVEMENT_PACIFIST = "pacifist"