"""`#329`: how many vocabularies this product has for "what kind of thing is this number", counted so a
fourth cannot appear unnoticed.

THE OWNER'S THIRD COHERENCE POPULATION. The two cross-surface invariants in
`invariant_registry` are "one engine figure reads the same on every surface" (census 9) and "a
withheld quantity does not reach a person on any surface" (census 12). The third asked for is:
THE SAME SEMANTIC STATE MEANS THE SAME THING ON EVERY SURFACE, AT EVERY VIEWPORT. Measured, that
claim is FALSE today, and this file exists to say so with a number rather than to assert it:

    draft room   `shared.js` KIND          measured, a count, withheld, not measured,
                                           not charged, not priced into value      (6)
    front page   `build_front.stamp_kind`  measured, constructed, absent            (3)
    engine       `basis_semantics`         bounded_input, bounded_by_rule           (2)

    shared by the two USER-FACING surfaces: `measured`, and nothing else.

Three consequences, each worth stating separately because each is a different defect:

  1. The room can say five things the front page cannot express.
  2. The front page can say `constructed` -- the word that marks a figure as FABRICATED FOR A
     DEMO -- and the draft room has no way to say it at all. That is the absence contract's
     (`#187`) most load-bearing word missing from the product's reference surface.
  3. `basis_semantics` distinguishes "more evidence would sharpen this" (BOUNDED_INPUT) from
     "this is the limit of what is knowable" (BOUNDED_BY_RULE), and NEITHER user-facing surface
     can render either. The engine computes an epistemic distinction that never reaches a person.

WHY THIS IS A RATCHET AND NOT A PASSING INVARIANT. The claim it wants to make -- one vocabulary
-- does not hold, so registering it in `invariant_registry` today would mean registering a
census against a claim the code contradicts. What CAN be guarded immediately is the thing that
makes the repair harder every time it happens: a FOURTH vocabulary. `boundary_census` is the
model -- it allows 41 reaches and watches for 42 while the work to get to zero proceeds. So this
allows three vocabularies and fails on a fourth, and the number falling is the repair landing.

WHAT IT DOES NOT CLAIM. It counts DECLARED vocabularies -- a map or dispatch whose members are
state words. A surface that spells one state word inline, with no map, is invisible here, exactly
as `_surfaces_consulting_the_withholding_policy` cannot see a surface that never asks. That is
what the per-surface rendering tests are for; this counts the sources of truth.
"""

from __future__ import annotations

import pathlib
import re

#: Each declared vocabulary: where it lives, how to read it out, and what it is FOR. Hand-listed
#: because "is this a state vocabulary" is a judgement about meaning -- the same reason
#: `boundary_census.DATA_MODULES` and `api_surface.LAYERS` are hand-assigned -- but each entry
#: carries a reader, so the WORDS are derived and cannot drift from the source.
VOCABULARIES: dict[str, dict[str, str]] = {
    "draft_room": {
        "path": "ui_explore/round2/fableA/_src/shared.js",
        "pattern": r"const KIND = \{(.*?)\};",
        "members": r"(\w+)\s*:\s*\"([^\"]+)\"",
        "for": "what kind of thing a number in the engine's working is, as a reader sees it",
    },
    "front_page": {
        "path": "ui_explore/round3/build_front.py",
        "pattern": r"def stamp_kind\(stamp\):(.*?)\ndef ",
        "members": r"\"(measured|constructed|absent)\"",
        "for": "whether a figure on the front page was measured, fabricated, or is missing",
    },
    "engine": {
        "path": "basis_semantics.py",
        "pattern": r"(BOUND_KIND_\w+ = \"\w+\")",
        "members": r"\"(\w+)\"",
        "for": "whether more evidence would sharpen a bounded quantity",
    },
}

#: First measured at `#310`, RE-DERIVED at `#329` against the tree as it stands -- the draft
#: room's `shared.js` moved three times in between (`#316`, `#320`, `#325`) and the readers
#: still resolve, which is the point of deriving the words rather than listing them.
#: A RISE is the regression: a fourth place that decides what a number's kind is called.
#: A FALL is the repair -- the words moving to one home.
CENSUS = 3

#: How many state words the two USER-FACING surfaces must BOTH be able to say. A FLOOR, not a
#: target: it may rise and must not fall.
#:
#: `#329` set this at 1 -- they shared `measured` and nothing else. `#330` added `constructed`
#: to the draft room and the floor FOLLOWS THE REPAIR UP to 2, because a ratchet that does not
#: move with its own repair is just a ceiling: the gain would be lossless to give back, silently.
#: At zero, no semantic state would mean the same thing on both surfaces at all, which is the
#: owner's third coherence population failing outright rather than partially.
SHARED_FLOOR = 2


def words_of(name: str, root: pathlib.Path = pathlib.Path(".")) -> list[str]:
    spec = VOCABULARIES[name]
    text = (root / spec["path"]).read_text(encoding="utf-8")
    # findall, NOT search. An earlier draft of this used `re.search` and read only the FIRST
    # match of `pattern` -- which found `bounded_input` and silently dropped
    # `bounded_by_rule`, because that vocabulary is declared as two sibling assignments rather
    # than one block. A census that under-reports its own population is the exact failure this
    # repository keeps finding, so every declaration the pattern matches is joined and read.
    blocks = re.findall(spec["pattern"], text, re.S)
    if not blocks:
        raise LookupError(f"{name}: the vocabulary's own declaration is no longer at "
                          f"{spec['path']} in the shape this file reads. Re-derive it rather "
                          f"than hand-listing the words here.")
    joined = "\n".join(b if isinstance(b, str) else "\n".join(b) for b in blocks)
    found = re.findall(spec["members"], joined, re.S)
    words = sorted({(m[0] if isinstance(m, tuple) else m) for m in found})
    if not words:
        raise LookupError(f"{name}: the declaration was found but no state words were read "
                          f"out of it -- the member pattern no longer matches.")
    return words


def divergence(root: pathlib.Path = pathlib.Path(".")) -> dict[str, object]:
    per = {name: words_of(name, root) for name in VOCABULARIES}
    room, front = set(per["draft_room"]), set(per["front_page"])
    engine = set(per["engine"])
    return {
        "vocabularies": len(per),
        "per_surface": per,
        "union": sorted(room | front | engine),
        "shared_by_user_facing": sorted(room & front),
        "room_only": sorted(room - front),
        "front_only": sorted(front - room),
        "engine_only_unrenderable": sorted(engine - room - front),
    }


def widened(root: pathlib.Path = pathlib.Path(".")) -> list[str]:
    """What is WORSE than the census records. Empty is the passing state.

    Two different regressions, deliberately separated. A FOURTH vocabulary is a new place that
    decides what a number's kind is called. A SHRINKING shared set is the two user-facing
    surfaces drifting further apart -- there is exactly one word (`measured`) holding them
    together today, and losing it would mean no state means the same thing on both.

    What is NOT here, on purpose: the divergence itself. `room_only` is 5 and `front_only` is 2,
    and a REPAIR makes those fall. Asserting today's numbers would make the repair fail the test,
    which is how a census stops being a ratchet and starts being a cast.
    """
    d = divergence(root)
    out = []
    if d["vocabularies"] > CENSUS:
        out.append(f"A FOURTH VOCABULARY: {d['vocabularies']} places now decide what a number's "
                   f"kind is called, census allows {CENSUS}. Every one of them is a home the "
                   f"state words have to be kept in step across by hand.")
    if len(d["shared_by_user_facing"]) < SHARED_FLOOR:
        out.append(f"THE USER-FACING SURFACES HAVE DRIFTED FURTHER APART: "
                   f"{len(d['shared_by_user_facing'])} state words are common to the draft room "
                   f"and the front page, floor is {SHARED_FLOOR}. They shared only `measured` "
                   f"when this was written; below that, no state means the same thing on both.")
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="fail if a fourth vocabulary appeared or the shared set shrank")
    args = parser.parse_args(argv)

    d = divergence()
    if not args.check:
        for surface, words in d["per_surface"].items():
            spec = VOCABULARIES[surface]
            print(f"  {surface:12} ({len(words)})  {', '.join(words)}")
            print(f"  {'':12}        -- {spec['for']}")
        print(f"\n  shared by the two user-facing surfaces: "
              f"{', '.join(d['shared_by_user_facing']) or 'NOTHING'}")
        print(f"  the room can say, the front page cannot : {', '.join(d['room_only'])}")
        print(f"  the front page can say, the room cannot : {', '.join(d['front_only'])}")
        print(f"  the engine computes, neither can render : "
              f"{', '.join(d['engine_only_unrenderable'])}")
        return 0

    grew = widened()
    if grew:
        for line in grew:
            print(line)
        return 1
    print(f"{d['vocabularies']} state vocabularies (census allows {CENSUS}); the two user-facing "
          f"surfaces share {len(d['shared_by_user_facing'])} "
          f"({', '.join(d['shared_by_user_facing'])}), floor {SHARED_FLOOR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
