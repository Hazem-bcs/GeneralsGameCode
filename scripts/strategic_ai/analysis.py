"""Read-only statistical analysis of skirmish log samples."""
from collections import defaultdict
from math import hypot

def distance(a,b):
    return hypot(a[0]-b[0], a[1]-b[1])

def analyze(run, starts, minimum_frame=36000):
    frames=sorted(run.snapshots)
    slots=set(range(len(starts)))
    if not frames or frames[-1]<minimum_frame:
        raise ValueError("Insufficient frames")
    if any(set(run.snapshots[f])!=slots for f in frames):
        raise ValueError("Missing player observations")
    if not run.pathfind or max(x["frame"] for x in run.pathfind)<minimum_frame:
        raise ValueError("Missing pathfinding telemetry")
    if any(x["free"]<=0 or x["failures"]!=0 for x in run.pathfind):
        raise ValueError("Path pool failed")
    teams={s:run.snapshots[frames[-1]][s]["team"] for s in slots}
    tracks=defaultdict(list)
    for f in sorted(run.ground):
        for row in run.ground[f]:
            if row["combat"]:
                tracks[int(row["slot"]),int(row["id"])].append(row)
    armies={}
    for slot in sorted(slots-{0}):
        samples=[(f,run.snapshots[f][slot]) for f in frames]
        last=samples[-1][1]
        enemies=[starts[s] for s in slots if teams[s]!=teams[slot]]
        if not enemies: raise ValueError("No enemies")
        vehicles=[rows for (s,_),rows in tracks.items() if s==slot]
        records=[row for rows in vehicles for row in rows]
        near=min((distance((r["x"],r["y"]),e) for r in records for e in enemies),default=None)
        far=max((distance((r["x"],r["y"]),starts[slot]) for r in records),default=None)
        movements=late=recent=0
        first_move=first_near=None
        for rows in vehicles:
            for old,new in zip(rows,rows[1:]):
                frame=int(new["frame"])
                if distance((old["x"],old["y"]),(new["x"],new["y"]))>=20:
                    movements+=1
                    late+=frame>=12600
                    recent+=frame>=minimum_frame-1800
                    first_move=frame if first_move is None else min(frame,first_move)
                if any(distance((new["x"],new["y"]),e)<=1200 for e in enemies):
                    first_near=frame if first_near is None else min(frame,first_near)
        def first(key):
            return next((f for f,r in samples if r.get(key,0)>0),None)
        peak=max(r.get("combatUnits",0) for _,r in samples)
        drops=sum(max(0,a.get("combatUnits",0)-b.get("combatUnits",0))
                  for (_,a),(_,b) in zip(samples,samples[1:]))
        state=[]
        if peak==0: state.append("no_combat_units_observed")
        elif not records: state.append("no_ground_combat_vehicles_observed")
        elif far<=0.8*min([distance(starts[slot],starts[a]) for a in slots if a!=slot and teams[a]==teams[slot]] or [1000]):
            state.append("ground_vehicle_base_confined_proximity_proxy")
        elif near>1200: state.append("ground_vehicles_not_near_enemy_base")
        if last.get("earned",0)>0 and last.get("kills",0)==0:
            state.append("economy_without_kill_evidence")
        armies[slot]=dict(
            team=teams[slot],faction=last.get("faction"),
            built_units_counter=last.get("builtUnits"),combat_units=last.get("combatUnits"),
            peak_combat_units=peak,net_combat_count_drops=drops,
            kills=last.get("kills"),earned=last.get("earned"),cash=last.get("cash"),
            supply_centers=last.get("supplyCenters"),tech_buildings=last.get("techBuildings"),
            first_kill_frame=first("kills"),first_frontline_frame=first("frontlineUnits"),
            first_approach_frame=first("approachUnits"),
            max_frontline=max(r.get("frontlineUnits",0) for _,r in samples),
            max_approach=max(r.get("approachUnits",0) for _,r in samples),
            ground_vehicle_ids=len(vehicles),ground_vehicle_samples=len(records),
            moved_20plus=movements,late_moved_20plus=late,
            final_minute_moved_20plus=recent,
            first_ground_move_frame=first_move,first_ground_near_enemy_frame=first_near,
            closest_ground_to_enemy=round(near,1) if near is not None else None,
            furthest_ground_from_home=round(far,1) if far is not None else None,
            flags=state)
    return dict(final_frame=frames[-1],minutes=frames[-1]/1800,
        minimum_free=min(int(x["free"]) for x in run.pathfind),
        allocation_failures=max(int(x["failures"]) for x in run.pathfind),
        limitations=[
            "Ground positions omit infantry and aircraft",
            "No attack/damage/target/death telemetry: first engagement and losses unmeasured",
            "Kill counters could reflect defense, not an advance",
            "builtUnits includes noncombat units; combat count drops are not casualties",
            "Approach/frontline counters do not show the selected waypoint path"],
        slots=armies)
