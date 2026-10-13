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
