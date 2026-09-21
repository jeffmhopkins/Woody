# Wave R7 — datasheet reconciliation

**2026-09-21.** Not a review wave. A **fetch-and-reconcile** wave: get the
documents four review waves could not reach, bank them, and check what they
actually say against what the corpus believes.

## Method

Six researchers ran in parallel, **sliced by document, not by file** — the same
principle as the review waves, applied to the other axis. Each was told to bank
its documents under `datasheets/`, write proposed manifest rows to a scratch
file, and **edit nothing else in the repo**. All reconciliation into the corpus
was done by the lead, after checking each load-bearing claim by hand.

| Agent | Assignment |
|---|---|
| *(lead)* | LT1641-1 `164112fc.pdf` — the Priority-1 document, and the parts-order blocker |
| `TI` | OPA2197 SBOS737, REF5050 SBOS410 |
| `ADILF` | LT5400 5400fc, SP0504BAHT |
| `LOGIC` | 74HC165 second sources — Nexperia, Toshiba, anything with a 3 V row |
| `MECH` | Waveshare schematic, Neutrik etherCON, IDC socket, AN1646, 1N4148W |
| `BEAD` | Choose a ferrite bead and bank it; Gateron KS-33; Tai-Hao MT165 |
| `LED` | The gaps `MECH` opened: WS2812B-0807, B5819WS, ME6217C33M5G |

The agents' own reports are in this directory. `VERIFIED.md` records what the
lead checked by hand and where an agent was wrong.

## What made it work

**The network was different, and nobody had re-measured it.** Waves R1–R6 found
every vendor host blocked and built a sophisticated GitHub-mining method around
that constraint. It was excellent work and it was solving the wrong problem by
the time R7 ran: ti.com, neutrik.com, murata.com, gateron.com, waveshare,
farnell, onsemi.cn and **web.archive.org** all answered normally. **Nine of the
seventeen gaps closed by asking again.** The first action of any wave that
inherits a list of blocked hosts should be to re-probe it.

**The Internet Archive reaches hosts that are still dead.** `analog.com` fails
today exactly as it did in every earlier wave — an origin-side HTTP/2 reset, not
a proxy denial. Its 2019 capture of `164112fc.pdf` fetched in one try. That one
lever closed the Priority-1 gap that four waves had left open.

**Mirrors lie, and three of them lied in this wave.** An RS-online URL recorded
in an earlier BLOCKED row *as the LT1641's mirror* is a real PDF of the
**LT4256**. A Farnell URL found searching for a 74HC165 contains no occurrence
of "165". A Diodes Inc URL found searching for a 1N4148W is the **MMST3906
transistor**. Every one returned HTTP 200 with a plausible filename. Grep the
extracted text for the part number or do not bank the file.

**Some documents have no text at all.** Gateron's drawing, the Laird bead
drawings and the Neutrik outlines are vector CAD; `pdftotext` returns a byte or
two and the numbers exist only in the picture. The plate thickness and the bead
bias curve — two of this wave's most consequential findings — were read by
rendering at 150 dpi and looking. An earlier wave recorded the NE8FDP drawing as
"does not state the panel thickness", which was true: the number was in the
*datasheet*, and nobody had fetched that.

## The shape of the result

**28 documents banked. 10 previously-BLOCKED parts closed. 4 rows still
blocked, and three of those four are gaps this wave opened rather than
inherited.**

Of the claims checked against a real document, the split is roughly two-thirds
confirmed and one-third refuted — and **the refutations clustered in exactly the
places the corpus had already flagged as weakly sourced**, which is a good sign
about the corpus's own self-assessment. The LT1641 section, which carried the
loudest provenance warning in the repo, came through with eight of nine claims
confirmed verbatim.

**The most valuable single finding is a reversal of a fix made the day before.**
See `VERIFIED.md`.

**And the most useful "failure" is a vendor negative.** `LED` could not find a
WS2812B-0807 datasheet — because Worldsemi does not publish one, which it
established from the vendor's own machine-readable datasheet index rather than
by running out of URLs. It banked two surrogates under their real manufacturer's
name, refused to quote their numbers as the fitted part's, and said the
remaining question is now a bench measurement. That is the right shape for a
gap: bounded, evidenced, and pointing at the thing that would actually close it.
