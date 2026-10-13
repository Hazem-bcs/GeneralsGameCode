"""Checks for the RefPack map decompressor."""
import struct
import unittest
from scripts.map_unpack import RefPackError, decode_ear


def pack_literal(payload):
    parts = bytearray()
    while len(payload) >= 4:
        chunk_len = min((len(payload) // 4) * 4, 112)
        parts.append(0xE0 + (chunk_len // 4) - 1)
        parts.extend(payload[:chunk_len])
        payload = payload[chunk_len:]
    parts.append(0xFC | len(payload))
    parts.extend(payload)
    return parts


def literal_wrapper(payload):
    stream = b"\x10\xfb" + len(payload).to_bytes(3, "big") + pack_literal(payload)
    return b"EAR\0" + struct.pack("<I", len(payload)) + stream


class TestMapUnpack(unittest.TestCase):
    def test_empty_magic(self):
        with self.assertRaises(RefPackError):
            decode_ear(b"CkMp")

    def test_literal_round_trip(self):
        for length in (1, 3, 4, 9, 112, 119, 1000):
            payload = bytes((i * 37) % 256 for i in range(length))
            self.assertEqual(decode_ear(literal_wrapper(payload)), payload)

    def test_small_backreference(self):
        payload = b"ABCD" + b"ABCD" * 4
        # emit "ABCD" then one long? medium command: 16 extra bytes from offset 4
        stream = b"\x10\xfb" + len(payload).to_bytes(3, "big") + bytes([0xE0]) + b"ABCD"
        stream += bytes([0x8C, 0x00, 0x03, 0xFC])
        wrapped = b"EAR\0" + struct.pack("<I", len(payload)) + stream
        self.assertEqual(decode_ear(wrapped), payload)

    def test_reject_size_mismatch(self):
        with self.assertRaises(RefPackError):
            decode_ear(literal_wrapper(b"ABCDEFGH")[:-2])


if __name__ == "__main__":
    unittest.main()
