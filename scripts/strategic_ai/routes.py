"""Native waypoint geometry contract: no licensed maps or terrain generation."""
from copy import deepcopy
import math

def segment_clearance(point,a,b):
    dx=b[0]-a[0]; dy=b[1]-a[1]
    t=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy)

def geometry_audit(layout, supply_clearance=195, tech_clearance=155):
    """Audit full line segments: checking waypoint endpoints alone misses collisions."""
    issues=[]
    starts=layout["starts"]
    paths=layout["ai_paths"]
    if len(starts)!=10 or len(paths)!=30:
        issues.append("Expected 10 starts and 30 paths")
    labels=[p["label"] for p in paths]
    if len(labels)!=len(set(labels)):
        issues.append("Duplicate route names")
    for n in range(1,len(starts)+1):
        for kind in ("Center","Flank","Backdoor"):
            if f"{kind}{n}" not in labels:
                issues.append(f"Missing {kind}{n}")
    collisions={}
    for path in paths:
        label=path["label"]
        if len(path["vertices"])!=len(path["ids"]) or len(path["vertices"])<2:
            issues.append(f"{label}: invalid number of path vertices");continue
        try:
            start_number=int("".join(c for c in label if c.isdigit()))
            target=starts[start_number-1]
        except (IndexError,ValueError):
            issues.append(f"{label}: unknown start");continue
        if math.dist(path["vertices"][-1],target)>1000:
            issues.append(f"{label}: endpoint too far from labelled base")
        if math.dist(path["vertices"][0],target)<1500:
            issues.append(f"{label}: reversed or too short inbound route")
        violations=[]
        for idx,(a,b) in enumerate(zip(path["vertices"],path["vertices"][1:])):
            for j,site in enumerate(layout["supplies"]):
                gap=segment_clearance(site[:2],a,b)
                if gap < supply_clearance:
                    violations.append(dict(segment=idx,site=f"supply:{j}",clearance=round(gap,1)))
            for j,site in enumerate(layout["tech"]):
                gap=segment_clearance(site[:2],a,b)
                if gap < tech_clearance:
                    violations.append(dict(segment=idx,site=f"tech:{j}",clearance=round(gap,1)))
        if violations:collisions[label]=violations
    return dict(issues=issues,collisions=collisions,collision_count=sum(map(len,collisions.values())),
                interfering_routes=len(collisions),path_count=len(paths))

def propose_routes(layout):
    """Map-layout overlay candidate, independent of texture or C++ engine."""
    if layout.get("style") not in ("v4", "v5") and "ai_route_policy" not in layout:
        raise ValueError("Non-v5 maps need an explicit ai_route_policy in map_contract.json")
    policy=layout.get("ai_route_policy", {})
    center_x=policy.get("midline_x", sum((min(p[0] for p in layout["starts"]),
                                          max(p[0] for p in layout["starts"])))/2)
    center_y=policy.get("midline_y", sum((min(p[1] for p in layout["starts"]),
                                          max(p[1] for p in layout["starts"])))/2)
    cross_index=policy.get("crossing_vertex_index", 3)
    center_indexes=policy.get("center_vertex_indexes", (2,3,4,5))
    flank_indexes=policy.get("flank_vertex_indexes", (3,4))
    center_offset=policy.get("center_offset", 225)
    flank_offset=policy.get("flank_offset", 220)
    inward_fraction=policy.get("inward_fraction", .15)
    expected_vertices=policy.get("vertices_per_path", 8)
    amended=deepcopy(layout)
    for path in amended["ai_paths"]:
        vertices=path["vertices"]
        if len(vertices)!=expected_vertices:
            raise ValueError("Expected eight path vertices")
        kind="".join(c for c in path["label"] if not c.isdigit())
        crossing=vertices[cross_index][1]
        if kind=="Center":
            for idx in center_indexes:
                x=vertices[idx][0]
                vertices[idx][1]=crossing+(center_offset if x>center_x else -center_offset)
        else:
            outer=1 if crossing<center_y else -1
            if kind=="Backdoor":outer*=-1
            for idx in flank_indexes:
                vertices[idx][1]=crossing+outer*flank_offset
        n=int("".join(c for c in path["label"] if c.isdigit()))
        target=amended["starts"][n-1]
        vertices[-1][0]+=inward_fraction*(target[0]-vertices[-1][0])
    return amended

def diff_paths(old,new):
    before={p["label"]:p for p in old["ai_paths"]}
    changes=[]
    for path in new["ai_paths"]:
        previous=before[path["label"]]
        for i,(a,b) in enumerate(zip(previous["vertices"],path["vertices"])):
            if list(a)!=list(b):
                changes.append(dict(label=path["label"],id=path["ids"][i],
                                    previous=a,proposed=b))
    return changes
