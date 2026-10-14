# Vehicle stall and 5v5 checkpoint — 2026-10-14

The owner explicitly requested that development/tests stop, all source changes and
documentation be committed/pushed, and a prompt be supplied to the next agent.
This is a **handoff of partially validated work**, not a declaration that vehicle
movement or the professional 5v5 map is finished.

Read [HANDOFF_TEN_PLAYERS.md](../../HANDOFF_TEN_PLAYERS.md) first for implementation,
preservation rules, reproduction commands, private artifacts and next tasks.

## Build and executable evidence

Both `z_generals` and `g_generals` built successfully with Docker/VC6 after the shared
pathfinding header change. A final combined incremental build passed after the
release CLI test FPS/cash options were added. Existing outputs were preserved;
no build/disk cleanup was used. The original Generals executable was compiled,
but its gameplay was not retested in this checkpoint.

Final candidate: private `runtime/ZeroHour/generalszh-ground-fix-final.exe`.
SHA-256: `c59281662f436d271e74460b44b51ac7f3541213d771612a43d28023245c5e0f`.
Matching PDB: `patch-backups/vehicle-stall-20261014/generalszh-ground-fix-final.pdb`.

Earlier candidate `generalszh-ground-fix-v1.exe`:
`72b2366a2d69308b9a8216d7ce3aae7e324037c07d3acefaf5c30d81b1dcf48b`.
It reached frame 9,900 on TenBases with default 10,000 credits and nine Easy AI;
economy/expansion checks passed at frame 9,000. The 360-second timeout then ended
that short test. Its passed build/test is not evidence beyond 5.5 simulated minutes.

Build logs in `/home/hazem/projects/generals-extended-tests`:

- `vehicle-pathfinding-build.log`: coherent 1,089-step Zero Hour rebuild.
- `vehicle-pathfinding-generals-build.log`: original Generals rebuild.
- `vehicle-pathfinding-v2-build.log`: direct CLI test FPS support.
- `vehicle-pathfinding-final-build.log`: final Zero Hour + Generals targets.

## Live diagnosis, preserved

The old owner executable remains running at the end of the checkpoint. Two read-only
memory samples found all 30,000 pathfinding records allocated and a null free-list
head. About 26,000 records retained obstacle IDs. The owner reported stuck vehicles
while infantry/aircraft continued, and screenshots showed stalled dozer construction.
No live memory, GPU setting or original Windows game file was changed.

`vehicle-stall-live-pool.txt` SHA-256:
`fcca91e66a2d47f4e9e52da8216f44552e8cff679306f14086924c49502884ae`.
See the handoff for old-PE symbol matching and the limits of a live non-atomic sample.

## Final candidate: actual interrupted runs

Both runs used separate copied Wine prefixes, 50,000 starting credits, seed 12345,
one idle human and nine Hard Army AI. `-localskirmishtestfps 120` requested faster
normal updates; actual progress below is taken from frame logs. No logic frames were
skipped. The old owner's match was left open during the tests.

| Map | Last observed frame | Simulated minutes | Pool capacity | Lowest observed free records | Allocation failures |
|---|---:|---:|---:|---:|---:|
| TwilightFlame_TenBases_v1, free-for-all | 9,000 | 5.0 | 375,084 | 365,673 | 0 |
| AmberCanyon_5v5_v4, teams west/east | 11,700 | 6.5 | 375,084 | 363,630 | 0 |

Both logs passed actual controller/start/color checks and reported serializer
`networkSlots=8 localSlots=10 legacy=pass`. Amber also passed the explicit two-team,
fixed-start and Hard Army configuration checks. The nine AI economy/second-depot
verification passed on TenBases at frame 9,000.

Ground combat vehicle position changes of at least 20 world units between sampled
observations were recorded, grouped by zero-based slot:

| AI slot | TenBases displacement observations | Amber displacement observations |
|---:|---:|---:|
| 1 | 9 | 32 |
| 2 | 0 | 0 |
| 3 | 7 | 34 |
| 4 | 17 | 24 |
| 5 | 46 | 59 |
| 6 | 51 | 78 |
| 7 | 15 | 17 |
| 8 | 2 | 6 |
| 9 | 0 | 4 |

These are repeated observations, not distinct-unit totals. They show some actual
ground movement, including added slot 8 and, on Amber, slot 9. They do **not** show
that every army's combat vehicles attacked. In Amber slot 2, some dozers/harvesters
changed position but observed combat vehicles remained at the base. At frame 11,700
that Hard Army slot had 44 objects, 19 completed structures, three depots, 14 combat
units, 21,600 earned, zero kills, zero frontline units and zero approach units.

**The strict Amber battle/economy verifier failed at frame 11,700**, reporting
`AI slot 2 has not reached battle or registered combat`. Do not hide this failure or
relax it just to obtain a pass. Investigate faction-7 attack-team composition,
native skirmish routes/targets and longer gameplay after resolving global exhaustion.

The late-ground verifier requires frame 27,000 (15 minutes), actual combat-vehicle
movement after frame 12,600 (seven minutes), and continued movement during the final
minute. Neither interrupted run reached those thresholds. **Long-duration validation
of the fix, human vehicle commands and all-nine-army ground attacks remain unfinished.**
No source build failure or runtime access violation/stack overflow was observed in
these bounded runs. That does not prove stability after the old failure interval.

Runtime log hashes:

- `vehicle-fix-tenbases-final.log`:
  `5722b278738ccb5a3eec3263ad2b6b34547bd0254145bd3f6eda428927ebae64`.
- `vehicle-fix-amber-final.log`:
  `2e957dfcf0b824b73b964b415f25b9ef565a93243e181ce67726876c1eb5ef79`.

Both complete logs remain private. Compact checkpoint JSON files (controllers, sites,
pool measurements and displacement counts) are committed under
[`evidence/vehicle-stall-2026-10-14`](evidence/vehicle-stall-2026-10-14/).

## Checks on verification tools

Python syntax checks passed for the map generator and both runtime verifiers.
The new ground verifier accepted an all-nine-AI movement fixture and rejected zero
free records, allocation failures, a short run and stationary coordinates with
`moving=1`. Thus the moving flag alone cannot fake successful movement.
`git diff --check` passed before committing.

The pre-fix Amber-v4 run reached frame 18,000 and passed the older battle/economy
checks at 10,000 starting credits. This is a different executable/cash configuration
and cannot override the failed final-candidate check above. None of those snapshots
proved automatic tech-building capture; all recorded tech ownership was zero.

## Stop state and continuation

Only the agent's two identified final-candidate containers were stopped:
`7f77a67dddc6` (Amber) and `c375e44403e2` (TenBases). The owner container
`4562ad967e5f` remained running. Re-identify containers next session rather than
assuming these IDs persist. No agent test is intentionally left running.

The owner launcher **still selects the old executable**. It was not switched to a
candidate before the requested stop. A new agent should complete late movement and
human-command validation before choosing a new versioned private launcher. The
old running match does not contain this source fix.

Unfinished: extended-match vehicle testing, slot-2 attack-team diagnosis, manual human
vehicle input, <=8 runtime/reset regression, live save/load/replay verification, Amber
visual terrain polish, faction/difficulty/seed coverage, neutral-tech capture/use and
a completed 5v5 battle. See the ordered continuation tasks in the handoff.

All source changes, map generator, diagnostic flags, verification scripts, compact
evidence and this documentation belong to this checkpoint. Generated owner maps,
licensed assets, full Wine prefixes, executables, screenshots and backups are preserved
at their documented local paths rather than distributed with the GPL source repository.
