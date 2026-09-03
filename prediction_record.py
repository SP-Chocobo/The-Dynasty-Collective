"""A committed, timestamped record of what this engine predicted, before the outcomes exist.

WHY THIS EXISTS. Everything validating this engine so far asks whether it behaves consistently
with its own definitions -- absence contracts, provenance, independence, ablation, unit
discipline. None of it asks whether those definitions predict anything. An engine can be
immaculately self-consistent and wrong, and every guard in this repo would stay green.

The obvious answer is a backtest, and this repo cannot run one. Checked, September 2026:
data/sleeper_snapshots/ is empty, and every ranking source_date is inside a two-week August
2026 window. There is no completed season to score against and no historical ranking to score
with. That is an acquisition problem, not a code problem (see #49, #88).

But the same fact opens a better door. Those August rankings are point-in-time for a season
that has not been played. So instead of looking backward through data that already knows how
things turned out, this writes down what the engine believes NOW, before Week 1, and lets
reality arrive on its own schedule.

WHY FORWARD BEATS BACKWARD HERE. A backtest built from current dynasty rankings scored against
last season would produce a spectacular and meaningless result: those rankings already
incorporate knowledge of what happened. Hindsight contamination is not a bias you can correct
for after the fact -- it is baked into the inputs. A forward record cannot have it, because the
outcomes do not exist yet when the prediction is written. This is the weaker-looking method
that is actually the stronger one.

THE RECORD IS WRITE-ONCE, AND THAT IS THE WHOLE POINT. `capture` refuses to overwrite an
existing record for a date. A prediction you can quietly revise after seeing the result is not
a prediction; it is a description. The refusal is the mechanism, not a convenience -- every
other integrity artifact here can be regenerated on purpose (`--write` repairs a damaged
manifest), and this one deliberately cannot.

WHAT IT DOES NOT DO. It scores nothing. Scoring needs realized outcomes this repo does not yet
have, and writing the scorer now would mean writing it against imagined data -- the exact trap
that voided four measurement instruments earlier in this project. The record is the half that
is possible today and perishable; the scorer is the half that is neither.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Optional

import store_io

RECORD_DIR = Path("data/predictions")

#: Fields captured per player. Deliberately the engine's OWN outputs plus the raw anchor it
#: builds them from -- not a derived summary. A summary is a claim about the prediction; these
#: are the prediction. Anything reconstructible from these is left out.
FIELDS = ("player_id", "name", "position", "team", "universal_value", "projected_points",
          "bpa", "bpa_source", "confidence", "time_horizon_adj", "risk_adj")


def _fingerprint(rows: list[dict]) -> str:
    """Content hash of the predictions themselves, so a record can prove it was not edited.

    Over the rows only, never the metadata: a record re-serialized with a different comment or
    tool version is the same prediction, and a hash that moved for that reason would cry wolf
    the first time anything cosmetic changed.
    """
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def record_path(as_of: str, root: Path = RECORD_DIR) -> Path:
    return root / f"predictions_{as_of}.json"


def build(merger, players_db: dict[str, dict], league: dict) -> list[dict]:
    """The engine's current opinion of every player, at an empty board.

    Empty picks on purpose: a prediction conditioned on a particular draft's state would only
    be testable against that draft. This is the league-shaped but roster-independent view --
    universal_value's own altitude, which is the layer whose contact with reality is in
    question.
    """
    import draft_room as dr

    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id=None, league=league, mode="balanced",
    )
    return [{field: row.get(field) for field in FIELDS} for row in board]


def capture(rows: list[dict], *, as_of: Optional[str] = None, source_dates: Optional[list] = None,
            league_shape: Optional[str] = None, pool_size: Optional[int] = None,
            root: Path = RECORD_DIR) -> dict:
    """Write the record. Refuses to overwrite an existing one for the same date.

    Returns the record written. Raises FileExistsError if one already exists -- see the module
    docstring for why that refusal is the feature.
    """
    as_of = as_of or date.today().isoformat()
    path = record_path(as_of, root)
    if path.exists():
        raise FileExistsError(
            f"{path} already exists. A prediction record is written once and never revised -- "
            f"a prediction you can edit after seeing the outcome is not a prediction. Delete it "
            f"deliberately if it was written in error."
        )
    record = {
        "_comment": (
            "What this engine predicted, written before the outcomes existed. See "
            "prediction_record.py. NOT to be regenerated: the value of this file is entirely "
            "that it predates what it will be scored against."
        ),
        "as_of": as_of,
        "n_players": len(rows),
        # What this record does NOT cover, stated in the record rather than inferable from it.
        # A prediction file that reports its own count without its own scope overstates itself
        # by omission -- and the reader who most needs the scope is the one scoring it months
        # from now, who cannot ask.
        "coverage": {
            "positions": sorted({r.get("position") for r in rows if r.get("position")}),
            "by_position": {
                position: sum(1 for r in rows if r.get("position") == position)
                for position in sorted({r.get("position") for r in rows if r.get("position")})
            },
            "source_pool_size": pool_size,
            "excluded": (
                "K, DEF and all IDP positions carry no slot in this league shape and so never "
                "reach the board. They are absent from this record, NOT predicted-and-wrong. "
                "Any scorer must exclude them rather than count them as misses."
            ),
        },
        "input_source_dates": sorted({str(d) for d in (source_dates or []) if d}),
        "league_shape": league_shape,
        "fingerprint": _fingerprint(rows),
        "predictions": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    store_io.write(path, record)
    return record


def load(as_of: str, root: Path = RECORD_DIR) -> Optional[dict]:
    path = record_path(as_of, root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def records(root: Path = RECORD_DIR) -> list[str]:
    """Every as-of date on disk, oldest first."""
    if not root.exists():
        return []
    return sorted(p.stem.replace("predictions_", "") for p in root.glob("predictions_*.json"))


def verify(as_of: str, root: Path = RECORD_DIR) -> dict:
    """Does this record still hash to what it claimed when written?

    A record's whole worth is that it predates its own scoring, and a file on disk cannot
    prove that by existing. The fingerprint is what makes tampering visible rather than
    merely improbable.
    """
    record = load(as_of, root)
    if record is None:
        return {"as_of": as_of, "state": "missing"}
    actual = _fingerprint(record.get("predictions", []))
    claimed = record.get("fingerprint")
    return {
        "as_of": as_of,
        "state": "intact" if actual == claimed else "ALTERED",
        "claimed": claimed,
        "actual": actual,
        "n_players": record.get("n_players"),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--capture", action="store_true", help="write today's record")
    parser.add_argument("--verify", action="store_true", help="check every record's fingerprint")
    parser.add_argument("--list", action="store_true", help="list recorded dates")
    args = parser.parse_args(argv)

    if args.list or (not args.capture and not args.verify):
        existing = records()
        print(f"{len(existing)} prediction record(s): {', '.join(existing) or '(none)'}")
        return 0

    if args.verify:
        bad = 0
        for as_of in records():
            result = verify(as_of)
            print(f"  {result['as_of']}  {result['state']:8} n={result.get('n_players')}")
            bad += result["state"] != "intact"
        return 1 if bad else 0

    import data_merger as dm
    from player_universe import FANTASY_POSITIONS

    merger = dm.DataMerger()
    proj = merger.projections
    players_db, pid = {}, 0
    for _, row in proj.iterrows():
        pid += 1
        parts = str(row["norm_name"]).split()
        players_db[str(pid)] = {
            "first_name": (parts[0] if parts else "").upper(),
            "last_name": " ".join(parts[1:]).title(),
            "position": row["position"], "fantasy_positions": [row["position"]],
            "team": row.get("team"),
        }
    league = {
        "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX",
                             "BN", "BN", "BN", "BN", "BN"],
        "total_rosters": 12, "settings": {"type": 2},
    }
    rows = build(merger, players_db, league)
    record = capture(
        rows,
        source_dates=proj["source_date"].dropna().unique().tolist(),
        league_shape="12-team dynasty, 1QB, 2RB/2WR/1TE/2FLEX, 5 bench",
        pool_size=len(proj),
    )
    print(f"recorded {record['n_players']} predictions as of {record['as_of']} "
          f"(of {record['coverage']['source_pool_size']} in the pool)")
    print(f"  covers            : {record['coverage']['by_position']}")
    print(f"  fingerprint       : {record['fingerprint']}")
    print(f"  input source dates: {', '.join(record['input_source_dates'])}")
    print(f"  -> {record_path(record['as_of'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
