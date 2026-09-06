# PLAN_R3.md — Stellar Vanguard Round 3

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `585f3ee` (R2 polish, tests 6/6)
Trust: VERDICT.md / SHOP_FIX.md / POLISH_R2.md over SEQUEL_STATUS.md

## Chosen slice (ONE coherent MAJOR gameplay upgrade)

**Themed Wave Variety + Boss Phase Depth** — reuse existing enemies; no new sequel pillars.

Why this (not the other examples):
- Pause already works; highscores already persist as numbers; Survival exists but is thin.
- Random `enemy_pools` rolls make waves feel identical; boss already has 3 phases but telegraphs/patterns are shallow.
- Highest leverage: make *existing* content read as distinct encounters without inventing new systems spam.

## In scope

1. **Wave themes** (Arcade + Survival + boss-minion spawns): named compositions (Assault, Swarm, Armor, Support, Ghost Ambush, Fracture, Mixed) biasing spawn pools toward existing types including Cloaker/Splitter when unlocked by wave.
2. **Wave banner HUD**: short on-screen announce when wave/theme changes.
3. **Boss depth**: charge wind-up telegraph before rush; clearer phase enter FX; phase-specific shot patterns; Phase 3 minions include cloaker/splitter when available; boss HP bar shows phase.
4. Keep pygame; no rewrite; tests stay **6/6**.

## Out of scope / deferred

- New enemies, music, art, sequel pillars
- Survival milestone shop loop (future)
- Named leaderboard initials (future)
- Damage-number accessibility (future)
- Dirty `game.py` 1280 stretch WIP (stashed; restore unstaged after commit)
- Push to remote

## Honest completion bar

Not "100% complete sequel". R3 delivers one playable combat-feel upgrade with py_compile + 6/6 tests and an honest UPGRADE_R3.md.
