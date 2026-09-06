"""Loadouts + Active Abilities (PR6 foundation).

Creative: Simple data-driven archetypes that modify player stats and provide active abilities with cooldowns.
Promotes existing dash, adds EMP (stun nearby), Repair.

See DESIGN for details. Hooked via simulation (apply on reset) and player.

This enables the "modular ship" pillar early.

R2 polish: apply_to_player uses absolute bases (no stack); activate_ability never
crashes on missing particles/sounds.
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
        self.abilities = list(data.get("abilities", ["dash"]))

    def apply_to_player(self, player, game=None):
        """Apply stat mods from absolute bases (not multiply-on-multiply).

        Prefer game.player_speed / game.max_health when provided so PlayingState
        reset + apply_difficulty can re-apply the selected loadout cleanly.
        """
        if game is not None:
            base_speed = float(getattr(game, "player_speed", getattr(player, "speed", 5)) or 5)
            base_hp = int(getattr(game, "max_health", getattr(player, "max_health", 100)) or 100)
        else:
            # Snapshot once so re-apply does not stack
            if not hasattr(player, "_sv_base_speed"):
                player._sv_base_speed = float(getattr(player, "speed", 5) or 5)
            if not hasattr(player, "_sv_base_max_health"):
                player._sv_base_max_health = int(getattr(player, "max_health", 100) or 100)
            base_speed = float(player._sv_base_speed)
            base_hp = int(player._sv_base_max_health)

        try:
            player.speed = base_speed * float(self.stats.get("speed_mult", 1.0))
            player.max_health = int(base_hp * float(self.stats.get("health_mult", 1.0)))
            player.health = player.max_health
            player.dash_speed = player.speed * 3
            # Expose combat mults for systems that read them (no-op if unused)
            player.damage_mult = float(self.stats.get("damage_mult", 1.0))
            player.fire_rate_mult = float(self.stats.get("fire_rate_mult", 1.0))
            player.shield_duration_mult = float(self.stats.get("shield_duration_mult", 1.0))
            player.dash_cooldown_mult = float(self.stats.get("dash_cooldown_mult", 1.0))
            player.current_loadout = self
        except Exception as ex:
            # Never block play start on a loadout apply glitch
            print("Loadout apply note:", ex)
            try:
                player.current_loadout = self
            except Exception:
                pass


def _safe_ability_fx(game, player, color, count=8):
    """Best-effort particles; never raise if Particle/particles missing."""
    try:
        if game is None or player is None:
            return
        particles = getattr(game, "particles", None)
        if particles is None:
            return
        from particles import Particle
        cx = getattr(getattr(player, "rect", None), "centerx", 0)
        cy = getattr(getattr(player, "rect", None), "centery", 0)
        for _ in range(count):
            try:
                p = Particle(cx, cy, color, "smoke")
                if hasattr(particles, "append"):
                    particles.append(p)
                elif hasattr(game, "add_particle"):
                    game.add_particle(p)
            except Exception:
                break
    except Exception:
        pass


def _safe_play_sfx(game, name):
    """Play a named sound if present; never crash on None/missing mixer."""
    try:
        if game is None:
            return
        assets = getattr(game, "assets", None)
        if assets is None:
            return
        snd = assets.get_sound(name, volume=getattr(game, "sfx_volume", None))
        if snd is not None:
            snd.play()
    except Exception:
        pass


def activate_ability(player, ability_name, game):
    """Activate a loadout ability. Returns False if unavailable. Never crashes on FX."""
    try:
        if not hasattr(player, "current_loadout") or player.current_loadout is None:
            return False
        if ability_name not in getattr(player.current_loadout, "abilities", []):
            return False
        if ability_name == "emp":
            enemies = getattr(game, "enemies", None) or []
            try:
                for e in list(enemies):
                    try:
                        if hasattr(e, "frozen_timer"):
                            e.frozen_timer = 120
                            e.frozen = True
                    except Exception:
                        continue
            except Exception:
                pass
            _safe_ability_fx(game, player, (0, 255, 255), 15)
            _safe_play_sfx(game, "emp")
            return True
        if ability_name == "repair":
            try:
                player.health = min(player.health + 30, player.max_health)
            except Exception:
                pass
            _safe_ability_fx(game, player, (80, 255, 120), 10)
            _safe_play_sfx(game, "powerup")
            return True
        if ability_name == "dash":
            try:
                if hasattr(player, "dash_cooldown"):
                    player.dash_cooldown = 0
                player.speed_multiplier = getattr(player, "speed_multiplier", 1.0) * 1.5
                if hasattr(player, "powerup_timers"):
                    player.powerup_timers["dash_boost"] = 30
            except Exception:
                pass
            _safe_ability_fx(game, player, (255, 100, 100), 8)
            _safe_play_sfx(game, "dash")
            return True
        return False
    except Exception as ex:
        print("activate_ability note:", ex)
        return False
