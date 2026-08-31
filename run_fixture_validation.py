"""Validate a real Sleeper capture against the research-fixture contract.

WHY THIS EXISTS. Four separate investigations in this audit terminated on the same wall --
magnitude measured, reach unmeasurable -- because every fixture available here is synthetic:

    #85 future-pick valuation   needed traded_picks
    D   injury-status reach     needed real players_nfl injury_status
    E   eligibility_bonus reach needed real fantasy_positions multiplicity
    #87 peer-relative depth     needed real rosters and the engine's own slot semantics

Synthetic fixtures cannot answer a reach question, and this audit has caught itself four
times reporting a fixture's property as an engine property (a 0/237 injury rate, a 0/12
eligibility ablation, a voided depth measurement). So the rule this file enforces is: a
fixture is only admissible for a reach question if it can actually EXERCISE the dimension
that question asks about. A capture that is merely well-formed is not enough.

This validates; it never generates. There is deliberately no synthetic-fixture mode.

HOW TO PRODUCE THE CAPTURE (must be run where api.sleeper.app is reachable -- it is blocked
by egress policy inside the audit session):

    from sleeper_client import SleeperClient
    c = SleeperClient()
    c.sync_league("<your league id>", c.get_players())
    # writes data/sleeper_snapshots/<league_id>_latest.json
    # and  data/sleeper_snapshots/players_nfl.json

Then:  python run_fixture_validation.py data/sleeper_snapshots/<league_id>_latest.json

REDACTION. Safe to strip or replace: display_name, avatar, user_id, league name, any
metadata.* free text. MUST NOT be normalized, defaulted, or dropped -- these ARE the
measurement: rosters[].players, rosters[].starters, rosters[].settings.wins/losses/ties,
traded_picks[].{season,round,roster_id,owner_id}, league.roster_positions,
players_nfl[].{position,fantasy_positions,injury_status}.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path


def _players_path(snapshot_path: Path) -> Path:
    return snapshot_path.parent / "players_nfl.json"


def _load(path: Path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def audit(snapshot: dict, players: dict) -> list[dict]:
    """One row per dimension: what it unblocks, whether the fixture can exercise it, and the
    denominator the reach question will actually be computed over."""
    rosters = snapshot.get("rosters") or []
    league = snapshot.get("league") or {}
    traded = snapshot.get("traded_picks") or []

    rostered_ids = {str(p) for r in rosters for p in (r.get("players") or [])}
    rostered = [players[p] for p in rostered_ids if p in players]

    multi = [p for p in rostered if len(p.get("fantasy_positions") or []) > 1]
    injured = [p for p in rostered if p.get("injury_status")]
    with_record = [r for r in rosters
                   if (r.get("settings") or {}).get("wins") is not None]
    games = [((r.get("settings") or {}).get("wins", 0) or 0)
             + ((r.get("settings") or {}).get("losses", 0) or 0)
             + ((r.get("settings") or {}).get("ties", 0) or 0) for r in with_record]

    return [
        {"dimension": "rosters + slot eligibility", "unblocks": "#87 peer-relative depth",
         "present": bool(rosters) and bool(league.get("roster_positions")),
         "exercises": len(rosters) >= 2 and bool(rostered_ids),
         "detail": f"{len(rosters)} rosters, {len(rostered_ids)} rostered players, "
                   f"{len(league.get('roster_positions') or [])} roster_positions"},
        {"dimension": "settings.wins/losses", "unblocks": "#85 future-pick valuation",
         "present": bool(with_record),
         "exercises": bool(games) and max(games) > 0 and len(set(games)) >= 1
                      and len({(r.get('settings') or {}).get('wins') for r in with_record}) > 1,
         "detail": f"{len(with_record)}/{len(rosters)} rosters carry a record; "
                   f"games played {min(games) if games else 0}-{max(games) if games else 0}; "
                   f"{len({(r.get('settings') or {}).get('wins') for r in with_record})} distinct win totals"},
        {"dimension": "traded_picks", "unblocks": "#85 future-pick valuation (reach)",
         "present": "traded_picks" in snapshot,
         "exercises": len(traded) > 0,
         "detail": f"{len(traded)} traded picks; "
                   f"seasons {sorted({str(t.get('season')) for t in traded}) if traded else '[]'}"},
        {"dimension": "injury_status", "unblocks": "D injury-status reach",
         "present": any("injury_status" in p for p in rostered),
         "exercises": len(injured) > 0,
         "detail": f"{len(injured)}/{len(rostered)} rostered players carry a status; "
                   f"{dict(collections.Counter(p['injury_status'] for p in injured))}"},
        {"dimension": "fantasy_positions multiplicity", "unblocks": "E eligibility_bonus reach",
         "present": any(p.get("fantasy_positions") for p in rostered),
         "exercises": len(multi) > 0,
         "detail": f"{len(multi)}/{len(rostered)} rostered players are multi-eligible; "
                   f"{sorted({'/'.join(sorted(p['fantasy_positions'])) for p in multi})[:6]}"},
    ]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        print("usage: python run_fixture_validation.py <snapshot_latest.json>")
        return 2
    snapshot_path = Path(argv[1])
    players_path = _players_path(snapshot_path)
    for path in (snapshot_path, players_path):
        if not path.exists():
            print(f"MISSING: {path}")
            print("both the league snapshot and players_nfl.json are required -- the players "
                  "payload is where injury_status and fantasy_positions live.")
            return 1

    rows = audit(_load(snapshot_path), _load(players_path))
    print(f"{'dimension':<34}{'present':>9}{'exercises':>11}   unblocks")
    for row in rows:
        print(f"{row['dimension']:<34}{('yes' if row['present'] else 'NO'):>9}"
              f"{('yes' if row['exercises'] else 'NO'):>11}   {row['unblocks']}")
        print(f"    {row['detail']}")

    blocked = [r for r in rows if not r["exercises"]]
    print()
    if blocked:
        print("FIXTURE INCOMPLETE for reach measurement. These dimensions are present in shape "
              "but cannot exercise their question:")
        for row in blocked:
            print(f"  - {row['dimension']}  ({row['unblocks']})")
        print("\nA dimension that cannot be exercised yields a fixture property, not an engine "
              "property. Do NOT report a reach number for it.")
        return 1
    print("FIXTURE ADMISSIBLE: every dimension is both present and exercisable.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
