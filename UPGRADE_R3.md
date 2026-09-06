# UPGRADE_R3.md — Stellar Vanguard Round 3

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `585f3ee` (R2 polish)
Trust: VERDICT.md / SHOP_FIX.md / POLISH_R2.md over SEQUEL_STATUS.md

## Slice

**Themed Wave Variety + Boss Phase Depth** (one coherent MAJOR gameplay upgrade).

Not sequel-pillar spam. Reuses existing enemies (including Cloaker/Splitter). No new art/music/modes rewrite.

## What landed

### Wave themes (`wave_themes.py` + `simulation.py` + `game.py`)
- Named compositions: Assault Wing, Swarm Tide, Armor Column, Support Nest, Ghost Ambush (wave≥4), Fracture Protocol (wave≥6), Mixed Patrol.
- Spawn bias ~70% theme pool / 30% legacy `enemy_pools` (+ registry extras).
- Arcade: theme refreshes when score advances the wave.
- Survival: theme refreshes every ~45s (still no bosses — intentional).
- Boss-fight minion spawns bias to theme + phase.
- HUD: compact `W{n} THEME` tag + short centered wave banner.

### Boss depth (`enemies.py` + `renderer.py`)
- Charge has a **wind-up telegraph** (~0.75s sparks) before the rush — not an instant lunge.
- Phase enter FX + `boss_phase_announce_timer` HUD flash.
- Distinct volleys: P1 3-way, P2 denser fan, P3 wide-angle burst.
- Phase 3 special still swarmers/barrage; also pulls **existing** cloaker/splitter via registry when present.
- Boss HP label shows `BOSS P{n}` and `[CHARGING!]` during wind-up.

## Verification

```
python -m py_compile wave_themes.py simulation.py enemies.py game.py renderer.py test_game.py
python test_game.py   # 6/6 tests passed (includes R3 theme + windup asserts inside sequel test)
```

## Intentionally NOT done / leftovers

- Dirty `game.py` **1280 stretch WIP** restored unstaged after commit (not discarded, not part of R3).
- No named leaderboard initials, damage numbers, Survival milestone shop loop.
- No new enemies / pillars / music / art.
- No push to remote.
- SEQUEL_STATUS.md not updated (overclaims; not trusted).
- Not claiming "100% complete" sequel — R3 is one combat-feel upgrade on the solid R1/R2 base.

## Files

- `wave_themes.py` (new)
- `simulation.py`, `enemies.py`, `game.py`, `renderer.py`, `test_game.py`
- `PLAN_R3.md`, `UPGRADE_R3.md`
