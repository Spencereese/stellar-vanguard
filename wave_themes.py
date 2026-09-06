"""R3: Themed wave compositions using existing enemy types.

No new enemies — only named pools / bias so waves feel distinct.
"""
from __future__ import annotations

import random

# id, display name, min_wave gate, biased type list (existing + registry types)
WAVE_THEMES = [
    {
        "id": "assault",
        "name": "ASSAULT WING",
        "min_wave": 1,
        "pool": ["normal", "fast", "shooter", "kamikaze", "zigzag"],
        "boss_minions": ["shooter", "kamikaze", "fast"],
    },
    {
        "id": "swarm",
        "name": "SWARM TIDE",
        "min_wave": 1,
        "pool": ["swarmer", "drone", "fast", "zigzag", "normal"],
        "boss_minions": ["swarmer", "drone", "fast"],
    },
    {
        "id": "armor",
        "name": "ARMOR COLUMN",
        "min_wave": 2,
        "pool": ["tank", "big", "turret", "bomber", "elite"],
        "boss_minions": ["tank", "bomber", "turret"],
    },
    {
        "id": "support",
        "name": "SUPPORT NEST",
        "min_wave": 3,
        "pool": ["healer", "elite", "shooter", "teleporter", "drone"],
        "boss_minions": ["healer", "elite", "shooter"],
    },
    {
        "id": "ghost",
        "name": "GHOST AMBUSH",
        "min_wave": 4,
        "pool": ["cloaker", "teleporter", "fast", "elite", "kamikaze"],
        "boss_minions": ["cloaker", "teleporter", "elite"],
    },
    {
        "id": "fracture",
        "name": "FRACTURE PROTOCOL",
        "min_wave": 6,
        "pool": ["splitter", "swarmer", "big", "drone", "tank"],
        "boss_minions": ["splitter", "swarmer", "tank"],
    },
    {
        "id": "mixed",
        "name": "MIXED PATROL",
        "min_wave": 1,
        "pool": None,  # fall back to enemy_pools + enhanced
        "boss_minions": ["tank", "shooter", "bomber"],
    },
]


def available_themes(wave: int):
    w = max(1, int(wave or 1))
    return [t for t in WAVE_THEMES if w >= int(t.get("min_wave", 1))]


def pick_wave_theme(wave: int, previous_id=None):
    """Pick a theme for this wave. Prefer not repeating the previous id."""
    opts = available_themes(wave)
    if not opts:
        opts = [WAVE_THEMES[-1]]
    if previous_id and len(opts) > 1:
        non_repeat = [t for t in opts if t["id"] != previous_id]
        if non_repeat:
            opts = non_repeat
    # Slight weight toward mixed late so default pools still appear
    weights = []
    for t in opts:
        weights.append(2 if t["id"] == "mixed" and wave >= 5 else 3)
    return random.choices(opts, weights=weights, k=1)[0]


def resolve_enemy_type(theme, wave: int, fallback_pool=None):
    """70% theme pool / 30% fallback (or pure fallback for mixed)."""
    if theme is None or theme.get("pool") is None:
        if fallback_pool:
            return random.choice(fallback_pool)
        return "normal"
    if fallback_pool and random.random() < 0.30:
        return random.choice(fallback_pool)
    return random.choice(theme["pool"])


def boss_minion_type(theme, phase: int = 1):
    """Minion types during boss fight, biased by active theme + phase."""
    if theme and theme.get("boss_minions"):
        pool = list(theme["boss_minions"])
    else:
        pool = ["tank", "shooter", "bomber"]
    if phase >= 3:
        pool = pool + ["swarmer", "elite"]
    if phase >= 2 and "healer" not in pool:
        pool = pool + ["healer"]
    return random.choice(pool)


# R8: Survival / themed boss archetypes reuse existing enemy types (no new content).
THEME_BOSS_VARIANT = {
    "assault": "shooter",
    "swarm": "swarmer",
    "armor": "tank",
    "support": "healer",
    "ghost": "teleporter",
    "fracture": "splitter",
    "mixed": "elite",
}

BOSS_VARIANT_META = {
    "tank": {
        "title": "TANK DREADNOUGHT",
        "body": (80, 100, 140),
        "core": (180, 200, 255),
        "hp_mult": 1.35,
        "minions": ["tank", "turret", "big"],
    },
    "swarmer": {
        "title": "SWARM MATRIARCH",
        "body": (160, 60, 180),
        "core": (255, 150, 255),
        "hp_mult": 0.85,
        "minions": ["swarmer", "drone", "fast"],
    },
    "elite": {
        "title": "ELITE OVERLORD",
        "body": (180, 40, 40),
        "core": (255, 200, 80),
        "hp_mult": 1.15,
        "minions": ["elite", "shooter", "bomber"],
    },
    "healer": {
        "title": "SUPPORT NEXUS",
        "body": (40, 140, 90),
        "core": (120, 255, 180),
        "hp_mult": 1.0,
        "minions": ["healer", "elite", "drone"],
    },
    "teleporter": {
        "title": "PHASE WRAITH",
        "body": (60, 60, 140),
        "core": (140, 180, 255),
        "hp_mult": 0.9,
        "minions": ["teleporter", "cloaker", "fast"],
    },
    "shooter": {
        "title": "ARTILLERY PRIME",
        "body": (160, 80, 40),
        "core": (255, 180, 60),
        "hp_mult": 1.05,
        "minions": ["shooter", "turret", "bomber"],
    },
    "bomber": {
        "title": "PAYLOAD TITAN",
        "body": (120, 50, 30),
        "core": (255, 100, 40),
        "hp_mult": 1.2,
        "minions": ["bomber", "kamikaze", "tank"],
    },
    "splitter": {
        "title": "FRACTURE CORE",
        "body": (100, 140, 60),
        "core": (200, 255, 100),
        "hp_mult": 1.1,
        "minions": ["splitter", "swarmer", "big"],
    },
}


def boss_variant_from_theme(theme, wave: int = 1):
    """Pick an existing-enemy-type boss archetype from the active theme."""
    if theme and theme.get("id") in THEME_BOSS_VARIANT:
        return THEME_BOSS_VARIANT[theme["id"]]
    # Fallback: rotate a few solid archetypes by wave so Survival still varies
    fallback = ["elite", "tank", "swarmer", "shooter", "healer", "teleporter"]
    return fallback[max(0, int(wave or 1) - 1) % len(fallback)]


def boss_variant_meta(variant: str):
    """Metadata for a boss archetype (title/colors/hp/minions)."""
    if variant in BOSS_VARIANT_META:
        return BOSS_VARIANT_META[variant]
    return BOSS_VARIANT_META["elite"]

