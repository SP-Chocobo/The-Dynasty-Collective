"""Is `misquoted_constants`' history shield PARAGRAPH-scoped, like `dead_names`', or still
BLOCK-scoped -- the defect D-F2 repaired in the other checker?

Measures, over the real corpus:
  1. the CHECKABLE population of each half (quotations of a single-homed constant), which the
     tool's own summary line does not print -- it prints 112 constants and 18347 blocks instead;
  2. how many quotations are shielded by a marker that is NOT in their own paragraph. Those are
     the ones a paragraph-scoped shield would examine and a block-scoped one never looks at.
Run from the repo root: PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_prose_names_scope.py
"""
import prose_names as pn

real = pn.numeric_constants()
py = tuple(pn.prose_blocks())
md = tuple(pn.markdown_blocks())

for label, blocks in (("python comments+docstrings", py), ("markdown paragraphs", md)):
    quoted = shielded_block = shielded_para_too = 0
    hidden = []
    for path, line, text in blocks:
        for m in pn.QUOTED_VALUE.finditer(text):
            name = m.group(1) or m.group(3)
            if name not in real:
                continue
            quoted += 1
            block_hist = pn.is_history(text)
            para_hist = pn.is_history(pn._paragraph_around(text, m.start()))
            if block_hist:
                shielded_block += 1
                if para_hist:
                    shielded_para_too += 1
                else:
                    hidden.append((f"{path}:{line}", name, m.group(0).strip()))
    print(f"\n{label}: {len(blocks)} blocks")
    print(f"  quotations of a single-homed constant : {quoted}")
    print(f"  shielded by the BLOCK-wide marker     : {shielded_block}")
    print(f"  ...marker also in the OWN paragraph   : {shielded_para_too}")
    print(f"  ...marker only ELSEWHERE in the block : {len(hidden)}  <-- unexamined by block scope")
    for site, name, form in hidden:
        print(f"      {site:60s} {name:40s} {form}")
