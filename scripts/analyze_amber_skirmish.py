#!/usr/bin/env python3
"""Generate portable movement/route diagnostics from private read-only sources."""
import argparse
import hashlib
import json
from pathlib import Path
from strategic_ai.telemetry import parse_log
from strategic_ai.analysis import analyze
from strategic_ai.routes import geometry_audit, propose_routes, diff_paths
from strategic_ai.native_map import native_audit
from strategic_ai.terrain_clearance import audit_cliffs
from strategic_ai.site_reachability import audit_sites

def summary(audit):
    return {key:value for key,value in audit.items() if key!="collisions"}

def inspect(log,layout,map_bytes=None,minimum_frame=36000):
    baseline=geometry_audit(layout)
    candidate=propose_routes(layout)
    proposed=geometry_audit(candidate)
    response={
        "runtime":analyze(parse_log(log),layout["starts"],minimum_frame),
        "map_before":summary(baseline),
        "map_proposal":summary(proposed),
        "proposal_status":"STATIC_CANDIDATE_ONLY_NOT_GAMEPLAY_VALIDATED",
        "unresolved_proposal_intersections":proposed["collisions"],
        "waypoint_changes":diff_paths(layout,candidate),
        "runtime_sha256":hashlib.sha256(log.encode()).hexdigest(),
    }
    if map_bytes is not None:
        response["native_graph"]=native_audit(map_bytes,layout)
        response["cliff_before"]=audit_cliffs(map_bytes,layout)
        response["sites_before"]=audit_sites(map_bytes,layout)
        response["cliff_proposal"]=audit_cliffs(map_bytes,candidate)
        response["sites_proposal"]=audit_sites(map_bytes,candidate)
        response["map_sha256"]=hashlib.sha256(map_bytes).hexdigest()
    return response

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",required=True,type=Path)
    p.add_argument("--layout",required=True,type=Path,
                   help="v5 layout, or terrain-agent v6 contract with matching schema")
    p.add_argument("--map",type=Path,help="private CkMp for native link audit")
    p.add_argument("--minimum-frame",type=int,default=36000)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--proposal-contract",type=Path,help="private data-only route proposal")
    args=p.parse_args()
    if args.output.exists():p.error("Refusing to overwrite report")
    report=inspect(args.log.read_text(errors="replace"),
                   json.loads(args.layout.read_text()),
                   args.map.read_bytes() if args.map else None,args.minimum_frame)
    if args.proposal_contract:
        if args.proposal_contract.exists():p.error("Refusing to overwrite route contract")
        contract=propose_routes(json.loads(args.layout.read_text()))
        args.proposal_contract.parent.mkdir(parents=True,exist_ok=True)
        args.proposal_contract.write_text(json.dumps(contract,indent=2)+"\n")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("Saved",args.output)
    print("Frame",report["runtime"]["final_frame"],
          "geometric intersections",report["map_before"]["collision_count"],
          "->",report["map_proposal"]["collision_count"])
if __name__=="__main__":
    main()
