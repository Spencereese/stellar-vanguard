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
