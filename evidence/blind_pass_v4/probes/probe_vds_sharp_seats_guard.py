"""Can `run_vds_battery._report`'s noise-arm exclusion fire?

The block that builds `STRATEGY_SPECIFIC_FINDINGS` says:

    # Also skipped: arms whose `sharp_seats` is empty. `noisy_k3`/`noisy_k8` contain no engine
    # seat at all, so a finding there is a property of uniform random draws and belongs on no
    # strategy's ledger.
    if row["label"] in inert_labels or not row.get("sharp_seats", ["present"]):

`sharp_seats` is not a key on an arm row. It lives at `opponent_noise.sharp_seats` in
`vds_battery.STRATEGIES`, is passed into `simulate_full_draft`, and the arm row that
`draft_battery.run_battery` produces carries neither spelling. `row.get(..., ["present"])`
therefore always returns the truthy default and `not [...]` is always False.

Measured against PRODUCTION'S OWN SHAPE rather than a hand-built dict (engine-measurement:
"build production's inputs in production's SHAPE"): the rows here are the real serialized arms
from the last committed VDS run.

Run from the repo root:
  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_vds_sharp_seats_guard.py
"""
import copy
import glob
import json
import time

import run_vds_battery as rvb
import vds_battery


def main() -> None:
    path = sorted(glob.glob("evidence/batteries/VDS_*.json"))[-1]
    committed = json.load(open(path))
    rows = committed["results"]
    print(f"committed run: {path}")
    print(f"arms: {len(rows)}")
    print(f"keys on an arm row: {sorted(rows[0])}")
    print(f"rows carrying a top-level 'sharp_seats': "
          f"{sum(1 for r in rows if 'sharp_seats' in r)} of {len(rows)}")
    print(f"rows carrying 'opponent_noise'        : "
          f"{sum(1 for r in rows if 'opponent_noise' in r)} of {len(rows)}")
    print("\nwhere sharp_seats really lives, per STRATEGIES:")
    for name, cfg in vds_battery.STRATEGIES.items():
        noise = cfg.get("opponent_noise")
        print(f"   {name:<18} opponent_noise={noise}")

    # Rebuild the report from the committed arms with TODAY's _report, so the reading is about
    # the code on disk now rather than the code that wrote that file.
    rebuilt = rvb._report(committed["universe"], copy.deepcopy(rows), time.time(), complete=True)
    print(f"\n_report(...) rebuilt from those arms:")
    print(f"   INERT_ARMS                 : {rebuilt['INERT_ARMS']}")
    print(f"   STRATEGY_SPECIFIC_FINDINGS : {rebuilt['STRATEGY_SPECIFIC_FINDINGS']}")

    noise_strategies = sorted(n for n, c in vds_battery.STRATEGIES.items()
                              if (c.get("opponent_noise") or {}).get("sharp_seats") == [])
    print(f"\nstrategies the comment says must be excluded (sharp_seats == []): {noise_strategies}")
    listed = sorted({s for ss in rebuilt["STRATEGY_SPECIFIC_FINDINGS"].values() for s in ss})
    print(f"strategies STRATEGY_SPECIFIC_FINDINGS actually lists             : {listed}")
    print(f"   -> {'EXCLUSION DID NOT FIRE' if set(listed) & set(noise_strategies) else 'excluded'}")

    # Now the same rows with the key the guard reads actually present, to prove the guard body
    # works and it is the KEY NAME that is wrong.
    patched = copy.deepcopy(rows)
    for r in patched:
        cfg = vds_battery.STRATEGIES.get(r.get("strategy")) or {}
        noise = cfg.get("opponent_noise") or {}
        if "sharp_seats" in noise:
            r["sharp_seats"] = noise["sharp_seats"]
    with_key = rvb._report(committed["universe"], patched, time.time(), complete=True)
    print(f"\nsame arms, with a top-level sharp_seats copied in from STRATEGIES:")
    print(f"   STRATEGY_SPECIFIC_FINDINGS : {with_key['STRATEGY_SPECIFIC_FINDINGS']}")


if __name__ == "__main__":
    main()
