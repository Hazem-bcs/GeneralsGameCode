#!/usr/bin/env python3
"""Make a private ten-base variant from the owner's experimental 600x600 map.

Preserves the input. Repositions ten starts, adds two local supply docks per base
and ten expansion docks, clears base/route obstructions, and grades connected
build pads and routes. No proprietary map or objects are embedded in this script.
"""
import argparse
import json
import math
from pathlib import Path
import re
import struct
from map_probe import inspect_map, MapFormatError
from map_resize_lab import parse_chunks
from extend_map_player_starts import _read_objects, OBJECT_HEADER


def object_name(data):
    length = struct.unpack_from("<H", data, 20)[0]
    return data[22:22 + length].decode("ascii")


def replace_label(data, old, new):
    a, b = old.encode(), new.encode()
    return data.replace(struct.pack("<H", len(a)) + a, struct.pack("<H", len(b)) + b)


def build(data):
    table, chunks = parse_chunks(data)
    hi = next(i for i, item in enumerate(chunks) if item[3] == "HeightMapData")
    bi = next(i for i, item in enumerate(chunks) if item[3] == "BlendTileData")
    oi = next(i for i, item in enumerate(chunks) if item[3] == "ObjectsList")
    height = bytearray(chunks[hi][2])
    width, rows, border = struct.unpack_from("<3i", height)
    if (width - 2 * border, rows - 2 * border) != (600, 600):
        raise MapFormatError("Requires the existing 600x600 experimental map")
    center, radius = (3000.0, 3000.0), 2150.0
    starts, supplies = [], []
    for i in range(10):
        angle = -math.pi / 2 + i * 2 * math.pi / 10
        ux, uy = math.cos(angle), math.sin(angle)
        x, y = center[0] + radius * ux, center[1] + radius * uy
        starts.append((x, y))
        supplies.extend(((x + 270 * ux, y + 270 * uy),
                         (x - 370 * uy, y + 370 * ux)))
    for i in range(10):
        angle = -math.pi / 2 + (i + .5) * 2 * math.pi / 10
        supplies.append((3000 + 1100 * math.cos(angle), 3000 + 1100 * math.sin(angle)))
    # Keep the middle's original landmarks. Flat, connected outer pads use the
    # dominant low plateau elevation of the inherited map (159).
    modified, clear = set(), set()
    for gy in range(border, rows - border):
        y = (gy - border) * 10.0
        for gx in range(border, width - border):
            x = (gx - border) * 10.0
            rr = math.hypot(x - 3000, y - 3000)
            weight = max(0.0, min(1.0, (260 - abs(rr - 1800)) / 90))
            for sx, sy in starts:
                distance = math.hypot(x - sx, y - sy)
                weight = max(weight, max(0.0, min(1.0, (650 - distance) / 150)))
                # Straight radial routes connect every base to the central arena.
                ux, uy = (sx - 3000) / radius, (sy - 3000) / radius
                along = (x - 3000) * ux + (y - 3000) * uy
                across = abs((x - 3000) * uy - (y - 3000) * ux)
                if 250 < along < radius:
                    weight = max(weight, max(0.0, min(1.0, (240 - across) / 80)))
            for sx, sy in supplies[20:]:
                distance = math.hypot(x - sx, y - sy)
                weight = max(weight, max(0.0, min(1.0, (260 - distance) / 80)))
            if weight > 0:
                index = gy * width + gx
                height[28 + index] = round(height[28 + index] * (1 - weight) + 159 * weight)
                modified.add(index)
                if weight >= .8:
                    clear.add(index)
    chunks[hi] = (chunks[hi][0], chunks[hi][1], bytes(height), chunks[hi][3])
    blend = bytearray(chunks[bi][2])
    samples = width * rows
    if struct.unpack_from("<i", blend)[0] != samples:
        raise MapFormatError("Height/blend dimensions differ")
    for index in modified:
        for field in (1, 2, 3):
            struct.pack_into("<H", blend, 4 + field * samples * 2 + index * 2, 0)
        gy, gx = divmod(index, width)
        flag = 4 + samples * 8 + gy * ((width + 7) // 8) + gx // 8
        blend[flag] &= ~(1 << (gx % 8))
    chunks[bi] = (chunks[bi][0], chunks[bi][1], bytes(blend), chunks[bi][3])
    objects = _read_objects(chunks[oi][2])
    dock = next(item for item in objects if object_name(item[2]) == "SupplyDock")
    dock_label = re.search(rb"SupplyDock \d+", dock[2])[0].decode()
    kept, removed, found = [], 0, set()
    for ident, version, original in objects:
        name = object_name(original)
        if name == "SupplyDock":
            removed += 1
            continue
        item = bytearray(original)
        match = re.search(rb"Player_(\d+)_Start", item)
        if match:
            number = int(match[1])
            if 1 <= number <= 10:
                struct.pack_into("<2f", item, 0, *starts[number - 1])
                found.add(number)
        elif not name.startswith("*Waypoints/"):
            x, y = struct.unpack_from("<2f", item)
            gx, gy = round(x / 10) + border, round(y / 10) + border
            if 0 <= gx < width and 0 <= gy < rows and gy * width + gx in clear:
                removed += 1
                continue
        kept.append((ident, version, bytes(item)))
    if found != set(range(1, 11)):
        raise MapFormatError("Input must contain ten starting waypoints")
    for i, (x, y) in enumerate(supplies):
        item = bytearray(replace_label(dock[2], dock_label, f"TenBaseSupply_{i + 1}"))
        struct.pack_into("<4f", item, 0, x, y, 0, math.atan2(3000 - y, 3000 - x))
        kept.append((dock[0], dock[1], bytes(item)))
    payload = b"".join(OBJECT_HEADER.pack(ident, version, len(item)) + item for ident, version, item in kept)
    chunks[oi] = (chunks[oi][0], chunks[oi][1], payload, chunks[oi][3])
    output = table + b"".join(OBJECT_HEADER.pack(ident, version, len(payload)) + payload
                             for ident, version, payload, _ in chunks)
    return output, {"starts": starts, "supplies": supplies, "removed_obstructions_and_old_docks": removed,
                    "graded_cells": len(modified), "base_radius": radius, "pad_radius": 500}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Refusing to overwrite a map")
    output, report = build(args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    report["format"] = inspect_map(args.output)
    args.output.with_suffix(".layout.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
