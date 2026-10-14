"""Static cliff clearance sampler; never assumes engine collision validity."""
import math
import struct
from map_resize_lab import parse_chunks

def mask_reader(data):
    _,chunks=parse_chunks(data)
    blobs={name:p for _,_,p,name in chunks}
    width,height,border=struct.unpack_from("<3i",blobs["HeightMapData"])
    mask=blobs["BlendTileData"]
    stride=(width+7)//8
    start=4+8*width*height
    if len(mask)<start+stride*height:
        raise ValueError("Incomplete cliff mask")
    def blocked(x,y):
        gx=round(x/10)+border;gy=round(y/10)+border
        if gx<3 or gy<3 or gx>=width-3 or gy>=height-3:return True
        return any(mask[start+(gy+dy)*stride+(gx+dx)//8]&(1<<((gx+dx)%8))
                   for dx,dy in ((0,0),(-2,0),(2,0),(0,-2),(0,2)))
    return blocked,width,height,border

def audit_cliffs(data,layout):
    blocked,_,_,_=mask_reader(data)
    violations=[]
    for route in layout["ai_paths"]:
        for index,(a,b) in enumerate(zip(route["vertices"],route["vertices"][1:])):
            steps=max(1,math.ceil(math.dist(a,b)/20))
            for tick in range(steps+1):
                x=a[0]+(b[0]-a[0])*tick/steps
                y=a[1]+(b[1]-a[1])*tick/steps
                if blocked(x,y):
                    violations.append(dict(path=route["label"],segment=index,
                                           point=[round(x),round(y)]))
                    break
    return dict(failed_segments=len(violations),violations=violations)
