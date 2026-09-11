# #148 NARROWED: the whole in-repo chain is sign-capable, and it still produced 499 unsigned rows

`term_lifetimes.UNSIGNED_TREND` recorded the cause of the missing sign as a hypothesis, stated
as one because it "cannot be confirmed from here." Half of it can be, and now is. This does not
close #148 — it removes one of the two candidate explanations and removes the repo from
suspicion, which changes where the remedy has to come from.

## What was open

Across all 499 rows of the committed KeepTradeCut export there is not one negative `trend_30d`.
Direction is the entire information content of a trend, so the field is unusable as ingested.
Two things upstream of the CSV could each produce exactly that column:

- **(a)** the instrument drops a `-` that IS present in the page's text, or
- **(b)** no `-` was ever in the page's text.

The record named (b) as most likely and left (a) untested. They have different remedies: (a) is
an in-repo bug, re-parseable today from PDFs the owner still holds; (b) needs a new capture.

## What was measured

**The parser was sign-capable when the data was ingested, not merely today.** `_KTC_ROW_RE`
captures the trend as `(-?\d+)` and `parse_keeptradecut_pdf` converts it with `int()` — no
`abs`, no clamp. `git log -S` finds exactly one commit ever touching that pattern (`32e6991`),
and `git show` confirms the identical regex at **both** commits that produced the committed CSV
(`32e6991`, `98e2df1` — the top-250 original and the top-500 extension). There is no window in
this repo's history in which a sign-blind parser read these PDFs.

**pypdf round-trips the minus.** `ktc_sign_probe.py` hand-assembles a one-page PDF (reportlab
is not installed here, so the content stream is written out in the probe itself and nothing is
taken on trust from a generator), writes three lines including a KTC-shaped row ending in
`-12`, and reads them back through the same `pypdf` version the parser uses:

```
lines written    : ['-12', 'Sample Player WR7 T3 45671 -12', 'Sample Player WR7 T3 45671 12']
lines extracted  : ['-12', 'Sample Player WR7 T3 45671 -12', 'Sample Player WR7 T3 45671 12']
ROUND-TRIPPED    : True
  regex on 'Sample Player WR7 T3 45671 -12' -> trend -12
  regex on 'Sample Player WR7 T3 45671 12'  -> trend +12
```

**Fork (a) is falsified.** The probe's prediction was pre-registered in its own docstring before
running, along with what would have falsified it.

**And no row was silently dropped, either.** This closes the one remaining way the sign could
have gone missing inside the repo. `parse_keeptradecut_pdf` anchors the trend at end-of-line
(`$`) and carries an `expected_rank` that only advances on an accepted row — so a row whose tail
did not match (an arrow glyph where a number belongs, say) would fail the regex, stall the
counter, and cascade every later row into the `blob.endswith(rank_str)` rejection. The committed
CSV holds **499 rows at ranks 1–499, consecutive with no gaps**, and the one absent row (rank
500) is documented in ATTRIBUTION.md for an unrelated digit-splitting ambiguity. Zero rows were
rejected. Every one of the 499 rows ended in a bare integer in the extracted text.

## The column cannot be a genuine signed trend

The record asserts the field is unusable; here is the size of it. Of 499 rows, **471 are
positive, 28 are zero, 0 are negative.** Under any reading where direction survived and the
underlying quantity is even mildly two-sided, all-471-positive is not a sample you get:
`P = 2^-471 ≈ 10^-142` at an even split. For the observed column to be plausible at even a
1-in-20 level, KTC's 30-day market would have to have risen for **at least 99.37%** of assets —
fewer than 3 expected decliners in 471. That is not a market, and it is not a coincidence
either: it is the signature of a magnitude with its direction stripped.

## What this changes

| | before | after |
|---|---|---|
| cause | hypothesis, two candidates, untested | **(b) only — (a) falsified, in two independent ways** |
| repo's parser | not ruled out | **exonerated, by construction and by history** |
| remedy | "a re-scrape that preserves sign" | unchanged — but now the *only* remedy, not the likelier of two |
| classification | KNOWN-OPEN-ACCEPTABLE | unchanged; the blocker is confirmed external |

**#148 stays open and stays blocked.** The advance is that it is now blocked on a measured
finding rather than an untested guess, and nobody needs to re-open the parser to check.

## Guarded against the regression that would matter

The hazard this creates is specific and quiet. `(-?\d+)` → `(\d+)` reads as tidying, breaks no
existing test (no committed fixture carries a negative trend), and would silently discard the
sign on the first re-scrape that finally carries one — turning a repaired input back into the
defect it was repaired for, with no failure anywhere.

`TheTrendSignSurvivesTheParserTests` in `test_parser_integrity.py` pins all three facts: the row
pattern captures a negative, a negative reaches the parsed record as a negative, and the
committed export is all-non-negative **despite** that capability. The third fails the day a
signed re-scrape lands, which is the correct moment to retire this record rather than loosen the
assertion. Mutation-checked 3/3 — dropping the sign group, wrapping the conversion in `abs()`,
and anchoring the tail positive-only are each caught.

## What this does NOT establish

Whether KTC's page renders direction as a coloured arrow glyph, as ATTRIBUTION.md's parsing note
suspects by analogy with the value/rank concatenation it documents. That remains a guess about a
vendor's rendering. What is established is that *whatever* the page does, the character never
reached the extracted text, and nothing in this repo removed it.
