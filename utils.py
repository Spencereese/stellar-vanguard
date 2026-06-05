import pygame
import os

# ---------------------------------------------------------------------------
# AssetManager (PR1)
# Centralizes image + sound loading with caching and theme hooks.
# Preserves the exact load_image_with_fallback contract (including draw_func
# for procedural fallbacks) so existing call sites continue to work.
# Later PRs will migrate call sites to use game.assets or injected manager.
# ---------------------------------------------------------------------------


class AssetManager:
    """Central asset loader with caches for images and sounds.

    Usage (preferred going forward):
        assets = AssetManager()
        img = assets.load_image('player.png', (64, 48), draw_player)
        snd = assets.get_sound('shoot', volume=0.6)

    Backwards compatible: the module-level load_image_with_fallback still works.
    """

    def __init__(self):
        self._image_cache = {}
        self._sound_cache = {}
        # Future: theme variants, e.g. self._theme = 'space'

    def load_image(self, filename, size, draw_func=None, *draw_args):
        """Load (or procedurally generate) an image, with caching.

        Mirrors the original load_image_with_fallback behavior exactly for
        compatibility with the many draw_* lambdas in player/enemies/powerups.
        """
        # Simple cache key: filename + size. Procedural results for a given
        # (name, size) are cached after first draw (different draw_funcs for
        # same name are rare in this codebase and the first one wins).
        cache_key = (filename, size[0], size[1])
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        try:
            # Auto-prefer reworked v3 assets if present (e.g. player_v3.png over player.png)
            base, ext = os.path.splitext(filename)
            v3_filename = f"{base}_v3{ext}"
            v3_path = os.path.join('images', v3_filename)
            image_path = os.path.join('images', filename)
            chosen_path = None
            if os.path.exists(v3_path):
                chosen_path = v3_path
            elif os.path.exists(image_path):
                chosen_path = image_path
            if chosen_path:
                image = pygame.image.load(chosen_path).convert_alpha()
                if image.get_size() != size:
                    image = pygame.transform.smoothscale(image, size)
                self._image_cache[cache_key] = image
                return image
            else:
                # Procedural fallback (the important contract we must preserve)
                if draw_func:
                    surface = pygame.Surface(size, pygame.SRCALPHA)
                    draw_func(surface, *draw_args)
                    self._image_cache[cache_key] = surface
                    return surface
                else:
                    surface = pygame.Surface(size)
                    surface.fill((255, 0, 255))  # Magenta = missing asset
                    self._image_cache[cache_key] = surface
                    return surface
        except Exception as e:
            print(f"Error loading image {filename}: {e}")
            surface = pygame.Surface(size)
            surface.fill((255, 0, 255))
            self._image_cache[cache_key] = surface
            return surface

    def get_sound(self, name, volume=None):
        """Load a sound by base name (prefers sounds/{name}.wav, falls back to {name}.wav).

        Returns a pygame.mixer.Sound or None. Results are cached (including
        the None case for missing sounds so we don't spam the console).
        """
        if name in self._sound_cache:
            snd = self._sound_cache[name]
            if snd and volume is not None:
                try:
                    snd.set_volume(volume)
                except Exception:
                    pass
            return snd

        try:
            # Look in sounds/ subdir first (preferred), then fallback to cwd for backward compat
            candidates = [f"sounds/{name}.wav", f"{name}.wav"]
            path = None
            for cand in candidates:
                if os.path.exists(cand):
                    path = cand
                    break
            if path:
                snd = pygame.mixer.Sound(path)
                if volume is not None:
                    snd.set_volume(volume)
                self._sound_cache[name] = snd
                return snd
            else:
                # Missing sounds are common in the current tree; cache the None
                # so we only log once per name.
                print(f"Sound {name} not found (will be silent)")
                self._sound_cache[name] = None
                return None
        except Exception as e:
            print(f"Error loading sound {name}: {e}")
            self._sound_cache[name] = None
            return None

    def get_music(self):
        """Stub for future theme music / playlist support (PR1 + PR12)."""
        return None

    def clear_caches(self):
        """Useful for tests or theme switches."""
        self._image_cache.clear()
        self._sound_cache.clear()


# Default module-level manager so we can start benefiting from caching
# immediately without changing every call site in one PR.
_default_assets = AssetManager()


def get_asset_manager():
    """Return the process-wide default AssetManager."""
    return _default_assets


# Image loading utility with fallback to procedural generation.
# Kept for 100% backwards compatibility during the transition.
# Implementation now delegates to the default manager (so caching applies
# to all existing call sites automatically).
def load_image_with_fallback(filename, size, draw_func=None, *draw_args):
    """Load an image from file, or create it procedurally if file doesn't exist.

    This is now a thin wrapper around the default AssetManager so that
    caching, logging, and future theme support benefit every caller.
    The draw_func(surface, *draw_args) contract is preserved exactly.
    """
    return _default_assets.load_image(filename, size, draw_func, *draw_args)
