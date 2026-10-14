#!/usr/bin/env python3
"""Validate base exits and contingency flank routes from an owner-private .map."""
import argparse
import json
from pathlib import Path

from amber_strategic.audit import audit,flood_reached,grid_index
from amber_strategic.ckmp import inspect_source
from map_resize_lab import parse_chunks

def verify(map_file, contract_file):
    data=map_file.read_bytes()
    _,chunks,_,width,rows,border=inspect_source(data)
    payload={name:part for _,_,part,name in chunks}
    height=payload['HeightMapData'][28:]
    bp=payload['BlendTileData']
    stride=(width+7)//8
    encoded=bp[4+width*rows*8:4+width*rows*8+stride*rows]
    cliffs=bytearray(width*rows)
    for y in range(rows):
        for x in range(width):
            cliffs[y*width+x]=bool(encoded[y*stride+x//8]&(1<<(x%8)))
    layout=json.loads(map_file.with_suffix('.layout.json').read_text())
    contract=json.loads(contract_file.read_text())
    base_report,walkable=audit(height,cliffs,layout,width,rows,border)
    assert base_report['passed'],base_report['errors']
    exits={base['id']:grid_index(*base['exit'],width,border) for base in contract['bases']}
    starts={base['id']:grid_index(*base['at'],width,border) for base in contract['bases']}
    reachable=flood_reached(walkable,width,starts[1])
    exit_ok={str(i):bool(walkable[idx] and reachable[idx]) for i,idx in exits.items()}
    blocked=bytearray(walkable)
    for gy in range(border+275,border+326):
        begin=gy*width+border+270
        blocked[begin:begin+61]=bytes(61)
    detour=flood_reached(blocked,width,starts[3])
    other_side=detour[starts[8]]!=0
    flank_points={
        'north':grid_index(3000,480,width,border),
        'south':grid_index(3000,5520,width,border)
    }
    flank_ok={name:bool(detour[idx]) for name,idx in flank_points.items()}
    errors=[]
    if not all(exit_ok.values()): errors.append('One or more vehicle exits unreachable')
    if not other_side: errors.append('No east-west detour with central crossing closed')
    if not all(flank_ok.values()): errors.append('One or more flank passages isolated')
    return {'passed':not errors,'errors':errors,
            'exit_reachable':exit_ok,
            'central_crossing_blocked_detour':other_side,
            'flank_crossings_accessible':flank_ok,
            'pathfinding_kind':'STATIC terrain approximation; game engine required'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('map',type=Path)
    p.add_argument('contract',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    result=verify(args.map,args.contract)
    print(json.dumps(result,indent=2))
    if args.report:
        if args.report.exists():
            p.error('Refusing to overwrite existing report')
        args.report.write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:
        raise SystemExit(1)

if __name__=='__main__':
    main()
