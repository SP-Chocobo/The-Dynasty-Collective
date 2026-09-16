"""#112: does `absence_kind` land on rows that ARE priced? Cross-tab, not inference.

The field's own contract says a priced row carries None -- there is no absence to classify.
`_derive_points_and_source` assigns ABSENCE_BELOW_SOURCE_CUTOFF on `no_points & trade_value
.notna()`, and that is EXACTLY the branch whose bpa_source is `position_relative_trade_value_vor`
-- the trade-value fallback, which prices the row. If that reading is right the field breaks its
own contract on every such row, and the "all 643 are one kind" result was measuring a pool in
which the second kind is unreachable-by-construction rather than merely unpopulated.

Measured against bpa, which is what "priced" MEANS here -- not against my reading of the code.

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/absence_kind/kind_vs_priced.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb

OUT = Path("evidence/absence_kind/kind_vs_priced.json")


def main() -> int:
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                  te_premium=False, dynasty=True, base_scoring=base)
    merger.set_league_format(db.league_format_hint(league))            # NEVER SKIP
    board = dr.compute_draft_board(merger, players_db, [], my_roster_id="1", league=league,
                                   mode="balanced", sleeper_projections=season,
                                   sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    print(f"universe {prov['players_in_pool']}   board rows {len(board)}", flush=True)

    # THE CROSS-TAB. "priced" is bpa is not None -- the row has a number -- never my reading
    # of which branch set bpa_source.
    cells = Counter()
    by_source = Counter()
    for r in board:
        priced = r.get("bpa") is not None
        kind = r.get("absence_kind")
        cells[(kind, priced)] += 1
        by_source[(kind, r.get("bpa_source"))] += 1

    print(f"\n   {'absence_kind':<22} {'priced':<8} rows", flush=True)
    for (kind, priced), n in sorted(cells.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        print(f"   {str(kind):<22} {str(priced):<8} {n}", flush=True)

    print(f"\n   {'absence_kind':<22} {'bpa_source':<40} rows", flush=True)
    for (kind, src), n in sorted(by_source.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        print(f"   {str(kind):<22} {str(src):<40} {n}", flush=True)

    # THE CONTRACT, stated as a number rather than as a claim.
    breaches = cells[(dr.ABSENCE_NO_INPUT, True)] + cells[(dr.ABSENCE_BELOW_SOURCE_CUTOFF, True)] \
        + cells[(dr.ABSENCE_NO_REPLACEMENT, True)]
    silent = cells[(None, False)]
    print(f"\n   CONTRACT BREACHES (a kind on a PRICED row): {breaches}", flush=True)
    print(f"   UNCLASSIFIED (an unpriced row with NO kind): {silent}", flush=True)

    OUT.write_text(json.dumps(
        {"board_rows": len(board), "universe": prov["players_in_pool"],
         "kind_by_priced": {f"{k}|{p}": n for (k, p), n in cells.items()},
         "kind_by_source": {f"{k}|{s}": n for (k, s), n in by_source.items()},
         "contract_breaches_kind_on_priced_row": breaches,
         "unclassified_unpriced_rows": silent}, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
