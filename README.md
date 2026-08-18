# Fantasy Football Multi-LLM Command Center

A local "front office" for dynasty fantasy football: it syncs your Sleeper
league automatically, merges in your paid Draft Sharks projections from
files on your own disk, and runs roster questions through a four-model
debate panel — grounded in Draft Sharks' math, the wider public market, and
live news — before handing you one clear verdict.

## The Front Office

| Persona | Model | Job |
|---|---|---|
| **Quant / VORP Specialist** | Claude (Anthropic) | Math only — VORP, positional scarcity, roster construction, trade equity, using your league's real scoring settings, your local Draft Sharks data, and Sleeper's own native weekly stat-category projections. Neither numeric source is the final word. |
| **Beat / News Tracker** | Gemini (Google, search-grounded) | Cross-references Draft Sharks against public market consensus (KeepTradeCut, FantasyCalc, FantasyPros, ESPN, etc.), plus live news, injuries, and depth charts. |
| **Contrarian / Risk Analyst** | ChatGPT (OpenAI, web-search-enabled) | Pressure-tests the other two — regression risk, small-sample overreaction, model blind spots, age curves, and Draft-Sharks-vs-market divergence. |
| **Debate Moderator** | Claude (Anthropic) | Synthesizes all three into one actionable verdict, calling out where Draft Sharks, the market, and the news disagree. |

Draft Sharks is deliberately treated as **one input among several**, not
ground truth — the Beat Tracker and Contrarian are explicitly instructed to
weigh it against the broader market and against live news rather than just
restate it.

## Design Principles

- **Zero manual credential exposure for league data.** Sleeper's read API
  (`https://api.sleeper.app/v1/`) needs no API key — just your username.
- **Local data sovereignty.** Draft Sharks exports never leave your machine
  or hit a vendor API — you export/save them yourself and upload them here,
  keeping you compliant with Draft Sharks' terms of service. (Market
  consensus sites like KTC/FantasyCalc/FantasyPros are looked up live by the
  Beat Tracker via ordinary web search, since that data is public.)
- **Persisted league threads.** Every league gets its own chat memory at
  `data/chats/<league_id>_history.json`, independent of every other league.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in ANTHROPIC_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY as you have them —
# the app degrades gracefully and tells you in the sidebar which personas are live

streamlit run app.py
```

You only need the keys for the models you want to use. Sleeper sync and the
roster dashboard work with zero keys configured.

## Using it

1. **Sidebar → Sleeper Sync**: enter your Sleeper username, click **Sync
   Leagues**. All leagues you're in for the current season are discovered
   automatically; pick one from the dropdown. Click **Refresh This League**
   any time to re-pull rosters/scoring/taxi/traded picks — a timestamped
   snapshot is cached in `data/sleeper_snapshots/` so the dashboard still has
   data even if Sleeper is briefly unreachable.
   Use **Manage Leagues** below the dropdown to **Archive** leagues you don't
   want cluttering the front dashboard (dead leagues, leagues you left) and
   to reorder the rest with the ▲/▼ buttons — this is saved per Sleeper user
   in `data/league_prefs.json` and persists across sessions. Archived
   leagues stay listed there so you can unarchive them later; a newly
   discovered league is appended to the end rather than disrupting your
   saved order.
2. **Sidebar → Draft Sharks / War Room Data**: one upload box, auto-routed
   by what the file actually is — the kind is sniffed from the PDF's own
   content, not its filename or which league happens to be selected:
   - **Dynasty Rankings** — a season/multi-year overall ranking (1yr proj,
     3yr proj, 3D Value), computed from *format* assumptions (PPR/standard,
     superflex/1QB, TE premium), not from any specific roster. The same
     export is correct for every league sharing that format, so it goes
     into a **shared pool** (`data/projections/_global/`) and is available
     to every league automatically — no re-uploading per league, no
     cross-league copying to reason about.
   - **Free Agent Finder** — a rest-of-season, this-league-contextual view
     (3D Proj, 3D ROS, Ceiling, 3D Value+) that also tags each player Mine
     (already on your roster), Add/Drop (Draft Sharks' own suggested waiver
     move), or blank (an ordinary free agent). This genuinely can't be
     shared — it reflects one league's actual roster — so it's stored under
     `data/projections/<league_id>/` and only ever applies to the league
     selected when you upload it. Supports K/DEF and IDP (LB/DL/DB)
     leagues, not just standard offensive skill positions.
   - **League Analyzer** (team-vs-team power rankings/standings) is also
     league-specific but isn't parsed yet — uploading one shows a clear
     error rather than being silently mis-read by the rankings parser.
   Even a same-format shared ranking won't perfectly match every league's
   exact rules, so this league's **full, real Sleeper scoring settings**
   (every non-zero stat-category weight, not just a PPR/superflex label)
   are always given to the Quant too — see "Scoring-aware tier adjustment"
   below. CSV/JSON exports from other vendors also work via the normal
   column-alias path, and are treated as format-based (shared pool) like
   Dynasty Rankings.
3. **Main dashboard**: your roster (starters, bench, taxi, IR) with merged
   rank/VORP/projection/3D-value columns (plus rest-of-season/ceiling/value
   from the Free Agent Finder export, when loaded), a staleness banner if
   the loaded projections are getting old (see below), and a full-width
   **Free Agents** panel below it — filterable by position, sorted by 3D
   Value+, with your own roster excluded by default (toggle to include it).
   If any roster players didn't auto-match to your loaded Draft Sharks data,
   an **Unmatched Players** expander shows up under the match-rate line —
   pick the player, type the exact name Draft Sharks printed for them, and
   save; that mapping is remembered in `data/player_aliases.json` and
   overrides automatic matching for that player from then on. Automatic
   matching mostly works, but an unusual name shape, a mid-season team
   change, or WR/RB dual eligibility can occasionally slip through it.
   Below that, a full-width **Reference Material** panel holds anything
   uploaded that *isn't* recognized Draft Sharks data — a screenshot of an
   injury notification, an article, a tweet — instead of the upload just
   silently discarding it. Give each one a short caption; the caption text
   (not the raw file) is what actually reaches the debate panel, labeled
   explicitly as an unverified claim to weigh, not fact. The same upload box
   used for Draft Sharks data handles this automatically: anything that
   doesn't parse as Dynasty Rankings or Free Agent Finder falls through to
   here rather than erroring out.
4. **Debate Studio**: type a question and either click a quick-action button
   or prefix your message:
   - `/debate <question>` — full four-agent panel (default if no prefix)
   - `/claude <question>` — Quant only
   - `/gemini <question>` — Beat Tracker only
   - `/gpt <question>` — Contrarian only
   When Free Agent Finder data is loaded, the top 15 available free agents
   (by 3D Value+) are included in the debate context automatically, so
   waiver/pickup questions have real data to reason from.
   The panel also has real memory now: your last ~16 messages (plus any
   compacted summary — see below) are fed back into every debate's context,
   so a later question can reference earlier trade discussions, consensus
   verdicts, and roster strategy instead of starting fresh each time.

### Scoring-aware tier adjustment

A Draft Sharks tier list is computed under Draft Sharks' own scoring
assumptions, which will often sit somewhere *between* what two different
list flavors assume for your actual league — a partial-PPR league between
a full-PPR and a standard list, a modest TE bonus that only partly closes
the gap a full TE-premium list would show, and so on. Rather than treating
a loaded tier/value number as exact, the Quant is given this league's
complete real scoring settings and instructed to use judgment: nudge a
player's implied value up or down when the specific weights point that
way, and say so explicitly rather than silently overriding the number.

### Chat history compaction

Long-running leagues build up a lot of chat history. **🧹 Compact History**
(next to Clear Chat History, once there's something to compact) distills
everything older than a chosen age (30 days by default) into one dense
memory block — targeted players, trade/waiver consensus reached, long-term
roster strategy — via a dedicated Claude call, then prunes the raw old
messages, keeping recent turns untouched. It's safe by construction: the
file is never overwritten unless the summarization call actually succeeds
(a failure leaves your history exactly as it was), a timestamped backup of
the pre-compaction file is written first regardless, and a prior summary is
merged forward on repeated compactions rather than overwritten, so older
context doesn't quietly disappear over multiple runs.

### Data freshness — you don't need to re-sync every session

Draft Sharks updates aren't needed every time you open the app — the
sidebar and dashboard track the date embedded in the loaded PDF (or the
file's save date for CSV/JSON) and only nudge you to refresh once it's **7+
days old**. Roughly a weekly re-export is plenty; the app won't pester you
in between.

Every debate also gets an explicit **DATA FRESHNESS** manifest in its
context — an as-of date and age for Draft Sharks Dynasty Rankings, Draft
Sharks Free Agent Finder, and the Sleeper league sync, sorted freshest
first (the Beat Tracker's and Contrarian's own live web search is always
treated as fresher than any of those, since it runs at the moment of the
question). When two sources disagree, the panel is instructed to lean
toward the more recently updated one — decisively for time-sensitive
claims like injury status or depth chart position, only mildly for stable
long-term dynasty valuations, since staleness doesn't invalidate a
season-long projection the way it invalidates "is this guy still the
starter." The Moderator treats this as its primary tie-breaker and is told
to say explicitly when it's using it, so a verdict reads as "X is more
current" rather than an unexplained "X is more correct."

## Project layout

```
sleeper_client.py   Sleeper API wrapper: league discovery, rosters, scoring,
                     taxi, traded picks, cached player DB, snapshot caching.
data_merger.py       Draft Sharks PDF parsers (Dynasty Rankings + Free Agent
                     Finder, auto-detected) + CSV/JSON projection parser,
                     name/team/position matching onto Sleeper players, and
                     projection-freshness tracking.
league_prefs.py       Per-Sleeper-user league archive/reorder preferences.
attachments.py         Reference material (screenshots/articles) that isn't
                        structured Draft Sharks data — storage + captions.
llm_engine.py         Four-persona prompt routing across Claude / Gemini / ChatGPT.
app.py                 Streamlit dashboard + debate studio.
data/sleeper_snapshots/  Cached league syncs (gitignored).
data/projections/_global/   Dynasty Rankings / format-based exports, shared by
                             every league (gitignored).
data/projections/<league_id>/  Free Agent Finder exports, one folder per league,
                                never shared (gitignored).
data/attachments/           Reference material + captions.json (gitignored).
data/chats/                 Per-league persisted debate history (gitignored).
data/league_prefs.json      Archived/reordered league ids per user (gitignored).
data/player_aliases.json    Manual name-matching overrides (gitignored).
```

## Notes

- **Sleeper's own native projections**: alongside Draft Sharks, every league
  sync also pulls Sleeper's own per-stat-category weekly projection for each
  player (pass yards, receptions, rush TDs, etc.) and scores it under your
  league's *actual* `scoring_settings` — the same math Sleeper's own apps use
  to show a "proj" points column. This shows up as `sleeper_proj` in the
  roster table and in the debate context, as a second, independent
  quantitative source to weigh against Draft Sharks. **Caveat**: unlike the
  league/roster/user endpoints this project otherwise uses, that projections
  endpoint isn't part of Sleeper's *documented* public API — it's
  reverse-engineered from what Sleeper's own clients call internally, and
  could change shape or disappear without notice. Every call to it fails
  soft (the sidebar just shows "Sleeper Native Projections ❌" and everything
  else keeps working) — if it stops matching reality, tell me what broke and
  I'll fix the parsing. It's also a **single week's** number, not a season or
  multi-year total like Draft Sharks' — the Quant prompt is told this
  explicitly so it doesn't compare the two at face value.
- **Draft Sharks PDF format**: their rankings page prints as a two-column
  PDF (a numbers column, then a names column) that scrambles naive
  text-extraction order. `data_merger.py` reconstructs each row on a
  per-page basis rather than assuming the whole document reads top to
  bottom, and disambiguates Draft Sharks' first-initial-only names (e.g.
  "J Chase") against Sleeper's full names using team + position, since
  whole-string fuzzy matching alone under- and over-matches on that
  abbreviation. If Draft Sharks changes their page layout, this parser may
  need updating — send me a fresh export if matching quality drops.
- **Draft Sharks Free Agent Finder**: a structurally different export from
  Dynasty Rankings — different columns (3D Proj / 3D ROS / Ceiling / 3D
  Value+ instead of 1yr/3yr proj), different "rank" semantics (this-league
  contextual, not a pure dynasty overall rank), and a `Mine`/`Add`/`Drop`/
  `Lock` status tag Draft Sharks assigns per player. It's kept as its own
  table (`DataMerger.free_agents`) rather than merged into the rankings
  table, so the two don't clobber each other's meaning of "rank" or
  "value" — both get cross-matched onto your roster independently, and the
  Free Agents panel/context only ever reads from the free-agent table.
  IDP (LB/DL/DB) and K/DEF are supported since some leagues score them, but
  are only lightly tested against one real export — flag it if a position
  or team code doesn't parse right.
- Only keep **one** Dynasty Rankings flavor in the shared pool
  (`data/projections/_global/`) at a time — if your leagues are dynasty
  superflex PPR, load that flavor, not a generic one. Since the pool is
  shared across every league, mixing multiple ranking flavors there will
  give inconsistent values for the same players in whichever league you
  look at. (This doesn't apply to the Free Agent Finder export, which is
  already specific to your one league and stored separately.)
- Default models (`claude-3-5-sonnet-20241022`, `gemini-2.0-flash`, `gpt-4o`)
  are set in `.env.example` and overridable via `ANTHROPIC_MODEL` /
  `GEMINI_MODEL` / `OPENAI_MODEL` — point them at newer model releases as
  they become available.
- Sleeper's `/players/nfl` endpoint is large and rate-limit sensitive, so it's
  cached locally for 24 hours before being re-pulled.
