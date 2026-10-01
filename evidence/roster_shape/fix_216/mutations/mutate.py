"""Mutation runner for the #216 tests. One mutation at a time (POST_AUDIT_PLAN #215's rules):
pattern present exactly once before, one backup per target, byte-identical after restore,
full unittest output read (a SyntaxError is not a survivor)."""
import hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT = Path("/home/user/The-Dynasty-Collective/.claude/worktrees/agent-ab5e1af412aeb9182")
OUT = Path(sys.argv[1])
MUTATIONS = [
    {
        "id": "M1_no_deduction_ever",
        "file": "lineup_optimizer.py",
        "old": "    displaced = max(displaced, free)\n",
        "new": "    displaced = free\n",
        "tests": ["test_216_displacement", "test_216_value_board_falsification.B_FeedbackDirectionTests",
                  "test_216_value_board_falsification.C_MagnitudeTests", "test_216_value_board_falsification.D_SamePointsPairTests"],
    },
    {
        "id": "M2_term_dropped_from_the_sum",
        "file": "draft_room.py",
        "old": "            universal_value + need_bonus + eligibility_bonus_value + depth_exposure_value\n            + displacement_adj, 2)",
        "new": "            universal_value + need_bonus + eligibility_bonus_value + depth_exposure_value, 2)",
        "tests": ["test_216_displacement", "test_216_room_integrity.TheRealBoardStillRunsTests",
                  "test_depth_exposure.WiredIntoTeamAcquisitionValueTests",
                  "test_216_value_board_falsification.D_SamePointsPairTests"],
    },
    {
        "id": "M3_adjustments_never_computed",
        "file": "draft_room.py",
        "old": "    out: dict[str, dict] = {}\n    for position, level in levels.items():\n        if level is None or pd.isna(level):\n            continue\n",
        "new": "    out: dict[str, dict] = {}\n    for position, level in []:\n        if level is None or pd.isna(level):\n            continue\n",
        "tests": ["test_216_displacement", "test_216_room_integrity.TheRealBoardStillRunsTests",
                  "test_216_value_board_falsification.C_MagnitudeTests"],
    },
    {
        "id": "M4_multi_eligible_takes_the_worst_position",
        "file": "draft_room.py",
        "old": "                        _my_points_players, roster_positions, eligible | {position},\n",
        "new": "                        _my_points_players, roster_positions, {position},\n",
        "tests": ["test_draft_room.EligibilityBonusWiringTests"],
    },
    {
        "id": "M5_sign_flipped",
        "file": "lineup_optimizer.py",
        "old": "    return {\"displaced\": displaced, \"adjustment\": round(free - displaced, 2), \"basis\": basis}",
        "new": "    return {\"displaced\": displaced, \"adjustment\": round(displaced - free, 2), \"basis\": basis}",
        "tests": ["test_216_displacement", "test_216_value_board_falsification.B_FeedbackDirectionTests"],
    },
    {
        "id": "M6_partial_basis_never_stamped",
        "file": "lineup_optimizer.py",
        "old": "        if set(eligible) & reachable_eligible:\n            basis = DISPLACEMENT_ROSTER_PARTIAL\n",
        "new": "        if False:\n            basis = DISPLACEMENT_ROSTER_PARTIAL\n",
        "tests": ["test_216_displacement.DisplacementLevelDerivationTests"],
    },
    {
        "id": "M7_room_sentence_dropped",
        "file": "draft_board_ui.py",
        "old": "  if (num(c.displacementAdj) && c.displacementAdj < 0) {\n    s.push(",
        "new": "  if (false) {\n    s.push(",
        "tests": ["test_216_room_integrity.EveryTermOfTheIdentityReachesTheRoomTests"],
    },
    {
        "id": "M8_a_literal_constant_in_the_value_path",
        "file": "draft_room.py",
        "old": "        out[position] = lo.displacement_level(\n            roster_players, roster_positions, position, float(level), unpriced_eligible,\n        )",
        "new": "        out[position] = lo.displacement_level(\n            roster_players, roster_positions, position, float(level) * 1.5, unpriced_eligible,\n        )",
        "tests": ["test_216_displacement.NoConstantInTheValuePathTests"],
    },
    {
        "id": "M9_term_not_serialized_to_the_room",
        "file": "draft_board_ui.py",
        "old": "        \"displacementAdj\": c.displacement_adj,\n",
        "new": "        \"displacementAdj\": None,\n",
        "tests": ["test_216_room_integrity.EveryTermOfTheIdentityReachesTheRoomTests"],
    },
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


results = []
for m in MUTATIONS:
    target = ROOT / m["file"]
    original = target.read_bytes()
    text = original.decode("utf-8")
    count = text.count(m["old"])
    if count != 1:
        results.append({"id": m["id"], "status": f"PATTERN_COUNT_{count}_NOT_APPLIED"})
        print(results[-1], flush=True)
        continue
    backup = OUT / (m["file"] + ".bak")
    backup.write_bytes(original)
    target.write_text(text.replace(m["old"], m["new"]), encoding="utf-8")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest"] + m["tests"], cwd=ROOT, capture_output=True, text=True,
            env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin:/usr/local/bin"}, timeout=1500)
        tail = proc.stderr[-4000:]
    finally:
        target.write_bytes(original)
    restored = sha(target) == hashlib.sha256(original).hexdigest()
    ran = next((l for l in tail.splitlines() if l.startswith("Ran ")), "")
    verdict = next((l for l in tail.splitlines() if l.startswith(("OK", "FAILED"))), "")
    syntax = "SyntaxError" in tail or "ImportError" in tail
    status = "SYNTAX_ERROR_NOT_TESTED" if syntax else ("KILLED" if verdict.startswith("FAILED") else "SURVIVED")
    failing = sorted({l.split(" ")[1] for l in tail.splitlines() if l.startswith(("FAIL:", "ERROR:"))})
    results.append({"id": m["id"], "status": status, "ran": ran, "verdict": verdict, "restored_byte_identical": restored,
                    "failing_tests": failing, "seconds": round(time.time() - t0, 1)})
    print(results[-1], flush=True)
    (OUT / "mutations.json").write_text(json.dumps(results, indent=1))
    (OUT / f"{m['id']}.txt").write_text(tail)
print("done")
