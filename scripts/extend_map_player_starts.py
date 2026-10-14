#!/usr/bin/env python3
"""Add test-only ninth/tenth starting waypoints to an uncompressed CkMp map.

Clones an existing *Waypoints/Waypoint Object* chunk, updates its location,
name and unique waypoint ID. Does NOT modify the original map or add economy.
The result is an experimental gameplay test map, not a balanced finished map.
"""
import argparse
import re
import struct
from pathlib import Path

if __package__:
    from .map_probe import inspect_map, MapFormatError
    from .map_resize_lab import parse_chunks
else:
    from map_probe import inspect_map, MapFormatError
    from map_resize_lab import parse_chunks

OBJECT_HEADER = struct.Struct("<IHi")
WAYPOINT_ID_PROPERTY = b"\x01\x26\x00\x00"
START_8 = b"Player_8_Start"


def _read_objects(payload):
    entries = []
    pos = 0
    while pos < len(payload):
        if pos + OBJECT_HEADER.size > len(payload):
            raise MapFormatError("Truncated Object header")
        ident, version, size = OBJECT_HEADER.unpack_from(payload, pos)
        if size < 0 or pos + OBJECT_HEADER.size + size > len(payload):
            raise MapFormatError("Corrupt Object chunk length")
        item = payload[pos + OBJECT_HEADER.size:pos + OBJECT_HEADER.size + size]
        entries.append((ident, version, item))
        pos += OBJECT_HEADER.size + size
    return entries


def _wpid(item):
    if item.count(WAYPOINT_ID_PROPERTY) != 1:
        return None
    index = item.index(WAYPOINT_ID_PROPERTY) + len(WAYPOINT_ID_PROPERTY)
    if index + 4 > len(item):
        raise MapFormatError("Truncated waypoint ID")
    return struct.unpack_from("<i", item, index)[0]


def _copy_start(template, name, waypoint_id, x, y):
    old_label = struct.pack("<H", len(START_8)) + START_8
    new_label = struct.pack("<H", len(name)) + name
    if template.count(old_label) != 2:
        raise MapFormatError("Expected two matching Player_8_Start property strings")
    if template.count(WAYPOINT_ID_PROPERTY) != 1:
        raise MapFormatError("Waypoint-ID dictionary property missing/ambiguous")
    output = bytearray(template.replace(old_label, new_label))
    struct.pack_into("<2f", output, 0, x, y)
    idx = output.index(WAYPOINT_ID_PROPERTY) + len(WAYPOINT_ID_PROPERTY)
    struct.pack_into("<i", output, idx, waypoint_id)
    return bytes(output)


def add_starts(map_bytes, positions=((5550.0, 2700.0), (2700.0, 5550.0))):
    table, chunks = parse_chunks(map_bytes)
    if len(positions) != 2:
        raise ValueError("Exactly two new starts required")
    matches = [idx for idx, (_, _, _, name) in enumerate(chunks)
               if name == "ObjectsList"]
    if len(matches) != 1:
        raise MapFormatError("Expected a single ObjectsList chunk")
    idx = matches[0]
    ident, version, payload, name = chunks[idx]
    objects = _read_objects(payload)
    templates = [p for _, ver, p in objects if ver == 3 and
                 p.count(struct.pack("<H", len(START_8)) + START_8) == 2]
    if len(templates) != 1:
        raise MapFormatError("Expected exactly one Player_8_Start waypoint")
    template = templates[0]
    ids = [v for _, _, p in objects if (v := _wpid(p)) is not None]
    if not ids:
        raise MapFormatError("No existing waypoint IDs")
    if any(b"Player_9_Start" in p or b"Player_10_Start" in p
           for _, _, p in objects):
        raise MapFormatError("9th or 10th start already exists")
    next_id = max(ids) + 1
    result = bytearray(payload)
    subident, subversion, _ = next((a,b,c) for a,b,c in objects
                                   if c is template)
    for slot, (x,y) in zip((9,10), positions):
        assert 0 < x < 7000 and 0 < y < 7000
        data = _copy_start(template, f"Player_{slot}_Start".encode(),
                           next_id, x, y)
        result += OBJECT_HEADER.pack(subident, subversion, len(data))
        result += data
        next_id += 1
    chunks[idx] = (ident, version, bytes(result), name)
    out = bytearray(table)
    for ident,ver,payload,_ in chunks:
        out += OBJECT_HEADER.pack(ident,ver,len(payload))
        out += payload
    return bytes(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Existing experimental 600x600 .map")
    parser.add_argument("output", type=Path, help="New private test map")
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Refusing to overwrite a map")
    source_info = inspect_map(args.source)
    if (source_info["playable_width"], source_info["playable_height"]) != (600, 600):
        parser.error("The two default positions are calibrated for a 600x600 map")
    result = add_starts(args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    info = inspect_map(args.output)
    print("Generated 10-start experimental map:", info)


if __name__ == "__main__":
    main()
