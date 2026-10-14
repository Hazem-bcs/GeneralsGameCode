import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify_local_human_vehicle_commands import verify


def make_log(move_first=True, move_second=True, failures=0, final_frame=27000):
    first = 1500 if move_first else 900
    second = 900 if move_second else 1500
    return "\n".join([
        "LOCAL_PATHFIND frame=12600 capacity=375084 free=360000 failures=0",
        "LOCAL_HUMAN_MOVE_ISSUE frame=12600 id=42 x=900 y=700 tx=1600 ty=720 source=CMD_FROM_PLAYER",
        "LOCAL_HUMAN_MOVE_POSITION frame=12600 id=42 x=900 y=700",
        f"LOCAL_HUMAN_MOVE_POSITION frame=13500 id=42 x={first} y=700",
        f"LOCAL_HUMAN_MOVE_POSITION frame=14400 id=42 x={first} y=700",
        "LOCAL_PATHFIND frame=23400 capacity=375084 free=350000 failures=0",
        f"LOCAL_HUMAN_MOVE_ISSUE frame=23400 id=42 x={first} y=700 tx=900 ty=800 source=CMD_FROM_PLAYER",
        f"LOCAL_HUMAN_MOVE_POSITION frame=24300 id=42 x={second} y=800",
        f"LOCAL_PATHFIND frame={final_frame} capacity=375084 free=340000 failures={failures}"
    ])


class TestLocalHumanVehicleCommands(unittest.TestCase):
    def test_reject_stationary_flag(self):
        with self.assertRaisesRegex(ValueError, "did not move"):
            verify(make_log(move_first=False))

    def test_reject_second_order_stall(self):
        with self.assertRaisesRegex(ValueError, "did not move"):
            verify(make_log(move_second=False))

    def test_reject_exhaustion(self):
        with self.assertRaisesRegex(ValueError, "exhaustion"):
            verify(make_log(failures=1))

    def test_reject_short_run(self):
        with self.assertRaisesRegex(ValueError, "required game time"):
            verify(make_log(final_frame=18000))

    def test_real_position_changes(self):
        data=verify(make_log())
        self.assertEqual(len(data["real_human_vehicle_order_tests"]),2)
        self.assertFalse(data["mouse_ui_click_tested"])


if __name__ == "__main__":
    unittest.main()
