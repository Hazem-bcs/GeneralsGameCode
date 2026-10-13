# Building and testing Hazem's Zero Hour fork on Ubuntu

Updated 2026-10-13. All commands below refer to branch `research/player-limits` and the verified local checkout.

## What the source repository contains

The GitHub repository contains engine and tool source code, **not** the complete copyrighted game assets. The original EA Zero Hour installation provides maps, models, textures, music, sounds and other runtime files. Building code does not create these assets.

### Verified local machine

- Ubuntu 24.04 x86_64.
- Source checkout: `/home/hazem/projects/GeneralsGameCode`
- Docker 29.3.1 running.
- Original Windows EA installation mounted **read-only** at `/media/hazem/OS`.
- Game folder:
  `/media/hazem/OS/Program Files/EA Games/Command and Conquer Generals Zero Hour/Command and Conquer Generals Zero Hour`
- This is an EA installation with extra GeneralsOnline/mod-related files. Do not overwrite any original executable or attempt modifications while the Windows NTFS volume is mounted read-only.
- Wine was **not** installed on Ubuntu's PATH during the initial check. The Docker builder includes Wine internally for compilation, **not** as a host game launcher.

## Build only Zero Hour

```bash
cd /home/hazem/projects/GeneralsGameCode
git switch research/player-limits
git pull --ff-only origin research/player-limits

# Requires substantial spare disk for the initial Docker image.
# This compiles a Windows EXE while running Docker on Ubuntu:
./scripts/docker-build.sh --target z_generals

# Optional: build the Windows World Builder application too:
./scripts/docker-build.sh --target z_worldbuilder
```

Outputs *if the build succeeds*:

- `build/docker/GeneralsMD/generalszh.exe`
- `build/docker/GeneralsMD/WorldBuilderZH.exe`

The first Docker build creates a large toolchain image. Future incremental builds reuse Docker image/cache. **Do not use `--clean` casually.** On a nearly full filesystem, postpone building.

## How runtime testing works

**Option A: Windows test.** Reboot into Windows and use a *separate test copy* of the EA game install; place the built executable in the appropriate game directory. Keep the source game's launchers and executables untouched and back them up. The built executable must be tested with a compatible set of original game data/DLLs. Copying only the source code does not make a runnable game.

**Option B: Ubuntu test.** Install Wine (system administration required) and create a separate writable staging directory containing a compiled binary and access to the game data files, then launch with Wine. A test Wine prefix and launcher settings may be required. Do not attempt to run the executable from a read-only original Windows install as if it were a writable game folder.

**Note:** Review `scripts/docker-install.sh` before using it with EA's current installation. It assumes the executable belongs under `GAME_DIR/Data`, whereas this particular Windows game installation has `Generals.exe`, `Game.dat` and `WorldBuilder.exe` at the root; the automated path assumption may be incompatible. Do not use it against this original installation without adapting and testing it.

## Current experimental maps

Original Twilight Flame was extracted from the *owned local installation's* `MapsZH.big`, `EAR` decompressed and measured:
- stored heightmap `630 × 630`, border `70`, nominal playable grid `490 × 490`;
- **in-game boundary metadata** is approximately `486 × 469` (not identical to the nominal grid size).

Experimental CkMp map files (no original asset files have been committed to GitHub):

```
/home/hazem/projects/GeneralsMapTests/maps/TF_Expanded_600/TF_Expanded_600.map
/home/hazem/projects/GeneralsMapTests/maps/TF_Expanded_800/TF_Expanded_800.map
/home/hazem/projects/GeneralsMapTests/maps/TF_Expanded_1000/TF_Expanded_1000.map
```

Their new stored sizes respectively include the original 70-cell border on each axis: 740², 940² and 1140². The scripts preserve all original non-terrain chunks byte-for-byte and expand the terrain, blend and boundary data. **Only structural/format checks have passed. Runtime validation is still pending.** All old player starting positions remain clustered as in original Twilight Flame; these are size stress tests, not balanced 12/16-player maps.

## Tests and map tools

```bash
cd /home/hazem/projects/GeneralsGameCode
python3 -m unittest discover -s Tests/MapTools -p 'test_*.py' -v
python3 scripts/map_probe.py /home/hazem/projects/GeneralsMapTests/maps
```

The `scripts/map_unpack.py` helper decodes owned EA EAR/RefPack-compressed `.map` files. The `scripts/map_resize_lab.py` helper enlarges an **uncompressed** v4 CkMp map with v8 blend data and exactly one rectangular boundary; other input layouts are refused.

## Practical order of testing

1. Build and run an **unmodified game executable** in a separate game installation.
2. Test Twilight Flame baseline (nominal 490×490).
3. Test TF_Expanded_600, then 800, then 1000. Record load success, ability to traverse all corners with camera, new-build areas, AI pathfinding, radar and fog behavior, frame time, RAM and load time. If any test fails, stop and debug before larger dimensions.
4. Only after the large map works, patch player-slot and AI limits, then incrementally try 10 and 12 total players.

No source code changes to the game engine have been performed yet: only map-analysis and map-generation tools were added.

## Actual build result (2026-10-13)

**Both compilation targets succeeded** on Ubuntu 24.04 using `./scripts/docker-build.sh`:

| Target | Output | Bytes | SHA-256 |
|---|---|---:|---|
| `z_generals` | `build/docker/GeneralsMD/generalszh.exe` | 6,365,252 | `c9f186403e20c06a2741d90ae466b1de1b74d20bb486677067d94fdfd3a85525` |
| `z_worldbuilder` | `build/docker/GeneralsMD/WorldBuilderZH.exe` | 6,340,680 | `ad1a6535ce2c9e078cfc2d745076ed3ce0846bb4cb62ff74bf72838160071180` |

Both binaries were verified as **32-bit Windows GUI PE executables**. This is a build success, **not a runtime/playability validation**. No game engine player or map size limits have been changed.

An initial Docker image setup failed due to HTTP 500 on GitHub's MinGit asset; the build Dockerfile now retries and uses a checksum-verified fallback mirror. Later the source revealed missing type includes / PreRTS initialization in `Core/GameEngine/Include/GameLogic/Pathfinder/PathfindCellInfo.h` and three associated pathfinder translation units. These were fixed in the research branch, and compilation/links succeeded.

`python3 -m unittest discover -s Tests/MapTools -p 'test_*.py' -q`: **12 tests passed**.

Disk free immediately after both targets built was approximately **13 GiB** on the Ubuntu filesystem. Do not clean unrelated projects; disk cleanup is separately managed.

### Windows test installation guidance

To test on the user's already-installed Windows partition, first create a **separate Windows-side copy of the original Zero Hour game installation**, then stage the compiled `generalszh.exe` in that copy and test launch; do not overwrite `Game.dat`, `Generals.exe`, or `WorldBuilder.exe` in the original installation. Use a compatible original-data folder and a writable user Maps path. The game has not been launched on either platform during this build work, and Wine is not installed on the Ubuntu host PATH. This repository's Docker builder uses Wine internally for **building**, not for native gameplay.
