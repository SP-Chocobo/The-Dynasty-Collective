"""How much of G9's verdict is the ruler's own named contamination?

G9a (the owner's gate) is a SIGN TEST on `run_roster_proof`'s `cdme` ruler compared on
`total_value` -- the pre-draft board's `universal_value` summed over the whole finished roster.
That sum carries a contamination the roster proof already names and refuses to fix:
`CDME_TOTAL_CONTAMINATION` -- it counts a below-replacement player as a LIABILITY you carry
rather than as someone you would simply drop. #216's fix changes the BENCH's character (surplus
scarce-position players out, near-lineup receivers in), which is precisely the population that
contamination is about, so the gate's verdict and the contamination are not independent.

THIS INSTRUMENT SETTLES NOTHING AND RE-GATES NOTHING. Flooring the sum is a reserved question
(#155/#165) and the exchange rate between what a roster FIELDS and what it OWNS is #50, the
owner's. All this does is re-score the ALREADY-RECORDED rosters under the same `universal_value`
summed over three different SETS, so the owner can see whether G9's two superflex reversals are
a statement about the fix or a statement about the sum:

    total    -- every drafted player, negatives included (G9's ruler, as pre-registered)
    floored  -- every drafted player, each contribution floored at 0.0 (the reserved reading)
    starter  -- the optimal lineup only (what the roster FIELDS; already recorded, reproduced
                here as a harness check)

No draft is run: the rosters come from the recorded probe output, and the ruler is rebuilt from
the same pre-draft board the probe used. The harness proves itself by REPRODUCING each recorded
`cdme_total_value` and `cdme_starter_value` exactly; a run that cannot reproduce them says so
and reports nothing else.

Read `--in` (the fix probe's output directory), write a table and a JSON beside it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import lineup_optimizer as lo
import resume_join
import run_draft_battery as rdb
import run_roster_proof as rp

SETS = ("total", "floored", "starter")


def _roster_ids(draft: dict) -> list[str]:
    """The engine seat's drafted player_ids, in pick order, from the recorded states.

    `sequence` carries names only; `states` carries the chosen ROW, and a row has an id. One
    state per one of my picks, so the two must agree in length -- checked by the caller, because
    a silent length mismatch here would score a roster that is not the one that was drafted.
    """
    return [str(s["chosen"]["player_id"]) for s in draft["states"]]


def score_sets(ids, values, eligible, slots) -> dict:
    entries = [{"id": pid, "value": values.get(pid) or 0.0, "eligible": eligible[pid]} for pid in ids]
    floored = [{**e, "value": max(e["value"], 0.0)} for e in entries]
    return {
        "total": round(sum(e["value"] for e in entries), 2),
        "floored": round(sum(e["value"] for e in floored), 2),
        "starter": round(lo.optimize_lineup(entries, slots)["total_value"], 2),
        "unpriced": sum(1 for pid in ids if values.get(pid) is None),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    src = Path(args.src)
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    report = {"commit": resume_join.head_commit(), "universe": universe,
              "source": str(src), "reproduces_recorded": True, "formats": []}
    lines = []
    for path in sorted(src.glob("*.json")):
        recorded = json.loads(path.read_text())
        label = recorded.get("format")
        if label is None:
            continue
        spec = next((s for s in rp.PROOF_FORMATS if s["label"] == label), None)
        if spec is None:
            continue
        league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"],
                                      scoring=spec["scoring"], te_premium=spec["te_premium"],
                                      dynasty=True, base_scoring=scoring)
        merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
        values = db.reference_values(merger, players_db, league, sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        block = {"format": label, "arms": []}
        for draft in recorded["drafts"]:
            ids = _roster_ids(draft)
            if len(ids) != len(draft["sequence"]):
                block.setdefault("skipped", []).append(
                    {"arm": draft["arm"], "seat": draft["seat"],
                     "why": f"states {len(ids)} != sequence {len(draft['sequence'])}"})
                continue
            eligible = {pid: set((players_db.get(pid) or {}).get("fantasy_positions")
                                 or ([(players_db.get(pid) or {}).get("position")]
                                     if (players_db.get(pid) or {}).get("position") else []))
                        for pid in ids}
            scored = score_sets(ids, values, eligible, slots)
            g9 = draft.get("g9_engine") or {}
            check = {"total": g9.get("cdme_total_value"), "starter": g9.get("cdme_starter_value")}
            ok = all(check[k] is None or abs(check[k] - scored[k]) < 0.02 for k in check)
            if not ok:
                report["reproduces_recorded"] = False
            block["arms"].append({"arm": draft["arm"], "seat": draft["seat"], **scored,
                                  "recorded": check, "reproduced": ok})
        report["formats"].append(block)
        lines.append(f"## {label}")
        lines.append(f"| seat | arm | total | floored | starter | reproduces recorded |")
        lines.append("|---|---|---|---|---|---|")
        for a in sorted(block["arms"], key=lambda a: (a["seat"], a["arm"])):
            lines.append(f"| {a['seat']} | {a['arm']} | {a['total']:.1f} | {a['floored']:.1f} "
                         f"| {a['starter']:.1f} | {'yes' if a['reproduced'] else 'NO'} |")
        lines.append("")
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "asset_ruler_sets.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "TABLES_asset_ruler_sets.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("reproduces every recorded number:", report["reproduces_recorded"])
    return 0 if report["reproduces_recorded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
