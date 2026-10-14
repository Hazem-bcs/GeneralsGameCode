# Skirmish AI features requiring a separate engine change

**Do not implement here.** This branch changes no C++ and no
network format; the following are proposed diagnostic interfaces.

1. **Attack command and engagement evidence:** LOCAL_GROUND only
   logs sampled ground positions and flags. Accurate first
   engagement, offensive target, damage dealt and unit loss counts
   require event telemetry at targeting/weapon damage/death handlers
   in game logic, with attacker owner slot, target owner slot,
   coordinates and frame. Log only in explicit private diagnostic
   mode. Existing kills counters cannot provide these distinctions.
2. **Which native path was selected:** in `ScriptActions.cpp`,
   `doTeamFollowSkirmishApproachPath` selects the enemy's indexed
   path and the nearest waypoint to the team centroid. Instrument
   selected enemy slot, path label, entry waypoint ID and order
   outcome for diagnostics; current logs cannot prove a team
   actually used Center, Flank or Backdoor.
3. **Attack-team creation and tasking:** AI army production, rally
   thresholds, team selection and abort/retry conditions reside
   outside map geometry (AIPlayer / native scripts). A stationary
   faction-7 combat group may have no attack order or may be
   waiting for an unsuitable composition, not be blocked by terrain.
   First capture selected team plan, available troop types, funds,
   active tasks and failures; then propose a scoped engine patch
   **on another branch** if the evidence supports it.
4. **Actual reachability:** the map's cliff mask and circular
   resource-clearance heuristic are not the engine's true
   collision/footprint/locomotor model. Need runtime path request
   result, failure reason, current position and target, retries,
   and whether bridge/water rules are respected.
5. **Defensive versus offensive kills:** ground proximity to an
   enemy base does not prove engagement. Opponent units may fight
   elsewhere; aircraft can cross and attack while ground units
   stay near base. Include class/locomotor/aircraft identity in
   the opt-in diagnostic event stream if separately authorized.

**No engine edits are authorized as part of this AI-route branch.**
Do not add free troops, teleportation, unlimited funds or
slot-specific forced attack logic. Never increase the eight-slot
network protocol for local-only skirmish fixes.
