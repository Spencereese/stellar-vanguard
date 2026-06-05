"""Roguelite Run Modifiers (Vanguard Protocols - PR7/8 creative stub).

Example modifiers that can be chosen between waves/levels for replayability.
Applied in simulation on reset or via game.

Creative: simple, stackable, risk/reward.

See DESIGN.
"""

class Modifier:
    def __init__(self, name, desc, apply_fn):
        self.name = name
        self.desc = desc
        self.apply_fn = apply_fn

    def apply(self, sim_or_game):
        self.apply_fn(sim_or_game)

# Examples (creative: actually affect sim/player for observable roguelite juice in run)
def glass_cannon(sim):
    if sim.player:
        sim.player.damage_mult = getattr(sim.player, 'damage_mult', 1.0) * 1.3
        # risk: e.g. note only; or lower health mult in full
    if hasattr(sim, 'glass_cannon_active'):
        sim.glass_cannon_active = True

def resourceful(sim):
    # more drops via flag (used in handle_enemy_death random? or powerup chance)
    sim.resourceful = True
    if hasattr(sim, 'game') and sim.game:
        sim.game.coin_multiplier = getattr(sim.game, 'coin_multiplier', 1.0) * 1.2

def overclock(sim):
    if sim.player:
        sim.player.fire_rate = getattr(sim.player, 'fire_rate', 1.0) * 1.25  # faster
    sim.overclock = True

MODIFIER_POOL = [
    Modifier("Glass Cannon", "+30% damage (risky play)", glass_cannon),
    Modifier("Resourceful", "+20% coins/powerup chance", resourceful),
    Modifier("Overclock", "Faster fire rate this run", overclock),
]

def get_random_modifiers(n=3):
    import random
    return random.sample(MODIFIER_POOL, min(n, len(MODIFIER_POOL)))
