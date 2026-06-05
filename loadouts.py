"""Loadouts + Active Abilities (PR6 foundation).

Creative: Simple data-driven archetypes that modify player stats and provide active abilities with cooldowns.
Promotes existing dash, adds EMP (stun nearby), Repair.

See DESIGN for details. Hooked via simulation (apply on reset) and player.

This enables the "modular ship" pillar early.
"""

ARCHETYPES = {
    "scout": {
        "name": "Scout",
        "desc": "Fast and agile. Bonus speed and dash cooldown reduction.",
        "speed_mult": 1.3,
        "health_mult": 0.9,
        "dash_cooldown_mult": 0.7,
        "abilities": ["dash"],
    },
    "gunner": {
        "name": "Gunner",
        "desc": "High damage output. Bonus fire rate and crit.",
        "damage_mult": 1.25,
        "fire_rate_mult": 1.2,
        "abilities": ["dash", "emp"],
    },
    "tank": {
        "name": "Tank",
        "desc": "Tough and protective. High health and shield.",
        "health_mult": 1.4,
        "shield_duration_mult": 1.5,
        "abilities": ["dash", "repair"],
    },
}

class Loadout:
    def __init__(self, archetype="scout"):
        data = ARCHETYPES.get(archetype, ARCHETYPES["scout"])
        self.archetype = archetype
        self.name = data["name"]
        self.desc = data["desc"]
        self.stats = {k: v for k, v in data.items() if k.endswith("_mult")}
        self.abilities = data.get("abilities", ["dash"])

    def apply_to_player(self, player):
        """Apply stat mods to player (called on creation/reset)."""
        for k, v in self.stats.items():
            if k == "speed_mult" and hasattr(player, "speed"):
                player.speed *= v
            elif k == "health_mult" and hasattr(player, "max_health"):
                player.max_health = int(player.max_health * v)
                player.health = player.max_health
            # Add more as stats expand (damage etc via game or player)
        # Store for ability use
        player.current_loadout = self

# Basic ability activation example (called from input later)
def activate_ability(player, ability_name, game):
    if not hasattr(player, "current_loadout") or ability_name not in getattr(player.current_loadout, "abilities", []):
        return False
    if ability_name == "emp":
        # Stun nearby enemies
        for e in list(getattr(game, "enemies", [])):
            if hasattr(e, "frozen_timer"):
                e.frozen_timer = 120
                e.frozen = True
        # particles etc.
        return True
    if ability_name == "repair":
        player.health = min(player.health + 30, player.max_health)
        return True
    if ability_name == "dash":
        # creative: reset dash cooldown or temp speed boost
        if hasattr(player, 'dash_cooldown'):
            player.dash_cooldown = 0
        player.speed_multiplier = getattr(player, 'speed_multiplier', 1.0) * 1.5  # temp
        if hasattr(player, 'powerup_timers'):
            player.powerup_timers['dash_boost'] = 30  # short
        return True
    return False
