# UPGRADE_R9.md - Stellar Vanguard Round 9

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `fcbdaa8` (R8 Survival boss variety)
Trust: UPGRADE_R6–R8 leftovers over SEQUEL_STATUS.md
Version string: **3.6**

## Slice

**Loadout select polish (cards / pad / last-archetype) + Settings joy-hat Window Size fix**

No new art, music, enemies, or sequel pillars. Pygame only. No full rewrite.
Survival ramp/boss variety already landed in R7/R8.

## What landed

### Loadout select polish (`game_states.py` + `renderer.py` + `persistence.py`)
- Archetype **detail cards** from `ARCHETYPES` (name, desc, stats, abilities).
- **Pad support**: D-pad / stick Y nav, A confirm, B/Start back; W/S + SPACE on keyboard.
- **last_archetype** persisted in settings (default scout); enter() restores selection.
- Renderer: list + right-hand detail panel; updated hint line.

### Settings joy-hat Window Size (`game_states.py`)
- JOYHATMOTION L/R and left-stick X on setting index 3 now call `toggle_window_size()` (keyboard already did).
- Closes the R6 leftover where hat L/R stayed volume-only on Window Size.

### Version bump
- `config.VERSION` / test banners → **3.6**
- R9 asserts in sequel test (cards, persist, pad-parity source, toggle smoke).

## Verification

```
python -m py_compile persistence.py game_states.py renderer.py config.py test_game.py
$env:SDL_VIDEODRIVER='dummy'; python test_game.py   # expect 6/6
```

## Intentionally NOT done / leftovers

- Further Survival/Campaign depth beyond R7/R8
- Shop featured UX beyond prior SHOP_FIX
- No push to remote
- SEQUEL_STATUS.md not updated (overclaims; not trusted)
- No sequel pillars / art / music

## Files

- `persistence.py`, `game_states.py`, `renderer.py`
- `config.py`, `test_game.py`
- `UPGRADE_R9.md`
