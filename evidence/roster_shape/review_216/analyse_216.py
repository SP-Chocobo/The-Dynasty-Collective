"""Tables for the #216 review report, from r216 (CURRENT/NOFEAS/NEEDCAP), r216b (MLV arms,
fixed phantoms) and r216c (CURRENT re-recorded with fixed phantoms for the static metric)."""
import json, sys, collections
from pathlib import Path
SP = Path(sys.argv[1])
out = []
P = out.append
for fmt in ("12T_ppr", "12T_ppr_SF"):
    a = json.load(open(SP / "r216" / f"{fmt}.json"))
    b = json.load(open(SP / "r216b" / f"{fmt}.json"))
    c = json.load(open(SP / "r216c" / f"{fmt}.json"))
    by = {(x["arm"], x["seat"]): x for x in a["drafts"] + b["drafts"]}
    cur_fixed = {x["seat"]: x for x in c["drafts"]}
    P(f"\n## {fmt}  {a['roster_positions']}  pool {a['pool_size']}  commit {a['commit']}\n")
    P("| seat | arm | composition | lineup pts | roster pts | forced by feasibility_first (round pos) | QB taken (round, bpa at that state) |")
    P("|---|---|---|---|---|---|---|")
    for seat in ("1", "6", "12"):
        for arm in ("CURRENT", "NOFEAS", "NEEDCAP", "RFMLV_LEX", "RFMLV_ADD", "RAWMLV_LEX"):
            x = by.get((arm, seat))
            if not x:
                continue
            forced = [f"r{s['round']} {s['position']}" for s in x["sequence"] if s["fills_required_slot"]]
            qb = [(s["round"], st["chosen"]["bpa"]) for s, st in zip(x["sequence"], x["states"]) if s["position"] == "QB"]
            comp = " ".join(f"{p}{n}" for p, n in sorted(x["composition"].items(), key=lambda t: -t[1]))
            P(f"| {seat} | {arm} | {comp} | {x['lineup_points']:.0f} | {x['roster_points']:.0f} | {', '.join(forced) or '-'} | {qb or '-'} |")
        ctl = by[("CURRENT", seat)]
        P(f"| {seat} | control (seat {ctl['control_seat']}) | " + " ".join(f"{p}{n}" for p, n in sorted(ctl['control_composition'].items(), key=lambda t: -t[1])) + f" | {ctl['control_lineup_points']:.0f} | - | - | - |")
    # identity checks
    for seat in ("1", "6", "12"):
        cu = [s["player"] for s in by[("CURRENT", seat)]["sequence"]]
        nc = [s["player"] for s in by[("NEEDCAP", seat)]["sequence"]]
        P(f"- seat {seat}: NEEDCAP pick-for-pick identical to CURRENT: {cu == nc}; replay matches recorded #216 JSON: {by[('CURRENT', seat)].get('replay_matches_recorded')}")
    # static metric with fixed phantoms
    P("\n### Static: at CURRENT's own 14/15 states per seat (fixed phantoms), RF-MLV vs the board\n")
    P("| seat | states | rf top == board top | rank of board's top row under RF-MLV (per round) | of board's top-10 rows, how many change rank (per round) |")
    P("|---|---|---|---|---|")
    for seat in ("1", "6", "12"):
        st = cur_fixed[seat]["states"]
        P(f"| {seat} | {len(st)} | {sum(1 for s in st if s['rf_top_equals_board_top'])} | {[s['rf_rank_of_board_top'] for s in st]} | {[s['board_top10_moved_under_rf'] for s in st]} |")
    P("\n### QB pricing in CURRENT (best QB row's bpa per round; league QB starter demand per round)\n")
    for seat in ("1", "6", "12"):
        st = by[("CURRENT", seat)]["states"]
        P(f"- seat {seat}: bpa {[round(s['best_by_position'].get('QB', {}).get('bpa'), 1) if s['best_by_position'].get('QB', {}).get('bpa') is not None else None for s in st]}")
        P(f"  demand {[s['remaining_starter_demand'].get('QB', 0) for s in st]}  need_bonus max on board {max(s['need_bonus_max_on_board'] for s in st)}  rows at NEED_BONUS_MAX {sum(s['rows_at_need_cap'] for s in st)}  depth_exposure max {max((s['depth_exposure_max'] or 0) for s in st)}")
    P("\n### Replacement gap WR-TE (points) and my TE count, per round, CURRENT\n")
    for seat in ("1", "6", "12"):
        st = by[("CURRENT", seat)]["states"]
        P(f"- seat {seat}: {[(s['round'], round(s['implied_replacement'].get('WR', 0) - s['implied_replacement'].get('TE', 0), 1), s['my_counts'].get('TE', 0)) for s in st]}")
    P("\n### Sequences\n")
    for seat in ("1", "6", "12"):
        for arm in ("CURRENT", "NOFEAS", "RFMLV_LEX", "RFMLV_ADD", "RAWMLV_LEX"):
            x = by.get((arm, seat))
            if x:
                P(f"- {arm} seat {seat}: " + " | ".join(f"r{s['round']} {s['position']} {s['player']} {s['projected_points']}{'*' if s['fills_required_slot'] else ''}" for s in x["sequence"]))
print("\n".join(out))
