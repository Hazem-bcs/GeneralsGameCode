# Ubuntu GUI runtime progress — 2026-10-14

Branch: `research/player-limits`. This is a record of real **local** tests. None of the proprietary assets described below are committed.

## Runtime staging and fixes

Project checkout: `/home/hazem/projects/GeneralsGameCode`.

Private runtime staging: `/home/hazem/projects/generals-extended-tests/runtime/ZeroHour`.

- The screenshot assertion `INI::load, cannot open file Data\\INI\\Default\\GameData.ini` was caused by placing the compiled executable in a `Data/` subdirectory, resulting in a traced lookup for `.../Data/Data/INI/Default/GameData.ini`. Running the executable from the game **root**, beside `INIZH.big`, bypasses this error.
- `zerohour-build` is a *build* image without GL runtime libraries. A **separate** image named `zerohour-runtime-gl` was made with amd64+i386 Mesa OpenGL/EGL/Vulkan dependencies.
- A private Wine prefix was configured with the base Generals registry InstallPath pointing to `Z:\\work\\runtime\\ZeroHour\\ZH_Generals\\`.
- `Data\\English\\generals.csf` and `Language.ini` were extracted into the private staging directory from the owner's `EnglishZH.big`. A Wine `+file` trace **confirmed the game opens both files**, so blank shell-menu labels cannot be attributed simply to missing CSF files.
- Privately staged the owner's Windows Arial, Times New Roman, and Courier New TrueType fonts (~11 MiB) into Wine's Fonts directory, then registered them in `HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Fonts`. The private Language.ini was separately trial-modified from `UnicodeFontName = "Arial Unicode MS"` to `UnicodeFontName = "Arial"`, with a backup. **Neither operation conclusively resolved shell-menu labels.** The original Windows assets and font files remain untouched.
- The native Ubuntu XWayland display and integrated **Intel RPL-P GPU** can be used through `--device /dev/dri/renderD128 --group-add 992`. Actual render group ID may vary; read dynamically. The Nvidia RTX 4070 was identified by `nvidia-smi`, but **NVIDIA Docker GPU passthrough is not configured**. Do not claim RTX acceleration.
- Test launcher on laptop: `/home/hazem/projects/generals-extended-tests/launch-gpu-test.sh`. It uses the existing Wine prefix and Intel DRM render node, does not modify Windows, and terminates after a test timeout.

## Source-supported launch options

`Core/GameEngine/Source/Common/CommandLine.cpp:814,1195` explicitly implements `-noshellmap`, which disables the animated shell-map background. The `-nologo` and `-noShellAnim` flags also exist. These are useful to reduce unnecessary menu/demo overhead while testing.

Example:
```bash
bash /home/hazem/projects/generals-extended-tests/launch-gpu-test.sh 'generalszh.exe -noshellmap -nologo -noShellAnim' 90
```
This launches **only the test environment**. It is not a command to build from source; build artifacts already exist in `build/docker/GeneralsMD`.

## Validated observations

1. With the Wine OpenGL runtime, the **compiled Generals Zero Hour game** drew 3D animated scenes, logo and HUD (money, abilities/general points, timer, units, buildings) in direct X11 window screenshots. With `-noshellmap` the renderer reached an in-game HUD scene. The scene/map identity was **not determined**, and no claim is made that the 600x600 experimental map was played.
2. Shell menu boxes were observed, but their text labels remained blank after copies of CSF and Windows fonts were installed and registered. HUD/gameplay text **is** displayed, suggesting a shell-menu-specific problem rather than a complete CSF failure.
3. Intel GPU-enabled `WorldBuilderZH.exe` opened the experimental Twilight Flame **600x600** map and its status line showed **537 objects and 121 waypoints**. Its central terrain viewport remained black, so visible terrain rendering is not confirmed. Intel GPU test used substantially less CPU than pure `llvmpipe` tests.
4. With GPU-enabled World Builder, **800x800** created a window bearing the test filename but showed `Ready` / no confirmed object count in the captured snapshot. Prior software trials of 700/800/1000 were also inconclusive. **Do not infer playable or fully imported sizes** from file name alone.
5. OpenGL software `llvmpipe` consumed several CPU cores during the shell animation. Intel GPU rendering could still encounter Wine startup/stack-overflow problems depending on mode. These compatibility issues are separate from map-size limits.
6. One prior 90-second GPU test was intentionally terminated on expiration. Attempting to press Escape in a subsequently exited test process produced a harmless X11 `BadWindow`; no separate desktop application was controlled.

## Next priorities

- Resolve or bypass the shell menu and **start a reproducible skirmish on a known original map** under a stable Wine/hardware configuration.
- Prove the experimental 600x600 map loads **in actual gameplay** with units able to move into newly extended terrain; record fog, radar and frame time.
- Try 700, then 800, then 1000 incrementally, **not simultaneously**.
- As a fallback, validate on a separately staged Windows test build, never overwrite the owner's retail installation.
- Only then start implementing >8 AI players. The goal may be user + 12 or 16 AI (13/17 total), so clarify total player slots in the future.

The Ubuntu root partition had roughly 9.6 GiB free near the latest tests. No disk cleanup, original Windows modifications, or game binaries/assets added to GitHub.
