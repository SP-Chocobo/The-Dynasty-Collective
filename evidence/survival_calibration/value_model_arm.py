"""#206: score the VALUE-SHARE take model against the rank table, on the real draft.

WHY THIS FILE EXISTS RATHER THAN A FLAG IN THE ENGINE. `draft_strategy._board_take_probability`
is a seam: production has exactly one take model, and an alternative is substituted here for
the duration of ONE measurement process. Both arms therefore run the same `estimate_survival`,
the same `build_snapshot` and the same boards, and exactly one thing is toggled -- the
engine-measurement rule. Nothing below may outlive the process that runs it.

WHAT IS BEING TESTED. The rank table cannot express the difference between an opponent scoring
their top two 265.11 / 262.54 (a coin flip) and 265.11 / 199.00 (a lock): both are "rank 1 and
rank 2". `_value_take_weight` reads the opponent's own `final_score` instead --
exp((score - leader) / scale), with `scale` derived per board from the dispersion among one
round's worth of contenders.

WHAT THE PRE-MEASUREMENT ALREADY SHOWED, stated here so the arms are not read as a search. On
this league's boards the value model's PRICED shape is what it claims: the leader takes
0.157-0.265 of the priced mass, the top five 0.60-0.78, with 6.6-10.6 effective contenders.
But the unpriced block -- 638 rows carrying RANK_TAKE_PROBABILITY_FLOOR each -- weighs 2.0x to
3.4x the entire priced mass, so a straight wiring would dilute that shape by a factor of three.
The floor's 0.02 was derived against a rank table whose leader was 0.55; the value model's
leader weighs 1.0, and carrying the constant across unchanged is the unit drift `#75` names.
The floor arms below exist to measure that, not to tune it.

THE ARMS, and what each may conclude:

  rank        production, untouched. The number to beat, and the control that proves the
              patching machinery changed nothing when it is not installed.
  value_floor value weights, unpriced rows keep RANK_TAKE_PROBABILITY_FLOOR. The honest
              straight wiring -- what shipping `_value_take_weight` today would do.
  value_zero  value weights, unpriced rows carry NO mass. NOT A CANDIDATE: it asserts
              "unpriced means safe", which the owner ruled against and which 31 of 301 real
              picks refute. It is here as a BOUND -- the best the value model could score if
              the floor question were wished away -- so the floor's cost is measurable rather
              than argued.
  value_min   WITHDRAWN BEFORE IT RAN, and the reason is kept because it is the finding.
              The idea was to place an unpriced row at the priced board's OWN minimum weight:
              derived per board, no constant, a genuine bound. Pinned against a real board it
              produced p(rank1)=0.4440 and an unpriced share of 0.0% -- DIGIT-FOR-DIGIT
              `value_zero`. It degenerates because the minimum priced weight is
              exp((worst - leader) / scale) with the board spanning ~13 scales, so 638 rows
              times ~1e-6 is not a share at all. Running it would have produced a second
              identical number, and `#245` says identical numbers are a broken instrument
              until proven otherwise -- this one is explained rather than broken, so it is
              withdrawn rather than reported. It is NOT a third option: it is `value_zero`
              wearing a derivation, and it asserts the same "unpriced means safe" the owner
              ruled against.

Run from the repo root. NEVER cd first.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u \
        evidence/survival_calibration/value_model_arm.py <arm>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import draft_strategy as ds

sys.path.insert(0, str(Path("evidence/survival_calibration")))
import calibrate  # noqa: E402  (path is set immediately above)

ARMS = ("rank", "value_floor", "value_zero")
OUT_DIR = Path("evidence/survival_calibration")


def _value_seam(contention_size: int, unpriced_mode: str):
    """Build the substitute seam. `contention_size` is one round's worth of picks -- a league
    fact, not a tuned number -- and `unpriced_mode` is which of the three floor treatments
    above to apply."""
    def seam(board, target_key, rank, unpriced, is_run, run_position):
        cache_key = ("_value_mass", run_position or "", unpriced_mode)
        cache = board.setdefault("_value_mass_cache", {})
        if cache_key not in cache:
            by_id = board.get("by_id") or {}
            scores = []
            for player_id in (board.get("rank_by_id") or {}):
                row = by_id.get(player_id)
                if row is not None and not ds._is_absent(row.get("final_score")):
                    scores.append((player_id, float(row["final_score"])))
            scale = ds.board_contention_scale(board, contention_size)
            if not scores or scale is None:
                cache[cache_key] = None
            else:
                leader = max(s for _, s in scores)
                weights = {}
                for player_id, score in scores:
                    row = by_id.get(player_id)
                    run = bool(run_position and row is not None
                               and row.get("position") == run_position)
                    weights[player_id] = ds._value_take_weight(score, leader, scale, run)
                n_unpriced = len(board.get("unpriced_ids") or ())
                if unpriced_mode == "floor":
                    w_unpriced_each = ds.RANK_TAKE_PROBABILITY_FLOOR
                elif unpriced_mode == "zero":
                    w_unpriced_each = 0.0
                else:
                    raise ValueError(f"unknown unpriced_mode {unpriced_mode!r}")
                w_unpriced = n_unpriced * w_unpriced_each
                total = sum(weights.values()) + w_unpriced
                cache[cache_key] = {
                    "weights": weights, "each": w_unpriced_each, "total": total,
                    "share": (w_unpriced / total) if total > 0 else None,
                }
        mass = cache[cache_key]
        if mass is None or mass["total"] <= 0:
            # The board cannot support the statistic. Measured 0 of 120 times on this league's
            # real boards, so this is defensive -- and it falls back to PRODUCTION rather than
            # to a substituted number, because an arm that quietly invents a value here would
            # be measuring itself.
            return ds._board_take_probability_production(
                board, target_key, rank, unpriced, is_run, run_position)
        if unpriced:
            return mass["each"] / mass["total"], mass["share"]
        return mass["weights"].get(target_key, 0.0) / mass["total"], mass["share"]
    return seam


def main(arm: str) -> int:
    if arm not in ARMS:
        raise SystemExit(f"usage: value_model_arm.py [{'|'.join(ARMS)}]  (got {arm!r})")

    rules = json.loads(calibrate.REAL_RULEBOOK.read_text())
    contention = int(rules["total_rosters"])

    # Keep production reachable under its own name, so the fallback above is not recursive and
    # so the control arm can prove the machinery is inert.
    ds._board_take_probability_production = ds._board_take_probability
    if arm != "rank":
        ds._board_take_probability = _value_seam(contention, arm.split("_", 1)[1])

    # Redirect the harness's outputs so an arm cannot overwrite another arm's evidence (#176:
    # a dead process's output overwriting a valid run cost a whole finding once already).
    calibrate.OUT_REAL = OUT_DIR / f"calibration_real_{arm}.json"
    calibrate.OUT_REAL_RAW = OUT_DIR / f"calibration_real_{arm}_raw.json"
    print(f"=== ARM {arm}  contention_size={contention}  "
          f"seam={'PRODUCTION (control)' if arm == 'rank' else 'value-share substitute'} ===",
          flush=True)
    return calibrate.main_real()


if __name__ == "__main__":
    raise SystemExit(main((sys.argv[1] if len(sys.argv) > 1 else "rank").lower()))
