# PLAN_R4.md — Stellar Vanguard Round 4

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `c17e066` (R3 themed waves + boss depth)
Trust: VERDICT.md / SHOP_FIX.md / POLISH_R2.md / UPGRADE_R3.md over SEQUEL_STATUS.md

## Chosen slice (ONE coherent HEAVY gameplay upgrade)

**Survival Milestone Shop + Scoring Persist** — reuse existing ShopState claim-1 UX; deepen Survival mode.

Why this (prefer gameplay depth over cosmetics):
- Damage numbers / pause a11y are polish; named leaderboard is meta UX.
- Survival already has themed waves (R3) but no mid-run progression loop and no persisted bests — thin vs Arcade/Campaign shop cadence.
- Highest leverage: every ~60s Survival pause opens the proven post-boss shop (3+skip, rarity, rerolls) without new art/music/pillars.

## In scope

1. Track `survival_time` while `survival` is True; milestones at 60/120/180/240/300s…
2. On milestone: coin stipend + `just_survival_milestone` → ShopState (same claim-1 path as post-boss).
3. `preserve_run` so PlayingState.enter does not `reset_game()` when returning from Survival shop.
4. Persist Survival best time + best score via persistence facade; GameOver records them; HUD + game-over show them.
5. Keep pygame; tests stay **6/6**; bump visible version to **3.1**.

## Out of scope / deferred

- Damage floating numbers, named leaderboard initials, pause a11y deep pass
- New enemies / pillars / music / art / full rewrite
- Dirty `game.py` **1280 stretch WIP** (stashed; restore unstaged after commit)
- Push to remote; SEQUEL_STATUS.md updates

## Honest completion bar

Not "100% complete sequel". R4 delivers one Survival depth loop with py_compile + 6/6 tests and honest UPGRADE_R4.md.
