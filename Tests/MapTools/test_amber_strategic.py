"""Regression tests for strategic terrain and immutable v5 route/object payloads."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from amber_strategic.config import TerrainConfig
from amber_strategic.terrain import TerrainField,segment_distance
from amber_strategic.ckmp import inspect_source,nonterrain_sha
from amber_strategic.audit import audit

PRIVATE=Path('/home/hazem/projects/generals-extended-tests/maps')
V5=PRIVATE/'AmberCanyon_5v5_v5'/'AmberCanyon_5v5_v5.map'
V6=PRIVATE/'AmberCanyon_Strategic_v6'/'AmberCanyon_Strategic_v6.map'

@unittest.skipUnless(V5.exists(),'Private owner map not present')
class TerrainUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout=json.loads(V5.with_suffix('.layout.json').read_text())
        cls.field=TerrainField(cls.layout)

    def test_deterministic_seed(self):
        x,y=2370,1820
        self.assertEqual(self.field.sample(x,y),TerrainField(self.layout).sample(x,y))
        altered=TerrainField(self.layout,TerrainConfig(seed=1010))
        self.assertNotEqual(self.field.raw_elevation(x,y),altered.raw_elevation(x,y))

    def test_east_west_mirrored_elevations(self):
        for x in range(140,2990,130):
            for y in range(190,5820,240):
                self.assertEqual(self.field.sample(x,y)[0],self.field.sample(6000-x,y)[0])

    def test_build_pads_and_resource_docks_are_flat(self):
        for x,y in self.layout['starts']:
            self.assertEqual(self.field.sample(x,y)[0],72)
        for x,y,_ in self.layout['supplies']+self.layout['tech']:
            self.assertEqual(self.field.sample(x,y)[0],72)

    def test_mountain_has_functional_height(self):
        summit=self.field.sample(3000,1900)[0]
        self.assertGreater(summit,130)
        self.assertLess(self.field.sample(3000,3000)[0],80)

    def test_segment_distance_geometry(self):
        self.assertAlmostEqual(segment_distance(5,5,(0,0,10,0,100)),5)
        self.assertAlmostEqual(segment_distance(20,0,(0,0,10,0,100)),10)

@unittest.skipUnless(V5.exists() and V6.exists(),'Generated private map absent')
class MapIntegrityTests(unittest.TestCase):
    def test_object_network_byte_for_byte_preserved(self):
        self.assertEqual(nonterrain_sha(V5.read_bytes()),nonterrain_sha(V6.read_bytes()))

    def test_explicit_exits_and_center_detour(self):
        from verify_amber_contract import verify
        report=verify(V6,V6.parent/'map_contract.json')
        self.assertTrue(report['passed'],report['errors'])
        self.assertEqual(len(report['exit_reachable']),10)
        self.assertTrue(report['central_crossing_blocked_detour'])

    def test_map_grid_consistent(self):
        _,_,_,w,h,b=inspect_source(V6.read_bytes())
        self.assertEqual((w,h,b),(740,740,70))

    def test_audit_connectivity_and_build_pads(self):
        from scripts.map_resize_lab import parse_chunks
        from amber_strategic.config import TerrainConfig
        data=V6.read_bytes()
        _,chunks=parse_chunks(data)
        fields={name:payload for _,_,payload,name in chunks}
        heights=fields['HeightMapData'][28:]
        flags=fields['BlendTileData']
        w,h,b=740,740,70
        pos=4+w*h*8
        packed=flags[pos:pos+((w+7)//8)*h]
        cliffs=bytearray(w*h)
        for row in range(h):
            for col in range(w):
                cliffs[row*w+col]=bool(packed[row*((w+7)//8)+col//8]&(1<<(col%8)))
        layout=json.loads(V5.with_suffix('.layout.json').read_text())
        report,_=audit(heights,cliffs,layout,w,h,b,TerrainConfig())
        self.assertTrue(report['passed'],report['errors'])
        self.assertEqual(report['checked_sites'],294)
        self.assertEqual(report['isolated_sites'],[])

if __name__=='__main__':
    unittest.main()
