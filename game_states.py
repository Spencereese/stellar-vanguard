import pygame
import random
import math
import time

from projectiles import Bomb
from config import SCREEN_HEIGHT, SCREEN_WIDTH, BLUE, PURPLE, MODE_CAMPAIGN, MODE_ARCADE, MODE_SURVIVAL, MODE_MULTIPLAYER, DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT, BLACK, WHITE, YELLOW, GRAY, GREEN, GOLD, CYAN, SILVER, BRONZE
from enemies import Boss
from particles import Particle

# Base GameState class
class GameState:
    def __init__(self, game):
        self.game = game

    def enter(self):
        pass

    def exit(self):
        pass

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self):
        pass

# MenuState
class MenuState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.last_nav_time = 0

    def enter(self):
        # Calm menu background music
        self.game.play_music("menu_ambient")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.game.selected_option = (self.game.selected_option - 1) % len(self.game.menu_options)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.game.selected_option = (self.game.selected_option + 1) % len(self.game.menu_options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.game.selected_option == 0:  # Play Game
                    self.game.change_state(GameModeMenuState(self.game))
                elif self.game.selected_option == 1:  # Multiplayer
                    self.game.change_state(MultiplayerMenuState(self.game))
                elif self.game.selected_option == 2:  # Shop & Upgrades
                    self.game.change_state(ShopState(self.game))
                elif self.game.selected_option == 3:  # Settings
                    self.game.change_state(SettingsState(self.game))
                elif self.game.selected_option == 4:  # Quit
                    self.game.running = False
        elif event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:  # D-pad up
                self.game.selected_option = (self.game.selected_option - 1) % len(self.game.menu_options)
            elif event.value[1] == -1:  # D-pad down
                self.game.selected_option = (self.game.selected_option + 1) % len(self.game.menu_options)
        elif event.type == pygame.JOYAXISMOTION:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_nav_time > 200:
                if event.axis == 1:  # Left stick Y
                    if event.value < -0.5:  # Up
                        self.game.selected_option = (self.game.selected_option - 1) % len(self.game.menu_options)
                        self.last_nav_time = current_time
                    elif event.value > 0.5:  # Down
                        self.game.selected_option = (self.game.selected_option + 1) % len(self.game.menu_options)
                        self.last_nav_time = current_time
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button
                if self.game.selected_option == 0:  # Play Game
                    self.game.change_state(GameModeMenuState(self.game))
                elif self.game.selected_option == 1:  # Multiplayer
                    self.game.change_state(MultiplayerMenuState(self.game))
                elif self.game.selected_option == 2:  # Shop & Upgrades
                    self.game.change_state(ShopState(self.game))
                elif self.game.selected_option == 3:  # Settings
                    self.game.change_state(SettingsState(self.game))
                elif self.game.selected_option == 4:  # Quit
                    self.game.running = False
                elif self.game.selected_option == 6:  # Settings
                    self.game.change_state(SettingsState(self.game))
                elif self.game.selected_option == 7:  # Quit
                    self.game.running = False

    def draw(self):
        self.game.renderer.draw_menu(self.game)

# GameModeMenuState - Submenu for selecting game modes
class GameModeMenuState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.last_nav_time = 0
        self.game.selected_option = 0  # ensure clean selection for this menu (4 options)
        self.game_mode_options = ["Campaign Mode", "Arcade Mode", "Survival Mode", "Back"]

    def enter(self):
        self.game.play_music("menu_ambient")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.game.selected_option = (self.game.selected_option - 1) % len(self.game_mode_options)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.game.selected_option = (self.game.selected_option + 1) % len(self.game_mode_options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.game.selected_option == 0:  # Campaign Mode
                    self.game.game_mode = MODE_CAMPAIGN
                    self.game.level_manager.start_level(1)
                    self.game.change_state(LoadoutSelectState(self.game))  # PR5: loadout before play
                elif self.game.selected_option == 1:  # Arcade Mode
                    self.game.game_mode = MODE_ARCADE
                    self.game.change_state(LoadoutSelectState(self.game))
                elif self.game.selected_option == 2:  # Survival Mode
                    self.game.game_mode = MODE_SURVIVAL
                    self.game.survival = True
                    self.game.change_state(LoadoutSelectState(self.game))
                elif self.game.selected_option == 3:  # Back
                    self.game.change_state(MenuState(self.game))
            elif event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:  # D-pad up
                self.game.selected_option = (self.game.selected_option - 1) % len(self.game_mode_options)
            elif event.value[1] == -1:  # D-pad down
                self.game.selected_option = (self.game.selected_option + 1) % len(self.game_mode_options)
        elif event.type == pygame.JOYAXISMOTION:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_nav_time > 200:
                if event.axis == 1:  # Left stick Y
                    if event.value < -0.5:  # Up
                        self.game.selected_option = (self.game.selected_option - 1) % len(self.game_mode_options)
                        self.last_nav_time = current_time
                    elif event.value > 0.5:  # Down
                        self.game.selected_option = (self.game.selected_option + 1) % len(self.game_mode_options)
                        self.last_nav_time = current_time
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button
                if self.game.selected_option == 0:  # Campaign Mode
                    self.game.game_mode = MODE_CAMPAIGN
                    self.game.level_manager.start_level(1)
                    self.game.change_state(LoadoutSelectState(self.game))  # PR5: loadout before play
                elif self.game.selected_option == 1:  # Arcade Mode
                    self.game.game_mode = MODE_ARCADE
                    self.game.change_state(LoadoutSelectState(self.game))
                elif self.game.selected_option == 2:  # Survival Mode
                    self.game.game_mode = MODE_SURVIVAL
                    self.game.survival = True
                    self.game.change_state(LoadoutSelectState(self.game))
                elif self.game.selected_option == 3:  # Back
                    self.game.change_state(MenuState(self.game))
            elif event.button == 1 or event.button == 7:  # B or Start button to back
                self.game.change_state(MenuState(self.game))

    def draw(self):
        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            r = int(25 * (y / SCREEN_HEIGHT))
            g = 0
            b = int(50 * (y / SCREEN_HEIGHT))
            pygame.draw.line(self.game.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Update and draw stars
        for i in range(len(self.game.stars)):
            self.game.stars[i] = ((self.game.stars[i][0] - self.game.star_speed) % SCREEN_WIDTH, self.game.stars[i][1])
        for star in self.game.stars:
            pygame.draw.circle(self.game.screen, WHITE, star, 1)
        
        # Title
        title = self.game.renderer.render_shadowed_text("Select Game Mode", WHITE, self.game.font)
        self.game.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 180))
        
        # Subtitle
        subtitle = self.game.renderer.render_shadowed_text("Choose your adventure!", (200, 200, 255), self.game.small_font)
        self.game.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 210))
        
        # Options
        for i, option in enumerate(self.game_mode_options):
            color = GREEN if i == self.game.selected_option else WHITE
            option_text = self.game.renderer.render_shadowed_text(option, color, self.game.small_font)
            self.game.screen.blit(option_text, (SCREEN_WIDTH//2 - option_text.get_width()//2, 260 + i * 35))
        
        # Back hint
        back_text = self.game.renderer.render_shadowed_text("ESC or B to go back", (150, 150, 150), self.game.tiny_font)
        self.game.screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, SCREEN_HEIGHT - 50))
        
        pygame.display.flip()

# OptionsState
class OptionsState(GameState):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))
            elif event.key == pygame.K_1:
                self.game.difficulty = 'easy'
                self.game.apply_difficulty()
            elif event.key == pygame.K_2:
                self.game.difficulty = 'normal'
                self.game.apply_difficulty()
            elif event.key == pygame.K_3:
                self.game.difficulty = 'hard'
                self.game.apply_difficulty()
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button for easy
                self.game.difficulty = 'easy'
                self.game.apply_difficulty()
            elif event.button == 1:  # B button for normal
                self.game.difficulty = 'normal'
                self.game.apply_difficulty()
            elif event.button == 2:  # X button for hard
                self.game.difficulty = 'hard'
                self.game.apply_difficulty()
            elif event.button == 7:  # Start button to back
                self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_options(self.game)

# TutorialState
class TutorialState(GameState):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0 or event.button == 7:  # A or Start button
                self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_tutorial(self.game)

# LeaderboardState
class LeaderboardState(GameState):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0 or event.button == 7:  # A or Start button
                self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_leaderboard(self.game)

# SettingsState
class SettingsState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.last_nav_time = 0

    def enter(self):
        self.game.play_music("menu_ambient")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.game.selected_setting = (self.game.selected_setting - 1) % len(self.game.setting_options)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.game.selected_setting = (self.game.selected_setting + 1) % len(self.game.setting_options)
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                if self.game.selected_setting == 1:  # Music Volume
                    self.game.music_volume = max(0, self.game.music_volume - 0.1)
                    pygame.mixer.music.set_volume(self.game.music_volume)
                elif self.game.selected_setting == 2:  # SFX Volume
                    self.game.sfx_volume = max(0, self.game.sfx_volume - 0.1)
                    self.game.update_sound_volumes()
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                if self.game.selected_setting == 1:  # Music Volume
                    self.game.music_volume = min(1, self.game.music_volume + 0.1)
                    pygame.mixer.music.set_volume(self.game.music_volume)
                elif self.game.selected_setting == 2:  # SFX Volume
                    self.game.sfx_volume = min(1, self.game.sfx_volume + 0.1)
                    self.game.update_sound_volumes()
            elif event.key == pygame.K_RETURN:
                if self.game.selected_setting == 0:  # Difficulty
                    # Cycle through difficulties
                    if self.game.difficulty == 'easy':
                        self.game.difficulty = 'normal'
                    elif self.game.difficulty == 'normal':
                        self.game.difficulty = 'hard'
                    else:
                        self.game.difficulty = 'easy'
                    self.game.apply_difficulty()
                elif self.game.selected_setting == 3:  # Leaderboard
                    self.game.change_state(LeaderboardState(self.game))
                elif self.game.selected_setting == 4:  # Upgrade Tree
                    self.game.change_state(UpgradeTreeState(self.game))
                elif self.game.selected_setting == 5:  # Back
                    self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:  # D-pad up
                self.game.selected_setting = (self.game.selected_setting - 1) % len(self.game.setting_options)
            elif event.value[1] == -1:  # D-pad down
                self.game.selected_setting = (self.game.selected_setting + 1) % len(self.game.setting_options)
            elif event.value[0] == -1:  # D-pad left
                if self.game.selected_setting == 1:  # Music Volume
                    self.game.music_volume = max(0, self.game.music_volume - 0.1)
                    pygame.mixer.music.set_volume(self.game.music_volume)
                elif self.game.selected_setting == 2:  # SFX Volume
                    self.game.sfx_volume = max(0, self.game.sfx_volume - 0.1)
                    self.game.update_sound_volumes()
            elif event.value[0] == 1:  # D-pad right
                if self.game.selected_setting == 1:  # Music Volume
                    self.game.music_volume = min(1, self.game.music_volume + 0.1)
                    pygame.mixer.music.set_volume(self.game.music_volume)
                elif self.game.selected_setting == 2:  # SFX Volume
                    self.game.sfx_volume = min(1, self.game.sfx_volume + 0.1)
                    self.game.update_sound_volumes()
        elif event.type == pygame.JOYAXISMOTION:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_nav_time > 200:
                if event.axis == 1:  # Left stick Y
                    if event.value < -0.5:  # Up
                        self.game.selected_setting = (self.game.selected_setting - 1) % len(self.game.setting_options)
                        self.last_nav_time = current_time
                    elif event.value > 0.5:  # Down
                        self.game.selected_setting = (self.game.selected_setting + 1) % len(self.game.setting_options)
                        self.last_nav_time = current_time
                elif event.axis == 0:  # Left stick X
                    if event.value < -0.5:  # Left
                        if self.game.selected_setting == 1:  # Music Volume
                            self.game.music_volume = max(0, self.game.music_volume - 0.1)
                            pygame.mixer.music.set_volume(self.game.music_volume)
                        elif self.game.selected_setting == 2:  # SFX Volume
                            self.game.sfx_volume = max(0, self.game.sfx_volume - 0.1)
                            self.game.update_sound_volumes()
                        self.last_nav_time = current_time
                    elif event.value > 0.5:  # Right
                        if self.game.selected_setting == 1:  # Music Volume
                            self.game.music_volume = min(1, self.game.music_volume + 0.1)
                            pygame.mixer.music.set_volume(self.game.music_volume)
                        elif self.game.selected_setting == 2:  # SFX Volume
                            self.game.sfx_volume = min(1, self.game.sfx_volume + 0.1)
                            self.game.update_sound_volumes()
                        self.last_nav_time = current_time
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button
                if self.game.selected_setting == 0:  # Difficulty
                    # Cycle through difficulties
                    if self.game.difficulty == 'easy':
                        self.game.difficulty = 'normal'
                    elif self.game.difficulty == 'normal':
                        self.game.difficulty = 'hard'
                    else:
                        self.game.difficulty = 'easy'
                    self.game.apply_difficulty()
                elif self.game.selected_setting == 3:  # Leaderboard
                    self.game.change_state(LeaderboardState(self.game))
                elif self.game.selected_setting == 4:  # Upgrade Tree
                    self.game.change_state(UpgradeTreeState(self.game))
                elif self.game.selected_setting == 5:  # Back
                    self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_settings(self.game)

# CreditsState
class CreditsState(GameState):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0 or event.button == 7:  # A or Start button
                self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_credits(self.game)

# LoadoutSelectState (PR5 scaffolding)
class LoadoutSelectState(GameState):
    """PR5 stub: simple loadout select (archetypes from loadouts.py). Creative: 3 choices, apply on select, back to menu/playing.
    Input: up/down nav, 1/2/3 direct, RETURN apply+to play, ESC to main menu.
    """
    def __init__(self, game):
        super().__init__(game)
        self.options = ["Scout (fast/dash)", "Gunner (dmg)", "Tank (tough)"]
        self.selected = 0
        self.archetypes = ["scout", "gunner", "tank"]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_1:
                self.selected = 0
                self._apply_selected()
            elif event.key == pygame.K_2:
                self.selected = 1
                self._apply_selected()
            elif event.key == pygame.K_3:
                self.selected = 2
                self._apply_selected()
            elif event.key == pygame.K_RETURN:
                self._apply_selected()
            elif event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))

    def _apply_selected(self):
        arch = self.archetypes[self.selected]
        try:
            from loadouts import Loadout
            ld = Loadout(arch)
            if self.game.session:
                self.game.session.current_loadout = ld
            if self.game.player:
                ld.apply_to_player(self.game.player)
            # transition to playing after apply (PR5: loadout then play)
            self.game.change_state(PlayingState(self.game))
        except:
            self.game.change_state(PlayingState(self.game))

    def update(self):
        pass

    def draw(self):
        # Use the proper renderer implementation (virtual surface, scaling, polish)
        try:
            self.game.renderer.draw_loadout_select(self.game, self.options, self.selected)
        except Exception:
            # Last-resort fallback (should rarely be needed)
            font = self.game.font
            self.game.screen.fill((10, 0, 30))
            title = font.render("SELECT LOADOUT", True, (255, 220, 100))
            self.game.screen.blit(title, (100, 100))
            hint = self.game.small_font.render("UP/DOWN or 1/2/3 • SPACE/ENTER to apply • ESC back", True, (200,200,200))
            self.game.screen.blit(hint, (100, 140))
            for i, opt in enumerate(self.options):
                col = (255,255,0) if i==self.selected else (255,255,255)
                txt = font.render(f"{i+1}. {opt}", True, col)
                self.game.screen.blit(txt, (120, 180 + i*40))


# ModifierChoiceState (PR8 scaffolding for roguelite Vanguard Protocols)
class ModifierChoiceState(GameState):
    """PR8 stub: choose 1 of 3 random modifiers post-wave (or on demand). Creative: apply chosen to session, simple list UI fallback.
    Input: 1/2/3 or nav+RETURN. Applies and returns to Playing.
    """
    def __init__(self, game):
        super().__init__(game)
        from modifiers import get_random_modifiers
        self.options = []
        self.mods = get_random_modifiers(3)
        for m in self.mods:
            self.options.append(f"{m.name}: {m.desc}")
        self.selected = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % max(1, len(self.options))
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % max(1, len(self.options))
            elif event.key == pygame.K_1:
                self.selected = 0
                self._apply_selected()
            elif event.key == pygame.K_2:
                self.selected = 1
                self._apply_selected()
            elif event.key == pygame.K_3:
                self.selected = 2
                self._apply_selected()
            elif event.key == pygame.K_RETURN:
                self._apply_selected()
            elif event.key == pygame.K_ESCAPE:
                self.game.change_state(PlayingState(self.game))

    def _apply_selected(self):
        if self.selected < len(self.mods):
            mod = self.mods[self.selected]
            if self.game.session:
                self.game.session.active_modifiers = [mod]  # or append for stack; here replace for demo simplicity
                mod.apply(self.game.session)
        self.game.change_state(PlayingState(self.game))

    def update(self):
        pass

    def draw(self):
        try:
            # reuse or simple fallback
            font = self.game.font
            title = font.render("CHOOSE VANGUARD PROTOCOL (modifier)", True, (255,255,255))
            self.game.screen.blit(title, (80, 80))
            hint = self.game.small_font.render("1/2/3 or UP/DOWN+RETURN; ESC skip", True, (200,200,200))
            self.game.screen.blit(hint, (80, 110))
            for i, opt in enumerate(self.options):
                col = (255,255,0) if i==self.selected else (255,255,255)
                txt = font.render(f"{i+1}. {opt[:60]}", True, col)
                self.game.screen.blit(txt, (100, 150 + i*35))
        except:
            # Fallback clean draw for modifier choice
            screen = self.game.screen
            vw, vh = screen.get_width(), screen.get_height()
            for y in range(vh):
                r = int(10 * (y / float(vh)))
                g = int(5 * (y / float(vh)))
                b = int(35 * (y / float(vh)))
                pygame.draw.line(screen, (r, g, b), (0, y), (vw, y))
            for star in getattr(self.game, 'stars', []):
                sx = int(star[0] % vw)
                sy = int(star[1] % vh)
                pygame.draw.circle(screen, (180, 200, 255), (sx, sy), 1)
            font = self.game.font
            title = font.render("CHOOSE VANGUARD PROTOCOL", True, (100, 255, 200))
            screen.blit(title, (vw//2 - title.get_width()//2, 100))
            for i, opt in enumerate(self.options):
                col = (255,255,0) if i==self.selected else (255,255,255)
                txt = self.game.small_font.render(f"{i+1}. {opt[:55]}", True, col)
                screen.blit(txt, (vw//2 - txt.get_width()//2, 160 + i*40))
            hint = self.game.tiny_font.render("1/2/3 or ENTER to choose • ESC skip", True, (200,200,200))
            screen.blit(hint, (vw//2 - hint.get_width()//2, vh - 80))


class PlayingState(GameState):
    def enter(self):
        if not self.game.boss_spawned:
            self.game.reset_game()
        self.game.play_music("game_ambient")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.game.death_animation_timer <= 0:
                self.game.player.shoot()
            elif event.key == pygame.K_b and self.game.death_animation_timer <= 0:
                if self.game.player.bombs > 0:
                    bomb = Bomb(self.game.player.rect.right, self.game.player.rect.centery, self.game)
                    self.game.all_sprites.add(bomb)
                    self.game.bombs.add(bomb)
                    self.game.player.bombs -= 1
            elif event.key == pygame.K_m and self.game.death_animation_timer <= 0:
                self.game.player.fire_missile()
            elif event.key == pygame.K_p:
                self.game.paused = not self.game.paused
                if self.game.paused:
                    self.game.pause_music()
                else:
                    self.game.resume_music()
            elif event.key == pygame.K_g:
                self.game.god_mode = not self.game.god_mode
            elif event.key == pygame.K_ESCAPE:
                self.game.paused = not self.game.paused
                if self.game.paused:
                    self.game.pause_music()
                else:
                    self.game.resume_music()
            elif event.key == pygame.K_e and self.game.death_animation_timer <= 0:
                # Creative: trigger loadout ability (e.g. EMP)
                if hasattr(self.game, 'session') and self.game.session and self.game.player:
                    from loadouts import activate_ability
                    activate_ability(self.game.player, 'emp', self.game)
                    # visual feedback
                    if hasattr(self.game, 'particles'):
                        try:
                            from particles import Particle
                            for _ in range(15):
                                p = Particle(self.game.player.rect.centerx, self.game.player.rect.centery, (0,255,255), 'smoke')
                                self.game.particles.append(p)
                        except:
                            pass
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3) and self.game.death_animation_timer <= 0:
                # simple choose 1 of 3 stub for modifiers (PR7/8)
                if hasattr(self.game, 'session') and self.game.session:
                    from modifiers import get_random_modifiers
                    idx = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2}.get(event.key, 0)
                    mods = get_random_modifiers(3)
                    if idx < len(mods):
                        self.game.session.active_modifiers = [mods[idx]]
                        mods[idx].apply(self.game.session)
                    # in full: present choices in draw, apply only chosen, clear pending
            elif event.key == pygame.K_c and self.game.death_animation_timer <= 0:
                # manual open modifier choose (PR8) - 'c' for choose protocol (avoids K_m missile conflict)
                try:
                    self.game.change_state(ModifierChoiceState(self.game))
                except:
                    pass
            elif event.key == pygame.K_r and self.game.death_animation_timer <= 0:
                # full ability: repair (R)
                if hasattr(self.game, 'session') and self.game.session and self.game.player:
                    from loadouts import activate_ability
                    activate_ability(self.game.player, 'repair', self.game)
            elif event.key == pygame.K_q and self.game.death_animation_timer <= 0:
                # other ability stub (Q) - e.g. dash boost or future
                if hasattr(self.game, 'session') and self.game.session and self.game.player:
                    from loadouts import activate_ability
                    activate_ability(self.game.player, 'dash', self.game)  # reuse dash as example
                    # visual
                    if hasattr(self.game, 'particles'):
                        try:
                            from particles import Particle
                            for _ in range(8):
                                p = Particle(self.game.player.rect.centerx, self.game.player.rect.centery, (255,100,100), 'smoke')
                                self.game.particles.append(p)
                        except:
                            pass
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0 and self.game.death_animation_timer <= 0:  # A button
                self.game.player.shoot()
            elif event.button == 1 and self.game.death_animation_timer <= 0:  # B button
                if self.game.player.bombs > 0:
                    bomb = Bomb(self.game.player.rect.right, self.game.player.rect.centery, self.game)
                    self.game.all_sprites.add(bomb)
                    self.game.bombs.add(bomb)
                    self.game.player.bombs -= 1
            elif event.button == 2 and self.game.death_animation_timer <= 0:  # X button
                self.game.player.fire_missile()
            elif event.button == 7:  # Start button
                self.game.paused = not self.game.paused
                if self.game.paused:
                    self.game.pause_music()
                else:
                    self.game.resume_music()

    def update(self):
        if not self.game.paused:
            # Controller input
            if self.game.joystick:
                axis_x = self.game.joystick.get_axis(0)
                axis_y = self.game.joystick.get_axis(1)
                p = self.game.player
                eff_speed = getattr(p, 'speed', 5) * getattr(p, 'speed_multiplier', 1.0)
                self.game.player.change_x = axis_x * eff_speed
                self.game.player.change_y = axis_y * eff_speed
            else:
                self.game.player.change_x = 0
                self.game.player.change_y = 0
            
            # Continuous shooting for rapid fire
            keys = pygame.key.get_pressed()
            if 'rapid' in self.game.player.active_powerups:
                # Rapid fire allows continuous shooting
                if keys[pygame.K_SPACE] and self.game.death_animation_timer <= 0:
                    # Add a shoot timer to prevent infinite firing
                    if not hasattr(self.game.player, 'shoot_timer'):
                        self.game.player.shoot_timer = 0
                    self.game.player.shoot_timer += 1
                    # Use fire_rate upgrade to determine shoot cooldown (higher fire_rate = faster shooting)
                    shoot_cooldown = max(1, int(5 / self.game.fire_rate))  # Minimum 1 frame cooldown
                    if self.game.player.shoot_timer >= shoot_cooldown:
                        self.game.player.shoot()
                        self.game.player.shoot_timer = 0
            elif keys[pygame.K_SPACE] and self.game.death_animation_timer <= 0:
                # Reset shoot timer for non-rapid fire
                if hasattr(self.game.player, 'shoot_timer'):
                    self.game.player.shoot_timer = 0
            
            prev_death = getattr(self.game, 'death_animation_timer', 0)
            self.game.update_game_logic()
            # Update multiplayer state
            self.game.update_multiplayer()

            # Transition to continue/respawn prompt exactly when death anim finishes
            if prev_death > 0 and getattr(self.game, 'death_animation_timer', 0) <= 0:
                self.game.change_state(ContinuePromptState(self.game))
                return  # don't process further this frame

            # PR8: after even waves, enter ModifierChoiceState (stub UI for choose; headless may bypass via direct 1/2/3 in playing)
            if hasattr(self.game, 'session') and self.game.session and self.game.wave % 2 == 0 and len(getattr(self.game.session, 'active_modifiers', [])) == 0:
                try:
                    self.game.change_state(ModifierChoiceState(self.game))
                except Exception:
                    # headless/demo fallback
                    from modifiers import get_random_modifiers
                    chosen = get_random_modifiers(1)
                    self.game.session.active_modifiers.extend(chosen)
                    for m in chosen:
                        m.apply(self.game.session)

            # Dynamic music intensity based on combo / rank (extends background music)
            try:
                base_vol = self.game.music_volume
                combo = getattr(self.game, 'combo', 0)
                rank = getattr(self.game, 'style_rank', 'D')
                mult = 1.0
                if rank == 'S':
                    mult = 1.35
                elif rank == 'A':
                    mult = 1.2
                elif rank == 'B':
                    mult = 1.1
                elif combo >= 7:
                    mult = 1.15
                elif combo >= 4:
                    mult = 1.08
                eff_vol = min(1.0, base_vol * mult)
                pygame.mixer.music.set_volume(eff_vol)
            except:
                pass
        else:
            self.game.change_state(PauseMenuState(self.game))

    def draw(self):
        self.game.renderer.draw_playing(self.game)

# PauseMenuState
class PauseMenuState(GameState):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.paused = False
                self.game.resume_music()
                self.game.change_state(PlayingState(self.game))
            elif event.key == pygame.K_q:
                self.game.running = False
            elif event.key == pygame.K_n:
                self.game.paused = False
                self.game.resume_music()
                self.game.change_state(PlayingState(self.game))
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button for resume
                self.game.paused = False
                self.game.resume_music()
                self.game.change_state(PlayingState(self.game))
            elif event.button == 1:  # B button for quit
                self.game.running = False

    def draw(self):
        self.game.renderer.draw_pause_menu(self.game)

# ContinuePromptState
class ContinuePromptState(GameState):
    def __init__(self, game):
        super().__init__(game)
        # Dynamic options based on remaining lives
        if self.game.player.lives > 1:
            self.options = [f"Continue ({self.game.player.lives - 1} lives left)", "Shop", "Main Menu"]
        else:
            self.options = ["Continue (Last Life!)", "Shop", "Main Menu"]
        self.selected = 0
        self.last_nav_time = 0
        self.last_select_time = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                current_time = pygame.time.get_ticks()
                if current_time - self.last_select_time > 200:
                    self.last_select_time = current_time
                    if self.selected == 0:  # Continue
                        self.game.player.lives -= 1
                        if self.game.player.lives > 0:
                            self.game.continuing = True
                            # Set invincibility BEFORE changing state to prevent instant death
                            self.game.player.invincibility = True
                            self.game.player.invincibility_timer = 120  # 2 seconds invincibility
                            self.game.change_state(PlayingState(self.game))
                            # Reset player position to middle left
                            self.game.player.rect.centerx = SCREEN_WIDTH // 4
                            self.game.player.rect.centery = SCREEN_HEIGHT // 2
                            # Respawn spark animation
                            for _ in range(25):
                                angle = random.uniform(0, 2 * math.pi)
                                distance = random.randint(10, 30)
                                x = self.game.player.rect.centerx + math.cos(angle) * distance
                                y = self.game.player.rect.centery + math.sin(angle) * distance
                                p = Particle(x, y, BLUE, 'spark')
                                self.game.particles.append(p)
                        else:
                            self.game.change_state(GameOverState(self.game))
                    elif self.selected == 1:  # Shop
                        self.game.change_state(ShopState(self.game))
                    elif self.selected == 2:  # Quit
                        self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:  # D-pad up
                self.selected = (self.selected - 1) % len(self.options)
            elif event.value[1] == -1:  # D-pad down
                self.selected = (self.selected + 1) % len(self.options)
        elif event.type == pygame.JOYAXISMOTION:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_nav_time > 200:
                if event.axis == 1:  # Left stick Y
                    if event.value < -0.5:  # Up
                        self.selected = (self.selected - 1) % len(self.options)
                        self.last_nav_time = current_time
                    elif event.value > 0.5:  # Down
                        self.selected = (self.selected + 1) % len(self.options)
                        self.last_nav_time = current_time
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button
                current_time = pygame.time.get_ticks()
                if current_time - self.last_select_time > 200:
                    self.last_select_time = current_time
                    if self.selected == 0:  # Continue
                        self.game.player.lives -= 1
                        if self.game.player.lives > 0:
                            self.game.continuing = True
                            # Set invincibility BEFORE changing state to prevent instant death
                            self.game.player.invincibility = True
                            self.game.player.invincibility_timer = 120  # 2 seconds invincibility
                            self.game.change_state(PlayingState(self.game))
                            # Reset player position to middle left
                            self.game.player.rect.centerx = SCREEN_WIDTH // 4
                            self.game.player.rect.centery = SCREEN_HEIGHT // 2
                            # Respawn spark animation
                            for _ in range(25):
                                angle = random.uniform(0, 2 * math.pi)
                                distance = random.randint(10, 30)
                                x = self.game.player.rect.centerx + math.cos(angle) * distance
                                y = self.game.player.rect.centery + math.sin(angle) * distance
                                p = Particle(x, y, BLUE, 'spark')
                                self.game.particles.append(p)
                        else:
                            self.game.change_state(GameOverState(self.game))
                    elif self.selected == 1:  # Shop
                        self.game.change_state(ShopState(self.game))
                    elif self.selected == 2:  # Main Menu
                        self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_continue_prompt(self.game, self.options, self.selected)

# GameOverState
class GameOverState(GameState):
    def enter(self):
        self.game.play_music("menu_ambient")
        # PR3: Use persistence for highscore save (deduped, evolvable, with migration support)
        try:
            from persistence import get_persistence
            pers = get_persistence()
            current = pers.load_highscores()
            current.append(int(self.game.score))
            pers.save_highscores(sorted(current, reverse=True)[:10])

            # Update in-memory
            self.game.high_scores = pers.load_highscores()
            self.game.high_score = self.game.high_scores[0] if self.game.high_scores else 0
            # save settings example (PR12 polish) e.g. current volumes/diff etc
            try:
                pers.save_settings({
                    'music_volume': getattr(self.game, 'music_volume', 0.5),
                    'sfx_volume': getattr(self.game, 'sfx_volume', 0.5),
                    'difficulty': getattr(self.game, 'difficulty', 'normal'),
                    'colorblind_mode': getattr(self.game, 'colorblind_mode', None),
                    'mouse_aim': getattr(self.game, 'mouse_aim', False),
                })
            except:
                pass
        except Exception:
            pass  # graceful during transition
        self.game.just_defeated_boss = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                # Reset game state for restart
                self.game.continuing = False
                self.game.boss_spawned = False
                self.game.level_manager.current_level = 1
                self.game.change_state(PlayingState(self.game))
            elif event.key == pygame.K_s:
                self.game.change_state(ShopState(self.game))
            elif event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button for restart
                # Reset game state for restart
                self.game.continuing = False
                self.game.boss_spawned = False
                self.game.level_manager.current_level = 1
                self.game.change_state(PlayingState(self.game))
            elif event.button == 1:  # B button for shop
                self.game.change_state(ShopState(self.game))
            elif event.button == 7:  # Start button for menu
                self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_game_over(self.game)

# ShopState
class ShopState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.last_nav_time = 0
        self.purchase_message = ""

    def enter(self):
        self.game.play_music("menu_ambient")
        self.purchase_message_time = 0
        self.is_post_boss = getattr(self.game, 'just_defeated_boss', False)
        self.skip_bonus = 50  # always set (main shop featured also calls generate which builds skip card)
        if self.is_post_boss:
            # Consume flag
            self.game.just_defeated_boss = False
            # Modern roguelite post-boss reward: rank-gated free rerolls + claimed state
            rank = getattr(self.game, 'style_rank', 'D')
            self.free_rerolls = 1 + (1 if rank in ('S', 'A') else (1 if rank == 'B' else 0))
            self.rerolls_remaining = self.free_rerolls
            self.has_claimed_reward = False
            self.post_boss_items = self._generate_post_boss_choices(3)
            self.category_items = self.post_boss_items
            self.categories = ["boss rewards"]
            self.current_category = 0
            self.game.selected_item = 0
        else:
            self.categories = ["all", "consumables", "weapons", "upgrades", "special"]
            self.current_category = 0  # Index into categories list
            self.category_items = []  # Filtered items for current category
            self._update_category_items()
            # Modern shop: generate featured 3 random on visit (roguelite style)
            self.featured_items = self._generate_post_boss_choices(3)

    def _update_category_items(self):
        """Update the list of items for the current category"""
        if getattr(self, 'is_post_boss', False):
            self.category_items = self.post_boss_items
            return
        category = self.categories[self.current_category]
        if category == "all":
            self.category_items = self.game.shop_items
        else:
            self.category_items = [item for item in self.game.shop_items if item.get("category") == category]

        # Reset selection if it's out of bounds
        if self.game.selected_item >= len(self.category_items):
            self.game.selected_item = 0

    # --- Modern roguelite shop enhancements (Hades/StS/Isaac-inspired) ---
    RARITY_TIERS = ['common', 'rare', 'epic', 'legendary']
    RARITY_WEIGHTS_BASE = [55, 30, 12, 3]  # conservative; higher rank biases better

    def _get_rarity_colors(self, rarity):
        """Return (border, badge, glow_alpha) for rarity visual."""
        if rarity == 'legendary':
            return (GOLD, GOLD, 120)
        elif rarity == 'epic':
            return (PURPLE, (180, 80, 220), 90)
        elif rarity == 'rare':
            return (CYAN, (80, 180, 255), 70)
        return (SILVER, (160, 160, 160), 40)  # common subtle

    def _assign_rarity_and_synergy(self, item, player_rank="D", player_weapon="", loadout=None, active_mods=None):
        """Assign rarity (weighted by rank) + synergy tag based on current build (weapon/loadout/mods/rank).
        Conservative: visual + minor bonus on high rarity for dynamic post-boss; no power creep.
        """
        import random as _r  # local to avoid shadowing
        weights = self.RARITY_WEIGHTS_BASE[:]
        if player_rank in ("S", "A"):
            weights = [30, 35, 25, 10]
        elif player_rank == "B":
            weights = [42, 33, 18, 7]
        rarity = _r.choices(self.RARITY_TIERS, weights=weights, k=1)[0]
        item["rarity"] = rarity
        item["rarity_note"] = f"[{rarity.upper()}]" if rarity != "common" else ""

        # Synergy detection (simple, extensible; uses existing state)
        synergy = False
        tag = ""
        w = (player_weapon or "").lower()
        arch = getattr(loadout, "archetype", "") if loadout else ""
        iname = item.get("name", "").lower()
        cat = item.get("category", "")
        # Weapon/loadout bias examples
        if ("flame" in w or "flamethrower" in w or "fire" in iname) and ("flame" in iname or "damage" in iname or "fire" in iname):
            synergy = True
            tag = "SYNERGY (FIRE)"
        elif ("rail" in w or "railgun" in w) and ("pierce" in iname or "damage" in iname or "weapon" in cat):
            synergy = True
            tag = "SYNERGY (RAIL)"
        elif "gunner" in arch and ("damage" in iname or "weapon" in cat or "crit" in iname):
            synergy = True
            tag = "RECOMMENDED (GUNNER)"
        elif "tank" in arch and ("health" in iname or "shield" in iname or "life" in iname):
            synergy = True
            tag = "RECOMMENDED (TANK)"
        elif "scout" in arch and ("speed" in iname or "energy" in iname or "regen" in iname):
            synergy = True
            tag = "RECOMMENDED (SCOUT)"
        # Mod synergy (e.g. glass_cannon likes damage)
        if active_mods:
            mod_names = " ".join([getattr(m, 'name', str(m)).lower() for m in active_mods])
            if "glass" in mod_names and "damage" in iname:
                synergy = True
                tag = (tag + " + GLASS").strip(" +") if tag else "SYNERGY (GLASS CANNON)"
            if "resource" in mod_names and ("coin" in iname or "ammo" in iname):
                synergy = True
                tag = (tag + " + RESOURCE").strip(" +") if tag else "SYNERGY (RESOURCEFUL)"
        item["synergy"] = synergy
        item["synergy_tag"] = tag
        if synergy and tag:
            base_desc = item.get("description", "")
            if tag not in base_desc:
                item["description"] = (base_desc + " • " + tag).strip()

        # Enhanced preview for dynamic upgrades (shows current -> next, respects Upgrades)
        if item.get("dynamic_cost") and "cost_key" in item:
            key = item["cost_key"]
            u = self.game.upgrades
            lvl = u.levels.get(key, 0)
            curr = u.data.get(key, u.get_base_value(key))
            inc = u.get_increment(key) * (0.95 ** lvl)
            nxt = curr + max(0.01 if isinstance(curr, float) else 1, inc)
            preview = f"Lv{lvl}: {curr:.2f}→{nxt:.2f}" if isinstance(curr, float) else f"Lv{lvl}: {int(curr)}→{int(nxt)}"
            item["display_desc"] = preview
            if rarity in ("epic", "legendary"):
                item["display_desc"] += " [EPIC+]"
        return item

    def _generate_post_boss_choices(self, n=3):
        """Best-in-class post-boss: 3 curated (Hades 3-boon style) + explicit skip.
        - Rarity tiers (weighted by rank)
        - Synergy bias from loadout/weapon/mods/rank (Isaac/Gungeon style)
        - Diversity guarantee (spread weapons/upgrades/special)
        - Discount + one-time
        - Skip card as 4th for agency (Slay the Spire skip)
        """
        pool = [item for item in self.game.shop_items if item.get("category") in ("upgrades", "weapons", "special")]
        if len(pool) < n:
            pool = list(self.game.shop_items)

        # Bucket for diversity (guarantee spread like modern roguelites)
        buckets = {"weapons": [], "upgrades": [], "special_consumable": []}
        for it in pool:
            cat = it.get("category", "")
            nm = it.get("name", "")
            if "weapon" in cat.lower() or "Weapon" in nm:
                buckets["weapons"].append(it)
            elif cat == "upgrades":
                buckets["upgrades"].append(it)
            else:
                buckets["special_consumable"].append(it)

        chosen = []
        seen = set()
        # Priority pass: at most ONE from each bucket for guaranteed diversity (weapons, upgrades, special)
        order = ["weapons", "upgrades", "special_consumable"]
        for bname in order:
            if len(chosen) >= n:
                break
            for cand in buckets.get(bname, []):
                key = cand.get("cost_key") or cand.get("name")
                if key not in seen:
                    seen.add(key)
                    c = dict(cand)
                    if "cost" in c and not c.get("dynamic_cost"):
                        c["cost"] = max(50, int(c["cost"] * 0.75))
                        c["post_boss_discount"] = True
                    c["post_boss"] = True
                    loadout = getattr(getattr(self.game, "session", None), "current_loadout", None)
                    mods = getattr(getattr(self.game, "session", None), "active_modifiers", None)
                    weapon = getattr(getattr(self.game, "player", None), "weapon", "")
                    rank = getattr(self.game, "style_rank", "D")
                    c = self._assign_rarity_and_synergy(c, rank, weapon, loadout, mods)
                    chosen.append(c)
                    break  # only one per bucket in priority pass
        # Fill remaining randomly (deduped) from full pool
        random.shuffle(pool)
        for item in pool:
            if len(chosen) >= n:
                break
            key = item.get("cost_key") or item.get("name")
            if key not in seen:
                seen.add(key)
                c = dict(item)
                if "cost" in c and not c.get("dynamic_cost"):
                    c["cost"] = max(50, int(c["cost"] * 0.75))
                    c["post_boss_discount"] = True
                c["post_boss"] = True
                loadout = getattr(getattr(self.game, "session", None), "current_loadout", None)
                mods = getattr(getattr(self.game, "session", None), "active_modifiers", None)
                weapon = getattr(getattr(self.game, "player", None), "weapon", "")
                rank = getattr(self.game, "style_rank", "D")
                c = self._assign_rarity_and_synergy(c, rank, weapon, loadout, mods)
                chosen.append(c)

        # Explicit SKIP as always-available 4th (agency, StS-style; small positive to feel fair)
        skip_item = {
            "name": "SKIP / TAKE NONE",
            "cost": 0,
            "description": f"Forfeit reward. +{self.skip_bonus} coins for the run.",
            "effect": lambda: setattr(self.game, "coins", getattr(self.game, "coins", 0) + self.skip_bonus),
            "skip": True,
            "icon": "⏭️",
            "post_boss": True,
            "rarity": "common",
            "rarity_note": "",
            "synergy": False,
            "synergy_tag": "",
        }
        chosen.append(skip_item)
        return chosen

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if getattr(self, 'is_post_boss', False):
                    # Post-boss: always allow continue (even mid-claim or after)
                    self.game.change_state(PlayingState(self.game))
                else:
                    self.game.change_state(GameOverState(self.game))
            # Category switch only for main shop (non-post)
            if not getattr(self, 'is_post_boss', False):
                if event.key == pygame.K_q:  # Previous category
                    self.current_category = (self.current_category - 1) % len(self.categories)
                    self._update_category_items()
                elif event.key == pygame.K_e:  # Next category
                    self.current_category = (self.current_category + 1) % len(self.categories)
                    self._update_category_items()

            # Reroll handling (post uses free then paid; main paid) - top level to avoid elif swallowing
            if event.key == pygame.K_r:
                if getattr(self, 'is_post_boss', False):
                    # Post-boss: free (rank) first, then affordable paid rerolls (escalating optional)
                    if self.rerolls_remaining > 0:
                        cost = 0
                        self.rerolls_remaining -= 1
                    else:
                        cost = 50  # simple paid after frees
                    if cost > 0 and self.game.coins < cost:
                        self.purchase_message = f"Not enough for reroll ({cost}💰)!"
                        self.purchase_message_time = pygame.time.get_ticks()
                    else:
                        if cost > 0:
                            self.game.coins -= cost
                        self.post_boss_items = self._generate_post_boss_choices(3)
                        self.category_items = self.post_boss_items
                        self.game.selected_item = 0
                        fr = self.rerolls_remaining
                        self.purchase_message = f"Rerolled! ({fr} free left)" if fr > 0 else "Rerolled (paid 50)"
                        self.purchase_message_time = pygame.time.get_ticks()
                else:
                    # Main shop featured reroll (paid)
                    reroll_cost = 150
                    if self.game.coins >= reroll_cost:
                        self.game.coins -= reroll_cost
                        self.featured_items = self._generate_post_boss_choices(3)
                        self.purchase_message = "Featured offers rerolled!"
                        self.purchase_message_time = pygame.time.get_ticks()
                    else:
                        self.purchase_message = "Not enough for reroll!"
                        self.purchase_message_time = pygame.time.get_ticks()
            elif event.key == pygame.K_w or event.key == pygame.K_UP:
                # Move up in grid (3 items per row)
                items_per_row = 3
                current_row = self.game.selected_item // items_per_row
                current_col = self.game.selected_item % items_per_row
                new_row = max(0, current_row - 1)
                new_index = new_row * items_per_row + current_col
                if new_index < len(self.category_items):
                    self.game.selected_item = new_index
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                # Move down in grid (3 items per row)
                items_per_row = 3
                current_row = self.game.selected_item // items_per_row
                current_col = self.game.selected_item % items_per_row
                max_row = (len(self.category_items) - 1) // items_per_row
                new_row = min(max_row, current_row + 1)
                new_index = new_row * items_per_row + current_col
                if new_index < len(self.category_items):
                    self.game.selected_item = new_index
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                # Move left in grid
                self.game.selected_item = (self.game.selected_item - 1) % len(self.category_items)
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                # Move right in grid
                self.game.selected_item = (self.game.selected_item + 1) % len(self.category_items)
            elif event.key == pygame.K_RETURN:
                item = self.category_items[self.game.selected_item]
                if getattr(self, 'is_post_boss', False) and getattr(self, 'has_claimed_reward', False) and not item.get('skip'):
                    self.purchase_message = "Reward claimed — ESC to continue to next level."
                    self.purchase_message_time = pygame.time.get_ticks()
                else:
                    if item.get('dynamic_cost', False):
                        cost = self.game.upgrades.get_upgrade_cost(item['cost_key'])
                    else:
                        cost = item.get('cost', 0)
                    if self.game.coins >= cost:
                        self.game.coins -= cost
                        # Apply effect (skip or upgrade)
                        item["effect"]()
                        if item.get('skip'):
                            self.purchase_message = f"Skipped — +{self.skip_bonus} coins!"
                            self.purchase_message_time = pygame.time.get_ticks()
                            # Skip immediately proceeds (agency)
                            self.game.change_state(PlayingState(self.game))
                            return
                        self.purchase_message = f"Purchased {item['name']}!"
                        self.purchase_message_time = pygame.time.get_ticks()
                        if getattr(self, 'is_post_boss', False):
                            # Post-boss: claim exactly one (Hades boon feel). Mark + lock further.
                            self.has_claimed_reward = True
                            self.rerolls_remaining = 0
                            name = item.get('name')
                            # Keep only the chosen + skip for clean "continue" UX
                            self.category_items = [it for it in self.category_items if it.get('name') == name or it.get('skip')]
                            if self.game.selected_item >= len(self.category_items):
                                self.game.selected_item = max(0, len(self.category_items) - 1)
                            # Epic/Legendary bonus: one extra apply for dynamic (visual juice, conservative)
                            if item.get('rarity') in ('epic', 'legendary') and item.get('dynamic_cost'):
                                try:
                                    item["effect"]()
                                    self.purchase_message = f"Purchased {item['name']}! [EPIC BONUS]"
                                except Exception:
                                    pass
                    else:
                        self.purchase_message = "Not enough coins!"
                        self.purchase_message_time = pygame.time.get_ticks()
        elif event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:  # D-pad up
                items_per_row = 3
                current_row = self.game.selected_item // items_per_row
                current_col = self.game.selected_item % items_per_row
                new_row = max(0, current_row - 1)
                new_index = new_row * items_per_row + current_col
                if new_index < len(self.category_items):
                    self.game.selected_item = new_index
            elif event.value[1] == -1:  # D-pad down
                items_per_row = 3
                current_row = self.game.selected_item // items_per_row
                current_col = self.game.selected_item % items_per_row
                max_row = (len(self.category_items) - 1) // items_per_row
                new_row = min(max_row, current_row + 1)
                new_index = new_row * items_per_row + current_col
                if new_index < len(self.category_items):
                    self.game.selected_item = new_index
            elif event.value[0] == -1:  # D-pad left
                self.game.selected_item = (self.game.selected_item - 1) % len(self.category_items)
            elif event.value[0] == 1:  # D-pad right
                self.game.selected_item = (self.game.selected_item + 1) % len(self.category_items)
            elif not getattr(self, 'is_post_boss', False):
                if event.value[0] == -1 and event.value[1] == 0:  # Left shoulder (LB)
                    self.current_category = (self.current_category - 1) % len(self.categories)
                    self._update_category_items()
                elif event.value[0] == 1 and event.value[1] == 0:  # Right shoulder (RB)
                    self.current_category = (self.current_category + 1) % len(self.categories)
                    self._update_category_items()
        elif event.type == pygame.JOYAXISMOTION:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_nav_time > 200:
                if event.axis == 1:  # Left stick Y
                    if event.value < -0.5:  # Up
                        items_per_row = 3
                        current_row = self.game.selected_item // items_per_row
                        current_col = self.game.selected_item % items_per_row
                        new_row = max(0, current_row - 1)
                        new_index = new_row * items_per_row + current_col
                        if new_index < len(self.category_items):
                            self.game.selected_item = new_index
                        self.last_nav_time = current_time
                    elif event.value > 0.5:  # Down
                        items_per_row = 3
                        current_row = self.game.selected_item // items_per_row
                        current_col = self.game.selected_item % items_per_row
                        max_row = (len(self.category_items) - 1) // items_per_row
                        new_row = min(max_row, current_row + 1)
                        new_index = new_row * items_per_row + current_col
                        if new_index < len(self.category_items):
                            self.game.selected_item = new_index
                        self.last_nav_time = current_time
                elif event.axis == 0:  # Left stick X
                    if event.value < -0.5:  # Left
                        self.game.selected_item = (self.game.selected_item - 1) % len(self.category_items)
                        self.last_nav_time = current_time
                    elif event.value > 0.5:  # Right
                        self.game.selected_item = (self.game.selected_item + 1) % len(self.category_items)
                        self.last_nav_time = current_time
                elif not getattr(self, 'is_post_boss', False):
                    if event.axis == 2:  # Left trigger (LT)
                        if event.value > 0.5:
                            self.current_category = (self.current_category - 1) % len(self.categories)
                            self._update_category_items()
                            self.last_nav_time = current_time
                    elif event.axis == 5:  # Right trigger (RT)
                        if event.value > 0.5:
                            self.current_category = (self.current_category + 1) % len(self.categories)
                            self._update_category_items()
                            self.last_nav_time = current_time
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A button
                item = self.category_items[self.game.selected_item]
                if getattr(self, 'is_post_boss', False) and getattr(self, 'has_claimed_reward', False) and not item.get('skip'):
                    self.purchase_message = "Reward claimed — Start/ESC to continue to next level."
                    self.purchase_message_time = pygame.time.get_ticks()
                else:
                    if item.get('dynamic_cost', False):
                        cost = self.game.upgrades.get_upgrade_cost(item['cost_key'])
                    else:
                        cost = item.get('cost', 0)
                    if self.game.coins >= cost:
                        self.game.coins -= cost
                        item["effect"]()
                        if item.get('skip'):
                            self.purchase_message = f"Skipped — +{self.skip_bonus} coins!"
                            self.purchase_message_time = pygame.time.get_ticks()
                            self.game.change_state(PlayingState(self.game))
                            return
                        self.purchase_message = f"Purchased {item['name']}!"
                        self.purchase_message_time = pygame.time.get_ticks()
                        if getattr(self, 'is_post_boss', False):
                            self.has_claimed_reward = True
                            self.rerolls_remaining = 0
                            name = item.get('name')
                            self.category_items = [it for it in self.category_items if it.get('name') == name or it.get('skip')]
                            if self.game.selected_item >= len(self.category_items):
                                self.game.selected_item = max(0, len(self.category_items) - 1)
                            if item.get('rarity') in ('epic', 'legendary') and item.get('dynamic_cost'):
                                try:
                                    item["effect"]()
                                    self.purchase_message = f"Purchased {item['name']}! [EPIC BONUS]"
                                except Exception:
                                    pass
                    else:
                        self.purchase_message = "Not enough coins!"
                        self.purchase_message_time = pygame.time.get_ticks()
            elif event.button == 4:  # Left shoulder (LB)
                if not getattr(self, 'is_post_boss', False):
                    self.current_category = (self.current_category - 1) % len(self.categories)
                    self._update_category_items()
            elif event.button == 5:  # Right shoulder (RB)
                if not getattr(self, 'is_post_boss', False):
                    self.current_category = (self.current_category + 1) % len(self.categories)
                    self._update_category_items()
            elif event.button == 7:  # Start button to back
                if getattr(self, 'is_post_boss', False):
                    self.game.change_state(PlayingState(self.game))
                else:
                    self.game.change_state(GameOverState(self.game))

    def draw(self):
        self.game.renderer.draw_shop(self.game, self.purchase_message, self.purchase_message_time)

# UpgradeTreeState
class UpgradeTreeState(GameState):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0 or event.button == 7:  # A or Start button
                self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_upgrade_tree(self.game)

# AchievementsState
class AchievementsState(GameState):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0 or event.button == 7:  # A or Start button
                self.game.change_state(MenuState(self.game))

    def draw(self):
        self.game.renderer.draw_achievements(self.game)

# VictoryState
class VictoryState(GameState):
    def enter(self):
        self.game.play_music("menu_ambient")
        self.input_delay = 30  # 0.5 second delay before accepting input
        # Build options for better flow
        self.options = ["Continue to Next Level"]
        if getattr(self.game, 'just_defeated_boss', False):
            self.options.append("Claim Post-Boss Reward (3 Powerful Choices + Rerolls)")
        self.options.append("Main Menu")
        self.selected = 0
    
    def handle_event(self, event):
        if self.input_delay > 0:
            return  # Ignore input during delay
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select_option()
            elif event.key == pygame.K_ESCAPE:
                self.game.just_defeated_boss = False
                self.game.change_state(MenuState(self.game))
        elif event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.value[1] == -1:
                self.selected = (self.selected + 1) % len(self.options)
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A continue/select
                self._select_option()
            elif event.button == 7:  # Start menu
                self.game.just_defeated_boss = False
                self.game.change_state(MenuState(self.game))

    def _select_option(self):
        choice = self.options[self.selected]
        if "Continue" in choice:
            self.game.just_defeated_boss = False
            self.game.change_state(PlayingState(self.game))
        elif "Shop" in choice or "Upgrade" in choice or "Reward" in choice or "Post-Boss" in choice:
            # Go to shop; flag will be handled in shop for post-boss mode
            self.game.change_state(ShopState(self.game))
        else:
            self.game.just_defeated_boss = False
            self.game.change_state(MenuState(self.game))

    def update(self):
        if self.input_delay > 0:
            self.input_delay -= 1

    def draw(self):
        self.game.renderer.draw_victory(self.game)

# BossIncomingState
class BossIncomingState(GameState):
    def enter(self):
        self.timer = 0
        self.game.play_music("boss_music")

    def update(self):
        self.timer += 1
        if self.timer > 180:  # 3 seconds
            # Spawn boss
            boss = Boss(self.game)
            self.game.all_sprites.add(boss)
            self.game.enemies.add(boss)
            self.game.boss_spawned = True
            # Boss spawn smoke animation
            for _ in range(30):
                p = Particle(boss.rect.centerx, boss.rect.centery, PURPLE, 'smoke')
                self.game.particles.append(p)
            self.game.change_state(PlayingState(self.game))

    def draw(self):
        self.game.renderer.draw_boss_incoming(self.game)

# MultiplayerMenuState
class MultiplayerMenuState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["Host Game", "Join Game", "P2P Game", "Back"]
        self.selected = 0
        self.last_nav_time = 0
        self.server_host = DEFAULT_SERVER_HOST
        self.server_port = DEFAULT_SERVER_PORT
        self.input_mode = None  # 'host' or 'port'
        self.input_text = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.input_mode:
                # Handle text input for host/port
                if event.key == pygame.K_RETURN:
                    if self.input_mode == 'host':
                        self.server_host = self.input_text if self.input_text else DEFAULT_SERVER_HOST
                        self.input_mode = 'port'
                        self.input_text = str(self.server_port)
                    elif self.input_mode == 'port':
                        try:
                            self.server_port = int(self.input_text) if self.input_text else DEFAULT_SERVER_PORT
                        except ValueError:
                            self.server_port = DEFAULT_SERVER_PORT
                        self.input_mode = None
                        self.input_text = ""
                        # Start the multiplayer game
                        if self.selected == 0:  # Host
                            if self.game.start_multiplayer_server(self.server_host, self.server_port):
                                self.game.game_mode = MODE_MULTIPLAYER
                                self.game.change_state(PlayingState(self.game))
                        elif self.selected == 1:  # Join
                            if self.game.join_multiplayer_game(self.server_host, self.server_port):
                                self.game.game_mode = MODE_MULTIPLAYER
                                self.game.change_state(PlayingState(self.game))
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_mode = None
                    self.input_text = ""
            else:
                # Handle menu navigation
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    if self.selected == 0:  # Host Game
                        self.input_mode = 'host'
                        self.input_text = self.server_host
                    elif self.selected == 1:  # Join Game
                        self.input_mode = 'host'
                        self.input_text = self.server_host
                    elif self.selected == 2:  # P2P Game
                        # Start P2P multiplayer directly
                        player_name = f"Player_{int(time.time()) % 1000}"
                        if self.game.start_p2p_multiplayer(player_name):
                            self.game.game_mode = MODE_MULTIPLAYER
                            self.game.change_state(PlayingState(self.game))
                    elif self.selected == 3:  # Back
                        self.game.change_state(MenuState(self.game))

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill(BLACK)

        # Draw title
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("Multiplayer", True, WHITE)
        self.game.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))

        # Draw menu options
        menu_font = pygame.font.Font(None, 36)
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            text = menu_font.render(option, True, color)
            y_pos = 250 + i * 60
            self.game.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_pos))

        # Draw input field if in input mode
        if self.input_mode:
            input_font = pygame.font.Font(None, 32)
            prompt = f"Enter server {self.input_mode}:"
            prompt_text = input_font.render(prompt, True, WHITE)
            self.game.screen.blit(prompt_text, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, 450))

            input_bg = pygame.Rect(SCREEN_WIDTH // 2 - 150, 490, 300, 40)
            pygame.draw.rect(self.game.screen, GRAY, input_bg)
            pygame.draw.rect(self.game.screen, WHITE, input_bg, 2)

            input_text = input_font.render(self.input_text, True, BLACK)
            self.game.screen.blit(input_text, (SCREEN_WIDTH // 2 - input_text.get_width() // 2, 500))

            # Instructions
            instr_font = pygame.font.Font(None, 24)
            instr_text = instr_font.render("Press ENTER to confirm, ESC to cancel", True, WHITE)
            self.game.screen.blit(instr_text, (SCREEN_WIDTH // 2 - instr_text.get_width() // 2, 550))