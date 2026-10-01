# Phase 2 — the boundary audit

**What does the hull reach for that is NOT the engine's public answer?**

Measured at `2918631` by `boundary_audit.py`, beside this file. Call sites, not imports: an
import is a declaration, a call is a dependency.

## The headline, and it inverts the assumption

| layer | calls | share |
|---|---|---|
| LLM | 75 | 28.8% |
| hull state | 64 | 24.6% |
| UI | 48 | 18.5% |
| **engine** | **38** | **14.6%** |
| **data** | **21** (+23 instance) | — |
| infra | 14 | 5.4% |
| **total module calls** | **260** | |

**`app.py` reaches the vendor data layer 44 times and the engine 38 times.** The hull talks to
the data layer *more* than to the engine it was built around. Every one of those 44 is something
a non-Streamlit client would have to reproduce, or that the API must answer — which is the
concrete size of the gap between "the snapshot is the contract" and the truth.

The engine boundary itself is genuinely narrow, which is the good news: 10 modules, 38 calls,
dominated by `pick_synthesis` (11) and `player_universe` (9). `build_snapshot` remains the
single most important entry.

**The LLM layer is the largest consumer at 75 calls.** That is independent, measured support for
the roadmap's §3 claim: if the engine only ties a need-aware baseline on pick quality, the
explanation layer is the product — and the hull already spends more of itself on that layer than
on any other.

## The 44 data-layer reaches, classified

### EXPOSE — the API must answer these (13)

The hull is asking the vendor layer a question the engine should own.

| reach | sites | the question |
|---|---|---|
| `merger.merge_player` | 5 | resolve a player onto a vendor record — **three distinct shapes**: a roster row with a position (1761), a Sleeper FA row (4128, 4133), and free text with no position hint at all (4325, 4362) |
| `merger.pick_value` | 4 | a draft pick's trade value from a label (2348, 4355, 4414, 6407) |
| `merger.composite_player_score` | 1 | the trade pad's multi-source valuation (4324) |
| `merger.external_player_values` | 1 | the same pad's per-source breakdown (4323) |
| `merger.build_roster_table` | 1 | a priced view over a roster's ids (3851) |
| `merger.list_free_agents` | 1 | top-N free agents (2258) |

The three `merge_player` shapes matter for the contract: a resolution endpoint that only accepts
`(name, position)` cannot serve the trade pad, which has free text and no position. That is a
contract requirement discovered by measurement rather than by imagining the API.

### MOVE SERVER-SIDE — the client never talks to Sleeper (15)

`SleeperClient` construction, `sync_league` ×2, `get_players` ×2, `get_user`,
`get_user_leagues`, `get_league`, `compute_points_from_stats`, `find_roster_for_user`,
`league_format_summary` ×2, `players_freshness_entry`, `priceable_season_projections`,
`season_projection_freshness_entry`.

These are legitimate — the product must fetch league data — but they belong behind the service
layer, not in a client. They are also where the data-freshness signal originates, which the
roadmap's Phase 4 needs to surface to the user rather than to a log line.

### ADMIN SURFACE — not part of the product's API (13)

Identity curation (`save_alias`, `remove_alias`, `reload` ×2), data upload and freshness
(`load_projection_file`, `external_upload_targets`, `recency_grade`, `horizon_gap_lines`),
source configuration (`composite_capable_source_names`), and league format override
(`get_format_override` ×2, `set_format_override` ×2).

These want their own admin surface with different auth, not endpoints on the product API. Three
`DataMerger` constructions sit alongside them.

## What this changes about the contract

1. **The snapshot is necessary and not sufficient.** `build_snapshot` is the Draft Room's whole
   boundary, but the app has three other surfaces — trade pad, free agents, roster view — whose
   questions the snapshot does not answer. The contract needs those as named operations.
2. **Player resolution needs more than one input shape**, because the trade pad resolves free
   text and the roster view resolves `(name, position)`.
3. **The admin surface is a separate product decision**, and discovering that now is cheaper than
   discovering it when an endpoint list is already published.
4. **The data-freshness signal has a known origin** — three `sleeper_client` freshness calls —
   so Phase 4's "staleness reaches the user" has somewhere concrete to come from.

## What this audit does NOT say

It counts reaches, not necessity. A call site being in the data layer does not prove it is
misplaced — `pick_value` may belong to the engine or may belong to a trade service, and this
audit does not decide that. It says where the hull currently goes, how often, and what a second
client would have to reproduce. The expose/move/admin split above is a first classification to be
argued with, not a ruling.

It also covers `app.py` only. The other UI modules (`draft_board_ui`, `draft_history_ui`,
`trade_ledger_ui`) may have their own reaches; they were out of scope because the hull is where
a client boundary would be drawn.
