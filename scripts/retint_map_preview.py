#!/usr/bin/env python3
"""Repaint a private Amber minimap preview using its actual terrain-tile classes.

The supplied base preview is from the owner's own game asset files. It is
never embedded in the source repository. This affects UI preview only.
"""
import argparse
import math
import struct
from pathlib import Path

from PIL import Image

from build_five_aside_desert_map import read_texture_classes
from map_resize_lab import parse_chunks


def render(old_preview: Image.Image, map_bytes: bytes):
    table, chunks = parse_chunks(map_bytes)
    parts = {name: data for _,_,data,name in chunks}
    height=parts["HeightMapData"]
    width, rows, border = struct.unpack_from("<3i",height)
    blend=parts["BlendTileData"]
    num,=struct.unpack_from("<i",blend)
    if num != width*rows:
        raise ValueError("Blended tile count doesn't match map")
    _, classes, _ = read_texture_classes(blend,width,rows)
    pix=old_preview.convert("RGB").copy()
    data=pix.load()
    for py in range(pix.height):
        y=int((py+.5)/pix.height*(rows-2*border)*10)
        gy=min(rows-border-1, border+y//10)
        for px in range(pix.width):
            x=int((px+.5)/pix.width*(width-2*border)*10)
            gx=min(width-border-1,border+x//10)
            tile,=struct.unpack_from("<H",blend,4+2*(gy*width+gx))
            tile_idx=tile//4
            name=next((kind for first,tiles,edge,kind in classes
                       if first<=tile_idx<first+tiles),"")
            if name not in ("SandMediumType10","SandMediumType7Rocky"):
                continue
            orig=data[px,py]
            # Preserve hill shading/markers from the owner preview;
            # soften hue only where the updated .map uses added textures.
            if name=="SandMediumType10":
                target=(229,191,139)
                alpha=.22
            else:
                target=(141,113,86)
                alpha=.30
            data[px,py]=tuple(round((1-alpha)*orig[i]+alpha*target[i])
                              for i in range(3))
    return pix


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("old_preview",type=Path)
    p.add_argument("new_map",type=Path)
    p.add_argument("new_preview",type=Path)
    p.add_argument("--inspect-png",type=Path)
    args=p.parse_args()
    if args.new_preview.exists():
        p.error("Refusing to overwrite an existing minimap preview")
    if args.new_preview.resolve()==args.old_preview.resolve():
        p.error("Never overwrite the licensed source preview")
    with Image.open(args.old_preview) as original:
        result=render(original,args.new_map.read_bytes())
    result.save(args.new_preview,format="TGA")
    if args.inspect_png:
        result.save(args.inspect_png,format="PNG")
    print("Created", args.new_preview, result.size)


if __name__ == "__main__":
    main()
