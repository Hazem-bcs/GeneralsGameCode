# To the terrain/level-design agent — integration request for v6

This document is a REQUEST, not a terrain edit. AI agent did not
modify `HeightMapData`, `BlendTileData`, textures, rocks or resources.

## Confirmed source facts

Amber v5 has 30 directed, inbound paths, 210 links and 240 route
nodes; its source waypoint-node connectivity is intact.
However, conservative whole-line clearance checks flag **198**
resource/tech proximity events across 30 paths. This cannot be
detected by a waypoint-endpoint-only audit.
Some center routes pass directly through contested supply dock
locations, while flank/backdoor corridors include the contested
docks at the top and bottom map edges.

The first data-only path proposal reduces that figure to **100**
but leaves 28 paths flagged; it is blocked from map generation.
The actual physical object radius and pathfinder footprint must
be confirmed before interpreting all warnings as collisions.

## Request to terrain agent

1. Provide `map_contract.json` with `starts` (ten ordered
   [x,y] positions), `supplies` ([[x,y,role],...]), `tech`
   ([[x,y,type],...]), and `ai_paths` ([[label, ids, vertices]]).
   Use records `{"label":"Center1","ids":[...],"vertices":[[x,y],...]}`
   for individual paths. Include terrain/path collision hashes. To calculate a waypoint
   proposal for v6, supply an explicit `ai_route_policy` object:
   `midline_x`, `midline_y`, `crossing_vertex_index`,
   `center_vertex_indexes`, `flank_vertex_indexes`,
   `center_offset`, `flank_offset`, `inward_fraction`,
   `vertices_per_path`. These values must be calibrated to v6.
2. Define each base's safe exit / assembly radius, resource footprint,
   and traversable pass polygons. Use explicit world-coordinate
   measurements for your **new** v6 geometry. Do NOT reuse v5
   coordinates unless verified against v6.
3. Inspect contested supply docks inside direct attack corridors.
   Either move docks outside required military lanes, or provide
   navigable alternative lanes around them with vehicle clearance.
4. Keep at least two distinct vehicle-safe approaches per team:
   frontal and real flanking routes, not merely overlapping labels
   that converge on a single building/object choke. Avoid directing
   supply collection traffic and the main army through the same
   narrow bottleneck where feasible.
5. Give west/east base exits enough room for allied base traffic,
   dozers, supply trucks and assembly, and do not force diagonal
   links through hard cliff edges, bridges without validated crossing,
   or terrain decorations with collision.
6. Recheck all segments (not only waypoint vertices) against
   terrain, road edge, supply/tech footprints and choke width.
   Report outstanding exceptions explicitly rather than downgrading
   acceptance thresholds.

## How to integrate

The AI agent's parser/geometry validator reads the schema above.
Route proposal parameters are independent of slot identities;
different-sized v6 path patterns require a map-contract-guided
algorithm rather than an automatic v5 point-index transplant.
The binary overlay writer intentionally rejects unsafe layouts
and changes only existing route waypoint coordinates: it cannot
rebuild v6 rock/mountain terrain or add native waypoint nodes.

Return the v6 map contract first. It should be possible to
re-run the static auditor, adjust route proposals and request
a separate owner-private runtime match without touching the
terrain agent's own worktree. No auto-merge by this agent.
