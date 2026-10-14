#!/usr/bin/env python3
"""Build an owner-asset desert map with ten starts grouped west/east, five each.

Only texture metadata and object prototypes are read from the supplied private map.
All elevation, terrain painting, routes, resource placement and decoration are new.
No licensed textures/models/maps are embedded here. Existing outputs are refused.
"""
import argparse
from array import array
from collections import deque
import json
import math
from pathlib import Path
import random
import re
import struct
import sys
from build_ten_base_map import object_name, replace_label
from extend_map_player_starts import _read_objects, _copy_start, OBJECT_HEADER, WAYPOINT_ID_PROPERTY
from map_probe import inspect_map, MapFormatError
from map_resize_lab import parse_chunks

BASE = 72
ROWS = (700, 1850, 3000, 4150, 5300)
PASSES = (1050, 3000, 4950)


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def distance_segment(x, y, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - x1 - t * dx, y - y1 - t * dy)


def read_texture_classes(data, width, height):
    n = width * height
    pos = 4 + 8 * n + ((width + 7) // 8) * height
    bitmap_count, _, _, count = struct.unpack_from('<4i', data, pos)
    pos += 16
    begin = pos
    classes = []
    for _ in range(count):
        first, tiles, edge, legacy = struct.unpack_from('<4i', data, pos)
        pos += 16
        length = struct.unpack_from('<H', data, pos)[0]
        pos += 2
        name = data[pos:pos + length].decode('ascii')
        pos += length
        classes.append((first, tiles, edge, name))
    return bitmap_count, classes, data[begin:pos]


def new_object(prototype, kind, label, x, y, angle=0):
    data = prototype[2]
    old_kind = object_name(data)
    old_name = re.search(rb'TenBaseSupply_\d+|SupplyDock \d+', data)
    if not old_name:
        raise MapFormatError('Supply prototype has no unique name')
    data = replace_label(data, old_kind, kind)
    data = replace_label(data, old_name[0].decode(), label)
    data = bytearray(data)
    struct.pack_into('<4f', data, 0, x, y, 0, angle)
    return prototype[0], prototype[1], bytes(data)


def route_waypoint(prototype, label, waypoint_id, x, y):
    data = prototype[2]
    old_name = re.search(rb'Waypoint \d+', data)
    if not old_name or data.count(b'Center1') != 2:
        raise MapFormatError('Center1 route waypoint prototype is missing')
    data = replace_label(data, old_name[0].decode(), f'AmberWaypoint_{waypoint_id}')
    data = bytearray(replace_label(data, 'Center1', label))
    struct.pack_into('<3f', data, 0, x, y, 0)
    struct.pack_into('<i', data, data.index(WAYPOINT_ID_PROPERTY) + 4, waypoint_id)
    return prototype[0], prototype[1], bytes(data)


def build(data, style='v4'):
    if style not in ('v4', 'v5'):
        raise ValueError('Supported visual styles are v4 and v5')
    detail_v5 = style == 'v5'

    table, chunks = parse_chunks(data)
    by_name = {n: i for i, (_, _, _, n) in enumerate(chunks)}
    hi, bi, oi = (by_name[n] for n in ('HeightMapData', 'BlendTileData', 'ObjectsList'))
    height = bytearray(chunks[hi][2])
    width, rows, border = struct.unpack_from('<3i', height)
    if (width - 2 * border, rows - 2 * border) != (600, 600) or chunks[bi][1] != 8:
        raise MapFormatError('Requires the private 600x600 map and BlendTileData v8')
    starts = [(900, y) for y in ROWS] + [(5100, y) for y in ROWS]
    supplies = []
    for side in (0, 1):
        reflect = lambda x: x if side == 0 else 6000 - x
        for y in ROWS:
            supplies += [(reflect(580), y + 320, 'home'), (reflect(1210), y + 320, 'home')]
        supplies += [(reflect(1850), y - 160, 'expansion') for y in ROWS]
    supplies += [(x, y, 'contested') for y in PASSES for x in (2550, 3450)]
    supplies += [(3000, 480, 'contested'), (3000, 5520, 'contested')]
    tech = [(x, y, 'TechOilDerrick') for x in (2210, 3790) for y in (1050, 4950)]
    tech += [(3000, 2730, 'TechHospital'), (3000, 3270, 'TechOilRefinery')]
    roads = [(1100, 480, 1100, 5520, 150), (4900, 480, 4900, 5520, 150),
             (1850, 480, 1850, 5520, 150), (4150, 480, 4150, 5520, 150)]
    roads += [(1400, y, 4600, y, 250) for y in PASSES]
    roads += [(900, y, 5100, y, 150) for y in (480, 5520)]
    for y in ROWS:
        roads += [(900, y, 1850, y - 160, 135), (5100, y, 4150, y - 160, 135)]
    # Deterministic organic terrain, exactly mirrored west/east.
    n = width * rows
    terrain = bytearray(n)
    cliffs = bytearray(((width + 7) // 8) * rows)
    road_mask = bytearray(n)
    for gy in range(rows):
        y = (gy - border) * 10
        for gx in range(width):
            x = (gx - border) * 10
            idx = gy * width + gx
            mx, my = abs(x - 3000), abs(y - 3000)
            ridge = 172 * math.exp(-(mx / 520) ** 2 - ((my - 1040) / 520) ** 4)
            ridge *= .87 + .08 * math.sin(mx / 75) + .05 * math.cos(my / 90)
            edge = max(0, 210 - min(x, y, 6000 - x, 6000 - y)) / 210
            h = BASE + ridge + 128 * min(1, edge) ** 2
            h += 2.5 * math.sin(mx / 145) * math.cos(my / 170)
            path_distances = [distance_segment(x, y, *r[:4]) for r in roads]
            path_dist = min(d - r[4] for d, r in zip(path_distances, roads))
            paint_dist = min(d - r[4] * .32 for d, r in zip(path_distances, roads))
            pad_dist = min(math.hypot(x - sx, y - sy) - 475 for sx, sy in starts)
            resource_dist = min(math.hypot(x - sx, y - sy) - 175 for sx, sy, _ in supplies)
            tech_dist = min(math.hypot(x - sx, y - sy) - 135 for sx, sy, _ in tech)
            clear = min(path_dist, pad_dist, resource_dist, tech_dist)
            grading = 1 - smooth(0, 140, clear)
            h = h * (1 - grading) + BASE * grading
            height[28 + idx] = round(max(BASE - 3, min(250, h)))
            if h > BASE + 35 and clear > 65:
                cliffs[gy * ((width + 7) // 8) + gx // 8] |= 1 << (gx % 8)
            if paint_dist < 0 and pad_dist > -90 and resource_dist > -100:
                kind = 1  # packed earth tracks
                road_mask[idx] = 1
            elif h > BASE + 80:
                kind = 2  # weathered cliff
            elif h > BASE + 22:
                kind = 3  # sandstone rubble
            elif (math.sin(mx / 210) + math.cos(my / 270) + .35 * math.sin((mx + my) / 85)) > .8:
                kind = 4  # secondary sand with natural patches
            else:
                kind = 0
            if detail_v5:
                # Paint weathered strata and windblown washes on the existing,
                # audited collision terrain. Both coordinates mirror across x=3000.
                # Roads, build pads and resources keep their original paint.
                ripple = (.55 * math.sin(mx / 103 + my / 237)
                          + .39 * math.cos(mx / 179 - my / 111)
                          + .2 * math.sin(my / 67))
                if kind == 3 and h > BASE + 34 and paint_dist > 105 and ripple > -.12:
                    kind = 6  # broken rocky sand at mesa foothills
                elif kind in (0, 4) and pad_dist > 110 and resource_dist > 110 and paint_dist > 105 and ripple > .48:
                    kind = 5  # dune-wash sand, no obstruction or height changes
            terrain[idx] = kind
    chunks[hi] = (*chunks[hi][:2], bytes(height), chunks[hi][3])
    bitmap_count, classes, raw_classes = read_texture_classes(chunks[bi][2], width, rows)
    wanted = ('SandMediumType6', 'DirtMediumType10', 'CliffLargeType11',
              'RocksMediumType1', 'SandMediumType8')
    palette = [next(c for c in classes if c[3] == name) for name in wanted]
    if detail_v5:
        # Texture names come from the owner's base map; no licensed asset is
        # embedded in this generator and the generated .map stays private.
        palette.extend(next(c for c in classes if c[3] == name)
                       for name in ('SandMediumType10', 'SandMediumType7Rocky'))
    def tile(kind, gx, gy):
        first, _, edge, _ = palette[kind]
        # Preserve the original texture's tile/quadrant ordering for seamless repetition.
        return 4 * (first + (gx // 2) % edge + ((gy // 2) % edge) * edge) + (gx & 1) + 2 * (gy & 1)
    base_tiles, blend_tiles = array('H', [0]) * n, array('H', [0]) * n
    blend_records, blend_ids = [], {}
    for gy in range(rows):
        for gx in range(width):
            idx = gy * width + gx
            kind = terrain[idx]
            base_tiles[idx] = tile(kind, gx, gy)
            # Feather class boundaries using real engine two-texture blend records.
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < width and 0 <= ny < rows and terrain[ny * width + nx] < kind:
                    target = tile(terrain[ny * width + nx], gx, gy)
                    key = (target, bool(dx), bool(dy), dx < 0 or dy < 0)
                    if key not in blend_ids:
                        blend_ids[key] = len(blend_records) + 1
                        blend_records.append(struct.pack('<i6BiI', target, bool(dx), bool(dy), 0, 0,
                                                         dx < 0 or dy < 0, 0, -1, 0x7ADA0000))
                    blend_tiles[idx] = blend_ids[key]
                    break
    if len(blend_records) >= 16000:
        raise MapFormatError('Too many terrain blend records')
    if sys.byteorder != 'little':
        base_tiles.byteswap(); blend_tiles.byteswap()
    blend = (struct.pack('<i', n) + base_tiles.tobytes() + blend_tiles.tobytes() + bytes(n * 4) + cliffs
             + struct.pack('<4i', bitmap_count, len(blend_records) + 1, 1, len(classes)) + raw_classes
             + struct.pack('<2i', 0, 0) + b''.join(blend_records))
    chunks[bi] = (*chunks[bi][:2], blend, chunks[bi][3])
    old_objects = _read_objects(chunks[oi][2])
    start_proto = next(o for o in old_objects if o[2].count(b'Player_8_Start') == 2)
    route_proto = next(o for o in old_objects if o[2].count(b'Center1') == 2)
    supply_proto = next(o for o in old_objects if object_name(o[2]) == 'SupplyDock')
    objects = [(start_proto[0], start_proto[1], _copy_start(start_proto[2],
                f'Player_{i + 1}_Start'.encode(), 100 + i, x, y)) for i, (x, y) in enumerate(starts)]
    links, ai_paths = [], []
    for i, (sx, sy) in enumerate(starts):
        mirrored = i >= 5
        reflect = lambda x: 6000 - x if mirrored else x
        center_pass = min(PASSES, key=lambda y: abs(y - sy))
        flank_pass = 480 if sy <= 3000 else 5520
        back_pass = 5520 if sy <= 3000 else 480
        for mode, crossing in enumerate((center_pass, flank_pass, back_pass)):
            label = ('Center', 'Flank', 'Backdoor')[mode] + str(i + 1)
            route = [(1650, sy), (1850, crossing), (2350, crossing), (2850, crossing),
                     (3150, crossing), (3650, crossing), (4150, crossing), (4700, sy)]
            if crossing == 480:
                # Keep flank goals off the first pair of forward supply docks.
                route[1] = (1650, crossing)
                route[-2] = (4350, crossing)
            # Skirmish scripts select the ENEMY's numbered path, then follow it
            # toward that enemy. Each numbered route must therefore be inbound.
            route.reverse()
            ids = []
            for j, (x, y) in enumerate(route):
                ident = 1000 + i * 100 + mode * 20 + j
                ids.append(ident)
                objects.append(route_waypoint(route_proto, label, ident, reflect(x), y))
            links += list(zip(ids, ids[1:]))
            ai_paths.append({'label': label, 'vertices': [(reflect(x), y) for x, y in route], 'ids': ids})
    objects += [new_object(supply_proto, 'SupplyDock', f'AmberSupply_{i + 1}', x, y,
                          math.pi if x > 3000 else 0) for i, (x, y, _) in enumerate(supplies)]
    objects += [new_object(supply_proto, kind, f'AmberTech_{i + 1}', x, y) for i, (x, y, kind) in enumerate(tech)]
    # Small ruins set back from the central roadway, with open approaches.
    villages = [(2650, 2680, 'MogadishuHouse03'), (3350, 2680, 'MogadishuHouse03'),
                (2670, 3340, 'MogadishuHouse05'), (3330, 3340, 'MogadishuHouse05')]
    objects += [new_object(supply_proto, kind, f'AmberVillage_{i + 1}', x, y,
                          0 if x < 3000 else math.pi) for i, (x, y, kind) in enumerate(villages)]
    rng = random.Random(5010)
    decorations = []
    for _ in range(155 if detail_v5 else 90):
        x, y = rng.randint(2420, 2980), rng.choice((rng.randint(1550, 2400), rng.randint(3600, 4450)))
        gx, gy = round(x / 10) + border, round(y / 10) + border
        if height[28 + gy * width + gx] < BASE + 65:
            continue
        if min(math.hypot(x - a, y - b) for a, b, _ in supplies + tech) < 300:
            continue
        if min(distance_segment(x, y, *r[:4]) - r[4] for r in roads) < 150:
            continue
        kind = rng.choice(('RockClusterMedium01', 'RockClusterSmall01', 'Rocks3Brown'))
        decorations += [(x, y, kind), (6000 - x, y, kind)]
    objects += [new_object(supply_proto, kind, f'AmberRock_{i + 1}', x, y, rng.random() * 6.28)
                for i, (x, y, kind) in enumerate(decorations)]
    payload = b''.join(OBJECT_HEADER.pack(i, v, len(d)) + d for i, v, d in objects)
    chunks[oi] = (*chunks[oi][:2], payload, chunks[oi][3])
    # Replace old water and AI links with the actual ten-slot route network.
    idx = by_name['PolygonTriggers']
    chunks[idx] = (*chunks[idx][:2], struct.pack('<i', 0), 'PolygonTriggers')
    idx = by_name['WaypointsList']
    payload = struct.pack('<i', len(links)) + b''.join(struct.pack('<2i', *link) for link in links)
    chunks[idx] = (*chunks[idx][:2], payload, 'WaypointsList')
    # Verify access after expanding cliff masks to allow for tank-sized clearance.
    def blocked(gx, gy):
        return bool(cliffs[gy * ((width + 7) // 8) + gx // 8] & (1 << (gx % 8)))
    clear_mask = bytearray(n)
    for gy in range(border, rows - border):
        for gx in range(border, width - border):
            clear_mask[gy * width + gx] = not any(blocked(gx + dx, gy + dy)
                for dx, dy in ((0, 0), (-2, 0), (2, 0), (0, -2), (0, 2)))
    origin = (int(starts[0][1] / 10) + border) * width + int(starts[0][0] / 10) + border
    reached, queue = bytearray(n), deque([origin]); reached[origin] = 1
    while queue:
        index = queue.popleft()
        for nxt in (index - 1, index + 1, index - width, index + width):
            if 0 <= nxt < n and not reached[nxt] and clear_mask[nxt]:
                reached[nxt] = 1; queue.append(nxt)
    sites = [(x, y) for x, y in starts] + [(x, y) for x, y, _ in supplies + tech]
    sites += [point for path in ai_paths for point in path['vertices']]
    if not all(reached[(int(y / 10) + border) * width + int(x / 10) + border] for x, y in sites):
        raise MapFormatError('A start/resource/tech site is isolated by terrain')
    for path in ai_paths:
        if any(math.hypot(x - a, y - b) < 125 for x, y in path['vertices'] for a, b, _ in supplies + tech):
            raise MapFormatError(f"AI route {path['label']} overlaps a supply/tech footprint")
    output = table + b''.join(OBJECT_HEADER.pack(i, v, len(d)) + d for i, v, d, _ in chunks)
    return output, {'title': 'Amber Canyon — 5 vs 5', 'style': style,
                    'visual_changes': ('layered sandstone wash, rocky foothill texture, extra cliff-top rock clusters'
                                       if detail_v5 else 'baseline v4'),
                    'teams': [1] * 5 + [2] * 5,
        'starts': starts, 'supplies': supplies, 'tech': tech, 'passes': PASSES,
        'roads': roads, 'ai_paths': ai_paths, 'waypoint_links': len(links),
        'ai_path_direction': 'inbound toward the base whose start number labels the path',
        'decorations': len(decorations), 'terrain_blends': len(blend_records),
        'reachable_sites': len(sites), 'reachable_grid_cells': sum(reached), 'base_height': BASE,
        'construction_pad_radius': 475, 'min_start_separation': 1150,
        'terrain_audit': 'all starts, supplies and tech sites connected with 20-world-unit cliff clearance'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--style', choices=('v4', 'v5'), default='v4',
                        help='v5 repaints audited terrain without changing cliff collision or roads')
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        parser.error('Refusing to overwrite a map')
    data, report = build(args.source.read_bytes(), args.style)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    report['format'] = inspect_map(args.output)
    args.output.with_suffix('.layout.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
