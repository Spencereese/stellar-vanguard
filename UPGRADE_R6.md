# UPGRADE_R6.md - Stellar Vanguard Round 6

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `d77ccd5` (R5 damage numbers / pause a11y / named leaderboard)
Trust: UPGRADE_R5 leftovers over SEQUEL_STATUS.md
Version string: **3.3**

## Slice

**Finish 1280 stretch as optional Settings toggle (960 default)** — land the dirty `game.py` WIP as a persisted, reversible window-size option without breaking the 6/6 suite.

No new art, music, enemies, or sequel pillars. Pygame only. No full rewrite.
Survival ramp / boss variety intentionally deferred.

## What landed

### Optional window stretch (`persistence.py` + `game.py` + `game_states.py` + `renderer.py`)
- Defaults remain **960x720** (`DEFAULT_SETTINGS.window_width/height`).
- Settings menu gains **Window Size** (index 3): cycles **960x720 (default)** ↔ **1280x720 (native)** matching the renderer virtual base.
- `Game.toggle_window_size` + `_normalized_window_size` + `_recreate_display` apply live when windowed; F11 fullscreen restores the chosen windowed size (no longer hard-resets to 960 only).
- Keyboard: Enter / Left / Right on Window Size; pad A same as Enter.
- Dirty hardcoded-1280 WIP replaced by persisted toggle (960 default).

### Version bump
- `config.VERSION` / captions / test banners → **3.3**
- Sequel test asserts + dedicated R6 window toggle checks (isolated temp persistence).

## Verification

```
python -m py_compile persistence.py game.py game_states.py renderer.py config.py shooter.py test_game.py
python test_game.py   # 6/6 tests passed
```

## Intentionally NOT done / leftovers

- Survival difficulty ramp + mid-run milestones beyond 60s shops
- Boss variety from existing enemy types in Survival
- No push to remote
- SEQUEL_STATUS.md not updated (overclaims; not trusted)
- No sequel pillars / art / music
- Joy-hat LEFT/RIGHT on Window Size still volume-only (keyboard/Enter cover the toggle)

## Files

- `persistence.py`, `game.py`, `game_states.py`, `renderer.py`
- `config.py`, `shooter.py`, `test_game.py`
- `UPGRADE_R6.md`
