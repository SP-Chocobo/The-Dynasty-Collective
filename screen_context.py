"""ScreenContext -- the one shared contract every surface uses to hand the Debate Slab
(see the design-language reference's "Contextual Debate" section) what it needs, without the
Slab ever inferring anything by inspecting rendered UI. "Context is handed over, never
inferred": a surface builds one of these from values it already computed, and the Slab (or,
today, the existing question_input seeding a surface's own escalation buttons write to) reads
it as plain data.

Every ScreenContext answers the same five questions, always in this order:
  1. What am I looking at?
  2. What decision is being considered?
  3. What deterministic evidence already exists?
  4. What entities are involved?
  5. What does the user need to know to interpret the screen? (optional -- not every
     surface has something here beyond the other four fields)

This module holds the contract and per-surface builder functions only. It never computes a
price, a verdict, or any other new value -- every field here is a formatted view of arguments
a caller already had in hand (see build_trade_context, which takes already-priced rows and
already-decided verdict lines as plain strings, never recomputing either).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from pick_synthesis import PickSnapshot

# The two Debate-labeled controls that can appear on the same screen (Draft Room) must never
# read as the same action -- one is a general-purpose doorway into the shared panel, the
# other is Draft Room's own dedicated, deliberately separate deliberation system. Named
# constants here (rather than strings inlined at each call site in app.py) are what make that
# distinction a testable property instead of a hope: see test_screen_context.py's
# DebateHelpTextDistinctnessTests.
UNIVERSAL_DEBATE_HELP = (
    "Open the Debate Studio with the current screen's evidence and context. "
    "Nothing is submitted automatically."
)

DRAFT_ROOM_PICK_DEBATE_HELP = (
    "Run the pick-specific Draft Room deliberation (Strategist, Skeptic, Caller) using the "
    "current frozen snapshot -- a different, dedicated system from the general Debate Studio, "
    "built specifically to reason over this exact board with no live search involved."
)


@dataclass(frozen=True)
class ScreenContext:
    surface: str
    looking_at: str
    decision: str
    evidence: str
    entities: tuple[str, ...] = ()
    guidance: Optional[str] = None

    def to_prompt_seed(self) -> str:
        """The exact text block a Debate control seeds its conversation with -- today,
        this is what app.py's Trade Calculator anvil buttons write into
        st.session_state["question_input"]; going forward it's the same entry point any
        future global Debate control calls, regardless of which surface built the context."""
        blocks = [f"Current context: {self.surface}", self.looking_at, self.decision, self.evidence]
        if self.entities:
            blocks.append("Involved: " + ", ".join(self.entities))
        if self.guidance:
            blocks.append(self.guidance)
        return "\n\n".join(b for b in blocks if b and b.strip())


def build_trade_context(
    *,
    trade_partner: str,
    send_description: str,
    receive_description: str,
    entities: Sequence[str],
    raw_line: Optional[str],
    fit_line: Optional[str],
    overall: Optional[str],
) -> ScreenContext:
    """The Trade Calculator's ScreenContext. send_description/receive_description are
    _describe_trade_side's own output (already-priced rows, external/composite annotations
    and all); raw_line/fit_line/overall are the already-decided Raw Value / Roster Fit /
    Overall verdict strings from app.py's trade math and trade_ledger_ui.overall_synthesis.
    Nothing here re-prices an asset or re-derives a verdict -- it only assembles values the
    caller already computed into the shared ScreenContext shape."""
    looking_at = "Evaluating a trade" + (
        f" with {trade_partner}." if trade_partner and trade_partner != "Not specified" else "."
    )
    decision = (
        f"You send:\n{send_description or '  (nothing added yet)'}\n"
        f"You receive:\n{receive_description or '  (nothing added yet)'}"
    )
    verdict_lines = [line for line in (raw_line, fit_line, overall) if line]
    evidence = "\n".join(verdict_lines) if verdict_lines else "No priced assets to compare yet."
    return ScreenContext(
        surface="Trade Calculator", looking_at=looking_at, decision=decision,
        evidence=evidence, entities=tuple(entities),
    )


# Enough to be useful evidence for a follow-up question, not a dump of the entire available
# pool -- a wide-open "All players" scope early in a draft can have dozens of candidates, and
# the panel only needs the ones actually near the top of this pick's own ranking.
_MAX_CANDIDATES_IN_CONTEXT = 8


def build_draft_room_context(snap: PickSnapshot) -> ScreenContext:
    """Draft Room's ScreenContext -- built entirely from an already-computed PickSnapshot,
    the same translation-layer discipline as draft_board_ui.py's serialize_snapshot. Every
    field below is a direct read off snap/snap.candidates in the engine's own ranked order;
    nothing here re-ranks, re-scores, or recomputes a single value."""
    looking_at = f"On the clock for pick {snap.pick_label}."
    decision = f"Decision regime: {snap.decision_regime}."
    shown = snap.candidates[:_MAX_CANDIDATES_IN_CONTEXT]
    lines = []
    for c in shown:
        survival = f"{round(c.survival_probability * 100)}%" if c.survival_probability is not None else "unknown"
        lines.append(f"{c.name} ({c.position}) — {c.necessity_label}, TAV {c.team_acquisition_value:.0f}, survival {survival}")
    remaining = len(snap.candidates) - len(shown)
    if remaining > 0:
        lines.append(f"...and {remaining} more candidate(s) in the current pool/scope.")
    evidence = "\n".join(lines) if lines else "No candidates available in the current pool/scope."
    return ScreenContext(
        surface="Draft Room", looking_at=looking_at, decision=decision,
        evidence=evidence, entities=tuple(c.name for c in shown),
    )


def build_matchup_context(roster_table: Sequence[dict], focus_position: Optional[str] = None) -> ScreenContext:
    """Matchup's Roster Summary table -- built from the exact roster_table rows that view
    already renders (slot/tier/vorp/projection/injury, in the same Starter-then-Bench-then-
    TAXI/IR order app.py sorts them into). Deliberately just a roster listing with whatever
    per-player numbers are already computed; never a start/sit recommendation of its own --
    that's the separate, parked Lineup Recommendation concept, not duplicated here.

    focus_position implements the Debate Scope committed-object contract: when the grouped
    roster view has one position group explicitly expanded (a persistent UI state app.py
    tracks in st.session_state, never a hover or keyboard-traversal state), that group IS the
    committed object and this narrows to it -- lineage named in looking_at, per the contract's
    nesting rule. None means no group is expanded, so the whole roster is the object, exactly
    as before this parameter existed. A focus_position with zero matching rows still returns
    that (empty) group as the object, per the contract's "empty is still the object" rule --
    it never silently falls back to the whole roster."""
    if focus_position is not None:
        group_rows = [r for r in roster_table if r.get("position") == focus_position]
        looking_at = f"Looking at your {focus_position} group (within your roster)."
        starters = [r for r in group_rows if r.get("slot") == "Starter"]
        decision = f"{len(group_rows)} rostered player(s) at {focus_position}, {len(starters)} in starting slots."
        return ScreenContext(
            surface="Matchup", looking_at=looking_at, decision=decision,
            evidence=_matchup_evidence_lines(group_rows) or f"No rostered players in your {focus_position} group.",
            entities=tuple(r["name"] for r in group_rows),
        )
    looking_at = "Looking at your roster."
    starters = [r for r in roster_table if r.get("slot") == "Starter"]
    decision = f"{len(roster_table)} rostered player(s), {len(starters)} in starting slots."
    evidence = _matchup_evidence_lines(roster_table) or "No rostered players found."
    return ScreenContext(
        surface="Matchup", looking_at=looking_at, decision=decision,
        evidence=evidence, entities=tuple(r["name"] for r in roster_table),
    )


def _matchup_evidence_lines(rows: Sequence[dict]) -> str:
    lines = []
    for r in rows:
        bits = []
        if r.get("tier") is not None:
            bits.append(f"tier {r['tier']}")
        if r.get("vorp") is not None:
            bits.append(f"VORP {r['vorp']:.1f}")
        proj = r.get("sleeper_proj", r.get("projection"))
        if proj is not None:
            bits.append(f"proj {proj:.1f}")
        if r.get("injury_status"):
            bits.append(r["injury_status"])
        team_bit = f", {r['team']}" if r.get("team") else ""
        tail = " — " + ", ".join(bits) if bits else ""
        lines.append(f"{r['name']} ({r['position']}{team_bit}) — {r.get('slot') or 'Bench'}{tail}")
    return "\n".join(lines)


def build_free_agents_context(rows: Sequence[dict], position_filter: Optional[str], search_term: Optional[str]) -> ScreenContext:
    """Maintenance's Free Agents table -- built from the exact post-filter, post-sort rows
    that table already renders, in the same order, never a separate re-query of the player
    pool. Capped to the top _MAX_CANDIDATES_IN_CONTEXT like Draft Room's candidate list --
    a wide-open filter can run to hundreds of rows, and the panel only needs the ones actually
    at the top of the current sort."""
    filters = []
    if position_filter and position_filter not in ("All", "All Positions"):
        filters.append(f"position: {position_filter}")
    if search_term and search_term.strip():
        filters.append(f"search: '{search_term.strip()}'")
    looking_at = "Browsing free agents" + (f" ({', '.join(filters)})" if filters else "") + "."
    shown = rows[:_MAX_CANDIDATES_IN_CONTEXT]
    lines = []
    for r in shown:
        bits = []
        if r.get("ds_fa_rank") is not None:
            bits.append(f"FA rank {r['ds_fa_rank']}")
        elif r.get("ds_rank") is not None:
            bits.append(f"DS rank {r['ds_rank']}")
        if r.get("sleeper_proj") is not None:
            bits.append(f"proj {r['sleeper_proj']:.1f}")
        if r.get("ds_trade_value") is not None:
            bits.append(f"value {r['ds_trade_value']:.0f}")
        if r.get("injury_status"):
            bits.append(r["injury_status"])
        team_bit = f", {r['team']}" if r.get("team") else ""
        tail = " — " + ", ".join(bits) if bits else ""
        lines.append(f"{r['name']} ({r['position']}{team_bit}){tail}")
    remaining = len(rows) - len(shown)
    if remaining > 0:
        lines.append(f"...and {remaining} more in the current filter.")
    evidence = "\n".join(lines) if lines else "No free agents match the current filter."
    decision = f"{len(rows)} free agent(s) match the current filter/search."
    return ScreenContext(
        surface="Free Agents", looking_at=looking_at, decision=decision,
        evidence=evidence, entities=tuple(r["name"] for r in shown),
    )


def build_league_context(team_label: str, team_rows: Sequence[dict]) -> ScreenContext:
    """Another team's roster, browsed from the League view -- built entirely from the same
    per-player rows (name/position/team/slot/sleeper_proj/injury_status) that view already
    renders into its table. Deliberately just a roster listing, never a strength score: this
    stays an entry point a user can ask about, not a conclusion this module hands down (see
    the design-language reference's League "hard contract" -- strength is an entry point,
    never a conclusion, and nothing here invents a League Strength Score of its own)."""
    looking_at = f"Looking at {team_label}'s roster."
    starters = [r for r in team_rows if (r.get("slot") or "Bench") not in ("Bench", "TAXI", "IR")]
    decision = f"{len(team_rows)} rostered player(s), {len(starters)} in starting slots."
    lines = []
    for r in team_rows:
        team_bit = f", {r['team']}" if r.get("team") else ""
        proj_bit = f", proj {r['sleeper_proj']:.1f}" if r.get("sleeper_proj") is not None else ""
        injury_bit = f", {r['injury_status']}" if r.get("injury_status") else ""
        lines.append(f"{r['name']} ({r['position']}{team_bit}) — {r.get('slot') or 'Bench'}{proj_bit}{injury_bit}")
    evidence = "\n".join(lines) if lines else "No rostered players found."
    return ScreenContext(
        surface="League", looking_at=looking_at, decision=decision,
        evidence=evidence, entities=tuple(r["name"] for r in team_rows),
    )
