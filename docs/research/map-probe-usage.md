# Using the Generals map-size probe

The repository now includes a **read-only** Python 3 utility that extracts stored and playable dimensions from uncompressed CkMp `.map` files.

```bash
cd /home/hazem/projects/GeneralsGameCode
python3 scripts/map_probe.py "/path/to/Twilight Flame.map"
python3 scripts/map_probe.py --json "/path/to/maps-directory"
python3 -m unittest discover -s Tests/MapTools -p 'test_*.py' -v
```

Output distinguishes internal heightmap dimensions from **playable size**, subtracting twice the non-playable border from each dimension.

## Audit status

- The map editor passes user-provided X/Y dimensions to the map construction code without a local explicit maximum check.
- The binary `HeightMapData` chunk records the 2D dimensions and border.
- `W3DShroud` computes the fog data extent dynamically but relies on the Direct3D texture-cap validation path, so **GPU texture size and in-game clipping must be tested**.
- C&C Labs' community discussion reports >400×400 maps are possible, and cautions that 1000×1000 can cause serious performance and loading problems. These are historical anecdotal reports, not verified engine constraints. Source: https://www.cnclabs.com/forums/posts/7324/zero-hour--world-builder/
- **Absolute maximum map dimensions are unknown** until runtime testing. Do not promote 1000/1024/2048 as a verified cap.

### Testing sequence

1. Obtain a known original `.map` for Twilight Flame and measure its exact stored/playable dimensions with the script; **none was present in the inspected Ubuntu home directory** as of 2026-10-13.
2. Find a working Zero Hour + WorldBuilder runtime. Wine was not found on the Ubuntu PATH and no executable was found within the scanned home directories. A Windows installation may exist on a currently unmounted partition.
3. Test 600×600, 700×700, 800×800 and 1000×1000 maps individually. Record: successful load, full map camera travel, fog/radar, pathfinding corner-to-corner, sim FPS, RAM and load time.
4. After the map is stable, start 10-player skirmish modifications.

No large downloads, dependencies or Docker build were performed. Disk cleanup is out of scope, handled by a separate agent.
