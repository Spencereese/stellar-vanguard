"""Persistence facade for Stellar Vanguard v3.0 (PR3).

Evolvable single source for saves, highscores, upgrades, settings.
Today: versioned JSON (backwards compatible with v2 upgrades.json + highscore.txt).
Future: per user decision, clear extension points for compressed or binary formats
without changing call sites in Game / states / launcher.

See DESIGN_STELLAR_VANGUARD_v3.md PR3 + Data Model + user decisions.

Creative: clean API, automatic migrations with backups, easy settings, debug info.
"""

import json
import os
import shutil
from datetime import datetime

# Current schema
SCHEMA_VERSION = 2

DEFAULT_SETTINGS = {
    "music_volume": 0.5,
    "sfx_volume": 0.5,
    "difficulty": "normal",
    "colorblind_mode": None,  # None, "desat", etc.
    "enable_experimental_mp": False,
    "mouse_aim": False,
}


class Persistence:
    """The evolvable save manager."""

    def __init__(self, base_dir=None):
        self.base_dir = base_dir or "."
        self.upgrades_path = os.path.join(self.base_dir, "upgrades.json")
        self.highscores_path = os.path.join(self.base_dir, "highscores.json")  # preferred new
        self.legacy_highscore_txt = os.path.join(self.base_dir, "highscore.txt")
        self.settings_path = os.path.join(self.base_dir, "settings.json")

    # ---------------- Upgrades (extend existing v2 logic) ----------------
    def load_upgrades(self):
        """Load with full backward compat to the current upgrades.py format.
        Extends the exact 'if levels in data' logic from upgrades.py.
        """
        if not os.path.exists(self.upgrades_path):
            return None
        try:
            with open(self.upgrades_path, "r") as f:
                data = json.load(f)
            # The existing upgrades.py already does the heavy lifting; we just provide the data
            # and can wrap for schema.
            if isinstance(data, dict) and "schema" not in data:
                data["schema"] = 1  # mark what we saw
            return data
        except Exception as e:
            print(f"[persistence] upgrades load error: {e}")
            return None

    def save_upgrades(self, values: dict, levels: dict, schema: int = SCHEMA_VERSION):
        data = {"schema": schema, "values": values, "levels": levels}
        self._atomic_write(self.upgrades_path, data)
        # Also keep a backup on major schema bumps (simple)
        if schema > 1:
            backup = self.upgrades_path + f".bak.{datetime.now().strftime('%Y%m%d')}"
            if not os.path.exists(backup):
                shutil.copy2(self.upgrades_path, backup)

    # ---------------- Highscores (deduped) ----------------
    def load_highscores(self) -> list:
        """Single source. Tries new json, falls back to legacy txt, migrates on save."""
        scores = []
        # New json first
        if os.path.exists(self.highscores_path):
            try:
                with open(self.highscores_path, "r") as f:
                    data = json.load(f)
                    for entry in data.get("scores", []):
                        if isinstance(entry, dict):
                            scores.append(int(entry.get("score", 0)))
                        else:
                            scores.append(int(entry))
                return sorted(scores, reverse=True)[:10]
            except Exception:
                pass

        # Legacy txt (from v1/v2)
        if os.path.exists(self.legacy_highscore_txt):
            try:
                with open(self.legacy_highscore_txt, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            scores.append(int(line))
                # On load of legacy we can migrate on next save
                return sorted(scores, reverse=True)[:10]
            except Exception:
                pass

        return [0] * 5   # original default behavior

    def save_highscores(self, scores: list):
        data = {
            "schema": SCHEMA_VERSION,
            "scores": [{"score": int(s), "date": datetime.now().isoformat()} for s in scores[:10]]
        }
        self._atomic_write(self.highscores_path, data)

        # Optional: also update legacy txt for very old tools
        try:
            with open(self.legacy_highscore_txt, "w") as f:
                for s in scores[:10]:
                    f.write(f"{int(s)}\n")
        except Exception:
            pass

    # ---------------- Settings ----------------
    def load_settings(self) -> dict:
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    s = json.load(f)
                    # merge defaults for new keys
                    merged = DEFAULT_SETTINGS.copy()
                    merged.update(s)
                    return merged
            except Exception:
                pass
        return DEFAULT_SETTINGS.copy()

    def save_settings(self, settings: dict):
        data = {**DEFAULT_SETTINGS, **settings}
        data["schema"] = SCHEMA_VERSION
        self._atomic_write(self.settings_path, data)

    # ---------------- Profile (future combined) ----------------
    def load_profile(self):
        """One call for most things. Creative: returns a dict the Game can consume."""
        return {
            "upgrades": self.load_upgrades(),
            "highscores": self.load_highscores(),
            "settings": self.load_settings(),
        }

    def save_profile(self, *, upgrades=None, highscores=None, settings=None):
        if upgrades:
            self.save_upgrades(**upgrades)
        if highscores:
            self.save_highscores(highscores)
        if settings:
            self.save_settings(settings)

    # ---------------- Internals ----------------
    def _atomic_write(self, path: str, data: dict):
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)

    def migrate_if_needed(self):
        """Run once at startup. Creates highscores.json from legacy if missing."""
        if not os.path.exists(self.highscores_path) and os.path.exists(self.legacy_highscore_txt):
            scores = self.load_highscores()
            self.save_highscores(scores)
            print("[persistence] Migrated legacy highscores to highscores.json")


# Convenience global for easy use during transition
_default_persistence = Persistence()


def get_persistence():
    return _default_persistence
