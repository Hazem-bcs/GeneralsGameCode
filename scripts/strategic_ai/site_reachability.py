"""Check passable grid connectivity of bases, resources and route sites."""
from collections import deque
from strategic_ai.terrain_clearance import mask_reader

def audit_sites(data,layout):
    blocked,width,height,border=mask_reader(data)
    x_max=width-2*border;y_max=height-2*border
    start=layout["starts"][0]
    origin=(round(start[0]/10),round(start[1]/10))
    queue=deque([origin]);seen={origin}
    while queue:
        x,y=queue.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            pos=(nx,ny)
            if pos in seen or not (0<=nx<x_max and 0<=ny<y_max):
                continue
            if blocked(nx*10,ny*10):continue
            seen.add(pos);queue.append(pos)
    targets=[("start",i,p[:2]) for i,p in enumerate(layout["starts"])]
    targets += [("supply",i,p[:2]) for i,p in enumerate(layout["supplies"])]
    targets += [("tech",i,p[:2]) for i,p in enumerate(layout["tech"])]
    for path in layout["ai_paths"]:
        targets.extend(("route",path["label"],p) for p in path["vertices"])
    inaccessible=[dict(kind=kind,id=ident,position=p)
                  for kind,ident,p in targets
                  if (round(p[0]/10),round(p[1]/10)) not in seen]
    return dict(tested_sites=len(targets),reachable_sites=len(targets)-len(inaccessible),
                unreachable=inaccessible)
