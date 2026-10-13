# Extended player counts and map sizes — feasibility study

Status: research only. No engine behavior changed.

## Goal
Support 10, 12 and eventually 16 human/AI player slots, with maps large enough for fair starting positions and playable performance.

## Audit A: Player limits
- Identify all definitions of player counts, slots, connection IDs and neutral/spectator slots.
- Trace lobby setup, player assignment, skirmish AI, teams, diplomacy, starting waypoints, save/load, replays and networking serialization.
- Check all fixed arrays, bitmasks, loops and packet fields for 8-player assumptions.
- Do not assume a generic 16-player constant implies 16 playable/networked slots.

## Audit B: Map sizes
- Trace WorldBuilder map dimension UI and validation, map file reader/writer, terrain heightmap allocations, border and playable extents.
- Inspect pathfinding/navigation grids, fog of war, minimap, camera bounds, terrain rendering and object counts.
- Determine practical limits experimentally rather than guessing a hardcoded maximum.
- Compare a baseline 8-player map with 10-, 12- and 16-player test maps. Measure simulation frame time, memory, pathfinding and load times.

## Proposed milestones
1. Build and run an unmodified baseline; capture performance metrics.
2. Static code audit with file/line references and a risk register.
3. Single-player/skirmish prototype with 10 slots and 10 start positions.
4. Increase map dimensions incrementally; benchmark before raising limits further.
5. Test 12 then 16 slots, AI behavior and determinism.
6. LAN/network prototype with all clients using the same modified build; check sync, reconnect, lobby and replays.

## Safety/compatibility
Keep main unchanged. Research and experiments live in dedicated branches. Do not ship original proprietary game assets with GPL code. Treat multithreading as a separate later performance project.

## Open questions
- What is the largest map size currently accepted by the shipped game and WorldBuilder?
- Are there hidden map-dimension or object-count caps?
- Are 16 internal player records partly reserved for neutral/civilian players?
- What is the minimum viable map size for each player count without pathological pathfinding?
