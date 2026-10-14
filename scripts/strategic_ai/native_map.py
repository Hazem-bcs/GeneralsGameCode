"""Audit and optionally overlay native CkMp waypoint positions, never terrain."""
import math
import struct
from map_resize_lab import parse_chunks
from extend_map_player_starts import _read_objects, _wpid, OBJECT_HEADER

def native_audit(data, layout):
    _,chunks=parse_chunks(data)
    by_name={name:payload for _,_,payload,name in chunks}
    routes={node["id"]:(node["label"],node["proposed"])
            for node in waypoint_records(layout)}
    observed={}
    for _,_,payload in _read_objects(by_name["ObjectsList"]):
        ident=_wpid(payload)
        if ident in routes:
            if ident in observed:raise ValueError("Duplicate waypoint ID")
            observed[ident]=struct.unpack_from("<2f",payload)
    missing=routes.keys()-observed.keys()
    if missing:raise ValueError(f"Missing route waypoint IDs: {sorted(missing)}")
    for ident,(_,expected) in routes.items():
        if math.dist(observed[ident],expected)>0.05:
            raise ValueError(f"Native waypoint {ident} coordinate mismatch")
    links_data=by_name["WaypointsList"]
    count=struct.unpack_from("<i",links_data)[0]
    if count<0 or len(links_data)!=4+8*count:
        raise ValueError("Malformed native waypoint link table")
    actual=[struct.unpack_from("<2i",links_data,4+i*8) for i in range(count)]
    expected=[(a,b) for path in layout["ai_paths"]
              for a,b in zip(path["ids"],path["ids"][1:])]
    if len(set(actual))!=len(actual) or set(actual)!=set(expected):
        raise ValueError("Missing, reversed, unexpected or duplicate directed links")
    return dict(route_nodes=len(observed),directed_links=count,all_links_expected=True)

def waypoint_records(layout):
    for route in layout["ai_paths"]:
        for ident,coordinates in zip(route["ids"],route["vertices"]):
            yield dict(id=ident,label=route["label"],proposed=coordinates)
def overlay_waypoints(data,layout):
    """Change existing route waypoint locations only; keep all other chunks identical."""
    from strategic_ai.routes import geometry_audit
    audit=geometry_audit(layout)
    if audit["issues"] or audit["collision_count"]:
        raise ValueError("Unsafe overlay: unresolved static route intersections")
    table,chunks=parse_chunks(data)
    new_positions={r["id"]:r["proposed"] for r in waypoint_records(layout)}
    found=set()
    result=[]
    for kind,ver,payload,name in chunks:
        if name!="ObjectsList":
            result.append((kind,ver,payload,name))
            continue
        items=[]
        for entry_kind,entry_ver,entry in _read_objects(payload):
            ident=_wpid(entry)
            if ident in new_positions:
                if ident in found:raise ValueError("Duplicate target waypoint")
                found.add(ident)
                entry=bytearray(entry)
                struct.pack_into("<2f",entry,0,*new_positions[ident])
                entry=bytes(entry)
            items.append(OBJECT_HEADER.pack(entry_kind,entry_ver,len(entry))+entry)
        result.append((kind,ver,b"".join(items),name))
    if found!=set(new_positions):
        raise ValueError("Target waypoint count mismatch")
    patched=table+b"".join(OBJECT_HEADER.pack(k,v,len(p))+p for k,v,p,_ in result)
    native_audit(patched,layout)
    return patched
