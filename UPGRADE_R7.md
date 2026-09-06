# UPGRADE_R7.md - Stellar Vanguard Round 7

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `cfaab9c` (R6 optional 1280 window stretch)
Trust: UPGRADE_R6 leftovers over SEQUEL_STATUS.md
Version string: **3.4**

## Slice

**Survival depth — difficulty ramp + mid-run milestones past 60s** (prefer the bigger gameplay leftover).

No new art, music, enemies, or sequel pillars. Pygame only. No full rewrite.
Boss variety / joy-hat Window Size intentionally deferred.

## What landed

### Survival difficulty ramp (`game.py` + `simulation.py` + `enemies.py`)
- Time-based `survival_pressure` from `survival_time` (+0.18/min, soft-capped at 2.5) — replaces wall-clock `pygame.time.get_ticks()` spawn tightening.
- `survival_spawn_interval_frames()`: base 45 frames, -3 per 30s survived, floor 8; easy/hard settings nudge.
- Threat tiers: CALM → RISING → HOSTILE → SEVERE → CRITICAL → …
- Enemy speed/health scale lightly with pressure in Survival; asteroid density tracks pressure.

### Mid-run milestones past 60s (`game.py` + `renderer.py`)
- Shops still every 60s; milestones **after** the first (120/180/…) grant escalating **score bonus** + threat banner callout.
- HUD: `SURVIVE mm:ss  next shop Ns  THREAT xP.PP  best …`

### Version bump
- `config.VERSION` / captions / test banners → **3.4**
- R7 asserts inside sequel test (pressure curve, spawn tighten, 120s enrichment).

## Verification

```
python -m py_compile game.py simulation.py enemies.py renderer.py config.py shooter.py test_game.py
$env:SDL_VIDEODRIVER='dummy'; python test_game.py   # 6/6 tests passed
```

## Intentionally NOT done / leftovers

- Boss variety from existing enemy types in Survival
- Joy-hat LEFT/RIGHT on Window Size still volume-only (keyboard/Enter cover the toggle)
- No push to remote
- SEQUEL_STATUS.md not updated (overclaims; not trusted)
- No sequel pillars / art / music

## Files

- `game.py`, `simulation.py`, `enemies.py`, `renderer.py`
- `config.py`, `shooter.py`, `test_game.py`
- `UPGRADE_R7.md`
