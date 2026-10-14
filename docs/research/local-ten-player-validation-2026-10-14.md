# Local ten-player Zero Hour — 2026-10-14

Scope: one local human plus nine Skirmish AI players. This is a tested development
build, not a claim of complete retail compatibility, competitive balance, or long-match stability.

## Implementation

- `MAX_PLAYER` remains 7 and `MAX_SLOTS` remains 8. Connection numbering, packet
  arrays, relay masks and network replay disconnect flags are unchanged.
- `GameInfo::getSlotCount()` defaults to eight; local Skirmish and replay objects
  have storage for ten. Slot enumeration, player creation, alliances, randomized
  factions/colors/start positions and slot-to-player lookup follow the instance capacity.
- Local Skirmish adds two palette choices without changing the normal online
  `getNumColors()` result. A fifth team is available locally.
- Local save snapshots use version 5 and can read the older eight-slot snapshots.
  Save/load round trips have not been verified in a running match.
- Map metadata reads `Player_9_Start` and `Player_10_Start`. User map caches record
  the scanning capacity and automatically rescan old entries once. Original Windows
  cache files are not edited. Keep the private cache backup when running old builds.
- Ten-row Skirmish options, ten map-selection start controls, a separate local
  loading layout and ten-row local diplomacy popup are generated from the owner's extracted retail layouts. Proprietary
  game assets, executables and maps are not included in this repository.

## Crash investigation

The inherited ten-player prototype reproduced a stack-overflow report in Wine.
The recorded exception trace starts with an access violation, followed by recursive
exception handling; increasing stack size would not address that first error.

The old VC6/Ninja configuration generated GCC-style dependency rules, but the VC6
compile commands emitted no depfiles. Changing GameInfo.h had only relinked the
executable in the last inherited build. This made header-only experiments unreliable.
A coherent rebuild translated 1,089 build steps and successfully played the baseline
replay. The Docker build helper now fingerprints headers and refreshes source timestamps
when they change, preserving old outputs and requiring no directory cleanup.

After extending the instance capacity, a real ten-player match crashed at the ninth
slot. Its first access violation was at `0x004bba83`; the disassembly called the player
lookup with slot index 8, returned null, then read offset 0x24. The reverse lookup array
`PlayerList::m_slotToPlayerIndices` still held eight entries. Extending that **local
lookup** to ten resolved this crash. An eight-player control on the same 600x600 map
had already reached frame 900.

A CLI shortcut initially pushed the setup layout before startup completed and produced
a black screen. Both setup and direct match startup now wait until the intro finishes;
the direct path configures the game immediately before sending the new-game message.
Serializer checks were independently shown to pass.

## Runtime evidence

All runs use Docker image `zerohour-runtime-gl`, the isolated Wine prefix under
`/home/hazem/projects/generals-extended-tests`, and Intel render node `renderD128`.
The Windows asset tree is mounted read-only. No NVIDIA configuration was changed.

- Inherited prototype: stack overflow reproduced.
- Coherent eight-slot/virtual-method build: old `BaselineNuke.rep` played for 35 seconds
  without a stack-overflow report.
- Eight occupied slots on `TwilightFlame_600x600_10Players`: frames 150 and 900; unique
  players, colors and starts; initial objects for every player; no Network instance.
- Ten occupied slots, direct CLI launch: frames 150, 900 and 3600. Slots 0–9 mapped to
  actual players 2–11, ten distinct starts and colors, and initial objects for every slot.
  At frame 3600, slots 8/9 owned 12/13 objects (up from 3/3 at frame 150).
- GUI launch: all ten rows and ten map markers visible. The last row's color dropdown
  opened. A match started from the setup screen and reached frames 150, 900 and 3600.
  Runtime checks confirmed one actual local human and nine actual Skirmish AI controllers.
  At frame 3600 slots 8/9 owned 14/13 objects. Graphics showed gameplay and radar.
- In-game diplomacy now has ten rows. Pressing Tab on the final build showed the
  human and all nine AI armies, each with status Playing. The previous eight-row
  popup could conceal two armies even though they existed in the simulation.
- Serializer integration checks: ten-slot round trip passed; the eight-slot control
  rejected the ten-slot string; eight-slot serialization and import into the ten-slot
  object passed, with the two additional slots closed.

`local-ten-v2-smoke.log`, `local-ten-gui-fix.log`, screenshots and verified JSON results
are retained in the private test directory. The duration-limited runs are intentionally
terminated at their timeout; that does not constitute a completed match or clean replay
finalization. Wine reports audio/COM warnings in this environment.

## Reproduction

Build without cleaning:

```bash
bash scripts/docker-build.sh --target z_generals
```

Generate all four local layouts into a new directory, then stage them privately in
`Window/Menus`. Input directory contains the extracted original files
`SkirmishGameOptionsMenu.wnd`, `SkirmishMapSelectMenu.wnd`, `MultiplayerLoadScreen.wnd`,
`Diplomacy.wnd`. Stage `SkirmishDiplomacy.wnd` in `Window/`, the other three in `Window/Menus/`:

```bash
python3 scripts/extend_local_skirmish_assets.py INPUT_DIRECTORY NEW_OUTPUT_DIRECTORY
```

The map helper refuses to overwrite a map; defaults are calibrated for the existing
experimental 600x600 map:

```bash
python3 scripts/extend_map_player_starts.py SOURCE_600_MAP NEW_TEN_START_MAP
python3 scripts/build_ten_base_map.py TEN_START_600_MAP NEW_TEN_BASE_MAP
```

Executable options (map is the full Windows path in the private Wine Documents folder):

```text
-quickstart -localskirmish "FULL_MAP_PATH.map" 10
-quickstart -localskirmishsetup "FULL_MAP_PATH.map" 10
```

The first runs the same new-game message path as the Start button. The second opens
editable setup after the startup sequence. Both retain release-build diagnostic output
and the deterministic initial seed 12345; ordinary GUI sessions use their normal seed.
The setup shortcut loads the existing preferred starting cash and game speed.

Validate observations, not merely a successful build:

```bash
python3 scripts/verify_local_skirmish_log.py LOG_FILE --minimum-frame 9000 --economy --expansion
```

## Limits and follow-up

The new map is a redesigned ten-base test battlefield. Competitive balance has not
been established. No full-match,
network interoperability, save/load, or 12/16-slot claim is made. The network protocol
is still eight slots; a source-compatible rebuild is required for changed class layouts.
The original Generals target (`g_generals`) also compiled successfully after the
shared-header changes; its gameplay was not tested.

Generated GUI assets must accompany the executable. Extended replays/saves should be
used with this development build, not the original retail executable.

All inherited modified/untracked sources and the resume executable were backed up at
`/home/hazem/projects/generals-extended-tests/patch-backups/codex-resume-20261014-015048`.
Old test artifacts and the original Windows game remain in place. Additional private
cache and replay backups are retained beside those backups.

## Owner launcher

Run `bash /home/hazem/projects/generals-extended-tests/play-ten-skirmish.sh`.
This opens ten-row setup on `TwilightFlame_TenBases_v1` using `generalszh-ten-final.exe`, with no test
timeout. Click PLAY GAME. Press Tab during gameplay to see all ten Playing entries.
The local launcher preserves the owner's selected starting cash/game-speed preferences.

The replay observer army-selection panel remains limited to eight visible buttons;
use in-game diplomacy for ten-player verification. It is a follow-up UI item, not
a limit on the ten active local player controllers.

## Ten-base terrain and AI expansion

The owner reported that some armies built initial buildings then stopped. Object
counts alone in the initial smoke tests did not establish a working economy.
The old two added starts lacked redesigned local supply access and construction space.

`build_ten_base_map.py` creates a separate `TwilightFlame_TenBases_v1` variant:

- Ten starts evenly spaced on a ring (minimum separation approximately 1,329 world units).
- Each base has a graded build pad of radius 500 with a smooth transition, two nearby
  supply docks, and access to graded radial/ring routes. Obstructions in the clear areas
  are removed. Old cliff flags/blends on graded cells are cleared.
- Ten additional expansion docks sit inside the ring. Total supply docks: 30.
- 204,910 height cells were graded; 371 old docks/obstructions were replaced/cleared.
  The input map and original Windows files remain untouched.

Before the AI expansion supplement, the new map alone reached frame 9,000 with all
nine AI earning supplies and producing combat units. Both extra slots registered kills
(3 and 1). All nine AI still had just one supply center at that observation.
The verification helper deliberately rejects that log when `--expansion` is requested.

Matches with more than eight occupied players, GAME_SKIRMISH, and no Network now
budget for up to three supply centers per AI. Checks start after two game minutes,
once per 30 seconds with staggered player offsets. A 3,000-credit reserve remains
above construction cost; pending/in-progress depots prevent duplicate requests.
The existing `buildBySupplies` search selects resource sites using distance, remaining
supplies and enemy proximity, and the normal dozer/worker construction queue builds
and funds them. A final terrain/path/overlap check rejects impossible local expansion
orders instead of enqueuing an invalid location. Network and <=8-player matches
retain their existing AI behavior.

Runtime diagnostics count completed depots, resource income, harvesters, military
units, production and kills. The verifier now checks continued income, actual combat
units and completed second depots for every AI when those options are requested.
Negative controls with zero income/no military and the one-depot baseline are rejected.

Final exact executable: `runtime/ZeroHour/generalszh-ten-final.exe`, SHA-256
`b5ac37b96a280a74ed23f701f72ea078a9d80e742568b2f8884f79bafe168725`.
The Zero Hour build passed after the final >8-occupied-player gating change.

The exact final executable ran with `-headless -quickstart -localskirmish MAP 10`:
10,000 starting credits, seed 12345, nine Easy AI with mixed factions, no human input.
Frames 150, 900, 3600 and 9000 were observed (five simulated minutes). The completed
supply-center count was 2–3 for **every** AI; income continued increasing from frame
3600 to 9000; all nine fielded combat units. The extra slots 8/9 had 3 completed supply
centers each, earned 15,600/16,800, produced 13/11 units and registered 3/5 kills.
The strict economy/expansion verification passed. No stack-overflow/access violation
or Network instance was recorded. This run was stopped after the required observations.
Headless bypasses graphics/input/audio; prior visible new-map runs established rendering.
The attempted `-jumpToFrame` shortcut is debug-only and was not used as acceleration
evidence for the release build.

| AI slot (one-based UI row) | Completed supply centers | Harvesters | Income earned | Units built | Kills |
|---|---:|---:|---:|---:|---:|
| 2 | 3 | 9 | 15600 | 14 | 2 |
| 3 | 2 | 4 | 15000 | 8 | 3 |
| 4 | 3 | 9 | 18600 | 16 | 0 |
| 5 | 2 | 6 | 16200 | 15 | 0 |
| 6 | 3 | 15 | 14850 | 19 | 3 |
| 7 | 3 | 18 | 17475 | 23 | 0 |
| 8 | 2 | 6 | 16800 | 10 | 4 |
| 9 | 3 | 8 | 15600 | 13 | 3 |
| 10 | 3 | 5 | 16800 | 11 | 5 |

The additional 30-second economy check is supplemental to faction scripts; it does
not prove all difficulty/faction/map combinations or a complete match. One army's
combat units had been destroyed at the last snapshot but it had already fielded units,
registered four kills and retained six harvesters/two depots.

Final visible checks on the same executable: the legacy two-player `BaselineNuke.rep`
rendered actual play at replay time 00:23, with buildings under construction. The updated
owner launcher opened ten setup rows and ten start markers on `TwilightFlame_TenBases_v1`.
PLAY GAME started a match using the owner's 50,000-credit / speed-60 preferences;
frames 150 and 900 passed the controller/slot verifier. Tab displayed ten Playing rows.
The match was left open for the owner. `map.str` includes a non-missing intro label and
credits the source-map creators. The private launcher points to `generalszh-ten-final.exe`.
