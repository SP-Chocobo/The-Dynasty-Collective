"""The invariant_confirmation preflight, after the "BOTH BRANCHES" repair.

Two claims to test:

  (1) the fixture now exercises BOTH board branches. It loops `for mode in ("auto", "upside")`
      and the guard labels the pair ("balanced", "upside"). The upside arm is FORCED; the
      balanced arm is only ASSUMED -- `mode="auto"` resolves to upside whenever no priced row
      carries a positive `_vor`, so whether the first arm is the balanced branch is a property
      of the fixture, not of the call. This runs the module's OWN fixture script verbatim with
      one extra line that prints each board's emitted `mode`.

  (2) the guard reads `zip(("balanced", "upside"), boards)` with no check that there are two
      boards. If the fixture ever prints one again, zip truncates and the upside pair is skipped
      in silence -- the "three of four" shape the repair's own comment warns about.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_invariant_fixture_branches.py
"""
import subprocess
import sys

import invariant_confirmation as ic

# (1) the module's own fixture, verbatim, with the emitted `mode` added to what it prints.
script = ic._FINGERPRINT_SCRIPT.replace(
    'fields.append(f"{digest} {feas} {len(board)} {unfield}")',
    'fields.append(f"{digest} {feas} {len(board)} {unfield}")\n'
    '    print("ARG mode=", mode, " EMITTED mode=", board[0].get("mode"),'
    ' " priced=", sum(1 for r in board if r.get("final_score") is not None),'
    ' file=__import__("sys").stderr)')
assert script != ic._FINGERPRINT_SCRIPT, "the fixture's print line moved; update this probe"
out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                     env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin:/usr/local/bin"})
print("--- the fixture's own stderr (arg mode vs EMITTED mode) ---")
print(out.stderr.strip() or f"(no stderr; rc={out.returncode})")
if out.returncode:
    print("fixture rc:", out.returncode)
print("--- the fingerprint line ---")
print(out.stdout.strip()[:200])
fields = out.stdout.split()
print("fields:", len(fields), " -> boards:", len(fields) // 4)

# (2) the truncation, demonstrated on the guard's own expression.
print()
print("--- the guard's pairing, with a ONE-board fingerprint line ---")
for n_boards in (2, 1):
    parts = ["d", "5", "100", "7"] * n_boards
    boards = [parts[i:i + 4] for i in range(0, len(parts), 4)]
    checked = [b for b, _ in zip(("balanced", "upside"), boards)]
    print(f"   fingerprint carries {n_boards} board(s) -> guard checks {checked}"
          f"   {'both' if len(checked) == 2 else 'UPSIDE PAIR SILENTLY SKIPPED'}")
