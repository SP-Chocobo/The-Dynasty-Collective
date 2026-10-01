"""Does the suite DEFEND each repair, or merely coexist with it?

For each repair: revert exactly that line (or lines) in a clean worktree at the freeze candidate,
run the test modules that ought to notice, and record whether anything failed. A repair no test
defends is a repair that can be undone silently by the next hand.

Every arm runs under PYTHONDONTWRITEBYTECODE=1 with `__pycache__` cleared, because a
length-preserving edit inside one mtime second otherwise serves the previous bytecode (the
`engine-measurement` rule). Each arm is restored with `git checkout --` and the tree is asserted
clean before the next.

Usage, from the worktree root:
    PYTHONDONTWRITEBYTECODE=1 python3 probe_mutation_do_tests_defend_the_repairs.py
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

#: (label, file, find, replace, test modules that ought to notice)
ARMS = [
    ("A-F2  health_penalty returns 0.0 for an absent projection",
     "draft_room.py", "        return 0.0\n    return rate * projected_points",
     '        return float("nan")\n    return rate * projected_points',
     ["test_one_fact_two_paths_one_answer", "test_draft_room", "test_risk_adj_absence",
      "test_availability_haircut"]),

    ("B-F4  feasibility_first reads eligibility on the candidate side",
     "draft_room.py",
     '    if "player_id" not in scored.columns:\n'
     '        return scored["position"].map(\n'
     '            lambda position: 0 if position in needed_positions else 1).astype(int)\n'
     '    return pd.Series(',
     '    if True:\n'
     '        return scored["position"].map(\n'
     '            lambda position: 0 if position in needed_positions else 1).astype(int)\n'
     '    return pd.Series(',
     ["test_one_eligibility_vocabulary_everywhere", "test_feasibility_backstop",
      "test_draft_room"]),

    ("B-F6  a rosterless pick creates no phantom roster",
     "draft_room.py",
     '        if pick.get("roster_id") is None:\n            continue\n',
     '        if False:\n            continue\n',
     ["test_one_league_one_team_count", "test_draft_room"]),

    ("C-F3  filter_candidates_by_view filters on eligibility",
     "draft_board_ui.py",
     "        return bool((candidate.eligible_positions or {candidate.position}) & set(positions))",
     "        return candidate.position in set(positions)",
     ["test_one_eligibility_vocabulary_everywhere", "test_draft_board_ui",
      "test_a_flex_view_exists_for_every_flex_slot"]),

    ("C-F3  eligible_positions is populated by build_snapshot",
     "pick_synthesis.py",
     "        return frozenset(eligible or ({row[\"position\"]} if row.get(\"position\") else ()))",
     "        return frozenset()",
     ["test_one_eligibility_vocabulary_everywhere", "test_pick_synthesis",
      "test_snapshot_identity_boundary", "test_draft_board_ui"]),

    ("E-F5  a failed season fetch returns a refusal string",
     "sleeper_client.py",
     '        if (coverage or {}).get("error"):\n            return None, (',
     '        if False:\n            return None, (',
     ["test_a_partial_season_is_not_a_season", "test_sleeper_client"]),

    ("A-F5  the Draft Room puts the draft's seats on the league dict",
     "app.py", "                                league_config.PICK_ORDER_KEY: round_1_order,\n", "",
     ["test_one_league_one_team_count", "test_ui_source", "test_three_derivations_of_one_number",
      "test_mock_draft_wiring", "test_live_board_pricing"]),

    ("A-F1  presentable_text checks absence before withholding",
     "pick_synthesis.py",
     "    if rendered is None or rendered == ABSENT_FIGURE:\n        return rendered\n", "",
     ["test_withheld_propagation", "test_survival_absence_contract", "test_absence_survives_consumers",
      "test_pick_synthesis", "test_dock_absence_contract"]),

    ("D10  ambiguities splits the unknown-slot alarm into three bands",
     "league_config.py",
     '        if nonplaying:\n            found.append({\n                "kind": AMBIGUITY_UNKNOWN_SLOT_NONPLAYING,',
     '        if False:\n            found.append({\n                "kind": AMBIGUITY_UNKNOWN_SLOT_NONPLAYING,',
     ["test_a_warning_is_as_loud_as_its_consequence", "test_league_config", "test_slot_vocabulary"]),

    ("D-F2  the history shield is scoped to the paragraph, not the block",
     "prose_names.py",
     "            if is_history(_paragraph_around(text, match.start())):\n                continue\n",
     "            if is_history(text):\n                continue\n",
     ["test_prose_names", "test_source_scan"]),

    ("D-F4  the per-method floor key is qualified Class.method",
     "assertion_floors.py",
     'by_method[f"{cls.name}.{fn.name}"] = dict(sorted(inner.items()))',
     'by_method[fn.name] = dict(sorted(inner.items()))',
     ["test_assertion_floors"]),

    ("A-F5  _round_being_decided routes through team_count/round_of",
     "pick_synthesis.py",
     "    teams, basis = lc.team_count_with_basis(league, picks=picks)\n"
     "    if basis == lc.TEAM_BASIS_FLOOR:\n"
     "        return max((p.get(\"round\") or 1) for p in picks)\n"
     "    return lc.round_of(len(picks), teams)",
     "    teams = 0\n"
     "    if league:\n"
     "        teams = int(league.get(\"total_rosters\") or 0)\n"
     "    if not teams:\n"
     "        teams = len({p.get(\"roster_id\") for p in picks if p.get(\"roster_id\") is not None})\n"
     "    if not teams:\n"
     "        return max((p.get(\"round\") or 1) for p in picks)\n"
     "    return len(picks) // teams + 1",
     ["test_one_league_one_team_count", "test_pick_synthesis",
      "test_three_derivations_of_one_number"]),
]


def clear_cache():
    for d in pathlib.Path(".").rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def run(modules):
    clear_cache()
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "-v", *modules],
        capture_output=True, text=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".",
             "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": "/root"})
    tail = proc.stderr.strip().splitlines()
    verdict = next((l for l in reversed(tail) if l.startswith(("OK", "FAILED"))), "?")
    names = [l.split(" ")[1] for l in tail if l.startswith(("FAIL: ", "ERROR: "))]
    return verdict, names


def restore(path):
    subprocess.run(["git", "checkout", "--", path], check=True)
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout
    assert not dirty.strip(), f"TRACKED FILES NOT CLEAN after restoring {path}:\n{dirty}"


print("CONTROL: the clean tree, on the union of every module named below")
union = sorted({m for *_, mods in ARMS for m in mods})
print("   ", run(union)[0])
print()

for label, path, find, repl, modules in ARMS:
    source = pathlib.Path(path)
    text = source.read_text(encoding="utf-8")
    if text.count(find) != 1:
        print(f"[SKIP] {label}\n    anchor not unique in {path} "
              f"(found {text.count(find)}) -- update this probe")
        continue
    source.write_text(text.replace(find, repl), encoding="utf-8")
    try:
        verdict, failures = run(modules)
    finally:
        restore(path)
    caught = verdict.startswith("FAILED")
    print(f"[{'DEFENDED' if caught else 'UNDEFENDED'}] {label}", flush=True)
    print(f"    reverted in {path};  {' '.join(modules)}", flush=True)
    print(f"    -> {verdict}", flush=True)
    if failures:
        print(f"    -> first failures: {failures[:4]}", flush=True)
