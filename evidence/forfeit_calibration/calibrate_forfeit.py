"""#296: does `positional_forfeit` predict what actually happens, or does a constant do better?

THE QUESTION, AND WHY IT IS THIS ONE. `positional_forfeits` walks a position's value curve down by
`round(expected_taken)` players and reports the drop. The forfeit is therefore only as good as
`expected_taken` -- "how many players at position P go between this turn and my next one" -- and
that quantity is the one worth testing, because it is ROSTER-INDEPENDENT. The value terms are not:
my own roster changes between the two turns, so `position_next_turn_value` and the actual best
left at the next turn are not measured in the same units, and a difference between them would
confound the model with my own pick.

THE BAR IS THE ONE SURVIVAL FAILED. `survival_calibration/` asked whether a 30% claim came back
30% of the time, and the answer put the whole family behind `withheld_fields()`. Its cousin had
never been asked anything: `evidence/forfeit_knife_edge/` is a QUANTISATION probe (#86, whether
`round()` is a knife-edge), not a calibration. So the forfeit was shown on every door with no
evidence of its own, which is the gap this closes.

#56 HELD EXPLICITLY. This MEASURES and tunes nothing. No number it produces may be written back
into the engine as a constant: the capture's LIMITS forbid calibrating against one league, and
that prohibition does not soften because the error was measured rather than guessed.

THE POPULATION CONFOUND, RULED OUT RATHER THAN ASSUMED. Counting the wrong population is the
failure this repository keeps re-learning, and here it would manufacture exactly the bias the
model appears to have: if `expected_taken` only claims to predict takes from the PRICED pool and
the instrument counts every body drafted, the model looks systematically low for free. So both
populations are recorded per row. The restriction is not vacuous -- the priced filter excludes
489 of 970 board rows on an opening 12T_ppr board -- and it changed nothing, because every
intervening pick in every replay was already priced.

SCOPE LIMIT, STATED. The replays are engine-driven drafters (VDS `sharp_auto`), not humans. The
model predicts opponent takes; measuring it against opponents that are themselves engine strategy
is a real limit on how far the result generalises, and it cuts both ways -- failing to predict its
own kin is not a weaker indictment than failing to predict a stranger.

A SECOND LIMIT NOT RULED OUT. Takes are attributed by `players_db` position, so a multi-eligible
player taken into a flex counts under his listed position. If the engine counts by the opponent
board row's position instead, some of the gap is attribution rather than prediction. WR carries
the largest bias, which is where that would bite hardest.

Fixture discipline is the engine-measurement skill's, every line load-bearing: run from the REPO
ROOT (DataMerger resolves baselines against cwd); `build_players_db_from_capture`, which is the
6,595-row universe production receives, NOT the 764-row vendor reconstruction; season projections
on SLEEPER_BASIS_SEASON_SUM so the league's own scoring reaches a price; `set_league_format` per
format, because format is FILE SELECTION and not `scoring_settings`; turns chosen on the gap
AHEAD, since the forfeit is computed over the picks between this turn and my next one; and pick
records carrying {pick_no, round, roster_id, player_id} because mode="auto" reads `round`.

    PYTHONDONTWRITEBYTECODE=1 python3 -u evidence/forfeit_calibration/calibrate_forfeit.py [turns]
"""
import json, pathlib, sys, statistics, collections
sys.path.insert(0, str(pathlib.Path.cwd()))
import data_merger as dm, draft_room as dr, draft_battery as db, draft_strategy as ds
import pick_synthesis as ps, run_draft_battery as rdb

VDS = pathlib.Path("evidence/batteries/VDS_2026-10-01_varied_drafting_strategy_dd4ade7.json")
OUT = pathlib.Path("evidence/forfeit_calibration/forfeit_calibration.json")
WANT = ["12T_ppr", "12T_ppr_SF", "HEAVY_IDP", "12T_ppr_K_DEF", "4WR_TE_PREMIUM", "LIGHT_IDP"]
MAX_TURNS = int(sys.argv[1]) if len(sys.argv) > 1 else 13


def collect():
    players_db, _ = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    scoring = rdb.scoring_settings_from_capture()
    arms = {a["label"]: a for a in db.league_matrix(scoring)}
    vds = json.loads(VDS.read_text())
    seqs = {(r.get("format"), r.get("strategy")): r.get("pick_sequence")
            for r in vds["results"] if r.get("pick_sequence")}
    sim = pathlib.Path("ui_explore/_sim_sequences.json")
    if sim.exists():
        for label, seq in json.loads(sim.read_text()).items():
            seqs.setdefault((label, "sharp_auto"), seq)
    pid_of = lambda p: p.get("chosen_player_id") if isinstance(p, dict) else p
    pos_of = lambda pid: (players_db.get(str(pid)) or {}).get("position") or "?"

    rows, absent, skipped = [], collections.Counter(), []
    for label in WANT:
        arm, seq = arms.get(label), seqs.get((label, "sharp_auto"))
        if not arm or not seq:
            skipped.append(f"{label}: {'no arm' if not arm else 'no sequence'}"); continue
        league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
        merger = dm.DataMerger()
        merger.set_league_format(db.league_format_hint(league))
        order = ds.generate_pick_order([str(i) for i in range(1, teams + 1)], rounds, "snake")
        ME = "6"
        mine = [i for i in range(min(len(seq), len(order))) if order[i] == ME]
        usable = [(i, mine[n + 1]) for n, i in enumerate(mine)
                  if n + 1 < len(mine) and mine[n + 1] - i > 1]
        for (i, j) in usable[:MAX_TURNS]:
            picks = [{"pick_no": k + 1, "round": k // teams + 1, "roster_id": order[k],
                      "player_id": pid_of(seq[k])} for k in range(i)]
            if picks:
                need = {"pick_no", "round", "roster_id", "player_id"} - set(picks[0])
                assert not need, f"pick records missing {need}; mode='auto' reads `round`"
            snap = ps.build_snapshot(merger, players_db, picks, order, i, ME, league,
                pick_label=f"{i//teams+1}.{i%teams+1:02d}", mode="auto",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            bd = dr.compute_draft_board(merger, players_db, picks, ME, league, mode="auto",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            brows = bd if isinstance(bd, list) else bd.to_dict("records")
            priced = {str(r["player_id"]) for r in brows
                      if r.get("projected_points") is not None or r.get("final_score") is not None}
            actual = collections.Counter(pos_of(pid_of(seq[k])) for k in range(i + 1, j))
            rated = collections.Counter(pos_of(pid_of(seq[k])) for k in range(i + 1, j)
                                        if str(pid_of(seq[k])) in priced)
            before = collections.Counter(pos_of(pid_of(seq[k])) for k in range(i))
            seen = set()
            for c in snap.candidates:
                P = getattr(c, "position", None)
                if not P or P in seen: continue
                seen.add(P)
                et = getattr(c, "position_expected_taken", None)
                if et is None:
                    absent[f"{label}:{P}"] += 1; continue
                rows.append({"arm": label, "turn": i, "gap": j - i - 1, "pos": P,
                             "pred": float(et), "actual": actual.get(P, 0),
                             "actual_rated": rated.get(P, 0),
                             "share_prior": before.get(P, 0) / max(1, i),
                             "forfeit": getattr(c, "positional_forfeit", None)})
        print(f"  {label}: {sum(1 for r in rows if r['arm']==label)} (turn, position) pairs", flush=True)
    return rows, dict(absent), skipped


def report(rows):
    """Model against the naive predictors. A fitted constant is the STRONGEST constant, which is
    the honest bar -- survival lost to one, and so this asks the same question the same way."""
    mean = statistics.mean(r["actual"] for r in rows)
    bypos = {}
    for r in rows: bypos.setdefault(r["pos"], []).append(r["actual"])
    bypos = {p: statistics.mean(v) for p, v in bypos.items()}
    arms = {"MODEL expected_taken": lambda r: r["pred"],
            "base nothing taken":   lambda r: 0.0,
            "base global constant": lambda r: mean,
            "base per-position constant": lambda r: bypos[r["pos"]],
            "base gap x prior share":     lambda r: r["gap"] * r["share_prior"]}
    out = {}
    for name, f in arms.items():
        out[name] = {"MAE": round(statistics.mean(abs(f(r) - r["actual"]) for r in rows), 4),
                     "RMSE": round(statistics.mean((f(r) - r["actual"]) ** 2 for r in rows) ** 0.5, 4),
                     "bias": round(statistics.mean(f(r) - r["actual"] for r in rows), 4)}
    buckets = {}
    B = collections.defaultdict(list)
    for r in rows: B[min(3, int(r["pred"]))].append(r)
    for b in sorted(B):
        s = B[b]
        buckets[f"predicted {b}.x"] = {"n": len(s),
            "mean_predicted": round(statistics.mean(x["pred"] for x in s), 3),
            "mean_actual": round(statistics.mean(x["actual"] for x in s), 3),
            "mean_actual_rated": round(statistics.mean(x["actual_rated"] for x in s), 3)}
    wins = 0
    per_arm = {}
    for a in sorted({r["arm"] for r in rows}):
        s = [r for r in rows if r["arm"] == a]
        bp = {}
        for r in s: bp.setdefault(r["pos"], []).append(r["actual"])
        bp = {p: statistics.mean(v) for p, v in bp.items()}
        m = statistics.mean(abs(r["pred"] - r["actual"]) for r in s)
        c = statistics.mean(abs(bp[r["pos"]] - r["actual"]) for r in s)
        per_arm[a] = {"n": len(s), "model_MAE": round(m, 4), "constant_MAE": round(c, 4),
                      "model_better": bool(m < c)}
        wins += m < c
    return {"n": len(rows), "mean_actual_takes": round(mean, 4), "arms": out,
            "reliability": buckets, "per_format": per_arm,
            "formats_model_beats_its_own_constant": f"{wins} of {len(per_arm)}"}


if __name__ == "__main__":
    rows, absent, skipped = collect()
    payload = {"_what": "Calibration of positional_forfeit's input, expected_taken, against replayed drafts.",
               "_not": "Not a tuning run. #56: nothing here may be written back into the engine.",
               "_bar": "a fitted constant, the predictor survival_probability lost to",
               "_population": "VDS sharp_auto replays -- engine-driven drafters, not humans",
               "_absent": absent, "_skipped": skipped,
               "summary": report(rows), "rows": rows}
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\nwrote {len(rows)} rows -> {OUT}")
    for k, v in payload["summary"]["arms"].items():
        print(f"   {k:<30} MAE {v['MAE']:.3f}  bias {v['bias']:+.3f}")
    print(f"   {payload['summary']['formats_model_beats_its_own_constant']} formats beat their own constant")
