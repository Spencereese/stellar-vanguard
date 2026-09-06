# UPGRADE_R4.md — Stellar Vanguard Round 4

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `c17e066` (R3 themed waves + boss depth)
Trust: VERDICT.md / SHOP_FIX.md / POLISH_R2.md / UPGRADE_R3.md over SEQUEL_STATUS.md
Version string: **3.1**

## Slice

**Survival Milestone Shop + Scoring Persist** (one coherent HEAVY gameplay upgrade).

Reuses existing ShopState claim-1 / rarity / skip / reroll UX. No new art, music, enemies, or sequel pillars.

## What landed

### Survival mid-run shop (`game.py` + `game_states.py` + `renderer.py`)
- Real `survival_time` clock while `survival` is True (was only advancing under Campaign mission tracking before).
- Milestones every **60s** (60/120/180/…): coin stipend + `just_survival_milestone` opens ShopState.
- Shop path identical to post-boss (3 curated + SKIP, free rerolls by rank, claim-exactly-1).
- `preserve_run` so `PlayingState.enter` does **not** `reset_game()` when returning from a Survival shop (ESC / SKIP / Start).
- HUD: survive timer, next shop countdown, best time; shop title "SURVIVAL MILESTONE"; game-over Survival line.

### Scoring persist (`persistence.py` + GameOver)
- `load_survival_best()` / `record_survival_run(score, time_s)` stored under `highscores.json` → `"survival"`.
- Arcade/campaign score list preserved when writing Survival bests (and vice versa via `save_highscores` merge).
- GameOver in Survival mode records best time + best score.

## Verification

```
python -m py_compile persistence.py game.py game_states.py renderer.py config.py shooter.py test_game.py
python test_game.py   # 6/6 tests passed (R4 asserts inside sequel test)
```

## Intentionally NOT done / leftovers

- Dirty `game.py` **1280 stretch WIP** stashed then restored unstaged after commit (not discarded, not part of R4).
- Damage floating numbers / pause accessibility deep pass.
- Named leaderboard initials.
- No new enemies / pillars / music / art / full rewrite.
- No push to remote.
- SEQUEL_STATUS.md not updated (overclaims; not trusted).

## Files

- `persistence.py`, `game.py`, `game_states.py`, `renderer.py`, `config.py`, `shooter.py`, `test_game.py`
- `PLAN_R4.md`, `UPGRADE_R4.md`
