# Map dimensions audit — Generals Zero Hour

Research date: 2026-10-13
Branch: `research/player-limits`
Scope: static inspection of this repository only; **no large-map runtime tests yet**.

## Findings

1. **Twilight Flame is not proven to be the engine's maximum map size.** The community's original-map reference is approximately 460 × 480; that is a map-specific size, not a code-enforced engine ceiling. Source: C&C Labs Zero Hour 8-player maps listing, description for Twilight Frost (300 × 300 vs TF 460 × 480).
2. **The WorldBuilder new/resize dialog does not impose an explicit maximum on X and Y in its `OnOK` method.** Both are parsed with `atoi`. Source: `GeneralsMD/Code/Tools/WorldBuilder/src/NewHeightMap.cpp:189-212`.
3. **WorldBuilder map creation uses variable dimensions.** `WorldBuilderDoc.cpp:1246-1252,1285-1290` obtains `xExtent` and `yExtent`, then constructs `WorldHeightMapEdit`. In `WHeightMapEdit.cpp:91-117`, the internal grid width and height each gain `2 * border`, and arrays are sized using `width * height`.
4. **The map format stores dimensions as 32-bit integers.** Writer: `GeneralsMD/Code/Tools/WorldBuilder/src/WHeightMapEdit.cpp:577-599`. Reader: `Core/GameEngineDevice/Source/W3DDevice/GameClient/WorldHeightMap.cpp:872-901`. There is no explicit 512/1000/1024 dimension check in these shown writer/reader functions. This is **not** proof arbitrarily large maps work.
5. **Rendering / fog-of-war is a key risk.** `GeneralsMD/Code/GameEngineDevice/Source/W3DDevice/GameClient/W3DShroud.cpp:65-68` has a **commented-out** 1024 maximum and `DEFAULT_TERRAIN_SIZE 1024` described as an assumption, not a validated hard cap. `W3DShroud.cpp:117-170` computes dynamic cell counts but creates a destination texture, calling `TextureLoader::Validate_Texture_Size`. In `Core/Libraries/Source/WWVegas/WW3D2/textureloader.cpp:354-413`, dimensions are rounded up to powers of two and capped at the current Direct3D device's maximum texture dimensions. We need runtime tests to ensure no truncation / missing fog data.
6. **Radar is fixed-resolution but maps world coordinates to a variable extent.** `Core/GameEngine/Include/Common/Radar.h:53` sets the radar to 128 cells wide; `Core/GameEngineDevice/Source/W3DDevice/Common/System/W3DRadar.cpp:200-201` maps world coordinates using `m_mapExtent.width()/height()`. Large maps will reduce minimap detail; a 128-cell radar is not itself a map-size limit.
7. **Pathfinding and partitioning have dynamically allocated areas.** `Core/GameEngine/Source/GameLogic/AI/Pathfinder/PathfindLayer.cpp:198-230` allocates cells from computed extents; `GeneralsMD/Code/GameEngine/Source/GameLogic/Object/PartitionManager.cpp:2685-2700` derives partition cells from world extents. This suggests scaling with map area, with memory/CPU risks, not a demonstrated fixed limit.
8. **The WorldBuilder has a 3000 placed-object limit** in `GeneralsMD/Code/Tools/WorldBuilder/include/WorldBuilder.h:69`, checked in `src/CUndoable.cpp:284-286`. This is an editor-object limit, **not** necessarily a cap on units built during gameplay.

## Map-size experiment matrix

Use **playable/editor X,Y sizes**, and record border width separately, because internal heightmap dimensions add 2 × border on each axis.

| Stage | Playable dimensions (cells) | Relative area vs Twilight Flame 460×480 | Purpose |
|---|---:|---:|---|
| Baseline | ~460 × 480 | 1.00× | Compare Twilight Flame |
| A | 600 × 600 | 1.63× | First low-risk large-map trial |
| B | 700 × 700 | 2.22× | Room for 12–16 armies, subject to actual layout |
| C | 800 × 800 | 2.90× | Test loading, AI movement, shroud, minimap |
| D | 1000 × 1000 | 4.53× | Stress test, not an established maximum |

Test each map first with a clean 8-player setup, then add AI slots only after the map works. Verify full camera travel to all map corners, buildable regions and start positions, fog and minimap, units moving end-to-end, loading and saving, simulation FPS, and memory usage.

## Practical caveats

- No code evidence yet proves the **absolute maximum** dimensions that the game can reliably load.
- Enlarging a map alone **does not** increase the eight-player match setup.
- The user's phrasing “against 12 or 16 players” literally means 13 or 17 total players including the human, not 12/16 total; that increases the eventual player-slot engineering scope.
- Initial local checkout occupies ~111 MiB. At clone time only ~5.3 GiB was free on the Ubuntu root filesystem (97% used). **Do not install full Docker/vcpkg build dependencies or attempt a big build before checking disk requirements.**
- Repeated community reports mention 1000×1000 test maps, with serious load/performance concerns; treat as anecdotal, not a verified engine boundary.

## Next

1. Establish a runnable Zero Hour baseline and WorldBuilder environment.
2. Create **one** unmodified-engine 600×600 8-player map (with border) and test camera/minimap/pathfinding.
3. Try 700×700 and 800×800 in ascending order.
4. Document the highest **tested working** dimensions before editing the engine.
5. Only after map feasibility, audit the skirmish player-slot data structures and AI to exceed eight.
