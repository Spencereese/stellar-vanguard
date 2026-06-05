# Instructions for Modifying Space Shooter v2.0

> **Note (v3 development):** A full design document for the sequel / auto-rework ("Space Shooter: Stellar Vanguard" v3.0) exists at [DESIGN_STELLAR_VANGUARD_v3.md](./DESIGN_STELLAR_VANGUARD_v3.md). It contains the 12-PRs implementation plan, architecture changes, and user decisions. Follow it for the ongoing rework. This file remains the practical guide for v2-era patterns until the transition completes.

## Overview
This is a Pygame-based space shooter game with multiple game modes, level-based progression, and advanced weapon systems. The game features campaign mode with themed levels, arcade mode, survival mode, and various enemy types with unique behaviors.

## Version 2.0 New Features
- **Multiple Game Modes**: Campaign, Arcade, Survival, and Challenge modes
- **Level System**: 10 themed levels with increasing difficulty and special enemies
- **New Enemy Types**: Swarmer, Elite, Healer, Teleporter enemies with unique behaviors
- **Advanced Weapons**: Shotgun, Flamethrower, Lightning, Black Hole, Freeze Beam
- **Themed Levels**: Space, Nebula, Asteroid, Alien, and Cyber themes
- **Currency System**: Coins for purchasing upgrades and weapons
- **Camera Effects**: Screen shake and particle effects
- **Enhanced UI**: Modern interface with animations and better feedback

## File Structure and Responsibilities

### Core Files
- **shooter.py**: Main entry point. Initializes Pygame and starts the game loop via `Game().run()`.
- **game.py**: Contains the `Game` class, which manages game state, logic, updates, collisions, and rendering. Uses state machine pattern for menus and gameplay.
- **config.py**: Defines constants such as screen dimensions, colors, FPS, and game mode/weapon constants.
- **level_manager.py**: Manages level progression, themes, and camera effects.

### Game Entities
- **player.py**: Defines the `Player` class. Handles movement, shooting with multiple weapon types, power-ups, health, ammo, etc.
- **enemies.py**: Defines enemy classes: `Enemy`, `Boss`, `Asteroid`, `Swarmer`, `Elite`, `Healer`, `Teleporter`. Each has unique update logic and behaviors.
- **projectiles.py**: Defines projectile classes: `Bullet`, `Laser`, `Missile`, `Bomb`, `Plasma`, `Grenade`, and new v2 weapons.
- **powerups.py**: Defines the `PowerUp` class for collectible items that grant temporary or permanent boosts.
- **particles.py**: Defines the `Particle` class for visual effects like explosions and trails.

### Supporting Files
- **upgrades.py**: Manages persistent upgrades stored in `upgrades.json`. Provides methods to get/set upgrade values.
- **renderer.py**: Handles drawing the game elements to the screen with theme support.
- **game_states.py**: Defines state classes for different game modes and menus.

### Data Files
- **highscore.txt**: Stores top 10 high scores, one per line.
- **upgrades.json**: Stores upgrade levels for permanent stat boosts.

## How to Make Changes

### Adding a New Enemy Type
1. Create a new enemy class in `enemies.py`, inheriting from `pygame.sprite.Sprite` or `Enemy`.
2. Implement `__init__`, `update`, and any special behavior methods.
3. Add the enemy type constant to `config.py`.
4. Update `enemy_pools` in `enemies.py` to include the new enemy in appropriate levels.
5. If needed, update the `create_enemy` method in `game.py` to handle the new type.

### Adding a New Weapon
1. Create a new projectile class in `projectiles.py`, inheriting from `Bullet` or appropriate base class.
2. Add the weapon constant to `config.py`.
3. Update the `shoot` method in `player.py` to handle the new weapon type.
4. Add the weapon to the shop in `game.py` with appropriate cost and effect.

### Adding a New Level Theme
1. Add theme constant to `config.py`.
2. Update `LevelManager._apply_theme_settings()` in `level_manager.py` to define theme colors.
3. Update `LevelManager._get_level_theme()` to assign themes to levels.
4. Modify `Renderer.draw_playing()` to use theme-specific backgrounds.

### Adding a New Game Mode
1. Add mode constant to `config.py`.
2. Update menu options in `game.py`.
3. Add mode handling in `MenuState.handle_event()` in `game_states.py`.
4. Implement mode-specific logic in `Game.update_game_logic()`.

## Game Modes

### Campaign Mode
- Progress through 10 themed levels
- Each level has specific enemy counts and boss requirements
- Unlock new weapons and abilities
- Persistent progression with coins

### Arcade Mode
- Classic endless gameplay
- Score-based progression
- All weapons and upgrades available

### Survival Mode
- Survive as long as possible
- Increasing difficulty over time
- Time-based scoring

### Challenge Mode (Future)
- Special challenge levels
- Limited resources
- Unique objectives

## Weapon System

### Basic Weapons (from v1)
- **Normal**: Standard bullet
- **Laser**: Piercing beam
- **Plasma**: Homing projectile
- **Missile**: Explosive projectile

### Advanced Weapons (v2)
- **Shotgun**: Spread shot with multiple pellets
- **Flamethrower**: Continuous area damage
- **Lightning**: Chain damage between enemies
- **Black Hole**: Pulls enemies in, then explodes
- **Freeze Beam**: Slows enemies with ice effects

## Enemy Behaviors

### Basic Enemies
- **Normal**: Standard moving enemy
- **Fast**: Quick enemy, harder to hit
- **Big**: High health, slow moving
- **Shooter**: Fires bullets at player
- **Tank**: High health, shoots multiple projectiles

### Advanced Enemies (v2)
- **Swarmer**: Moves in wavy patterns, appears in groups
- **Elite**: High health with shield, shoots at player
- **Healer**: Heals nearby enemies, must be prioritized
- **Teleporter**: Teleports around the screen unpredictably

## Power-up System
- **Rapid Fire**: Increased fire rate
- **Spread Shot**: Multiple projectiles
- **Laser**: Piercing beam weapon
- **Homing**: Projectiles seek enemies
- **Plasma**: Energy-based projectiles
- **Multishot**: Fires in all directions
- **Grenade**: Explosive area damage
- **Shield**: Temporary invincibility
- **Speed Boost**: Increased movement speed
- **Health Pack**: Restore health
- **Freeze**: Slow all enemies
- **Invincibility**: Complete immunity
- **Ammo**: Restore ammunition

## Upgrade System
- **Max Ammo**: Increase ammunition capacity
- **Player Speed**: Increase movement speed
- **Shield Duration**: Longer shield protection
- **Max Health**: Increase health capacity
- **Damage**: Increase weapon damage

## Development Environment
- **Python virtual environment**: `.venv/` directory
- **Dependencies**: Pygame (install via `pip install pygame`)
- **Run command**: `python shooter.py`
- **No build step**: Direct Python execution
- **Debugging**: Print statements in game loop, check console output
1. Update default values in `upgrades.py` `__init__`.
2. Add buy methods in `game.py` (e.g., `buy_new_upgrade`).
3. Add to shop items in `game.py` `__init__`.
4. Apply effects in `apply_difficulty` or relevant places.

### Adding New Game States
1. Create a new state class in `game_states.py`, inheriting from a base state.
2. Implement `enter`, `exit`, `update`, `draw`, `handle_event`.
3. In `game.py`, use `self.change_state(NewState(self))` to switch.

### Best Practices
- Use sprite groups for efficient collision detection.
- Keep game logic in `game.py`, entity-specific logic in their respective files.
- For persistent data, use JSON for complex data, text files for simple lists.
- Test changes by running the game and checking for errors (use `get_errors` after edits).
- When adding new assets (sounds, images), ensure paths are correct and files exist.
- Balance difficulty: Adjust spawn rates, health, damage in `game.py`.
- For UI changes, modify rendering in `renderer.py` or state draw methods.

### Common Patterns
- Timers: Use frame-based counters (e.g., `self.timer += 1`, check `if self.timer > 60` for 1 second at 60 FPS).
- Randomness: Use `random.random()` for probabilities, `random.randint()` for ranges.
- Colors: Use constants from `config.py`.
- Sounds: Load in `game.py` `__init__`, play with `.play()`.

### Debugging
- Use `print` statements for variables.
- Check sprite positions with `print(self.rect)`.
- Ensure all sprites are added to groups correctly.
- For performance, avoid unnecessary loops or computations in update methods.

This guide should help in understanding and modifying the codebase effectively.