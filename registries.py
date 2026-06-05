"""Data-driven registries for easy content addition (supports PR10/11 + PR6 loadouts).

Creative goal: Adding a new enemy or weapon should touch as few files as possible
(ideally just this + the implementation file + one pool update).

See DESIGN for the vision. Current: basic registry + factories + 2 example
new enemies (Cloaker, Splitter) + 1 new weapon (Railgun) registered.

The content subagent (if it finishes) or direct work will expand this heavily.
"""

from config import *
import random

# --- Enemy Registry ---
# Each entry: factory or class + default stats + behavior notes
ENEMY_REGISTRY = {}

def register_enemy(name, factory, base_health=1, base_speed=3, **meta):
    ENEMY_REGISTRY[name] = {
        "factory": factory,
        "base_health": base_health,
        "base_speed": base_speed,
        "meta": meta,
    }

def create_enemy_from_registry(game, etype, **kwargs):
    if etype not in ENEMY_REGISTRY:
        etype = "normal"  # safe fallback
    reg = ENEMY_REGISTRY[etype]
    # The actual Enemy subclass or factory knows how to init with game
    return reg["factory"](game, etype, **kwargs)

# --- Weapon Registry (very lightweight for now) ---
WEAPON_REGISTRY = {}

def register_weapon(name, projectile_class, **meta):
    WEAPON_REGISTRY[name] = {"projectile_class": projectile_class, "meta": meta}

def get_weapon_projectile_class(name):
    return WEAPON_REGISTRY.get(name, {}).get("projectile_class")


# --- Example new content registrations (creative) ---
# These will be expanded by the parallel content work or here.

# Cloaker / Splitter now prefer full classes defined in enemies.py (proper inheritance)
# (old _make factories kept for compat during load; classes override in enemies.py __init__ re-register)
try:
    from enemies import Cloaker, Splitter
    register_enemy("cloaker", lambda g, t=None: Cloaker(g, t), base_health=1, base_speed=4,
                   desc="Phases in/out of visibility. Prioritize or it harasses you.")
    register_enemy("splitter", lambda g, t=None: Splitter(g, t), base_health=2, base_speed=2.5,
                   desc="Splits into fast children on death. Area denial classic.")
except Exception:
    # fallback if classes not present yet
    pass

# Railgun: full class in projectiles.py (slow high pierce dmg)
try:
    from projectiles import Railgun
    register_weapon("railgun", Railgun, desc="Slow-firing piercing rail. High damage.")
except Exception:
    pass

# --- Helper to enrich enemy_pools (called from game/enemies during transition) ---
def get_enhanced_enemy_pool(wave):
    base = []  # will be filled by caller or we can import enemy_pools and extend
    # Creative: higher waves get the new types
    if wave >= 4:
        base += ["cloaker"] * 1
    if wave >= 6:
        base += ["splitter"] * 1
    return base
