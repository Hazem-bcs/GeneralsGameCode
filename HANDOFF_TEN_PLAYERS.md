# Ten-player Zero Hour: continuation checkpoint

Updated 2026-10-14. Read this before continuing branch `feat/skirmish-ten-players`.
This is the owner's local development branch, not an upstream release.

## Current priorities and boundaries

The owner wants one local human plus nine functioning AI armies, then a polished
desert/mountain/rock-pass map for **5 versus 5**. The latest gameplay report interrupted
map polishing: aircraft and infantry move, but ground vehicles stop throughout the
match, including vehicles commanded by the human. Diagnose that before declaring the
map or ten-player experience finished. The owner then requested this checkpoint,
documentation, a commit and a push so another agent can continue.

Preserve all local sources, failed experiments, replays, maps, executable versions and
backups in `/home/hazem/projects/generals-extended-tests`. Do not overwrite the original
Windows installation, delete artifacts, clean build directories or change GPU settings.
The original Windows asset tree at `/media/hazem/OS` is mounted **read-only** by the
private runtime launcher. Do not stop an owner's running match to replace an executable.
Inspect current processes before stopping any test; container IDs below are historical.

Network connections, packets, masks and protocol remain **eight slots**. Do not solve
local slot limits by increasing `MAX_SLOTS` or `MAX_PLAYER` globally. Do not promise
12/16 players, network compatibility, complete save/load compatibility or match stability
without runtime evidence.

## Repository and previous milestones

- Checkout: `/home/hazem/projects/GeneralsGameCode`.
- Branch: `feat/skirmish-ten-players`.
- Owner remote: `https://github.com/Hazem-bcs/GeneralsGameCode.git`.
- Previous published feature commit: `9db078965bcb5ab22f79c888f9956cc38876ea9c`.
- Detailed earlier implementation and five-minute evidence:
  [local-ten-player-validation-2026-10-14](docs/research/local-ten-player-validation-2026-10-14.md).
- Older GPU/map/runtime context:
  [ubuntu-gpu-fonts-and-skirmish-status](docs/research/ubuntu-gpu-fonts-and-skirmish-status.md)
  and [extended-players-and-maps](docs/research/extended-players-and-maps.md).
- Original conversation: [تعديل عدد اللاعبين](https://chatgpt.com/c/6acd0d24-4740-83eb-a8b7-e7d1a9e56e4b).

The original prototype's reported stack overflow followed an earlier access violation
and recursive exception handling. A stale VC6 header build made experiments misleading:
Ninja expected dependency files that VC6 did not emit. `prepare_vc6_rebuild.py` now hashes
headers and refreshes source timestamps for a coherent rebuild without cleaning.

After coherent rebuilding, the ninth slot exposed an eight-entry reverse lookup in
`PlayerList::m_slotToPlayerIndices`: slot 8 returned null before a dereference at
`0x004bba83`. The local lookup was enlarged to ten. `GameInfo::getSlotCount()` defaults
to eight; local Skirmish/replay objects own ten slots. Creation, enumeration, colors,
teams, start positions, map cache scanning and local UI follow instance capacity.
The old network serializer still rejects ten-slot data; old eight-slot data imports
into the local object with the last two closed.

Ten-row setup, ten map markers, local loading and ten-row Tab diplomacy were verified
visually. A fifth local team and two extra local colors were added. The replay observer
army selection still exposes eight visible buttons; this is an open UI task.

The ten-base map generator places ten graded build pads, routes, two home supply docks
per base and ten expansion docks (30 total). In >8-player local Skirmish only, AI gets
a supplemental expansion check after two game minutes, then every 30 seconds with
staggered offsets. It budgets normal-cost depots with a 3,000-credit reserve, up to three
depots, avoids duplicate pending orders and checks build terrain/path/overlap. All nine
AI completed 2–3 depots, earned income and produced combat units in the five-minute
test. **That did not establish long-match vehicle movement.**

## Confirmed live vehicle stall

The old owner executable is `runtime/ZeroHour/generalszh-ten-final.exe`, SHA-256
`b5ac37b96a280a74ed23f701f72ea078a9d80e742568b2f8884f79bafe168725`.
The owner launched `TwilightFlame_TenBases_v1` through editable setup with approximately
50,000 starting credits / speed 60. Screenshots showed vehicles and dozers stuck while
infantry, aircraft, income and the game clock continued. A construction stayed at 0%.

Read-only inspection of the running old process directly confirmed **pool exhaustion**:

```text
records=30000 freeBits=0 firstFree=0x0
first sample: obstacles=26294 groundGoals=3316 groundPositions=3957 aircraftGoals=675
repeat sample: obstacles=26144 groundGoals=3521 groundPositions=3863 aircraftGoals=594
```

These categories overlap; do not add them as disjoint record counts. The observations
were snapshots of running memory, not a paused atomic dump, but both samples had zero
free records. `getACellInfo()` returns null when `s_firstFree` is empty. The retail
allocation mode retains records for obstacle footprints and unit reservations, starving
new ground searches on this map. Infantry/air movement alone is not proof of recovery.

At inspection time the owner match was host PID `191816`, Docker container
`4562ad967e5f` (`upbeat_dewdney`), window `0x2600003`. **Re-identify them before use.**
No live memory was modified, no debugger stopped it and no owner match was restarted.
The agent's own headless map test was stopped to reduce load.

How the inspection was established (for an experienced debugger): the unchanged
`PathfindCellInfo.cpp.obj` supplies the exact compiled `getACellInfo` instruction pattern.
Matching it in the old PE identifies `getACellInfo=0x704b00`, `s_firstFree=0xa21dc0` and
adjacent `s_infoArray=0xa21dbc`. The running PE mapped at `0x00400000`; each record is
48 bytes, flags at +44, obstacle ID +40, goal +28, position +32, aircraft +36. A temporary
Docker helper with host PID namespace and SYS_PTRACE read `/proc/191816/mem` **read-only**.
Those addresses are specific to the old executable and must not be reused for a new build.

Private evidence: `vehicle-stall-live-pool.txt`, `vehicle-stall-live-evidence.png`,
`live-stall-before.png`, `live-stall-after.png`. Source backup before this fix:
`patch-backups/vehicle-stall-20261014/map-work-before-pathfinding.patch` and the map
generator copy. The inherited sources are also preserved at
`patch-backups/codex-resume-20261014-015048`.

Related primary upstream investigations:
[pool exhaustion #330](https://github.com/TheSuperHackers/GeneralsGameCode/issues/330),
[large-map pathfinding #100](https://github.com/TheSuperHackers/GeneralsGameCode/issues/100),
[safe cleanup #994](https://github.com/TheSuperHackers/GeneralsGameCode/pull/994).
The diagnosis here rests on the owner's live memory and local source, not merely on
similarity to those reports.

## Implemented pathfinding candidate

- `PathfindCellInfo::allocateCellInfos(capacity=30000)` supports a measured pool size
  and exposes capacity/free-count/allocation-failure counters for opt-in runtime tests.
- In the first `Pathfinder::newMap()` allocation, only Zero Hour **GAME_SKIRMISH,
  >8 occupied players, no Network** reserves 30,000 plus every allocated ground,
  bridge and wall cell. It allocates before classification owns records, preserves
  record addresses throughout play, and retains the second-map-load sequencing.
- This mode enables the engine's existing fixed list/parent/obstacle handling from
  the start, rather than waiting for a crash-triggered fallback. In fixed allocation
  mode obstacle properties live on the cells, reducing persistent pool pressure.
- Legacy/<=8-player games keep capacity 30,000 and their initial retail behavior.
  Each new map selects capacity anew. No network packet or slot format changes.
- `LOCAL_PATHFIND` logs measured capacity/free/failures. `LOCAL_GROUND` logs vehicle
  object IDs and coordinates, excluding aircraft/structures, every 900 frames to
  frame 36,000. `verify_ground_movement_log.py` checks actual coordinate changes
  after seven game minutes, all nine AI combat-vehicle movers, late movement and
  zero allocation failures. A moving state flag alone cannot pass this check.

The original old executable and launcher were retained during validation. Rebuilding
does not patch an already-running match. Use a new versioned executable and a new
match for verification. Do not present a live-session recovery as tested.

## Desert 5v5 map prototype: Amber Canyon v4

The generator is committed; proprietary generated maps/textures/models are kept
privately. The owner chose desert, mountains and rocky passes.

`scripts/build_five_aside_desert_map.py` uses texture metadata/object prototypes from
the owner's existing 600x600 map, replacing heights, paint, objects, routes and water:

- Five west starts at x=900 and five east starts at x=5100; y=700,1850,3000,4150,5300.
  Minimum separation 1,150; build-pad radius 475 world units; graded transitions.
- Two central mountain masses; three broad passes at y=1050,3000,4950; flank routes
  at y=480/5520 and rear/forward connecting routes.
- 38 supply docks: 20 home, 10 forward, eight contested; six neutral tech buildings
  (four oil derricks, hospital, refinery); ruins and 124 rock decorations kept away
  from traffic/resources. Five existing terrain classes, 1,183 two-texture blends.
- 30 native AI routes: `Center1..10`, `Flank1..10`, `Backdoor1..10`. Each has eight
  vertices; 250 unique waypoints overall and 210 links.
- **Route direction is inbound toward the labelled base.** The native
  `doTeamFollowSkirmishApproachPath` selects an enemy start index, then follows its
  outgoing links. v2/v3 had outgoing routes and were superseded; don't revive them.
- Static terrain audit connected all 294 start/resource/tech/route sites with
  20-world-unit cliff clearance and rejected resource/tech waypoint overlap.
  This is a terrain heuristic, not a substitute for engine vehicle paths.
- `-localfiveaside` sets fixed starts and teams by slot/5; `-localhardai` selects
  `SLOT_BRUTAL_AI` (the UI's Hard Army). For this opt-in team mode only, depot search
  also considers allied depots to avoid stacking on a teammate's developed dock.

Current private candidate:
`maps/AmberCanyon_5v5_v4/AmberCanyon_5v5_v4.map`, SHA-256
`3bf06fdd17d8a57222f2520a9ea7f9bd1ada19abb3e9e1a95a891f368b44f7a1`.
v1–v4, layout JSON, map.str, plan PNG and minimap TGA are preserved. A staged copy is
under private Wine Documents/Maps. `work/render_amber_plan.py` in the Codex working
directory produced the plan/minimap; it is a supporting private utility, not engine code.

Before the ground fix, `generalszh-five-aside-v3.exe` ran v4 with one idle human and
nine Hard Army AI, seed 12345, 10,000 credits. It reached frame **18,000 (10 minutes)**.
Controller/team/economy/second-depot checks passed; all AI had at least some recorded
frontline presence or kills during the run. That verifier counted all combat units,
so this does **not** prove all vehicles attacked. Neutral tech ownership stayed zero
for every AI. Autonomous capture/use of all tech is **not validated**.

WorldBuilder accepted the generated file and reported objects, but captured editor
viewports were black; visual quality was not established. The owner paused polishing
for the vehicle stall. This is a playable test candidate, not a finished professional map.

## Build, run and verify

```bash
cd /home/hazem/projects/GeneralsGameCode
bash scripts/docker-build.sh --target z_generals
# Shared changes should also compile for the original game:
bash scripts/docker-build.sh --target g_generals --jobs 2
```

Never add `--clean`. Do not run two Ninja builds in the same directory concurrently.
Preserve old executables; stage the output under a new name in the private
`runtime/ZeroHour` directory. The extracted local GUI assets must accompany it.

Private `launch-gpu-test.sh` runs Docker/Wine with the asset mount read-only and
Intel renderD128. It takes an executable/argument string and a timeout in seconds
(0 means unlimited). Owner launcher `play-ten-skirmish.sh` opens editable ten-row
setup. Owner output shortcuts currently refer to that launcher.

For new validation, use **a separate Wine prefix**. Parallel sessions with the shared
prefix can overwrite `Replays/00000000.rep`, Skirmish.ini and caches. The new copied
prefix `wineprefix-vehicle-test-20261014` and launcher `launch-vehicle-validation.sh`
isolate those writes from the owner. Keep the clone and all logs.

Direct diagnostic launch options (quote the full Windows map path):

```text
-headless -quickstart -localskirmish "FULL_TENBASES_MAP_PATH.map" 10
-headless -quickstart -localfiveaside -localhardai -localskirmish "FULL_AMBER_V4_MAP_PATH.map" 10
```

`-localskirmishtestfps 120` optionally accelerates **direct CLI** testing by requesting
120 updates per second through the normal new-game message, skipping no logic frames.
Default remains 30; editable setup/normal GUI use their chosen speed. In these release
builds `-fps`, `-noFPSLimit`, `-jumpToFrame` are debug-only options: don't assume they
accelerate a run just because they were passed. Judge elapsed game time by logged
frame numbers (1,800 frames = one simulated minute).

`-localskirmishtestcash 50000` explicitly sets diagnostic starting credits (accepted
range 1–1,000,000). Without that flag the direct shortcut retains its 10,000-credit
default; editing the private Skirmish.ini alone does not change the shortcut's cash.

```bash
python3 scripts/verify_local_skirmish_log.py LOG --minimum-frame 27000 --economy --expansion
python3 scripts/verify_local_skirmish_log.py AMBER_LOG --minimum-frame 27000 --economy --expansion --five-aside --hard-ai
python3 scripts/verify_ground_movement_log.py LOG --minimum-frame 27000 --late-frame 12600
```

For legacy capacity use a direct <=8-player smoke test and inspect `LOCAL_PATHFIND`:
capacity must be 30,000. Test serializer integration output separately. Headless tests
bypass input, graphics and audio; visible human-controlled vehicle movement must be
checked separately. Timeouts do not finalize a replay or prove a completed match.

## Exact checkpoint evidence and next steps

See [checkpoint validation](docs/research/vehicle-stall-checkpoint-2026-10-14.md) for
the final build hashes, observed frame counts and pass/fail results for this commit.

1. Confirm late vehicle movement on both TenBases and Amber v4, then manually test
   a human dozer and tank after the old 7–11-minute failure interval. Test load/reset
   into a <=8-player game after a ten-player match. Save/load remains unverified.
   At the owner's stop, the final candidate had reached only frames 9,000/11,700.
   Amber's strict battle check failed because slot 2 had not reached combat. Read
   the checkpoint evidence before making any success claim.
2. Only after validation, update a **private** owner launcher to the new versioned
   executable, preserving its prior contents. A running old match needs a new match
   to use the fix. Do not overwrite the Windows installation.
3. Resume Amber terrain/texture visual review in the actual game. Inspect wide
   passes, base exits, resource traffic, team expansion, approach-path endpoints and
   attacks from every Hard Army faction. Verify ground, not just infantry/aircraft.
4. Investigate native AI neutral-tech capture priorities and any remaining camped
   attack teams. Do not inject free structures/units as a substitute for working AI.
5. Run longer/multiple-seed matches and difficulty/faction combinations. Finish a
   real match and test replay/save/load. Then document additional validated claims.

To push on this machine, the existing owner GitHub CLI authentication works without
changing global credential configuration:

```bash
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin feat/skirmish-ten-players
```

Do not print credentials or tokens. Do not force-push. The commit that introduces
this checkpoint is discoverable with `git log -1 -- HANDOFF_TEN_PLAYERS.md`; the
previous feature checkpoint is the full hash above.
