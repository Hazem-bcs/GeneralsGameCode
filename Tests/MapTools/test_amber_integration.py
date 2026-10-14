"""Contract-schema integration regression tests without licensed maps."""
import copy
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from strategic_ai.contract import normalize_contract
from strategic_ai.telemetry import parse_log
from strategic_ai.routes import propose_routes

def sample():
    source=json.loads((ROOT/"docs/research/amber-strategic-v6/map_contract.json").read_text())
    data=b"synthetic unlicensed ckmp fixture"
    source["map_sha256"]=hashlib.sha256(data).hexdigest()
    positions={}
    edges=set()
    for i,route in enumerate(source["vehicle_corridors"]):
        nodes=[]
        for n,position in enumerate(route["vertices"]):
            nodes.append((i*100+n,tuple(position)))
        positions[route["id"]]=nodes
        edges.update((nodes[j][0],nodes[j+1][0]) for j in range(len(nodes)-1))
    fake_chunks=(b"CkMp",[(1,4,struct.pack("<3i",740,740,70),"HeightMapData")])
    return source,data,positions,edges,fake_chunks

class ContractIntegrationTests(unittest.TestCase):
    def convert(self,contract, data, positions, edges, chunks):
        with patch("strategic_ai.contract.native_routes",return_value=(positions,edges)), \
             patch("strategic_ai.contract.parse_chunks",return_value=chunks), \
             patch("strategic_ai.native_map.native_audit",return_value={}):
            return normalize_contract(contract,data)

    def test_matching_v6_contract_matches_all_route_ids(self):
        c,data,positions,links,chunks=sample()
        layout=self.convert(c,data,positions,links,chunks)
        self.assertEqual(len(layout["ai_paths"]),30)
        self.assertEqual(sum(len(p["ids"])-1 for p in layout["ai_paths"]),210)
        self.assertEqual(layout["style"],"v6")
        self.assertNotIn("ai_route_policy",layout)

    def test_reject_stale_map_hash(self):
        c,data,pos,edges,chunks=sample()
        with self.assertRaisesRegex(ValueError,"SHA256"):
            self.convert(c,data+b"changed",pos,edges,chunks)

    def test_reject_wrong_team_assignments(self):
        c,data,pos,edges,chunks=sample()
        c["bases"][0]["team"]=2
        with self.assertRaisesRegex(ValueError,"team"):
            self.convert(c,data,pos,edges,chunks)

    def test_reject_reversed_native_link(self):
        c,data,pos,edges,chunks=sample()
        target=next(iter(edges))
        edges.remove(target)
        edges.add(tuple(reversed(target)))
        with self.assertRaisesRegex(ValueError,"missing or reversed"):
            self.convert(c,data,pos,edges,chunks)

    def test_reject_waypoint_contract_mismatch(self):
        c,data,pos,edges,chunks=sample()
        c["vehicle_corridors"][0]["vertices"][1][0]+=30
        with self.assertRaisesRegex(ValueError,"native waypoint"):
            self.convert(c,data,pos,edges,chunks)

    def test_no_v6_geometry_transform_without_policy(self):
        c,data,pos,edges,chunks=sample()
        layout=self.convert(c,data,pos,edges,chunks)
        with self.assertRaisesRegex(ValueError,"ai_route_policy"):
            propose_routes(layout)

    def test_long_wine_map_path_is_preserved(self):
        name="c:\\users\\wine\\documents\\command and conquer generals zero hour data\\maps\\ambercanyon_strategic_v6\\ambercanyon_strategic_v6.map"
        parsed=parse_log("LOCAL_SKIRMISH frame=150 occupied=10 network=none map="+name)
        self.assertEqual(parsed.headers[0]["map"],name)

    def test_unsupported_schema_rejected(self):
        c,data,pos,edges,chunks=sample()
        c["schema_version"]=99
        with self.assertRaisesRegex(ValueError,"schema"):
            self.convert(c,data,pos,edges,chunks)

if __name__=="__main__":
    unittest.main()
