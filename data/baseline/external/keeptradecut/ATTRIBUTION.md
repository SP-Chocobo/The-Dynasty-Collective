Source: KeepTradeCut (keeptradecut.com) Dynasty Rankings -- crowdsourced player/pick values
("from 26,622,552+ data points... provided by users like you," per the page's own header),
Superflex / .5 PPR format, TE Premium off. Pulled by the user as 5 PDF exports of the site's
own paginated view (ranks 1-50, 51-100, 101-150, 151-200, 201-250), captured 2026-08-20 (no
per-row date is printed on the page, just a relative "updated N minutes ago").

KTC's own API is blocked from this environment (confirmed directly: `CONNECT tunnel failed,
403` when this baseline effort tried it for the DynastyProcess/FantasyPros additions) and,
like FantasyPros, sits behind normal site access rather than an open-data license -- same
class of concern already worked through for Draft Sharks/DynastyProcess/FantasyPros earlier
in this effort. Applying that same resolved policy: facts-only extraction (rank/name/asset
type/position/tier/value/trend), never the site's own page/branding, attributed here rather
than re-litigating the question each time a new vendor comes up.

Only the top 250 of KTC's full ~500-entry list is included -- whatever the user actually
pulled, not padded out with unpulled data. dynasty_superflex_halfppr.csv's value column is
KTC's own 0-9999ish crowdsourced market-value scale, not comparable to Draft Sharks' 0-100,
DynastyProcess's ~0-10000 (different formula, different inputs), or FantasyPros' rank/tier --
rides alongside those as its own labeled opinion (see DataMerger.external_player_values),
never blended into any other source's numbers. asset_type separates named players from
rookie/future pick slots on the same list and scale (same shape as Draft Sharks' own Trade
Value Chart, just KTC's crowd instead of Draft Sharks' own model).

Parsing note: KTC's page renders each row's VALUE and RANK back-to-back with no separating
space in a flat text extraction (e.g. "9998" + "1" -> "99981" for the #1 overall asset).
parse_keeptradecut_pdf in data_merger.py splits these using the fact that the list is
strictly rank-ordered -- confirmed exactly against all 250 real rows pulled here, 0 ambiguous
splits -- rather than guessing at a fixed digit count that would break as soon as a value
crossed a digit-count boundary (e.g. 999 -> 1000).
