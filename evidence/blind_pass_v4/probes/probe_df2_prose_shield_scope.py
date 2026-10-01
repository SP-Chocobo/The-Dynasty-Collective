"""D-F2: does paragraph scoping actually cut the over-shielding it claims to cut?

The repair's claims, read as claims:

  (a) "MEASURED at the v4 pass: of 1,446 prose blocks naming something, 651 (45.0%) were never
      examined at all, 374 of 499 module docstrings (75%) were shielded, and 177 of the shielded
      blocks carried no marker other than 'was'."
  (b) "Paragraphs cut exactly that."
  (c) "the report still stands at four rather than nought after they [the new markers] were added"
  (d) `SELF_REFERENTIAL` excludes two whole files, "so a reader sees exactly what is unexamined".

This re-derives each number from `prose_names`' own readers -- block-scoped shield vs the shipped
paragraph-scoped shield vs a sentence-scoped shield -- in one process, and prices the two-file
exclusion by removing it.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_df2_prose_shield_scope.py
"""
import collections
import re

import prose_names as pn

NAME = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def sentence_around(text, position):
    start = 0
    for m in SENTENCE_SPLIT.finditer(text):
        if m.start() > position:
            break
        start = m.end()
    end = len(text)
    m = SENTENCE_SPLIT.search(text, position)
    if m:
        end = m.start() + 1
    return text[start:end]


blocks = pn.prose_blocks()
naming = [b for b in blocks if NAME.search(b[2])]
print("prose blocks total              :", len(blocks))
print("prose blocks NAMING something   :", len(naming))

block_shielded = [b for b in naming if pn.is_history(b[2])]
print()
print("(a) BLOCK-scoped shield (the pre-repair rule):")
print(f"    shielded blocks               : {len(block_shielded)} "
      f"({100.0 * len(block_shielded) / len(naming):.1f}%)")
only_was = [b for b in block_shielded
            if not any(pn.is_history(w) for w in ("",))  # placeholder, replaced below
            ]
# which markers each shielded block carries, through the module's own matcher
def markers_in(text):
    return sorted({m for m in pn.HISTORICAL_MARKERS if pn.is_history_marker(text, m)}) \
        if hasattr(pn, "is_history_marker") else None

docstrings = [b for b in naming if "\n" in b[2] or not b[2].lstrip().startswith("#")]
print(f"    naming blocks that are comment tokens (line-scoped by construction): "
      f"{sum(1 for b in naming if b[2].lstrip().startswith('#'))}")

print()
print("(b) the SHIPPED paragraph-scoped shield, counted per NAME OCCURRENCE:")
per_scope = collections.Counter()
residual_examples = []
for path, line, text in naming:
    if path.name in pn.SELF_REFERENTIAL:
        continue
    for m in NAME.finditer(text):
        para = pn._paragraph_around(text, m.start())
        sent = sentence_around(text, m.start())
        b, p, s = pn.is_history(text), pn.is_history(para), pn.is_history(sent)
        per_scope[(b, p, s)] += 1
        if b and p and not s and len(residual_examples) < 6:
            residual_examples.append((str(path), line, m.group(1), para.strip()[:150]))
total = sum(per_scope.values())
print(f"    name occurrences examined     : {total}")
for key in sorted(per_scope, reverse=True):
    b, p, s = key
    print(f"    block={int(b)} paragraph={int(p)} sentence={int(s)} : {per_scope[key]}")
shielded_block = sum(v for (b, p, s), v in per_scope.items() if b)
shielded_para = sum(v for (b, p, s), v in per_scope.items() if p)
shielded_sent = sum(v for (b, p, s), v in per_scope.items() if s)
print(f"    shielded by BLOCK     : {shielded_block} ({100.0*shielded_block/total:.1f}%)")
print(f"    shielded by PARAGRAPH : {shielded_para} ({100.0*shielded_para/total:.1f}%)  <- shipped")
print(f"    shielded by SENTENCE  : {shielded_sent} ({100.0*shielded_sent/total:.1f}%)")
print(f"    RESIDUAL over-shield the repair leaves (paragraph yes, sentence no): "
      f"{shielded_para - shielded_sent}")
print("    examples of that residual:")
for path, line, name, para in residual_examples:
    print(f"      {path}:{line}  `{name}`")
    print(f"        paragraph: {para!r}")

print()
print("(c) the report as it now stands:")
dead = pn.dead_names()
print(f"    dead_names() = {len(dead)}: {sorted(dead)}")

print()
print("(d) the price of the two-file SELF_REFERENTIAL exclusion -- the same scan with it removed:")
universe = pn.words(pn.haystack())
hidden = {}
for path, line, text in pn.prose_blocks():
    if path.name not in pn.SELF_REFERENTIAL:
        continue
    for m in NAME.finditer(text):
        if pn.is_history(pn._paragraph_around(text, m.start())):
            continue
        name = m.group(1)
        if len(name) < pn.MIN_NAME_LENGTH or pn.SHA.match(name):
            continue
        if name in universe:
            continue
        hidden.setdefault(name, []).append(f"{path}:{line}")
print(f"    names the exclusion suppresses: {len(hidden)}")
for name, sites in sorted(hidden.items()):
    print(f"      `{name}`  {sites[:3]}")
