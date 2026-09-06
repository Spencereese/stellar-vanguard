# UPGRADE_R13.md - Stellar Vanguard Round 13

Date: 2026-09-06 (America/New_York)
Repo: Spencereese/stellar-vanguard @ PC-Culture
Base: `2a20a8b` (R12 shop featured purchasable deals row)
Trust: VERDICT over SEQUEL_STATUS.md
Version string: **3.10**

## Slice

**Pause menu hub** — mid-run UX beyond Resume/Quit

Chose pause/menu over audio-only, leaderboard tabs, or more Survival/Campaign depth (one focus).
No new art, music assets, enemies, or sequel pillars.
No SEQUEL_STATUS updates. No push.

## What landed

### PauseMenuState hub (`game_states.py`)
- Options expanded to 6: **Resume**, **Music Volume**, **SFX Volume**, **Restart Run**, **Main Menu**, **Quit Desktop**.
- Live volume labels (percent); L/R (and pad hat/axis) adjust by 0.1, clamped 0–1, persisted via settings merge.
- **Resume** sets `preserve_run=True` so PlayingState.enter does not wipe the live run.
- **Restart Run** clears continuing/boss/preserve flags and re-enters Playing (full reset).
- **Main Menu** returns to MenuState; **Quit Desktop** sets `running=False`.
- P/ESC always resume; M main menu; Q quit; pad A select / Start resume / B menu.

### Renderer (`renderer.py`)
- Updated pause hints + tighter option spacing for 6 rows.

### Version bump
- `config.VERSION` / captions / test banners → **3.10**
- R13 asserts in sequel test; R5 pause asserts updated for hub options.

## Verification

```
python -m py_compile game_states.py renderer.py config.py shooter.py test_game.py
$env:SDL_VIDEODRIVER='dummy'; python test_game.py   # expect 6/6
```

## Intentionally NOT done / leftovers

- Leaderboard UX (mode/difficulty tabs / richer entry metadata)
- Further Survival/Campaign depth beyond R10/R11
- Dedicated audio system polish beyond pause volume hub
- Another shop/loadout pass
- No push to remote
- SEQUEL_STATUS.md not updated (overclaims; not trusted)
- No sequel pillars / art / music / new enemy classes

## Files

- `game_states.py`, `renderer.py`
- `config.py`, `shooter.py`, `test_game.py`
- `UPGRADE_R13.md`
