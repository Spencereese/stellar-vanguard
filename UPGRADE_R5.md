# UPGRADE_R5.md - Stellar Vanguard Round 5

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `9d8ea26` (R4 Survival shop)
Trust: VERDICT.md / UPGRADE_R4 leftovers over SEQUEL_STATUS.md
Version string: **3.2**

## Slice

**Combat feedback + pause a11y + named high-score leaderboard** (one HEAVY polish/UX pass combining all three R4 leftovers).

No new art, music, enemies, or sequel pillars. Pygame only. No full rewrite.

## What landed

### Floating damage numbers (`game.py` + `simulation.py` + `projectiles.py` + `renderer.py`)
- `Game.spawn_damage_number` / `update_damage_numbers` with TTL, drift, crit gold tint.
- Simulation hit sites + key projectile paths emit floaters via `_spawn_hit_number` / direct spawn.
- Drawn above HUD in playing virtual render.

### Pause accessibility (`game_states.py` + `renderer.py`)
- PauseMenu options: Resume / Quit with arrow/WASD + pad hat/axis nav.
- Resume keys match UI: **P / ESC / R / N / Enter / Space / Start**.
- Quit: **Q / B**.
- Dim overlay over gameplay underlay; on-screen hints for keyboard + pad.
- Fixes prior mismatch ("Press P to Resume" while only R/N worked).

### Named high-score leaderboard (`persistence.py` + `game_states.py` + `renderer.py`)
- `load_named_highscores` / `save_named_highscores` / `add_named_highscore` / `qualifies_for_leaderboard`.
- Backward compatible with bare int scores (name `---`).
- `NameEntryState`: 3 initials, arrows/WASD/type, Enter confirm, Esc=AAA.
- GameOver routes to name entry when score qualifies; Survival bests still recorded.
- Leaderboard UI shows `rank. NAME  score`.

## Verification

```
python -m py_compile persistence.py game.py game_states.py renderer.py simulation.py projectiles.py config.py shooter.py test_game.py
python test_game.py   # 6/6 tests passed (R5 asserts inside sequel test)
```

## Intentionally NOT done / leftovers

- Dirty `game.py` **1280 stretch WIP** restored unstaged after commit (not discarded).
- No push to remote.
- SEQUEL_STATUS.md not updated (overclaims; not trusted).
- No sequel pillars / art / music.

## Files

- `persistence.py`, `game.py`, `game_states.py`, `renderer.py`, `simulation.py`, `projectiles.py`
- `config.py`, `shooter.py`, `test_game.py`
- `PLAN_R5.md`, `UPGRADE_R5.md`
