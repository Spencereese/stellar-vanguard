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
    "fullscreen": False,  # v3 polish: default windowed (F11 to toggle); no forced fullscreen override
    "window_width": 960,   # R2/R6: windowed size persisted (960 default; 1280 optional stretch)
    "window_height": 720,
    "last_archetype": "scout",  # R9: remember last loadout pick
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
    # R14: entries carry optional mode + difficulty for leaderboard tabs.
    # Pool keeps more than top-10 so per-mode/diff boards stay meaningful.
    HS_POOL_LIMIT = 90
    HS_VIEW_LIMIT = 10
    VALID_HS_MODES = ("arcade", "campaign", "survival")
    VALID_HS_DIFFS = ("easy", "normal", "hard")

    def _normalize_hs_mode(self, mode) -> str:
        m = str(mode or "arcade").strip().lower()
        if m in ("mode_campaign",):
            m = "campaign"
        if m not in self.VALID_HS_MODES:
            m = "arcade"
        return m

    def _normalize_hs_diff(self, difficulty) -> str:
        d = str(difficulty or "normal").strip().lower()
        if d not in self.VALID_HS_DIFFS:
            d = "normal"
        return d

    def _coerce_hs_entry(self, entry) -> dict:
        if isinstance(entry, dict):
            name = str(entry.get("name") or entry.get("initials") or "---")[:3].upper()
            if not name.strip():
                name = "---"
            mode = entry.get("mode")
            diff = entry.get("difficulty")
            # Legacy rows without mode/diff migrate as arcade/normal
            return {
                "name": name,
                "score": int(entry.get("score", 0) or 0),
                "date": entry.get("date") or datetime.now().isoformat(),
                "mode": self._normalize_hs_mode(mode if mode is not None else "arcade"),
                "difficulty": self._normalize_hs_diff(diff if diff is not None else "normal"),
            }
        return {
            "name": "---",
            "score": int(entry),
            "date": datetime.now().isoformat(),
            "mode": "arcade",
            "difficulty": "normal",
        }

    def _load_all_named_highscores(self) -> list:
        """Full pool (unfiltered), newest schema fields included."""
        entries = []
        if os.path.exists(self.highscores_path):
            try:
                with open(self.highscores_path, "r") as f:
                    data = json.load(f) or {}
                for entry in data.get("scores", []):
                    entries.append(self._coerce_hs_entry(entry))
            except Exception:
                entries = []

        if not entries and os.path.exists(self.legacy_highscore_txt):
            try:
                with open(self.legacy_highscore_txt, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            entries.append(self._coerce_hs_entry(int(line)))
            except Exception:
                entries = []

        entries.sort(key=lambda e: int(e.get("score", 0)), reverse=True)
        return entries[: self.HS_POOL_LIMIT]

    def load_highscores(self) -> list:
        """Single source of score ints (compat). Prefer load_named_highscores for UI."""
        return [int(e.get("score", 0)) for e in self.load_named_highscores()] or [0] * 5

    def load_named_highscores(self, mode=None, difficulty=None, limit=None) -> list:
        """Return top entries: {name, score, date, mode, difficulty}.

        R14: optional mode/difficulty filters for leaderboard tabs.
        mode/difficulty None or 'all' => no filter on that axis.
        Default limit is HS_VIEW_LIMIT (10). Pass limit=0 or None for view default;
        use _load_all / large limit when rewriting the pool.
        """
        if limit is None:
            limit = self.HS_VIEW_LIMIT
        entries = self._load_all_named_highscores()
        mode_f = None if mode in (None, "", "all") else self._normalize_hs_mode(mode)
        diff_f = None if difficulty in (None, "", "all") else self._normalize_hs_diff(difficulty)
        if mode_f:
            entries = [e for e in entries if e.get("mode") == mode_f]
        if diff_f:
            entries = [e for e in entries if e.get("difficulty") == diff_f]
        entries.sort(key=lambda e: int(e.get("score", 0)), reverse=True)
        return entries[:limit] if limit else entries

    def save_highscores(self, scores: list):
        """Compat: accept ints or dict entries; preserve names when possible."""
        named = []
        existing = {int(e["score"]): e for e in self._load_all_named_highscores()}
        for s in scores[: self.HS_VIEW_LIMIT]:
            if isinstance(s, dict):
                named.append(self._coerce_hs_entry(s))
            else:
                sc = int(s)
                prev = existing.get(sc)
                if prev:
                    named.append(dict(prev))
                else:
                    named.append(self._coerce_hs_entry(sc))
        self.save_named_highscores(named)

    def save_named_highscores(self, entries: list):
        survival = {}
        if os.path.exists(self.highscores_path):
            try:
                with open(self.highscores_path, "r") as f:
                    prev = json.load(f) or {}
                    survival = prev.get("survival") or {}
            except Exception:
                survival = {}
        cleaned = [self._coerce_hs_entry(e) for e in (entries or [])]
        cleaned.sort(key=lambda x: x["score"], reverse=True)
        cleaned = cleaned[: self.HS_POOL_LIMIT]
        data = {"schema": SCHEMA_VERSION, "scores": cleaned}
        if survival:
            data["survival"] = survival
        self._atomic_write(self.highscores_path, data)
        try:
            with open(self.legacy_highscore_txt, "w") as f:
                # Legacy txt: overall top view scores only
                for e in cleaned[: self.HS_VIEW_LIMIT]:
                    f.write(f"{int(e['score'])}\n")
        except Exception:
            pass

    def qualifies_for_leaderboard(self, score: int, limit: int = 10, mode=None, difficulty=None) -> bool:
        try:
            score = int(score or 0)
        except Exception:
            return False
        if score <= 0:
            return False
        entries = self.load_named_highscores(mode=mode, difficulty=difficulty, limit=limit)
        if len(entries) < limit:
            return True
        return score > min(int(e.get("score", 0) or 0) for e in entries)

    def add_named_highscore(self, name: str, score: int, mode=None, difficulty=None) -> list:
        """Insert named score with mode/difficulty; keep pool. Returns filtered view list.

        Returns top view for the entry's mode+difficulty (R14 tabs), falling back to
        overall top-10 when mode/diff omitted (R5 compat).
        """
        name = (str(name or "AAA")[:3].upper() or "AAA")
        try:
            score = int(score or 0)
        except Exception:
            score = 0
        mode_n = self._normalize_hs_mode(mode if mode is not None else "arcade")
        diff_n = self._normalize_hs_diff(difficulty if difficulty is not None else "normal")
        entries = self._load_all_named_highscores()
        entries.append({
            "name": name,
            "score": score,
            "date": datetime.now().isoformat(),
            "mode": mode_n,
            "difficulty": diff_n,
        })
        entries.sort(key=lambda e: int(e.get("score", 0)), reverse=True)
        entries = entries[: self.HS_POOL_LIMIT]
        self.save_named_highscores(entries)
        # R5 callers expect top board including the new score; return overall top view
        # when called without explicit mode/diff (legacy). With mode/diff, return that tab.
        if mode is None and difficulty is None:
            return self.load_named_highscores()
        return self.load_named_highscores(mode=mode_n, difficulty=diff_n)
    # ---------------- Survival bests (R4) ----------------
    def load_survival_best(self) -> dict:
        """Return {best_time: float seconds, best_score: int}. Defaults to zeros."""
        best = {"best_time": 0.0, "best_score": 0}
        if not os.path.exists(self.highscores_path):
            return best
        try:
            with open(self.highscores_path, "r") as f:
                data = json.load(f) or {}
            surv = data.get("survival") or {}
            best["best_time"] = float(surv.get("best_time", 0) or 0)
            best["best_score"] = int(surv.get("best_score", 0) or 0)
        except Exception:
            pass
        return best

    def record_survival_run(self, score: int, time_s: float) -> dict:
        """Update persisted Survival bests if this run improves either. Returns new bests."""
        best = self.load_survival_best()
        changed = False
        try:
            score = int(score or 0)
            time_s = float(time_s or 0)
        except Exception:
            return best
        if score > best.get("best_score", 0):
            best["best_score"] = score
            changed = True
        if time_s > best.get("best_time", 0):
            best["best_time"] = time_s
            changed = True
        if not changed:
            return best
        # Merge into highscores.json without dropping arcade scores
        scores_payload = []
        if os.path.exists(self.highscores_path):
            try:
                with open(self.highscores_path, "r") as f:
                    prev = json.load(f) or {}
                for entry in prev.get("scores", []):
                    if isinstance(entry, dict):
                        scores_payload.append(entry)
                    else:
                        scores_payload.append({"score": int(entry), "date": datetime.now().isoformat()})
            except Exception:
                scores_payload = []
        if not scores_payload:
            for e in self.load_named_highscores():
                scores_payload.append({
                    "name": e.get("name", "---"),
                    "score": int(e.get("score", 0) or 0),
                    "date": e.get("date") or datetime.now().isoformat(),
                })
        data = {
            "schema": SCHEMA_VERSION,
            "scores": scores_payload[:10],
            "survival": {
                "best_time": float(best.get("best_time", 0) or 0),
                "best_score": int(best.get("best_score", 0) or 0),
                "updated": datetime.now().isoformat(),
            },
        }
        self._atomic_write(self.highscores_path, data)
        return best

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
        # Merge with on-disk settings first so partial updates (e.g. GameOver volumes)
        # cannot wipe F11 fullscreen / window size.
        existing = {}
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    existing = json.load(f) or {}
            except Exception:
                existing = {}
        data = {**DEFAULT_SETTINGS, **existing, **settings}
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
