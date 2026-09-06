# UPGRADE_R10.md - Stellar Vanguard Round 10

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `394626a` (R9 loadout polish + Settings joy-hat Window Size)
Trust: UPGRADE_R7-R9 leftovers / VERDICT over SEQUEL_STATUS.md
Version string: **3.7**

## Slice

**Survival depth — threat-tier elite events + composition bias** (prefer leftover Survival/Campaign depth beyond R7/R8).

No new art, music, enemies, or sequel pillars. Pygame only. No full rewrite.
Shop featured polish intentionally deferred. No SEQUEL_STATUS updates.

## What landed

### Threat-tier elite events (`game.py` + `simulation.py` + `renderer.py`)
- On Survival threat-tier up (past CALM), fire a one-shot **ELITE SWARM** event per tier.
- Queues forced elite-pack spawns (existing enemy types only), kill quota, short timer window.
- Clearing the quota grants escalating coin + score juice and a CLEARED banner; timer expiry can partial-clear.
- HUD Survival line shows active event chip (`ELITE SWARM — LABEL k/n`).

### Composition bias (`simulation.py` + `game.py`)
- Ordinary Survival spawns bias toward tougher existing types as threat rises (`survival_composition_bias` / `survival_elite_types`).
- Active events drain `survival_event_spawns` with forced elite picks before normal theme resolution.
- Kill paths (`game` + `simulation`) call `note_survival_kill()` to advance event progress.

### Version bump
- `config.VERSION` / captions / test banners → **3.7**
- R10 asserts in sequel test (elite pools, bias curve, fire-once, clear bonus, forced spawn drain).

## Verification

```
python -m py_compile game.py simulation.py renderer.py config.py shooter.py test_game.py
$env:SDL_VIDEODRIVER='dummy'; python test_game.py   # expect 6/6
```

## Intentionally NOT done / leftovers

- Shop featured UX polish beyond SHOP_FIX (purchasable featured row / deals)
- Further Campaign objective depth (secondary objectives; no_damage recursion edge)
- No push to remote
- SEQUEL_STATUS.md not updated (overclaims; not trusted)
- No sequel pillars / art / music / new enemy classes

## Files

- `game.py`, `simulation.py`, `renderer.py`
- `config.py`, `shooter.py`, `test_game.py`
- `UPGRADE_R10.md`
