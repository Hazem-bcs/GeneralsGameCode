# Amber v5 — skirmish AI evidence and waypoint audit (2026-10-14)

## Scope and provenance

Branch: `feat/amber-strategic-ai`, independent worktree based on `a95f2cd1e`.
Original working tree contains uncommitted changes: **not modified**.
The original C++ engine, Windows files, network protocol, terrain heights,
textures and rock positions were not changed. A user's active Wine game
(PID 15081 at inspection) was intentionally not interrupted.

Inputs: owner-private `groundfix-amber-v5-long-20261014.log`,
`groundfix-amber-long-20261014.log`, Amber v4/v5 layout JSON and CkMp maps.
Both long logs reached 36,000 logic frames (20 simulated minutes); reported
seed 12345 in the original validation handoff. There is **no distinct-seed run**
in this change. Full, SHA-tagged numerical output is owner-private at
`/home/hazem/projects/generals-extended-tests/amber-strategic-ai/experiments/`.
No licensed map, game executable, log or Wine prefix is added to Git.

## Observations per AI slot (Amber v5)

`builtUnits` is the existing runtime **counter**, not a verified count
of offensive troops; `near` is minimum sampled ground-combat-vehicle
distance from any enemy starting base (not nearest enemy unit).
`moves` are actual consecutive >=20-world-unit position differences
for combat ground vehicles, not the `moving` flag.

| Slot | Faction ID | builtUnits | kills | Ground moves | Nearest enemy base | Max distance from own start |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 155 | 26 | 256 | 2225 | 2656 |
| 2 | 7 | 74 | 48 | 159 | 3441 | 807 |
| 3 | 6 | 95 | 139 | 444 | 3441 | 765 |
| 4 | 10 | 125 | 16 | 105 | 3036 | 1299 |
| 5 | 12 | 181 | 8 | 326 | 869 | 5623 |
| 6 | 11 | 220 | 7 | 295 | 864 | 4771 |
| 7 | 2 | 109 | 12 | 102 | 3276 | 929 |
| 8 | 9 | 308 | 39 | 114 | 1254 | 3208 |
| 9 | 7 | 65 | 0 | 218 | 3390 | 827 |

### Interpretation

Slots 2, 3 and 9 are **base-confined by a relative spatial proxy**:
their combat ground vehicles never exceed about 80% of their same-team
neighbouring-base spacing; slot 7 is near that threshold. Slot 9 still
has measured ground displacement: it is incorrect to call its vehicles
immobile or to infer total lack of attacks from zero kills. Slots 5
and 6 show much deeper ground movement near enemy start positions.
The physical bases form two x-columns (west/east); there is no true
second x-layer of rear starts. Here 'rear' refers to observed military
deployment depth, not a map-start type.
## Faction and combat limits

Slots 2 and 9 both have faction ID 7 (identified as USA Air Force
General in the prior project handoff). Both were restricted in ground
deployment, but slot 2 obtained 48 kills and slot 9 obtained none.
This is consistent with asymmetric air/infantry attack composition
and/or AI attack-team selection; **faction causality is not proven**.
Compare other seeds/faction placements before attributing a defect
to the Air Force General itself.

Observed first increase in a kill counter is **not** an attack-order
timestamp or a precise first engagement. LOCAL_GROUND excludes
infantry/aircraft, and records no health, deaths, targets, damage,
path selections or route identifiers. Unit losses and actual ground
attack success are therefore unknown; the report includes only
net decreases in current combat-unit counts, which are NOT a casualty
total. Earnings and completed depots are observed separately from attack.

## Native waypoint/path finding

In `ScriptActions::doTeamFollowSkirmishApproachPath` the game selects
`getSkirmishEnemyPlayer()->getMpStartIndex()+1`, builds
`CenterN/FlankN/BackdoorN` and calls
`getClosestWaypointOnPath`, then follows directed links.
Therefore Amber's numbered paths correctly run **inward toward
the numbered enemy base**. Native CkMp auditing verified
240 path nodes, 210 directed links, 30 correctly identified routes,
no missing/reversed links, and a complete ten-start layout.

Earlier map generation audited waypoint **sites**, but not whole
path segments against resource/tech footprints. A new conservative
geometric heuristic checks continuous segment-to-site clearance
(supply 195 world units; neutral tech 155). Results:

| Geometric metric | v4/v5 baseline | first proposal |
| --- | ---: | ---: |
| Paths | 30 | 30 |
| Suspected resource/tech proximity events | 198 | 100 |
| Paths with suspected conflicts | 30 | 28 |
| Segments crossing 20-unit-clearance cliff mask | 0 | 0 |

These are **proximity warnings at heuristic thresholds**, not confirmed
physical collisions with an actual building, and no causal proof that
the warnings explain Slot 9. Some crossings pass through supply dock
centers, however, and warrant higher-priority engine playtesting.
The proposal offsets a portion of crossing routes and advances route
endpoints, but still has 100 warnings. The strict map overlay builder
correctly REFUSES to generate it: not deployable, not merged into v6.

## v4/v5 comparison (same map geometry, same reported seed)

| Slot | v4 kills | v5 kills | v4 ground moves | v5 ground moves |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 55 | 26 | 335 | 256 |
| 2 | 25 | 48 | 289 | 159 |
| 3 | 143 | 139 | 415 | 444 |
| 4 | 18 | 16 | 84 | 105 |
| 5 | 7 | 8 | 325 | 326 |
| 6 | 19 | 7 | 311 | 295 |
| 7 | 9 | 12 | 151 | 102 |
| 8 | 21 | 39 | 113 | 114 |
| 9 | 5 | 0 | 248 | 218 |

V4→v5 was graphics-only according to the reference evidence,
so these differences must not be attributed to new waypoint
geometry. No valid runtime 'after route fix' result exists yet.
Do not advertise all-nine-army successful ground attacks.
## Strict verification and what remains

The unmodified `verify_local_skirmish_log.py` and
`verify_ground_movement_log.py` passed for the real 36,000-frame
Amber v5 log. New MapTools tests (23 total) verify stationary `moving=1` does
not count as displacement, path-pool exhaustion fails, incomplete
logs fail and a segment-midpoint resource intersection is detected.
No existing strict assertion was weakened.

The native map overlay writer changes ONLY existing route waypoint
coordinates and preserves other chunks. It refuses files already
present, intersects-with-resources candidates, and cliff intersections.
No edited .map was emitted because the proposal fails the clearance
gate. A different source map with added/deleted waypoint IDs requires
its own native topology contract; this tool does not silently alter
the binary object/link count.

A new 20-minute independent-seed comparison is **not done**.
An owner's interactive Wine match was active during inspection,
so no heavy competing gameplay was started or stopped. No actual
damage/target telemetry exists to prove when the AI first engaged,
or to distinguish defensive kills from frontline attacks.

Before shipping: coordinate with the terrain agent to remove route
footprint warnings and publish a map contract, generate a fresh
PRIVATE candidate, run separate-prefix >=36,000-frame matches
on at least two genuinely distinct seeds/faction assignments,
verify original strict tests, then compare each slot's ground
positions and offensive outcomes. Keep hard failure conditions.
