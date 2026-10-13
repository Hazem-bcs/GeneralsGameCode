# Zero Hour Ubuntu runtime recovery and map-size smoke tests — 2026-10-14

Branch: `research/player-limits`. All changes below were made to **isolated local test staging** unless otherwise stated. The Windows game installation remains mounted read-only.

## Assertion cause and fix

A screenshot supplied by the user reported:

`ASSERTION FAILURE: INI::load, cannot open file 'Data\\INI\\Default\\GameData.ini'`

File tracing with Wine showed an attempted lookup from
`Z:\\work\\runtime\\ZeroHour\\Data\\Data\\INI\\Default\\GameData.ini`.
The game was started from `.../ZeroHour/Data/generalszh.exe` and had changed its current working directory to its executable's `Data` folder, causing a doubled `Data\\Data` relative path.

`INIZH.big` at the installation root **does** contain `Data\\INI\\Default\\GameData.ini`. The isolated test was fixed by placing the compiled `generalszh.exe` in `.../runtime/ZeroHour/` (the same level as `INIZH.big`) and running it from that root. No original Windows assets were changed.

## Graphics runtime

The `zerohour-build` Docker image is sufficient for compiling, but not for exercising Wine's Direct3D path. A derivative image named `zerohour-runtime-gl` was created, installing Debian Bookworm OpenGL/EGL/Vulkan/Mesa for both amd64 and i386 (about 83 MB of package downloads and 358 MB installed before image layers).

The private Wine prefix was given a Generals base-game registry key:
- `HKCU\\Software\\Electronic Arts\\EA Games\\Generals`
- `InstallPath = Z:\\work\\runtime\\ZeroHour\\ZH_Generals\\`

The game was then launched via Wine and rendered a recognizable **Zero Hour main-menu scene**, including the ship, water and logo. Menu-button labels were blank. The GUI therefore **partly works**, but entering a playable match has not been established.

Original English language files `Data\\English\\generals.csf` (929 kB) and `Language.ini` (2 kB) were extracted from the user's licensed `EnglishZH.big` into the **isolated test data directory** to investigate missing UI text; these proprietary assets were **not committed** to GitHub. No conclusive text-rendering fix was confirmed.

The program still emits nonfatal Wine OLE / DirectSound warnings. Rendering uses Mesa software OpenGL, `llvmpipe`, and has poor large-map performance. Earlier `stack overflow` / missing library errors were avoided by the corrected root layout and GL runtime.

## World Builder test status

The **compiled** `WorldBuilderZH.exe` was likewise run from the test installation root. Local copies of 32-bit `mfc42.dll`, `msvcp60.dll`, `msvcirt.dll` were staged from the user's Windows installation for runtime only (not checked in).

The editor opens, displaying menus and toolbar. Its 3D viewport was black under the current Wine/llvmpipe environment, so terrain rendering was **not** verified. Screenshot capture of the individual X11 window confirmed the editor UI even when grabbing the XWayland root yielded an all-black image.

Maps are experimental expanded versions of the user's `Twilight Flame Edit` (490x490 playable); their new areas replicate edge terrain rather than being designed as finished balanced maps. The `.map` files are in `/home/hazem/projects/generals-extended-tests/maps`, not in the source repository.

| Playable map size | Total stored vertices including 70-cell borders | Editor observations |
|---|---|---|
| 600x600 | 740x740 | Filename visible; status showed **537 objects and 121 waypoints**. Editor remained open for a 70 s smoke test. No 3D terrain shown. |
| 700x700 | 840x840 | Filename visible; object-count completion **not established** within 40 s. High CPU (about 82–95% of one core) and around 825 MB RSS. |
| 800x800 | 940x940 | Filename visible; observed 0 objects in status during a 34 s test; **not proof** of successful full import. |
| 1000x1000 | 1140x1140 | Filename visible; status showed 'Ready' rather than object count. About 100% of one core and ~972 MB RSS in an early sample. No verified full import in a 38 s test. |

**Do not claim that 700, 800 or 1000 have been proven playable or fully loadable**. Current experiments indicate that software rendering is inadequate for judging the real hardware/gameplay limit. Even for 600, rendering and gameplay remain unverified.

## Next experiments

1. Resolve missing UI labels and demonstrate navigation to the game's skirmish menu.
2. Prefer GPU-backed Wine/D3D runtime or a separate Windows test installation on the user's computer (retain the retail installation untouched) instead of software `llvmpipe`.
3. Validate a known unmodified Twilight Flame map as a control, then 600x600, 700x700, 800x800 and 1000x1000.
4. Record actual map visibility, camera reach, fog, unit movement, memory, load times and playable AI before proposing an engine map-size cap.
5. Only after map rendering/gameplay works, start the 10+ AI player-slot prototype.

Source repository branch should remain clean: no game archives, binaries, proprietary assets or generated test maps committed.
