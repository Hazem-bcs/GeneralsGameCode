# Amber Canyon Strategic v6 — independent terrain handoff

Date: 2026-10-14. Branch: `feat/amber-strategic-terrain`.
Worktree: `/home/hazem/projects/GeneralsGameCode-amber-terrain`.
Primary checkout `feat/skirmish-ten-players` and all its uncommitted code are unchanged.
**Status: terrain prototype / engine smoke tested, NOT visual-final or long-match certified.**

## Private outputs (never upload binary maps or game assets)
- `/home/hazem/projects/generals-extended-tests/maps/AmberCanyon_Strategic_v6/AmberCanyon_Strategic_v6.map`
- Same folder: `map_contract.json`, `terrain_audit.json`, `vehicle_detour_audit.json`, `generation_report.json`, schematic `AmberCanyon-v6-terrain-plan.png`, `map.str`, preview TGA and layout JSON.
- SHA256 of private .map: `6c66ccf3e60ffb22832e0d8faa494518967ee78846777465980c95e521fa1823`.
- Private v4/v5 maps remain intact. No Windows installation or engine file was changed.
- Uncommitted v5 generator backed up separately at `generals-extended-tests/patch-backups/amber-terrain-v6-20261014/build_five_aside_desert_map-v5-uncommitted.py`.

## Repo deliverables
- `scripts/amber_strategic/terrain.py`: seeded mirrored terrain model, grading for pads, roads, resources.
- `scripts/amber_strategic/config.py`: generator parameters.
- `scripts/amber_strategic/ckmp.py`: CkMp v4 heightmap / BlendTileData v8 codec, reusing existing metadata reader.
- `scripts/amber_strategic/audit.py`: static slope, clearance, connectivity, pad audit.
- `scripts/build_amber_strategic_map.py`: new non-overwriting private-map CLI, contract and schematic.
- `scripts/verify_amber_contract.py`: base-exit and detour reachability.
- `Tests/MapTools/test_amber_strategic.py`: nine new tests.
- `docs/research/amber-strategic-v6/map_contract.json`: AI client's machine-readable contract (no private assets).
- `docs/research/amber-strategic-v6/engine-smoke-evidence.json`: concise engine evidence (raw logs remain private).

**AI agent:** consume the map contract; it contains 10 base IDs/teams, exits, all 38 docks, 6 tech sites, 30 inbound vehicle corridors, 5 crossings/chokepoints and advisory forbidden mountain cores. The AI agent must not alter the terrain generator; report missing data back to the terrain owner.

## Verified geometry and tests
- Height range 41–226. Flat within ±5 of base 72: **62.74%** (earlier ~76%; measure by same tolerance).
- All 10 base pads passed with 100% of sampled sites level and static-driveable.
- All 294 v5 starts, resource/tech and inbound AI-waypoint sites connect.
- Center crossing y=3000 and four alternate crossings y=480/1050/4950/5520 connect.
- A separate test confirmed 10/10 base exits traversable and both flanks accessible even after artificially blocking the central crossing.
- Terrain elevation mirror west/east; all ObjectsList, WaypointsList, SidesList and PolygonTriggers bytes are identical to v5.
- `python3 -m unittest discover -s Tests/MapTools -p 'test_amber_strategic.py' -v` → **9/9 pass**; 12 existing `test_map_*.py` tests also passed.
- Static tests use a 4-neighbor traversability estimate, <=7 height units per 10 world, plus 20 world cliff clearance. This cannot model all engine rock-object collision or actual tank turning.

## Real engine smoke (separate Wine prefix, owner game unaffected)
- Private log: `generals-extended-tests/amber-v6-engine-smoke-20261014.log`; SHA256 in `engine-smoke-evidence.json`.
- Headless real engine, one idle human + nine Hard AI, west/east 5v5; reached frame 20,700 = **11.5 game minutes**.
- Vehicle movement verifier **PASS**: late combat vehicles displaced for AI slots 1–9, 932 late changes and 388 last-minute changes.
- Pathfinding: capacity 375,084, minimum 358,257 free, allocation failures 0.
- Economy, expansions, five-a-side team and Hard AI checks **PASS**.
- Test runner intentionally ended after 180 wall-clock seconds (timeout exit 124); no crash was inferred.
- No full victory, replay/save-load, physical human mouse drive, 20+ minute session, or 3D visual inspection has been validated.
- No live match was closed. Owner's separate v5 GUI game was active during this test.

## Repro commands (use a NEW destination directory)
```bash
cd /home/hazem/projects/GeneralsGameCode-amber-terrain
python3 scripts/build_amber_strategic_map.py \
  /home/hazem/projects/generals-extended-tests/maps/AmberCanyon_5v5_v5/AmberCanyon_5v5_v5.map \
  /home/hazem/projects/generals-extended-tests/maps/AmberCanyon_Strategic_v6_rebuild
python3 scripts/verify_amber_contract.py PRIVATE_MAP.map PRIVATE_CONTRACT.json
python3 -m unittest discover -s Tests/MapTools -p 'test_amber_strategic.py' -v
```

## Remaining
1. In-game visual/editor audit of cliff textures, heightmap, transitions and existing rock-decoration collisions; existing rendered image is a **schematic**, not an engine screenshot.
2. Large vehicles ordered to each choke, side detour, resource and each base exit, including after seven minutes. Existing smoke validates actual AI movement globally, not every route.
3. 20+ minute run, multiple seeds/factions, full win/loss and replay/save/load.
4. True bridge objects were deliberately **not** added: collision/pathfinding support in this custom-map setting was not independently established.
5. Neutral-tech ownership remained unverified; changes to capture behavior belong to the AI agent.
6. No merge, push, or publication of private licensed files is part of this terrain branch.
