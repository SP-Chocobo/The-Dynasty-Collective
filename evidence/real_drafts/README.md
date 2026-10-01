# Real draft boards — the corpus, recovered from the session transcript

**Why this directory exists.** 161 images had been pasted into this session and were living
only inside a 591 MB conversation transcript on an ephemeral container. Nothing pointed at
them, so the owner was asked to hand-type a twelve-seat draft that was already here in full,
legibly, as screenshots. That is the failure this directory prevents from recurring.

108 of the 161 are draft boards or roster captures. They are copied here verbatim, named
`<transcript-line>_<n>.jpg`, with `boards/index.json` carrying each file's line number and the
owner's caption from that message.

## What is in the corpus

| lines | league | what it is | rulebook captured? |
|---|---|---|---|
| 26805, 26818, 26828 | **Fourth and Forever** | complete 12x26 startup board, every pick, position, NFL team, bye, pick number, and trade annotations | **no** |
| 26873 | **Fourth and Forever** | the 4-round rookie draft that followed; undrafted-pool panel with ADP visible | **no** |
| 26929 | **$$ Too fast too fun** | redraft, 1 SF / 2 RB / 3 WR / 2 FLEX, 30-second clock, ~20 rounds | no |
| 26958, 26969, 26979, 26990, 27000 | **Greatest Show on Paper 2** | complete board incl. kickers; kickers were placeholders for rookie picks (1st K = rookie 1.01, 13th K = 2.01) | **YES** — `data/league_captures/greatest_show_on_paper_2.json` + 4 projection CSVs |
| 27069, 27086, 27103, 27114, 27166, 27176, 27194, 27204 | assorted | boards found online or in group chats; one is `.5 PPR / .5 TEP`; several read as 1QB redraft. Format and competition level unverified for most | no |
| 50385-50563 | **Greatest Show on Paper 2** | 26 roster/board captures, "no DST/K/IDP in this one" | YES |
| 100721-100927 | owner's eight live rosters | mid-season rosters incl. IR and taxi (chop league, Fourth and Forever, Playbook, Down With IDP, Battle of NFC/AFC, and others) | partial |

## Legibility

Verified by reading them, not assumed. Player name, position, NFL team, bye week, pick number
and traded-pick ownership are all readable at the stored resolution (923x2000 for the wide
captures). Several shots also carry the undrafted-pool panel with ADP and projected points,
which is the supply-side capture the `roster_shape` work has been missing.

## The one already-transcribed board

`evidence/roster_shape/real_drafts/` holds Fourth and Forever tallied by hand from the owner's
typed pick orders. That transcription is INDEPENDENT of these images and should be used to
check any read taken off them, in that direction only -- the images are the primary record.

## Dates, resolved by the owner

Fourth and Forever's **veteran startup opened 9 August** and the **rookie draft ran 14 August**.
The startup is a slow-clock draft, so it took days to complete -- which is why the line-26873
caption reads "immediately after the veteran draft" while the owner separately dated the startup
to the 9th. Both are right; the gap is the startup's own duration.

The five-day gap is not cosmetic. Picks were traded between the two boards (the rookie board
carries "-> <manager>" annotations), so the rookie draft is a SEPARATE decision environment
downstream of the startup, not a continuation of the same sitting.
