"""One mutation at a time. Backup named after its target; pattern verified present BEFORE;
file compared byte-for-byte AFTER. Patterns come from JSON, never a shell heredoc (#215)."""
import hashlib, json, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path("/home/user/The-Dynasty-Collective/.claude/worktrees/agent-ab5e1af412aeb9182")
HERE = pathlib.Path(__file__).parent
MUTS = json.loads((HERE / "mutations.json").read_text())
TESTS = sys.argv[2] if len(sys.argv) > 2 else "test_216_value_board_falsification.E_OverCorrectionGuards"
name = sys.argv[1]
spec = MUTS[name]
target = ROOT / spec["target"]
backup = HERE / f"backup__{spec['target']}"

original = target.read_text()
before = hashlib.sha256(original.encode()).hexdigest()
if spec["find"] not in original:
    print(f"ABORT {name}: pattern NOT PRESENT in {spec['target']}"); sys.exit(2)
shutil.copy2(target, backup)
try:
    target.write_text(original.replace(spec["find"], spec["replace"], 1))
    assert target.read_text() != original, "mutation did not change the file"
    r = subprocess.run([sys.executable, "-m", "unittest", TESTS, "-v"],
                       cwd=ROOT, capture_output=True, text=True, env={"PYTHONPATH": ".", "PATH": "/usr/bin:/bin"})
    print(f"=== {name}: {spec['why']}")
    print(r.stdout[-400:])
    print(r.stderr[-6000:])
    print(f"=== exit {r.returncode}  -> {'CAUGHT' if r.returncode else 'SURVIVED'}")
finally:
    shutil.copy2(backup, target)
    after = hashlib.sha256(target.read_text().encode()).hexdigest()
    print(f"restore byte-identical: {before == after}")
