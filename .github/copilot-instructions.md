# AI Coding Guidelines for Space Shooter Game

## Architecture Overview
This is a Pygame-based space shooter with a **state machine pattern** and **component-based entity system**. The `Game` class orchestrates everything through state transitions, while individual game entities (player, enemies, projectiles) are self-contained classes.

**Core Flow**: `shooter.py` → `Game().run()` → State machine (MenuState, PlayingState, etc.) → Entity updates → Renderer.draw()

**Key Architectural Patterns:**
- **State Machine**: Game states handle input, updates, and drawing for specific modes
- **Entity Component System**: Self-contained entity classes with update() methods
- **Centralized Rendering**: Renderer class manages all drawing with theme support
- **Network Layer**: Client-server multiplayer with message-based communication
- **Procedural Level Generation**: Algorithmic level creation with themes and scaling difficulty

## Key Design Patterns

### State Machine Pattern
- **Location**: `game_states.py` defines state classes inheriting from `GameState`
- **Usage**: `game.change_state(new_state)` transitions between menus, gameplay, and game over
- **Example**: Menu navigation uses `MenuState`, gameplay uses `PlayingState`
- **States handle**: Input, updates, and drawing for their specific mode

### Entity Component System
- **Player**: `player.py` - Movement, weapons, health, power-ups with energy/ammo management
- **Enemies**: `enemies.py` - AI behavior, health, spawning patterns with special types (Swarmer, Elite, Healer, Teleporter)
- **Projectiles**: `projectiles.py` - Movement, damage, special effects (homing, plasma, advanced weapons)
- **Power-ups**: `powerups.py` - Temporary boosts with timers and collision detection
- **Particles**: `particles.py` - Visual effects for explosions/damage with particle limits

### Sprite Group Management
- **Pattern**: Use `pygame.sprite.Group()` for collision detection
- **Groups**: `self.enemies`, `self.bullets`, `self.powerups`, etc. stored in Game class
- **Collisions**: `pygame.sprite.spritecollide()` between groups with dokill parameter
- **Example**: `pygame.sprite.spritecollide(self.player, self.enemies, False)`

### Network Communication Pattern
- **Architecture**: Client-server model with TCP sockets and message queues
- **Messages**: JSON-based with message types (MSG_PLAYER_UPDATE, MSG_SHOOT, etc.)
- **Synchronization**: 30Hz updates with interpolation for smooth movement
- **Threading**: Separate threads for send/receive operations

## Critical Workflows

### Adding New Game Entities
1. **Create class** in appropriate file (e.g., `enemies.py` for new enemy types)
2. **Inherit** from `pygame.sprite.Sprite` or existing entity base class
3. **Implement** `__init__`, `update()`, and custom methods
4. **Add to Game**: Initialize in `game.py` `__init__`, add to sprite groups
5. **Handle collisions**: Add collision logic in game's `update()` method
6. **Network sync**: Add to multiplayer message handling if needed

### Weapon/Projectiles System
- **Base class**: All projectiles inherit from `pygame.sprite.Sprite`
- **Player weapons**: Modified in `player.py` `shoot()` method with weapon switching
- **Special effects**: Homing missiles, plasma beams, bombs with area damage
- **Ammo management**: `self.energy` counter with regeneration and weapon-specific costs
- **Advanced weapons**: Shotgun, Flamethrower, Lightning, Black Hole, Freeze Beam with unique behaviors

### Upgrade System
- **Storage**: JSON persistence in `upgrades.json` with values and levels tracking
- **Access**: `self.upgrades.get('max_health')` returns current level-calculated value
- **Modification**: `self.upgrades.upgrade('damage')` increments level and recalculates value
- **Application**: Player stats updated from upgrade values on initialization
- **Economics**: Diminishing returns with `increment = base * (0.95 ** current_level)`

### State Transitions
- **Menu flow**: MenuState → PlayingState → GameOverState/ContinuePromptState
- **Boss fights**: PlayingState → BossIncomingState → PlayingState
- **Survival mode**: `self.survival = True` flag modifies gameplay loop
- **Multiplayer**: NetworkManager initialization and state synchronization

### Level and Theme System
- **Procedural Generation**: `_generate_level_data()` creates levels algorithmically
- **Themes**: Space, Nebula, Asteroid, Alien, Cyber with color schemes and backgrounds
- **Difficulty Scaling**: Health/speed multipliers increase with level number
- **Special Enemies**: Unlocked at specific level thresholds (Swarmer at 3, Elite at 5, etc.)

## Data Persistence
- **High scores**: `highscore.txt` - one score per line, sorted descending, max 10 entries
- **Upgrades**: `upgrades.json` - key-value pairs for permanent upgrades with level tracking
- **Loading**: Try/catch blocks handle missing files gracefully with defaults
- **Saving**: Automatic on upgrade purchases and game completion

## Rendering System
- **Centralized**: `Renderer` class in `renderer.py` handles all drawing
- **Methods**: `draw_menu()`, `draw_game()`, `draw_ui()` for different states
- **Themes**: Dynamic backgrounds, starfields, celestial bodies with parallax
- **Performance**: Pre-calculated positions, particle limits, efficient sprite batching
- **Effects**: Shadowed text, particle systems, gradient backgrounds, screen shake

## Configuration
- **Constants**: `config.py` defines colors, screen size, FPS, game modes, weapon types
- **Dynamic config**: Screen size adapts to fullscreen display info
- **Audio**: Optional sound files with graceful fallback to None
- **Multiplayer**: Network constants for host/port, message types, update rates

## Common Modification Patterns

### New Enemy Type
```python
class NewEnemy(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        # Setup image, rect, stats
        self.health = 50
        self.speed = 2
        self.game = game

    def update(self):
        # Movement and behavior logic
        self.rect.x -= self.speed
        # Add to enemy_pools in enemies.py for spawning
```

### New Power-up Effect
```python
# In game.py collision handling
elif pu.type == 'new_power':
    self.player.active_powerups.add('new_power')
    self.player.powerup_timers['new_power'] = 300  # 5 seconds at 60 FPS
    # Apply effect in player.update()
```

### New Weapon
```python
# In player.py shoot method
elif self.weapon == WEAPON_NEW:
    projectile = NewProjectile(self.rect.right, self.rect.centery)
    self.game.new_projectiles.add(projectile)
    self.energy -= new_weapon_cost
```

### New Game State
```python
class NewState(GameState):
    def __init__(self, game):
        super().__init__(game)
        # Initialize state-specific variables

    def handle_event(self, event):
        # Handle input for this state

    def update(self):
        # Update game logic for this state

    def draw(self):
        # Render this state's UI/game elements
```

## Development Environment
- **Python virtual environment**: `.venv/` directory (create with `python3 -m venv .venv`)
- **Dependencies**: Pygame (install via `pip install pygame`)
- **Run command**: `python3 shooter.py` (uses python3 for macOS compatibility)
- **No build step**: Direct Python execution with Pygame initialization
- **Debugging**: Print statements in game loop, check console output, use `test_game.py` for isolated testing
- **Testing**: `multiplayer_test.py` for network testing, `test_p2p_stun.py` for P2P connectivity

## File Organization Principles
- **One class per file**: Entity types separated for maintainability (player.py, enemies.py, etc.)
- **Import hierarchy**: `shooter.py` imports all modules, modules import from `config.py`
- **Global state**: Game instance passed to entities for inter-entity communication
- **Constants**: All magic numbers in `config.py` for easy tuning and consistency
- **Resource loading**: `utils.py` provides `load_image_with_fallback()` for graceful asset handling

## Network Development Patterns
- **Message format**: JSON dictionaries with message type keys and data payloads
- **Connection handling**: Automatic reconnection and timeout management
- **State synchronization**: Periodic full state syncs with delta updates
- **Thread safety**: Message queues for thread-safe communication between network and game threads

## Performance Considerations
- **Sprite groups**: Efficient collision detection with grouped sprites
- **Particle limits**: `PARTICLE_LIMIT = 200` prevents performance degradation
- **Update frequency**: 60 FPS with selective updates for different game elements
- **Memory management**: Object pooling for frequently created/destroyed entities
- **Rendering optimization**: Theme-based background caching and parallax calculations</content>
<parameter name="filePath">/Users/spencereese/Documents/shooter.py/.github/copilot-instructions.md