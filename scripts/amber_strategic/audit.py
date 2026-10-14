"""Conservative static vehicle checks, not a substitute for engine movement."""
from collections import deque
import math
from .config import TerrainConfig, PASS_Y

def grid_index(x,y,width,border):
    return (round(y/10)+border)*width+round(x/10)+border

def flood_reached(walkable, width, origin):
    """Reachable cell mask on a conservative four-neighbor vehicle grid."""
    visited = bytearray(len(walkable))
    visited[origin] = 1
    queue = deque([origin])
    while queue:
        i = queue.popleft()
        y, x = divmod(i, width)
        for j in (i - 1, i + 1, i - width, i + width):
            yy, xx = divmod(j, width)
            if abs(xx-x) + abs(yy-y) != 1 or not walkable[j] or visited[j]:
                continue
            visited[j] = 1
            queue.append(j)
    return visited

def audit(heights,cliffs,layout,width,rows,border,config=TerrainConfig()):
    n=width*rows
    playable=[y*width+x for y in range(border,rows-border)
              for x in range(border,width-border)]
    flat=sum(abs(heights[i]-config.base_height)<=5 for i in playable)/len(playable)
    min_height=min(heights[i] for i in playable)
    max_height=max(heights[i] for i in playable)
    walkable=bytearray(n)
    rough_slopes=0
    for y in range(border,rows-border):
        for x in range(border,width-border):
            i=y*width+x
            steep=max(abs(heights[i]-heights[i+d]) for d in (-1,1,-width,width))
            if steep>config.max_neighbour_change:
                rough_slopes+=1
                continue
            if any(cliffs[i+dy*width+dx] for dx,dy in ((0,0),(-2,0),(2,0),(0,-2),(0,2))):
                continue
            walkable[i]=1
    starts=[tuple(site) for site in layout['starts']]
    sites=starts+[(x,y) for x,y,_ in layout['supplies']+layout['tech']]
    sites += [tuple(p) for route in layout['ai_paths'] for p in route['vertices']]
    origin=grid_index(*starts[0],width,border)
    reached=flood_reached(walkable,width,origin)
    isolated=[list(site) for site in sites if not reached[grid_index(*site,width,border)]]
    pad_fractions=[]
    for sx,sy in starts:
        samples=[(sx+dx,sy+dy) for dx in range(-400,401,40)
                 for dy in range(-400,401,40) if dx*dx+dy*dy<=400*400]
        valid=sum(walkable[grid_index(x,y,width,border)] and
                  abs(heights[grid_index(x,y,width,border)]-config.base_height)<=2
                  for x,y in samples)
        pad_fractions.append(round(valid/len(samples),4))
    crossings={}
    for y in PASS_Y:
        checks=[(2350,y),(2850,y),(3150,y),(3650,y)]
        crossings[str(y)]=all(reached[grid_index(x,yy,width,border)] for x,yy in checks)
    symmetry=all(heights[grid_index(x,y,width,border)]==
                 heights[grid_index(6000-x,y,width,border)]
                 for x in range(100,3000,100) for y in range(100,6000,200))
    errors=[]
    if flat>config.max_flat_fraction: errors.append('Excessive flat terrain')
    if isolated: errors.append('Isolated starts, resources or AI route vertices')
    if min(pad_fractions)<config.min_build_fraction: errors.append('Insufficient level build pads')
    if not all(crossings.values()): errors.append('One or more crossings are blocked')
    if not symmetry: errors.append('Mirrored elevation fairness failed')
    return {'passed':not errors,'errors':errors,'grid':{'width':width,'height':rows,
            'border':border,'cell_world':10},
            'base_height':config.base_height,'min_height':min_height,'max_height':max_height,
            'flat_fraction_within_5':round(flat,4),'slope_cells_over_limit':rough_slopes,
            'static_vehicle_reachable_cells':sum(reached),'checked_sites':len(sites),
            'isolated_sites':isolated,'pad_fraction_by_base':pad_fractions,
            'crossing_reachable':crossings,'east_west_mirrored':symmetry,
            'method':'4-neighbor flood fill; <=7 height delta per 10-world tile; 20-world cliff avoidance; NOT game pathfinder'},walkable
