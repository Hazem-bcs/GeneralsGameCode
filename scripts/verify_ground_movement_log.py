#!/usr/bin/env python3
"""Check actual late-game vehicle displacement and pathfinding capacity in Wine logs."""
import argparse
import json
import math
from pathlib import Path
import re


def verify(text, players=10, minimum_frame=27000, late_frame=12600):
    stats, vehicles = [], {}
    for line in text.splitlines():
        if line.startswith(("LOCAL_PATHFIND ", "LOCAL_GROUND ")):
            row = {k: float(v) for k, v in re.findall(r"(\w+)=(-?[\d.]+)", line)}
            if line.startswith("LOCAL_PATHFIND "):
                stats.append(row)
            else:
                vehicles.setdefault(int(row["frame"]), []).append(row)
    if not stats or stats[-1]["frame"] < minimum_frame:
        raise ValueError("The run did not reach the requested game time")
    if any(s["failures"] or s["free"] <= 0 for s in stats):
        raise ValueError("Pathfinding records were exhausted")
    if players > 8 and any(s["capacity"] <= 30000 for s in stats):
        raise ValueError("The extended local pathfinding pool was not enabled")
    if players <= 8 and any(s["capacity"] != 30000 for s in stats):
        raise ValueError("Legacy match pathfinding capacity changed")

    previous, movements = {}, []
    for frame, rows in sorted(vehicles.items()):
        current = {int(row["id"]): row for row in rows}
        for oid, row in current.items():
            old = previous.get(oid)
            if old and old["slot"] == row["slot"] and frame >= late_frame:
                distance = math.hypot(row["x"] - old["x"], row["y"] - old["y"])
                if distance >= 20:
                    movements.append({"frame": frame, "slot": int(row["slot"]),
                                      "id": oid, "combat": int(row["combat"]),
                                      "distance": round(distance, 1)})
        previous = current
    ai_slots = set(range(1, players))
    moving_ai = {row["slot"] for row in movements if row["combat"]}
    if not ai_slots.issubset(moving_ai):
        raise ValueError(f"No late combat vehicle displacement for AI slots {sorted(ai_slots-moving_ai)}")
    recent = [m for m in movements if m["frame"] >= minimum_frame - 1800]
    if not any(m["combat"] for m in recent):
        raise ValueError("No combat vehicles moved during the final minute")
    return {"final_frame": int(stats[-1]["frame"]), "game_minutes": stats[-1]["frame"] / 1800,
            "capacity": int(stats[-1]["capacity"]), "minimum_free_records": int(min(s["free"] for s in stats)),
            "allocation_failures": int(stats[-1]["failures"]),
            "late_moving_combat_ai_slots": sorted(moving_ai),
            "late_displacements": len(movements), "final_minute_displacements": len(recent),
            "examples": movements[-20:]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--players", type=int, default=10)
    parser.add_argument("--minimum-frame", type=int, default=27000)
    parser.add_argument("--late-frame", type=int, default=12600)
    args = parser.parse_args()
    print(json.dumps(verify(args.log.read_text(), args.players, args.minimum_frame, args.late_frame), indent=2))
