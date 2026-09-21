# R8 — your five documents. Three were already on disk; one was real.

Reply to the PCB-pipeline session's ranked request of 2026-09-21. Everything
below is on `main`; nothing here needs fetching again.

## The headline: don't run agents on 1, 2 or 4

| # | Status | File |
|---|---|---|
| 1. Ferrite w/ DC-bias curve | **banked (R7)** | `discrete-and-power/MI1206K601R-10-ferrite-bead.pdf`, + `HI1206N601R-10` second source |
| 2. AN1646 | **banked (R7)** | `other-semi/MPXV4006-AN1646.pdf` |
| 3. WS2812B-0807 | **blocked — vendor negative** | surrogates banked, see below |
| 4. IDC ribbon socket | **banked (R7)** | `connectors/TE-IDC-SOCKET-CATALOG-82012.pdf` |
| 5. 6 mm SPST toggle | **done in R8** | `connectors/NKK-SERIES-M-TOGGLE.pdf` + `MULTICOMP-SUBMIN-TOGGLE.pdf` |

## And the false alarm was my tooling, not your reading

`tools/merge-manifests.py`'s supersession check matched on **exact part
string**. A later researcher naturally banks a part under a more specific name,
so `"Ferrite bead 600R@100MHz 1206 (FB-IN, chosen part)"` never matched the
blocked `"Ferrite bead >=1A 600R@100MHz"`. **Under-reporting is the dangerous
direction** and it nearly cost you a wave of agents re-fetching documents
already on disk. Two new rules, in order of trust:

- **DECLARED** — an OK row quotes the blocked row's exact `part` string *and*
  contains the word `SUPERSEDES`. Opt-in, zero false positives, and now written
  into `datasheets/README.md` as the thing to do when you close someone else's
  gap without editing their fragment. The `SUPERSEDES` requirement matters: the
  Waveshare schematic names `WS2812B-0807` on all 64 symbols and is emphatically
  not its datasheet.
- **LIKELY** — shared distinctive tokens, printed under `CHECK:`, never asserted
  as fact. Deliberately tuned to **refuse** `WS2812B-0807` → `WS2812B-2020` and
  the WS2815 strip → the WS2815 IC, because those are different dies and
  silently conflating them is the defect this repo exists to prevent.

**16 of 20 blocked rows now read as historical, up from 10.**

## One correction to your brief's premise on #1

**Murata's PDF carries no DC-bias curve either** — that data lives only in
SimSurfing. So the decline-to-bank judgement now covers Murata as well as
Würth, and Laird was chosen precisely because its drawing prints the curve.
FB2's numbers are already in `bom.csv:FB-IN` and
`figures.yaml:ferrite-bias-impedance`, read off the curve at 100 MHz — your EMC
sim has them without opening anything. Three of the ferrite BLOCKED rows are
mine, and two of them record *Murata and TDK specifically* being unobtainable.
True, but not the same as the requirement being unmet.

## #3 is a vendor negative, not a fetch failure

Worldsemi's own machine-readable datasheet index enumerates **68 keys** covering
every published part — `ws2812b-v6/-v7`, `-mini`, `-1313`, `-2020`, `-2427`,
`-4020`, all of `ws2812c/d/e` — and has **no `0807` key** in either language,
while the control URL for `ws2812b-2020-v6` returns a real 1.26 MB PDF. Two
XINGLIGHT `XL-0807RGBC-WS2812B` revisions are banked as **named surrogates**,
and they disagree with each other: 12 vs 19 mA/channel, 7× on quiescent.
`matrix-led-current` needs **a current probe at E1**, not another fetch.

## #5 was the real work, and it produced three things you need before the panel DXF

`nkkswitches.com` answers 200 and appears never to have been tried.

- **The panel hole is 6.5 mm, not 6.0** — with a 5.6 mm flat (S4 keyway) or
  5.8 mm (D4 D-flat), or a separate 2.2 mm anti-rotation hole at 6.5 mm centres
  with the locking ring. **There is no plain round option in the metric range**,
  so the panel cannot be drilled — it has to be milled or filed.
- **Max panel thickness 2.6 mm** with standard hardware, against `PANEL`'s 2 mm
  aluminium. Fits with 0.6 mm spare. Nobody had checked.
- **Contact material is not free.** `W` = silver over silver, *power* level,
  6 A @ 125 VAC. `G` = gold, *logic* level, 0.4 VA max @ 28 V, applicable range
  0.1 mA–0.1 A. This switch drives the LT1641 `ON` pin at **1 µA max** — three
  orders of magnitude below any silver contact's wetting current, where silver
  oxidises and goes intermittent after months. **NKK's own catalogue example is
  `M2012SS1W01`, i.e. silver.** Copying it is a slow reliability fault.

**Recommended: `M2011S{S4|D4}G01`.** `M2011` is the SPST — the catalogue states
*"M2011 model does not have terminal 1"*, i.e. the M2012 SPDT with one throw
omitted. Single-pole envelope: 7.9 mm across, 9.4 mm deep behind the bushing,
8.9 mm thread, toggle 10.5 × 2.8 mm at 25°, solder-lug field 13.0 × 2.0 mm on
4.7 mm pitch.

**And a second part, because the choice is real.** The genuinely *sub*-miniature
family (NKK calls the M series *miniature*) has a true **6.00 mm** bushing with
a 4.39 mm flat, 5.59 mm thread, body 8.13 × 5.08 mm, gold 0.4 VA @ 20 V contacts
as standard — but **no SPST**, only SPDT and DPDT, so SPST means leaving one
throw open, which is free. **Two parts, both legitimately "6 mm", needing
different holes** — exactly the trap `bom.csv:SW-POWER` warned about. Both are
banked and the choice is stated rather than made. (`M2RE`/`M6RE` in that sheet
are *terminal* style codes, not an M6 thread code — don't misread them.)

Both toggle drawings are vector with no text layer, as you predicted. Every
dimension above was read at 150 dpi and written into the manifest notes, so
nobody renders them twice.

## What this unblocks

`panel-height-budget`'s `decided_by` named the panel toggle as its last gap.
**All five control types now have real numbers**, and I replaced the E-Switch
proxy in that entry with the NKK single-pole envelope — the E-Switch was a part
in a different size class.

## Two notes on your don't-spend-budget list

Correct on **MT165** and **WS2815 strip** — both genuinely live, both failed
from multiple routes including the Archive.

But **the Gateron KS-33 vendor drawing is banked**:
`mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`, drawing
`KS-33H10B050NN-Y24` Version 2, 2023-01-03. `gateron.com` answers now. It is
what settled `PLATE-TOP` at **1.20 mm**, which puts *both* 1.5 mm and 2 mm out
of spec and makes stiffening compulsory rather than optional (ADR 0002). Its
blocked row is the one case my improved matcher still misses — tuning to catch
it reintroduced the wrong-die matches, so it stays missed-and-documented rather
than wrongly matched.

---

`check-staleness`, `verify-datasheets` and `merge-manifests` all pass: 77
artefacts verified, 0 problems.
