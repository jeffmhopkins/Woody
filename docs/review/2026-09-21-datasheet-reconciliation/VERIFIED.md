# Hand-checked, and where an agent was wrong

Findings are claims. Everything below that changed a number in the corpus was
re-read by the lead against the banked PDF before it was applied — several times
by rendering the page, because the document had no text layer.

## Checked by hand, agent confirmed

| Claim | How it was checked | Verdict |
|---|---|---|
| onsemi MC74HC165A publishes a **3.0 V** threshold row, `V_IH` 2.1 / `V_IL` 0.9 | `pdftotext` of the banked PDF, DC characteristics table p.4 | **Correct.** Read the table myself |
| Nexperia Rev. 8 has **no** 3 V row | Same, Table 6 p.6 — 2.0/4.5/6.0 only | **Correct** |
| LT5400 MS8E **has an exposed pad** | `pdftotext`, p.2: "EXPOSED PAD (PIN 9) IS FLOATING" | **Correct** |
| SP0504BAHTG is **SOT23-5**, not -6 | `pdftotext`, p.1 ordering table; SP0505BAHTG is the -6 | **Correct** |
| SP0504BAHT power is **0.225 W** and there is **no** peak-pulse spec | p.2 abs max; grep for "peak pulse"/"8/20"/"Ipp" returns nothing across 8 pages | **Correct** |
| REF50xx**AI** is the *Standard* grade, ±0.1 % / 8 ppm/°C | Table 4-2 p.3 | **Correct** |
| OPA2197 `ZO` is **specified** at 375 Ω | EC table, two occurrences (p.8, p.10) | **Correct** |
| The "1 nF" **is** an OPA2197 figure | p.1 Features line 32, and §7.3.5 p.22 | **Correct** |
| Waveshare board is fitted with **WS2812B-0807** | 64 occurrences in extracted text, all on `VCC_5V` | **Correct** |
| NE8MC is **discontinued**, successor NE8MX | NE8MC datasheet p.1 | **Correct** |
| NE8FDP datasheet states **panel thickness max 4 mm** | p.2 mechanical table | **Correct** |
| Gateron plate slot is **1.20 ±0.05 mm** | Rendered sheet 6 at 150 dpi and read the elevation | **Correct** |
| Laird bead datasheet carries a real **DC-bias curve family** | Rendered sheet 1; traces at 0 / 250 / 500 / 1000 / 1500 mA | **Correct** |

## The one that matters most: a fix from the previous day, reversed

`key-release-time` and `key-press-time` were moved on 2026-09-20/21 from
119.9 µs / 5.92 µs to 138.7 µs / 6.89 µs, on the reasoning that TI's SCLS116E
has no 3.3 V row, that the 0.70/0.30 ratio "breaks" at 2 V, and that
extrapolating it down to 3.3 V therefore runs through the contradicting
datapoint. **onsemi publishes a 3.0 V row and it is 0.70/0.30.**

So 3.3 V is bracketed *on both sides* by published 0.70/0.30 rows and needs no
extrapolation at all; 2 V is the single exception at the bottom of the family's
range, not the beginning of a trend. All four vendors agree digit-for-digit at
every shared rail, which is what makes onsemi's extra row the family's rather
than one vendor's. The figures are back to 119.9 µs and 5.92 µs, with the
TI-only pessimistic bound recorded in each entry's `conservative_bound`.

**Two things about this are worth keeping.**

The reasoning that produced the wrong answer was *good* reasoning. It noticed a
real discontinuity in the data, refused to extrapolate through it, and took the
conservative side. It failed only because it treated "absent from the one
datasheet I have" as "absent from the world". **The lesson is not "be more
careful"; it is "check a second vendor before inferring a missing row".**

And the move left an internal contradiction that no grep would find:
`cluster-boards.md` said 0.75/0.25 in its derivation and 0.7/0.3 in its
open-questions list, while ADR 0001 carried the *new* times against the *old*
thresholds. That is CLAUDE.md §4 happening **inside the commit that was about
§4** — the fourth recorded instance — and the stale line was the one that was
right.

## Where the lead was wrong, caught on the same day

**I filed a refuted inference as confirmed, in `bom.csv`'s `U-TVS-SPI` row.**
While resolving the rebase conflict against `main`, I merged the other
session's ESD7104 observation — that the ESD7104 specifies pulse ratings only
and no steady-state dissipation, *"which suggests the reviewer's 0.98W
sustained-fault figure may be outside what this whole class of array is
specified for"*, explicitly flagged there as an inference needing confirmation
against the SP0504BAHT itself — and wrote **"It is confirmed."**

**It is refuted.** The two documents are mirror images:

| | steady-state `P_D` | pulse rating |
|---|---|---|
| onsemi ESD7104 | **none stated** | 8/20 µs, IEC 61000-4-2 |
| Littelfuse SP0504BAHT | **0.225 W** (Abs Max p.2; `PD@70°C .225W` p.7) | **none at all** |

The sentence I wrote contradicted itself inside one clause — *"specifies no
steady-state or pulse power either — only the 0.225 W package limit"* — because
the 0.225 W **is** the steady-state specification. The `.manifest-R7.csv` row
and the table above both had it right; only the merged prose was wrong, and the
prose is what a reader of `bom.csv` sees.

**What it does to the conclusion: strengthens it.** A sustained-fault rating is
*not* outside what this part is specified for — it is 0.225 W, a published hard
ceiling, and the prior review's 0.98 W is refuted by a real sourced number
4.4× lower rather than by an absence. The fix stays a series resistor or a
resettable element, not a bigger array.

**Two things worth keeping from this.** It is the failure CLAUDE.md names as
the worse one — *"a wrong finding gets caught by the next reviewer while a
finding filed as handled does not"* — and it happened at a **merge**, where two
correct records were combined into a wrong one. And the correct version was
already sitting in the manifest row two files away. **A merge is a place to
re-read the evidence, not just to reconcile two texts.**

## Where an agent overreached, and was corrected

**`MECH` reported the panel-thickness hedge as simply "wrong".** The Product
Guide it cites does show 3 mm as the D-series range's base and 4 mm as the
exception, which refutes the specific claim that the blanket 4 mm was
"over-general". But `bom.csv`'s "somewhere in 1–4 mm depending on variant" is
wrong only *for NE8FDP and NE8FDV*, which is what the row is about. Recorded as
a partial refutation, not a full one.

**`BEAD` reported the brief's premise, not just the repo's, as wrong** — that
Murata BLM publishes DC-bias data. It does, but **not in the PDF**; it lives in
SimSurfing. That distinction is the whole point of the gap, so it is recorded in
the BOM row rather than buried: a Murata part can be an *alternate* flagged
"bias assumed", never the characterised part. The earlier researcher's refusal
to bank a Würth WE-CBF for the same reason is upheld, and `BEAD` upheld it too
rather than taking the easy fetch.

**`ADILF` flagged its own weakest link without being asked**, and it was the
right one: it banked LT5400 rev **fa**, not the **fc** the corpus names
canonical. Rev fa's option table predates the `-7`, so `LT5400-7` is
**not-in-document**, not refuted — and it explicitly warned against anyone
"correcting" ADR 0006 by citing rev fa's silence. That warning is preserved in
the BOM row.

**`TI` declined to resolve a question it could not source.** Table 4-2, which
settles the REF5050 grade mapping, is *new in rev O*, so the corpus's belief may
have had an honest origin in an earlier revision that `TI` did not fetch. It
reported rev O and said so, rather than concluding the corpus had simply been
careless. The `ref5050-grade` figure is recorded as **disputed** rather than
settled for exactly that reason — and because changing it is a part change, not
a documentation fix.

## Not verified, and flagged as such

- The bead bias-curve readings are **pixel traces off a plotted curve**, ±10 Ω.
  The structural conclusion — that impedance at 100 MHz collapses with DC bias
  and that FB2 gets roughly half its nameplate — is visible by eye and is not in
  doubt. The individual numbers are digitisations.
- The Toshiba 74HC165 row is a **6-page excerpt** cut from a 675-page 1986
  databook, banked rather than the whole book on size grounds, with the parent
  SHA-256 in the manifest note. It is also a 1986 document for the `TC74HC165P/F`
  rather than the modern `AP`. It supports only one claim — "Toshiba also omits
  3 V" — which TI and Nexperia corroborate independently. Kept, with the
  provenance stated in full; drop it if the awkwardness outweighs the corroboration.
- `LT5400-7`, and whether an earlier REF5050 revision labelled the grades
  differently. Both need a document nobody has.
