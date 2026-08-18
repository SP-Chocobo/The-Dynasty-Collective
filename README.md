# Fantasy Football Multi-LLM Command Center

A local "front office" for fantasy football — dynasty first, but redraft,
keeper, Best Ball, and Chopped all get genuinely different treatment, not
just a label swap (see "League format" below). It syncs your Sleeper league
automatically, merges in your paid Draft Sharks projections from files on
your own disk, and runs roster questions through a four-model debate
panel — grounded in Draft Sharks' math, the wider public market, and live
news — before handing you one clear verdict.

## The Front Office

| Persona | Model | Job |
|---|---|---|
| **Quant / VORP Specialist** | Claude (Anthropic) | Math only — VORP, positional scarcity, roster construction, trade equity, using your league's real scoring settings, your local Draft Sharks data, and Sleeper's own native weekly stat-category projections. Neither numeric source is the final word. |
| **Beat / News Tracker** | Gemini (Google, search-grounded) | Cross-references Draft Sharks against public market consensus (KeepTradeCut, FantasyCalc, FantasyPros, ESPN, etc.), plus live news, injuries, and depth charts. |
| **Contrarian / Risk Analyst** | ChatGPT (OpenAI, web-search-enabled) | Pressure-tests the other two — regression risk, small-sample overreaction, model blind spots, age curves, and Draft-Sharks-vs-market divergence. |
| **Debate Moderator** | Claude (Anthropic) | Synthesizes all three into one actionable verdict, calling out where Draft Sharks, the market, and the news disagree, and closes with a structured recommendation (see "Structured verdicts & the decision log" below). |

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

### Staying up to date

There's no live sync between this repo and your local copy — git doesn't
work that way, and Streamlit needs the actual files on disk to run. The
closest thing to it: `update_and_run.ps1` (Windows) / `update_and_run.sh`
(Mac/Linux) pulls the latest pushed code, installs anything new in
`requirements.txt`, and launches the app, all in one command:

```powershell
.\update_and_run.ps1        # Windows
```
```bash
./update_and_run.sh         # Mac/Linux — chmod +x it once first
```

Run that instead of `streamlit run app.py` directly whenever you want
whatever's newest. It never touches `data/` or `.env` — those are yours,
gitignored, and untouched by pulling new code.

You only need the keys for the models you want to use. Sleeper sync and the
roster dashboard work with zero keys configured. Rather than hand-editing
`.env`, you can also paste them straight into the app: sidebar → **🔑 Connect
Your Accounts** takes a pasted `.env`-style blob (or an uploaded
`.txt`/`.env`/`.pdf`) with any of `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` /
`OPENAI_API_KEY` / `SLEEPER_USERNAME` on it, applies them immediately, and
writes them into your local `.env` so it's a one-time step. It also
recognizes a few common aliases (`CLAUDE`, `GOOGLE`, `CHATGPT`, `GPT`) and
falls back to sniffing bare key values by their provider prefix (`sk-ant-`,
`AIza…`, `sk-…`) if you paste something with no labels at all.

**Run this locally — don't deploy it to a public host.** Every persistence
mechanism in this app (chat history, the decision log, league archive/
reorder prefs, Draft Sharks uploads, player aliases, format overrides, the
remembered Sleeper username) is a flat JSON file on local disk, by design —
see "Design Principles" above. That's correct and private for `streamlit run
app.py` on your own machine, but breaks on something like Streamlit
Community Cloud: the filesystem there isn't durable (a redeploy or a
free-tier sleep/wake cycle can wipe `data/` without warning) and, worse,
isn't private to you — it's one shared container across every visitor to
that URL, so their local files (and yours) can collide or leak into each
other. The Sleeper-session auto-restore (below) is the clearest example —
whoever loaded the page last is whose session the next visitor would see —
but the same mismatch applies to every file under `data/`. None of this
code changes based on where you run it; running it locally is what makes it
correct.

## Using it

1. **Sidebar → Sleeper Sync**: enter your Sleeper username, click **Sync
   Leagues**. All leagues you're in for the current season are discovered
   automatically; pick one from the dropdown. Your username is remembered
   locally (`data/last_session.json`) and re-synced automatically the next
   time you open or refresh the page — Streamlit's own `session_state`
   resets on every browser reload, so without this you'd have to type your
   username and click Sync Leagues again every single time. Click **Refresh This League**
   any time to re-pull rosters/scoring/taxi/traded picks — a timestamped
   snapshot is cached in `data/sleeper_snapshots/` so the dashboard still has
   data even if Sleeper is briefly unreachable.
   Since Sleeper's league list is a full replacement each time (not
   incremental), **Sync Leagues** doubles as new-league detection — anything
   you've joined or created since last sync just shows up. It also detects
   the opposite: if a league you were tracking is no longer returned (you
   left, were removed, or the league was deleted), a prompt appears letting
   you **Archive**, **Delete**, or **Keep as-is** for each one, rather than
   it just silently vanishing from the list with its local data left behind
   forever. This check is against what's actually persisted, not just the
   current browser session, so it still works on your very first sync after
   a restart.
   Use **Manage Leagues** below the dropdown to **Archive** leagues you don't
   want cluttering the front dashboard (still fully cached, just hidden) or
   **Delete** them permanently (purges the cached snapshot, that league's
   own Draft Sharks uploads, chat history, and format override — gated
   behind a confirmation step since it's not reversible). Reorder the rest
   with the ▲/▼ buttons. All of this is saved per Sleeper user in
   `data/league_prefs.json` and persists across sessions; a newly discovered
   league is appended to the end rather than disrupting your saved order.
   Deleting is local-only — it doesn't leave the Sleeper league itself, so
   if you're still actually a member it'll simply reappear, unsynced, next
   time you sync.
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
   The upload box itself has a **comments/questions/labels** text field
   right alongside the file picker — write a note at the moment you upload
   (e.g. "ignore this ranking, Bijan tweaked his hamstring in preseason")
   rather than having to track it down afterward. Above that is a **Global /
   Specific league(s)** toggle — pick Specific and a league multiselect
   appears — since a note's scope can't be reliably guessed from its content
   the way a Draft Sharks PDF's kind can: "Chase is questionable" is true
   for every league, but "considering trading my 2nd for their WR1" is
   clearly about one league's roster and would just be noise (or actively
   misleading) in another league's debate. It defaults to Global; a
   Specific-scoped note is only ever included in the leagues you picked.
   Click **Upload** to submit everything together (it's a form, not an
   instant-on-select uploader, so nothing gets processed until you actually
   click it). If the file turns out to be recognized Draft Sharks data, the
   note still reaches the panel as a small reference-material entry with
   the same scope.
   Below that, a full-width **Reference Material** panel holds anything
   uploaded that *isn't* recognized Draft Sharks data — a screenshot of an
   injury notification, an article, a tweet — instead of the upload just
   silently discarding it. This panel always lists everything regardless of
   scope (so you can find and manage anything), showing each item's current
   scope and letting you change it after the fact. Every item's caption
   (not the raw file) is what actually reaches the debate panel, labeled
   explicitly as an unverified claim to weigh, not fact; edit a caption
   there any time too.
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

### League format — dynasty, redraft, Best Ball, Chopped

Dynasty vs. keeper vs. redraft is detected automatically from Sleeper
(`settings.type`) and shapes reasoning without you doing anything: in a
non-dynasty league, the Quant is told explicitly to discount or ignore
Draft Sharks' 3yr/5yr multi-year projections and rookie-pick trade value,
since the roster doesn't persist to next season and only this-year
production matters.

Best Ball and Chopped are a different story — I don't have verified
knowledge of the exact Sleeper API field either mode uses (Chopped
especially is newer/niche), and I'd rather not guess a field name and risk
silent misdetection. So they're a manual **Special format** dropdown next
to the league selector, off by default:
- **Best Ball**: no start/sit decisions (your highest-scoring eligible
  lineup is picked automatically each week) and typically no waivers or
  trades either. The panel is told to say so plainly if asked a
  week-to-week question that doesn't apply, and redirect toward what
  actually is decidable — draft-day roster construction and depth.
- **Chopped**: no 1v1 matchups — the whole field competes each week and the
  single lowest scorer is eliminated, their full roster dumped onto
  waivers at once. Trades are disabled, so the panel never suggests or
  evaluates one in a Chopped league. Start/sit leans toward floor over
  ceiling more than usual, since surviving one bad week against the entire
  field matters more than a big week against one opponent.

Setting this doesn't touch Sleeper — it's local-only and instant, one
dropdown per league, persisted to `data/league_formats.json`.

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
current" rather than an unexplained "X is more correct." Data missing
entirely is handled the same way: the panel is told plainly what isn't
loaded and to answer anyway from positional reasoning, market consensus,
and general judgment — never to refuse or stall — flagging the gap in its
answer only when it's actually material to the question, not as boilerplate
on every response. A source aged 30+ days is called out as **egregiously
outdated** rather than lumped in with ordinary staleness.

### Proactive nudge for stale waiver data

Free Agent Finder data is the most time-sensitive thing this app loads —
waiver value shifts week to week, unlike season-long dynasty rankings. So
rather than leaving that caveat buried in the LLM's prose, the app itself
checks it deterministically: if the loaded Free Agent Finder data is stale
when you ask a debate question, a **⚠️ NOTICE** message appears in the
chat suggesting a fresh export, before the panel answers anyway with
what's loaded. It won't repeat itself every question — the nudge is keyed
to that file's specific as-of date, so it only fires once per that
freshness state (a fresh session, or the data getting even more stale,
resets it), not on every message while you're mid-conversation.

### Structured verdicts & the decision log

Every `/debate` answer ends with a structured block instead of one free-text
verdict line:

```
RECOMMENDATION: BUY / SELL / HOLD / WAIT
CONVICTION: Unanimous / Majority / Split / Speculative / Worth investigation
REASON: <the deciding factor>
DISSENT: <who dissented and why — only if CONVICTION is Majority>
RISK: <the biggest risk to this being wrong>
RECON: <a concrete thing to ask another manager — only if CONVICTION is Worth investigation>
PRICE CEILING: <the most to give up — only if it's a trade question>
```

**CONVICTION is deliberately not a confidence percentage** — a self-reported
number from an LLM is fake precision with nothing calibrating it. Instead it
reflects something real: whether the Quant, Beat Tracker, and Contrarian
actually agree.

- **Unanimous** — all three land the same direction.
- **Majority** — two agree, one dissents; the Moderator says who and why.
- **Split** — no real consensus among the three.
- **Speculative** — agreement isn't the issue, the underlying evidence is
  thin (a rookie with no track record, a projection with no market/news
  confirmation, stale data).
- **Worth investigation** — the analysis is sound as far as it goes, but the
  real answer depends on something only another manager can tell you. The
  Moderator's `RECON` line spells out exactly what to go ask them — e.g.
  "Ask Team 4 if Player X is available for picks."

Every parsed verdict is appended to that league's **decision log**
(`data/decisions/<league_id>.json`) — question, recommendation, conviction,
reason, dissent, risk, recon, price ceiling, and the full Moderator text.
Parsing fails soft: if a response doesn't follow the format (or a provider
call errored), nothing is logged rather than recording a fabricated verdict.
A **📋 Decision Log** expander under the chat history shows the running
table for the selected league, newest first — the actual point being able
to look back later and check whether the front office's calls held up.

## Project layout

```
sleeper_client.py   Sleeper API wrapper: league discovery, rosters, scoring,
                     taxi, traded picks, cached player DB, snapshot caching.
data_merger.py       Draft Sharks PDF parsers (Dynasty Rankings + Free Agent
                     Finder, auto-detected) + CSV/JSON projection parser,
                     name/team/position matching onto Sleeper players, and
                     projection-freshness tracking.
league_prefs.py       Per-Sleeper-user league archive/reorder preferences.
league_format.py       Manual Best Ball / Chopped override + the strategic
                        guidance text injected into context for each.
attachments.py           Reference material (screenshots/articles) that isn't
                          structured Draft Sharks data — storage, captions,
                          and per-item global-vs-league(s) scoping.
llm_engine.py               Four-persona prompt routing across Claude / Gemini / ChatGPT,
                             plus the structured-verdict parser.
decision_log.py               Per-league record of every parsed Moderator verdict.
app.py                         Streamlit dashboard + debate studio.
update_and_run.ps1/.sh          Pulls latest code + deps, then launches the app.
data/sleeper_snapshots/  Cached league syncs (gitignored).
data/projections/_global/   Dynasty Rankings / format-based exports, shared by
                             every league (gitignored).
data/projections/<league_id>/  Free Agent Finder exports, one folder per league,
                                never shared (gitignored).
data/attachments/           Reference material + captions.json (gitignored).
data/chats/                 Per-league persisted debate history (gitignored).
data/decisions/              Per-league decision log, one JSON file per league (gitignored).
data/last_session.json      Last-used Sleeper username, for auto-restore on page refresh (gitignored).
data/league_prefs.json      Archived/reordered league ids per user (gitignored).
data/league_formats.json    Manual Best Ball/Chopped overrides (gitignored).
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
