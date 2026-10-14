# Ten-player local skirmish — long ground-path validation and Amber v5

**Date:** 2026-10-14  
**Branch:** `feat/skirmish-ten-players`  
**Starting checkpoint:** `a95f2cd1ea4e86af39ea46272fe5c8b4bb572935`  
**Status:** Long, headless ground pathfinding and player-source dozer move checks **passed**; visual/manual mouse tests and automatic tech capture **remain open**.

This supersedes the short/interrupted test outcomes in [vehicle-stall-checkpoint-2026-10-14](vehicle-stall-checkpoint-2026-10-14.md). See [HANDOFF_TEN_PLAYERS.md](../../HANDOFF_TEN_PLAYERS.md) for history, runtime isolation and security boundaries.

## Proven defect and fix

The original local ten-player GUI match had a live **30,000-record pathfinding pool fully allocated**, causing ground vehicle/dozer freezes while some infantry and aircraft still acted. The preceding checkpoint introduced a candidate: in >8-player **local Skirmish only**, select the engine's existing fixed pathfinding mode from the first map load and allocate one ground/bridge/wall-cell-backed pool (375,084 records for the tested 600×600 maps). **Legacy ≤8-player and online game capacity is not changed by this fix.**

We retained the owner's older executables and tested the compiled candidate in isolated Docker/Wine prefixes, with no original Windows installation writes. Real game frames, not wall-clock durations, establish progress: **36,000 frames = 20 simulated minutes** at the engine's baseline 30 logic frames/s. The test-only `-localskirmishtestfps 120` accelerates ordinary updates without skipping logic frames.

## Completed runtime validation (20 simulated minutes each)

| Private log in `/home/hazem/projects/generals-extended-tests` | Minimum free path records | Allocation failures | Actual late combat-vehicle displacements | Last-minute displacements | Nine AI controllers/economy/expansion/battle |
|---|---:|---:|---:|---:|---|
| `groundfix-tenbases-long-20261014.log` | 367,812 | 0 | 764 | 85 | PASS |
| `groundfix-amber-long-20261014.log` | 353,755 | 0 | 2,850 | 264 | PASS |
| `groundfix-amber-v5-long-20261014.log` | 352,869 | 0 | 2,687 | 279 | PASS |
| `human-ground-command-qa-20261014.log` (Amber v5) | 353,528 | 0 | 2,548 | 212 | PASS |

All four had **actual >=20-unit position changes by combat vehicles belonging to each of AI slots 1–9** after frame 12,600, with continuing combat vehicle movements during the last minute. This is stronger evidence than the unit AI `moving` flag. All had local human + nine AI, no network transport. The Amber runs additionally verified west/east teams (5 versus 5), correct ten starting positions and Hard AI. All AI generated income, constructed combat units and established at least two depots. On Amber v4, the previously stalled AI slot2 (Air Force General/faction7) recorded **25 kills by frame 36,000**; on Amber v5, slot2 recorded **48 kills**. On v5, slot9 recorded **zero kills but one frontline combat unit** at the final observation; do **not** claim all nine had confirmed kills. The strict battle checker counts frontline presence or kills over the test.

The old owner's live game was never terminated as part of testing; it subsequently exited on its own. The **test-only processes** were intentionally terminated after their 36,000-frame verifiers passed (reported exit143), not after crashes.

### Legacy8 isolation

`groundfix-legacy-eight-regression-20261014.log` reached frame 11,700 (6.5 simulated minutes) with one human + seven AI. Pathfinding remained `capacity=30000`, minimum free21,965, failures0, and controller/slot checks passed. This is **not** a 20-minute legacy-match or save/load compatibility proof.

### Human dozer orders (engine path)

A new **opt-in** release flag `-localhumanmovetest` issues the player's normal `CMD_FROM_PLAYER` group-movement action to a real human-owned dozer, once at frame 12,600 (target 1600,720) and again at 23,400 (target 900,800). It is only enabled with this explicit flag, 10-player local Skirmish and no network. Normal owner games never pass this flag.

The full 36,000-frame private test and `scripts/verify_local_human_vehicle_commands.py` **PASSED**:

- Dozer object ID 266: actual start **(840.5,630.5)**; after first order reached **(1599.8,730.4)**, maximum displacement **765.8**.
- The second order returned it to **(911.3,810.4)**, maximum displacement **693.1**.
- Path records remained available, failure count zero.
- **Not tested:** real human cursor selection/right-click injection through the X11 Wine GUI. We exercised the engine command action used by the UI, not physical mouse input. The fixture test explicitly rejects stationary `moving=1`, short match and allocation-failure false positives. Five new fixture tests passed; 17 MapTools tests total passed.

The new VC6/Docker-built artifact is privately installed at:
`/home/hazem/projects/generals-extended-tests/runtime/ZeroHour/generalszh-ten-validated-20261014.exe`. SHA256 `1be253fa8c8767dd017405db647fb0395c2e17e03f078dc8d30a75a2af4b2c45`. The old pathfix build `generalszh-ground-fix-final.exe` (SHA `c59281662f436d271e74460b44b51ac7f3541213d771612a43d28023245c5e0f`) and old owner executable remain preserved. This new binary includes the **disabled-by-default** command QA feature. Both `z_generals` and `g_generals` were successfully built in the preceding checkpoint; the latest diagnostic changes were verified with a fresh full **`z_generals` build** and not another new `g_generals` rebuild.

## Amber Canyon v5: graphics-only prototype upgrade

`scripts/build_five_aside_desert_map.py --style v5` generates a new owner-private 600×600 map, adds natural windblown sand/foothill rocky washes using licensed textures already in the owner's private map, expands distant decorations to **216**, and uses 1,472 tile-blend records. The old default `--style v4` reproduces the original v4 map **byte for byte**, SHA `3bf06fdd17d8a57222f2520a9ea7f9bd1ada19abb3e9e1a95a891f368b44f7a1`.

Crucially, v5's `HeightMapData`, `WaypointsList`, `PolygonTriggers` match v4 **byte for byte**: navigation collision, cliff masks, map elevations, all 210 route links, ten starts, 38 supply docks, six neutral technical buildings and three passes were not rearranged. The v5 terrain audit confirms all 294 checked sites reachable with the established clearance heuristic. The optional `scripts/retint_map_preview.py` creates a private v5 minimap thumbnail without embedding licensed content in Git. V5 map SHA256 `3f60067137789912739bed92b80835dd41bcfe967aa8d53f385abd6e8465009a`. Both v4 and v5 passed their long AI/vehicle tests.

**Not proved:** professional cinematic terrain appearance inside the actual 3D game, complete pass visual visibility/texture quality, neutral-tech capture behavior (0 AI-owned tech buildings reported in the long matches), and completion of a full 5v5 victory/defeat. The preview is only a navigational thumbnail, not a 3D visual validation.

## How the owner runs the actual validated build

After passing tests, the **private** owner launcher was updated to the new versioned binary. Its previous state was preserved in `/home/hazem/projects/generals-extended-tests/patch-backups/play-ten-skirmish-before-ground-fix-20261014.sh`. The change was only to the launch script and private Wine installation; it does not alter the original Windows game. None of these private binaries, original assets or generated maps are committed.

**Recommended tested 5 versus 5 direct startup** (one human on west team with four AI allies versus five east Hard AI enemies; `START_CASH` optional):

```bash
bash /home/hazem/projects/generals-extended-tests/play-amber-five-aside.sh
# or START_CASH=10000 bash .../play-amber-five-aside.sh
```

This launches `generalszh-ten-validated-20261014.exe -quickstart -localfiveaside -localhardai -localskirmishtestcash 50000 -localskirmish "...AmberCanyon_5v5_v5.map" 10` through the existing Wine/Docker launcher **with no timeout**. Do not add the `-localhumanmovetest` flag during ordinary play.

**Editable ten-slot setup**, maintaining the owner's former TenBases map choice (manual teams/armies as desired):

```bash
bash /home/hazem/projects/generals-extended-tests/play-ten-skirmish.sh
```

The new Amber v5 map, minimap and `map.str` have also been staged in the owner's private Wine Documents/Maps, so it can be selected if using editable setup (the exact 5v5 team auto-assignment is guaranteed only in the direct startup script). If the map or tenth slot is missing, check the executable's versioned name, the 10-player `.wnd` layout staging, and the map's `Player_10_Start` waypoint. Start a **new** game for any fix; an already-open process cannot adopt a new executable.

In the game, use **Tab diplomacy** to confirm the 10 rows/players, look for all 9 AI's military/supply buildings and unit production, observe late combat moves/attacks after 7–15 minutes. For **machine-checkable proof** use the isolated validator (safe for owner's launcher/main prefix):

```bash
cd /home/hazem/projects/GeneralsGameCode
python3 scripts/verify_ground_movement_log.py /home/hazem/projects/generals-extended-tests/groundfix-amber-v5-long-20261014.log --minimum-frame 36000
python3 scripts/verify_local_skirmish_log.py /home/hazem/projects/generals-extended-tests/groundfix-amber-v5-long-20261014.log --minimum-frame 36000 --economy --expansion --five-aside --hard-ai
python3 scripts/verify_local_human_vehicle_commands.py /home/hazem/projects/generals-extended-tests/human-ground-command-qa-20261014.log --minimum-frame 36000
```

Compact SHA-linked measured evidence is in `docs/research/evidence/vehicle-stall-2026-10-14/long-ground-validation-2026-10-14.json`. Full logs/artifacts remain private; tests were in separate Wine prefix `wineprefix-vehicle-test-20261014`. No disk cleanup, owner live game shutdown, Windows installation write, changes to network slot limits, or proprietary asset commits were performed.

## Remaining priorities

1. Manually click/move both a human dozer and human combat tank through the actual Wine GUI in a fresh match; verify after an hour-scale game or at least after seven game minutes.
2. Native AI tech capture: all technical sites remain neutral in these matches; assess faction capture upgrades, script priorities and path accessibility. Do not cheat by assigning ownership for free.
3. Check v5's actual rendered texture quality and mountain pass/rock collision inside the game, not just minimap.
4. Multiple seeds, 5v5 victory, save/load/replay backwards compatibility and 20+ minute legacy8 performance validation.
5. Future GPU fps/performance comparison against Windows and, separately, the networking/player-capacity architectural roadmap.
