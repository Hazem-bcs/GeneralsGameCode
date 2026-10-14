"""v6 terrain-agent contract adapter; native map supplies authoritative route IDs."""
from collections import defaultdict
import hashlib
import math
import re
import struct

from extend_map_player_starts import _read_objects, _wpid
from map_resize_lab import parse_chunks

ROUTE_LABEL = re.compile(rb"(?:Center|Flank|Backdoor)(?:10|[1-9])(?!\d)")

def native_routes(map_bytes):
    """Extract labelled route IDs and directed edges, never assume per-slot ID ranges."""
    _,chunks=parse_chunks(map_bytes)
    parts={name:payload for _,_,payload,name in chunks}
    found=defaultdict(list)
    for _,_,record in _read_objects(parts["ObjectsList"]):
        ident=_wpid(record)
        if ident is None:
            continue
        labels={match.decode("ascii") for match in ROUTE_LABEL.findall(record)}
        if len(labels)>1:
            raise ValueError(f"Ambiguous route labels on waypoint {ident}")
        for label in labels:
            found[label].append((ident,struct.unpack_from("<2f",record)))
    payload=parts["WaypointsList"]
    count=struct.unpack_from("<i",payload)[0]
    if count<0 or len(payload)!=4+count*8:
        raise ValueError("Invalid native waypoint link table")
    links={struct.unpack_from("<2i",payload,4+i*8) for i in range(count)}
    if len(links)!=count:
        raise ValueError("Duplicate native waypoint link")
    return found,links

def _check_ids(records, name, count):
    ids=[record["id"] for record in records]
    if sorted(ids)!=list(range(1,count+1)):
        raise ValueError(f"{name}: expected contiguous one-based identifiers")
def normalize_contract(contract, map_bytes):
    """Return legacy-layout-shaped authoritative data from terrain schema v1.

    A native map is mandatory: contract waypoints have no binary waypoint IDs.
    This rejects stale maps, missing/ambiguous vertices or broken link direction.
    """
    if contract.get("schema_version") != 1:
        raise ValueError("Unsupported map contract schema")
    digest=hashlib.sha256(map_bytes).hexdigest()
    if contract.get("map_sha256") != digest:
        raise ValueError("Contract SHA256 does not match private map")
    bases=contract["bases"]
    resources=contract["resources"]
    tech=contract["neutral_tech"]
    corridors=contract["vehicle_corridors"]
    _check_ids(bases,"base",10)
    _check_ids(resources,"resource",len(resources))
    starts=[record["at"] for record in sorted(bases,key=lambda x:x["id"])]
    teams={r["id"]:r["team"] for r in bases}
    expected_teams={id_:1 if id_ in contract["teams"]["west"] else 2
                    for id_ in range(1,11)}
    if teams != expected_teams or set(contract["teams"]["west"]) != set(range(1,6)) or \
            set(contract["teams"]["east"]) != set(range(6,11)):
        raise ValueError("Contract player IDs/teams do not match local five-aside setup")
    labelled,links=native_routes(map_bytes)
    route_labels=set()
    paths=[]
    for corridor in corridors:
        label=corridor["id"]
        if corridor.get("direction")!="inbound_to_labelled_base":
            raise ValueError(f"{label}: route direction must be inbound")
        if label in route_labels:
            raise ValueError(f"Duplicate route: {label}")
        route_labels.add(label)
        vertices=corridor["vertices"]
        actual=labelled.get(label,[])
        if len(actual)!=len(vertices) or len(vertices)<2:
            raise ValueError(f"{label}: map and contract waypoint count differs")
        ordered_ids=[]
        remaining=dict(actual)
        for point in vertices:
            matches=[ident for ident,located in remaining.items()
                     if math.dist(located,point)<0.1]
            if len(matches)!=1:
                raise ValueError(f"{label}: missing or ambiguous native waypoint location")
            chosen=matches[0]
            ordered_ids.append(chosen)
            del remaining[chosen]
        required=set(zip(ordered_ids,ordered_ids[1:]))
        if not required.issubset(links):
            raise ValueError(f"{label}: missing or reversed directed waypoint link")
        paths.append(dict(label=label,ids=ordered_ids,vertices=vertices))
    required_labels={f"{kind}{i}" for i in range(1,11)
                     for kind in ("Center","Flank","Backdoor")}
    if route_labels!=required_labels or set(labelled)!=required_labels:
        raise ValueError("Native map and contract must define all thirty routes")
    if len(links)!=sum(len(p["ids"])-1 for p in paths):
        raise ValueError("Unexpected native route links in map")
    _,chunks=parse_chunks(map_bytes)
    height_blob=next(blob for _,_,blob,name in chunks if name=="HeightMapData")
    dimensions=struct.unpack_from("<3i",height_blob)
    grid=contract["grid"]
    if dimensions!=(grid["width"],grid["height"],grid["border"]):
        raise ValueError("Map grid does not match contract")
    layout=dict(
        starts=starts,
        supplies=[[x["at"][0],x["at"][1],x["kind"]] for x in resources],
        tech=[[x["at"][0],x["at"][1],x["kind"]] for x in tech],
        ai_paths=paths,
        style="v6",
        contract_name=contract["map"],
        map_sha256=digest
    )
    if "ai_route_policy" in contract:
        layout["ai_route_policy"]=contract["ai_route_policy"]
    from strategic_ai.native_map import native_audit
    native_audit(map_bytes,layout)
    return layout
