#!/usr/bin/env python3
"""Generate owner-private Amber v6 from v5; never overwrite maps or touch game engine."""
import argparse
import hashlib
import json
from pathlib import Path

from amber_strategic.audit import audit
from amber_strategic.ckmp import encode, inspect_source, nonterrain_sha
from amber_strategic.config import PASS_Y, TerrainConfig
from amber_strategic.terrain import TerrainField
from map_probe import inspect_map

def build_contract(layout, report, map_hash, seed):
    starts=[{'id':i+1,'team':1 if i<5 else 2,'at':point,
             'safe_build_radius':475,'exit':[
                point[0]+(520 if i<5 else -520),point[1]]}
            for i,point in enumerate(layout['starts'])]
    resources=[{'id':i+1,'at':[x,y],'kind':kind}
               for i,(x,y,kind) in enumerate(layout['supplies'])]
    paths=[{'id':p['label'],'direction':'inbound_to_labelled_base',
            'vertices':p['vertices']} for p in layout['ai_paths']]
    return {'schema_version':1,'map':'AmberCanyon_Strategic_v6',
            'seed':seed,'map_sha256':map_hash,'coordinates':'world units, bottom-left origin',
            'grid':report['grid'],'teams':{'west':[1,2,3,4,5],'east':[6,7,8,9,10]},
            'bases':starts,'resources':resources,
            'neutral_tech':[{'at':[x,y],'kind':kind} for x,y,kind in layout['tech']],
            'vehicle_corridors':paths,'crossings':[
                {'id':f'cross_{y}','at':[3000,y],'width_hint':250 if y in (1050,3000,4950) else 150,
                 'static_reachable':report['crossing_reachable'][str(y)]} for y in PASS_Y],
            'chokepoints':[{'at':[3000,y],'meaning':'central/edge pass'} for y in PASS_Y],
            'forbidden_areas':[{'type':'mountain_core','center':[3000,y],
                                'radius_hint':[490,570],'advisory_only':True} for y in (1900,4120)],
            'navigation':{'static_grid_clearance_world':20,
                          'static_max_height_step_per_10_world':7,
                          'all_key_sites_connected':not report['isolated_sites'],
                          'engine_vehicle_traversal_verified':False},
            'do_not_modify':'Treat contract as map-authoritative; AI agent must not edit terrain generator'}

def create_preview(heights, layout, width, border, destination):
    """Schematic only: grayscale terrain plus route/resource overlays."""
    from PIL import Image, ImageDraw
    im=Image.new('RGB',(600,600))
    pix=im.load()
    for y in range(600):
        for x in range(600):
            h=heights[(y+border)*width+x+border]
            if h>=170: color=(106,85,70)
            elif h>=120: color=(158,115,74)
            elif h>=90: color=(201,167,115)
            elif h<=61: color=(167,156,113)
            else: color=(222,197,149)
            pix[x,599-y]=color
    draw=ImageDraw.Draw(im)
    for x1,y1,x2,y2,radius in layout['roads']:
        draw.line([(x1//10,599-y1//10),(x2//10,599-y2//10)],
                  fill=(247,219,161),width=max(2,round(radius/55)))
    for x,y,kind in layout['supplies']:
        px,py=round(x/10),599-round(y/10)
        draw.ellipse((px-3,py-3,px+3,py+3),fill=(60,225,169))
    for i,(x,y) in enumerate(layout['starts']):
        px,py=round(x/10),599-round(y/10)
        fill=(60,130,225) if i<5 else (222,80,72)
        draw.ellipse((px-7,py-7,px+7,py+7),fill=fill,outline=(20,20,20),width=2)
        draw.text((px-3,py-5),str(i%5+1),fill=(255,255,255))
    im.resize((1200,1200),Image.Resampling.NEAREST).save(destination)
    return im

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path,help='Private Amber v5 .map')
    parser.add_argument('output_dir',type=Path,help='Fresh private AmberCanyon_Strategic_v6 directory')
    parser.add_argument('--seed',type=int,default=6014)
    args=parser.parse_args()
    if args.output_dir.exists():
        parser.error('Refusing to overwrite existing output directory')
    source=args.source.read_bytes()
    source_layout=json.loads(args.source.with_suffix('.layout.json').read_text())
    _,_,_,width,rows,border=inspect_source(source)
    config=TerrainConfig(seed=args.seed)
    print('Generating terrain grid...',flush=True)
    heights,materials,cliffs=TerrainField(source_layout,config).generate(width,rows,border)
    print('Running static vehicle/build/resource audit...',flush=True)
    audit_data,walkable=audit(heights,cliffs,source_layout,width,rows,border,config)
    print(json.dumps(audit_data,indent=2),flush=True)
    if not audit_data['passed']:
        raise RuntimeError('Static terrain audit failed; no map published')
    print('Encoding CkMp v4/v8 without touching objects...',flush=True)
    output,encoder_info=encode(source,heights,materials,cliffs)
    if nonterrain_sha(source)!=nonterrain_sha(output):
        raise RuntimeError('Object/waypoint payload changed unexpectedly')
    folder=args.output_dir
    folder.mkdir(parents=True)
    name='AmberCanyon_Strategic_v6'
    destination=folder/(name+'.map')
    destination.write_bytes(output)
    digest=hashlib.sha256(output).hexdigest()
    contract=build_contract(source_layout,audit_data,digest,args.seed)
    (folder/'map_contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    (folder/'terrain_audit.json').write_text(json.dumps({
        **audit_data,'generator':{'seed':args.seed,**encoder_info},
        'original_nonterrain_sha256':nonterrain_sha(source),
        'new_nonterrain_sha256':nonterrain_sha(output)},indent=2)+'\n')
    preview=create_preview(heights,source_layout,width,border,folder/'AmberCanyon-v6-terrain-plan.png')
    preview.resize((256,256),__import__('PIL.Image',fromlist=['Image']).Resampling.BILINEAR).save(folder/(name+'.tga'))
    (folder/'map.str').write_text('MapIntro:01\n"AMBER CANYON STRATEGIC V6 - 5 vs 5"\nEnd\n')
    (folder/(name+'.layout.json')).write_text(json.dumps({
        **source_layout,'title':'Amber Canyon Strategic v6','style':'v6',
        'terrain_audit':audit_data,'map_sha256':digest},indent=2)+'\n')
    output_report={'map':str(destination),'sha256':digest,
                   'static_audit':audit_data,'encoder':encoder_info,
                   'ckmp':inspect_map(destination),'engine_validation':'NOT RUN'}
    (folder/'generation_report.json').write_text(json.dumps(output_report,indent=2)+'\n')
    print('Created private map and audit:',destination,flush=True)

if __name__=='__main__':
    main()
