# Space Shooter Graphics Requirements

## Directory Structure
```
images/
├── player.png                 # Player ship (square, 1:1 ratio)
├── boss.png                   # Boss enemy (square, 1:1 ratio)
├── enemy_normal.png           # Normal enemy (square, 1:1 ratio)
├── enemy_fast.png             # Fast enemy (square, 1:1 ratio)
├── enemy_big.png              # Big enemy (square, 1:1 ratio)
├── enemy_shooter.png          # Shooting enemy (square, 1:1 ratio)
├── enemy_kamikaze.png         # Kamikaze enemy (square, 1:1 ratio)
├── enemy_tank.png             # Tank enemy (square, 1:1 ratio)
├── enemy_turret.png           # Turret enemy (square, 1:1 ratio)
├── enemy_bomber.png           # Bomber enemy (square, 1:1 ratio)
├── enemy_drone.png            # Drone enemy (square, 1:1 ratio)
├── enemy_zigzag.png           # Zigzag enemy (square, 1:1 ratio)
├── enemy_swarmer.png          # Swarmer enemy (square, 1:1 ratio)
├── enemy_elite.png            # Elite enemy (square, 1:1 ratio)
├── enemy_healer.png           # Healer enemy (square, 1:1 ratio)
├── enemy_teleporter.png       # Teleporter enemy (square, 1:1 ratio)
├── powerup_rapid.png          # Rapid fire power-up (square, 1:1 ratio)
├── powerup_spread.png         # Spread shot power-up (square, 1:1 ratio)
├── powerup_laser.png          # Laser power-up (square, 1:1 ratio)
├── powerup_shield.png         # Shield power-up (square, 1:1 ratio)
├── powerup_ammo.png           # Ammo power-up (square, 1:1 ratio)
├── powerup_bomb.png           # Bomb power-up (square, 1:1 ratio)
├── powerup_homing.png         # Homing missile power-up (square, 1:1 ratio)
├── powerup_missile.png        # Missile power-up (square, 1:1 ratio)
├── powerup_freeze.png         # Freeze power-up (square, 1:1 ratio)
├── powerup_invincibility.png  # Invincibility power-up (square, 1:1 ratio)
├── powerup_health.png         # Health power-up (square, 1:1 ratio)
├── powerup_slow.png           # Slow motion power-up (square, 1:1 ratio)
├── powerup_plasma.png         # Plasma power-up (square, 1:1 ratio)
├── powerup_teleport.png       # Teleport power-up (square, 1:1 ratio)
├── powerup_speed_boost.png    # Speed boost power-up (square, 1:1 ratio)
├── powerup_multishot.png      # Multishot power-up (square, 1:1 ratio)
├── powerup_grenade.png        # Grenade power-up (square, 1:1 ratio)
├── powerup_nuke.png           # Nuke power-up (square, 1:1 ratio)
└── powerup_extra_life.png     # Extra life power-up (square, 1:1 ratio)
```

## Image Specifications

### Format
- **File Format**: PNG with transparency support
- **Color Depth**: 32-bit RGBA
- **Background**: Transparent (alpha channel)

### Sizing
- **Aspect Ratio**: 1:1 (square images)
- **Recommended Sizes**: 32x32, 64x64, or 128x128 pixels
- **Scaling**: Images will be automatically scaled to fit game requirements
- **Flexibility**: Any square size works - the game will scale appropriately

### Scaling Behavior
- **Smooth Scaling**: Uses high-quality smooth scaling for non-pixel art
- **Automatic Sizing**: Your 1:1 ratio images will be scaled to match game object sizes
- **Quality Preservation**: Smooth scaling maintains image quality during resize

### Style Guidelines
- **Art Style**: Pixel art or clean vector graphics
- **Color Palette**: Vibrant, game-appropriate colors
- **Theme Support**: Images should work with different level themes (space, nebula, asteroid, alien, cyber)
- **Consistency**: Similar elements should have consistent visual style

## Fallback System
If image files are missing, the game will automatically generate procedural graphics:
- Player: Blue triangle ship
- Enemies: Colored polygons/shapes
- Power-ups: Colored squares (theme-aware)
- Boss: Red polygonal shape

## Implementation Details
- Images are loaded from `images/` directory relative to game root
- System supports PNG format with alpha transparency
- Automatic fallback to procedural generation if images missing
- Theme-aware color modification for procedural fallbacks

## Development Notes
- Test with and without images to ensure fallbacks work
- Images should be optimized for web/game use (small file sizes)
- Consider creating themed variants for different level themes
- **1:1 Ratio**: All images use square aspect ratios for consistency
- **Flexible Sizing**: Any square dimension works - scaling is automatic
