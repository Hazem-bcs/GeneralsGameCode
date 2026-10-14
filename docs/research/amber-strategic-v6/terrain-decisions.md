# Amber Canyon Strategic v6 — terrain and strategic decisions

**Owner-private desert map:** 600×600 playable height samples (10 world units/sample), 740×740 including non-playable border, base elevation 72. `HeightMapData` is a 28-byte v4 header followed by one byte/sample. `BlendTileData` v8 contains base tiles, blend indices, two additional tile fields, per-row cliff bits, owner palette metadata and blend records. `ObjectsList` holds starts, docks, tech, 30 AI approach paths and decorations. `WaypointsList` links existing AI routes. No licensed data is embedded in source control.

## Strategic terrain grammar

| Feature | Approximate world location | Intent | Counterplay / safety |
|---|---|---|---|
| Two highland ridges | Center x≈3000, y≈1900 and y≈4120 | Break line-of-sight/frontline regularity and steer armies to strategic crossings | Broad east-west passages at y1050/3000/4950; open north/south flanks |
| Elevated accessible shelves | Mirrored around x≈2280/y1710 and x≈2220/y4320 | Valuable local height positions, defensible but not impassable | Graded approaches; no mandatory resource/build site on steep edge |
| Rolling perimeter hills | Mirrored x≈1610/y1470,4530 and x≈1900/y2800,3390 | Give defenders terrain choices away from a single flat plain | Protected 475-world-radius base pads and 175-world dock zones |
| Dry lowland washes | Mirrored x≈2070/y2420 and y3650 | Alternative low routes between high ground | Five cross-frontier corridors stay open; no forced dead end |
| Central front gate | x≈3000/y3000 | Main pressure point with nearby neutral tech and contested supplies | Flank detours remain when central crossing is blocked |
| North/south end runs | y480 and y5520 | High-cost strategic bypass of main bottleneck | Reachable from both halves of the map |
| Neutral tech + contested resources | Existing v5 sites preserved unchanged | Incentivize territorial contests without changing AI scripting | Equal mirrored placements, clearance buffers, connectivity verified |

All east-west elevation/collision silhouettes are mirrored; side fairness is built into the generation. The 38 supply docks and six neutral tech sites are untouched, as are ten start objects, all AI route waypoints and their inbound directions. Starting armies remain five west versus five east in the local five-aside game mode.

## Tradeoffs and measured outcome

Elevation range is 41–226, versus the base height 72. **62.74%** of playable height samples lie within ±5 height units of base, compared with roughly 76% in the prior version. The new terrain contains meaningful highlands but also retains broad open/buildable lowland strips. Grade-to-flat protection is intentionally explicit for bases, docks, tech and the existing vehicle roads; reducing these safety corridors just to improve a texture/elevation metric would be counterproductive.

A strict static audit checked 294 starts/docks/tech/AI route nodes: zero isolated, all five crossings connected, ten pad usability fractions 1.0. A separate contract validator checked all ten base exits and the ability to cross the map after blocking the center gate. These are approximations: tests cannot prove sightlines, wheel collisions, tank turn radii, WorldBuilder visuals, or the value of each tactical height feature.

The runtime smoke test reached **11.5 game minutes**, confirmed late movement of combat vehicles for all nine AI slots and no pathfinding pool failures. It did not prove every route, full match, real human GUI controls, or visual aesthetics. No actual bridge was placed because native bridge behavior and AI vehicle collision were not established.

The private plan PNG illustrates terrain heights and route sites, **not** the actual in-engine perspective. Treat v6 as an experiment requiring a playtest before release.
