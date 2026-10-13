#!/usr/bin/env python3
"""Decode the EAR/RefPack wrapper used by archived C&C Generals map files.

Implements the reference decoder in
Core/Libraries/Source/Compression/EAC/refdecode.cpp.
Never modifies the input. Does not require Wine or Docker.
"""
import argparse
import struct
from pathlib import Path


class RefPackError(ValueError):
    """Malformed or unsupported RefPack data."""


def decode_ear(data: bytes, max_decoded_bytes: int = 128 * 1024 * 1024) -> bytes:
    if len(data) < 13 or data[:4] != b"EAR\0":
        raise RefPackError("Expected EAR/RefPack wrapper")
    expected = struct.unpack_from("<I", data, 4)[0]
    if expected < 1 or expected > max_decoded_bytes:
        raise RefPackError("Invalid or excessive decoded size")
    raw = memoryview(data)
    p = 8
    packtype = (raw[p] << 8) | raw[p + 1]
    if packtype not in (0x10FB, 0x11FB, 0x90FB, 0x91FB):
        raise RefPackError("Unsupported RefPack header")
    p += 2
    size_bytes = 4 if packtype & 0x8000 else 3
    if packtype & 0x100:
        p += size_bytes
    if p + size_bytes > len(raw):
        raise RefPackError("Truncated RefPack size")
    stream_size = int.from_bytes(raw[p:p + size_bytes], "big")
    p += size_bytes
    if stream_size != expected:
        raise RefPackError("Wrapper and stream sizes disagree")
    out = bytearray()

    def literals(count: int) -> None:
        nonlocal p
        if p + count > len(raw) or len(out) + count > expected:
            raise RefPackError("Truncated literals or decoded size exceeded")
        out.extend(raw[p:p + count])
        p += count

    def backref(distance: int, count: int) -> None:
        if distance < 1 or distance > len(out) or len(out) + count > expected:
            raise RefPackError("Invalid backreference")
        for _ in range(count):
            out.append(out[-distance])

    while p < len(raw):
        first = raw[p]
        p += 1
        if first < 0x80:
            if p >= len(raw):
                raise RefPackError("Truncated short command")
            second = raw[p]
            p += 1
            literal_count = first & 3
            distance = (((first & 0x60) << 3) | second) + 1
            count = ((first & 0x1C) >> 2) + 3
        elif first < 0xC0:
            if p + 2 > len(raw):
                raise RefPackError("Truncated medium command")
            second, third = raw[p:p + 2]
            p += 2
            literal_count = second >> 6
            distance = (((second & 0x3F) << 8) | third) + 1
            count = (first & 0x3F) + 4
        elif first < 0xE0:
            if p + 3 > len(raw):
                raise RefPackError("Truncated long command")
            second, third, fourth = raw[p:p + 3]
            p += 3
            literal_count = first & 3
            distance = (((first & 0x10) << 12) | (second << 8) | third) + 1
            count = ((first & 0x0C) << 6) + fourth + 5
        elif first < 0xFC:
            literals(((first & 0x1F) << 2) + 4)
            continue
        else:
            literals(first & 3)
            if len(out) != expected:
                raise RefPackError(f"Decoded {len(out)} bytes; expected {expected}")
            return bytes(out)
        literals(literal_count)
        backref(distance, count)
    raise RefPackError("RefPack stream ended without EOF marker")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="EAR-wrapped .map extracted from a BIG archive")
    parser.add_argument("output", type=Path, help="Destination uncompressed CkMp map")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("input and output must differ")
    if args.output.exists():
        parser.error("output exists; refusing to overwrite")
    result = decode_ear(args.input.read_bytes())
    if result[:4] != b"CkMp":
        parser.error("decoded data is not a CkMp map")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(f"Decoded {args.input} -> {args.output} ({len(result):,} bytes)")


if __name__ == "__main__":
    main()
