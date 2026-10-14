#!/usr/bin/env python3
"""Verify real position changes after opt-in player-source dozer move commands.

This tests GameLogic's CMD_FROM_PLAYER order path without asserting that a
physical mouse click or shell UI was exercised. Runs only against private
LOCAL_HUMAN_MOVE_* diagnostics from -localhumanmovetest.
"""
import argparse
import json
import math
import re
from pathlib import Path


def rows(text, prefix):
    for line in text.splitlines():
        if not line.startswith(prefix + " "):
            continue
        values = dict(re.findall(r"(\w+)=([^ \r\n]+)", line))
        yield values


def verify(text, minimum_frame=27000, displacement=180):
    pool = list(rows(text, "LOCAL_PATHFIND"))
    if not pool or int(pool[-1]["frame"]) < minimum_frame:
        raise ValueError("The test did not reach the required game time")
    if any(int(r["failures"]) or int(r["free"]) <= 0 for r in pool):
        raise ValueError("Pathfinding pool exhaustion occurred")
    if list(rows(text, "LOCAL_HUMAN_MOVE_MISSING")):
        raise ValueError("The human dozer was not found")
    commands = list(rows(text, "LOCAL_HUMAN_MOVE_ISSUE"))
    samples = list(rows(text, "LOCAL_HUMAN_MOVE_POSITION"))
    if len(commands) != 2 or not samples:
        raise ValueError("Expected two real player-source move orders and sampled positions")
    if [int(c["frame"]) for c in commands] != [12600, 23400]:
        raise ValueError("Move commands were issued at incorrect game frames")
    if any(c.get("source") != "CMD_FROM_PLAYER" for c in commands):
        raise ValueError("A command did not use the player's command source")

    result = []
    for number, cmd in enumerate(commands):
        ident, frame = int(cmd["id"]), int(cmd["frame"])
        next_frame = (int(commands[number + 1]["frame"]) if number + 1 < len(commands)
                      else minimum_frame)
        initial = (float(cmd["x"]), float(cmd["y"]))
        positions = [(int(p["frame"]), float(p["x"]), float(p["y"]))
                     for p in samples if int(p["id"]) == ident
                     and frame < int(p["frame"]) <= next_frame]
        moved = [(f, round(math.hypot(x-initial[0], y-initial[1]), 1))
                 for f,x,y in positions]
        best = max((d for f,d in moved), default=0)
        if best < displacement:
            raise ValueError(f"Player dozer {ident} did not move after order at {frame}: max {best}")
        result.append({"command_frame": frame, "id": ident,
                       "target": [float(cmd["tx"]),float(cmd["ty"])],
                       "max_actual_displacement": best,
                       "last_observed_frame": max((f for f,_ in moved), default=frame)})
    return {"last_frame": int(pool[-1]["frame"]),
            "minimum_free": min(int(p["free"]) for p in pool),
            "allocation_failures": int(pool[-1]["failures"]),
            "real_human_vehicle_order_tests": result,
            "mouse_ui_click_tested": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log",type=Path)
    parser.add_argument("--minimum-frame",type=int,default=27000)
    args=parser.parse_args()
    print(json.dumps(verify(args.log.read_text(errors="replace"),args.minimum_frame),indent=2))
