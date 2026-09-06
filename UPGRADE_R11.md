# UPGRADE_R11.md - Stellar Vanguard Round 11

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `a3ec0d0` (R10 Survival threat-tier elite events + composition bias)
Trust: UPGRADE_R10 leftovers / VERDICT over SEQUEL_STATUS.md
Version string: **3.8**

## Slice

**Campaign objective depth — secondary objectives + `no_damage` recursion fix**

Chose Campaign over shop featured polish (one focus). No new art, music, enemies, or sequel pillars.
No SEQUEL_STATUS updates. No push.

## What landed

### `no_damage` primary recursion fix (`level_manager.py`)
- Prior `is_level_complete()` for `no_damage` called itself (`... and self.is_level_complete()`), infinite recursion.
- Now: damage==0 AND hostile/boss clear (same clear rules as kill_enemies / boss), without re-entry.

### Secondary objectives (`level_manager.py` + `renderer.py`)
- From level 3+, levels may attach an optional **secondary** (bonus reward, not required to clear).
- Types: `no_damage`, `collect_powerups`, `survive_time`, `extra_kills`, `style_rank` (avoids duplicating primary except extra_kills).
- `is_secondary_complete()` + reward multiply via `bonus_mult` when satisfied.
- `get_mission_data()` exposes structured `secondary`; expanded mission panel draws SECONDARY [BONUS/COMPLETE] bar.

### Version bump
- `config.VERSION` / captions / test banners → **3.8**
- R11 asserts in sequel test (secondary attach, no_damage non-recursive, reward bump, mission data).

## Verification

```
python -m py_compile level_manager.py renderer.py config.py shooter.py test_game.py
$env:SDL_VIDEODRIVER='dummy'; python test_game.py   # expect 6/6
```

## Intentionally NOT done / leftovers

- Shop featured UX polish beyond SHOP_FIX (purchasable featured row / deals)
- No push to remote
- SEQUEL_STATUS.md not updated (overclaims; not trusted)
- No sequel pillars / art / music / new enemy classes

## Files

- `level_manager.py`, `renderer.py`
- `config.py`, `shooter.py`, `test_game.py`
- `UPGRADE_R11.md`
