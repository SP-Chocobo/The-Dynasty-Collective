"""E-F5: does the repaired guard fire when the season fetch actually fails?

No hand-built coverage record. The coverage dict comes from `_sum_weeks` itself, driven by
the real `get_weekly_projections`, whose own docstring says it FAILS SOFT on an unreachable
API. Then the production consumer is called on it.
"""
import sleeper_client as sc

class Boom(sc.SleeperClient):
    def _weekly_stat_lines(self, *a, **k):
        raise sc.SleeperAPIError("Failed to reach Sleeper API at https://api.sleeper.app/...: "
                                 "ConnectionError")

c = Boom()
totals, coverage = c.get_season_projections("2026", "regular", weeks=18)
print("totals rows            :", len(totals))
print("coverage keys          :", sorted(coverage))
print("coverage['error'] ?    :", "error" in coverage, "->", coverage.get("error"))
print("weeks_answered         :", coverage["weeks_answered"])
print("weeks_failed (n)       :", len(coverage["weeks_failed"]))
print("season_sum_is_complete :", sc.season_sum_is_complete(coverage))

snap = {"season_projections": totals, "season_projection_coverage": coverage}
priced, reason = sc.priceable_season_projections(snap)
print()
print("priceable -> projections:", priced)
print("priceable -> REFUSAL    :", repr(reason))
print()
print("VERDICT:", "SILENT (no warning) -- E-F5 guard did not fire" if reason is None
      else "warned")

# And the arm the repair's own comment describes: get_season_projections RAISES.
print()
print("--- the arm the repair's comment describes (an exception out of the fetch) ---")
raised = {"weeks_answered": [], "weeks_failed": [], "players": 0,
          "error": "SleeperAPIError: Failed to reach Sleeper API"}
print("priceable ->", repr(sc.priceable_season_projections(
    {"season_projections": {}, "season_projection_coverage": raised})[1])[:90], "...")
