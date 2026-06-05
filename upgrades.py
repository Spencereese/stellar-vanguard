import json

class Upgrades:
    def __init__(self):
        self.data = {'max_ammo': 100, 'player_speed': 5, 'shield_duration': 300, 'max_health': 100, 'damage': 1.0, 'fire_rate': 1.0, 'crit_chance': 0.0, 'crit_damage': 1.5, 'coin_multiplier': 1.0, 'exp_multiplier': 1.0, 'weapon_damage': 1.0, 'shotgun_damage': 1.0, 'flamethrower_damage': 1.0, 'lightning_damage': 1.0, 'blackhole_damage': 1.0, 'freeze_damage': 1.0, 'energy_regen': 0.5}
        self.levels = {}  # Track upgrade levels separately
        self.load()

    def load(self):
        try:
            with open('upgrades.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Check if it's the old format (just values) or new format (with levels)
                    if 'levels' in data:
                        self.data = data['values']
                        self.levels = data['levels']
                    else:
                        # Old format, convert to new format
                        self.data = data
                        self.levels = {}
                        for key in self.data:
                            base = self.get_base_value(key)
                            if key in ['max_ammo', 'player_speed', 'shield_duration', 'max_health']:
                                # For integer upgrades, calculate level
                                increment = self.get_increment(key)
                                if increment > 0:
                                    level = max(0, int((self.data[key] - base) / increment))
                                    self.levels[key] = level
                            else:
                                # For float upgrades, approximate level
                                increment = self.get_increment(key)
                                if increment > 0:
                                    level = max(0, int((self.data[key] - base) / increment))
                                    self.levels[key] = level
                else:
                    self.data = {'max_ammo': 100, 'player_speed': 5, 'shield_duration': 300, 'max_health': 100, 'damage': 1.0, 'fire_rate': 1.0, 'crit_chance': 0.0, 'crit_damage': 1.5, 'coin_multiplier': 1.0, 'exp_multiplier': 1.0, 'weapon_damage': 1.0, 'shotgun_damage': 1.0, 'flamethrower_damage': 1.0, 'lightning_damage': 1.0, 'blackhole_damage': 1.0, 'freeze_damage': 1.0, 'energy_regen': 0.5}
                    self.levels = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {'max_ammo': 100, 'player_speed': 5, 'shield_duration': 300, 'max_health': 100, 'damage': 1.0, 'fire_rate': 1.0, 'crit_chance': 0.0, 'crit_damage': 1.5, 'coin_multiplier': 1.0, 'exp_multiplier': 1.0, 'weapon_damage': 1.0, 'shotgun_damage': 1.0, 'flamethrower_damage': 1.0, 'lightning_damage': 1.0, 'blackhole_damage': 1.0, 'freeze_damage': 1.0, 'energy_regen': 0.5}
            self.levels = {}

    def save(self):
        with open('upgrades.json', 'w') as f:
            json.dump({'values': self.data, 'levels': self.levels}, f)

    def get(self, key, default=0):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def upgrade(self, key):
        current_level = self.levels.get(key, 0)
        
        if key == 'max_ammo':
            increment = 20 * (0.9 ** current_level)  # Diminishing returns
            self.data[key] += max(5, increment)  # Minimum increment of 5
        elif key == 'energy_regen':
            increment = 0.1 * (0.95 ** current_level)  # Energy regen upgrade
            self.data[key] += max(0.02, increment)
        elif key == 'player_speed':
            increment = 1 * (0.95 ** current_level)
            self.data[key] += max(0.2, increment)
        elif key == 'shield_duration':
            increment = 50 * (0.9 ** current_level)
            self.data[key] += max(10, increment)
        elif key == 'max_health':
            increment = 20 * (0.9 ** current_level)
            self.data[key] += max(5, increment)
        elif key == 'damage':
            increment = 0.2 * (0.95 ** current_level)
            self.data[key] += max(0.05, increment)
        elif key == 'fire_rate':
            increment = 0.1 * (0.95 ** current_level)
            self.data[key] += max(0.02, increment)
        elif key == 'crit_chance':
            increment = 0.05 * (0.9 ** current_level)
            self.data[key] += max(0.01, increment)
        elif key == 'crit_damage':
            increment = 0.1 * (0.95 ** current_level)
            self.data[key] += max(0.02, increment)
        elif key == 'coin_multiplier':
            increment = 0.25 * (0.9 ** current_level)
            self.data[key] += max(0.05, increment)
        elif key == 'exp_multiplier':
            increment = 0.2 * (0.95 ** current_level)
            self.data[key] += max(0.04, increment)
        elif key == 'weapon_damage':
            increment = 0.15 * (0.95 ** current_level)
            self.data[key] += max(0.03, increment)
        elif key == 'shotgun_damage':
            increment = 0.2 * (0.95 ** current_level)
            self.data[key] += max(0.05, increment)
        elif key == 'flamethrower_damage':
            increment = 0.25 * (0.95 ** current_level)
            self.data[key] += max(0.05, increment)
        elif key == 'lightning_damage':
            increment = 0.3 * (0.95 ** current_level)
            self.data[key] += max(0.05, increment)
        elif key == 'blackhole_damage':
            increment = 0.4 * (0.95 ** current_level)
            self.data[key] += max(0.1, increment)
        elif key == 'freeze_damage':
            increment = 0.2 * (0.95 ** current_level)
            self.data[key] += max(0.05, increment)
        
        self.levels[key] = current_level + 1
        self.save()

    def get_level(self, key):
        """Get the upgrade level (how many times this upgrade has been purchased)"""
        base_value = self.get_base_value(key)
        current_value = self.data.get(key, base_value)
        return max(0, int((current_value - base_value) / self.get_increment(key)))

    def get_base_value(self, key):
        """Get the base value for an upgrade"""
        base_values = {
            'max_ammo': 100, 'player_speed': 5, 'shield_duration': 300,
            'max_health': 100, 'damage': 1.0, 'fire_rate': 1.0,
            'crit_chance': 0.0, 'crit_damage': 1.5, 'coin_multiplier': 1.0,
            'exp_multiplier': 1.0, 'weapon_damage': 1.0, 'shotgun_damage': 1.0,
            'flamethrower_damage': 1.0, 'lightning_damage': 1.0, 'blackhole_damage': 1.0,
            'freeze_damage': 1.0
        }
        return base_values.get(key, 0)

    def get_increment(self, key):
        """Get the base increment for an upgrade"""
        increments = {
            'max_ammo': 20, 'player_speed': 1, 'shield_duration': 50,
            'max_health': 20, 'damage': 0.2, 'fire_rate': 0.1,
            'crit_chance': 0.05, 'crit_damage': 0.1, 'coin_multiplier': 0.25,
            'exp_multiplier': 0.2, 'weapon_damage': 0.15, 'shotgun_damage': 0.2,
            'flamethrower_damage': 0.25, 'lightning_damage': 0.3, 'blackhole_damage': 0.4,
            'freeze_damage': 0.2
        }
        return increments.get(key, 1)

    def get_upgrade_cost(self, key):
        """Calculate upgrade cost based on current level"""
        level = self.levels.get(key, 0)
        base_costs = {
            'max_ammo': 300, 'player_speed': 400, 'shield_duration': 350,
            'max_health': 450, 'damage': 400, 'fire_rate': 500,
            'crit_chance': 600, 'crit_damage': 550, 'coin_multiplier': 700,
            'exp_multiplier': 650, 'weapon_damage': 450, 'shotgun_damage': 800,
            'flamethrower_damage': 1000, 'lightning_damage': 1200, 'blackhole_damage': 1500,
            'freeze_damage': 900
        }
        base_cost = base_costs.get(key, 300)
        # Cost increases exponentially with level
        return int(base_cost * (1.5 ** level))