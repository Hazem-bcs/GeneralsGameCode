"""Structured parser of opt-in LOCAL_* runtime logs."""
from collections import defaultdict
from dataclasses import dataclass, field
import re

PAIRS = re.compile(r"(\w+)=([^\s]+)")

def parse_fields(line):
    row = {}
    for key, value in PAIRS.findall(line):
        try:
            row[key] = float(value) if "." in value else int(value)
        except ValueError:
            row[key] = value
    return row

@dataclass
class Run:
    snapshots: dict = field(default_factory=lambda: defaultdict(dict))
    ground: dict = field(default_factory=lambda: defaultdict(list))
    pathfind: list = field(default_factory=list)
    headers: list = field(default_factory=list)

def parse_log(text):
    run = Run()
    frame = None
    for line in text.splitlines():
        if line.startswith("LOCAL_SKIRMISH frame="):
            header = parse_fields(line)
            frame = int(header["frame"])
            run.headers.append(header)
        elif line.startswith("LOCAL_SKIRMISH slot=") and frame is not None:
            record = parse_fields(line)
            slot = int(record["slot"])
            if slot in run.snapshots[frame]:
                raise ValueError("Duplicate slot observation")
            run.snapshots[frame][slot] = record
        elif line.startswith("LOCAL_GROUND "):
            record = parse_fields(line)
            if not all(k in record for k in ("frame", "slot", "id", "x", "y", "combat")):
                raise ValueError("Malformed LOCAL_GROUND observation")
            run.ground[int(record["frame"])].append(record)
        elif line.startswith("LOCAL_PATHFIND "):
            run.pathfind.append(parse_fields(line))
    return run
