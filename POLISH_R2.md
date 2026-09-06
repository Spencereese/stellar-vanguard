# POLISH_R2.md ? Stellar Vanguard Round 2 polish

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `06051f5` (shop blockers green, tests 6/6)
Trust: VERDICT.md / SHOP_FIX.md over SEQUEL_STATUS.md

## Mission (one coherent slice from SHOP_FIX deferred set)

1. Loadout select from mode menu must persist into PlayingState
2. E/R/Q abilities must not crash if particles/sounds missing
3. Windowed 960x720 + F11 fullscreen persist via persistence.py

## What polished

### Loadout persist
- `LoadoutSelectState._apply_selected` stores `session.current_loadout` + `selected_archetype` before entering Playing.
- `PlayingState.enter` re-applies session loadout after `reset_game()`.
- `Loadout.apply_to_player(..., game=)` uses **absolute** bases (`game.player_speed` / `game.max_health`) ? no multiply-on-multiply stacking.
- `SimulationWorld.set_player` prefers existing session loadout over default scout.
- `_apply_loadout_and_modifiers` actually re-applies (was a no-op).
- `Game.apply_difficulty` re-applies selected loadout after writing upgrade bases (fixes init wipe).

### E/R/Q missing-asset hardening
- `activate_ability` wraps FX in `_safe_ability_fx` / `_safe_play_sfx` (None particles, missing Particle, missing sounds ? silent, no raise).
- PlayingState E/R/Q handlers call `activate_ability` inside try/except; duplicate particle loops removed (FX lives in loadouts).

### Windowed 960x720 + F11 persist
- Default windowed remains **960x720**; settings keys `window_width` / `window_height` added.
- `toggle_fullscreen` persists `fullscreen` + window size via persistence.
- `Persistence.save_settings` **merges with on-disk** settings so partial saves (e.g. GameOver volumes) cannot wipe F11 fullscreen.
- GameOver settings save now merges and includes `fullscreen`.

## Deferred / left alone

- Dirty `game.py` **1280 stretch WIP** was stashed before this slice and restored after commit (uncommitted). Not discarded. Not part of this commit.
- No sequel pillars, new enemies, music, or art.
- No from-scratch rewrite of renderer.py / game.py.
- SEQUEL_STATUS.md not appended.
- Phaser Idle Quest not started.

## Files touched

- `loadouts.py` ? absolute apply + safe ability FX
- `simulation.py` ? preserve/re-apply loadout on reset
- `game_states.py` ? LoadoutSelect persist, Playing re-apply, E/R/Q harden, GameOver settings merge
- `game.py` ? apply_difficulty re-apply; window size from settings; F11 persist window_*
- `persistence.py` ? window_* defaults; merge-on-save
- `POLISH_R2.md` ? this note

## Tests

```
python -m py_compile loadouts.py simulation.py game_states.py game.py persistence.py
python test_game.py   # 6/6 tests passed
```

Manual: LoadoutSelect tank ? Playing keeps tank + 1.4x health; emp/repair with `particles=None` no crash; save_settings partial update preserves fullscreen=True.
