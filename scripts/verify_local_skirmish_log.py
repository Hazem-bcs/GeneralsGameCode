#!/usr/bin/env python3
"""Validate actual Wine simulation observations from -localskirmish runs."""
import argparse
import json
from pathlib import Path
import re


def verify(text, players=10, minimum_frame=900, economy=False, expansion=False, five_aside=False, hard_ai=False):
    if re.search(r"stack overflow|EXCEPTION_ACCESS_VIOLATION|LOCAL_SKIRMISH rejected|serialization=FAIL", text, re.I):
        raise ValueError("Runtime reported a crash or rejected the setup")
    observations = []
    current = None
    for line in text.splitlines():
        if line.startswith("LOCAL_SKIRMISH frame="):
            current = dict(re.findall(r"(\w+)=([^ ]+)", line))
            current["slots"] = []
            observations.append(current)
        elif line.startswith("LOCAL_SKIRMISH slot=") and current is not None:
            current["slots"].append({key: int(value) for key, value in re.findall(r"(\w+)=(-?\d+)", line)})
        elif line.startswith("LOCAL_SITE ") and current is not None:
            current.setdefault("sites", []).append({key: float(value) for key, value in re.findall(r"(\w+)=(-?[\d.]+)", line)})
    if not observations or int(observations[-1]["frame"]) < minimum_frame:
        raise ValueError("Simulation did not reach the required frame")
    for observation in observations:
        slots = observation["slots"]
        if observation["network"] != "none" or int(observation["occupied"]) != players:
            raise ValueError("Wrong player count or an unexpected network instance")
        if {slot["slot"] for slot in slots} != set(range(players)):
            raise ValueError("Missing or duplicate slot observations")
        if sum(slot["ai"] for slot in slots) != players - 1 or slots[0]["ai"] != 0:
            raise ValueError("Expected one human and all other slots to be AI")
        if "skirmishAI" in slots[0]:
            if any(slot["skirmishAI"] != slot["ai"] or slot["local"] != (slot["slot"] == 0) for slot in slots):
                raise ValueError("Runtime player controllers do not match the local setup")
        for key in ("player", "start", "color"):
            values = [slot[key] for slot in slots]
            if min(values) < 0 or len(set(values)) != players:
                raise ValueError(f"Invalid or duplicate {key} assignment")
        if int(observation["frame"]) == 150 and any(slot["objects"] < 2 for slot in slots):
            raise ValueError("A player did not receive initial objects")
        if five_aside and (players != 10 or any(slot.get("team") != slot["slot"] // 5 or
                                              slot["start"] != slot["slot"] for slot in slots)):
            raise ValueError("Expected two teams of five at the fixed west/east starts")
        if hard_ai and any(slot.get("aiState") != 4 for slot in slots[1:]):
            raise ValueError("An AI slot is not Hard Army")
    active = observations[-1]["slots"][1:]
    if economy:
        for slot in active:
            if slot.get("earned", 0) <= 0 or slot.get("builtUnits", 0) < 3:
                raise ValueError(f"AI slot {slot['slot']} did not collect supplies and produce units")
            if not any(item["slots"][slot["slot"]].get("combatUnits", 0) > 0 for item in observations):
                raise ValueError(f"AI slot {slot['slot']} never fielded combat units")
        earlier = next((item for item in observations if int(item["frame"]) >= 3600), None)
        if earlier and int(earlier["frame"]) < int(observations[-1]["frame"]):
            if any(slot["earned"] <= earlier["slots"][slot["slot"]]["earned"] for slot in active):
                raise ValueError("An AI economy stopped earning resources")
    if expansion and any(slot.get("supplyCenters", 0) < 2 for slot in active):
        raise ValueError("An AI did not complete a second supply center")
    if five_aside and minimum_frame >= 9000:
        for slot in active:
            history = [item["slots"][slot["slot"]] for item in observations]
            if not any(x.get("frontlineUnits", 0) > 0 or x.get("kills", 0) > 0 for x in history):
                raise ValueError(f"AI slot {slot['slot']} has not reached battle or registered combat")
    return {"players": players, "human": 1, "ai": players - 1,
            "economy_verified": economy, "expansion_verified": expansion,
            "five_aside_verified": five_aside, "hard_ai_verified": hard_ai,
            "frames": [int(item["frame"]) for item in observations],
            "initial_slots": observations[0]["slots"], "latest_slots": observations[-1]["slots"],
            "latest_sites": observations[-1].get("sites", [])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--players", type=int, default=10)
    parser.add_argument("--minimum-frame", type=int, default=900)
    parser.add_argument("--economy", action="store_true")
    parser.add_argument("--expansion", action="store_true")
    parser.add_argument("--five-aside", action="store_true")
    parser.add_argument("--hard-ai", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.log.read_text(), args.players, args.minimum_frame,
                            args.economy, args.expansion, args.five_aside, args.hard_ai), indent=2))
