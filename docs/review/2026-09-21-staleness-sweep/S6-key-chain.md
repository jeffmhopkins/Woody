# S6 — Key chain staleness sweep

**Domain:** key switches, the shift-register chain, the cluster boards, the
32-bit allocation.
**Date:** 2026-09-21. **Auditor:** S6. **No file was edited but this one.**

**Corpus audited:** `hardware/**`, `docs/decisions/**`, `config/**`,
`docs/reference/**`, `ROADMAP.md`, `README.md`, `firmware/README.md`.
`docs/review/**`, `docs/log/**` and `docs/research/**` were read for provenance
only and are **not** reported as stale.

Indexed by **disputed fact**, not by document. Every entry quotes both sides.

---

## Summary

| # | Disputed fact | Rank | Stale sites |
|---|---|---|---|
| **D1** | Marker bits: 8 or 6 or "four to six" | **Showstopper** | ADR 0010, `carrier.md` |
| **D2** | Genuinely free bits: 3 or 5 | **Showstopper** | ADR 0001, `key-layout.yaml`, `carrier.md` |
| **D3** | Conductors per hop: 12 or 6 | **High** | ADR 0001 ×3, `key-layout.yaml`, `bom.csv` ×1, `ROADMAP.md` |
| **D4** | `J-CHAIN` count: 8, 5, or "~4" | **High** | `bom.csv` `WIRE-LOOM`, ADR 0001 table |
| **D5** | `R-KEY-PU` / `C-KEY` values: 2.2 kΩ + 47 nF or 10 kΩ + 10 nF | **High** | ADR 0009, `bom.csv` `R-KEY-SER` |
| **D6** | `R-KEY-PU` quantity: 24 or 21 | **High** | ADR 0001, `carrier.md` |
| **D7** | Key network timings: 119.9/5.92 µs or 125/5.7 or 93/1 | **High** | ADR 0001, `bom.csv` ×2, `cluster-boards.md` (self) |
| **D8** | 3V3 chain load: 25.8 mA or "microamps" | **High** | ADR 0005 |
| **D9** | Full chain read: 32 µs, 16 µs, or <10 µs | **High** | `latency-budget.md` ×2 |
| **D10** | Note-on debounce: fire immediately, or two agreeing samples | **Medium** | `firmware/README.md`, `latency-budget.md`, `ROADMAP.md` |
| **D11** | Network passive total: 66 or 63 | **Medium** | 6 sites incl. `cluster-boards.md` itself |
| **D12** | Is pin 6 `SER` a bus? | **Medium** | `cluster-boards.md` §3 (self) |
| **D13** | ADR 0001's own hop breakdown sums to 13, not 12 | **Medium** | ADR 0001 |
| **D14** | Tail-topology wire count: 32–44 / ~46 / 35 / 21 | **Medium** | ADR 0001, `bom.csv` ×2, `carrier.md`, `cluster-boards.md` |
| **D15** | `V_IL` threshold cited: 0.8 V (LVC) on an HC part | **Low** | ADR 0001, `bom.csv` `C-KEY` |
| **D16** | Static current per closed key: 1.43 mA or 1.5 mA | **Low** | `bom.csv` `R-KEY-PU` |

Plus **7 facts asserted but never derived** (§N) and **9 facts verified
consistent** (§V).

---

## D1 — The marker pattern is 8 bits. Two documents still say 6, or 4–6. **Showstopper**

This is hard-wired copper on boards that bond into the instrument. ADR 0010 is
the ADR that owns the *plate cutouts*, so a reader who trusts it will reserve
the wrong number of retrofittable positions.

**Current truth** — `docs/decisions/0001-mcu-and-board-partitioning.md:320-322`:

> **Use 8 of the 14 spare chain bits as a fixed marker pattern. DECIDED,
> 2026-09-21** — this line read "4–6" until then.

and `config/key-layout.yaml:138`: `spare_bits_marker: 8      # DECIDED 2026-09-21, ADR 0001 - was 6`
and `hardware/controller/cluster-boards.md:289`: "### The marker pattern: 8 bits, not 6 — DECIDED 2026-09-21".

**Stale — `docs/decisions/0010-key-layout-as-data.md:172-174`:**

> - **Four to six of the spare chain bits belong to the marker pattern**
>   (ADR 0001) and are not available for switches. Eight to ten remain, which is
>   more than three.

Both halves are wrong: 8 belong to the marker, and **6** remain (3 reserved
switches + 3 free), not "eight to ten". ADR 0010 is also the document that
declares the M3 cutout deadline, so this is the worst place for the number to
be wrong.

**Stale — `hardware/controller/carrier.md:514-516`:**

> **Which six bits carry the marker and to what pattern is still undecided, and
> it is now a cluster-board decision**

and `hardware/controller/carrier.md:863-866`:

> **Two items left this page with the registers.** The **marker pattern**
> (which six bits, to what levels) and the **`H`…`A`-to-switch mapping** are
> now `PCB-CLUSTER` decisions

Same page already carries the corrected table at `carrier.md:510`
("**Decided 2026-09-21: 8, not 6**"), so `carrier.md` contradicts itself twice
over. The 2026-09-21 hardware review already flagged this
(`docs/review/2026-09-21-hardware-and-standards-review/VERIFIED.md:22`) and it
was only half-applied — the table was fixed, the prose was not.

---

## D2 — There are 3 genuinely free bits. Three documents still say 5. **Showstopper**

Same copper, and it additionally drives the `R-KEY-PU` quantity (D6). One of
the three sites is **`config/key-layout.yaml` contradicting its own field**.

**Current truth** — `docs/decisions/0001-mcu-and-board-partitioning.md:337-338`:

> So the allocation is **6 marker →
> 8 marker, 5 free → 3 free**, and the 3 that remain still get pulled per fix 6.

and `config/key-layout.yaml:140-143`:

> `spare_bits_free: 3        # was 5; two went to the marker.`

**Stale — `config/key-layout.yaml:131-132`, eleven lines above its own field:**

> `#   The 5 genuinely free bits are FLOATING CMOS INPUTS and must be pulled -`
> `#   the exact fault R-KEY-PU exists to fix (ADR 0001).`

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:289-292`,
fix 6 of the very ADR that decided 3:**

> 6. **Tie `CLK INH` low at all four devices, and pull every unused parallel
>    input.** Both are permanent and both were sitting only in a review document.
>    The five genuinely free spare bits are floating CMOS inputs — the exact
>    fault `R-KEY-PU` exists to fix.

ADR 0001 therefore says "5 free" at line 291 and "3 free" at line 338.

**Stale — `hardware/controller/carrier.md:520-523`:**

> **The option worth costing has got cheaper.** Giving the 5 free bits the full
> network too is now 15 passives spread across four boards that already carry
> 21 sets

Both the count (5) and the derived passive figure (15 = 5 × 3) are stale; it is
3 bits, and the decision taken on `cluster-boards.md:349-351` was **one
`R-KEY-PU` each and nothing else** — not the full network.

---

## D3 — 12 conductors per hop. Six documents still say six. **High**

`J-CHAIN` is a 2×6 IDC, 12 conductors per hop. "Six" is the *signal* count
(SCK, SH/LD, SER, QH, 3V3, GND) and it is repeatedly written as the *conductor*
count — including in the M4 fit-check that is supposed to prove the loom fits
the side channel.

**Current truth** — `docs/decisions/0001-mcu-and-board-partitioning.md:81-83`:

> `|  ONE chained run, 12 conductors per hop (2x6 IDC), passing through`
> `|  each cluster board in turn: SCK, SH/LD, serial in, serial out,`
> `|  a ground between every signal, 3V3, and two spares`

and `hardware/bom.csv:72` (`WIRE-LOOM`): "TWELVE conductors per hop".

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:160-162`,
the paragraph that *wins the argument for the topology*:**

> It wins on hand-joint count (about 4 connectors against about 46 wires, in a
> strap-worn instrument that is bonded shut), on loom width (6 conductors per hop
> against 40–56 mm of ribbon sharing channels with the LED strips and the breath
> tube)

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:365-367`
(Consequences):**

> a trace on the board the switch is already soldered to, and six conductors
> leave each cluster.

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:131`:**

> connection is a copper trace. Four conductors plus power leave each board.

("Four plus power" is neither 6 nor 12; it is a third framing.)

**Stale — `config/key-layout.yaml:100-102`:**

> `# Six conductors leave each board - VCC, GND, CLK, SH/LD, SER-in, QH-out - with`
> `# a ground return per signal, chained cluster to cluster rather than starred.`

Internally incoherent as written: six conductors *cannot* carry a ground return
per signal. That is precisely what took it to twelve.

**Stale — `hardware/bom.csv:110` (`PCB-CLUSTER`):**

> every switch-to-chip connection becomes a TRACE and only six conductors leave each board

**Stale — `ROADMAP.md:196`, the M4 verification row:**

> | **Does the chained key loom fit the side channel?** | M4 | Six conductors per hop rather than the 32–44 the tail-mounted alternative needed — much easier, but still check it against the real cavity section…

The fit check is booked against half the real ribbon width.

**Half-stale — `hardware/controller/carrier.md:471-474`:**

> **Six conductors is the signal count, not the
> conductor count.** Whether this connector is 6-way or 10-way is a decision this
> page cannot take alone — see *Still open*.

The first sentence is the correct clarification; the second is stale — it is
neither 6-way nor 10-way, it is 2×6/12-way, and the same page says so at
`carrier.md:395` and `carrier.md:856-857` ("**Two items were decided rather than
left open.** `J-CHAIN` is **2×6**").

*Borderline, not reported as stale:* `cluster-boards.md:20` "six signals leave
the board instead of twenty-one" — correct as a *signal* count.

---

## D4 — Eight `J-CHAIN` connectors across five boards. `bom.csv` says five, in the same file that says eight. **High**

**Current truth** — `hardware/bom.csv:93` (`J-CHAIN`), qty **8**:

> EIGHT of them, not five: the chain is four hops and SER/QH are point-to-point rather than bus, so every cluster board but the last carries an IN and an OUT. Carrier 1, right_thumb 2, right_hand 2, left_thumb 2, left_hand 1

matched by ADR 0001:249-256, `carrier.md:418-422` and `cluster-boards.md:231-236`.

**Stale — `hardware/bom.csv:72` (`WIRE-LOOM`), 21 rows above:**

> chained through each cluster board in turn rather than starred, so five connectors must match: one on the carrier and one per cluster board.

Two rows of the same CSV give 5 and 8 for the same quantity. `WIRE-LOOM` is the
row a loom builder reads.

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:136`,
against line 252 of the same ADR:**

> | Hand-terminated joints | **~4 connectors** | **~46 individual wires** |

versus `docs/decisions/0001-mcu-and-board-partitioning.md:250-256`:

> **Eight connectors have
>    to match, across five boards**: … carrier 1, RT 2, RH 2, LT 2, LH 1, with four ribbon
>    assemblies between them.

Four ribbon assemblies means **eight IDC terminations**, not four. The
hand-joint count is the headline number the per-cluster topology was won on
(D14) and it is understated 2× in the comparison table.

---

## D5 — 2.2 kΩ / 100 Ω / 47 nF. ADR 0009 still specifies 10 kΩ / 100 Ω / 10 nF. **High**

**Current truth** — `docs/decisions/0001-mcu-and-board-partitioning.md:216-219`:

> **Per switch position: 2.2 kΩ to 3V3, 100 Ω in series, 47 nF to ground**, on the
> **cluster board**, at the register inputs

with `bom.csv:90` `R-KEY-PU` = 2k2 and `bom.csv:92` `C-KEY` = 47nF.

**Stale — `docs/decisions/0009-enclosure-construction.md:473-476`**, in the
"Things that are free now and impossible later" list:

> **Fit the key input networks.** A 74x165's parallel inputs have no internal
> pull-up, so without them every key input floats in a channel shared with 12 V
> LED power and 800 kHz data — 10 kΩ, 100 Ω and 10 nF per switch position on the
> cluster boards (ADR 0001).

Two faults in one sentence:

1. **Values.** 10 kΩ and 10 nF are the pre-reversal pair.
2. **The refuted coupling framing survives.** "a channel shared with **12 V LED
   power**" is the aggressor ADR 0001 explicitly retired —
   `docs/decisions/0001-mcu-and-board-partitioning.md:145-147`:

   > - **There is no 12 V edge.** The WS2815 rail is held up by 470–1000 µF and its
   >   LED current is PWM'd at ~2 kHz (ADR 0014). The fast aggressor is the **data
   >   line, at 5 V**.

   ADR 0009 is an *accepted* ADR presenting the refuted aggressor as live
   justification for an unretrofittable part.

**Stale — `hardware/bom.csv:91` (`R-KEY-SER`)**, the row directly above `C-KEY`:

> With C-KEY: press is ~1us (100R x 10nF) so it stays instant, release is ~93us (10k x 10nF) which is a free hardware debounce. Also bounds injected current

versus `hardware/bom.csv:92` (`C-KEY`), the next line:

> 47nF with the 2k2 pull-up keeps tau at ~103us, the same release filter as the old 10k/10nF pair.

`R-KEY-SER` cites the exact `10k × 10nF` pair that the row beneath it exists to
correct, and ADR 0001:230-234 explicitly says those figures were retired:

> Earlier versions of this line read "~1 µs" and "~93 µs". Those were the
> 10 kΩ/10 nF pair against LVC thresholds and both parts of that changed.

The correction was applied to `C-KEY` and not to its neighbour.

---

## D6 — `R-KEY-PU` is qty 24. ADR 0001 and `carrier.md` still say 21. **High**

The three genuinely free bits (22, 23, 31) need pull-ups too; leaving them off
is the exact ADR 0001 fix-6 fault and is unretrofittable.

**Current truth** — `hardware/bom.csv:90` (`R-KEY-PU`), qty **24**:

> TWENTY-FOUR: one per switch position including the 3 spare-switch bits, PLUS one each for the 3 genuinely free bits (22, 23, 31) which the first cluster-board draft left floating - the exact ADR 0001 fix-6 fault, and unretrofittable

and `hardware/controller/cluster-boards.md:430` component table: `R-KEY-PU … **6** | **6** | 6 | 6` → **24, not 21**.

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:217-219`**, the
ADR that owns the part:

> Twenty-one sets across the
> four boards, so the three reserved spare-switch bits are covered too.
> (`R-KEY-PU`, `R-KEY-SER`, `C-KEY`; values per `bom.csv`.)

21 is right for `R-KEY-SER`/`C-KEY` and wrong for `R-KEY-PU`. **The 21 → 24
decision appears nowhere in any ADR.** It lives only in `bom.csv` and
`cluster-boards.md`. Combined with D2 (fix 6 still says "five genuinely free"),
ADR 0001 currently cannot be used to derive the correct pull-up count at all.

**Stale — `hardware/controller/carrier.md:406-408`:**

> `   3V3  ───────[F-CHAIN, see below]─────────► 10  3V3     → 21 pull-ups,`
> `                                              11  spare      4 × VCC, 4 × 100 nF`

This also under-books the 3V3 load the same page derives in §2.

---

## D7 — 119.9 µs release / 5.92 µs press. ADR 0001, `bom.csv` and `cluster-boards.md`'s own prose still carry 125/5.7. **High**

**Current truth** — `hardware/controller/cluster-boards.md:156-157`:

> | Release, τ = 2.2 kΩ × 47 nF | 103 µs; crosses `V_IH` at **119.9 µs** |
> | Press, τ = 100 Ω × 47 nF | 4.7 µs; crosses `V_IL` at **5.92 µs** — 42× inside the 250 µs scan |

(Independently derived twice in the 2026-09-21 review — `A1-cluster-boards.md:97-99`,
`D1-arithmetic.md:155-156` — the difference is that the node starts at the
pressed level 0.1435 V, not 0 V.)

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:225-226`:**

> | Release, τ = 2.2 kΩ × 47 nF | 103 µs; crosses `V_IH` at **125 µs** |
> | Press, τ = 100 Ω × 47 nF | 4.7 µs; crosses `V_IL` at **5.7 µs** — 44× inside the 250 µs scan |

**Stale — `hardware/bom.csv:92` (`C-KEY`):**

> Press crosses HC165's VIL (0.99V at 3.3V) in ~5.7us, so 'press is instant' survives - 44x margin against the 250us scan period. Release crosses VIH (2.31V) at ~125us.

**Stale — `hardware/controller/cluster-boards.md:163-164`**, nine lines below
its own corrected table:

> The 125 µs release filter is half a scan period and costs
> nothing musically; note-off is filtered in firmware anyway.

The page that carries the correct figure contradicts itself in prose.

Also stale in the same family: `bom.csv:91` `R-KEY-SER`'s "~1 µs / ~93 µs" (D5).
The "~1.4 µs / 176×" pair is **gone everywhere** — verified (§V7).

---

## D8 — The chain draws 25.8 mA at play rate. ADR 0005 calls it "microamps". **High**

ADR 0005 is the power authority and its 3V3 description predates the
10 kΩ → 2.2 kΩ change by three orders of magnitude.

**Current truth** — `docs/decisions/0001-mcu-and-board-partitioning.md:227-228`:

> | Static | **1.43 mA** per closed key; 18 closed = **25.8 mA** |

and `hardware/controller/carrier.md:345-356`, which accepts the consequence:

> 18 keys closed           = 25.8 mA step on the ADC's reference
> at an LDO load regulation of ~0.3 % per 100 mA [from memory]: 0.077 % = 3.2 LSB

**Stale — `docs/decisions/0005-power-architecture.md:202-204`:**

> **3.3 V does not need its own converter.** The loads on it are the shift register
> chain (microamps), the ADC (milliamps) and pull-ups, all comfortably inside the
> headroom of the real-time board's onboard regulator.

and the rail diagram at `0005:197-200` lists `74HC165 chain`, `breath ADC`,
`I2C pull-ups` with no key-pull-up branch at all. The 25.8 mA step — the
largest 3V3 load in the instrument, and the one that lands on the MCP3202's
voltage reference — appears in no ADR 0005 load table. The conclusion ("does
not need its own converter") may still hold, but it is currently supported by a
number that is wrong by ~1000×, and ADR 0005 is where a reader goes to check
whether a separate pull-up rail is affordable — which `carrier.md:358-361` names
as the fix if the 3.2 LSB is ever to be removed.

---

## D9 — The chain reads in ~32 µs at 1 MHz. The latency budget books it at 16 µs in one place and <10 µs in another. **High**

**Current truth** — `docs/decisions/0001-mcu-and-board-partitioning.md:369-372`:

> Full chain reads in
> ~32 µs at 1 MHz, about 13 % of a 250 µs loop period. **1 MHz is the design
> rate and the chain should not be pushed much past it**

and `hardware/controller/carrier.md:574`: "**1 MHz, and not much more**".

**Stale — `docs/reference/latency-budget.md:146-148`**, the arithmetic that
decides whether the loop closes:

> pass costs ADC 24 µs + key chain 16 µs + six DAC channels at 2 MHz 96 µs =
>    **136 µs**, against a 125 µs period at 8 kHz. At 4 kHz it is 136 µs of
>    250 µs — 54 % duty, with room for the loop to do work.

16 µs is 32 bits at **2 MHz**, a rate ADR 0001 explicitly warns against. At the
design rate the pass is **152 µs / 250 µs = 61 % duty**, not 54 %. The
2026-09-21 review found exactly this
(`.../hardware-and-standards-review/VERIFIED.md:210-212`) and it has not been
applied.

**Stale — `docs/reference/latency-budget.md:96`**, the key-path table on the
same page:

> | 74HC165 chain read | < 10 µs via SPI DMA |

A third figure, implying >3.2 MHz. One page gives two numbers, neither of which
is the ADR's.

---

## D10 — Note-on debounce: "fire immediately" vs "two consecutive agreeing samples". **Medium**

**Current truth** — `docs/decisions/0001-mcu-and-board-partitioning.md:313-317`,
listed as one of "Two firmware rules the chain depends on":

> **Require two consecutive agreeing samples before a note-on.** At the 4 kHz loop
> rate that is 250 µs of added latency — inaudible, and a twentieth of the 5 ms
> budget. … This keeps the asymmetric debounce's fast attack while
> removing its single-sample credulity.

**Stale — `firmware/README.md:25-28`**, under "Architecture constraints …
not negotiable":

> - **Asymmetric key debounce** — fire immediately on press, filter only the
>   release.

**Stale — `docs/reference/latency-budget.md:97`:**

> | Debounce (press) | 0 — fire immediately |

**Stale — `ROADMAP.md:44`:**

> | E4 | Key scan | 74HC165 chain reads all switches; debounce asymmetric (instant press, filtered release) |

Three corpus documents book 0 µs of press debounce; the ADR books 250 µs. The
250 µs is also missing from the key-path total in `latency-budget.md:94-101`.
The rule exists specifically because ADR 0009:466-468 and ADR 0001:196-199 both
argue that a single corrupted word becomes a spurious note-on at full velocity —
so the omission removes the mitigation from the documents firmware will actually
be written from.

Related gap: **`firmware/README.md` never mentions the marker pattern at all.**
ADR 0001:340-342 and `cluster-boards.md:367-368` both say "firmware has to be
told the pattern". It has not been written down on the firmware side. See §N7.

---

## D11 — 66 network passives, not 63. **Medium**

The 21 → 24 pull-up change (D6) moved the total and no derived figure followed.
`cluster-boards.md` contradicts its own component table.

**Current truth** — `hardware/controller/cluster-boards.md:430-432`
component table: `R-KEY-PU` 6+6+6+6 = **24**, `R-KEY-SER` 5+4+6+6 = **21**,
`C-KEY` 5+4+6+6 = **21**. Total **66**.

**Stale — `hardware/controller/cluster-boards.md:438-440`**, nine lines below
that table:

> **Totals across the four boards:** 4 ICs, 4 decoupling caps, 18 fitted switches
> in 21 networked positions, 63 network passives, 7 chain connectors

**Stale — five further sites, all reading 63:**

- `docs/decisions/0001-mcu-and-board-partitioning.md:138` — "| Carrier area | as designed | **+41 %**: 4 ICs and 63 passives |"
- `docs/decisions/0001-mcu-and-board-partitioning.md:162` — "the tail version added 4 ICs and 63 passives"
- `docs/decisions/0013-two-mcu-split.md:241` — "keeps 4 ICs and 63 passives off a carrier that is short of room"
- `hardware/controller/carrier.md:754` — "4 ICs and 63 passives moved to `PCB-CLUSTER`"
- `hardware/bom.csv:69` (`PCB-CARRIER`) — "the registers and their 63 passives live on the cluster boards"; `hardware/bom.csv:110` (`PCB-CLUSTER`) — "it keeps 63 passives off the carrier"

(`hardware/bom.csv:113` `R-LED-SER`'s "against 63 on the victims" is the same
figure, reached from the lighting side.)

Low physical risk — `bom.csv` quantities are individually correct — but this is
the project's signature failure mode: a count changed in one row and every
derived total kept the old value.

---

## D12 — `cluster-boards.md` §3 says pin 6 `SER` is not a bus, and draws it as one. **Medium**

**`hardware/controller/cluster-boards.md:200-220`**, the connector diagram,
buses `SER` straight through:

> `    6 SER   ─────────────┼──┼──┼──┼──┬──────────────────► 6 SER`

and `LK-SER` position B depends on it: "SER comes from the IN pin 6
passthrough, which reaches all the way back to the carrier."

**Contradicted at `hardware/controller/cluster-boards.md:231`, same section:**

> **`QH` and `SER` are not a bus, and that is what forces two connectors.**

and at `cluster-boards.md:228-229`, which lists the bus and omits `SER`:

> **`SCK`, `SH/LD`, `3V3` and the five grounds are a straight bus** — IN to OUT,
> 1:1, so a plain straight-through ribbon works between any two boards.

`carrier.md:424-425` has it right:

> Pin 6 SER is the exception: it IS a pass-through, riding every hop to reach
> the far device's serial input.

Only `QH` (pin 8) is point-to-point. Copper detail on an unretrofittable board,
stated two ways in one section.

---

## D13 — ADR 0001's hop breakdown sums to 13. **Medium**

**`docs/decisions/0001-mcu-and-board-partitioning.md:135`:**

> | Conductors down the body | **12 per hop** — 6 signals-and-supply, 5 grounds, 2 spare | 32–44 |

6 + 5 + 2 = **13**. The pinout everyone else carries —
`GND SCK GND SH/LD GND SER GND QH GND 3V3 spare spare` (ADR 0001:250 itself,
`bom.csv:72`, `bom.csv:93`, `carrier.md:395-409`, `cluster-boards.md:196-197`) —
is **4 signals + 1 supply (5), 5 grounds, 2 spare = 12**. "6
signals-and-supply" is the error; the headline 12 is right. Flagged because this
is the one table a reader uses to check the 12.

---

## D14 — What the tail topology would have cost: 32–44, ~46, 35, or 21. **Medium**

Four incompatible numbers for the same superseded quantity, all still live, all
used as the justification for the current topology.

- `docs/decisions/0001-mcu-and-board-partitioning.md:135` — "| … | 32–44 |" (conductors)
- `docs/decisions/0001-mcu-and-board-partitioning.md:136` and `:159` — "**~46 individual wires**" / "about 46 wires"
- `hardware/bom.csv:72` (`WIRE-LOOM`) — "the tail-mounted alternative's 32-44 conductors and ~46 hand-terminated joints"
- `hardware/bom.csv:110` (`PCB-CLUSTER`) — "~46 individual wires for the tail-mounted alternative"
- `ROADMAP.md:196` — "the 32–44 the tail-mounted alternative needed"
- `hardware/controller/carrier.md:808-810` — "That was the tail-register arithmetic — **35 conductors of key loom, one per switch**."
- `hardware/controller/cluster-boards.md:20` — "six signals leave the board instead of **twenty-one**"

`carrier.md`'s "35 … one per switch" is self-refuting: there are 21 switch
positions and 18 fitted switches, not 35. `cluster-boards.md`'s 21 is the only
one consistent with "one per switch position". Nothing in the corpus derives
32–44 or 46. See §N4.

---

## D15 — `V_IL` = 0.8 V is the LVC threshold, on a part that is now HC. **Low**

**`docs/decisions/0001-mcu-and-board-partitioning.md:154-155`:**

> Corrected, an unfiltered wire sees **1.36 V**, landing at 1.94 V against a
> 0.8 V threshold.

**`hardware/bom.csv:92` (`C-KEY`):**

> an unfiltered wire sees 1.36V, which does not cross a 0.8V threshold

ADR 0001 gets it right fifty lines later, at `0001:207-209`:

> nowhere near `V_IL` on either family (0.8 V for LVC, 0.99 V for the
> 74HC165 actually fitted)

The conclusion is unchanged (1.94 V clears both 0.8 V and 0.99 V), so this is a
cosmetic residue of the LVC → HC change rather than a design error. Reported
only because it is the last surviving unqualified LVC number in the domain.

---

## D16 — 1.43 mA or 1.5 mA per closed key. **Low**

`docs/decisions/0001-mcu-and-board-partitioning.md:227`, `carrier.md:351` and
`cluster-boards.md:160` all give **1.43 mA**; `hardware/bom.csv:90`
(`R-KEY-PU`) gives "1.5mA per PRESSED key". 3.3 / 2300 = 1.435 mA, so 1.43 is
right. Same row compares that current "against a 360mA budget", which is
ADR 0005's **+12 V** typical-play figure (`0005:158`) — a 3V3 load measured
against a 12 V budget. Rounding and a category error; no consequence.

---

## §N — Facts asserted but never derived

**N1. "ADR 0001 has that input terminated at the far device" — ADR 0001 says no
such thing.** Three corpus documents attribute the specification to it:

- `hardware/controller/carrier.md:438-440` — "**`CLK INH` is tied low and `SER` is terminated at the far device** — both on the cluster boards, not here `[repo] 0001`."
- `hardware/controller/carrier.md:424-428` — "ADR 0001 has that input *"terminated at the far device"*, which would make this conductor redundant."
- `hardware/controller/cluster-boards.md:252-254` — "`R-SER-TERM` holds the input high if nothing drives it, which is the tied-off case ADR 0001 specified."
- `hardware/bom.csv:112` (`R-SER-TERM`) — "which is the tied-off case ADR 0001 specified"

ADR 0001's only statement in the area is fix 6 at `0001:289-290`: "**Tie
`CLK INH` low at all four devices, and pull every unused parallel input.**" —
*parallel* inputs, not `SER`. Searched ADR 0001 for `SER` / "far device" /
"serial input": no such specification exists. `R-SER-TERM` (a proposed BOM row,
`bom.csv:112`) and the whole self-test-versus-tie-off argument rest on a
requirement that was never written. Either ADR 0001 should state it or the three
citations should stop claiming it does.

**N2. "~26 pF of loom plus connectors".** Asserted twice —
`docs/decisions/0001-mcu-and-board-partitioning.md:180` and `:305` — and used to
conclude "the drive is ample". No derivation anywhere in the corpus: no
capacitance per metre, no connector allowance, no input-capacitance figure for
the four HC165s on the line. This is the number that decides whether HC's drive
is sufficient at 1 MHz over 265 mm, i.e. the number the whole LVC → HC reversal
rests on.

**N3. "+41 % carrier area" and "~82 % covered".** `0001:138`, `bom.csv:69`
(`PCB-CARRIER`). One of the three counts the per-cluster topology was won on
(`0001:159-163`). No area arithmetic exists in the corpus; `bom.csv:69`
attributes the 82 % to "a review" without naming it.

**N4. "32–44 conductors" and "~46 individual wires".** See D14. Neither is
derived anywhere, and they coexist with 35 and 21 for the same quantity.

**N5. `carrier.md` argues against a figure that no longer exists.**
`hardware/controller/carrier.md:806-808`:

> `[calc]`, built from the repo's own rules — **not** the "~23" that ADR 0001,
> `WIRE-LOOM` and the ROADMAP all carry `[repo]`

and again at `carrier.md:808-814` ("the repo's figure is approximately right
after all"). Grepped all three: **"~23" appears in none of ADR 0001,
`bom.csv` `WIRE-LOOM`, or `ROADMAP.md`.** The citation is dangling — either the
figure was removed from those documents without updating the page that argues
with it, or it was never there.

**N6. The 74HC165 pin map and its 3.3 V thresholds.**
`cluster-boards.md:88-104` marks the whole pin map `[from memory]` and lists it
under *Still open* (`cluster-boards.md:460-463`): "Every number in this page's
timing table rests on `V_IH` = 0.7 × VCC and `V_IL` = 0.3 × VCC `[from
memory]`." But **ADR 0001:222-223 states the same thresholds flat, with no
uncertainty marker**: "`[calc]`, at 3.3 V into 74HC165 thresholds (`V_IH`
2.31 V, `V_IL` 0.99 V)". The ADR presents as settled what the schematic page
correctly presents as unverified. Every figure in D7 inherits this.

**N7. The marker pattern has never been written down on the firmware side.**
ADR 0001:340-342 — "The bit-by-bit assignment and levels are in
`hardware/controller/cluster-boards.md` §4" — and `cluster-boards.md:367-368` —
"firmware has to be told the pattern." `firmware/README.md` contains no
reference to the marker, the error counter, the hold-previous-frame rule, or the
two-agreeing-samples rule (D10). `config/key-layout.yaml` is declared the
single source of truth for "74HC165 bit mapping" (`key-layout.yaml:6`,
ADR 0010:16-19) but carries **no bit numbers and no marker levels** — it points
at `cluster-boards.md` §4 in a comment (`key-layout.yaml:129-131`). The
allocation that generated firmware is supposed to consume by construction is
prose in a schematic page.

---

## §V — Facts I verified consistent

**V1. Register location.** No surviving "all four on the carrier", "four
ribbons" as a live topology, or "key clusters — switches and nothing else".
Every mention of the tail-register topology is explicitly marked superseded:
ADR 0001:70-76, ADR 0013:238-241 ("~~The shift registers~~ — **no.**"),
ROADMAP.md:54, `bom.csv:8` (`U-KEYS`, "ONE PER CLUSTER BOARD"), `bom.csv:69`,
`bom.csv:110`, `carrier.md:3-6`, `carrier.md:754`, `cluster-boards.md:17-22`.
`carrier.md:830` mentions "four ribbons" only as the rejected alternative. Clean.

**V2. The part is 74HC165.** ADR 0001:172-185 and :294-306, `bom.csv:8`,
`cluster-boards.md:119-125`, ROADMAP.md:44, `latency-budget.md:96`,
ADR 0005:197, ADR 0008:108, `key-layout.yaml:6`. No live `74LVC165` anywhere;
every LVC mention is a marked reversal or a named fallback. (Residual LVC
*threshold* at D15.)

**V3. The 32-bit allocation.** `cluster-boards.md:270-275` (allocation table),
`carrier.md:506-512`, `key-layout.yaml:118-121` and `:137-140` all agree:
18 fitted + 3 reserved switches + 8 marker + 3 free = 32; 14 spare = 8 + 3 + 3.
Per-device spare counts in `key-layout.yaml:118-121` (5/2/4/3) reconcile exactly
with `cluster-boards.md` §4's per-device assignment.

**V4. The marker levels and the `left_thumb` flip.** `cluster-boards.md:316-321`
gives RT B(6)=1 A(7)=0, RH B(14)=0 A(15)=1, LT D(20)=0 C(21)=1, LH C(29)=0
B(30)=1 — matching the decided post-flip pattern, and the bit-order read-out
"`1 0 · 0 1 · 0 1 · 0 1`" (`cluster-boards.md:323`) is arithmetically correct
against the `H`-first ordering at `cluster-boards.md:110-116`. The flip
rationale and its exhaustive derivation are correctly attributed to
`docs/review/2026-09-21-hardware-and-standards-review/C1-break-key-chain.md`
(verified: C1:57, :105, :109, :142, :610). The old repeating-nibble pattern
`1 0 · 0 1 · 1 0 · 0 1` survives only as a marked correction.

**V5. `J-CHAIN` pinout.** `GND SCK GND SH/LD GND SER GND QH GND 3V3 spare spare`
is byte-identical across ADR 0001:250, `bom.csv:72`, `bom.csv:93`,
`carrier.md:395-409` and `cluster-boards.md:196-197`. Boxed and keyed at all
eight positions, stated in all of them.

**V6. Chain order, and the proposed reorder.** `RT → RH → LT → LH` is the live
order in `key-layout.yaml:144-148`, ADR 0001:267-270, `bom.csv:72` and
`carrier.md:431-434`. The reorder `RT → RH → LH → LT` appears in exactly three
places — `cluster-boards.md:67`, `:331`, `:451` — and is labelled **"Proposed,
not applied"** (`cluster-boards.md:80`) in all of them, with the bit-group
consequence stated twice (`cluster-boards.md:82-84`, `:453-455`). **Nothing in
the corpus assumes it.** The §4 allocation table and the marker levels are
written against the as-applied order, correctly. The skew magnitude ("~0.5 ns
against tens of nanoseconds", "a few percent of hold margin") is consistent
between ADR 0001:272-278, `key-layout.yaml:122-129` and `cluster-boards.md:70-74`,
including the retired "hold-margin violations" honesty marker being flagged as
such in both.

**V7. The refuted coupling model is properly quarantined** — with one
exception. `12 V LED edge`, `~15 pF`, `180 pC`, `Q/C`, `4.5 V` and `18 mV`
appear at ADR 0001:141-155 and :204-210, `carrier.md:482-492`,
`cluster-boards.md:166-176` and `bom.csv:92` — in every case as an explicitly
refuted model, with the honest 1.36 V / 1.94 V figure alongside. The "~1.4 µs /
176×" pair is gone from the corpus entirely. The one exception is ADR 0009:474-475
(D5), which still presents "12 V LED power" as live justification.

**V8. New BOM rows all exist.** `J-CHAIN` (`bom.csv:93`, qty 8), `LK-SER`
(`:111`, qty 4), `R-SER-TERM` (`:112`, qty 1), `R-CHAIN-SER` (`:94`, qty 3),
`U-TVS-CHAIN` (`:95`, qty 1), `F-CHAIN` (`:96`, qty 1). Each carries the
proposing page and a status. `LK-SER` positions (A on three boards, B on the
chain-end board) agree between `bom.csv:111` and `cluster-boards.md:211-220`
and `:434`. `J-CHAIN` per-board quantities (LH 1, LT 2, RH 2, RT 2 = 7, plus
carrier 1 = 8) reconcile across `bom.csv:93`, `cluster-boards.md:433`,
`cluster-boards.md:438-440` and `carrier.md:418-421`.

**V9. Secondary chain facts.** SPI3 dedicated to the chain because `QH` has no
output-enable: ADR 0001:103-118, ADR 0003:226-228, ADR 0007:189-190,
ADR 0008:82, ADR 0013:46-47 and :62 — all agree, including the GPIO
assignments (IO38 SCK, IO40 MISO, IO7 latch) against `carrier.md:398-404`.
`C-DECOUPLE-165` qty 4, at the package, on the cluster board: ADR 0001:287-288,
`bom.csv:43`, `cluster-boards.md:96-99`, `:428`. `CLK INH` tied low and
`QH_bar` left open: ADR 0001:289, `bom.csv:8`, `cluster-boards.md:100-103`.
`R-TERM-CHAIN` deleted and not restored, with `R-CHAIN-SER` correctly
distinguished as a different job: ADR 0001:180-185, :280-286, `bom.csv:94`,
`carrier.md:755`. Cluster geometry (LH upper/265 mm, RH lower/115 mm):
ADR 0013:146-147, :179-180, `key-layout.yaml:68`, `cluster-boards.md:44-49`.
The 1.54 kHz pole → 54 dB at 800 kHz checks out (`20·log10(800/1.54) = 54.3`).

---

## What I would fix first

1. **ADR 0010:172-174 and `carrier.md:514, :520, :863`** — the marker/free-bit
   counts (D1, D2). Unretrofittable copper, and ADR 0010 gates the plate DXF.
2. **`key-layout.yaml:131`** — a file that contradicts its own field is the
   single most dangerous artefact in this domain, because it is the declared
   source of truth for generated output (D2).
3. **ADR 0001:291 (fix 6) and ADR 0001:217-219** — until these say "three free
   bits" and account for 24 pull-ups, no ADR supports the BOM (D2, D6).
4. **ADR 0009:473-476** — wrong values *and* the refuted aggressor, in an
   accepted ADR's "impossible later" list (D5).
5. **`bom.csv:91` and `bom.csv:72`** — two rows contradicting their own
   neighbours in the same file (D5, D4).
6. **`latency-budget.md:96, :146`** — the loop-duty arithmetic is built on a
   clock rate ADR 0001 forbids (D9).
