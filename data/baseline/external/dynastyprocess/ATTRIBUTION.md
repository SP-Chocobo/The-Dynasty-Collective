Source: [dynastyprocess/data](https://github.com/dynastyprocess/data), an open-data repository
maintained by DynastyProcess.com (Tan Ho and Joe Sydlowski), licensed GPL-3.0. Pulled directly
from `files/values-players.csv` and `files/values-picks.csv` via GitHub's raw content host — a
public, unauthenticated, no-login endpoint the repository itself describes as "open-data,"
unlike Draft Sharks' subscription exports, which is why this lives in git as-is rather than as
a facts-only extraction.

`value_1qb`/`value_2qb` are DynastyProcess's own transform of FantasyPros' Expert Consensus
Rankings (a 12-team PPR dynasty ECR), not a re-hosting of FantasyPros' own numbers: roughly
`10500 * e^(ECR * -0.0235)`, with position-specific variants, and a LOESS-regression-fitted
1QB-to-2QB conversion in place of a smaller 2QB-specific sample. See
https://dynastyprocess.com/values/ for the full methodology. This is a genuinely independent
valuation (different inputs, different math) from Draft Sharks' proprietary "3D Value" --
that's the point of carrying it as its own labeled pool rather than blending it into
Draft Sharks' trade_value column.

players.csv / picks.csv here are trimmed to the columns this app actually uses (name, position,
team, ecr_1qb, ecr_2qb, value_1qb, value_2qb / name, ecr_1qb, ecr_2qb) plus source_date, which
is DynastyProcess's own scrape_date, not the date this copy was pulled into this repo.
Pulled into this repo: 2026-08-20.
