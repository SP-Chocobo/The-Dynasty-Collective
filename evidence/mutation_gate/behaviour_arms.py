"""Three mutation arms for the three BEHAVIOUR-changing repairs of the hardening pass.

WHY THIS IS NOT AN ARM OF `invariant_confirmation` (which is the v4 gate). That harness decides
whether a mutation is INERT by comparing a BOARD fingerprint, and its docstring says so
deliberately: comparing whole boards needs no per-mutation knowledge, so a later arm inherits the
guard. That design is right for board invariants and cannot judge these three:

  * the `team_count` coercion is unreachable whenever `total_rosters` is present, which every
    board fixture has, so no board moves;
  * the eligibility row the empty-answer repair governs is filtered out of the pool before any
    board is built (0 of 6,594);
  * the snapshot default is on the debate boundary and touches no board at all.

All three would read `MUTATION IS INERT`, which is in that harness's `INCONCLUSIVE` set, so the
gate would exit 2 -- passing nothing while looking rigorous. Each arm here therefore carries its
OWN witness, which is the bespoke cost `#126` warns about and is unavoidable: a non-board
invariant cannot be witnessed by a board.

WHAT EACH ARM PROVES, in order, and it needs all three to mean anything:
  1. ANCHOR APPLIED -- the mutation landed at the expected number of sites.
  2. WITNESSED -- the mutated code actually answers the governed question differently. Without
     this, a `caught` verdict can come from a mutation that changed nothing (`#245`).
  3. CAUGHT -- the named test module fails. Scope stated honestly: this runs the DESIGNATED
     module, not the full suite, so the claim is "a named test defends this repair", not "no other
     test depends on it". The full suite is run separately against the same tree.
"""
import ast
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path("/home/user/The-Dynasty-Collective")

#: (name, file, anchor, replacement, witness, module that must catch it, what breaking it means)
#: The witness is a snippet printing exactly one line: REPAIRED or DEFECTIVE.
ARMS = [
    ("team_count's picks rule stops coercing roster_id",
     "league_config.py",
     'drafting = {str(p.get("roster_id")) for p in picks if p.get("roster_id") is not None}',
     'drafting = {p.get("roster_id") for p in picks if p.get("roster_id") is not None}',
     'import league_config as lc\n'
     'picks = [{"player_id": "1", "roster_id": 0}, {"player_id": "2", "roster_id": "0"}]\n'
     'print("REPAIRED" if lc.team_count(picks=picks) == 1 else "DEFECTIVE")\n',
     "test_one_league_one_team_count",
     "roster_id 0 and \"0\" become two teams to the count and one roster to the census -- the "
     "#126 split B-F6 claims to have closed, one rule inward"),

    ("the composed eligibility rule falls back on the empty ANSWER again",
     "player_universe.py",
     'return frozenset(player_eligible_positions(info))',
     'return frozenset(player_eligible_positions(info) or ({position} if position else ()))',
     'import player_universe as pu\n'
     'db = {"1269": {"first_name": "Bradley", "last_name": "Sowell",\n'
     '               "position": "TE", "fantasy_positions": ["OL"]}}\n'
     'print("REPAIRED" if pu.eligible_positions_for("1269", "TE", db) == frozenset()\n'
     '      else "DEFECTIVE")\n',
     "test_one_eligibility_reader",
     "a man the feed says starts NOWHERE is handed the raw `position` back, which is the field "
     "#172 says not to trust -- and the board's feasibility backstop then promotes him for a "
     "hole he cannot fill"),

    ("the snapshot's eligibility default goes back to an empty set",
     "pick_synthesis.py",
     'eligible_positions: Optional[frozenset] = None',
     'eligible_positions: Optional[frozenset] = frozenset()',
     'import dataclasses, pick_synthesis as ps\n'
     'd = {f.name: f.default for f in dataclasses.fields(ps.CandidateSnapshot)}\n'
     'print("REPAIRED" if d["eligible_positions"] is None else "DEFECTIVE")\n',
     "test_one_eligibility_vocabulary_everywhere",
     "absence becomes indistinguishable from \"startable nowhere\" on the debate boundary, so "
     "the view filter has to resurrect the raw `position` for both"),
]

ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".", "PATH": "/usr/bin:/bin"}


def run(args, timeout):
    return subprocess.run(args, capture_output=True, text=True, cwd=ROOT, env=ENV,
                          timeout=timeout)


def witness(snippet: str) -> str:
    proc = run([sys.executable, "-c", snippet], 120)
    if proc.returncode != 0:
        return f"WITNESS CRASHED: {(proc.stdout + proc.stderr)[-300:]}"
    lines = [l for l in proc.stdout.strip().splitlines() if l in ("REPAIRED", "DEFECTIVE")]
    return lines[-1] if lines else f"WITNESS SAID NOTHING: {proc.stdout[-200:]!r}"


def apply_mutation(source: str, anchor: str, replacement: str) -> tuple[str, int]:
    """Line-wise at each site's own indentation -- the same rule the board harness uses, so an
    anchor written unindented in the table above cannot land at the wrong block level."""
    out, sites = [], 0
    for line in source.splitlines(keepends=True):
        if anchor in line:
            sites += 1
            indent = line[:len(line) - len(line.lstrip())]
            out.append(line.replace(anchor, replacement))
            assert out[-1].startswith(indent)
        else:
            out.append(line)
    return "".join(out), sites


def main() -> int:
    verdicts = []
    print("=== PRECONDITION: every witness must read REPAIRED on the CLEAN tree ===")
    print("    Without this a 'caught' verdict could come from a witness that is simply wrong.")
    clean_ok = True
    for name, _f, _a, _r, wit, _m, _why in ARMS:
        said = witness(wit)
        print(f"  {said:12s}  {name}")
        if said != "REPAIRED":
            clean_ok = False
    if not clean_ok:
        print("\nPRECONDITION FAILED -- the harness is not measuring what it claims.")
        return 2
    print()

    for name, filename, anchor, replacement, wit, module, why in ARMS:
        path = ROOT / filename
        backup = path.read_text(encoding="utf-8")
        mutated, sites = apply_mutation(backup, anchor, replacement)
        print(f"--- ARM: {name}")
        print(f"    file={filename}  sites={sites}  catches-with={module}")
        print(f"    breaking it means: {why}")
        if sites != 1:
            verdicts.append((name, "ANCHOR FAILED", f"{sites} sites, expected 1"))
            print(f"    VERDICT: ANCHOR FAILED ({sites} sites)\n")
            continue
        try:
            ast.parse(mutated)
        except SyntaxError as exc:
            verdicts.append((name, "MUTANT DOES NOT PARSE", str(exc)))
            print(f"    VERDICT: MUTANT DOES NOT PARSE\n")
            continue
        try:
            path.write_text(mutated, encoding="utf-8")
            said = witness(wit)
            if said != "DEFECTIVE":
                verdicts.append((name, "MUTATION IS INERT", said))
                print(f"    witness: {said}")
                print(f"    VERDICT: MUTATION IS INERT -- nothing to catch\n")
                continue
            print(f"    witness: DEFECTIVE (the mutation changed the governed answer)")
            proc = run([sys.executable, "-m", "unittest", module], 1800)
            caught = proc.returncode != 0
            tail = [l for l in (proc.stdout + proc.stderr).splitlines()
                    if l.startswith(("FAIL:", "ERROR:"))]
            verdicts.append((name, "caught" if caught else "*** SURVIVED ***",
                             "; ".join(tail[:3]) or "(no FAIL/ERROR lines)"))
            print(f"    VERDICT: {'caught' if caught else '*** SURVIVED ***'}")
            for t in tail[:4]:
                print(f"      {t}")
            print()
        finally:
            path.write_text(backup, encoding="utf-8")

    print("=== SUMMARY ===")
    for name, verdict, detail in verdicts:
        print(f"  {verdict:20s} {name}")
        if detail:
            print(f"      {detail[:160]}")
    inconclusive = [v for _n, v, _d in verdicts
                    if v in ("ANCHOR FAILED", "MUTANT DOES NOT PARSE", "MUTATION IS INERT")]
    survived = [v for _n, v, _d in verdicts if v == "*** SURVIVED ***"]
    print(f"\n{len(verdicts)} arms: {sum(1 for _n,v,_d in verdicts if v == 'caught')} caught, "
          f"{len(survived)} survived, {len(inconclusive)} inconclusive")
    if survived or inconclusive or len(verdicts) != len(ARMS):
        return 1
    print("ALL THREE BEHAVIOUR REPAIRS ARE DEFENDED BY A NAMED TEST.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
