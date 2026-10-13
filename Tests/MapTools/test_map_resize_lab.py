"""Unit tests for experimental CkMp large-map canvas expansion."""
import struct
import unittest

from scripts.map_resize_lab import parse_chunks, resize_map
from scripts.map_probe import MapFormatError


def _chunk(ident, version, data):
    return struct.pack("<IHi", ident, version, len(data)) + data


def original_fixture():
    width, height, border = 10, 12, 1
    symbols = [(1, b"HeightMapData"), (2, b"BlendTileData"), (3, b"WorldInfo")]
    toc = b"CkMp" + struct.pack("<i", len(symbols))
    for ident, label in symbols:
        toc += struct.pack("<B", len(label)) + label + struct.pack("<I", ident)
    pixels = bytes((y * width + x) % 256 for y in range(height) for x in range(width))
    hdata = struct.pack("<7i", width, height, border, 1, 8, 10, width * height) + pixels
    tile = struct.pack("<" + "h" * (width * height), *range(width * height))
    shorts = b"\0\0" * (width * height)
    flag = bytes([0x0F, 0x01] * height)
    blend = struct.pack("<i", width * height) + tile + shorts * 3 + flag + b"TRAILER"
    return (toc + _chunk(1, 4, hdata) + _chunk(2, 8, blend)
            + _chunk(3, 1, b"UNCHANGED-METADATA"))


class TestMapResizeLab(unittest.TestCase):
    def test_600_equivalent_extension_and_preservation(self):
        src = original_fixture()
        expanded = resize_map(src, 15, 17)
        old_table, old_chunks = parse_chunks(src)
        table, chunks = parse_chunks(expanded)
        self.assertEqual(old_table, table)
        self.assertEqual(chunks[2], old_chunks[2])
        self.assertEqual(len(chunks), 3)
        wp, hp, border, nb, bx, by, count = struct.unpack_from("<7i", chunks[0][2], 0)
        self.assertEqual((wp, hp, border, bx, by, count), (17, 19, 1, 15, 17, 323))
        old_samples = old_chunks[0][2][28:]
        new_samples = chunks[0][2][28:]
        # An existing sample remains exactly where it was.
        self.assertEqual(new_samples[2 * wp + 3], old_samples[2 * 10 + 3])
        # New area inherits the last *playable* source value.
        self.assertEqual(new_samples[18 * wp + 16], old_samples[10 * 10 + 8])
        bp = chunks[1][2]
        self.assertEqual(struct.unpack_from("<i", bp)[0], count)
        self.assertTrue(bp.endswith(b"TRAILER"))
        self.assertEqual(len(bp), 4 + count * 8 + ((wp + 7) // 8) * hp + 7)

    def test_refuse_shrink_or_same_dimensions(self):
        with self.assertRaises(MapFormatError):
            resize_map(original_fixture(), 8, 15)

    def test_refuse_absurd_area(self):
        with self.assertRaises(MapFormatError):
            resize_map(original_fixture(), 4000, 4000)

    def test_reject_incomplete_chunk(self):
        with self.assertRaises(MapFormatError):
            resize_map(original_fixture()[:-5], 15, 17)


if __name__ == "__main__":
    unittest.main()
