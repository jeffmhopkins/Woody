# Hand-checked, and where I disagree with an agent

**In progress. 4 of 12 sweep agents in.**

## Confirmed against my own work

**The 107 mm assertion was never withdrawn.** Commit `745af8c`'s message
says the figure "is asserted twice and derived nowhere. So this commit
derives it." Both assertions are still there — ADR 0004 `:500` and `:585` —
150 lines above the new 97 mm derivation at `:667`. Verified by grep.
**Eighth instance of the staleness pattern, third time inside a commit
whose own message was about it.**

**The 97 mm budget repeats the defect it replaced.** S1's reconstruction
holds: B1 diagnosed the old 107 mm as "a sum of component heights with no
clearance allowance at all", and the replacement is a sum of component
heights with no clearance allowance at all. Restore B1's clearances →
112 mm against ~110. Put back the toggle/LED row, which I asserted fits
"beside" a 26 mm flange without checking the 24.5 mm either side →
124 mm.

**And the rationale I gave is wrong.** ADR 0004 now says the 10HP win "is
that three pots fit in one row instead of two, which deletes a whole
20+ mm row". **B1's 115 mm already had the pots in one row.** The pot row
did not shrink — it grew, 18 → 22 mm. I explained the saving with the one
line item that got worse. 10HP may still be right; that argument for it is
not.

**`~110 mm usable` is derived nowhere in the corpus** (S1's N1). It is the
denominator of the whole budget. The only recorded panel dimension is
`50.50 × 128.5 mm`; nothing connects 128.5 to 110. The "13 mm of spare"
sits on 18.5 mm of unstated assumption.

## Where I disagree with an agent — the load switch

**S3 Showstopper 2 is half right, and the half it gets wrong matters.**

S3 says `power-entry.md` asserts a ~360 mA start load, says foldback
allows 240 mA at `V_out = 0`, and then integrates with a **zero-load**
closed form — so putting its own two numbers together gives
`240 − 360 = −120 mA` of charging current, the output never rises, and the
rebuilt section therefore does not establish that the circuit starts.

**The criticism is correct. The conclusion is not.** `[calc]`, integrating
`dV/dt = (I_foldback(V) − I_load(V)) / 2.2 mF` numerically:

| Load model | Result |
|---|---|
| Flat 360 mA from `V_out = 0` — S3's implicit model | **stalls at 0 V, never starts** |
| 360 mA appearing at `V_out ≈ 8 V` (the R-78E5.0's minimum input) | **starts in 60.1 ms** |
| Ramping in above 8 V | **starts in 54.4 ms** |

At `V_out = 0` the instrument has no supply, so it draws essentially
nothing; the load appears abruptly when the bucks reach their 8 V minimum,
by which point foldback already allows **707 mA**. So the flat-load model
is not physical and the circuit probably does start — in ~60 ms, against
the 150 ms timer, which is the margin the rebuild was aiming for.

**But S3 found the real defect, which is sharper than either verdict:
the load model is the missing input, and no document states it.** My page
asserted a start load and then used a formula that assumes none. Both
S3's objection and my defence rest on an assumption nobody has written
down. That is what needs fixing — not the number.

> Related, and S3 is right: **"10 nF wrong by 12× to 300×" is itself
> wrong.** The page's own equation gives **37× to 925×**. `bom.csv`
> repeats the bad ratio identically, so cross-checking the two finds false
> agreement — which is exactly how a wrong number survives a review.

## The one deletion done properly

S7's finding, worth holding up as the standard: **`EN`/`IO0` is the only
one of twelve deletions that landed end to end** — header 2×5 → 2×3, loom
11-way → 9-way, conductor tally updated, and the RC networks withdrawn
*by name* in all four documents that mentioned them. Five of the other
eleven are still **depended on**, not merely mentioned.

---

## The structural finding — why this keeps happening

S11's observation, and it is the most useful output of the sweep so far
because it describes a **mechanism** rather than another list of instances:

> Corrections have been landing in the hardware pages (`cluster-boards.md`,
> `carrier.md`, `mod-channels.md`, `digital-and-supervision.md`), which are
> right about nearly everything — while the ADRs and `firmware/README.md`
> retain the superseded text. **On all ten highest-ranked facts, the
> document firmware would actually consult is the one carrying the stale
> value.**

That is not bad luck. Fixes land where the design work is happening, which
is the schematic page in front of whoever is editing. They do not land
where the *consumer* reads. S8 found the same shape from the other side —
`carrier.md` still says four parts are "not in the BOM" when all four now
have rows — so the drift runs both ways.

### The one rule in the corpus with zero staleness findings

**USB MIDI opt-in.** S11 checked it and could not fault it. What makes it
different is the **direction of citation**: the fact is stated once in
`firmware/README.md`, and ADR 0009, `bom.csv` and `carrier.md` all cite it
*back by name* rather than restating it. Nothing can drift, because there
is only one copy.

Every other firmware-facing rule is restated locally in two to five places,
and every one of them has drifted.

**This is the fix worth making**, and it is worth more than any individual
correction in this sweep: a firmware-owned contract page holding the facts
firmware depends on — bit map and marker, loop budget, SPI clocks and write
order, note-on rule, thresholds — with every hardware page *citing* it
instead of repeating it. The same discipline would work for the shared
numbers that keep diverging (the in-amp full scale, the umbilical current,
the LM317 rail), which is the piece of work I flagged in my own words
earlier in this project and did not do:

> "Before much more design happens, the shared figures want declaring once
> and referencing — the filter pole alone lives in five documents. That's a
> piece of work rather than a habit I can fix by trying harder."

Seven waves of review later, that is still the finding.
