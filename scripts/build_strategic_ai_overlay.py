#!/usr/bin/env python3
"""Safely patch only waypoint locations in a PRIVATE validated native map."""
import argparse
import json
from pathlib import Path
from strategic_ai.routes import geometry_audit
from strategic_ai.terrain_clearance import audit_cliffs
from strategic_ai.native_map import native_audit,overlay_waypoints
from strategic_ai.site_reachability import audit_sites

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source-map",type=Path,required=True)
    cli.add_argument("--proposal-contract",type=Path,required=True)
    cli.add_argument("--output-map",type=Path,required=True)
    args=cli.parse_args()
    if args.output_map.exists() or args.output_map.resolve()==args.source_map.resolve():
        cli.error("Existing/private source map cannot be overwritten")
    layout=json.loads(args.proposal_contract.read_text())
    source=args.source_map.read_bytes()
    checks=geometry_audit(layout)
    if checks["issues"] or checks["collision_count"]:
        cli.error("Proposal has unresolved route geometry intersections")
    if audit_cliffs(source,layout)["failed_segments"]:
        cli.error("Proposal crosses cliff mask")
    if audit_sites(source,layout)["unreachable"]:
        cli.error("Some map sites are isolated from the starting bases")
    output=overlay_waypoints(source,layout)
    native_audit(output,layout)
    args.output_map.parent.mkdir(parents=True,exist_ok=True)
    args.output_map.write_bytes(output)
    print("Created private waypoint-only trial:",args.output_map)

if __name__=="__main__":
    main()
