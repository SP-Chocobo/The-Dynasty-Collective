Source: ESPN (espn.com) Fantasy Football staff rankings -- "Fantasy football draft rankings
2026: Individual defensive players," pulled by the user as a PDF of the live article, dated
2026-08-20 (the PDF's own creation timestamp; the page itself only carries a relative
"published Aug 14, 2026" byline plus rolling news-item timestamps, no single per-row date).
Public ESPN.com content, no login/paywall involved in the pull -- same facts-only-extraction
posture applied to every source in this baseline effort regardless, for consistency.

A SEASON-LONG draft-prep list (no dynasty framing anywhere on the page), same posture as
FantasyPros' own idp_redraft_rankings.csv and best_ball_rankings.csv -- never read as a
dynasty valuation. Ranks are the AVERAGE of three named ESPN analysts (Mike Clay, Tristan H.
Cockcroft, Eric Moody) each ranking the position independently; analyst_avg is that average,
lower is better, same convention as everyone else's "rank" column. injury_flag carries the
page's own Q(uestionable)/O(ut)-type tags where present.

Parsing note: this is a scraped article page, not a clean export -- the PDF interleaves large
blocks of unrelated navigation/ad/related-article text between table rows, and the live page's
own pagination means the column header re-prints every ~4 rows. Worse, the DL/LB/DB section
captions ("2026 Linebacker Rankings") are unreliable as anchors: confirmed on this real file,
they appear buried in the clutter AFTER their own table's last row rather than before its
first, and the Defensive Lineman section's caption never appears at all. parse_espn_idp_pdf
(data_merger.py) sidesteps this entirely -- the three sections always appear in the same fixed
order (DL, then LB, then DB, per the page's own "Top 40 DLs, LBs and DBs" nav text) and each
new section's row 1 resets the shared rank counter back to 1, so position is assigned by
counting resets, never by matching the unreliable caption text.

Kept as its own labeled source (see DataMerger.external_player_values), never blended into any
other source's numbers, and -- being redraft-scope -- deliberately excluded from the dynasty
composite score's inputs (_EXTERNAL_PERCENTILE_RULES in data_merger.py), same treatment as
FantasyPros' two redraft-scope files.
