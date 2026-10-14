#!/usr/bin/env python3
"""Audit skirmish telemetry against v5 layout or the v6 authoritative contract."""
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
from strategic_ai.contract import normalize_contract

def summary(audit):
    return {key:value for key,value in audit.items() if key!="collisions"}

def inspect(log,layout,map_bytes=None,minimum_frame=36000):
    run=parse_log(log)
    name=layout.get("contract_name")
    if name and any(name.lower() not in str(h.get("map","")).lower()
                    for h in run.headers):
        raise ValueError(f"Runtime map does not match {name}")
    baseline=geometry_audit(layout)
    candidate=None
    if layout.get("style") in ("v4","v5") or "ai_route_policy" in layout:
        candidate=propose_routes(layout)
    proposed=geometry_audit(candidate) if candidate else None
    report={
        "runtime":analyze(run,layout["starts"],minimum_frame),
        "map_before":summary(baseline),
        "proposal_status":("STATIC_CANDIDATE_ONLY_NOT_GAMEPLAY_VALIDATED"
                           if candidate else "V6_ROUTE_POLICY_NOT_PROVIDED"),
        "runtime_sha256":hashlib.sha256(log.encode()).hexdigest(),
    }
    if candidate:
        report["map_proposal"]=summary(proposed)
        report["unresolved_proposal_intersections"]=proposed["collisions"]
        report["waypoint_changes"]=diff_paths(layout,candidate)
    if map_bytes is not None:
        report["native_graph"]=native_audit(map_bytes,layout)
        report["cliff_before"]=audit_cliffs(map_bytes,layout)
        report["sites_before"]=audit_sites(map_bytes,layout)
        if candidate:
            report["cliff_proposal"]=audit_cliffs(map_bytes,candidate)
            report["sites_proposal"]=audit_sites(map_bytes,candidate)
        report["map_sha256"]=hashlib.sha256(map_bytes).hexdigest()
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",required=True,type=Path)
    sources=p.add_mutually_exclusive_group(required=True)
    sources.add_argument("--layout",type=Path,help="Original v4/v5 layout JSON")
    sources.add_argument("--map-contract",type=Path,
                         help="Terrain-agent v6 schema version 1; --map required")
    p.add_argument("--map",type=Path,help="Owner-private native CkMp map")
    p.add_argument("--minimum-frame",type=int,default=36000)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--proposal-contract",type=Path,help="Private route overlay candidate")
    args=p.parse_args()
    if args.output.exists():
        p.error("Refusing to overwrite report")
    if args.proposal_contract and args.proposal_contract.exists():
        p.error("Refusing to overwrite route proposal")
    if args.map_contract and not args.map:
        p.error("--map-contract requires the matching native --map")
    map_bytes=args.map.read_bytes() if args.map else None
    layout=(normalize_contract(json.loads(args.map_contract.read_text()),map_bytes)
            if args.map_contract else json.loads(args.layout.read_text()))
    if args.proposal_contract and not (layout.get("style") in ("v4","v5")
                                       or "ai_route_policy" in layout):
        p.error("Map contract lacks AI route policy; cannot generate a v6 overlay")
    report=inspect(args.log.read_text(errors="replace"),
                   layout,map_bytes,args.minimum_frame)
    if args.proposal_contract:
        proposal=propose_routes(layout)
        args.proposal_contract.parent.mkdir(parents=True,exist_ok=True)
        args.proposal_contract.write_text(json.dumps(proposal,indent=2)+"\n")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("Saved",args.output)
    print("Frame",report["runtime"]["final_frame"],
          "geometry before",report["map_before"]["collision_count"],
          "proposal",report.get("map_proposal",{}).get("collision_count","not authorized"))

if __name__=="__main__":
    main()
