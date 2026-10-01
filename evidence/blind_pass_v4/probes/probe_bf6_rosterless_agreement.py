"""B-F6: "ONE RULE about what a rosterless pick means, in both places (`#126`)" -- is it one rule?

`draft_room.team_slots_filled` skips `roster_id is None` and keys on `str(roster_id)`.
`league_config.team_count_with_basis` filters `is None` on the picks rule but does NOT coerce,
while its SEATS rule does (`{str(seat) ...}`). This walks the histories where the two readers can
still disagree, and checks the guard the repair must not disarm.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_bf6_rosterless_agreement.py
"""
import draft_room as dr
import league_config as lc

PLAYERS = {
    "1": {"first_name": "A", "last_name": "One", "position": "QB", "fantasy_positions": ["QB"]},
    "2": {"first_name": "B", "last_name": "Two", "position": "RB", "fantasy_positions": ["RB"]},
}
ROSTER = ["QB", "RB", "WR", "TE", "FLEX", "BN"]

CASES = {
    "the module's own fixture (a rosterless pick)":
        [{"player_id": "1", "roster_id": "1"}, {"player_id": "2", "roster_id": None}],
    "a roster whose only pick is a player the pool does not know":
        [{"player_id": "1", "roster_id": "1"}, {"player_id": "999", "roster_id": "2"}],
    "roster_id as an EMPTY STRING":
        [{"player_id": "1", "roster_id": "1"}, {"player_id": "2", "roster_id": ""}],
    "roster_id MISSING from the dict":
        [{"player_id": "1", "roster_id": "1"}, {"player_id": "2"}],
    "roster_id 0 (int) and '0' (str) -- Sleeper's own type is int":
        [{"player_id": "1", "roster_id": 0}, {"player_id": "2", "roster_id": "0"}],
}

for tag, picks in CASES.items():
    filled = dr.team_slots_filled(picks, PLAYERS, ROSTER)
    count = lc.team_count(picks=picks)
    verdict = "AGREE" if len(filled) == count else "DISAGREE"
    print(tag)
    print(f"   team_slots_filled keys = {sorted(filled)} (len {len(filled)})   "
          f"team_count = {count}   {verdict}")
    try:
        demand = dr.remaining_starter_demand(ROSTER, 1, picks, PLAYERS)
        print(f"   remaining_starter_demand(num_teams=1) -> ok, {len(demand)} entries")
    except Exception as exc:                            # noqa: BLE001
        print(f"   remaining_starter_demand(num_teams=1) -> {type(exc).__name__}: {str(exc)[:100]}")

print()
print("the guard the repair must not disarm -- two REAL rosters, one team:")
picks = [{"player_id": "1", "roster_id": "1"}, {"player_id": "2", "roster_id": "2"}]
try:
    dr.remaining_starter_demand(ROSTER, 1, picks, PLAYERS)
    print("   NOT REFUSED -- the foreign-history guard is disarmed")
except ValueError as exc:
    print(f"   still refused: ValueError: {str(exc)[:90]}")
