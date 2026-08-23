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
