"""Synthetic correctness and regression tests; no licensed maps required."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from strategic_ai.telemetry import parse_log
from strategic_ai.analysis import analyze
from strategic_ai.routes import geometry_audit,propose_routes

def fixture(x1=0,x2=0,moveflag=1,free=10):
    rows=[]
    for frame,x in ((150,x1),(36000,x2)):
        rows += [
            f"LOCAL_SKIRMISH frame={frame} occupied=2 network=none",
            f"LOCAL_PATHFIND frame={frame} capacity=30000 free={free} failures=0",
            f"LOCAL_SKIRMISH slot=0 team=0 ai=0",
            f"LOCAL_SKIRMISH slot=1 team=1 ai=1 faction=7 builtUnits=65 "
            "combatUnits=20 earned=10000 supplyCenters=3 kills=0",
            f"LOCAL_GROUND frame={frame} slot=1 id=4 x={x} y=0 moving={moveflag} combat=1",
        ]
    return "\n".join(rows)

class TelemetryTests(unittest.TestCase):
    def test_moving_flag_does_not_count_as_displacement(self):
        result=analyze(parse_log(fixture(4500,4500)),[(0,0),(4500,0)],36000)
        self.assertEqual(result["slots"][1]["moved_20plus"],0)
        self.assertEqual(result["slots"][1]["flags"][0],"ground_vehicle_base_confined_proximity_proxy")

    def test_coordinate_displacement_is_observed(self):
        result=analyze(parse_log(fixture(4500,2000)),[(0,0),(4500,0)],36000)
        self.assertEqual(result["slots"][1]["moved_20plus"],1)
        self.assertEqual(result["slots"][1]["late_moved_20plus"],1)

    def test_no_pool_exhaustion_accepted(self):
        with self.assertRaises(ValueError):
            analyze(parse_log(fixture(free=0)),[(0,0),(4500,0)])

    def test_reject_short_log(self):
        with self.assertRaises(ValueError):
            analyze(parse_log(fixture()),[(0,0),(4500,0)],36001)

    def test_reject_duplicate_slot(self):
        log=fixture()+"\nLOCAL_SKIRMISH frame=36000\nLOCAL_SKIRMISH slot=1 ai=1\nLOCAL_SKIRMISH slot=1 ai=1"
        with self.assertRaises(ValueError):parse_log(log)

def layout_fixture():
    starts=[[0,i*300] for i in range(5)]+[[5000,i*300] for i in range(5)]
    paths=[]
    for i,start in enumerate(starts):
        for mode in ("Center","Flank","Backdoor"):
            far_x=5000 if i<5 else 0
            near_x=500 if i<5 else 4500
            paths.append(dict(label=f"{mode}{i+1}",
                              vertices=[[far_x,start[1]],[near_x,start[1]]],
                              ids=[i*100+len(paths)*2,i*100+len(paths)*2+1]))
    return dict(starts=starts,ai_paths=paths,supplies=[],tech=[])

class RouteTests(unittest.TestCase):
    def test_no_collision(self):
        self.assertEqual(geometry_audit(layout_fixture())["collision_count"],0)

    def test_segment_middle_catches_resource(self):
        layout=layout_fixture()
        layout["supplies"]=[[2500,0,"contested"]]
        audit=geometry_audit(layout)
        self.assertGreater(audit["collision_count"],0)
        self.assertIn("Center1",audit["collisions"])

    def test_missing_required_route_fails(self):
        layout=layout_fixture()
        layout["ai_paths"].pop()
        self.assertTrue(geometry_audit(layout)["issues"])

    def test_proposal_rejects_unknown_path_shape(self):
        with self.assertRaises(ValueError):
            propose_routes(layout_fixture())

if __name__=="__main__":unittest.main()

class SafetyGateTests(unittest.TestCase):
    def test_invalid_overlay_is_rejected_before_binary_edit(self):
        from strategic_ai.native_map import overlay_waypoints
        layout=layout_fixture()
        layout["supplies"]=[[2500,0,"contested"]]
        with self.assertRaisesRegex(ValueError,"Unsafe overlay"):
            overlay_waypoints(b"not a map",layout)

    def test_unreachable_resource_is_identified(self):
        from unittest.mock import patch
        from strategic_ai.site_reachability import audit_sites
        layout=dict(starts=[[100,100],[900,100]],supplies=[[900,900,"dock"]],
                    tech=[],ai_paths=[])
        checker=lambda x,y:x>400
        with patch("strategic_ai.site_reachability.mask_reader",
                   return_value=(checker,100,100,0)):
            result=audit_sites(b"fake",layout)
        self.assertEqual(result["reachable_sites"],1)
        self.assertEqual({r["kind"] for r in result["unreachable"]},{"start","supply"})
