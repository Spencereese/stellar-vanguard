import pygame
import math
import random
import os
from config import *
from enemies import Boss
from particles import Particle

class Renderer:
    def __init__(self, game):
        self.game = game
        # Base virtual resolution for UI scaling (width x height)
        self.base_width = 1280
        self.base_height = 720
        self.ui_scale = 1.0
        self._virtual_surface = None

    def _create_virtual_surface(self):
        # recreate if needed
        if (self._virtual_surface is None or
            self._virtual_surface.get_width() != self.base_width or
            self._virtual_surface.get_height() != self.base_height):
            self._virtual_surface = pygame.Surface((self.base_width, self.base_height))
        return self._virtual_surface

    def _render_virtual_and_blit(self, draw_callback, game, *cb_args):
        """Helper: draw into virtual surface using draw_callback(game, surface, *cb_args),
        then stretch to exactly the current window size so the game always takes up the *entire* window (no letterboxing/black bars)."""
        virtual = self._create_virtual_surface()
        # Clear virtual surface
        virtual.fill((0, 0, 0))
        # While drawing into virtual, set ui_scale to 1.0 so draw functions use base coords
        old_scale = getattr(self, 'ui_scale', 1.0)
        self.ui_scale = 1.0
        try:
            draw_callback(game, virtual, *cb_args)
        finally:
            self.ui_scale = old_scale

        sw = SCREEN_WIDTH
        sh = SCREEN_HEIGHT
        # Always stretch to fill the whole window (content may be slightly distorted on non-16:9 windows, but always uses 100% of the window area).
        scaled = pygame.transform.smoothscale(virtual, (sw, sh))

        # Minimal colorblind accessibility stub (user decision + PR12 scope).
        # Very cheap: optional desaturate or simple shift. Controlled by game.colorblind_mode or similar.
        filtered = self._apply_minimal_colorblind_filter(game, scaled)
        game.screen.fill((0, 0, 0))  # still clear in case of prior direct draws
        game.screen.blit(filtered, (0, 0))
        pygame.display.flip()

    def render_shadowed_text(self, text, color, font):
        shadow = font.render(text, True, BLACK)
        main = font.render(text, True, color)
        surface = pygame.Surface((main.get_width() + 2, main.get_height() + 2), pygame.SRCALPHA)
        surface.blit(shadow, (2, 2))
        surface.blit(main, (0, 0))
        return surface

    def _apply_minimal_colorblind_filter(self, game, surf):
        """Minimal, cheap colorblind support (desaturate for protan/deutan simulation or simple remap).
        No-op unless game.colorblind_mode is truthy (e.g. 'desat' or 'protan').
        This is the cheap stub; full filters can be expanded in PR12 polish.
        Creative: support protan (red-green swap-ish), deutan, tritan (blue-yellow) via channel mix.
        """
        mode = getattr(game, 'colorblind_mode', None) or getattr(game, 'settings', {}).get('colorblind', None)
        if not mode:
            return surf
        try:
            arr = pygame.surfarray.pixels3d(surf)
            if mode in ('desat', 'grayscale', True):
                gray = (0.3 * arr[:,:,0] + 0.59 * arr[:,:,1] + 0.11 * arr[:,:,2]).astype('uint8')
                arr[:,:,0] = gray
                arr[:,:,1] = gray
                arr[:,:,2] = gray
            elif mode in ('protan', 'redgreen'):
                # simple protan: reduce red, boost green/blue mix
                r, g, b = arr[:,:,0].astype(float), arr[:,:,1].astype(float), arr[:,:,2].astype(float)
                arr[:,:,0] = (0.567 * r + 0.433 * g).astype('uint8')
                arr[:,:,1] = (0.558 * g + 0.442 * b).astype('uint8')
                arr[:,:,2] = b.astype('uint8')
            elif mode in ('deutan', 'greenred'):
                r, g, b = arr[:,:,0].astype(float), arr[:,:,1].astype(float), arr[:,:,2].astype(float)
                arr[:,:,0] = (0.625 * r + 0.375 * g).astype('uint8')
                arr[:,:,1] = (0.7 * g + 0.3 * b).astype('uint8')
                arr[:,:,2] = b.astype('uint8')
            elif mode in ('tritan', 'blueyellow'):
                r, g, b = arr[:,:,0].astype(float), arr[:,:,1].astype(float), arr[:,:,2].astype(float)
                arr[:,:,0] = r.astype('uint8')
                arr[:,:,1] = (0.95 * g + 0.05 * b).astype('uint8')
                arr[:,:,2] = (0.433 * g + 0.567 * b).astype('uint8')
            del arr
            return surf
        except Exception:
            # If surfarray not available or any issue, silently skip (minimal scope)
            return surf

    def draw_background_to_surface(self, game, surface):
        """Draw the game background to a surface (theme color or custom image)"""
        theme_bg = game.level_manager.background_color
        surface.fill(theme_bg)

        # Try to load custom background image
        if not hasattr(self, 'background_image'):
            try:
                # Prefer seamless endless v3 background (generated + code mirrored tiling for no visible seams)
                bg_candidates = ['images/background_seamless.png', 'images/background_v3.png', 'images/background.png']
                loaded = None
                for cand in bg_candidates:
                    if os.path.exists(cand):
                        loaded = pygame.image.load(cand)
                        break
                if loaded:
                    if loaded.get_alpha() is not None:
                        self.background_image = loaded.convert_alpha()
                    else:
                        self.background_image = loaded.convert()
                    img_ratio = self.background_image.get_width() / self.background_image.get_height()
                    target_height = SCREEN_HEIGHT
                    target_width = int(target_height * img_ratio)
                    self.background_image = pygame.transform.smoothscale(self.background_image, (target_width, target_height))
                else:
                    self.background_image = None
            except (pygame.error, FileNotFoundError, NameError):
                self.background_image = None

        # Draw custom background image if available - seamless endless scroll using reverse/flip technique
        if self.background_image:
            surface.fill(theme_bg)
            bg_width = self.background_image.get_width()
            # Prepare flipped version for seamless "end and begin with inverted" look (user requested)
            if not hasattr(self, '_bg_flipped') or self._bg_flipped is None:
                try:
                    self._bg_flipped = pygame.transform.flip(self.background_image, True, False)
                except:
                    self._bg_flipped = self.background_image
            # Scroll using double period (normal + flipped) to hide transition lines
            # The seam between image and its reverse often looks continuous for nebulae/space
            period = bg_width * 2
            x_pos = game.bg_x
            # Draw enough copies to cover screen + margin, alternating normal/flipped
            while x_pos < SCREEN_WIDTH + bg_width:
                # even tile: normal image
                surface.blit(self.background_image, (x_pos, 0))
                # next tile: reversed/flipped image for seamless join
                surface.blit(self._bg_flipped, (x_pos + bg_width, 0))
                x_pos += period
            # Update scroll - slower for more epic feel, negative for leftward movement (enemies come from right)
            game.bg_x -= 0.3
            if game.bg_x <= -period:
                game.bg_x += period

    def draw_starfield_to_surface(self, game, surface):
        """Draw the animated starfield background to a surface - polished with twinkle/size animation"""
        import math
        star_colors = game.level_manager.star_colors
        t = pygame.time.get_ticks() / 1000.0
        # Draw themed stars with animation
        for i in range(len(game.slow_stars)):
            game.slow_stars[i] = ((game.slow_stars[i][0] - 0.5) % (2*SCREEN_WIDTH), game.slow_stars[i][1])
        for star in game.slow_stars:
            tw = 0.6 + 0.4 * math.sin(t * 0.8 + star[0]*0.01)
            r = max(1, int(1 * tw))
            pygame.draw.circle(surface, star_colors[0], star, r)

        for i in range(len(game.stars)):
            game.stars[i] = ((game.stars[i][0] - game.star_speed) % (2*SCREEN_WIDTH), game.stars[i][1])
        for star in game.stars:
            tw = 0.7 + 0.3 * math.sin(t * 1.5 + star[1]*0.02)
            r = max(1, int(1.5 * tw))
            pygame.draw.circle(surface, star_colors[1] if len(star_colors) > 1 else star_colors[0], star, r)

        for i in range(len(game.fast_stars)):
            game.fast_stars[i] = ((game.fast_stars[i][0] - 2) % (2*SCREEN_WIDTH), game.fast_stars[i][1])
        for star in game.fast_stars:
            tw = 0.5 + 0.5 * math.sin(t * 2.0 + star[0]*0.03)
            r = max(1, int(2 * tw))
            pygame.draw.circle(surface, star_colors[2] if len(star_colors) > 2 else star_colors[0], star, r)

    def draw_celestial_bodies_to_surface(self, game, surface):
        """Draw background celestial bodies with parallax and enhanced effects to a surface"""
        if self.background_image:
            return  # Skip if using custom background

        parallax_sun = 0.05
        parallax_blue = 0.1
        parallax_orange = 0.15
        parallax_moon = 0.2
        parallax_nebula = 0.02

        # Nebula background effect (subtle gas clouds)
        if game.level_manager.level_theme in ['nebula', 'cosmic', 'void']:
            for i in range(3):
                nebula_x = (SCREEN_WIDTH * i * 0.3 + game.bg_x * parallax_nebula) % (SCREEN_WIDTH * 1.5)
                nebula_surf = pygame.Surface((200, 150), pygame.SRCALPHA)
                
                # Create nebula cloud effect
                for _ in range(20):
                    x = random.randint(0, 200)
                    y = random.randint(0, 150)
                    size = random.randint(30, 80)
                    alpha = random.randint(10, 30)
                    color = random.choice([(100, 50, 150, alpha), (150, 50, 100, alpha), (50, 100, 150, alpha)])
                    pygame.draw.circle(nebula_surf, color, (x, y), size)
                
                surface.blit(nebula_surf, (nebula_x - 100, SCREEN_HEIGHT // 2 - 75))

        # Enhanced distant sun with corona effect
        sun_x = (SCREEN_WIDTH - 80 + game.bg_x * parallax_sun) % (SCREEN_WIDTH + 160)
        sun_y = 80
        
        # Sun corona (outer glow)
        corona_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        for i in range(10):
            alpha = 20 - i * 2
            pygame.draw.circle(corona_surf, (255, 200, 100, alpha), (60, 60), 60 - i * 5)
        surface.blit(corona_surf, (sun_x - 60, sun_y - 60))
        
        # Main sun
        pygame.draw.circle(surface, (255, 255, 150), (int(sun_x), sun_y), 40)
        
        # Sun surface details
        for i in range(8):
            angle = i * 45
            x = sun_x + math.cos(math.radians(angle)) * 35
            y = sun_y + math.sin(math.radians(angle)) * 35
            pygame.draw.circle(surface, (255, 220, 100), (int(x), int(y)), 3)

        # Enhanced blue planet with atmosphere and rings
        blue_x = (SCREEN_WIDTH//4 + game.bg_x * parallax_blue) % (SCREEN_WIDTH + 200)
        blue_y = SCREEN_HEIGHT//4
        
        # Planet shadow
        pygame.draw.circle(surface, (20, 30, 60), (int(blue_x + 5), int(blue_y + 5)), 52)
        
        # Planet body
        pygame.draw.circle(surface, (80, 120, 200), (int(blue_x), blue_y), 50)
        
        # Atmospheric glow
        atmosphere_surf = pygame.Surface((110, 110), pygame.SRCALPHA)
        pygame.draw.circle(atmosphere_surf, (100, 150, 255, 80), (55, 55), 55)
        surface.blit(atmosphere_surf, (blue_x - 55, blue_y - 55))
        
        # Ice caps
        pygame.draw.ellipse(surface, (200, 220, 255), (blue_x - 25, blue_y - 45, 50, 15))
        pygame.draw.ellipse(surface, (200, 220, 255), (blue_x - 25, blue_y + 30, 50, 15))
        
        # Enhanced ring system
        ring_surf = pygame.Surface((160, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(ring_surf, (150, 180, 220, 150), (0, 0, 160, 40))
        pygame.draw.ellipse(ring_surf, (120, 150, 200, 100), (5, 5, 150, 30))
        surface.blit(ring_surf, (blue_x - 80, blue_y - 20))

        # Enhanced orange gas giant
        orange_x = (3*SCREEN_WIDTH//4 + game.bg_x * parallax_orange) % (SCREEN_WIDTH + 160)
        orange_y = SCREEN_HEIGHT//3
        
        # Planet body with storm bands
        pygame.draw.circle(surface, (200, 120, 50), (int(orange_x), orange_y), 40)
        
        # Storm bands
        for i in range(3):
            band_y = orange_y - 15 + i * 15
            pygame.draw.ellipse(surface, (150, 80, 30), (orange_x - 35, band_y, 70, 8))
        
        # Great red spot
        pygame.draw.ellipse(surface, (100, 30, 20), (orange_x - 15, orange_y - 10, 20, 12))

        # Enhanced moon with craters
        moon_x = (SCREEN_WIDTH//2 + game.bg_x * parallax_moon) % (SCREEN_WIDTH + 100)
        moon_y = 2*SCREEN_HEIGHT//3
        
        # Moon body
        pygame.draw.circle(surface, (120, 120, 120), (int(moon_x), moon_y), 25)
        
        # Craters
        crater_positions = [(moon_x - 8, moon_y - 5), (moon_x + 5, moon_y + 8), (moon_x - 5, moon_y + 10)]
        for cx, cy in crater_positions:
            pygame.draw.circle(surface, (80, 80, 80), (int(cx), int(cy)), random.randint(3, 6))
            # Crater highlights
            pygame.draw.circle(surface, (150, 150, 150), (int(cx - 1), int(cy - 1)), 2)

    def draw_sprites_to_surface(self, game, surface):
        """Draw all game sprites to a surface"""
        game.all_sprites.draw(surface)
        self.draw_multiplayer_players_to_surface(game, surface)

    def draw_multiplayer_players_to_surface(self, game, surface):
        """Draw multiplayer players to a surface (placeholder for now)"""
        # TODO: Implement multiplayer player drawing
        pass

    def draw_sprites(self, game):
        """Draw all game sprites"""
        game.all_sprites.draw(self.game.screen)
        self.draw_multiplayer_players(game)

    def draw_multiplayer_players(self, game):
        """Draw multiplayer players (placeholder for now)"""
        # TODO: Implement multiplayer player drawing
        pass

    def draw_particles_to_surface(self, game, surface):
        """Draw particle effects to a surface - polished with rotation, trails, and image support for explosions"""
        assets = None
        try:
            from utils import get_asset_manager
            assets = get_asset_manager()
            exp_img = assets.load_image('explosion_v3.png', (64, 64))  # cached
        except:
            exp_img = None

        for p in game.particles:
            px, py = int(p.x), int(p.y)
            size = max(1, int(getattr(p, 'size', 2)))
            alpha = max(0, min(255, int(getattr(p, 'alpha', 255))))
            color = getattr(p, 'color', (255, 255, 255))

            if p.particle_type == 'explosion' and exp_img is not None:
                # Use the polished explosion asset for big bursts, with rotation and scale
                rot = getattr(p, 'rotation', 0)
                try:
                    scaled = pygame.transform.smoothscale(exp_img, (size*3, size*3))
                    if rot != 0:
                        scaled = pygame.transform.rotate(scaled, rot)
                    scaled.set_alpha(alpha)
                    rect = scaled.get_rect(center=(px, py))
                    surface.blit(scaled, rect)
                except:
                    # fallback circle
                    particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surf, (*color, alpha), (size, size), size)
                    surface.blit(particle_surf, (px - size, py - size))
            elif p.particle_type == 'spark' and hasattr(p, 'trail') and p.trail:
                # Draw trail for sparks
                for i, (tx, ty) in enumerate(p.trail):
                    talpha = int(alpha * (i + 1) / len(p.trail))
                    tsize = max(1, size - (len(p.trail) - i))
                    particle_surf = pygame.Surface((tsize * 2, tsize * 2), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surf, (*color, talpha), (tsize, tsize), tsize)
                    surface.blit(particle_surf, (int(tx - tsize), int(ty - tsize)))
                # current spark
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*color, alpha), (size, size), size)
                surface.blit(particle_surf, (px - size, py - size))
            else:
                # Standard circle with alpha and optional rotation (for fire/plasma etc)
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*color, alpha), (size, size), size)
                rot = getattr(p, 'rotation', 0)
                if rot != 0:
                    try:
                        particle_surf = pygame.transform.rotate(particle_surf, rot)
                    except:
                        pass
                surface.blit(particle_surf, (px - size, py - size))

            # New impressive types
            ptype = getattr(p, 'particle_type', '')
            if ptype == 'ring':
                r = max(2, int(getattr(p, 'size', 8)))
                ring_surf = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (*color, max(10, alpha)), (r+2, r+2), r, max(1, r//7))
                surface.blit(ring_surf, (px - r-2, py - r-2))
            elif ptype in ('thrust', 'muzzle'):
                # Elongated bright streak for engine/muzzle
                streak = pygame.Surface((size*3, size), pygame.SRCALPHA)
                pygame.draw.ellipse(streak, (*color, alpha), (0, 0, size*3, size))
                # point backward for thrust feel
                surface.blit(streak, (px - size*2, py - size//2))
            elif ptype == 'debris':
                # Tiny tumbling metal chunk
                deb = pygame.Surface((size+2, size+2), pygame.SRCALPHA)
                pygame.draw.rect(deb, (*color, alpha), (1,1,size,size))
                if getattr(p, 'rotation', 0):
                    deb = pygame.transform.rotate(deb, p.rotation)
                surface.blit(deb, (px-size//2, py-size//2))
            elif ptype == 'ghost':
                # Faded afterimage rectangle (ship-like silhouette hint)
                gsurf = pygame.Surface((size*2, size), pygame.SRCALPHA)
                pygame.draw.ellipse(gsurf, (*color, max(15, alpha//2)), (0,0,size*2,size))
                surface.blit(gsurf, (px - size, py - size//2))

    def draw_player_effects_to_surface(self, game, surface):
        """Draw player special effects to a surface (death, shield, invincibility)"""
        # Draw death animation effect on player
        if game.death_animation_timer > 0:
            overlay_alpha = int(150 + 105 * math.sin(game.death_animation_timer * 0.3))
            overlay_surf = pygame.Surface(game.player.rect.size, pygame.SRCALPHA)
            overlay_surf.fill((255, 0, 0, overlay_alpha))
            surface.blit(overlay_surf, game.player.rect)

            flash_intensity = (game.death_animation_timer // 3) % 3
            if flash_intensity > 0:
                for ring in range(flash_intensity):
                    ring_radius = 20 + ring * 15
                    pygame.draw.circle(surface, (255, 50, 0), game.player.rect.center, ring_radius, 2)

                for _ in range(8):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.randint(25, 70)
                    x = game.player.rect.centerx + math.cos(angle) * distance
                    y = game.player.rect.centery + math.sin(angle) * distance
                    spark_size = random.randint(2, 4)
                    pygame.draw.circle(surface, (255, 150, 0), (int(x), int(y)), spark_size)

            # Reworked explosion asset for much better death animation
            try:
                from utils import get_asset_manager
                assets = get_asset_manager()
                exp = assets.load_image('explosion_v3.png', (96, 96))
                t = game.death_animation_timer
                # Pulse scale and alpha
                s = 0.8 + (t % 10) / 12.0
                ew, eh = int(exp.get_width() * s), int(exp.get_height() * s)
                if ew > 4 and eh > 4:
                    exp_s = pygame.transform.smoothscale(exp, (ew, eh))
                    alpha = max(60, int(255 * (t / 30.0)))
                    exp_s.set_alpha(alpha)
                    ex = game.player.rect.centerx - ew // 2
                    ey = game.player.rect.centery - eh // 2
                    surface.blit(exp_s, (ex, ey))
            except Exception:
                pass

        # Draw shield and invincibility effects
        if game.player.shield:
            pygame.draw.circle(surface, BLUE, game.player.rect.center, 30, 2)
        if game.player.invincibility:
            pygame.draw.circle(surface, MAGENTA, game.player.rect.center, 35, 2)

    def draw_boss_health_to_surface(self, game, surface):
        """Draw boss health bar to a surface if boss is present"""
        if game.boss_spawned:
            for e in game.enemies:
                if isinstance(e, Boss):
                    # Scale boss health bar to UI scale
                    vw = surface.get_width()
                    vh = surface.get_height()
                    bar_width = int(300)
                    bar_height = int(25)
                    bar_x = vw // 2 - bar_width // 2
                    bar_y = int(20)

                    # Background
                    pygame.draw.rect(surface, (64, 64, 64), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
                    pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height))

                    # Health bar
                    health_ratio = max(0.0, min(1.0, float(e.health) / float(max(1, e.max_health))))
                    current_width = int(bar_width * health_ratio)
                    bar_color = GREEN if health_ratio > 0.6 else YELLOW if health_ratio > 0.3 else RED
                    pygame.draw.rect(surface, bar_color, (bar_x, bar_y, current_width, bar_height))

                    # Border
                    pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

                    # Boss name and health text (R3: show phase)
                    phase = getattr(e, "phase", getattr(game, "boss_phase", 1))
                    wind = " [CHARGING!]" if getattr(e, "is_winding_up", False) else ""
                    title = getattr(e, "boss_title", None) or "BOSS"
                    boss_text = f"{title} P{phase}{wind} - {int(e.health)}/{int(e.max_health)}"
                    # Render boss text scaled: render then scale down/up to match UI scale
                    text_surf = self.render_shadowed_text(boss_text, WHITE, game.font)
                    if self.ui_scale != 1.0:
                        try:
                            target_w = int(text_surf.get_width() * self.ui_scale)
                            target_h = int(text_surf.get_height() * self.ui_scale)
                            if target_w > 0 and target_h > 0:
                                text_surf = pygame.transform.smoothscale(text_surf, (target_w, target_h))
                        except Exception:
                            pass
                    text_x = vw // 2 - text_surf.get_width() // 2
                    text_y = bar_y + bar_height + int(5)
                    surface.blit(text_surf, (text_x, text_y))

    def draw_hud_to_surface(self, game, surface):
        """Draw the heads-up display to a surface (health, ammo, score, etc.)"""
        # Scale HUD sizes according to UI scale. Use target surface size if available.
        vw = surface.get_width()
        vh = surface.get_height()
        s = max(0.5, float(vw) / float(self.base_width))

        # Health bar (bottom left)
        bar_width = int(150)
        bar_height = int(16)
        bar_x = int(10)
        bar_y = int(vh - 30)
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        if game.player.health > 0:
            try:
                health_ratio = float(game.player.health) / float(max(1, game.player.max_health))
            except Exception:
                health_ratio = 0.0
            health_width = int(health_ratio * bar_width)
            pygame.draw.rect(surface, GREEN, (bar_x, bar_y, health_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), max(1, int(1 * s)))

        # Health text (scaled surface)
        health_text = f"{int(game.player.health)}/{int(game.player.max_health)}"
        health_surf = self.render_shadowed_text(health_text, WHITE, game.tiny_font)
        surface.blit(health_surf, (bar_x + bar_width + 10, bar_y + 2))

        # Energy display (bottom right)
        energy_text = f"Energy: {int(game.player.energy)}/{int(game.player.max_energy)}"
        energy_surf = self.render_shadowed_text(energy_text, CYAN, game.small_font)
        energy_x = vw - energy_surf.get_width() - 10
        energy_y = vh - 35
        surface.blit(energy_surf, (energy_x, energy_y))

        # Score display (top left)
        score_text = f"Score: {game.score:,}"
        score_surf = self.render_shadowed_text(score_text, WHITE, game.small_font)
        surface.blit(score_surf, (10, 10))

        # R3: compact wave theme tag under score
        try:
            theme = getattr(game, "wave_theme_name", "") or ""
            if theme:
                wt = f"W{getattr(game, 'wave', 1)} {theme}"
                wt_surf = self.render_shadowed_text(wt, CYAN, game.tiny_font)
                surface.blit(wt_surf, (10, 28))
        except Exception:
            pass

        # R4: Survival timer + next milestone + best
        try:
            if getattr(game, 'survival', False):
                st = float(getattr(game, 'survival_time', 0) or 0)
                mins = int(st) // 60
                secs = int(st) % 60
                interval = int(getattr(game, 'survival_milestone_interval', 60) or 60)
                nxt = ((int(st) // interval) + 1) * interval
                best_t = float(getattr(game, 'best_survival_time', 0) or 0)
                threat = getattr(game, 'survival_threat_label', None) or 'CALM'
                pressure = float(getattr(game, 'survival_pressure', 1.0) or 1.0)
                event_chip = ''
                if getattr(game, 'survival_event_active', False):
                    ek = int(getattr(game, 'survival_event_kills', 0) or 0)
                    en = int(getattr(game, 'survival_event_kills_needed', 0) or 0)
                    elabel = getattr(game, 'survival_event_label', 'ELITE') or 'ELITE'
                    event_chip = f"  |  {elabel} {ek}/{en}"
                timer_txt = f"SURVIVE {mins:02d}:{secs:02d}  next shop {nxt}s  {threat} x{pressure:.2f}  best {int(best_t)}s{event_chip}"
                ts = self.render_shadowed_text(timer_txt, GOLD, game.tiny_font)
                surface.blit(ts, (10, 42))
        except Exception:
            pass

        # Combo display
        if game.combo > 1:
            combo_text = f"Combo: x{game.combo}"
            combo_surf = self.render_shadowed_text(combo_text, YELLOW, game.small_font)
            surface.blit(combo_surf, (10, 35))

        # === Compact Mission Panel (always visible) ===
        # Small boxed "Mission Panel" in top-left for expanded feel
        try:
            if hasattr(game, 'level_manager') and game.level_manager:
                mdata = game.level_manager.get_mission_data()
                panel_x, panel_y = 8, 55
                panel_w, panel_h = 280, 38

                # Panel background
                panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                panel.fill((15, 20, 35, 210))
                pygame.draw.rect(panel, (80, 120, 200), (0, 0, panel_w, panel_h), 1)
                surface.blit(panel, (panel_x, panel_y))

                # Title
                title = self.render_shadowed_text("MISSION", (100, 180, 255), game.tiny_font)
                surface.blit(title, (panel_x + 6, panel_y + 3))

                # Description (short)
                desc = mdata.get('description', 'Survive')
                desc_surf = self.render_shadowed_text(desc[:38], (200, 220, 240), game.tiny_font)
                surface.blit(desc_surf, (panel_x + 6, panel_y + 18))

                # Mini progress bar on the right of panel
                p = max(0.0, min(1.0, mdata.get('progress', 0.0)))
                bar_x = panel_x + panel_w - 72
                bar_y = panel_y + 22
                bar_w = 64
                pygame.draw.rect(surface, (40, 50, 70), (bar_x, bar_y, bar_w, 8))
                if p > 0:
                    fill_c = (80, 200, 120) if not mdata.get('is_boss') else (255, 100, 80)
                    pygame.draw.rect(surface, fill_c, (bar_x, bar_y, int(bar_w * p), 8))
                pygame.draw.rect(surface, (150, 180, 220), (bar_x, bar_y, bar_w, 8), 1)
        except Exception:
            pass

        # Boss approach / proximity bar (prominent when relevant, below the mission panel)
        boss_prog = 0.0
        try:
            if hasattr(game, 'level_manager') and game.level_manager:
                boss_prog = game.level_manager.get_boss_approach()
            elif getattr(game, 'boss_fight', False):
                killed = getattr(game, 'enemies_killed_this_level', 0)
                req = max(10, getattr(game, 'enemies_required', 20))
                boss_prog = min(1.0, killed / float(req))
        except Exception:
            pass

        if boss_prog > 0.01 or getattr(game, 'boss_fight', False):
            bbar_w = int(220)
            bbar_h = 11
            bbar_x = 10
            bbar_y = 96   # moved down a bit to sit under the new mission panel
            # Back
            pygame.draw.rect(surface, (30, 5, 5), (bbar_x, bbar_y, bbar_w, bbar_h))
            pygame.draw.rect(surface, (120, 30, 30), (bbar_x, bbar_y, bbar_w, bbar_h), 1)
            # Fill (red -> bright as it approaches)
            fill_w = int(bbar_w * boss_prog)
            fill_col = (255, 90, 60) if boss_prog < 0.85 else (255, 200, 50)
            if fill_w > 0:
                pygame.draw.rect(surface, fill_col, (bbar_x, bbar_y, fill_w, bbar_h))
            # Label
            blabel = self.render_shadowed_text("BOSS APPROACH", (255, 140, 100), game.tiny_font)
            surface.blit(blabel, (bbar_x + bbar_w + 8, bbar_y - 1))

        # Weapon display (top right)
        weapon_name = str(game.player.weapon).title()
        weapon_surf = self.render_shadowed_text(f"Weapon: {weapon_name}", CYAN, game.small_font)
        weapon_x = vw - weapon_surf.get_width() - 10
        weapon_y = 10
        surface.blit(weapon_surf, (weapon_x, weapon_y))

        # Powerup status effects (top center)
        if game.player.active_powerups:
            status_y = 10
            status_x = vw // 2 - 100
            for effect in game.player.active_powerups:
                if effect in game.player.powerup_timers:
                    time_left = max(0, game.player.powerup_timers[effect] // 60)  # seconds
                    effect_text = f"{effect.title()}: {time_left}s"
                    effect_surf = self.render_shadowed_text(effect_text, GREEN, game.tiny_font)
                    surface.blit(effect_surf, (status_x, status_y))
                    status_y += 20

        # Lives display (next to health)
        lives_text = f"Lives: {game.player.lives}"
        lives_color = GREEN if game.player.lives > 2 else (YELLOW if game.player.lives > 1 else RED)
        lives_surf = self.render_shadowed_text(lives_text, lives_color, game.small_font)
        lives_x = bar_x + bar_width + 10
        lives_y = bar_y - 25
        surface.blit(lives_surf, (lives_x, lives_y))

        # R3: centered wave theme banner (short-lived)
        try:
            timer = int(getattr(game, "wave_banner_timer", 0) or 0)
            name = getattr(game, "wave_theme_name", "") or ""
            if timer > 0 and name:
                alpha = 255 if timer > 40 else max(40, int(255 * (timer / 40.0)))
                title = f"WAVE {getattr(game, 'wave', 1)}"
                sub = name
                title_s = self.render_shadowed_text(title, GOLD, game.font)
                sub_s = self.render_shadowed_text(sub, CYAN, game.small_font)
                # fade via temp surfaces
                for surf_txt, yoff in ((title_s, -18), (sub_s, 16)):
                    tmp = pygame.Surface(surf_txt.get_size(), pygame.SRCALPHA)
                    tmp.blit(surf_txt, (0, 0))
                    tmp.set_alpha(alpha)
                    surface.blit(tmp, (vw // 2 - tmp.get_width() // 2, vh // 2 + yoff - 40))
            # Boss phase announce
            btimer = int(getattr(game, "boss_phase_announce_timer", 0) or 0)
            if btimer > 0 and getattr(game, "boss_spawned", False):
                phase = getattr(game, "boss_phase", 1)
                msg = f"BOSS PHASE {phase}"
                ms = self.render_shadowed_text(msg, RED if phase >= 3 else YELLOW, game.font)
                surface.blit(ms, (vw // 2 - ms.get_width() // 2, 55))
        except Exception:
            pass


    def draw_expanded_mission_panel(self, game, surface):
        """Full featured expandable mission / objectives panel.
        Called when game.show_mission_panel is True (toggled with TAB in PlayingState).
        Rich details: multiple progress bars, bonuses, boss emphasis.
        """
        vw, vh = surface.get_width(), surface.get_height()

        # Centered semi-transparent panel
        pw, ph = int(vw * 0.72), int(vh * 0.58)
        px = (vw - pw) // 2
        py = int(vh * 0.18)

        # Backdrop + frame
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((12, 16, 28, 235))
        pygame.draw.rect(panel, (70, 110, 180), (0, 0, pw, ph), 2)
        # Inner accent
        pygame.draw.rect(panel, (40, 70, 120), (4, 4, pw-8, ph-8), 1)
        surface.blit(panel, (px, py))

        # Try to get rich data
        mdata = {}
        try:
            if hasattr(game, 'level_manager') and game.level_manager:
                mdata = game.level_manager.get_mission_data()
        except Exception:
            mdata = {'title': 'Mission', 'description': 'Survive', 'progress': 0.0, 'trackers': [], 'is_boss': False, 'estimated_reward': 0}

        # Header
        header = self.render_shadowed_text("OBJECTIVES  •  " + mdata.get('title', 'CURRENT MISSION'), (120, 180, 255), game.font)
        surface.blit(header, (px + 20, py + 12))

        # Primary objective box
        obj_y = py + 55
        pygame.draw.rect(surface, (25, 30, 45, 200), (px + 16, obj_y, pw - 32, 52))
        pygame.draw.rect(surface, (100, 140, 200), (px + 16, obj_y, pw - 32, 52), 1)

        prim = self.render_shadowed_text("PRIMARY: " + mdata.get('description', 'Complete objectives'), (230, 240, 255), game.small_font)
        surface.blit(prim, (px + 26, obj_y + 8))

        # Overall progress bar for primary
        p = max(0.0, min(1.0, mdata.get('progress', 0.0)))
        bar_w = pw - 70
        bar_x = px + 35
        bar_y = obj_y + 32
        pygame.draw.rect(surface, (20, 25, 40), (bar_x, bar_y, bar_w, 12))
        fill_col = (90, 210, 130) if not mdata.get('is_boss') else (255, 110, 80)
        if p > 0:
            pygame.draw.rect(surface, fill_col, (bar_x, bar_y, int(bar_w * p), 12))
        pygame.draw.rect(surface, (160, 190, 230), (bar_x, bar_y, bar_w, 12), 1)

        pct = int(p * 100)
        pct_txt = self.render_shadowed_text(f"{pct}%", (255, 255, 255), game.tiny_font)
        surface.blit(pct_txt, (bar_x + bar_w + 6, bar_y - 1))

        # Trackers section
        track_y = obj_y + 62
        trackers = mdata.get('trackers', []) or []
        title_tr = self.render_shadowed_text("PROGRESS TRACKERS", (140, 170, 210), game.tiny_font)
        surface.blit(title_tr, (px + 20, track_y))

        ty = track_y + 18
        for tr in trackers[:6]:  # limit to keep it clean
            name = tr.get('name', 'Metric')
            cur = tr.get('current', 0)
            tgt = tr.get('target', 1)
            perc = max(0.0, min(1.0, tr.get('percent', 0.0)))
            unit = tr.get('unit', '')

            # Row
            row_h = 22
            pygame.draw.rect(surface, (18, 22, 35), (px + 18, ty, pw - 36, row_h))
            pygame.draw.rect(surface, (55, 80, 130), (px + 18, ty, pw - 36, row_h), 1)

            nm = self.render_shadowed_text(name, (200, 215, 235), game.tiny_font)
            surface.blit(nm, (px + 26, ty + 3))

            # Small bar
            sbw = 140
            sbx = px + pw - 200
            pygame.draw.rect(surface, (30, 35, 50), (sbx, ty + 5, sbw, 10))
            if perc > 0:
                fcol = (70, 190, 110) if not tr.get('invert') else (255, 80, 80)
                pygame.draw.rect(surface, fcol, (sbx, ty + 5, int(sbw * perc), 10))

            # Value text
            if isinstance(cur, (int, float)) and isinstance(tgt, (int, float)):
                val = f"{int(cur)}{unit} / {int(tgt)}{unit}"
            else:
                val = f"{cur} / {tgt}"
            val_surf = self.render_shadowed_text(val, (180, 200, 220), game.tiny_font)
            surface.blit(val_surf, (sbx - val_surf.get_width() - 8, ty + 2))

            ty += row_h + 3

        # Bonuses / reward footer
        footer_y = py + ph - 52
        pygame.draw.rect(surface, (20, 28, 42), (px + 16, footer_y, pw - 32, 38))
        pygame.draw.rect(surface, (80, 110, 160), (px + 16, footer_y, pw - 32, 38), 1)

        rew = mdata.get('estimated_reward', 0)
        rew_txt = self.render_shadowed_text(f"Estimated Reward: {rew} coins + bonuses", (255, 220, 100), game.small_font)
        surface.blit(rew_txt, (px + 26, footer_y + 5))

        hint = self.render_shadowed_text("TAB to close  •  Higher style & speed = better rewards", (140, 150, 170), game.tiny_font)
        surface.blit(hint, (px + 26, footer_y + 22))

        # Boss special callout
        if mdata.get('is_boss'):
            boss_call = self.render_shadowed_text("⚠ BOSS FIGHT — Full power recommended", (255, 140, 80), game.small_font)
            surface.blit(boss_call, (px + pw - boss_call.get_width() - 22, footer_y + 5))

    def draw_menu(self, game):
        def _draw_menu_virtual(game, surface):
            vw, vh = surface.get_width(), surface.get_height()
            # Draw gradient background
            for y in range(vh):
                r = int(25 * (y / float(vh)))
                g = 0
                b = int(50 * (y / float(vh)))
                pygame.draw.line(surface, (r, g, b), (0, y), (vw, y))

            # Update and draw stars (map positions to virtual)
            for i in range(len(game.stars)):
                game.stars[i] = ((game.stars[i][0] - game.star_speed) % self.base_width, game.stars[i][1])
            for star in game.stars:
                sx = int((star[0] / float(self.base_width)) * vw)
                sy = int((star[1] / float(SCREEN_HEIGHT)) * vh) if SCREEN_HEIGHT else star[1]
                pygame.draw.circle(surface, WHITE, (sx, sy), 1)

            game.menu_timer += 1
            color_value = int(128 + 127 * math.sin(game.menu_timer * 0.05))
            title_color = (255, color_value, 255)

            title = self.render_shadowed_text("SPACE SHOOTER", title_color, game.font)
            surface.blit(title, (vw//2 - title.get_width()//2, int(130 * (vh / float(self.base_height)))))

            subtitle = self.render_shadowed_text("STELLAR VANGUARD", (100, 200, 255), game.small_font)
            surface.blit(subtitle, (vw//2 - subtitle.get_width()//2, int(165 * (vh / float(self.base_height)))))

            tagline = self.render_shadowed_text("v3.1 - Survival Depth", (180, 180, 255), game.tiny_font)
            surface.blit(tagline, (vw//2 - tagline.get_width()//2, int(195 * (vh / float(self.base_height)))))

            high_score_text = self.render_shadowed_text(f"High Score: {game.high_score:,}", GREEN, game.small_font)
            surface.blit(high_score_text, (vw//2 - high_score_text.get_width()//2, int(220 * (vh / float(self.base_height)))))

            start_y = int(280 * (vh / float(self.base_height)))
            for i, option in enumerate(game.menu_options):
                if i == game.selected_option:
                    option_text = self.render_shadowed_text(f"> {option} <", GREEN, game.small_font)
                    bg_width = option_text.get_width() + 40
                    bg_height = option_text.get_height() + 10
                    bg_x = vw//2 - bg_width//2
                    bg_y = start_y + i * int(45 * (vh / float(self.base_height))) - 5
                    pygame.draw.rect(surface, (0, 50, 0), (bg_x, bg_y, bg_width, bg_height), border_radius=5)
                    pygame.draw.rect(surface, GREEN, (bg_x, bg_y, bg_width, bg_height), 2, border_radius=5)
                else:
                    option_text = self.render_shadowed_text(option, WHITE, game.small_font)
                surface.blit(option_text, (vw//2 - option_text.get_width()//2, start_y + i * int(45 * (vh / float(self.base_height)))))

            controls_text = self.render_shadowed_text("Use ↑↓ or W/S to navigate • SPACE or ENTER to select", (150, 150, 150), game.tiny_font)
            surface.blit(controls_text, (vw//2 - controls_text.get_width()//2, vh - int(60 * (vh / float(self.base_height)))))

            version_text = self.render_shadowed_text("v3.1", (150, 150, 200), game.tiny_font)
            surface.blit(version_text, (vw - version_text.get_width() - 10, vh - version_text.get_height() - 10))

        self._render_virtual_and_blit(_draw_menu_virtual, game)

    def draw_loadout_select(self, game, options, selected, cards=None):
        """R9 loadout polish: archetype list + detail card (stats/abilities)."""
        def _draw_loadout_virtual(game, surface, options, selected, cards=None):
            vw, vh = surface.get_width(), surface.get_height()
            scale_y = vh / float(self.base_height or 720)
            # Dark space gradient background
            for y in range(vh):
                r = int(12 * (y / float(vh)))
                g = 0
                b = int(35 * (y / float(vh)))
                pygame.draw.line(surface, (r, g, b), (0, y), (vw, y))

            # Stars for polish
            for star in getattr(game, 'stars', []):
                sx = int((star[0] / float(self.base_width)) * vw) if self.base_width else star[0] % vw
                sy = int((star[1] / float(self.base_height)) * vh) if self.base_height else star[1] % vh
                pygame.draw.circle(surface, (200, 210, 255), (sx, sy), 1)

            # Title
            title = self.render_shadowed_text("SELECT LOADOUT", (255, 220, 100), game.font)
            surface.blit(title, (vw//2 - title.get_width()//2, int(70 * scale_y)))

            sub = self.render_shadowed_text("Choose your ship archetype", (180, 190, 230), game.small_font)
            surface.blit(sub, (vw//2 - sub.get_width()//2, int(115 * scale_y)))

            # Left column: archetype names
            start_y = int(170 * scale_y)
            row_h = int(48 * scale_y)
            for i, opt in enumerate(options):
                label = opt
                if cards and i < len(cards):
                    label = cards[i].get("name", opt)
                if i == selected:
                    col = (255, 255, 0)
                    option_text = self.render_shadowed_text(f"> {i+1}. {label} <", col, game.small_font)
                    bg_width = max(option_text.get_width() + 40, int(220 * (vw / float(self.base_width or 960))))
                    bg_height = option_text.get_height() + 12
                    bg_x = int(80 * (vw / float(self.base_width or 960)))
                    bg_y = start_y + i * row_h - 6
                    pygame.draw.rect(surface, (20, 40, 20), (bg_x, bg_y, bg_width, bg_height), border_radius=6)
                    pygame.draw.rect(surface, (80, 200, 80), (bg_x, bg_y, bg_width, bg_height), 2, border_radius=6)
                else:
                    option_text = self.render_shadowed_text(f"  {i+1}. {label}", (230, 230, 230), game.small_font)
                    bg_x = int(80 * (vw / float(self.base_width or 960)))
                surface.blit(option_text, (bg_x + 12 if i == selected else bg_x + 12, start_y + i * row_h))

            # Right detail card for selected
            card = None
            if cards and 0 <= selected < len(cards):
                card = cards[selected]
            if card:
                cx = int(420 * (vw / float(self.base_width or 960)))
                cy = int(170 * scale_y)
                cw = int(480 * (vw / float(self.base_width or 960)))
                ch = int(320 * scale_y)
                pygame.draw.rect(surface, (18, 28, 48), (cx, cy, cw, ch), border_radius=10)
                pygame.draw.rect(surface, (90, 160, 220), (cx, cy, cw, ch), 2, border_radius=10)
                name_t = self.render_shadowed_text(card.get("name", "Loadout"), (255, 230, 140), game.font)
                surface.blit(name_t, (cx + 20, cy + 16))
                desc = card.get("desc", "")
                # wrap desc roughly
                words = desc.split()
                lines, cur = [], ""
                for w in words:
                    trial = (cur + " " + w).strip()
                    if len(trial) > 42:
                        if cur:
                            lines.append(cur)
                        cur = w
                    else:
                        cur = trial
                if cur:
                    lines.append(cur)
                for li, line in enumerate(lines[:3]):
                    dt = self.render_shadowed_text(line, (200, 210, 230), game.small_font)
                    surface.blit(dt, (cx + 20, cy + 70 + li * int(28 * scale_y)))
                stats = card.get("stats") or []
                sy0 = cy + 70 + max(len(lines), 1) * int(28 * scale_y) + int(16 * scale_y)
                st = self.render_shadowed_text("Stats", (140, 200, 255), game.small_font)
                surface.blit(st, (cx + 20, sy0))
                for si, s in enumerate(stats[:6]):
                    stxt = self.render_shadowed_text(f"• {s}", (220, 230, 240), game.tiny_font)
                    surface.blit(stxt, (cx + 28, sy0 + int(28 * scale_y) + si * int(24 * scale_y)))
                ab = ", ".join(a.upper() for a in (card.get("abilities") or []))
                at = self.render_shadowed_text(f"Abilities: {ab}", (180, 255, 180), game.small_font)
                surface.blit(at, (cx + 20, cy + ch - int(50 * scale_y)))

            hint = self.render_shadowed_text(
                "↑↓ / W S / D-pad  •  1/2/3  •  ENTER/SPACE/A confirm  •  ESC/B back",
                (160, 170, 190),
                game.tiny_font,
            )
            surface.blit(hint, (vw//2 - hint.get_width()//2, vh - int(55 * scale_y)))

        self._render_virtual_and_blit(_draw_loadout_virtual, game, options, selected, cards)

    def draw_options(self, game):
        def _draw_options_virtual(game, surface):
            vw, vh = surface.get_width(), surface.get_height()
            for y in range(vh):
                r = int(25 * (y / float(vh)))
                g = 0
                b = int(50 * (y / float(vh)))
                pygame.draw.line(surface, (r, g, b), (0, y), (vw, y))
            for i in range(len(game.stars)):
                game.stars[i] = ((game.stars[i][0] - game.star_speed) % self.base_width, game.stars[i][1])
            for star in game.stars:
                sx = int((star[0] / float(self.base_width)) * vw)
                sy = int((star[1] / float(SCREEN_HEIGHT)) * vh) if SCREEN_HEIGHT else star[1]
                pygame.draw.circle(surface, WHITE, (sx, sy), 1)
            options_title = self.render_shadowed_text("Difficulty Options", WHITE, game.font)
            surface.blit(options_title, (vw//2 - options_title.get_width()//2, int(100 * (vh / float(self.base_height)))))
            easy_text = self.render_shadowed_text("1. Easy (More lives, slower enemies)", GREEN if game.difficulty == 'easy' else WHITE, game.small_font)
            surface.blit(easy_text, (vw//2 - easy_text.get_width()//2, int(200 * (vh / float(self.base_height)))))
            normal_text = self.render_shadowed_text("2. Normal", GREEN if game.difficulty == 'normal' else WHITE, game.small_font)
            surface.blit(normal_text, (vw//2 - normal_text.get_width()//2, int(250 * (vh / float(self.base_height)))))
            hard_text = self.render_shadowed_text("3. Hard (Fewer lives, faster enemies)", GREEN if game.difficulty == 'hard' else WHITE, game.small_font)
            surface.blit(hard_text, (vw//2 - hard_text.get_width()//2, int(300 * (vh / float(self.base_height)))))
            back_text = self.render_shadowed_text("Press ESC to go back", WHITE, game.small_font)
            surface.blit(back_text, (vw//2 - back_text.get_width()//2, int(400 * (vh / float(self.base_height)))))

        self._render_virtual_and_blit(_draw_options_virtual, game)
        pygame.display.flip()

    def draw_tutorial(self, game):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(self.game.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(game.stars)):
            game.stars[i] = ((game.stars[i][0] - game.star_speed) % SCREEN_WIDTH, game.stars[i][1])
        for star in game.stars:
            pygame.draw.circle(self.game.screen, WHITE, star, 1)
        tutorial_title = self.render_shadowed_text("Tutorial", WHITE, game.font)
        self.game.screen.blit(tutorial_title, (SCREEN_WIDTH//2 - tutorial_title.get_width()//2, 50))
        lines = [
            "Use arrow keys to move your ship.",
            "Press SPACE to shoot. Energy regenerates over time!",
            "Press B to drop a bomb that explodes and damages nearby enemies.",
            "Power-ups (collect by shooting enemies):",
            "Green=Rapid Fire: Shoots 4 bullets at once (costs 4 energy)",
            "Yellow=Spread: 5 bullets with slight homing (costs 2 energy)",
            "Red=Laser: Wide beam with damage trail (costs 4 energy)",
            "Blue=Shield: Protects from damage (10 seconds, upgradable)",
            "Cyan=Energy: Restores 30 energy (regenerates automatically)",
            "Purple=Bomb: Adds 1 bomb",
            "Orange=Homing: Bullets seek enemies (costs 1 energy)",
            "Light Blue=Missile: Adds 5 missiles (fire with M key)",
            "Gray=Freeze: Stops enemies (10 seconds)",
            "Magenta=Invincibility: Immune to damage (10 seconds)",
            "Pink=Health: Restores 25 health",
            "Light Green=Time Slow: Slows enemies (10 seconds)",
            "Cyan=Plasma: Explodes on impact (costs 1 energy)",
            "Brown=Teleport: Random teleport",
            "Gold=Speed Boost: Doubles speed (10 seconds)",
            "Red-Orange=Multishot: 7 bullets, outer ones pierce (costs 4 ammo)",
            "Dark Green=Grenade: Throws explosive grenade (costs 2 ammo)",
            "Deep Pink=Extra Life: Grants an extra life",
            "Watch out for asteroids! They can damage you and block your shots.",
            "Avoid enemies and their bullets. Build combos for bonus points. Pause with P.",
            "Reach higher levels for more challenges.",
            "Defeat the boss for glory!"
        ]
        for i, line in enumerate(lines):
            text = self.render_shadowed_text(line, WHITE, game.small_font)
            self.game.screen.blit(text, (50, 100 + i*30))
        back_text = self.render_shadowed_text("Press ESC to go back", WHITE, game.small_font)
        self.game.screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 500))
        pygame.display.flip()


    def draw_damage_numbers_to_surface(self, game, surface):
        """R5: floating damage numbers (crits larger / gold)."""
        nums = getattr(game, 'damage_numbers', None) or []
        if not nums:
            return
        font = getattr(game, 'small_font', None) or getattr(game, 'font', None)
        big = getattr(game, 'font', font)
        for n in nums:
            try:
                ttl = max(1, int(n.get('ttl', 1)))
                max_ttl = max(1, int(n.get('max_ttl', ttl)))
                alpha = max(40, min(255, int(255 * (ttl / float(max_ttl)))))
                crit = bool(n.get('crit'))
                val = int(n.get('value', 0))
                text = str(val)
                color = (255, 220, 80) if crit else (255, 240, 240)
                use_font = big if crit else font
                if use_font is None:
                    continue
                img = use_font.render(text, True, color)
                img.set_alpha(alpha)
                x = int(n.get('x', 0) - img.get_width() // 2)
                y = int(n.get('y', 0))
                surface.blit(img, (x, y))
            except Exception:
                continue

    def draw_name_entry(self, game, chars, cursor):
        def _draw_name_virtual(game, surface, chars, cursor):
            vw, vh = surface.get_width(), surface.get_height()
            for y in range(vh):
                r = int(20 * (y / float(vh)))
                g = int(10 * (y / float(vh)))
                b = int(40 * (y / float(vh)))
                pygame.draw.line(surface, (r, g, b), (0, y), (vw, y))
            title = self.render_shadowed_text("NEW HIGH SCORE", GREEN, game.font)
            surface.blit(title, (vw//2 - title.get_width()//2, int(80 * (vh / float(self.base_height)))))
            score_txt = self.render_shadowed_text(f"Score: {int(getattr(game, 'score', 0) or 0)}", WHITE, game.small_font)
            surface.blit(score_txt, (vw//2 - score_txt.get_width()//2, int(140 * (vh / float(self.base_height)))))
            prompt = self.render_shadowed_text("Enter initials", WHITE, game.small_font)
            surface.blit(prompt, (vw//2 - prompt.get_width()//2, int(200 * (vh / float(self.base_height)))))
            # three letter boxes
            box_w, box_h, gap = 54, 64, 18
            total_w = 3 * box_w + 2 * gap
            start_x = vw // 2 - total_w // 2
            y0 = int(260 * (vh / float(self.base_height)))
            for i, ch in enumerate(chars[:3]):
                x = start_x + i * (box_w + gap)
                col = GREEN if i == cursor else WHITE
                pygame.draw.rect(surface, col, (x, y0, box_w, box_h), 2)
                letter = self.render_shadowed_text(str(ch), col, game.font)
                surface.blit(letter, (x + (box_w - letter.get_width()) // 2, y0 + (box_h - letter.get_height()) // 2))
            hints = "Left/Right move  Up/Down change  Enter confirm  Esc=AAA"
            ht = self.render_shadowed_text(hints, (180, 180, 200), game.small_font)
            surface.blit(ht, (vw//2 - ht.get_width()//2, int(360 * (vh / float(self.base_height)))))

        self._render_virtual_and_blit(lambda g, s: _draw_name_virtual(g, s, chars, cursor), game)

    def draw_leaderboard(self, game):
        def _draw_leaderboard_virtual(game, surface):
            vw, vh = surface.get_width(), surface.get_height()
            for y in range(vh):
                r = int(25 * (y / float(vh)))
                g = 0
                b = int(50 * (y / float(vh)))
                pygame.draw.line(surface, (r, g, b), (0, y), (vw, y))
            for i in range(len(game.stars)):
                game.stars[i] = ((game.stars[i][0] - game.star_speed) % self.base_width, game.stars[i][1])
            for star in game.stars:
                sx = int((star[0] / float(self.base_width)) * vw)
                sy = int((star[1] / float(SCREEN_HEIGHT)) * vh) if SCREEN_HEIGHT else star[1]
                pygame.draw.circle(surface, WHITE, (sx, sy), 1)
            leaderboard_title = self.render_shadowed_text("Leaderboard", WHITE, game.font)
            surface.blit(leaderboard_title, (vw//2 - leaderboard_title.get_width()//2, int(50 * (vh / float(self.base_height)))))
            named = getattr(game, 'named_high_scores', None) or []
            if not named:
                # fallback to bare ints
                named = [{"name": "---", "score": int(s)} for s in (getattr(game, 'high_scores', None) or [])]
            for i, entry in enumerate(named[:10]):
                rank = i + 1
                name = str(entry.get('name', '---') or '---')[:3]
                score = int(entry.get('score', 0) or 0)
                score_text = self.render_shadowed_text(f"{rank}. {name}  {score}", GREEN if i == 0 else WHITE, game.small_font)
                surface.blit(score_text, (vw//2 - score_text.get_width()//2, int((100 + i*30) * (vh / float(self.base_height)))))
            back_text = self.render_shadowed_text("Press ESC to go back", WHITE, game.small_font)
            surface.blit(back_text, (vw//2 - back_text.get_width()//2, int(500 * (vh / float(self.base_height)))))

        self._render_virtual_and_blit(_draw_leaderboard_virtual, game)

    def draw_playing(self, game):
        """Render gameplay into the virtual surface and scale/blit to the screen."""
        def _draw_playing_virtual(game, surface):
            # background and parallax
            self.draw_background_to_surface(game, surface)
            self.draw_starfield_to_surface(game, surface)
            self.draw_celestial_bodies_to_surface(game, surface)

            # game entities
            self.draw_sprites_to_surface(game, surface)
            self.draw_particles_to_surface(game, surface)
            self.draw_player_effects_to_surface(game, surface)

            # Cheap but very effective bloom/glow pass - makes explosions, thrusters, powerups, energy weapons *pop* (technically impressive 2D)
            try:
                small = pygame.transform.smoothscale(surface, (surface.get_width()//3, surface.get_height()//3))
                bloom = pygame.transform.smoothscale(small, surface.get_size())
                bloom.set_alpha(22)
                surface.blit(bloom, (0, 0), special_flags=pygame.BLEND_ADD)
                # Second wider softer pass for big explosions / engine glow
                bloom2 = pygame.transform.smoothscale(small, (surface.get_width(), surface.get_height()))
                bloom2.set_alpha(12)
                surface.blit(bloom2, (0, 0), special_flags=pygame.BLEND_ADD)
            except Exception:
                pass

            # UI on virtual surface
            self.draw_boss_health_to_surface(game, surface)
            self.draw_hud_to_surface(game, surface)
            self.draw_damage_numbers_to_surface(game, surface)

            # Expanded mission panel (toggle with TAB) - drawn on virtual (content will be stretched to fill the whole window)
            if getattr(game, 'show_mission_panel', False):
                self.draw_expanded_mission_panel(game, surface)

        # Use helper to render virtual and blit scaled
        self._render_virtual_and_blit(_draw_playing_virtual, game)

    def draw_pause_menu(self, game, options=None, selected=0):
        def _draw_pause_virtual(game, surface, options=None, selected=0):
            # Freeze-frame feel: draw gameplay underlay if possible, else gradient
            sw, sh = surface.get_width(), surface.get_height()
            try:
                self.draw_background_to_surface(game, surface)
                self.draw_starfield_to_surface(game, surface)
                self.draw_sprites_to_surface(game, surface)
                self.draw_particles_to_surface(game, surface)
                self.draw_hud_to_surface(game, surface)
            except Exception:
                for y in range(sh):
                    r = int(25 * (y / float(sh)))
                    g = 0
                    b = int(50 * (y / float(sh)))
                    pygame.draw.line(surface, (r, g, b), (0, y), (sw, y))
            # Dim overlay for a11y contrast
            dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 160))
            surface.blit(dim, (0, 0))
            pause_title = self.render_shadowed_text("PAUSED", WHITE, game.font)
            surface.blit(pause_title, (sw//2 - pause_title.get_width()//2, int(120 * (sh / float(self.base_height)))))
            opts = options or ["Resume", "Quit"]
            for i, label in enumerate(opts):
                col = GREEN if i == selected else WHITE
                prefix = "> " if i == selected else "  "
                txt = self.render_shadowed_text(f"{prefix}{label}", col, game.small_font)
                surface.blit(txt, (sw//2 - txt.get_width()//2, int((220 + i * 40) * (sh / float(self.base_height)))))
            hints = [
                "P / ESC / Enter — Resume",
                "Arrows / WASD — Move",
                "Q — Quit",
                "Pad: A/Start resume, B quit",
            ]
            for i, h in enumerate(hints):
                ht = self.render_shadowed_text(h, (180, 180, 200), game.small_font)
                surface.blit(ht, (sw//2 - ht.get_width()//2, int((340 + i * 28) * (sh / float(self.base_height)))))

        self._render_virtual_and_blit(lambda g, s: _draw_pause_virtual(g, s, options, selected), game)

    def draw_continue_prompt(self, game, options, selected):
        # Render the playing state to the virtual surface first, then overlay prompt
        def _draw_continue_virtual(game, surface, options, selected):
            # Draw current game visuals
            self.draw_background_to_surface(game, surface)
            self.draw_starfield_to_surface(game, surface)
            self.draw_celestial_bodies_to_surface(game, surface)
            self.draw_sprites_to_surface(game, surface)
            self.draw_particles_to_surface(game, surface)
            self.draw_player_effects_to_surface(game, surface)
            self.draw_boss_health_to_surface(game, surface)
            self.draw_hud_to_surface(game, surface)

            # Overlay continue prompt on virtual surface
            overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            # Positioning relative to virtual surface
            vw, vh = surface.get_width(), surface.get_height()
            title_text = self.render_shadowed_text("SHIP DESTROYED!", RED, game.font)
            surface.blit(title_text, (vw//2 - title_text.get_width()//2, vh//2 - int(150 *  (vh / self.base_height))))

            score_text = self.render_shadowed_text(f"Score: {game.score}", YELLOW, game.small_font)
            surface.blit(score_text, (vw//2 - score_text.get_width()//2, vh//2 - int(110 * (vh / self.base_height))))

            level_text = self.render_shadowed_text(f"Level: {game.level}", CYAN, game.small_font)
            surface.blit(level_text, (vw//2 - level_text.get_width()//2, vh//2 - int(85 * (vh / self.base_height))))

            for i, option in enumerate(options):
                color = GREEN if i == selected else WHITE
                option_text = self.render_shadowed_text(option, color, game.small_font)
                surface.blit(option_text, (vw//2 - option_text.get_width()//2, vh//2 - int(30 * (vh / self.base_height)) + i * int(45 * (vh / self.base_height))))

            hint_text = self.render_shadowed_text("↑↓ Select    SPACE or ENTER Choose", GRAY, game.tiny_font)
            surface.blit(hint_text, (vw//2 - hint_text.get_width()//2, vh//2 + int(120 * (vh / self.base_height))))

        self._render_virtual_and_blit(_draw_continue_virtual, game, options, selected)

    def draw_game_over(self, game):
        def _draw_game_over_virtual(game, surface):
            sw, sh = surface.get_width(), surface.get_height()
            # Gradient background
            for y in range(sh):
                r = 0
                g = 0
                b = int(50 * (y / float(sh)))
                pygame.draw.line(surface, (r, g, b), (0, y), (sw, y))
            # Stars
            for star in game.stars:
                # Map star positions to virtual space
                sx = int((star[0] / float(SCREEN_WIDTH)) * sw) if SCREEN_WIDTH else star[0]
                sy = int((star[1] / float(SCREEN_HEIGHT)) * sh) if SCREEN_HEIGHT else star[1]
                pygame.draw.circle(surface, WHITE, (sx, sy), 1)
            game.game_over_timer += 1
            color_value = int(128 + 127 * math.sin(game.game_over_timer * 0.05))
            game_over_color = (255, color_value, color_value)
            game_over_text = self.render_shadowed_text("Game Over", game_over_color, game.font)
            surface.blit(game_over_text, (sw//2 - game_over_text.get_width()//2, int(150 * (sh / float(self.base_height)))))
            final_score_text = self.render_shadowed_text(f"Final Score: {game.score}", WHITE, game.small_font)
            surface.blit(final_score_text, (sw//2 - final_score_text.get_width()//2, int(200 * (sh / float(self.base_height)))))
            enemies_text = self.render_shadowed_text(f"Enemies Killed: {game.enemies_killed}", WHITE, game.small_font)
            surface.blit(enemies_text, (sw//2 - enemies_text.get_width()//2, int(250 * (sh / float(self.base_height)))))
            bullets_text = self.render_shadowed_text(f"Bullets Fired: {game.bullets_fired}", WHITE, game.small_font)
            surface.blit(bullets_text, (sw//2 - bullets_text.get_width()//2, int(300 * (sh / float(self.base_height)))))
            level_text = self.render_shadowed_text(f"Level Reached: {game.level}", YELLOW, game.small_font)
            surface.blit(level_text, (sw//2 - level_text.get_width()//2, int(350 * (sh / float(self.base_height)))))
            if getattr(game, 'survival', False):
                st = float(getattr(game, 'survival_time', 0) or 0)
                best_t = float(getattr(game, 'best_survival_time', 0) or 0)
                best_s = int(getattr(game, 'best_survival_score', 0) or 0)
                surv_line = self.render_shadowed_text(
                    f"Survived {int(st)}s  |  Best {int(best_t)}s / {best_s:,} pts", CYAN, game.small_font)
                surface.blit(surv_line, (sw//2 - surv_line.get_width()//2, int(330 * (sh / float(self.base_height)))))
            achievements_text = self.render_shadowed_text("Achievements Unlocked:", GREEN, game.small_font)
            surface.blit(achievements_text, (sw//2 - achievements_text.get_width()//2, int(375 * (sh / float(self.base_height)))))
            ach_list = [k for k, v in game.achievements.items() if v]
            for i, ach in enumerate(ach_list):
                ach_text = self.render_shadowed_text(ach.replace('_', ' ').title(), GREEN, game.small_font)
                surface.blit(ach_text, (sw//2 - ach_text.get_width()//2, int((400 + i*25) * (sh / float(self.base_height)))))
            shop_text = self.render_shadowed_text("Press S for Shop, SPACE to Restart, ESC to Menu", WHITE, game.small_font)
            surface.blit(shop_text, (sw//2 - shop_text.get_width()//2, int(500 * (sh / float(self.base_height)))))

        self._render_virtual_and_blit(_draw_game_over_virtual, game)

    def draw_shop(self, game, purchase_message="", purchase_message_time=0):
        def _draw_shop_virtual(game, surface, purchase_message, purchase_message_time):
            vw, vh = surface.get_width(), surface.get_height()
            # Draw gradient background
            for y in range(vh):
                r = int(20 * (y / float(vh)))
                g = int(10 * (y / float(vh)))
                b = int(40 * (y / float(vh)))
                pygame.draw.line(surface, (r, g, b), (0, y), (vw, y))

            # Draw stars (map to virtual coords)
            for i in range(len(game.stars)):
                game.stars[i] = ((game.stars[i][0] - game.star_speed) % self.base_width, game.stars[i][1])
            for star in game.stars:
                sx = int((star[0] / float(self.base_width)) * vw)
                sy = int((star[1] / float(SCREEN_HEIGHT)) * vh) if SCREEN_HEIGHT else star[1]
                pygame.draw.circle(surface, WHITE, (sx, sy), 1)

            if hasattr(game.state, 'is_post_boss') and game.state.is_post_boss:
                if getattr(game.state, 'is_survival_milestone', False):
                    label = getattr(game, 'survival_milestone_label', 'milestone')
                    shop_title = self.render_shadowed_text(f"SURVIVAL MILESTONE ({label}) — CLAIM UPGRADE", GOLD, game.font)
                    surface.blit(shop_title, (vw//2 - shop_title.get_width()//2, int(25 * (vh / float(self.base_height)))))
                    sub = self.render_shadowed_text("Mid-run shop: pick ONE (or SKIP) — run continues after ESC", (220, 200, 120), game.tiny_font)
                    surface.blit(sub, (vw//2 - sub.get_width()//2, int(55 * (vh / float(self.base_height)))))
                else:
                    # Celebratory modern roguelite "boon" title (Hades-style)
                    shop_title = self.render_shadowed_text("BOSS DEFEATED — CLAIM YOUR REWARD", GOLD, game.font)
                    surface.blit(shop_title, (vw//2 - shop_title.get_width()//2, int(25 * (vh / float(self.base_height)))))
                    sub = self.render_shadowed_text("Pick ONE powerful upgrade (or SKIP for coins) — Rerolls limited by rank", (220, 200, 120), game.tiny_font)
                    surface.blit(sub, (vw//2 - sub.get_width()//2, int(55 * (vh / float(self.base_height)))))
            else:
                shop_title = self.render_shadowed_text("🛒 UPGRADE SHOP", WHITE, game.font)
                surface.blit(shop_title, (vw//2 - shop_title.get_width()//2, int(30 * (vh / float(self.base_height)))))

            coins_bg = pygame.Surface((250, 50), pygame.SRCALPHA)
            coins_bg.fill((0, 0, 0, 200))
            pygame.draw.rect(coins_bg, GOLD, (0, 0, 250, 50), 2, border_radius=25)
            surface.blit(coins_bg, (vw//2 - 125, int(75 * (vh / float(self.base_height)))))
            coins_text = self.render_shadowed_text(f"💰 {game.coins}", GOLD, game.small_font)
            surface.blit(coins_text, (vw//2 - coins_text.get_width()//2, int(85 * (vh / float(self.base_height)))))

            if not (hasattr(game.state, 'is_post_boss') and game.state.is_post_boss):
                category_names = ["ALL", "CONSUMABLES", "WEAPONS", "UPGRADES", "SPECIAL"]
                tab_width = 120
                tab_height = 35
                tab_spacing = 10
                total_tabs_width = len(category_names) * tab_width + (len(category_names) - 1) * tab_spacing
                start_x = (vw - total_tabs_width) // 2
                tab_y = int(140 * (vh / float(self.base_height)))

                for i, category in enumerate(category_names):
                    tab_x = start_x + i * (tab_width + tab_spacing)
                    tab_color = (60, 60, 80, 220) if i != game.state.current_category else (100, 150, 200, 240)
                    tab_border_color = (120, 120, 140) if i != game.state.current_category else (200, 220, 255)
                    tab_surf = pygame.Surface((tab_width, tab_height), pygame.SRCALPHA)
                    tab_surf.fill(tab_color)
                    pygame.draw.rect(tab_surf, tab_border_color, (0, 0, tab_width, tab_height), 2, border_radius=8)
                    surface.blit(tab_surf, (tab_x, tab_y))
                    text_color = WHITE if i != game.state.current_category else CYAN
                    tab_text = self.render_shadowed_text(category, text_color, game.tiny_font)
                    surface.blit(tab_text, (tab_x + tab_width//2 - tab_text.get_width()//2, tab_y + 8))

                # Modern touch: show featured offers (3 random this visit) — now with rarity badges
                if hasattr(game.state, 'featured_items'):
                    feat_y = tab_y + tab_height + 5
                    ft = self.render_shadowed_text("FEATURED THIS VISIT (random):", (200, 220, 100), game.tiny_font)
                    surface.blit(ft, (start_x, feat_y))
                    parts = []
                    for f in getattr(game.state, 'featured_items', [])[:3]:
                        r = f.get('rarity', 'common')
                        badge = f.get('rarity_note', '') or ('['+r[:3].upper()+']' if r!='common' else '')
                        nm = str(f.get('name',''))[:12]
                        parts.append(f"{nm}{badge}".strip())
                    fn = "  •  ".join(parts)
                    fnt = self.render_shadowed_text(fn, WHITE, game.tiny_font)
                    surface.blit(fnt, (start_x, feat_y + 16))

            current_state = game.state
            if hasattr(current_state, 'category_items'):
                shop_items = current_state.category_items
            else:
                shop_items = game.shop_items

            items_per_row = 3
            item_width = 200
            item_height = 100
            if getattr(game.state, 'is_post_boss', False):
                item_width = 220
                item_height = 110
            start_x = (vw - (items_per_row * item_width + (items_per_row - 1) * 20)) // 2
            start_y = int(190 * (vh / float(self.base_height)))
            if getattr(game.state, 'is_post_boss', False):
                start_y = int(145 * (vh / float(self.base_height)))  # room for celebratory title + sub
            if not (hasattr(game.state, 'is_post_boss') and game.state.is_post_boss) and hasattr(game.state, 'featured_items'):
                start_y += 40  # space for featured line

            for i, item in enumerate(shop_items):
                row = i // items_per_row
                col = i % items_per_row
                x = start_x + col * (item_width + 20)
                y = start_y + row * (item_height + 15)
                is_special_offer = 'original_cost' in item
                is_skip = item.get('skip', False)
                is_post = getattr(current_state, 'is_post_boss', False)
                has_claimed = getattr(current_state, 'has_claimed_reward', False) if is_post else False

                # Rarity setup (new modern roguelite juice)
                rarity = item.get('rarity', 'common')
                r_border, r_badge, r_glow = (GOLD, GOLD, 120) if rarity == 'legendary' else \
                    ((180, 80, 220), (180, 80, 220), 90) if rarity == 'epic' else \
                    ((80, 180, 255), (80, 180, 255), 70) if rarity == 'rare' else \
                    (SILVER, (160, 160, 160), 40)
                if is_special_offer:
                    glow_surf = pygame.Surface((item_width + 12, item_height + 12), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (255, 215, 0, 150), (0, 0, item_width + 12, item_height + 12), border_radius=12)
                    surface.blit(glow_surf, (x - 6, y - 6))
                    border_color = GOLD
                    card_color = (80, 60, 20, 240)
                elif is_post:
                    # Post-boss cards: rarity-driven border + subtle bg tint
                    border_color = r_border
                    base_r, base_g, base_b = (45, 55, 35) if rarity == 'common' else (40, 48, 55) if rarity == 'rare' else (48, 38, 58) if rarity == 'epic' else (55, 48, 30)
                    card_color = (base_r, base_g, base_b, 235)
                    if is_skip:
                        card_color = (35, 38, 48, 220)  # skip is calmer/neutral
                        border_color = (120, 120, 140)
                else:
                    if i == game.selected_item:
                        pulse = math.sin(pygame.time.get_ticks() * 0.008) * 0.3 + 0.7
                        card_color = (int(70 * pulse), int(100 * pulse), int(200 * pulse), 240)
                        border_color = (int(150 * pulse), int(200 * pulse), int(255 * pulse))
                    else:
                        border_color = (100, 100, 120)
                        card_color = (55, 55, 70, 230)

                if item.get('dynamic_cost', False):
                    item_cost = game.upgrades.get_upgrade_cost(item['cost_key'])
                else:
                    item_cost = item.get('cost', 0)
                can_afford = game.coins >= item_cost or (is_post and item_cost == 0)  # skip always "afford"
                if can_afford and i != game.selected_item and not is_special_offer and not is_post:
                    card_color = (50, 80, 50, 220)
                    border_color = (100, 150, 100)
                elif not can_afford and i != game.selected_item and not is_special_offer and not is_post:
                    card_color = (80, 30, 30, 220)
                    border_color = (150, 50, 50)

                # Claimed dim for non-chosen post-boss cards (by claimed_item_name, not selected index)
                claimed_name = getattr(current_state, 'claimed_item_name', None) if is_post else None
                if is_post and has_claimed and not item.get('skip') and item.get('name') != claimed_name:
                    card_color = tuple(int(c * 0.55) if isinstance(c, int) else c for c in card_color[:3]) + (card_color[3] if len(card_color) > 3 else 200,)

                card_surf = pygame.Surface((item_width, item_height), pygame.SRCALPHA)
                card_surf.fill(card_color)
                surface.blit(card_surf, (x, y))

                # Rarity frame/glow (post-boss or special)
                if (is_post or is_special_offer) and rarity != 'common':
                    rglow = pygame.Surface((item_width + 6, item_height + 6), pygame.SRCALPHA)
                    pygame.draw.rect(rglow, (*r_border[:3], min(70, r_glow)), (0, 0, item_width + 6, item_height + 6), border_radius=9)
                    surface.blit(rglow, (x - 3, y - 3))
                pygame.draw.rect(surface, border_color, (x, y, item_width, item_height), 2, border_radius=8)

                # Selected glow (tinted by rarity for post)
                if i == game.selected_item:
                    sel_col = r_border if (is_post and rarity != 'common') else (150, 200, 255)
                    glow_surf = pygame.Surface((item_width + 8, item_height + 8), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (*sel_col[:3], 110), (0, 0, item_width + 8, item_height + 8), border_radius=10)
                    surface.blit(glow_surf, (x - 4, y - 4))

                # Icon + badges
                icon = item.get('icon', self.get_shop_item_icon(item['name']))
                icon_text = self.render_shadowed_text(icon, WHITE, game.small_font)
                surface.blit(icon_text, (x + 10, y + 10))

                # Rarity badge (top-right, modern pedestal feel)
                if rarity != 'common' or is_post:
                    badge_text = item.get('rarity_note', '').strip('[]') or (rarity.upper()[:3] if rarity != 'common' else '')
                    if badge_text:
                        badge = self.render_shadowed_text(badge_text, r_badge, game.tiny_font)
                        surface.blit(badge, (x + item_width - badge.get_width() - 6, y + 4))

                # Synergy badge (gold/yellow highlight, below name area)
                if item.get('synergy') and item.get('synergy_tag'):
                    syn = self.render_shadowed_text(item['synergy_tag'][:18], (255, 215, 80), game.tiny_font)
                    surface.blit(syn, (x + 10, y + 18))

                name_color = WHITE if can_afford else (200, 100, 100)
                name_text = self.render_shadowed_text(item['name'], name_color, game.tiny_font)
                name_max_width = item_width - 60
                if name_text.get_width() > name_max_width:
                    truncated_name = item['name']
                    while self.render_shadowed_text(truncated_name + "...", name_color, game.tiny_font).get_width() > name_max_width and len(truncated_name) > 0:
                        truncated_name = truncated_name[:-1]
                    name_text = self.render_shadowed_text(truncated_name + "...", name_color, game.tiny_font)
                name_y = y + 8 if not item.get('synergy') else y + 2
                surface.blit(name_text, (x + 50, name_y))

                desc_color = (180, 180, 180) if can_afford else (150, 100, 100)
                desc_max_width = item_width - 60
                # Prefer display_desc (live preview for upgrades) then description
                description = item.get('display_desc') or item.get('description', '')
                if is_skip:
                    description = item.get('description', '')
                desc_lines = self._wrap_text(description, desc_max_width, game.tiny_font)
                desc_y = y + 28 if not (item.get('synergy') or (rarity != 'common' and is_post)) else y + 34
                for line in desc_lines[:2]:
                    desc_text = self.render_shadowed_text(line, desc_color, game.tiny_font)
                    surface.blit(desc_text, (x + 50, desc_y))
                    desc_y += 14

                # Cost / skip handling
                if item.get('dynamic_cost', False):
                    cost = game.upgrades.get_upgrade_cost(item['cost_key'])
                else:
                    cost = item.get('cost', 0)
                if is_special_offer:
                    original_cost = item['original_cost']
                    orig_cost_text = self.render_shadowed_text(f"{original_cost}💰", (150, 100, 100), game.tiny_font)
                    max_cost_width = item_width - 20
                    if orig_cost_text.get_width() > max_cost_width:
                        orig_cost_text = self.render_shadowed_text(f"{original_cost}💰"[:8] + "...", (150, 100, 100), game.tiny_font)
                    line_y = y + 55
                    pygame.draw.line(surface, (150, 100, 100), (x + 10, line_y), (x + 10 + orig_cost_text.get_width(), line_y), 2)
                    surface.blit(orig_cost_text, (x + 10, y + 45))
                    cost_text = self.render_shadowed_text(f"{cost}💰", GOLD, game.tiny_font)
                    cost_x = min(x + item_width - cost_text.get_width() - 10, x + item_width - 50)
                    surface.blit(cost_text, (cost_x, y + 45))
                elif is_skip:
                    skip_text = self.render_shadowed_text(f"+{item.get('cost', 0) or 50}💰  (or ESC)", (180, 200, 160), game.tiny_font)
                    surface.blit(skip_text, (x + 10, y + 48))
                else:
                    cost_text = self.render_shadowed_text(f"{cost}💰", GOLD if game.coins >= cost else (150, 100, 100), game.tiny_font)
                    surface.blit(cost_text, (x + item_width - cost_text.get_width() - 10, y + 45))

            # Footer message
            if purchase_message and pygame.time.get_ticks() - purchase_message_time < 2000:
                message_bg = pygame.Surface((400, 40), pygame.SRCALPHA)
                message_bg.fill((0, 0, 0, 200))
                surface.blit(message_bg, (vw//2 - 200, vh - 120))
                message_text = self.render_shadowed_text(purchase_message, WHITE, game.small_font)
                surface.blit(message_text, (vw//2 - message_text.get_width()//2, vh - 110))

        self._render_virtual_and_blit(_draw_shop_virtual, game, purchase_message, purchase_message_time)
        # Purchase confirmation message
        if purchase_message and pygame.time.get_ticks() - purchase_message_time < 2000:  # Show for 2 seconds
            message_color = GREEN if "Purchased" in purchase_message else RED
            message_bg = pygame.Surface((400, 50), pygame.SRCALPHA)
            message_bg.fill((0, 0, 0, 200))
            self.game.screen.blit(message_bg, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT - 120))
            message_text = self.render_shadowed_text(purchase_message, message_color, game.small_font)
            self.game.screen.blit(message_text, (SCREEN_WIDTH//2 - message_text.get_width()//2, SCREEN_HEIGHT - 110))

        # Navigation instructions (updated for modern post-boss UX)
        if hasattr(game.state, 'is_post_boss') and game.state.is_post_boss:
            claimed = getattr(game.state, 'has_claimed_reward', False)
            rerolls = getattr(game.state, 'rerolls_remaining', 0)
            if claimed:
                nav_text = self.render_shadowed_text("ESC or START: Continue to next level  •  Reward claimed", GOLD, game.tiny_font)
            elif rerolls > 0:
                nav = f"WASD/Arrows: Pick  •  ENTER/A: Claim  •  R: free reroll ({rerolls} left)  •  SKIP/ESC: +coins & continue"
                nav_text = self.render_shadowed_text(nav, GOLD, game.tiny_font)
            else:
                nav = "WASD/Arrows: Pick  •  ENTER/A: Claim  •  R: paid reroll (50)  •  SKIP/ESC: +coins & continue"
                nav_text = self.render_shadowed_text(nav, GOLD, game.tiny_font)
        else:
            nav_text = self.render_shadowed_text("Q/E or LB/RB: Switch categories • ↑↓←→ or WASD: Navigate • R: Reroll featured (150💰) • ENTER or A: Purchase • ESC: Back", WHITE, game.tiny_font)
        self.game.screen.blit(nav_text, (SCREEN_WIDTH//2 - nav_text.get_width()//2, SCREEN_HEIGHT - 60))

        pygame.display.flip()

    def draw_achievements(self, game):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(self.game.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Draw stars
        for star in game.stars:
            pygame.draw.circle(self.game.screen, WHITE, star, 1)
        achievements_title = self.render_shadowed_text("Achievements", WHITE, game.font)
        self.game.screen.blit(achievements_title, (SCREEN_WIDTH//2 - achievements_title.get_width()//2, 50))
        ach_list = [
            ('kill_100', 'Kill 100 Enemies'),
            ('reach_level_10', 'Reach Level 10'),
            ('combo_10', 'Achieve Combo of 10'),
            ('boss_defeated', 'Defeat the Boss'),
            ('kill_500', 'Kill 500 Enemies'),
            ('survive_5_min', 'Survive 5 Minutes in Survival Mode')
        ]
        for i, (key, desc) in enumerate(ach_list):
            color = GREEN if game.achievements.get(key, False) else RED
            status = "Unlocked" if game.achievements.get(key, False) else "Locked"
            ach_text = self.render_shadowed_text(f"{desc} - {status}", color, game.small_font)
            self.game.screen.blit(ach_text, (SCREEN_WIDTH//2 - ach_text.get_width()//2, 150 + i*40))
        back_text = self.render_shadowed_text("Press ESC to go back", WHITE, game.small_font)
        self.game.screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 500))
        pygame.display.flip()

    def draw_victory(self, game):
        def _draw_victory_virtual(game, surface):
            vw, vh = surface.get_width(), surface.get_height()
            # Gradient + stars
            for y in range(vh):
                r = int(10 * (y / float(vh)))
                g = int(20 * (y / float(vh)))
                b = int(40 * (y / float(vh)))
                pygame.draw.line(surface, (r, g, b), (0, y), (vw, y))
            for i in range(len(game.stars)):
                game.stars[i] = ((game.stars[i][0] - game.star_speed) % self.base_width, game.stars[i][1])
            for star in game.stars:
                sx = int((star[0] / float(self.base_width)) * vw)
                sy = int((star[1] / float(SCREEN_HEIGHT)) * vh) if SCREEN_HEIGHT else star[1]
                pygame.draw.circle(surface, WHITE, (sx, sy), 1)

            # Title
            title = self.render_shadowed_text("LEVEL COMPLETE!", GOLD, game.font)
            surface.blit(title, (vw//2 - title.get_width()//2, int(80 * (vh / float(self.base_height)))))

            score_text = self.render_shadowed_text(f"Score: {game.score}", WHITE, game.small_font)
            surface.blit(score_text, (vw//2 - score_text.get_width()//2, int(130 * (vh / float(self.base_height)))))

            # Options
            if hasattr(game.state, 'options'):
                options = game.state.options
                selected = getattr(game.state, 'selected', 0)
                for i, opt in enumerate(options):
                    col = (255, 255, 0) if i == selected else WHITE
                    opt_text = self.render_shadowed_text(opt, col, game.small_font)
                    y = int(200 * (vh / float(self.base_height))) + i * 50
                    surface.blit(opt_text, (vw//2 - opt_text.get_width()//2, y))
            else:
                cont = self.render_shadowed_text("Press RETURN/SPACE to continue", WHITE, game.small_font)
                surface.blit(cont, (vw//2 - cont.get_width()//2, int(250 * (vh / float(self.base_height)))))

            hint = self.render_shadowed_text("↑↓ to select • SPACE/ENTER to confirm • ESC menu", (180,180,180), game.tiny_font)
            surface.blit(hint, (vw//2 - hint.get_width()//2, vh - int(60 * (vh / float(self.base_height)))))

        self._render_virtual_and_blit(_draw_victory_virtual, game)

    def draw_boss_incoming(self, game):
        """Polished, non-annoying boss incoming warning.
        Dimmed gameplay + dramatic red warning elements + buildup bar.
        No harsh full-screen strobing flash.
        """
        # Draw underlying gameplay (slightly dimmed for focus on warning)
        self.draw_playing(game)

        # Subtle red danger vignette / border (not solid black flash)
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT
        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        # Red tint edges
        for i in range(40):
            alpha = int(6 * (40 - i))
            pygame.draw.rect(vignette, (180, 20, 20, alpha), (i, i, w - i*2, h - i*2), 3)
        self.game.screen.blit(vignette, (0, 0))

        # Timer based drama (0 -> 180)
        t = getattr(game, '_boss_incoming_timer', 0) or 0
        phase = min(1.0, t / 180.0)

        # Big animated warning text (pulsing scale + intensity, no strobe)
        pulse = 0.9 + 0.15 * math.sin(t * 0.18)
        scale = pulse
        try:
            base_font = game.font
            # Main title - grows in intensity
            title = getattr(game, "pending_boss_title", None) or "BOSS INCOMING"
            title_surf = base_font.render(title, True, (255, 60, 60))
            # Simple scale via rotozoom (cheap for one text)
            if scale != 1.0:
                title_surf = pygame.transform.rotozoom(title_surf, 0, scale)
            tx = (w - title_surf.get_width()) // 2
            ty = int(h * 0.38)
            # Glow layer behind (multiple offset low alpha)
            for off in range(3, 0, -1):
                glow = title_surf.copy()
                glow.set_alpha(30 + off * 8)
                self.game.screen.blit(glow, (tx - off, ty - off))
            self.game.screen.blit(title_surf, (tx, ty))
        except Exception:
            # Fallback
            boss_text = self.render_shadowed_text("BOSS INCOMING!", RED, game.font)
            self.game.screen.blit(boss_text, (w//2 - boss_text.get_width()//2, int(h * 0.38)))

        # Subtext that changes with phase (buildup feel like other games)
        pending = getattr(game, "pending_boss_title", None) or ""
        sub = "THREAT DETECTED • PREPARE FOR ENGAGEMENT"
        if phase > 0.33:
            sub = f"WARNING • {pending} APPROACHING" if pending else "WARNING • BOSS APPROACHING"
        if phase > 0.66:
            sub = f"!! {pending} - STAND BY !!" if pending else "!! BOSS INCOMING - STAND BY !!"
        sub_surf = self.render_shadowed_text(sub, (255, 220, 80), game.small_font)
        self.game.screen.blit(sub_surf, (w//2 - sub_surf.get_width()//2, int(h * 0.38) + 55))

        # Boss approach / danger bar (fills during the warning - very game-like)
        bar_w = int(w * 0.55)
        bar_h = 18
        bar_x = (w - bar_w) // 2
        bar_y = int(h * 0.38) + 95
        # Backing
        pygame.draw.rect(self.game.screen, (40, 10, 10), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(self.game.screen, (80, 20, 20), (bar_x, bar_y, bar_w, bar_h))
        # Fill
        fill = int(bar_w * phase)
        if fill > 0:
            pygame.draw.rect(self.game.screen, (255, 70, 50), (bar_x, bar_y, fill, bar_h))
        # Border + label
        pygame.draw.rect(self.game.screen, (255, 180, 80), (bar_x, bar_y, bar_w, bar_h), 2)
        label = self.render_shadowed_text("BOSS GAUGE", (255, 200, 100), game.tiny_font)
        self.game.screen.blit(label, (bar_x + (bar_w - label.get_width())//2 , bar_y - 22))

        # Small instruction / flavor
        hint = self.render_shadowed_text("The enemy flagship is near...", (200, 180, 160), game.tiny_font)
        self.game.screen.blit(hint, (w//2 - hint.get_width()//2, bar_y + 32))

    def draw_settings(self, game):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(self.game.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(game.stars)):
            game.stars[i] = ((game.stars[i][0] - game.star_speed) % SCREEN_WIDTH, game.stars[i][1])
        for star in game.stars:
            pygame.draw.circle(self.game.screen, WHITE, star, 1)
        settings_title = self.render_shadowed_text("Settings", WHITE, game.font)
        self.game.screen.blit(settings_title, (SCREEN_WIDTH//2 - settings_title.get_width()//2, 100))
        
        # Difficulty setting
        difficulty_text = f"Difficulty: {game.difficulty.title()}"
        difficulty_label = self.render_shadowed_text(difficulty_text, GREEN if game.selected_setting == 0 else WHITE, game.small_font)
        self.game.screen.blit(difficulty_label, (SCREEN_WIDTH//2 - difficulty_label.get_width()//2, 160))
        
        # Music Volume Bar
        music_label = self.render_shadowed_text("Music Volume", GREEN if game.selected_setting == 1 else WHITE, game.small_font)
        self.game.screen.blit(music_label, (SCREEN_WIDTH//2 - 100, 200))
        pygame.draw.rect(self.game.screen, WHITE, (SCREEN_WIDTH//2 - 100, 220, 200, 20), 2)
        pygame.draw.rect(self.game.screen, GREEN, (SCREEN_WIDTH//2 - 100, 220, int(game.music_volume * 200), 20))
        
        # SFX Volume Bar
        sfx_label = self.render_shadowed_text("SFX Volume", GREEN if game.selected_setting == 2 else WHITE, game.small_font)
        self.game.screen.blit(sfx_label, (SCREEN_WIDTH//2 - 100, 250))
        pygame.draw.rect(self.game.screen, WHITE, (SCREEN_WIDTH//2 - 100, 270, 200, 20), 2)
        pygame.draw.rect(self.game.screen, GREEN, (SCREEN_WIDTH//2 - 100, 270, int(game.sfx_volume * 200), 20))

        # R6: Window size toggle (960 default / 1280 optional stretch matching virtual base)
        ww = getattr(game, 'window_width', 960)
        stretch_label = "1280x720 (native)" if ww >= 1280 else "960x720 (default)"
        window_text = f"Window Size: {stretch_label}"
        window_label = self.render_shadowed_text(window_text, GREEN if game.selected_setting == 3 else WHITE, game.small_font)
        self.game.screen.blit(window_label, (SCREEN_WIDTH//2 - window_label.get_width()//2, 300))
        
        # Leaderboard option
        leaderboard_text = self.render_shadowed_text("View Leaderboard", GREEN if game.selected_setting == 4 else WHITE, game.small_font)
        self.game.screen.blit(leaderboard_text, (SCREEN_WIDTH//2 - leaderboard_text.get_width()//2, 330))
        
        # Upgrade Tree option
        upgrade_text = self.render_shadowed_text("Upgrade Tree", GREEN if game.selected_setting == 5 else WHITE, game.small_font)
        self.game.screen.blit(upgrade_text, (SCREEN_WIDTH//2 - upgrade_text.get_width()//2, 360))
        
        # Back option
        back_text = self.render_shadowed_text("Back to Menu", GREEN if game.selected_setting == 6 else WHITE, game.small_font)
        self.game.screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 390))
        
        hint_text = self.render_shadowed_text("Use ↑↓ to navigate, LEFT/RIGHT volumes/window, ENTER/A to select", WHITE, game.tiny_font)
        self.game.screen.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, 440))
        pygame.display.flip()

    def draw_credits(self, game):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(self.game.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(game.stars)):
            game.stars[i] = ((game.stars[i][0] - game.star_speed) % SCREEN_WIDTH, game.stars[i][1])
        for star in game.stars:
            pygame.draw.circle(self.game.screen, WHITE, star, 1)
        credits_title = self.render_shadowed_text("Credits", WHITE, game.font)
        self.game.screen.blit(credits_title, (SCREEN_WIDTH//2 - credits_title.get_width()//2, 50))
        credits_lines = [
            "Space Shooter Game",
            "Developed by: Spencer Reese",
            "Using Pygame",
            "Inspired by classic arcade shooters",
            "Thank you for playing!"
        ]
        for i, line in enumerate(credits_lines):
            text = self.render_shadowed_text(line, WHITE, game.small_font)
            self.game.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 150 + i*40))
        back_text = self.render_shadowed_text("Press ESC to go back", WHITE, game.small_font)
        self.game.screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, 500))
        pygame.display.flip()

    def _wrap_text(self, text, max_width, font):
        """Wrap text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines
        """Return appropriate emoji icon for shop item"""
        icon_map = {
            "Extra Life": "❤️",
            "Energy Capacity Upgrade": "⚡",
            "Energy Regeneration Upgrade": "🔋",
            "Speed Upgrade": "💨",
            "Shield Duration Upgrade": "🛡️",
            "Max Health Upgrade": "💚",
            "Damage Upgrade": "⚡",
            "Fire Rate Upgrade": "🔥",
            "Critical Chance Upgrade": "🎯",
            "Critical Damage Upgrade": "💥",
            "Coin Multiplier Upgrade": "💰",
            "Experience Multiplier Upgrade": "⭐",
            "Weapon Damage Upgrade": "🗡️",
            "Shotgun Damage Upgrade": "🔫",
            "Flamethrower Damage Upgrade": "🔥",
            "Lightning Damage Upgrade": "⚡",
            "Black Hole Damage Upgrade": "🕳️",
            "Freeze Beam Damage Upgrade": "❄️",
            "Bomb": "💣",
            "Missile Pack": "🚀",
            "Health Pack": "🩹",
            "Shotgun Weapon": "🔫",
            "Flamethrower Weapon": "🔥",
            "Lightning Weapon": "⚡",
            "Black Hole Weapon": "🕳️",
            "Freeze Beam Weapon": "❄️"
        }
        return icon_map.get(item_name, "❓")

    def draw_multiplayer_players(self, game):
        """Draw other multiplayer players"""
        if not game.is_multiplayer or not game.multiplayer_players:
            return

        for player_id, player_data in game.multiplayer_players.items():
            if player_id == getattr(game.network, 'player_id', None):
                continue  # Don't draw ourselves

            # Draw player ship
            x, y = player_data.get("x", 0), player_data.get("y", 0)
            health = player_data.get("health", 100)

            # Create a simple ship representation for other players
            ship_color = (0, 255, 0) if health > 50 else (255, 255, 0) if health > 25 else (255, 0, 0)

            # Draw ship triangle
            points = [
                (x, y - 15),  # Top
                (x - 10, y + 10),  # Bottom left
                (x + 10, y + 10)   # Bottom right
            ]
            pygame.draw.polygon(self.game.screen, ship_color, points)

            # Draw player name/ID
            name_font = pygame.font.Font(None, 20)
            name_text = name_font.render(f"P{player_id[-1]}", True, WHITE)
            self.game.screen.blit(name_text, (x - name_text.get_width() // 2, y - 35))

            # Draw projectile count for other players
            projectiles = player_data.get("projectiles", {})
            bullet_count = projectiles.get("bullet_count", 0)
            if bullet_count > 0:
                proj_font = pygame.font.Font(None, 16)
                proj_text = proj_font.render(f"B:{bullet_count}", True, YELLOW)
                self.game.screen.blit(proj_text, (x - proj_text.get_width() // 2, y + 20))

            # Draw enemy info for other players (if available)
            enemies = player_data.get("enemies", {})
            enemy_count = enemies.get("count", 0)
            if enemy_count > 0:
                enemy_font = pygame.font.Font(None, 16)
                enemy_text = enemy_font.render(f"E:{enemy_count}", True, RED)
                self.game.screen.blit(enemy_text, (x - enemy_text.get_width() // 2, y + 35))

            # Draw score for other players
            other_score = player_data.get("score", 0)
            if other_score > 0:
                score_font = pygame.font.Font(None, 16)
                score_text = score_font.render(f"S:{other_score}", True, CYAN)
                self.game.screen.blit(score_text, (x - score_text.get_width() // 2, y + 50))

            # Draw health bar for other players
            bar_width = 40
            bar_height = 4
            health_ratio = health / 100.0
            pygame.draw.rect(self.game.screen, RED, (x - bar_width//2, y - 25, bar_width, bar_height))
            pygame.draw.rect(self.game.screen, GREEN, (x - bar_width//2, y - 25, int(bar_width * health_ratio), bar_height))

    def draw_upgrade_tree(self, game):
        """Draw a visual upgrade tree showing upgrade categories and progression"""
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(15 * (y / SCREEN_HEIGHT))
            g = int(25 * (y / SCREEN_HEIGHT))
            b = int(35 * (y / SCREEN_HEIGHT))
            pygame.draw.line(self.game.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Draw stars
        for star in game.stars:
            pygame.draw.circle(self.game.screen, WHITE, star, 1)

        # Title
        title = self.render_shadowed_text("🌳 UPGRADE TREE", WHITE, game.font)
        self.game.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))

        # Current stats display
        stats_bg = pygame.Surface((300, 80), pygame.SRCALPHA)
        stats_bg.fill((0, 0, 0, 180))
        pygame.draw.rect(stats_bg, (100, 150, 200), (0, 0, 300, 80), 2, border_radius=10)
        self.game.screen.blit(stats_bg, (SCREEN_WIDTH//2 - 150, 80))

        # Display current coins and total upgrades
        total_upgrades = sum(game.upgrades.levels.values())
        coins_text = self.render_shadowed_text(f"💰 {game.coins}", GOLD, game.small_font)
        upgrades_text = self.render_shadowed_text(f"⬆️ {total_upgrades} Upgrades", CYAN, game.small_font)
        self.game.screen.blit(coins_text, (SCREEN_WIDTH//2 - coins_text.get_width()//2, 90))
        self.game.screen.blit(upgrades_text, (SCREEN_WIDTH//2 - upgrades_text.get_width()//2, 110))

        # Define upgrade categories and their positions
        upgrade_categories = {
            'core': {
                'title': 'CORE UPGRADES',
                'color': (100, 200, 100),
                'x': SCREEN_WIDTH//2 - 300,
                'y': 200,
                'upgrades': [
                    ('max_health', '❤️ Health', 'max_health'),
                    ('max_ammo', '🔋 Ammo', 'max_ammo'),
                    ('player_speed', '💨 Speed', 'player_speed'),
                    ('shield_duration', '🛡️ Shield', 'shield_duration')
                ]
            },
            'combat': {
                'title': 'COMBAT UPGRADES',
                'color': (200, 100, 100),
                'x': SCREEN_WIDTH//2 - 100,
                'y': 200,
                'upgrades': [
                    ('damage', '⚔️ Damage', 'damage'),
                    ('fire_rate', '🔥 Fire Rate', 'fire_rate'),
                    ('crit_chance', '🎯 Crit Chance', 'crit_chance'),
                    ('crit_damage', '💥 Crit Damage', 'crit_damage'),
                    ('weapon_damage', '🗡️ Weapon Damage', 'weapon_damage')
                ]
            },
            'weapons': {
                'title': 'WEAPON SPECIALIZATION',
                'color': (200, 150, 100),
                'x': SCREEN_WIDTH//2 + 100,
                'y': 200,
                'upgrades': [
                    ('shotgun_damage', '🏹 Shotgun', 'shotgun_damage'),
                    ('flamethrower_damage', '🔥 Flamethrower', 'flamethrower_damage'),
                    ('lightning_damage', '⚡ Lightning', 'lightning_damage'),
                    ('blackhole_damage', '🕳️ Black Hole', 'blackhole_damage'),
                    ('freeze_damage', '❄️ Freeze Beam', 'freeze_damage')
                ]
            },
            'utility': {
                'title': 'UTILITY UPGRADES',
                'color': (150, 100, 200),
                'x': SCREEN_WIDTH//2 + 300,
                'y': 200,
                'upgrades': [
                    ('coin_multiplier', '💰 Coin Multiplier', 'coin_multiplier'),
                    ('exp_multiplier', '⭐ Exp Multiplier', 'exp_multiplier')
                ]
            }
        }

        # Draw upgrade categories
        for category_key, category in upgrade_categories.items():
            # Category title
            title_color = category['color']
            title_text = self.render_shadowed_text(category['title'], title_color, game.tiny_font)
            self.game.screen.blit(title_text, (category['x'] - title_text.get_width()//2, category['y'] - 30))

            # Draw upgrade nodes
            for i, (upgrade_key, display_name, cost_key) in enumerate(category['upgrades']):
                node_x = category['x']
                node_y = category['y'] + i * 60

                # Get current level and next cost
                current_level = game.upgrades.levels.get(upgrade_key, 0)
                next_cost = game.upgrades.get_upgrade_cost(upgrade_key) if current_level < 10 else None
                can_afford = next_cost and game.coins >= next_cost

                # Node background color based on level and affordability
                if current_level > 0:
                    # Upgraded - green tint
                    node_color = (50, 100, 50, 220)
                    border_color = (100, 200, 100)
                elif can_afford:
                    # Can afford - blue tint
                    node_color = (50, 50, 150, 220)
                    border_color = (100, 100, 255)
                else:
                    # Cannot afford - gray
                    node_color = (60, 60, 60, 220)
                    border_color = (120, 120, 120)

                # Draw node background
                node_size = 120
                node_surf = pygame.Surface((node_size, 45), pygame.SRCALPHA)
                node_surf.fill(node_color)
                self.game.screen.blit(node_surf, (node_x - node_size//2, node_y))

                # Draw border
                pygame.draw.rect(self.game.screen, border_color,
                               (node_x - node_size//2, node_y, node_size, 45), 2, border_radius=5)

                # Upgrade name
                name_color = WHITE if current_level > 0 else (180, 180, 180)
                name_text = self.render_shadowed_text(display_name, name_color, game.tiny_font)
                self.game.screen.blit(name_text, (node_x - name_text.get_width()//2, node_y + 5))

                # Level indicator
                level_text = f"Lv.{current_level}"
                level_color = CYAN if current_level > 0 else (150, 150, 150)
                level_surf = self.render_shadowed_text(level_text, level_color, game.tiny_font)
                self.game.screen.blit(level_surf, (node_x - node_size//2 + 8, node_y + 25))

                # Next cost or max level indicator
                if current_level >= 10:
                    cost_text = self.render_shadowed_text("MAX", GOLD, game.tiny_font)
                elif next_cost:
                    cost_color = GOLD if can_afford else (150, 100, 100)
                    cost_text = self.render_shadowed_text(f"{next_cost}💰", cost_color, game.tiny_font)
                else:
                    cost_text = self.render_shadowed_text("???", (150, 150, 150), game.tiny_font)

                self.game.screen.blit(cost_text, (node_x + node_size//2 - cost_text.get_width() - 8, node_y + 25))

                # Draw connection lines between upgrades in same category
                if i > 0:
                    prev_y = category['y'] + (i-1) * 60 + 22
                    curr_y = node_y + 22
                    pygame.draw.line(self.game.screen, (80, 80, 80),
                                   (node_x, prev_y), (node_x, curr_y), 2)

        # Draw category connections (showing upgrade paths)
        # Core -> Combat
        pygame.draw.line(self.game.screen, (100, 100, 100),
                        (upgrade_categories['core']['x'], upgrade_categories['core']['y'] + 120),
                        (upgrade_categories['combat']['x'], upgrade_categories['combat']['y'] + 60), 3)

        # Combat -> Weapons
        pygame.draw.line(self.game.screen, (100, 100, 100),
                        (upgrade_categories['combat']['x'], upgrade_categories['combat']['y'] + 150),
                        (upgrade_categories['weapons']['x'], upgrade_categories['weapons']['y'] + 75), 3)

        # Combat -> Utility
        pygame.draw.line(self.game.screen, (100, 100, 100),
                        (upgrade_categories['combat']['x'], upgrade_categories['weapons']['x'] - upgrade_categories['combat']['x']),
                        (upgrade_categories['utility']['x'], upgrade_categories['utility']['y'] + 30), 3)

        nav_text = self.render_shadowed_text("Press ESC to return to menu", WHITE, game.tiny_font)
        self.game.screen.blit(nav_text, (SCREEN_WIDTH//2 - nav_text.get_width()//2, SCREEN_HEIGHT - 40))

        pygame.display.flip()

    def get_shop_item_icon(self, item_name):
        """Return appropriate emoji icon for shop item"""
        icon_map = {
            "Extra Life": "❤️",
            "Max Ammo Upgrade": "🔫",
            "Speed Upgrade": "💨",
            "Shield Duration Upgrade": "🛡️",
            "Max Health Upgrade": "💚",
            "Damage Upgrade": "⚡",
            "Bomb": "💣",
            "Missile Pack": "🚀",
            "Health Pack": "🩹",
            "Shotgun Weapon": "🔫",
            "Flamethrower Weapon": "🔥",
            "Lightning Weapon": "⚡",
            "Black Hole Weapon": "🕳️",
            "Freeze Beam Weapon": "❄️"
        }
        return icon_map.get(item_name, "❓")

    def _wrap_text(self, text, max_width, font):
        """Wrap text to fit within max_width, returning list of lines"""
        if not text:
            return []
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # Test if adding this word would exceed the width
            test_line = current_line + " " + word if current_line else word
            test_surface = font.render(test_line, True, (255, 255, 255))
            
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                # If current line is not empty, add it to lines
                if current_line:
                    lines.append(current_line)
                # Start new line with current word
                current_line = word
                
                # If single word is too long, truncate it
                test_surface = font.render(current_line, True, (255, 255, 255))
                if test_surface.get_width() > max_width:
                    # Truncate word
                    truncated = current_line
                    while font.render(truncated + "...", True, (255, 255, 255)).get_width() > max_width and len(truncated) > 0:
                        truncated = truncated[:-1]
                    current_line = truncated + "..."
        
        # Add the last line
        if current_line:
            lines.append(current_line)
            
        return lines