#!/usr/bin/env python3
"""EXPERIMENTAL: extend a Zero Hour map canvas for engine size tests.

Input: *uncompressed* CkMp v4 with one rectangular boundary and BlendTileData v8.
Output: an uncompressed CkMp with larger X/Y, preserving other chunks intact.

This is a **technical stress-test map**, not a finished multiplayer map.
Buildings, waypoints and player spawns stay in their original positions.
The original nonplayable right/top edge is replaced with repeated nearby tiles.
The original (smaller) preview must be treated as inaccurate.

Implementation follows:
  GeneralsMD/Code/Tools/WorldBuilder/src/WHeightMapEdit.cpp:575-630
  Core/GameEngineDevice/Source/W3DDevice/GameClient/WorldHeightMap.cpp:872-901
"""
import argparse
import struct
from pathlib import Path

from map_probe import inspect_map, MapFormatError

MAX_INPUT_BYTES = 128 * 1024 * 1024
MAX_GRID_SAMPLES = 4_000_000


def parse_chunks(data):
    if not data.startswith(b"CkMp") or len(data) < 8:
        raise MapFormatError("Only uncompressed CkMp is supported")
    count = struct.unpack_from("<i", data, 4)[0]
    if not 1 <= count <= 4096:
        raise MapFormatError("Invalid symbol count")
    pos = 8
    syms = {}
    for _ in range(count):
        if pos >= len(data):
            raise MapFormatError("Truncated table")
        length = data[pos]
        pos += 1
        if pos + length + 4 > len(data):
            raise MapFormatError("Truncated table entry")
        name = data[pos:pos + length].decode("ascii", errors="replace")
        pos += length
        ident = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        syms[ident] = name
    table = data[:pos]
    chunks = []
    while pos < len(data):
        if pos + 10 > len(data):
            raise MapFormatError("Truncated chunk header")
        ident, version, size = struct.unpack_from("<IHi", data, pos)
        pos += 10
        if size < 0 or pos + size > len(data):
            raise MapFormatError("Invalid chunk size")
        chunks.append((ident, version, data[pos:pos + size], syms.get(ident)))
        pos += size
    return table, chunks


def _replicate_pixels(src, old_width, old_height, cutoff_width,
                      cutoff_height, new_width, new_height, stride, extend_value=False):
    if len(src) != old_width * old_height * stride:
        raise MapFormatError("Input field size mismatch")
    results = bytearray(new_width * new_height * stride)
    for y in range(new_height):
        sy = min(y, cutoff_height - 1)
        srcstart = sy * old_width * stride
        deststart = y * new_width * stride
        fixed_len = min(cutoff_width, new_width)
        data_len = fixed_len * stride
        results[deststart:deststart + data_len] = src[srcstart:srcstart + data_len]
        if new_width > fixed_len and extend_value:
            pixel = src[srcstart + (fixed_len - 1) * stride:srcstart + fixed_len * stride]
            results[deststart + data_len:deststart + new_width * stride] = pixel * (new_width - fixed_len)
        if y >= cutoff_height and not extend_value:
            # New unblended areas should be blank (zero) rather than cloned cliffs.
            results[deststart:deststart + new_width * stride] = bytes(new_width * stride)
    return bytes(results)


def resize_map(source_bytes, playable_width, playable_height):
    if len(source_bytes) > MAX_INPUT_BYTES:
        raise MapFormatError("Input map is too large")
    toc, chunks = parse_chunks(source_bytes)
    old_width = old_height = border = None
    hindex = bindex = None
    for idx, (_, version, payload, name) in enumerate(chunks):
        if name == "HeightMapData":
            if version != 4 or len(payload) < 28:
                raise MapFormatError("Only HeightMapData v4 supported")
            old_width, old_height, border, nbound = struct.unpack_from("<4i", payload)
            if nbound != 1 or border < 0:
                raise MapFormatError("Only a single rectangular map boundary is supported")
            bx, by, data_size = struct.unpack_from("<3i", payload, 16)
            if data_size != old_width * old_height or data_size + 28 != len(payload):
                raise MapFormatError("Invalid heightmap length")
            hindex = idx
        elif name == "BlendTileData":
            if version != 8:
                raise MapFormatError("Only BlendTileData v8 supported")
            bindex = idx
    if hindex is None or bindex is None:
        raise MapFormatError("Required heightmap or blend chunk missing")
    old_playable_width = old_width - border * 2
    old_playable_height = old_height - border * 2
    if not (playable_width > old_playable_width and playable_height > old_playable_height):
        raise MapFormatError("Target must exceed the source map on both axes")
    new_width = playable_width + border * 2
    new_height = playable_height + border * 2
    if new_width * new_height > MAX_GRID_SAMPLES:
        raise MapFormatError("Requested heightmap exceeds the experiment safety limit")
    # Preserve the map origin, placement coordinates and its left/bottom border.
    # Remove old *right/top* non-playable border by cloning adjacent edge cells.
    keep_width = old_width - border
    keep_height = old_height - border
    h_ver = chunks[hindex][1]
    hpayload = chunks[hindex][2]
    height_bytes = hpayload[28:]
    enlarged_heights = _replicate_pixels(
        height_bytes, old_width, old_height, keep_width, keep_height,
        new_width, new_height, 1, extend_value=True
    )
    # Preserve any original playable-bounds margin.
    new_bx = bx + (playable_width - old_playable_width)
    new_by = by + (playable_height - old_playable_height)
    header = struct.pack("<7i", new_width, new_height, border, 1, new_bx, new_by, new_width * new_height)
    ident = chunks[hindex][0]
    chunks[hindex] = (ident, h_ver, header + enlarged_heights, "HeightMapData")

    version = chunks[bindex][1]
    bp = chunks[bindex][2]
    data_size = struct.unpack_from("<i", bp, 0)[0]
    if data_size != old_width * old_height:
        raise MapFormatError("BlendTileData sample count disagrees with HeightMapData")
    pos = 4
    fields = []
    for field in range(4):
        end = pos + data_size * 2
        if end > len(bp):
            raise MapFormatError("Truncated blend arrays")
        part = bp[pos:end]
        # Preserve visual base terrain; new area has no blended/cliff tiles.
        fields.append(_replicate_pixels(
            part, old_width, old_height, keep_width, keep_height,
            new_width, new_height, 2, extend_value=(field == 0)
        ))
        pos = end
    old_flag_stride = (old_width + 7) // 8
    new_flag_stride = (new_width + 7) // 8
    if pos + old_flag_stride * old_height > len(bp):
        raise MapFormatError("Truncated cliff flags")
    original_flags = bp[pos:pos + old_flag_stride * old_height]
    pos += len(original_flags)
    new_flags = bytearray(new_flag_stride * new_height)
    copy_bytes = (keep_width + 7) // 8
    for y in range(min(keep_height, new_height)):
        a = y * old_flag_stride
        b = y * new_flag_stride
        new_flags[b:b + copy_bytes] = original_flags[a:a + copy_bytes]
        if keep_width % 8:
            new_flags[b + copy_bytes - 1] &= (1 << (keep_width % 8)) - 1
    replacement = (struct.pack("<i", new_width * new_height)
                   + b"".join(fields) + bytes(new_flags) + bp[pos:])
    chunks[bindex] = (chunks[bindex][0], version, replacement, "BlendTileData")

    output = bytearray(toc)
    for chunk_id, version, payload, _ in chunks:
        output += struct.pack("<IHi", chunk_id, version, len(payload))
        output += payload
    return bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Uncompressed source .map")
    parser.add_argument("--playable-width", type=int, required=True)
    parser.add_argument("--playable-height", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; refusing to overwrite")
    if args.source.resolve() == args.output.resolve():
        parser.error("Source and output cannot be the same file")
    newdata = resize_map(args.source.read_bytes(), args.playable_width, args.playable_height)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(newdata)
    print(inspect_map(args.output))
    print("Created an EXPERIMENTAL map; not yet runtime-validated.")


if __name__ == "__main__":
    main()
