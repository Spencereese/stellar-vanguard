import pygame
import random
import sys
import math
import os

from particles import Particle
from projectiles import Bullet, Laser, Missile, Bomb, Plasma, Grenade, PiercingBullet, ShotgunBullet, Flamethrower, Lightning, BlackHole, FreezeBeam, RemoteBullet, KamikazeBullet
from enemies import Enemy, Boss, Asteroid, Swarmer, Elite, Healer, Teleporter, enemy_pools
from powerups import PowerUp
from config import *
from player import Player
from upgrades import Upgrades
from renderer import Renderer
from game_states import *
from level_manager import LevelManager, Camera
from network import NetworkManager
from utils import get_asset_manager
from simulation import SimulationWorld  # PR2 skeleton (full extraction in progress)
from persistence import get_persistence  # PR3 evolvable persistence
from registries import WEAPON_REGISTRY  # PR4 data-driven shop

# Create stars for space background
stars = [(random.randint(0, 2*SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(300)]

# Game class
class Game:
    def __init__(self):
        # Pygame is already initialized in shooter.py
        # v3 upgrade polish (PR12) + R6: default windowed 960x720; optional 1280x720 stretch (matches virtual render base).
        # Persisted fullscreen / window_* settings respected. F11 toggles fullscreen; Settings cycles window size.
        # Never forces desktop FULLSCREEN unless explicitly enabled in settings.
        try:
            pers = get_persistence()
            s = pers.load_settings()
            want_full = bool(s.get('fullscreen', False))
        except Exception:
            want_full = False
            s = {}

        # R6: allowed windowed sizes — 960 (default) or 1280 (optional native stretch)
        try:
            ww = int(s.get('window_width', 960) or 960)
            wh = int(s.get('window_height', 720) or 720)
        except Exception:
            ww, wh = 960, 720
        if ww >= 1280:
            ww, wh = 1280, 720
        else:
            ww, wh = 960, 720
        self.window_width = ww
        self.window_height = wh

        info = pygame.display.Info()
        global SCREEN_WIDTH, SCREEN_HEIGHT
        if want_full:
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
            display_flags = pygame.FULLSCREEN
        else:
            SCREEN_WIDTH = self.window_width
            SCREEN_HEIGHT = self.window_height
            display_flags = 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), display_flags)
        pygame.display.set_caption("Space Shooter: Stellar Vanguard (v3.4)")
        self.clock = pygame.time.Clock()
        self.fullscreen = want_full  # for toggle and HUD if wanted
        # Sync global screen size so enemy spawn (enemies.py), bullets etc use full res not stale 800
        try:
            import config as cfg
            cfg.SCREEN_WIDTH = SCREEN_WIDTH
            cfg.SCREEN_HEIGHT = SCREEN_HEIGHT
        except:
            pass
        # Recreate stars / parallax data using the actual current resolution (fixes spawn positions and bg scaling in fullscreen)
        self.stars = [(random.randint(0, 2 * SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(300)]
        self.slow_stars = [(random.randint(0, 2 * SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]
        self.fast_stars = [(random.randint(0, 2 * SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]
        self.bg_x = 0
        self.running = True
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)
        
        # Try to load better fonts if available
        try:
            self.font = pygame.font.Font('arial.ttf', 36)
        except (FileNotFoundError, OSError):
            pass
        try:
            self.small_font = pygame.font.Font('arial.ttf', 24)
        except (FileNotFoundError, OSError):
            pass
        try:
            self.tiny_font = pygame.font.Font('arial.ttf', 18)
        except (FileNotFoundError, OSError):
            pass
        self.music_volume = 0.5
        self.sfx_volume = 0.5
        self.current_music = None
        # load settings via pers (PR12)
        try:
            pers = get_persistence()
            s = pers.load_settings()
            self.music_volume = s.get('music_volume', 0.5)
            self.sfx_volume = s.get('sfx_volume', 0.5)
            self.difficulty = s.get('difficulty', 'normal')
            self.colorblind_mode = s.get('colorblind_mode')
            self.mouse_aim = s.get('mouse_aim', False)
            self.enable_experimental_mp = s.get('enable_experimental_mp', False)
            # loaded mouse_aim, mp flag etc via pers (PR12)
        except:
            pass
        # Screen shake effects
        self.screen_shake = 0
        self.screen_shake_timer = 0
        self.screen_shake_intensity = 5

        # Asset manager (PR1) - centralizes loads + caching for images/sounds.
        # Entities (player/enemies/...) continue to work via the compat wrapper
        # in utils.py; Game now also exposes self.assets for direct use.
        self.assets = get_asset_manager()

        # Load sounds via AssetManager (replaces scattered try/except + direct
        # pygame.mixer.Sound). Missing sounds are logged once and cached as None.
        self.shoot_sound = self.assets.get_sound('shoot', volume=self.sfx_volume)
        self.explosion_sound = self.assets.get_sound('explosion', volume=self.sfx_volume)
        self.powerup_sound = self.assets.get_sound('powerup', volume=self.sfx_volume)
        self.hit_sound = self.assets.get_sound('hit', volume=self.sfx_volume)
        # Initialize upgrades
        self.upgrades = Upgrades()
        # Set initial upgrade values
        self.max_health = self.upgrades.get('max_health')
        self.max_ammo = self.upgrades.get('max_ammo')
        self.player_speed = self.upgrades.get('player_speed')
        self.shield_duration = self.upgrades.get('shield_duration')
        self.damage = self.upgrades.get('damage')
        self.fire_rate = self.upgrades.get('fire_rate')
        self.crit_chance = self.upgrades.get('crit_chance')
        self.crit_damage = self.upgrades.get('crit_damage')
        self.coin_multiplier = self.upgrades.get('coin_multiplier')
        self.exp_multiplier = self.upgrades.get('exp_multiplier')
        self.weapon_damage = self.upgrades.get('weapon_damage')
        # Initialize renderer and input handler
        self.renderer = Renderer(self)
        # Initialize level manager and camera
        self.level_manager = LevelManager(self)
        self.camera = Camera(self)

        # PR2: SimulationWorld (stub for now) will own groups, update_game_logic,
        # collisions, spawning etc. Game stays thin coordinator + state host.
        self.session = None  # will become SimulationWorld(self, ...) after extraction

        # Initialize multiplayer
        self.network = None
        self.multiplayer_players = {}  # player_id -> player_data
        self.is_multiplayer = False
        self.is_server = False
        self.is_p2p = False
        # Initialize game variables
        self.menu_options = ["Play Game", "Multiplayer", "Shop & Upgrades", "Settings", "Quit"]
        self.setting_options = ["Difficulty", "Music Volume", "SFX Volume", "Window Size", "Leaderboard", "Upgrade Tree", "Back"]
        self.selected_option = 0
        self.selected_setting = 0
        self.selected_item = 0
        self.paused = False
        self.god_mode = False
        self.show_mission_panel = False  # TAB to expand full mission objectives panel
        self.enemy_timer = 0
        self.combo_timer = 0
        self.combo = 0
        self.max_combo = 0
        self.style_rank = "D"
        self.style_points = 0
        self.time_slow_timer = 0
        self.slow_factor = 1.0
        self.freeze_timer = 0
        self.continue_timer = 0
        self.menu_timer = 0
        self.survival = False
        self.continuing = False
        self.game_mode = MODE_ARCADE  # Default mode
        self.coins = 1000  # Starting coins
        self.score = 0  # Current game score
        self.enemies_killed = 0  # Track enemies killed for achievements
        self.bullets_fired = 0  # Track bullets fired for achievements
        self.survival_time = 0
        self.shop_items = [
            # Consumables
            {"name": "Extra Life", "cost": 500, "category": "consumables", "description": "Gain an extra life to continue playing", "effect": lambda: setattr(self.player, 'lives', self.player.lives + 1), "dynamic_cost": False, "icon": "❤️"},
            {"name": "Bomb", "cost": 200, "category": "consumables", "description": "Powerful area damage bomb", "effect": lambda: setattr(self.player, 'bombs', self.player.bombs + 2), "dynamic_cost": False, "icon": "💣"},
            {"name": "Missile Pack", "cost": 250, "category": "consumables", "description": "20 homing missiles", "effect": lambda: setattr(self.player, 'missile_count', self.player.missile_count + 20), "dynamic_cost": False, "icon": "🚀"},
            {"name": "Health Pack", "cost": 150, "category": "consumables", "description": "Restore 50 health points", "effect": lambda: setattr(self.player, 'health', min(self.player.max_health, self.player.health + 50)), "dynamic_cost": False, "icon": "🩹"},

            # Weapons - data-driven from registries (PR4 slim)
            # (base ones + any registered like railgun)
            {"name": "Shotgun Weapon", "cost": 800, "category": "weapons", "description": "Wide spread shotgun with high damage", "effect": lambda: setattr(self.player, 'weapon', WEAPON_SHOTGUN), "dynamic_cost": False, "icon": "🔫"},
            {"name": "Flamethrower Weapon", "cost": 1200, "category": "weapons", "description": "Continuous fire weapon with burn damage", "effect": lambda: setattr(self.player, 'weapon', WEAPON_FLAMETHROWER), "dynamic_cost": False, "icon": "🔥"},
            {"name": "Lightning Weapon", "cost": 1500, "category": "weapons", "description": "Chain lightning that hits multiple enemies", "effect": lambda: setattr(self.player, 'weapon', WEAPON_LIGHTNING), "dynamic_cost": False, "icon": "⚡"},
            {"name": "Black Hole Weapon", "cost": 2000, "category": "weapons", "description": "Creates gravitational anomalies", "effect": lambda: setattr(self.player, 'weapon', WEAPON_BLACKHOLE), "dynamic_cost": False, "icon": "🕳️"},
            {"name": "Freeze Beam Weapon", "cost": 1000, "category": "weapons", "description": "Slows and damages enemies with ice", "effect": lambda: setattr(self.player, 'weapon', WEAPON_FREEZE), "dynamic_cost": False, "icon": "❄️"},
            # dynamic from registry (e.g. railgun + future)
            *[
                {"name": f"{name.title()} Weapon", "cost": 1500 + i*300, "category": "weapons", "description": meta.get('desc', 'Special weapon'), "effect": (lambda n=name: setattr(self.player, 'weapon', n)), "dynamic_cost": False, "icon": "🔫"}
                for i, (name, meta) in enumerate(WEAPON_REGISTRY.items()) if name not in ('shotgun','flamethrower','lightning','blackhole','freeze')
            ],

            # Upgrades
            {"name": "Energy Capacity Upgrade", "cost_key": "max_ammo", "category": "upgrades", "description": "Increase maximum energy capacity", "effect": self.buy_max_ammo, "dynamic_cost": True, "icon": "⚡"},
            {"name": "Energy Regeneration Upgrade", "cost_key": "energy_regen", "category": "upgrades", "description": "Faster energy regeneration rate", "effect": self.buy_energy_regen, "dynamic_cost": True, "icon": "🔋"},
            {"name": "Speed Upgrade", "cost_key": "player_speed", "category": "upgrades", "description": "Increase ship movement speed", "effect": self.buy_speed, "dynamic_cost": True, "icon": "💨"},
            {"name": "Shield Duration Upgrade", "cost_key": "shield_duration", "category": "upgrades", "description": "Longer shield protection time", "effect": self.buy_shield_duration, "dynamic_cost": True, "icon": "🛡️"},
            {"name": "Max Health Upgrade", "cost_key": "max_health", "category": "upgrades", "description": "Increase maximum health capacity", "effect": self.buy_max_health, "dynamic_cost": True, "icon": "💚"},
            {"name": "Damage Upgrade", "cost_key": "damage", "category": "upgrades", "description": "Increase base weapon damage", "effect": self.buy_damage, "dynamic_cost": True, "icon": "⚔️"},
            {"name": "Fire Rate Upgrade", "cost_key": "fire_rate", "category": "upgrades", "description": "Increase weapon firing speed", "effect": self.buy_fire_rate, "dynamic_cost": True, "icon": "🔥"},
            {"name": "Critical Chance Upgrade", "cost_key": "crit_chance", "category": "upgrades", "description": "Higher chance for critical hits", "effect": self.buy_crit_chance, "dynamic_cost": True, "icon": "🎯"},
            {"name": "Critical Damage Upgrade", "cost_key": "crit_damage", "category": "upgrades", "description": "More damage from critical hits", "effect": self.buy_crit_damage, "dynamic_cost": True, "icon": "💥"},
            {"name": "Coin Multiplier Upgrade", "cost_key": "coin_multiplier", "category": "upgrades", "description": "Earn more coins from enemies", "effect": self.buy_coin_multiplier, "dynamic_cost": True, "icon": "💰"},
            {"name": "Experience Multiplier Upgrade", "cost_key": "exp_multiplier", "category": "upgrades", "description": "Gain more experience points", "effect": self.buy_exp_multiplier, "dynamic_cost": True, "icon": "⭐"},

            # Special Upgrades
            {"name": "Weapon Damage Upgrade", "cost_key": "weapon_damage", "category": "special", "description": "Increase damage for all weapons", "effect": self.buy_weapon_damage, "dynamic_cost": True, "icon": "🗡️"},
            {"name": "Shotgun Damage Upgrade", "cost_key": "shotgun_damage", "category": "special", "description": "Specialized shotgun damage boost", "effect": self.buy_shotgun_damage, "dynamic_cost": True, "icon": "🔫"},
            {"name": "Flamethrower Damage Upgrade", "cost_key": "flamethrower_damage", "category": "special", "description": "Specialized flamethrower damage boost", "effect": self.buy_flamethrower_damage, "dynamic_cost": True, "icon": "🔥"},
            {"name": "Lightning Damage Upgrade", "cost_key": "lightning_damage", "category": "special", "description": "Specialized lightning damage boost", "effect": self.buy_lightning_damage, "dynamic_cost": True, "icon": "⚡"},
            {"name": "Black Hole Damage Upgrade", "cost_key": "blackhole_damage", "category": "special", "description": "Specialized black hole damage boost", "effect": self.buy_blackhole_damage, "dynamic_cost": True, "icon": "🕳️"},
            {"name": "Freeze Beam Damage Upgrade", "cost_key": "freeze_damage", "category": "special", "description": "Specialized freeze beam damage boost", "effect": self.buy_freeze_damage, "dynamic_cost": True, "icon": "❄️"},
        ]

        # Generate special offers
        self._generate_special_offers()

        self.boss_sound = self.assets.get_sound('boss')  # AssetManager handles missing + caches None (no repeated spam)
        self.update_sound_volumes()  # ensure all sfx (incl boss) get initial volume from settings

        # Dynamic background music system (extended). Starts with menu track.
        # Switches based on game state (menu/game/boss) + combo intensity.
        self.play_music("menu_ambient", fade_ms=0)
        # Initialize sprites
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.remote_bullets = pygame.sprite.Group()  # Bullets from other players
        self.missiles = pygame.sprite.Group()
        self.plasmas = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.grenades = pygame.sprite.Group()
        self.particles = []
        # Stars
        self.stars = stars.copy()
        self.slow_stars = [(random.randint(0, 2*SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]
        self.fast_stars = [(random.randint(0, 2*SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]
        self.bg_x = 0
        # difficulty may have been loaded from pers earlier; default only if not
        if not getattr(self, 'difficulty', None):
            self.difficulty = 'normal'
        self.extra_lives = 0
        self.wave = 1
        self.level = 1
        self.enemies_killed_this_level = 0
        self.boss_wave = 0
        # R3 wave theme HUD fields (session owns the picker)
        self.wave_theme_name = ''
        self.wave_theme_id = None
        self.wave_banner_timer = 0
        self.boss_phase = 1
        self.boss_phase_announce_timer = 0
        self._survival_theme_clock = 0
        # Create player
        self.player = Player(self)
        self.all_sprites.add(self.player)

        # PR2 bridge (direct creative): give the rich main simulation skeleton a chance
        # to own some state. The full PR2 subagent will move the real logic and slim this.
        if self.session is None:
            try:
                self.session = SimulationWorld(self)
                self.session.set_player(self.player)
            except Exception:
                self.session = None

        # Steam prep stubs (PR12 per user decision: appid, controller db, overlay friendly)
        # (no full Steamworks; placeholder for packaging)
        try:
            if not os.path.exists('steam_appid.txt'):
                with open('steam_appid.txt', 'w') as f:
                    f.write('480\n')  # placeholder (e.g. Spacewar or your appid)
            # controller mappings note: pygame uses SDL; provide gamecontrollerdb.txt if needed for Steam Input
            # overlay: avoid forced fullscreen in some paths (already partial via virtual res)
        except:
            pass

        # Sync groups to session for PR2 ownership (creative: Game becomes thin view)
        if self.session:
            self.all_sprites = self.session.all_sprites
            self.enemies = self.session.enemies
            self.powerups = self.session.powerups
            self.asteroids = self.session.asteroids
            self.enemy_bullets = self.session.enemy_bullets
            self.bullets = self.session.bullets
            self.remote_bullets = self.session.remote_bullets
            self.missiles = self.session.missiles
            self.plasmas = self.session.plasmas
            self.bombs = self.session.bombs
            self.grenades = self.session.grenades
            self.particles = self.session.particles
        # Apply difficulty
        self.apply_difficulty()
        # Load high scores via PR3 persistence (deduped, evolvable, migrates legacy)
        pers = get_persistence()
        pers.migrate_if_needed()
        high_scores = pers.load_highscores()
        self.high_scores = high_scores
        self.high_score = self.high_scores[0] if self.high_scores else 0
        try:
            self.named_high_scores = pers.load_named_highscores()
        except Exception:
            self.named_high_scores = []
        # Initialize achievements
        self.achievements = {
            'kill_100': False,
            'reach_level_10': False,
            'combo_10': False,
            'boss_defeated': False,
            'kill_500': False,
            'survive_5_min': False
        }
        # Initialize boss spawn tracking
        self.boss_spawned = False
        self.just_defeated_boss = False
        # R4 Survival milestone shop + scoring persist
        self.just_survival_milestone = False
        self.preserve_run = False
        self._survival_milestones_hit = set()
        self.survival_milestone_interval = 60  # seconds between mid-run shops
        # R7: Survival pressure / difficulty ramp (time-based, not wall-clock)
        self.survival_pressure = 1.0
        self.survival_threat_tier = 0
        self.survival_threat_label = 'CALM'
        try:
            sb = pers.load_survival_best()
            self.best_survival_time = float(sb.get('best_time', 0) or 0)
            self.best_survival_score = int(sb.get('best_score', 0) or 0)
        except Exception:
            self.best_survival_time = 0.0
            self.best_survival_score = 0
        # Star speed for background
        self.star_speed = 1
        # Game over timer
        self.game_over_timer = 0
        # Death animation timer
        self.death_animation_timer = 0
        # Damage flash timer
        self.damage_flash_timer = 0
        # R5: floating damage numbers (x,y,value,ttl,crit,vy)
        self.damage_numbers = []
        self._score_saved_this_run = False
        # Shake timer
        self.shake_timer = 0
        self.shake_intensity = 0
        # Initialize game state
        self.state = MenuState(self)
        # Initialize joystick
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

    def spawn_damage_number(self, x, y, amount, crit=False):
        """R5: floating combat feedback. amount may be float; display rounds."""
        try:
            val = int(round(float(amount)))
        except Exception:
            return
        if val <= 0:
            return
        if not hasattr(self, 'damage_numbers') or self.damage_numbers is None:
            self.damage_numbers = []
        self.damage_numbers.append({
            'x': float(x),
            'y': float(y),
            'value': val,
            'ttl': 45 if crit else 36,
            'max_ttl': 45 if crit else 36,
            'crit': bool(crit),
            'vy': -1.35 if crit else -1.0,
            'vx': __import__('random').uniform(-0.45, 0.45),
        })
        # Cap to avoid HUD spam
        if len(self.damage_numbers) > 48:
            self.damage_numbers = self.damage_numbers[-48:]

    def update_damage_numbers(self):
        nums = getattr(self, 'damage_numbers', None) or []
        alive = []
        for n in nums:
            n['ttl'] -= 1
            n['x'] += n.get('vx', 0)
            n['y'] += n.get('vy', -1.0)
            n['vy'] = n.get('vy', -1.0) * 0.985
            if n['ttl'] > 0:
                alive.append(n)
        self.damage_numbers = alive

    def trigger_screen_shake(self, intensity=5, duration=15):
        """Trigger screen shake effect"""
        self.shake_timer = duration
        self.shake_intensity = intensity

    def _normalized_window_size(self, width=None, height=None):
        """R6: clamp windowed size to 960x720 (default) or 1280x720 (optional stretch)."""
        try:
            ww = int(width if width is not None else getattr(self, 'window_width', 960) or 960)
            wh = int(height if height is not None else getattr(self, 'window_height', 720) or 720)
        except Exception:
            ww, wh = 960, 720
        if ww >= 1280:
            return 1280, 720
        return 960, 720

    def _recreate_display(self):
        """Apply fullscreen / windowed size to the live display + config globals + starfields."""
        info = pygame.display.Info()
        global SCREEN_WIDTH, SCREEN_HEIGHT
        if getattr(self, 'fullscreen', False):
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
            flags = pygame.FULLSCREEN
        else:
            ww, wh = self._normalized_window_size()
            self.window_width, self.window_height = ww, wh
            SCREEN_WIDTH = ww
            SCREEN_HEIGHT = wh
            flags = 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        try:
            import config as cfg
            cfg.SCREEN_WIDTH = SCREEN_WIDTH
            cfg.SCREEN_HEIGHT = SCREEN_HEIGHT
        except Exception:
            pass
        self.stars = [(random.randint(0, 2 * SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(300)]
        self.slow_stars = [(random.randint(0, 2 * SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]
        self.fast_stars = [(random.randint(0, 2 * SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]

    def toggle_window_size(self):
        """R6: cycle windowed size 960x720 <-> 1280x720 (native virtual stretch), persist, apply if windowed."""
        cur_w, _ = self._normalized_window_size()
        if cur_w >= 1280:
            self.window_width, self.window_height = 960, 720
        else:
            self.window_width, self.window_height = 1280, 720
        try:
            pers = get_persistence()
            s = pers.load_settings()
            s['window_width'] = self.window_width
            s['window_height'] = self.window_height
            pers.save_settings(s)
        except Exception:
            pass
        if not getattr(self, 'fullscreen', False):
            self._recreate_display()
        print(f"[Stellar Vanguard] Window size: {self.window_width}x{self.window_height} (fullscreen={getattr(self, 'fullscreen', False)})")

    def toggle_fullscreen(self):
        """v3 polish: toggle between windowed and fullscreen, persist choice, recreate display + stars without losing run state."""
        self.fullscreen = not getattr(self, 'fullscreen', False)
        try:
            pers = get_persistence()
            s = pers.load_settings()
            s['fullscreen'] = self.fullscreen
            # Preserve chosen window size when returning to windowed (R6)
            ww, wh = self._normalized_window_size()
            self.window_width, self.window_height = ww, wh
            s['window_width'] = ww
            s['window_height'] = wh
            pers.save_settings(s)
        except Exception:
            pass
        self._recreate_display()
        print(f"[Stellar Vanguard] Fullscreen: {self.fullscreen} @ {SCREEN_WIDTH}x{SCREEN_HEIGHT}")


    # --- R7 Survival depth: time-based pressure ramp + milestone enrichment ---
    @staticmethod
    def compute_survival_pressure(survival_time):
        """Escalate pressure from survival_time (seconds). Tier every 60s past open."""
        try:
            t = max(0.0, float(survival_time or 0.0))
        except Exception:
            t = 0.0
        # +0.18 per minute, soft cap ~2.5 at ~8+ minutes
        pressure = 1.0 + (t / 60.0) * 0.18
        return float(min(2.5, max(1.0, pressure)))

    @staticmethod
    def survival_threat_meta(survival_time):
        """Return (tier_index, short_label) for HUD / banners."""
        try:
            t = max(0.0, float(survival_time or 0.0))
        except Exception:
            t = 0.0
        tier = int(t // 60)  # 0=<1m, 1=1m+, 2=2m+, ...
        labels = (
            'CALM', 'RISING', 'HOSTILE', 'SEVERE', 'CRITICAL',
            'OVERWHELMING', 'APOCALYPSE', 'LEGENDARY'
        )
        label = labels[min(tier, len(labels) - 1)]
        return tier, label

    def refresh_survival_pressure(self):
        """Sync pressure + threat label from current survival_time."""
        st = float(getattr(self, 'survival_time', 0.0) or 0.0)
        self.survival_pressure = self.compute_survival_pressure(st)
        tier, label = self.survival_threat_meta(st)
        self.survival_threat_tier = tier
        self.survival_threat_label = label
        return self.survival_pressure

    def survival_spawn_interval_frames(self):
        """Frames between Survival spawns; tightens with survival_time (not wall clock)."""
        st = float(getattr(self, 'survival_time', 0.0) or 0.0)
        # Base 45 frames (~0.75s); -3 per 30s survived; floor 8
        rate = 45 - int(st // 30) * 3
        # Mild settings nudge
        diff = getattr(self, 'difficulty', 'normal')
        if diff == 'easy':
            rate += 6
        elif diff == 'hard':
            rate -= 4
        return max(8, int(rate))

    def apply_difficulty(self):
        if self.difficulty == 'easy':
            self.enemy_speed = 2
            self.extra_lives = 2
            self.player.lives = 5 + self.extra_lives
        elif self.difficulty == 'normal':
            self.enemy_speed = 3
            self.extra_lives = 0
            self.player.lives = 3 + self.extra_lives
        elif self.difficulty == 'hard':
            self.enemy_speed = 4
            self.extra_lives = -1
            self.player.lives = 2 + self.extra_lives
        self.max_health = self.upgrades.get('max_health')
        self.player.max_health = self.max_health
        self.max_ammo = self.upgrades.get('max_ammo')
        self.player_speed = self.upgrades.get('player_speed')
        self.shield_duration = self.upgrades.get('shield_duration')
        self.player.speed = self.player_speed
        self.player.shield_duration = self.shield_duration
        self.damage = self.upgrades.get('damage')
        self.fire_rate = self.upgrades.get('fire_rate')
        self.crit_chance = self.upgrades.get('crit_chance')
        self.crit_damage = self.upgrades.get('crit_damage')
        self.coin_multiplier = self.upgrades.get('coin_multiplier')
        self.exp_multiplier = self.upgrades.get('exp_multiplier')
        self.weapon_damage = self.upgrades.get('weapon_damage')
        # R2: re-apply selected loadout on top of upgrade bases (absolute, not stacked)
        try:
            sess = getattr(self, 'session', None)
            ld = getattr(sess, 'current_loadout', None) if sess else None
            if ld is None:
                ld = getattr(self.player, 'current_loadout', None)
            if ld is not None:
                ld.apply_to_player(self.player, game=self)
                if sess is not None:
                    sess.current_loadout = ld
        except Exception:
            pass

    def reset_game(self):
        """Reset with improved delegation to session (combo/rank clears now in sim.reset_for_new_run too). Avoids desync on groups/particles list."""
        self.score = 0
        self.enemies_killed = 0
        self.bullets_fired = 0
        self.level = 1
        self.combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.style_rank = "D"
        self.style_points = 0
        self.death_animation_timer = 0
        self.show_mission_panel = False
        if not self.continuing:
            self.player.lives = 3 + self.extra_lives
        self.player.active_powerups.clear()  # Clear all active powerups
        self.player.powerup_timers.clear()  # Clear all powerup timers
        self.player.shield = False
        self.player.shield_timer = 0
        self.player.invincibility = False
        self.player.invincibility_timer = 0
        self.player.speed_multiplier = 1.0
        self.player.dash_speed = getattr(self.player, 'speed', self.player_speed) * 3
        self.player.ammo = self.max_ammo
        self.player.rect.centerx = SCREEN_WIDTH // 4  # Start in middle of left side
        self.player.rect.centery = SCREEN_HEIGHT // 2  # Start in middle vertically
        self.player.health = self.player.max_health
        self.boss_spawned = False
        self.just_defeated_boss = False
        self.just_survival_milestone = False
        self.preserve_run = False
        self._survival_milestones_hit = set()
        self.survival_time = 0.0
        self.survival_pressure = 1.0
        self.survival_threat_tier = 0
        self.survival_threat_label = 'CALM'
        self.freeze_timer = 0
        self.bg_x = 0
        self.wave = 1
        self.boss_wave = 0
        self.enemies_killed_this_level = 0
        self.wave_theme_name = ''
        self.wave_theme_id = None
        self.wave_banner_timer = 0
        self.boss_phase = 1
        self.boss_phase_announce_timer = 0
        self._survival_theme_clock = 0
        # Reset achievements
        self.achievements = {
            'kill_100': False,
            'reach_level_10': False,
            'combo_10': False,
            'boss_defeated': False,
            'kill_500': False,
            'survive_5_min': False
        }
        self.start_time = pygame.time.get_ticks()
        self.continuing = False

        if self.session:
            self.session.reset_for_new_run(player=self.player, score=0)
            # Re-sync all groups/refs for compat (prevents particles list desync etc from prior non-delegated clears)
            self.all_sprites = getattr(self.session, 'all_sprites', self.all_sprites)
            self.enemies = getattr(self.session, 'enemies', self.enemies)
            self.powerups = getattr(self.session, 'powerups', self.powerups)
            self.asteroids = getattr(self.session, 'asteroids', self.asteroids)
            self.enemy_bullets = getattr(self.session, 'enemy_bullets', self.enemy_bullets)
            self.bullets = getattr(self.session, 'bullets', self.bullets)
            self.remote_bullets = getattr(self.session, 'remote_bullets', self.remote_bullets)
            self.missiles = getattr(self.session, 'missiles', self.missiles)
            self.plasmas = getattr(self.session, 'plasmas', self.plasmas)
            self.bombs = getattr(self.session, 'bombs', self.bombs)
            self.grenades = getattr(self.session, 'grenades', self.grenades)
            self.particles = getattr(self.session, 'particles', self.particles)
            # sync combo/rank from sim
            self.combo = getattr(self.session, 'combo', 0)
            self.combo_timer = getattr(self.session, 'combo_timer', 0)
            self.max_combo = getattr(self.session, 'max_combo', 0)
            self.style_rank = getattr(self.session, 'style_rank', "D")
            self.style_points = getattr(self.session, 'style_points', 0)
            # ensure player attached
            if self.player not in self.all_sprites:
                self.all_sprites.add(self.player)
        else:
            # legacy direct clears (rare path)
            self.all_sprites.empty()
            self.bullets.empty()
            self.enemies.empty()
            self.powerups.empty()
            self.enemy_bullets.empty()
            self.particles = []
            self.asteroids.empty()
            self.plasmas.empty()
            self.all_sprites.add(self.player)

    def change_state(self, new_state):
        if self.state:
            self.state.exit()
        self.state = new_state
        self.state.enter()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.state.handle_event(event)

    def create_enemy(self):
        """Create an enemy of the appropriate type based on current wave.
        Delegates to session for PR2 (unified, registry-aware spawning).
        """
        if self.session:
            # Let session decide type (it uses pools + registries)
            return self.session.spawn_enemy()
        from config import ENEMY_SWARMER, ENEMY_ELITE, ENEMY_HEALER, ENEMY_TELEPORTER

        # Use level manager's current level for campaign mode, otherwise use wave
        level_or_wave = self.level_manager.current_level if self.game_mode == MODE_CAMPAIGN else self.wave
        
        # Determine enemy type from pools
        enemy_type = random.choice(enemy_pools.get(min(level_or_wave, MAX_LEVELS), enemy_pools[MAX_LEVELS]))

        # Create the appropriate enemy instance
        if enemy_type == ENEMY_SWARMER:
            return Swarmer(self)
        elif enemy_type == ENEMY_ELITE:
            return Elite(self)
        elif enemy_type == ENEMY_HEALER:
            return Healer(self)
        elif enemy_type == ENEMY_TELEPORTER:
            return Teleporter(self)
        else:
            # Create generic Enemy and set its type
            enemy = Enemy(self, enemy_type)
            return enemy

    def update_game_logic(self):
        """Slim delegation to SimulationWorld (PR2). The massive original body has been ported and creatively refactored into simulation.py for separation, testability, and extensibility (loadouts, registries, modifiers all hook here naturally).

        High-level mode/wave/boss/achievement logic can stay or move later; for now delegation + sync keeps everything working.
        """
        if self.session:
            self.session.update()
            # Sync groups for compatibility with renderer, states, old code paths during transition
            # Full list to complete PR2 delegation (prevents attribute errors in renderer/states/MP paths)
            self.all_sprites = getattr(self.session, 'all_sprites', self.all_sprites)
            self.enemies = getattr(self.session, 'enemies', self.enemies)
            self.powerups = getattr(self.session, 'powerups', self.powerups)
            self.asteroids = getattr(self.session, 'asteroids', self.asteroids)
            self.bullets = getattr(self.session, 'bullets', self.bullets)
            self.remote_bullets = getattr(self.session, 'remote_bullets', self.remote_bullets)
            self.missiles = getattr(self.session, 'missiles', self.missiles)
            self.plasmas = getattr(self.session, 'plasmas', self.plasmas)
            self.bombs = getattr(self.session, 'bombs', self.bombs)
            self.grenades = getattr(self.session, 'grenades', self.grenades)
            self.enemy_bullets = getattr(self.session, 'enemy_bullets', self.enemy_bullets)
            self.particles = getattr(self.session, 'particles', self.particles)
            # Stats sync (combo/style/rank/points) to prevent desync after decay or inc (renderer/HUD use game.*)
            self.combo = getattr(self.session, 'combo', self.combo)
            self.combo_timer = getattr(self.session, 'combo_timer', self.combo_timer)
            self.max_combo = getattr(self.session, 'max_combo', self.max_combo)
            self.style_rank = getattr(self.session, 'style_rank', self.style_rank)
            self.style_points = getattr(self.session, 'style_points', getattr(self, 'style_points', 0))
        else:
            # Legacy path (should be rare now)
            pass

        # Death animation timer (critical for respawn flow; was lost during PR2 slimming of update_game_logic)
        if getattr(self, 'death_animation_timer', 0) > 0:
            self.death_animation_timer -= 1

        # R5 floating damage numbers
        try:
            self.update_damage_numbers()
        except Exception:
            pass

        # Minimal high-level progression that was in the old method (can be moved fully later)
        if self.game_mode == MODE_CAMPAIGN:
            if self.level_manager.is_level_complete():
                reward = self.level_manager.get_level_reward()
                self.score += int(reward * self.exp_multiplier)
                self.coins += int((reward // 10) * self.coin_multiplier)
                if getattr(self.level_manager, 'current_level_data', {}).get('boss_required', False):
                    self.just_defeated_boss = True
                    # Modern post-boss generosity: small rank-based coin bonus (feeds shop choice; conservative)
                    rank_bonus = {'S': 180, 'A': 120, 'B': 80, 'C': 50}.get(getattr(self, 'style_rank', 'D'), 30)
                    self.coins += int(rank_bonus * getattr(self, 'coin_multiplier', 1.0))
                    self.score += int(rank_bonus * 0.5)  # style juice too
                if self.level_manager.next_level():
                    self.change_state(VictoryState(self))
                else:
                    self.change_state(GameOverState(self))
        elif not self.survival and self.score >= self.level * 200:
            self.level += 1

        if self.game_mode != MODE_CAMPAIGN and not self.survival and self.score >= self.wave * 500:
            self.wave += 1
            # R3: refresh themed composition + banner
            if self.session and hasattr(self.session, 'advance_wave'):
                try:
                    self.session.advance_wave(self.wave)
                except Exception:
                    pass
            elif self.session and hasattr(self.session, '_init_wave_theme'):
                self.session.wave = self.wave
                try:
                    self.session._init_wave_theme(self.wave)
                except Exception:
                    pass

        # R3 Survival: advance themed waves on a timer (no bosses; still get variety)
        if self.survival:
            self._survival_theme_clock = getattr(self, '_survival_theme_clock', 0) + 1
            if self._survival_theme_clock >= 45 * 60:  # ~45s
                self._survival_theme_clock = 0
                self.wave = int(getattr(self, 'wave', 1) or 1) + 1
                if self.session and hasattr(self.session, 'advance_wave'):
                    try:
                        self.session.advance_wave(self.wave)
                    except Exception:
                        pass
            # R4: real Survival clock + milestone shop (reuse post-boss ShopState claim-1 UX)
            if not hasattr(self, 'survival_time') or self.survival_time is None:
                self.survival_time = 0.0
            self.survival_time = float(self.survival_time) + (1.0 / 60.0)
            # R7: keep pressure/threat in sync with the Survival clock
            try:
                self.refresh_survival_pressure()
            except Exception:
                self.survival_pressure = self.compute_survival_pressure(self.survival_time)
            # 5-min achievement
            if self.survival_time >= 300 and not self.achievements.get('survive_5_min', False):
                self.achievements['survive_5_min'] = True
            interval = int(getattr(self, 'survival_milestone_interval', 60) or 60)
            hit = getattr(self, '_survival_milestones_hit', None)
            if hit is None:
                self._survival_milestones_hit = set()
                hit = self._survival_milestones_hit
            # Fire at 60, 120, 180... (not at 0)
            milestone = int(self.survival_time // interval) * interval
            if milestone >= interval and milestone not in hit:
                hit.add(milestone)
                step = milestone // interval  # 1 at 60s, 2 at 120s, ...
                stipend = 40 + step * 20
                # R7: mid-run milestones past 60s get escalating score juice + threat callout
                score_bonus = 0
                if milestone > interval:
                    score_bonus = 75 + (step - 1) * 50
                    self.score = int(getattr(self, 'score', 0)) + int(score_bonus * getattr(self, 'exp_multiplier', 1.0))
                self.coins = int(getattr(self, 'coins', 0)) + int(stipend * getattr(self, 'coin_multiplier', 1.0))
                self.just_survival_milestone = True
                self.preserve_run = True
                self.survival_milestone_label = f"{milestone // 60}m" if milestone % 60 == 0 else f"{milestone}s"
                # Banner reflects threat tier for late-run milestones
                tier, tlabel = self.survival_threat_meta(milestone)
                self.survival_threat_tier = tier
                self.survival_threat_label = tlabel
                if milestone > interval:
                    self.wave_theme_name = f"THREAT {tlabel} +{score_bonus}pts"
                self.wave_banner_timer = 90
                try:
                    self.change_state(ShopState(self))
                    return
                except Exception as ex:
                    print('Survival milestone shop note:', ex)

        if getattr(self, 'boss_phase_announce_timer', 0) > 0:
            self.boss_phase_announce_timer -= 1

        # Mission / objective tracking (supports visible missions HUD + boss approach bar)
        if self.game_mode == MODE_CAMPAIGN:
            if not hasattr(self, 'survival_time'):
                self.survival_time = 0.0
            # Campaign missions still use survival_time as level timer (separate from Survival mode above)
            if not self.survival:
                self.survival_time += 1.0 / 60.0
            if not hasattr(self, 'damage_taken_this_level'):
                self.damage_taken_this_level = 0
            if not hasattr(self, 'powerups_collected_this_level'):
                self.powerups_collected_this_level = 0

        # Boss trigger example (session may also signal)
        if not self.survival and self.wave > getattr(self, 'boss_wave', 3) and self.wave % 3 == 0:
            if not getattr(self, 'boss_spawned', False):
                self.change_state(BossIncomingState(self))
                self.boss_wave = self.wave

    def handle_enemy_death(self, enemy):
        """Delegate to session (PR2)."""
        if self.session:
            return self.session.handle_enemy_death(enemy)
        # fallback old (should not hit)
        enemy.kill()
        self.combo_timer = 0
        self.combo += 1
        if not hasattr(self, 'max_combo'):
            self.max_combo = 0
        self.max_combo = max(self.max_combo, self.combo)
        if not hasattr(self, 'style_points'):
            self.style_points = 0
        c = self.combo
        self.style_rank = "S" if c>=10 else ("A" if c>=7 else ("B" if c>=5 else ("C" if c>=3 else "D")))
        mult = 1.0
        sr = getattr(self, 'style_rank', 'D')
        if sr == "S": mult = 2.0
        elif sr == "A": mult = 1.5
        elif sr == "B": mult = 1.2
        self.style_points += int(10 * mult)
        self.score += int(10 * self.combo * self.exp_multiplier * mult)
        self.coins += int(1 * self.coin_multiplier)
        self.enemies_killed += 1
        self.enemies_killed_this_level += 1
        for _ in range(10):
            p = Particle(enemy.rect.centerx, enemy.rect.centery, RED, 'explosion')
            self.particles.append(p)
        if random.random() < 0.3:
            pu_type = random.choice(['rapid', 'spread', 'laser', 'shield', 'ammo', 'bomb', 'homing', 'missile', 'freeze', 'invincibility', 'health', 'slow', 'teleport', 'plasma', 'speed_boost', 'multishot', 'grenade', 'nuke', 'extra_life'])
            spawn_x = max(50, min(SCREEN_WIDTH - 50, enemy.rect.centerx))
            spawn_y = max(50, min(SCREEN_HEIGHT - 50, enemy.rect.centery))
            pu = PowerUp(spawn_x, spawn_y, pu_type, self)
            self.all_sprites.add(pu)
            self.powerups.add(pu)
        if self.explosion_sound:
            self.explosion_sound.play()

    def calculate_damage(self, base_damage, weapon_type=None):
        """Delegate to session (PR2)."""
        if self.session:
            return self.session.calculate_damage(base_damage, weapon_type)
        damage = base_damage * self.damage * self.weapon_damage
        if weapon_type:
            weapon_multipliers = {
                'shotgun': self.upgrades.get('shotgun_damage', 1.0),
                'flamethrower': self.upgrades.get('flamethrower_damage', 1.0),
                'lightning': self.upgrades.get('lightning_damage', 1.0),
                'blackhole': self.upgrades.get('blackhole_damage', 1.0),
                'freeze': self.upgrades.get('freeze_damage', 1.0)
            }
            damage *= weapon_multipliers.get(weapon_type, 1.0)
        if random.random() < self.crit_chance:
            damage *= self.crit_damage
        return damage

    def update_sound_volumes(self):
        if self.shoot_sound:
            self.shoot_sound.set_volume(self.sfx_volume)
        if self.explosion_sound:
            self.explosion_sound.set_volume(self.sfx_volume)
        if self.powerup_sound:
            self.powerup_sound.set_volume(self.sfx_volume)
        if self.hit_sound:
            self.hit_sound.set_volume(self.sfx_volume)
        if self.boss_sound:
            self.boss_sound.set_volume(self.sfx_volume)
        # Music is global
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except:
            pass

    def pause_music(self):
        try:
            pygame.mixer.music.pause()
        except:
            pass

    def resume_music(self):
        try:
            pygame.mixer.music.unpause()
        except:
            pass

    def play_music(self, track, fade_ms=800):
        """Switch to a specific background music track with fade. Tracks: 'menu_ambient', 'game_ambient', 'boss_music'"""
        path = f"sounds/{track}.wav"
        if not os.path.exists(path):
            return
        try:
            if self.current_music == track:
                return
            pygame.mixer.music.fadeout(fade_ms)
            # Small delay not possible easily, but fadeout + load is ok for our purposes
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
            self.current_music = track
        except Exception as e:
            print(f"Music switch note: {e}")

    def buy_max_ammo(self):
        self.upgrades.upgrade('max_ammo')
        self.max_ammo = self.upgrades.get('max_ammo')
        self.player.energy = self.max_ammo
        self.player.max_energy = self.max_ammo
        # PR3: persist via facade
        try:
            from persistence import get_persistence
            p = get_persistence()
            p.save_upgrades(self.upgrades.data if hasattr(self.upgrades, 'data') else {}, self.upgrades.levels if hasattr(self.upgrades, 'levels') else {})
            # save settings example in buy (PR12)
            p.save_settings({'music_volume': self.music_volume, 'sfx_volume': self.sfx_volume, 'difficulty': self.difficulty, 'colorblind_mode': getattr(self, 'colorblind_mode', None), 'mouse_aim': getattr(self, 'mouse_aim', False), 'window_width': getattr(self, 'window_width', 960), 'window_height': getattr(self, 'window_height', 720), 'fullscreen': getattr(self, 'fullscreen', False)})
        except:
            pass

    def buy_energy_regen(self):
        self.upgrades.upgrade('energy_regen')
        regen_rate = self.upgrades.get('energy_regen')
        self.player.energy_regen_rate = regen_rate

    def buy_speed(self):
        self.upgrades.upgrade('player_speed')
        self.player_speed = self.upgrades.get('player_speed')
        self.player.speed = self.player_speed

    def buy_shield_duration(self):
        self.upgrades.upgrade('shield_duration')
        self.shield_duration = self.upgrades.get('shield_duration')
        self.player.shield_duration = self.shield_duration

    def buy_max_health(self):
        self.upgrades.upgrade('max_health')
        self.max_health = self.upgrades.get('max_health')
        self.player.max_health = self.max_health

    def buy_damage(self):
        self.upgrades.upgrade('damage')

    def buy_fire_rate(self):
        self.upgrades.upgrade('fire_rate')
        self.fire_rate = self.upgrades.get('fire_rate')

    def buy_crit_chance(self):
        self.upgrades.upgrade('crit_chance')
        self.crit_chance = self.upgrades.get('crit_chance')

    def buy_crit_damage(self):
        self.upgrades.upgrade('crit_damage')
        self.crit_damage = self.upgrades.get('crit_damage')

    def buy_coin_multiplier(self):
        self.upgrades.upgrade('coin_multiplier')
        self.coin_multiplier = self.upgrades.get('coin_multiplier')

    def buy_exp_multiplier(self):
        self.upgrades.upgrade('exp_multiplier')
        self.exp_multiplier = self.upgrades.get('exp_multiplier')

    def buy_weapon_damage(self):
        self.upgrades.upgrade('weapon_damage')
        self.weapon_damage = self.upgrades.get('weapon_damage')

    def buy_shotgun_damage(self):
        self.upgrades.upgrade('shotgun_damage')

    def buy_flamethrower_damage(self):
        self.upgrades.upgrade('flamethrower_damage')

    def buy_lightning_damage(self):
        self.upgrades.upgrade('lightning_damage')

    def buy_blackhole_damage(self):
        self.upgrades.upgrade('blackhole_damage')

    def buy_freeze_damage(self):
        self.upgrades.upgrade('freeze_damage')

    def _generate_special_offers(self):
        """Generate random special offers and discounts"""
        import random
        self.special_offers = []

        # 30% chance to have special offers
        if random.random() < 0.3:
            # Select 1-3 random items for discount
            available_items = [item for item in self.shop_items if not item.get('dynamic_cost', False)]
            selected_items = random.sample(available_items, min(len(available_items), random.randint(1, 3)))

            for item in selected_items:
                discount_percent = random.choice([20, 30, 50])  # 20%, 30%, or 50% off
                original_cost = item['cost']
                discounted_cost = int(original_cost * (1 - discount_percent / 100))

                special_item = item.copy()
                special_item['name'] = f"{item['name']} ({discount_percent}% OFF!)"
                special_item['cost'] = discounted_cost
                special_item['original_cost'] = original_cost
                special_item['category'] = 'special'
                special_item['description'] = f"{item['description']} - SPECIAL OFFER!"
                special_item['icon'] = "🔥"  # Special offer icon

                self.special_offers.append(special_item)

        # Add special offers to shop items if any exist
        if self.special_offers:
            # Insert at the beginning of special category
            special_start = next((i for i, item in enumerate(self.shop_items) if item.get('category') == 'special'), len(self.shop_items))
            for i, offer in enumerate(self.special_offers):
                self.shop_items.insert(special_start + i, offer)

    def start_multiplayer_server(self, host=DEFAULT_SERVER_HOST, port=DEFAULT_SERVER_PORT):
        """Start a multiplayer server"""
        self.network = NetworkManager(self, is_server=True, host=host, port=port)
        if self.network.start():
            self.is_multiplayer = True
            self.is_server = True
            print("Multiplayer server started")
            return True
        return False

    def join_multiplayer_game(self, host=DEFAULT_SERVER_HOST, port=DEFAULT_SERVER_PORT):
        """Join a multiplayer game"""
        self.network = NetworkManager(self, is_server=False, host=host, port=port)
        if self.network.start():
            self.is_multiplayer = True
            self.is_server = False
            print("Joined multiplayer game")
            return True
        return False

    def stop_multiplayer(self):
        """Stop multiplayer connection"""
        if self.network:
            self.network.stop()
            self.network = None
        self.is_multiplayer = False
        self.is_server = False
        self.multiplayer_players.clear()

    def start_p2p_multiplayer(self, player_name="Player"):
        """Start P2P multiplayer"""
        from network import P2PNetworkManager
        self.network = P2PNetworkManager(self, player_name=player_name)
        if self.network.start():
            self.is_multiplayer = True
            self.is_p2p = True
            self.is_server = False  # In P2P, no server
            print("P2P multiplayer started")
            return True
        return False

    def stop_p2p_multiplayer(self):
        """Stop P2P multiplayer"""
        if self.network and self.is_p2p:
            self.network.stop()
            self.network = None
        self.is_multiplayer = False
        self.is_p2p = False
        self.multiplayer_players.clear()

    def update_multiplayer(self):
        """Update multiplayer state"""
        if not self.is_multiplayer or not self.network:
            return

        # Send player update
        if hasattr(self, 'player'):
            player_data = {
                "x": self.player.rect.centerx,
                "y": self.player.rect.centery,
                "health": self.player.health,
                "weapon": self.player.weapon,
                "powerups": list(self.player.active_powerups),
                "score": self.score
            }
            self.network.update_player(player_data)

            # Send projectile updates (detailed bullet data for rendering)
            if hasattr(self, 'bullets') and self.bullets:
                bullet_data = []
                for bullet in list(self.bullets)[:20]:  # Limit to first 20 bullets to avoid network spam
                    bullet_info = {
                        "x": bullet.rect.centerx,
                        "y": bullet.rect.centery,
                        "vel_x": getattr(bullet, 'vel_x', 0),
                        "vel_y": getattr(bullet, 'vel_y', 0),
                        "angle": getattr(bullet, 'angle', 0),
                        "homing": getattr(bullet, 'homing', False),
                        "is_enemy": getattr(bullet, 'is_enemy', False),
                        "type": type(bullet).__name__
                    }
                    bullet_data.append(bullet_info)

                self.network.send_message({
                    MSG_PROJECTILE_UPDATE: {
                        "id": self.network.player_id,
                        "projectiles": bullet_data,
                        "count": len(self.bullets)
                    }
                })
            else:
                # Send empty projectile update if no bullets
                self.network.send_message({
                    MSG_PROJECTILE_UPDATE: {
                        "id": self.network.player_id,
                        "projectiles": [],
                        "count": 0
                    }
                })

            # Send enemy updates (detailed enemy data for synchronization)
            if hasattr(self, 'enemies') and self.enemies:
                enemy_data = []
                for enemy in list(self.enemies)[:15]:  # Limit to first 15 enemies
                    enemy_info = {
                        "x": enemy.rect.centerx,
                        "y": enemy.rect.centery,
                        "health": getattr(enemy, 'health', 100),
                        "max_health": getattr(enemy, 'max_health', 100),
                        "type": type(enemy).__name__,
                        "alive": enemy.alive()
                    }
                    enemy_data.append(enemy_info)

                self.network.send_message({
                    MSG_ENEMY_UPDATE: {
                        "id": self.network.player_id,
                        "enemies": enemy_data,
                        "count": len(self.enemies)
                    }
                })
            else:
                # Send empty enemy update if no enemies
                self.network.send_message({
                    MSG_ENEMY_UPDATE: {
                        "id": self.network.player_id,
                        "enemies": [],
                        "count": 0
                    }
                })

        # Receive network messages
        while True:
            message = self.network.receive_message()
            if message is None:
                break

            if "welcome" in message:
                self.network.player_id = message["welcome"]["player_id"]
                print(f"Assigned player ID: {self.network.player_id}")
            elif MSG_PLAYER_UPDATE in message:
                update = message[MSG_PLAYER_UPDATE]
                player_id = update["id"]
                self.multiplayer_players[player_id] = update

                # Basic collision detection with other players
                if hasattr(self, 'player') and self.is_server:  # Only server handles collisions
                    other_x = update.get("x", 0)
                    other_y = update.get("y", 0)
                    distance = ((self.player.rect.centerx - other_x) ** 2 + (self.player.rect.centery - other_y) ** 2) ** 0.5
                    if distance < 50:  # Minimum distance between players
                        # Push players apart slightly
                        if distance > 0:
                            push_x = (self.player.rect.centerx - other_x) / distance * 2
                            push_y = (self.player.rect.centery - other_y) / distance * 2
                            self.player.rect.centerx += push_x
                            self.player.rect.centery += push_y
            elif MSG_PROJECTILE_UPDATE in message:
                update = message[MSG_PROJECTILE_UPDATE]
                player_id = update["id"]

                # Clear old remote bullets from this player
                for bullet in list(self.remote_bullets):
                    if hasattr(bullet, 'player_id') and bullet.player_id == player_id:
                        bullet.kill()

                # Create new remote bullets
                for bullet_data in update.get("projectiles", []):
                    remote_bullet = RemoteBullet(
                        bullet_data["x"], bullet_data["y"],
                        bullet_data["vel_x"], bullet_data["vel_y"],
                        bullet_data.get("angle", 0),
                        bullet_data.get("homing", False),
                        bullet_data.get("is_enemy", False),
                        bullet_data.get("type", "Bullet")
                    )
                    remote_bullet.player_id = player_id  # Mark which player this bullet belongs to
                    self.remote_bullets.add(remote_bullet)
                    self.all_sprites.add(remote_bullet)

                # Store projectile info for UI display
                if player_id not in self.multiplayer_players:
                    self.multiplayer_players[player_id] = {}
                self.multiplayer_players[player_id]["projectiles"] = {
                    "count": update.get("count", 0)
                }
            elif MSG_ENEMY_UPDATE in message:
                update = message[MSG_ENEMY_UPDATE]
                player_id = update["id"]

                # Only sync enemies if we're not the server (server is authoritative)
                if not self.is_server:
                    received_enemies = update.get("enemies", [])

                    # For each received enemy, find the closest matching local enemy
                    for received_enemy in received_enemies:
                        if not received_enemy.get("alive", True):
                            continue

                        received_x = received_enemy.get("x", 0)
                        received_y = received_enemy.get("y", 0)
                        received_type = received_enemy.get("type", "")
                        received_health = received_enemy.get("health", 100)

                        # Find the closest enemy of the same type within a reasonable distance
                        closest_enemy = None
                        min_distance = float('inf')

                        for enemy in list(self.enemies):
                            if type(enemy).__name__ != received_type:
                                continue

                            distance = ((enemy.rect.centerx - received_x) ** 2 + (enemy.rect.centery - received_y) ** 2) ** 0.5
                            if distance < min_distance and distance < 100:  # Within 100 pixels
                                min_distance = distance
                                closest_enemy = enemy

                        # Update the closest matching enemy
                        if closest_enemy and min_distance < 50:  # Closer match required for health sync
                            if hasattr(closest_enemy, 'health'):
                                # Smooth health interpolation to avoid jerky changes
                                current_health = closest_enemy.health
                                target_health = received_health
                                closest_enemy.health = current_health + (target_health - current_health) * 0.2

                            # Update position with interpolation
                            target_x = received_x
                            target_y = received_y
                            closest_enemy.rect.centerx += (target_x - closest_enemy.rect.centerx) * 0.05
                            closest_enemy.rect.centery += (target_y - closest_enemy.rect.centery) * 0.05

                # Store enemy info for UI display
                if player_id not in self.multiplayer_players:
                    self.multiplayer_players[player_id] = {}
                self.multiplayer_players[player_id]["enemies"] = {
                    "count": update.get("count", 0)
                }
            elif MSG_SCORE_UPDATE in message:
                update = message[MSG_SCORE_UPDATE]
                player_id = update["id"]
                if player_id not in self.multiplayer_players:
                    self.multiplayer_players[player_id] = {}
                self.multiplayer_players[player_id]["score"] = update["score"]

    def run(self):
        while self.running:
            try:
                self.handle_events()
                self.state.update()
                self.state.draw()
                pygame.display.flip()
                self.clock.tick(60)
            except Exception as e:
                import traceback
                print(f"Unexpected error: {e}")
                traceback.print_exc()
                self.running = False

        try:
            pygame.mixer.music.fadeout(300)
        except:
            pass
        pygame.quit()