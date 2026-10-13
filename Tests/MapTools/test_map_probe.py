"""Unit tests for map_probe's read-only CkMp parser."""
import struct
import tempfile
import unittest
from pathlib import Path
from scripts.map_probe import inspect_map, MapFormatError


def fixture(width=16, height=18, border=2, broken=False):
    label = b"HeightMapData"
    table = b"CkMp" + struct.pack("<iB", 1, len(label)) + label + struct.pack("<I", 7)
    payload = struct.pack("<iiii", width, height, border, 1)
    payload += struct.pack("<ii", width - 2 * border, height - 2 * border)
    payload += struct.pack("<i", width * height)
    payload += b"\0" * (width * height - (1 if broken else 0))
    return table + struct.pack("<IHi", 7, 4, len(payload)) + payload


class TestMapProbe(unittest.TestCase):
    def write_fixture(self, contents):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "test.map"
        path.write_bytes(contents)
        return path

    def test_version_four_dimensions(self):
        result = inspect_map(self.write_fixture(fixture()))
        self.assertEqual((result["stored_width"], result["stored_height"]), (16, 18))
        self.assertEqual((result["playable_width"], result["playable_height"]), (12, 14))
        self.assertEqual(result["border"], 2)

    def test_reject_bad_magic(self):
        with self.assertRaises(MapFormatError):
            inspect_map(self.write_fixture(b"not-a-map"))

    def test_reject_truncated_height_data(self):
        with self.assertRaises(MapFormatError):
            inspect_map(self.write_fixture(fixture(broken=True)))

    def test_reject_absurd_border(self):
        with self.assertRaises(MapFormatError):
            inspect_map(self.write_fixture(fixture(border=9)))


if __name__ == "__main__":
    unittest.main()
