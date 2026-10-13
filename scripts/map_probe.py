#!/usr/bin/env python3
"""Read Generals / Zero Hour CkMp map dimensions without changing the map.

Format references:
  GeneralsMD/Code/GameEngine/Source/Common/System/DataChunk.cpp
  GeneralsMD/Code/Tools/WorldBuilder/src/WHeightMapEdit.cpp
"""
import argparse
import json
import struct
import sys
from pathlib import Path


class MapFormatError(ValueError):
    """The input is not a supported, valid uncompressed CkMp map."""


def _read(f, count, end):
    if count < 0 or f.tell() + count > end:
        raise MapFormatError("Invalid size or truncated file")
    data = f.read(count)
    if len(data) != count:
        raise MapFormatError("Unexpected end of file")
    return data


def _i32(f, end):
    return struct.unpack("<i", _read(f, 4, end))[0]


def inspect_map(path):
    """Return map dimensions, including the non-playable border."""
    path = Path(path)
    with path.open("rb") as f:
        end = path.stat().st_size
        if _read(f, 4, end) != b"CkMp":
            raise MapFormatError("Not an uncompressed CkMp map")
        symbol_count = _i32(f, end)
        if not (1 <= symbol_count <= 4096):
            raise MapFormatError("Invalid symbol-table size")
        symbols = {}
        for _ in range(symbol_count):
            n = _read(f, 1, end)[0]
            name = _read(f, n, end).decode("ascii", errors="replace")
            ident = struct.unpack("<I", _read(f, 4, end))[0]
            symbols[ident] = name
        while f.tell() < end:
            if end - f.tell() < 10:
                raise MapFormatError("Incomplete chunk header")
            ident, version, chunk_size = struct.unpack("<IHi", _read(f, 10, end))
            start = f.tell()
            stop = start + chunk_size
            if chunk_size < 0 or stop > end:
                raise MapFormatError("Invalid chunk length")
            if symbols.get(ident) == "HeightMapData":
                if version < 1:
                    raise MapFormatError("Unsupported heightmap version")
                width = _i32(f, stop)
                height = _i32(f, stop)
                border = _i32(f, stop) if version >= 3 else 0
                if version >= 4:
                    n_bounds = _i32(f, stop)
                    if n_bounds < 0 or n_bounds > (stop - f.tell()) // 8:
                        raise MapFormatError("Invalid map boundaries")
                    f.seek(n_bounds * 8, 1)
                data_size = _i32(f, stop)
                if width <= 0 or height <= 0 or border < 0:
                    raise MapFormatError("Invalid map dimensions")
                if data_size != width * height or f.tell() + data_size > stop:
                    raise MapFormatError("Map height data does not match dimensions")
                if border * 2 >= min(width, height):
                    raise MapFormatError("Non-playable border exceeds map dimensions")
                return {
                    "file": str(path),
                    "format": "CkMp",
                    "heightmap_version": version,
                    "stored_width": width,
                    "stored_height": height,
                    "border": border,
                    "playable_width": width - border * 2,
                    "playable_height": height - border * 2,
                    "height_samples": data_size,
                    "note": "Version 1 maps are resampled by the game loader; stored dimensions shown."
                    if version == 1 else None,
                }
            f.seek(stop)
    raise MapFormatError("HeightMapData chunk not found")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Map file(s) or directories")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args(argv)
    files = []
    for item in args.paths:
        if item.is_dir():
            files.extend(sorted(item.rglob("*.map")))
        else:
            files.append(item)
    if not files:
        print("No .map files found", file=sys.stderr)
        return 1
    results = []
    failed = False
    for path in files:
        try:
            results.append(inspect_map(path))
        except (OSError, MapFormatError) as exc:
            failed = True
            results.append({"file": str(path), "error": str(exc)})
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for row in results:
            if "error" in row:
                print(f"{row['file']}: ERROR: {row['error']}")
            else:
                print(
                    f"{row['file']}: playable {row['playable_width']}x{row['playable_height']}, "
                    f"stored {row['stored_width']}x{row['stored_height']}, "
                    f"border {row['border']}, format v{row['heightmap_version']}"
                )
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
