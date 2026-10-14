# Handoff — Amber strategic AI, 2026-10-14

## Status: DIAGNOSIS AND STATIC CANDIDATE, NOT A SHIPPED AI FIX

Worktree:
`/home/hazem/projects/generals-extended-tests/worktrees/amber-strategic-ai`.
Branch: `feat/amber-strategic-ai`, base `a95f2cd1e`.
The original `feat/skirmish-ten-players` checkout was DIRTY before
this work. None of its uncommitted edits were modified, reset, stashed,
cleaned or merged. No engine, terrain height, texture, rock, executable
or network protocol was changed. No proprietary map/log/binary added
to Git and no running owner's match was closed.

## Deliverables

- `scripts/strategic_ai/telemetry.py`: parse LOCAL_* observations.
- `scripts/strategic_ai/analysis.py`: conservative slot-by-slot
  movement, economic, late displacement, counter and confidence audit.
- `scripts/strategic_ai/routes.py`: full-segment resource/tech
  clearance and data-only waypoint proposal.
- `scripts/strategic_ai/native_map.py`: directed native CkMp
  waypoint/link parity and guarded coordinate-only overlay.
- `scripts/strategic_ai/terrain_clearance.py`: cliff mask segment
  scan with 20-world-unit clearance heuristic.
- `scripts/strategic_ai/site_reachability.py`: independent BFS
  for starts, supply docks, tech buildings and waypoint sites.
- `scripts/analyze_amber_skirmish.py`: report JSON CLI, v5 layout
  or schema-equivalent v6 contract, optional native map validation.
- `scripts/build_strategic_ai_overlay.py`: private map trial
  builder, fails closed when static intersections remain.
- `Tests/MapTools/test_strategic_ai.py`: eleven additional tests.
- `docs/research/amber-strategic-ai-2026-10-14.md`: per-slot
  diagnoses, numerical tables and before/after limitations.
- `docs/research/AMBER_V6_TERRAIN_AGENT_REQUEST.md`: what the
  independent terrain agent should provide in map_contract.json.
- `docs/research/AMBER_ENGINE_AI_LIMITS.md`: prohibited
  engine instrumentation/change request for a separate branch.

## Evidence and uncompleted stages

Owner-private evidence:
`/home/hazem/projects/generals-extended-tests/amber-strategic-ai/experiments/`.
The 20-minute v4 and v5 original game logs both pass the existing
strict ground movement + skirmish checks (seed 12345 from checkpoint).
Static waypoint resource/tech clearance changed from 198 warnings
to 100 under the proposed overlay, cliff warnings 0→0.
This is NOT an after-gameplay result. 100 proximity warnings remain;
the safe map creator intentionally REJECTS the first candidate.
No new gameplay run/independent seed, no verified attacking
effectiveness for every slot, no measured casualties or exact
first engagement. The active owner's Wine match was untouched.

## Verification

`python3 -m unittest discover -s Tests/MapTools -p 'test_*.py' -q`
(23 tests PASS).
Strict verification, unmodified:
`python3 scripts/verify_local_skirmish_log.py LOG --minimum-frame 36000 --economy --expansion --five-aside --hard-ai`
`python3 scripts/verify_ground_movement_log.py LOG --minimum-frame 36000`
Both PASS against the private Amber-v5 long log. No test weakened.

Next: wait for terrain agent's v6 `map_contract.json`;
adapt route geometry to actual safe pass layout, make the
static overlay produce zero unresolved footprint warnings,
use new private map/Wine prefix, repeat >=36000-frame
real matches on two distinct seeds, observe true ground
advance and target engagement per army, and only then
write a measured gameplay before/after table.
Do not auto-merge with the terrain branch.
