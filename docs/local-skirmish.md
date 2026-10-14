# Ten-player local Skirmish

This Zero Hour change supports one local human and up to nine AI armies through
the existing Skirmish menus. Network games retain their eight-slot protocol.
Generals retains eight local slots. No new runtime classes or subsystems are added.

## Implementation

- `GameInfo::getSlotCount()` keeps the network default at eight; `SkirmishGameInfo`
  and `ReplayGameInfo` provide local capacity. Player lookup, map starts, colors,
  loading, diplomacy and the Skirmish menus use that capacity.
- The map cache reads `Player_9_Start` and `Player_10_Start`. A capacity marker
  invalidates caches created by older eight-slot readers.
- The local extended-match pathfinding pool covers allocated map/layer cells.
  Its addresses remain stable during a match. Existing fixed pathfinding is
  selected before classification, including playback of local Skirmish recordings.
  Ordinary eight-player and network matches retain their original pool capacity.
- Skirmish snapshots use version 5 and an explicit saved slot count. The loader
  accepts older eight-slot snapshots and closes the two additional slots.
  Older executables cannot read new ten-slot snapshots.

The change does not modify AI production, expansion rules, unit limits, build
speeds or terrain. It adds no startup automation, global test options, automatic
movement commands, periodic world scans or per-vehicle logging.

## Local interface assets

Use a licensed installation of Zero Hour. Extract these original layouts into
one temporary directory: `SkirmishGameOptionsMenu.wnd`,
`SkirmishMapSelectMenu.wnd`, `MultiplayerLoadScreen.wnd`, and `Diplomacy.wnd`.

Run:

```sh
python3 scripts/extend_local_skirmish_assets.py ORIGINAL_LAYOUTS NEW_LAYOUTS
```

The output contains ten-row Skirmish setup/map selection and separate
`SkirmishLoadScreen.wnd` and `SkirmishDiplomacy.wnd` layouts. Stage the first three
in the private game's `Window/Menus` directory and the diplomacy layout in
`Window`. Preserve original files. Generated assets are not distributed in Git.
The binary requires these matching layouts; it is not a drop-in retail replacement.
A ten-player map must contain all ten `Player_N_Start` waypoints.

Start the game normally, open Single Player / Skirmish, choose the map and set
nine AI opponents. For 5v5 choose one team for the human and four AI, and another
for the remaining five AI. The engine does not hard-code a particular map or seed.

## Files introduced by this contribution

Runtime changes extend existing engine files. The new supporting files are:

| File | Purpose |
| --- | --- |
| `scripts/extend_local_skirmish_assets.py` | Generate the four private local layouts |
| `scripts/extend_skirmish_layout.py` | Reusable setup-layout transformation |
| `scripts/prepare_vc6_rebuild.py` | Refresh source timestamps when legacy VC6 header dependencies change |
| `docs/local-skirmish.md` | Scope, integration and verification notes |

The preserved `feat/skirmish-ten-players` prototype branch contains map generators,
AI experiments, diagnostic flags and historical evidence. Those are deliberately
excluded from this focused contribution. Existing ten-player prototype saves and
replays may use different AI rules; compatibility with that experimental branch
is not promised.

## Verification boundaries

Build both `z_generals` and `g_generals` after shared changes. Existing replay tests
remain the compatibility baseline; additionally exercise a fresh ten-player match,
its save/load cycle and its replay. Check ten setup/diplomacy entries, distinct
starts/colors, ordinary eight-player behavior and continued ground movement.
Frame time and simulation speed require separate measurement. Refactoring does
not establish that late-match performance is fixed.

### Cleanup validation, 2026-10-14

- Both VC6 release targets (`z_generals`, `g_generals`) build successfully.
- Private layout generation produces the expected ten controls per category,
  preserves all four input files, and rejects overwriting existing outputs.
- The ordinary Zero Hour UI displays ten player rows and all ten start markers
  on a ten-player map. A new complete match/save/load/replay cycle is still open.
- A retained legacy replay fails its CRC at frame 2913 with both this build and
  the preserved pre-ten-player executable in the same isolated Wine environment.
  This is a failed compatibility check, not a claimed passing regression test.
- No runtime performance improvement is claimed by this cleanup.
