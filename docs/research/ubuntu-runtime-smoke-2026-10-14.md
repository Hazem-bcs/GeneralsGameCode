# Ubuntu runtime smoke tests — 2026-10-14

## Purpose
Determine whether the source-built Zero Hour executable and experimental large maps can be launched on the user's Ubuntu laptop. This report separates **file-format checks** from **actual in-game validation**.

## Confirmed local setup
- Project: `/home/hazem/projects/GeneralsGameCode`, branch `research/player-limits`.
- Build artifacts: `build/docker/GeneralsMD/generalszh.exe` and `WorldBuilderZH.exe` (32-bit Windows PE binaries).
- Existing game data, around 4.8 GiB, is mounted read-only from Windows NTFS under `/media/hazem/OS/Program Files/EA Games/Command and Conquer Generals Zero Hour/Command and Conquer Generals Zero Hour`.
- Test-only staging: `/home/hazem/projects/generals-extended-tests/runtime/ZeroHour`. Assets are linked read-only to original Windows data; test EXEs are copied to `Data`. No modifications were made to the Windows installation.
- Three generated maps (playable sizes 600x600, 800x800, 1000x1000): `/home/hazem/projects/generals-extended-tests/maps`. The uncompressed `CkMp` structures were validated by `scripts/map_probe.py`. They were also staged with copies of the original map's TGA preview in an isolated Wine user's Documents/Maps folder. **Maps are experimental extensions, not polished layouts; all original unit locations are unchanged.**
- The map probe successfully read 303 installed custom maps: largest found playable map was 670x670, whereas the installed Twilight Flame Edit was 490x490.

## Runtime observations
1. Docker image `zerohour-build:latest` has Wine 11.0 but lacked Linux `libGL.so.1`, `libvulkan.so.1` and Mesa software DRI libraries. Initial launch logged `Failed to load libvulkan.so.1`. The image is a *build* image and not by itself a complete graphics/runtime test environment.
2. Staging the host's x86_64 graphics libraries read-only into the container removed the Vulkan library error, but **did not resolve a compiled executable crash**. The built `generalszh.exe` created a "Command and Conquer Generals" X11 window, but immediately reached `EXCEPTION_ACCESS_VIOLATION` with EIP around `0x0010FFF8` and repeated exception dispatch eventually causing `EXCEPTION_STACK_OVERFLOW`. The game menu was **not** verified.
3. Adding a separate test-only `options.ini` with a 1024x768 resolution did not resolve the crash.
4. Built `WorldBuilderZH.exe` initially refused to load because `MFC42.DLL` was missing. Copies of the owner's own 32-bit Windows `mfc42.dll`, `msvcp60.dll`, `msvcirt.dll` were staged into the private runtime directory (never committed). The built editor subsequently exited with code 99; successful UI startup was not established.
5. As a comparison, a copy of the owner's original retail `Game.dat` was launched under the same Wine environment as `RetailGame.exe`. It opened a "Technical Difficulties..." dialog and exited with status 1. This suggests the Wine staging still has problems independent of the compiled game; the exact causes remain unresolved. The original retail WorldBuilder process did not complete its first 16-second smoke test and its usable UI was not verified.
6. A test-only `ReleaseCrashInfo.txt` reported "Uncaught Exception during initialization."

## Conclusion / next experiment
- **No large map has yet been loaded in a real game**, so there is no verified runtime maximum.
- Before editing map limits, establish a **working baseline** with either a properly installed native Wine environment (graphics + runtime/registry) or a safe native Windows test environment. Prefer the already installed licensed game data instead of downloading it again.
- When baseline works: load Twilight Flame Edit as a control, then 600x600, 800x800, and 1000x1000 in order. Verify camera corners, fog/shroud, minimap, pathfinding, and crashes. Test with only 8 players until map scaling is proven.
- No major package downloads and no Docker image rebuilds were performed in these tests. Treat Win32 compatibility and gameplay debugging as separate tracks. Windows volume remains read-only.
