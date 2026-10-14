# Amber AI + terrain integration — 2026-10-14

## Git and scope

Merged `feat/amber-strategic-terrain` and `feat/amber-strategic-ai`
in `feat/amber-ai-terrain-integration`; both feature branches remain
available with their original commits. Additional code connects the
authoritative v6 `map_contract.json` to the AI telemetry/route verifier.
This is **a software integration, not a validated AI combat fix**.

Owner worktree with uncommitted v5 and C++ edits was preserved.
No engine C++, Windows installation, owner process, terrain data,
rock positions, licensed maps or network protocol were modified.
Private runtime artifacts and diagnostics remain outside Git.

## Contract compatibility

v6 terrain schema version 1 uses `bases/resources/neutral_tech/`
`vehicle_corridors`; AI v5 internal schema uses `starts/supplies/`
`tech/ai_paths` with native waypoint IDs. New
`scripts/strategic_ai/contract.py` translates these data formats.
The adapter verifies original map SHA256, grid dimensions, ten
start IDs and teams, all 30 route names and inbound orientation,
and each of 240 native waypoint coordinates and 210 directed links.
Waypoint IDs are **extracted from the native map**, not fabricated.
Stale contract data, reversed edges, or mismatching maps hard-fail.

`scripts/analyze_amber_skirmish.py` now accepts
`--map-contract CONTRACT.json --map MATCHING_PRIVATE.map` for v6,
or `--layout PRIVATE_V5_LAYOUT.json` for legacy v4/v5 inputs.
The Wine log parser now reads the complete map path even with spaces
and guards against analysing a v5 log as v6.

No `ai_route_policy` is present in the terrain team's v6 contract.
**Correct behavior:** v6 route proposal remains disabled rather than
silently applying hard-coded v5 waypoint offsets. Geometric baseline
is still inspectable. Both CLI tools fail closed on proposed map
segments intersecting resource/tech clearance heuristics. Overlay
generation also checks cliff and site reachability.

## Validation (private, reproducible)

Source log: `generals-extended-tests/amber-v6-engine-smoke-20261014.log`
and private `AmberCanyon_Strategic_v6.map` matching the checked-in
contract SHA256. Runtime reached **20,700 frames = 11.5 simulated
minutes**. Original strict skirmish and ground movement checks pass
with a 20,700 minimum. Terrain contract verifier passes.

Integrated geometry: 30 inbound routes; 240 native nodes; 210
directed links; all **294** site points reachable with the static
cliff heuristic; 0 cliff-segment failures. **198**
resource/tech footprint-proximity warnings remain by the AI
auditor's conservative thresholds: they are not proven engine
collisions but prevent unsafe overlay output. All nine AI have
actual sampled ground vehicle displacement in the v6 smoke.
Slots 6 and 9 had no kills at 20,700; neither was proven incapable
of attacking. Actual offensive targets and total casualties
cannot be recovered from these old logs.

V5 original 36,000-frame baseline report also generated after
integration, and the CLI regression passed. These two runs have
*different simulated durations*, so numerical v5/v6 kill
comparisons do not establish an intervention effect.

Validation files are owner-private at
`generals-extended-tests/amber-ai-terrain-integration/validation/`.
No new v6 20-minute / multi-seed gameplay was performed. Existing
GUI game has not been terminated.

## Run checks

```bash
cd /home/hazem/projects/generals-extended-tests/worktrees/amber-ai-terrain-integration
python3 -m unittest discover -s Tests/MapTools -p 'test_*.py' -q
python3 scripts/verify_local_skirmish_log.py \
  /home/hazem/projects/generals-extended-tests/amber-v6-engine-smoke-20261014.log \
  --minimum-frame 20700 --economy --expansion --five-aside --hard-ai
python3 scripts/verify_ground_movement_log.py \
  /home/hazem/projects/generals-extended-tests/amber-v6-engine-smoke-20261014.log \
  --minimum-frame 20700
```

## Remaining before claiming AI improvements

1. Terrain agent must approve actual v6-safe corridor clearance,
   including the currently flagged resource/tech routes, and
   publish a calibrated `ai_route_policy` and map-contract
   update if waypoint movement is permitted.
2. Re-run segment clearance and conservative cliff/slope checks;
   do not lower thresholds simply to make the result pass.
3. Generate a fresh owner-private route-overlay map (never
   overwrite the current v6 original), then play distinct-seed
   matches of at least 36,000 simulation frames per candidate.
4. Capture actual offensive attack/target and enemy damage
   events in a separately authorized instrumentation branch if
   precise first engagement and loss rates are required.
5. Keep `feat/amber-strategic-terrain` and
   `feat/amber-strategic-ai` as historical unmodified branches.
   Do not auto-merge or push proprietary maps.

The v6 terrain map itself can be played as before; this integration
does not introduce a new executable, new 5v5 launcher or new
validated offensive AI behavior. The existing game is unaffected.
