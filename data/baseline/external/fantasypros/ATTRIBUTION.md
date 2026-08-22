Source: FantasyPros (fantasypros.com) Expert Consensus Rankings (ECR) -- pulled by the user as
PDF exports ("2026 Dynasty Fantasy Football Rankings (Keepers)" and "2026 Overall Best Ball
Rankings"), both dated 2026-08-20 (the PDFs' own creation timestamp; FantasyPros doesn't print
a per-row date on the page itself). FantasyPros does have an API, but it sits behind a login
and possibly a paywall tier -- the user flagged this proactively, same class of concern already
worked through for Draft Sharks earlier in this baseline effort (see the sibling dynastyprocess/
ATTRIBUTION.md and this repo's commit history for that discussion). Applying the same resolved
policy here rather than re-litigating it: facts-only extraction (name/team/position/rank/tier
and each file's own extra columns), never the vendor's own PDF or page layout/branding,
committed with clear attribution -- not a re-verified ToS conclusion, just consistent treatment
of the same situation.

Three files, three different products, kept in three separate CSVs and never merged with each
other or with dynastyprocess's/keeptradecut's/espn's data:

- dynasty_ppr_rankings.csv -- "Dynasty Fantasy Football Rankings (Keepers)," a 12-team PPR
  dynasty ECR: rank/tier plus the expert panel's best/worst/avg/std_dev spread behind each
  player's consensus rank.
- best_ball_rankings.csv -- "Overall Best Ball Rankings," a SEASON-LONG (not dynasty) redraft-
  style list with bye_week instead of the dynasty spread columns. Kept firmly separate from the
  dynasty file for the same reason the app already treats Redraft-vs-Dynasty as a real failure
  mode elsewhere (see app.py's upload handler) -- a single-season list has no business being
  read as a dynasty valuation.
- idp_redraft_rankings.csv -- "Individual Defensive Player Fantasy Football Rankings, IDP
  Cheat Sheets, Draft Rankings" -- also SEASON-LONG (its own header says "SOS SEASON ECR," no
  dynasty framing anywhere), same firm separation as best_ball_rankings.csv. Draft Sharks is
  this app's only DYNASTY IDP source; this rides alongside it purely as a second, redraft-scope
  opinion for the bots to weigh, not a dynasty valuation. Position codes here are more granular
  than Draft Sharks' three broad IDP buckets (DE/DT split out from DL, S/CB split out from DB)
  -- kept as-is rather than collapsed, since the extra detail is real information.

Neither file carries a Draft-Sharks-scale trade_value or a DynastyProcess-scale value_1qb --
FantasyPros' own numbers are rank/tier/ECR-shaped, not a comparable point value, so this source
rides alongside the others as its own labeled opinion (see DataMerger.external_player_values),
never blended into any other source's numbers.
