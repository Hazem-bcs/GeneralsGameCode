"""CkMp v4/v8 binary codec; existing objects and waypoint network are untouched."""
from array import array
import struct
import sys

from map_probe import MapFormatError
from map_resize_lab import parse_chunks
from build_five_aside_desert_map import read_texture_classes
from .config import PALETTE

CHUNK_HEADER = struct.Struct('<IHi')

def inspect_source(data):
    table,chunks=parse_chunks(data)
    index={name:i for i,(_,_,_,name) in enumerate(chunks)}
    if not {'HeightMapData','BlendTileData','ObjectsList','WaypointsList'}<=index.keys():
        raise MapFormatError('Missing required CkMp data chunks')
    h=chunks[index['HeightMapData']]
    b=chunks[index['BlendTileData']]
    if h[1]!=4 or b[1]!=8:
        raise MapFormatError('Requires HeightMapData v4 / BlendTileData v8')
    width,rows,border,bounds,bx,by,n=struct.unpack_from('<7i',h[2])
    if (width-2*border,rows-2*border)!=(600,600) or n!=width*rows:
        raise MapFormatError('Requires 600x600 height grid')
    if len(h[2])!=28+n or struct.unpack_from('<i',b[2])[0]!=n:
        raise MapFormatError('Inconsistent CkMp grid payload')
    return table,chunks,index,width,rows,border

def encode(source, heights, materials, cliff_cells):
    table,chunks,index,width,rows,border=inspect_source(source)
    n=width*rows
    if not all(len(field)==n for field in (heights,materials,cliff_cells)):
        raise MapFormatError('Terrain arrays must match grid dimensions')
    hi,bi=index['HeightMapData'],index['BlendTileData']
    h=chunks[hi]
    chunks[hi]=(h[0],h[1],h[2][:28]+bytes(heights),h[3])
    previous=chunks[bi]
    bitmap_count,classes,raw_classes=read_texture_classes(previous[2],width,rows)
    palette=[next((entry for entry in classes if entry[3]==name),None) for name in PALETTE]
    if any(entry is None for entry in palette):
        raise MapFormatError('Owner map lacks the required private texture class')
    def tile(kind,gx,gy):
        first,unused,edge,unused_name=palette[kind]
        return 4*(first+(gx//2)%edge+((gy//2)%edge)*edge)+(gx&1)+2*(gy&1)
    base=array('H',[0])*n
    blended=array('H',[0])*n
    records,identifiers=[],{}
    for gy in range(rows):
        for gx in range(width):
            i=gy*width+gx
            kind=materials[i]
            base[i]=tile(kind,gx,gy)
            for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
                xx,yy=gx+dx,gy+dy
                if 0<=xx<width and 0<=yy<rows and materials[yy*width+xx]<kind:
                    target=tile(materials[yy*width+xx],gx,gy)
                    key=(target,bool(dx),bool(dy),dx<0 or dy<0)
                    if key not in identifiers:
                        identifiers[key]=len(records)+1
                        records.append(struct.pack('<i6BiI',target,bool(dx),bool(dy),0,0,dx<0 or dy<0,0,-1,0x7ADA0000))
                    blended[i]=identifiers[key]
                    break

    if len(records)>=16000:
        raise MapFormatError('Tile blend identifier overflow')
    if sys.byteorder!='little':
        base.byteswap()
        blended.byteswap()
    flags=bytearray(((width+7)//8)*rows)
    for i,blocked in enumerate(cliff_cells):
        if blocked:
            gy,gx=divmod(i,width)
            flags[gy*((width+7)//8)+gx//8]|=1<<(gx%8)
    payload=(struct.pack('<i',n)+base.tobytes()+blended.tobytes()
             +bytes(n*4)+flags
             +struct.pack('<4i',bitmap_count,len(records)+1,1,len(classes))
             +raw_classes+struct.pack('<2i',0,0)+b''.join(records))
    chunks[bi]=(previous[0],previous[1],payload,previous[3])
    output=table+b''.join(CHUNK_HEADER.pack(i,v,len(payload))+payload
                          for i,v,payload,_ in chunks)
    return output,{'blend_records':len(records),'cliff_cells':sum(cliff_cells)}

def nonterrain_sha(data):
    """Checks that the complete original object and route payloads remain identical."""
    import hashlib
    _,chunks,index,*_=inspect_source(data)
    return {name:hashlib.sha256(chunks[index[name]][2]).hexdigest()
            for name in ('ObjectsList','WaypointsList','SidesList','PolygonTriggers')}
