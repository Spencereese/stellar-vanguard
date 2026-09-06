# SHOP_FIX.md — VERDICT §7 shop blockers

Date: 2026-09-05 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Trust: VERDICT.md (SEQUEL_STATUS.md overclaims 100% complete)

## Before (VERDICT.md FAIL)

1. Non-post ShopState.enter() AttributeError on skip_bonus — main shop from menu/death crashed.
2. Main shop K_r featured reroll unreachable (elif swallowed by non-post Q/E branch).
3. Post-boss diversity: weapons bucket filled all 3 slots (no per-bucket break).
4. Post-boss buy failed at test coins=300 (3x discounted weapons >=600).
5. Paid reroll after free was dead; footer still advertised R when rem==0 / after claim.
6. Claimed-card dim used selected index, not the claimed item name.
7. test_game.py 5/6 (post-boss shop block AssertionError on has_claimed_reward).

## After (this phase)

| # | Status | Notes |
|---|--------|-------|
| 1 | Already fixed in tree + re-verified | enter() always sets skip_bonus=50 before generate. Main shop opens. |
| 2 | Already fixed in tree + re-verified | K_r is a top-level if; main shop 150 featured reroll works; post-boss R still works. |
| 3 | Already fixed in tree + re-verified | One item per bucket then fill. Test printed `{weapons, upgrades, special}`. |
| 4 | Already fixed in tree + re-verified | Test coins=1200; diversity includes an upgrade; claim-1 + skip +50 hold. |
| 5 | Fixed this session | Paid 50 after free still works. After claim, R is locked (no regen). Footer: free N left / paid 50 / claimed. No lying "0 left" as a dead action. |
| 6 | Fixed this session | `claimed_item_name` set on KEY+JOY claim. renderer dims non-skip cards by name, not selected index. |
| 7 | Green | `python test_game.py` → **6/6** including full post-boss shop block. No workaround enters. |

## Files changed (this commit)

- `game_states.py` — claimed_item_name init + set on claim; post-boss R locked after claim; free-then-paid-50 kept.
- `renderer.py` — claimed dim by claimed_item_name; honest post-boss footer.
- `SHOP_FIX.md` — this note.

`renderer.py` working tree already had a pre-existing stretch-to-fill (letterbox removal) from before this ownership. That display WIP is still present in the file; it is **not** a VERDICT §7 shop fix. `game.py` 1280-wide default remains **unstaged**.

## Test results

```
python -m py_compile game_states.py renderer.py   # OK
python test_game.py                               # 6/6 tests passed
```

Post-boss block: Victory option, 4 offers + skip, rarities assigned, synergy bias, diversity 3 buckets, claim-1 lock, skip +50.

## Not done (intentionally deferred)

- No new sequel pillars / enemies / music / generated art.
- No from-scratch rewrite of renderer.py or game.py.
- Polish pass (loadout persist / E-R-Q harden / 960+F11) completed in **POLISH_R2.md** (Round 2).
- Dirty game.py 1280 stretch WIP remains unstaged (stashed around R2 commit, then restored).
- SEQUEL_STATUS.md not appended.
- Phaser Idle Quest not started.

