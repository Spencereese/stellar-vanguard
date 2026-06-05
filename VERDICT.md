# Shop Rework Verifier VERDICT (headless code review agent)

**Date**: 2026-06-02 (PT)
**Subagent**: headless-shop-verifier (focused on game_states.py / renderer.py / game.py / test_game.py recent changes)
**Workspace**: /Users/spencereese/projects/shooter.py

## VERDICT: FAIL (with PARTIAL post-boss functionality; main shop regressed + test breakage)

Not all key paths + asserts green in unmodified code. Post-boss UX/logic mostly matches research intent *when coins sufficient and diversity luck*, but blockers prevent full "best modern roguelite" (Hades 3+rarity+synergy+limited reroll, StS skip, Isaac curation+diversity, generous post-boss, no main shop regression).

### 1. Code review (key sections read via tools)
- **game_states.py: ShopState**:
  - `__init__`: minimal (last_nav, purchase_message). enter() sets is_post_boss from game.just_defeated_boss (consumes flag), free_rerolls (rank dep: S/A/B=2, else=1), rerolls_remaining, has_claimed=False, skip_bonus=50, post_boss_items=_generate(3), category_items=..., categories=["boss rewards"].
  - `_generate_post_boss_choices(n=3)`: pools upgrades/weapons/special, buckets for diversity, prioritize loop (flawed), fill, ALWAYS appends explicit SKIP (cost=0, effect +skip_bonus, post_boss=True, common). Applies discount 25% (min50) to non-dyn, sets post_boss, calls _assign for rarity+synergy+display_desc. Docstring claims "Diversity guarantee", "Hades 3-boon + StS skip".
  - `_assign_rarity_and_synergy`: weights by rank (S/A better [30,35,25,10], B med, base [55,30,12,3]), sets rarity/rarity_note. Synergy heuristics (flame/fire/gunner/tank/scout + mods glass/resource). Mutates item desc with tag. Dynamic preview + [EPIC+]. Good for Isaac bias.
  - `_get_rarity_colors`: implemented (GOLD/PURPLE/CYAN/SILVER) but **dead/unused** (renderer duplicates).
  - `handle_event`:
    - ESC: post -> PlayingState (always, even mid/after claim); non -> GameOver.
    - Post K_r: free only (rem>0 ? cost=0 : no), regen items, rem-=1, msg. (paid cost calc unreachable).
    - Non-post K_r: **unreachable** (see below).
    - Arrow/WASD/ Dpad / joyaxis: grid nav (3-col, clamp).
    - RETURN / JOY A: cost check (dyn via upgrades.get or item), deduct, effect(), if skip: +msg + change Playing return; else msg, if post: has_claimed=True, rerolls=0, filter category_items to [chosen_name or skip], selected clamp, if epic/leg dyn: extra effect() + bonus msg.
    - Post-claim RETURN on non-skip: "Reward claimed — ESC..." msg (no buy).
    - After claim, skip still buyable (goes to Playing +50).
    - Cat tabs/ q/e / shoulders only for !post.
  - Dupe logic for KEY vs JOY paths.
  - `draw`: delegates to renderer.draw_shop.
- **renderer.py: draw_shop**:
  - Post title "BOSS DEFEATED — CLAIM YOUR REWARD" + sub (Hades-style); non "🛒 UPGRADE SHOP".
  - Coins always.
  - Non-post: 5 tabs (ALL etc), featured line (names + rarity badges from state.featured), start_y adjust +40.
  - Post: larger cards (220x110), start_y=145 for title.
  - Card loop: is_post/has_claimed/skip/rarity setup (hardcoded ternary for border/badge/glow, duplicate of state's _get), special_offer glow, post bg tint by rarity (skip neutral), afford tint, **claimed dim** (if has and not (selected.name or skip): dim color).
  - Rarity glow/frame if post/special non-common; selected glow (rarity tint for post).
  - Icon, badge (if !=common or post), synergy tag if, name (afford color), desc (prefer display_desc), cost (skip special +50 or ESC; dyn live).
  - Footer purchase msg (in virtual + direct post-blit, WHITE vs GREEN/RED).
  - Nav: post claimed vs active (R rerolls left + SKIP/ESC); non: Q/E + R150 + ...
  - Uses config* (GOLD, RED, CYAN, SCREEN_* etc). from config import * at top.
- **game.py**:
  - Rank bonus on boss: if level_manager boss_required: just_defeated_boss=True; rank_bonus={'S':180,'A':120,'B':80,'C':50,'D':30}; coins += int(bonus * coin_mult); score += ...
  - just_defeated init/reset False.
  - Shop items defined (consumables cheap, weapons 800+, dyn upgrades/special via buy_* + cost_key).
  - from config import *; from game_states import *; from renderer import Renderer. (forward refs in methods ok at runtime).
- **test_game.py**:
  - New block in test_sequel_features (after data-shop ✓): g2 S-rank flamethrower+loadout+just_defeated+coins=300; Victory enter+assert option; Shop enter+assert is_post/has_claimed=False/rerolls>=1/len>=4/skip/rarities valid; print rarities/free; has_syn print; cats print; buy non-skip + assert claimed + len non-skip<=1; rerolls==0; g3 fresh skip+50 assert; print "✓ Full post-boss modern shop logic+UX (rarity, synergy curation, free reroll S-rank, diversity, skip agency, claim-1, dynamic preview, Victory flow)".
  - But uses coins=300 (insufficient for current weapon costs).
- **Imports/forward/syntax**: game_states uses explicit colors (all needed for rarity: GOLD/PURPLE/CYAN/SILVER present; no RED needed here); renderer config*; game_states/game/shooter use * or listed. Forward (PlayingState etc refs in Shop methods) runtime-ok (full module load before use). No syntax.
- Confirmed via read_file/grep on exact lines/sections (e.g. 881-1480 game_states, 850-1110 renderer, 508-513 game, 272-330 test_game).

### 2. Static checks
- `cd ... && python3 -m py_compile game_states.py renderer.py game.py test_game.py shooter.py` → **PY_COMPILE: PASS** (exit 0, no errors/lines reported). Repeated post-debug.

### 3. Headless functional tests (pygame mocked + dummy driver; targeted -c following test patterns + user sketch)
- Multiple runs (with high coins=2000 to reach buy, pre-set skip_bonus=0 before non-post enter to reach smoke, avoided broken K_r main):
  - Post: Victory option ✓, enter is_post/!claimed/rerolls=2 (S), 4+ items+skip ✓, rarities assigned (common/rare/epic/legendary in runs) ✓, synergy bias=True (flamethrower/gunner) ✓, buy RETURN: has_claimed=True, rerolls=0, <=1 non-skip + skip remain ✓, effect applied (weapon change) ✓, post-claim RETURN msgs "claimed" no re-buy ✓, ESC after claim: change_state(PlayingState) ✓.
  - Fresh skip: +50, proceeds ✓.
  - Non-post (w/ pre-set): enter !is_post, featured>=3 (note: generate always produces 4 incl hidden skip), tabs incl "all" ✓; grid nav (arrows/WASD) no crash ✓; buy path exercised ✓.
  - Other: post K_r free decrement ✓ (when >0), 0 left "No rerolls" ✓; main enter/nav/buy smoke ✓ (w/ workaround).
  - Renderer smoke: draw_shop called on post-claimed + main states (no logic except in draw; expected image errs tolerated).
  - Full user-specified -c style run: produced the ✓ for Victory/4+/rarities/synergy/buy/claimed/locked/rerolls0/skip+50/non-post featured/tabs/nav; ended "ALL PASS (with workaround...)" + exit 0.
- Without workarounds: non-post enter raises AttributeError on skip_bonus (see below); buy fails with 300 coins (see test).
- Image errs ("No video mode... player.png" etc) pre-existing in headless (tolerated in other tests like test_headless_verifier).

### 4. Project test run
- `cd ... && python3 test_game.py 2>&1 | tail -30`: ends with "VERDICT: PASS" (for its internal headless verifier) + "Test Results: 5/6 tests passed ❌ Some tests failed."
- Specific: `grep ...` shows:
  - "✓ VictoryState post-boss inserts 'Claim Post-Boss Reward' option"
  - "✓ ShopState post-boss: 4 offers (incl skip), rarities={'rare'}, free_rerolls=2"
  - "✓ Diversity buckets in offers: {'weapons'}"
  - Then **AssertionError at test_game.py:314 `assert getattr(s, 'has_claimed_reward', False)`** (the buy one, due to coins=300).
  - **NO "✓ Full post-boss modern shop"** (print is after the failing assert + skip sim).
  - Numpy warning (renderer surfarray optional, pre-existing).
- Thus, the "new post-boss shop exercise block" fails.

### 5. Smoke other flows
- Non-boss Shop enter: crashes (see blockers).
- Post-boss paths (high coins): all green as above (rarity/syn/claim1/skip/ESC->Playing/reroll free/rank S=2).
- Main shop (w/ attr pre-set to bypass generate crash): featured/tabs/nav/buy exercised, no grid crash. (Reroll not, see below.)
- Victory/Playing transitions, flag consume, etc ok in post.
- No full regression smoke possible due to enter crash for normal shop.

### 6. Specific assertions for "best UX" (from research)
- Post-boss: rarity in set ✓ (assigned), skip present ✓, free_rerolls rank-dep (S=2=1+1) ✓, has_claimed after buy ✓.
- After claim: rerolls=0 ✓, category_items has chosen + skip ✓.
- ESC/RETURN after claim goes to Playing (in code path) ✓ (ESC direct; RETURN on skip does; non-skip msgs).
- Diversity: not all same cat? **NO** (always {'weapons'} in runs; see blockers).
- Renderer: rarity branch (ternary+bg/glow/badge) ✓, badge blit ✓, synergy if ✓, skip cost special ✓, claimed dim logic ✓ (but flawed).
- Rank bonus in game.py present ✓ (lines ~510-512).
- Meets: rarity+synergy+free_reroll+skip+claim1+polish **partial yes**; diversity+no main regression+full limited reroll agency **no**.

### 7. Issues found (severity)
**BLOCKERS (must fix to have working/no-regression shop + passing tests + research goals)**:
- **Non-post Shop enter crash (AttributeError: 'ShopState' has no 'skip_bonus')**: enter else: self.featured_items = self._generate... ; _generate always builds skip_item using f"{self.skip_bonus}" + lambda (only set if is_post_boss before its call). Main shop (menu/continue/death -> ShopState) 100% broken. (Repro: any non-post s=ShopState(g); s.enter()).
- **Main shop K_r (150 reroll featured) unreachable**: in handle KEYDOWN: ... elif not post: (q/e cats only) ... elif post and r: ... elif r and not post: (150 code) ... . For !post + K_r, takes the not-post branch, never reaches r-elif. Feature dead (UI advertises it; code has purchase_message="Featured offers rerolled!"). Regression.
- **Post-boss buy often fails + test broken**: test+sim use coins=300; generate+prioritize always selects 3x weapons (base 800-2000 *0.75 =600+); 300 < cost => "Not enough", no has_claimed. (Upgrades ~300 base would be affordable if picked.)
- **No diversity guarantee**: prioritize for bname in ["weapons","upgrades","special_consumable"]: for cand in bucket: if len>=n break; if not seen: ... append  (NO break after append). Weapons bucket (~10 items) fills all 3 before reaching later buckets. Always cats={'weapons'}. Violates docstring + "Isaac curation bias" + "spread".
- **Post reroll paid after free unreachable/dead**: if rem <=0: "No left" else: ... calc cost (0 if rem>0 and used<free else paid) ... rem-=1 . Since rem>0 => always free, rem hits 0 => blocked. No "then cheap escalating". (free_rerolls only.)

**MINOR**:
- Claimed dim in renderer proxies via shop_items[selected].name (to decide "not chosen"); after claim nav to skip => dims chosen card (wrong; only chosen+skip remain anyway, so dim never hits "non-chosen").
- _get_rarity_colors unused (dead).
- post_boss_items not synced on claim filter (category_items only; _update would clobber if called, but !post guards).
- Duplicate msg draw in renderer (virtual WHITE + direct GREEN/RED); positions use fixed SCREEN_ (may misalign on dynamic res).
- Featured (main) items get post_boss=True + discounts (harmless, display only).
- free_rerolls gives B=2 (same S/A); weights/bonus distinguish.
- Minor msg/cond oddities in post reroll (e.g. always ", free" if fr>0).
- Headless image errs (tolerated elsewhere).
- No explicit test for main reroll / non-post enter (latent bugs).

**Suggested minimal fixes** (if resumed for edit; not applied here):
- In enter else: self.skip_bonus = 0; before featured= (or better: move skip creation to only post, or pass bonus=0 to _generate, or split _generate_featured).
- Restructure handle ifs: e.g. after esc, if not post and key in (q,e): ... ; if key==K_r: if post: post_r else: main_r ...
- In _generate prioritize: after chosen.append(c) add `break` (take 1 per bucket).
- Bump test coins to 2000 or pick cheapest non-skip (or make post items always affordable e.g. force some dyn).
- For reroll post paid: either remove dead cost code + update comments/UI, or redesign (e.g. separate paid_rerolls, allow when rem<=0 with cost, don't let rem<0).
- For dim: track self.claimed_item_name = name after claim; use in renderer: not item.skip and item.name != claimed_name .
- Optionally call state _get_rarity_colors in renderer, or remove dead method.

### 8. Meets research goals?
- Rarity + synergy + free_reroll (rank) + skip agency + claim-exactly-1 + generous post (discount + rank bonus coins + extra epic apply) + Victory flow + polish (rarity frames/glow/badge/syn tag/claimed dim/skip special/nav/ title): **yes (core post paths)**.
- Diversity (spread), no main shop regression, full limited rerolls (free+paid), test green, "3-choice curation bias" working: **no**.
- Overall: post-boss feels "Hades boon" when it triggers, but main shop UX broken, diversity absent, some dead code.

## Summary for user
- Thorough review done (multi reads/greps on exact changed funcs, 10+ targeted headless -c + debugs, full test runs, py_compile x2, flow smokes).
- Post-boss rework has good bones (rarity assign, synergy tags, skip, claim lock, reroll free, ESC agency) + matches many research points.
- **But blockers mean: do not ship; main shop enter/reroll dead, test broken, diversity not, some logic unreachable.**
- Recommend fix the 4-5 blockers (minimal ~5-10 LOC changes in generate/enter/handle), bump test coins or selection, re-run verifier + full manual shop flows (post + main from menu/after death).
- All absolute paths in review: /Users/spencereese/projects/shooter.py/game_states.py (e.g. 881,1009,1095,1110), renderer.py (850,992,1097), game.py (508,157 shop_items), test_game.py (272,314).
- No other files needed changes for this scope.
- Subagent complete; ready for resume on fixes if requested.

(End of structured VERDICT; see also any generated VERDICT.md)