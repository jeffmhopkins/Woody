# S11 — Firmware-facing facts: staleness audit

**Date:** 2026-09-21
**Slice:** everything the hardware promises firmware, and everything firmware is
told to assume.
**Corpus audited:** `firmware/README.md`, `config/key-layout.yaml`,
`docs/reference/latency-budget.md`, `docs/decisions/**`, `hardware/**`,
`ROADMAP.md`.
**Read but not reportable:** `docs/review/**`, `docs/log/**`, `docs/research/**`.

Nothing was edited except this file.

## Why this slice is the dangerous one

The firmware is a port from a working 2021 project onto hardware that does not
exist yet. Every hardware fact firmware depends on is a fact nobody has measured,
and the corpus has been revised hard in the last two days: the marker went 6 → 8
bits, `left_thumb`'s marker pair was flipped, the registers moved from the tail
back to the cluster boards, the mod stage went from four resistors to two (which
moved the shared offset from 2.500 V to 3.3333 V), a seventh DAC channel was
deleted, and **the module's frame watchdog was deleted entirely**. Each of those
left a trail of sentences behind, and several of the survivors are the sentence a
firmware author would actually be reading.

Indexed by the fact, not by the file.

---

## Ranked summary

| # | Fact firmware depends on | Rank |
|---|---|---|
| F1 | The mod-channel offset (`ch 7`) update cadence: once at boot vs every pass | **Showstopper** |
| F2 | The mod-channel transfer function and the value written to `ch 7` (2.5 V vs 3.3333 V) | **Showstopper** |
| F3 | Note-on requires two consecutive agreeing samples | **Showstopper** |
| F4 | Key-chain read cost: 10 µs / 16 µs / 32 µs | **Showstopper** (budget), High (schedule) |
| F5 | ADC conversion cost: 24 µs vs 50–200 µs, and what 200 µs means | **Showstopper** |
| F6 | Umbilical SPI clock: 2 MHz vs 1 MHz | **High** |
| F7 | Per-device clock for the MCP3202 on the shared host (0.9 MHz) | **High** |
| F8 | The trigger that zeroes the DAC — the watchdog no longer exists | **High** |
| F9 | Marker bit positions and levels; where they live machine-readably | **High** |
| F10 | `key-layout.yaml` contradicts its own fields on the spare-bit split | **High** |
| F11 | `carrier.md` still says the marker is six bits and undecided | **High** |
| F12 | ADR 0010 still says 4–6 marker bits, 8–10 remaining | **High** |
| F13 | Display core / SPI host — `firmware/README.md` still allocates them on the real-time board | **High** |
| F14 | LED blank-at-boot: hardware now depends on it, firmware is not told | **High** |
| F15 | Lighting current clamp (~3 W, proportional scaling) not in `firmware/` | **Medium** |
| F16 | Latency-budget totals do not match their own rows (632/662; 2.9–3.1 vs 2.68–2.93) | **Medium** |
| F17 | ADR 0003's own latency table is entirely superseded and still present | **Medium** |
| F18 | ADR 0003 books seven DAC channels | **Medium** |
| F19 | `LDAC` handling and the absence of atomic update | **Medium** |
| F20 | `IO33` — chain `SER` drive — is "spare" in the pin budget | **Medium** |
| F21 | Auto-zero rule stated two ways; not stated in `firmware/` at all | **Medium** |
| F22 | Release-filter figures disagree (5.7/5.92 µs, 119.9/125 µs); BOM row is stale | **Low** |
| F23 | Chain read time and anti-alias τ omitted from the budget that chose 4 kHz | **Medium** |
| G1–G9 | Facts no document states at all — see *Gaps* | **Showstopper**→Medium |

---

## 1. The bit map

### F9 — Do all four sources agree, bit for bit?

**On the allocation itself: yes, and this is the good news.** I checked every bit.

`hardware/controller/cluster-boards.md` §4:

> | Device | Bits | `H` | `G` | `F` | `E` | `D` | `C` | `B` | `A` |
> |---|---|---|---|---|---|---|---|---|---|
> | `right_thumb` | 0–7 | RT1 | RT2 | RT3 | sw+ | sw− | sw? | **M** | **M** |
> | `right_hand` | 8–15 | RH1 | RH2 | RH3 | RH4 | RH5 | RH6 | **M** | **M** |
> | `left_thumb` | 16–23 | LT1 | LT2 | LT3 | LT4 | **M** | **M** | free | free |
> | `left_hand` | 24–31 | LH1 | LH2 | LH3 | LH4 | LH5 | **M** | **M** | free |

and its levels table:

> | `right_thumb` | `B` | 6 | **1** | | `A` | 7 | **0** |
> | `right_hand` | `B` | 14 | **0** | | `A` | 15 | **1** |
> | `left_thumb` | `D` | 20 | **0** | | `C` | 21 | **1** |
> | `left_hand` | `C` | 29 | **0** | | `B` | 30 | **1** |
> Read in bit order the marker is `1 0 · 0 1 · 0 1 · 0 1`.

These are self-consistent: the bit numbers land on the `M` cells of the
allocation table, and the level string matches the bit order. The `left_thumb`
flip is applied consistently (the note records the pre-flip pattern as
`1 0 · 0 1 · 1 0 · 0 1`, and 20/21 now read `0 1`).

`config/key-layout.yaml`'s per-cluster counts also reconcile exactly:

> ```
> chain:
>   - cluster: right_thumb  # bits 0-7   — 3 used, 5 spare — nearest the MCU
>   - cluster: right_hand   # bits 8-15  — 6 used, 2 spare
>   - cluster: left_thumb   # bits 16-23 — 4 used, 4 spare
>   - cluster: left_hand    # bits 24-31 — 5 used, 3 spare — SER end of the loom
> ```

3+5, 6+2, 4+4, 5+3 = 8 each; and §4's per-device rows are 3 keys/3 spare-switch/
2 marker, 6 keys/2 marker, 4 keys/2 marker/2 free, 5 keys/2 marker/1 free. They
agree device by device.

`bit 0` is defined identically in all three places — ADR 0001 (*"`bit 0` means the
first bit clocked out — the device nearest the MCU"*), `key-layout.yaml`
(*"BIT 0 IS THE FIRST BIT CLOCKED OUT - the device nearest the MCU"*), and
`carrier.md` §3 (*"bit 0 is the first bit clocked out = QH of right_thumb"*) —
and `cluster-boards.md` §1 closes the last degree of freedom:

> **Bit order inside the device is `H` first, then `G F E D C B A`.**

**So the allocation is coherent. What is not coherent is everything that talks
*about* it.** Three of the four sources still describe a six-bit marker, a
five-bit free pool, or an undecided pattern — and two of those three are files a
firmware author is more likely to open than `cluster-boards.md`.

**Rank: High.** Firmware written from §4 is right. Firmware written from anything
else is wrong, and nothing tells the reader §4 wins.

**Where firmware would most likely be written from:** `config/key-layout.yaml`,
because ADR 0010 tells it to — *"`config/key-layout.yaml` is the single source of
truth… **Firmware** — key IDs drive the 74HC165 bit mapping and the fingering
table"* — and that file does not contain the bit map.

---

### F10 — `key-layout.yaml` contradicts its own fields

**Showstopper-adjacent because this is the generator's input file.**

The comment block:

> ```
> # Spare chain bits: 14 total, but NOT all available.
> #   8 are claimed by the marker pattern (ADR 0001) - wiring-only, …
> #   3 are reserved for spare switches: octave up, octave down, hold/preset.
> #   The 5 genuinely free bits are FLOATING CMOS INPUTS and must be pulled -
> #   the exact fault R-KEY-PU exists to fix (ADR 0001).
> ```

8 + 3 + 5 = **16**, against the "14 total" two lines above. And the fields
immediately below say something different again:

> ```
> spare_bits: 14
> spare_bits_marker: 8      # DECIDED 2026-09-21, ADR 0001 - was 6
> spare_bits_switches: 3    # reserved, cutouts required at M3
> spare_bits_free: 3        # was 5; two went to the marker. …
> ```

8 + 3 + 3 = 14 ✓. **The fields are right and the prose beside them is stale** —
the edit that took free from 5 to 3 updated the value and the trailing comment
but not the block above it.

A generator reads the fields, so the artefact is probably right. A human reads
the prose, so the *review* of the artefact is wrong. **Rank: High.**

---

### F11 — `carrier.md` still says the marker is six bits and undecided

`hardware/controller/carrier.md` §3, table, one row:

> | 8 | Marker pattern | **Cluster boards** — hard-wired at the register input. Unretrofittable. **Decided 2026-09-21: 8, not 6** |

and the sentence directly underneath it:

> **Which six bits carry the marker and to what pattern is still undecided, and
> it is now a cluster-board decision** — as is the `H`…`A`-to-switch mapping
> inside each device. Both still have to be settled before *those* boards are
> made, and firmware has to be told about both.

Same page, ten lines apart: decided/eight against undecided/six. The `H`…`A`
mapping is likewise described as unsettled when `cluster-boards.md` §1 settled
it. Two paragraphs later the same page is still costing the *five*-bit free pool:

> **The option worth costing has got cheaper.** Giving the 5 free bits the full
> network too is now 15 passives spread across four boards…

and §3's connector diagram still annotates the 3V3 conductor as feeding
`→ 21 pull-ups`, where `cluster-boards.md` and `bom.csv` now carry **24**
(`bom.csv` `R-KEY-PU`, qty 24: *"one per switch position including the 3
spare-switch bits, PLUS one each for the 3 genuinely free bits (22, 23, 31)"*).

**Rank: High.** `carrier.md` is the page that describes the MCU-side connector, so
it is a likely first stop for someone writing the scan driver, and it tells them
the marker does not exist yet.

---

### F12 — ADR 0010 still books 4–6 marker bits

`docs/decisions/0010-key-layout-as-data.md`:

> - **Four to six of the spare chain bits belong to the marker pattern**
>   (ADR 0001) and are not available for switches. Eight to ten remain, which is
>   more than three.

against ADR 0001:

> **Use 8 of the 14 spare chain bits as a fixed marker pattern. DECIDED,
> 2026-09-21** — this line read "4–6" until then.

ADR 0010 is the ADR that *defines what firmware generates from the layout file*.
It is also the one that was not updated. **Rank: High.**

---

### F13 — ADR 0001's own fix 6 still says five free bits

Inside ADR 0001, fix 6:

> **Tie `CLK INH` low at all four devices, and pull every unused parallel
> input.** … The five genuinely free spare bits are floating CMOS inputs — the
> exact fault `R-KEY-PU` exists to fix.

against the same ADR, forty lines later:

> So the allocation is **6 marker → 8 marker, 5 free → 3 free**, and the 3 that
> remain still get pulled per fix 6.

and the same ADR's key-network paragraph:

> **Per switch position: … Twenty-one sets across the four boards**, so the three
> reserved spare-switch bits are covered too.

— which is the 21-not-24 hole `cluster-boards.md` records as *"the first draft of
this page did not budget these three."* **Rank: Medium** for firmware (it is a
parts count), **High** as a signal that ADR 0001 was edited in one place and not
the other. Firmware's exposure is F9/G4: which bits are permanently high.

---

### F14 — The chain order is proposed-to-change, and the bit map moves with it

`cluster-boards.md` proposes `RT → RH → LH → LT` to save a body crossing, and is
explicit about the consequence:

> **If the order changes, the bit allocation in §4 changes with it** —
> `left_thumb` and `left_hand` swap their eight-bit groups. Decide it before the
> plate DXF is generated, not after.

It is listed under *Still open*. `config/key-layout.yaml` carries the current
order as fact, with no marker that it is contested. The same page also records
that the flipped marker is what makes the two proposals safe together:

> of the **23 wrong chain permutations exactly one passes undetected:
> `RT → RH → LH → LT`** — which is the reorder *this very page* proposes…
> Flipping this one pair kills all 23 permutations and a −5 shift hole while
> keeping all 24 hard faults caught.

**Rank: Medium**, and it is a *scheduling* fact firmware needs: the bit map is not
frozen, and `key-layout.yaml` does not say so. If firmware bakes bit indices
before M3, a loom reorder silently remaps sixteen bits.

---

## 2. The loop budget

**Finding: no single coherent budget exists in the corpus.** There are three,
they disagree on every shared row, and the one that sits in the file named
"latency budget" is arithmetically inconsistent with itself.

### F4 — The key chain read costs 10 µs, 16 µs, or 32 µs

Three figures, three files, all current.

`docs/reference/latency-budget.md`, *Key path* table:

> | 74HC165 chain read | < 10 µs via SPI DMA |

`docs/reference/latency-budget.md`, *Rules that follow*, rule 1:

> Serialised, one pass costs ADC 24 µs + key chain 16 µs + six DAC channels at
> 2 MHz 96 µs = **136 µs**, against a 125 µs period at 8 kHz. At 4 kHz it is
> 136 µs of 250 µs — 54 % duty…

`docs/decisions/0001-mcu-and-board-partitioning.md`, *Consequences*:

> Full chain reads in **~32 µs at 1 MHz**, about 13 % of a 250 µs loop period.
> **1 MHz is the design rate and the chain should not be pushed much past it**…

`hardware/controller/carrier.md` §4:

> ```
> SPI3  keys   32 bits      @ 1.0 MHz =  32.0 µs, concurrent → 13 %
> ```

**32 µs is the only figure with arithmetic behind it** — 32 bits at 1 MHz — and
1 MHz is a *hard* design rate in ADR 0001, not a target. 16 µs is 32 bits at
2 MHz, i.e. the chain clocked at the umbilical's rate, which ADR 0001 explicitly
forbids (*"Clocking it hard is how the transmission-line hazards come back"*).
`< 10 µs via SPI DMA` is not reachable at any permitted clock.

Redone with the real number, rule 1's own serialised sum becomes
24 + 32 + 96 = **152 µs**, not 136 — 61 % duty at 4 kHz. The conclusion (4 kHz,
not 8) survives; the margin statement does not.

**Rank: Showstopper for the budget, High for firmware.** A firmware author
budgeting 10 µs for the scan has under-booked the loop by 22 µs, which is 9 % of
the period, on the one task that has its own SPI host and could otherwise have
been scheduled concurrently.

**Which would firmware be written from?** The latency budget, because
`firmware/README.md` names it as one of two non-negotiable sources:
*"These come from [ADR 0001] and [the latency budget], and they are not
negotiable without revisiting those."* That is the document with the wrong
number in it.

### F23 — And the serialised model contradicts the two-host architecture

Rule 1 sums ADC + keys + DAC **serially**. But ADR 0001 gives the chain its own
host precisely so it does not contend:

> | **SPI3** | 74x165 chain alone | `QH` is always driven; it gets a bus to itself |
> … it has the side benefit the original line was after, since a key scan and a
> CV update no longer contend.

and `carrier.md` §4 books it as *"concurrent → 13 %"* while SPI2 carries
96.0 + 26.7 = **122.7 µs of 250 µs → 49 %**.

So the corpus contains two incompatible scheduling models: a 136 µs serial chain
(latency budget) and a 122.7 µs SPI2 critical path with the scan in parallel
(carrier). They give different answers to "does 8 kHz close" and to how much
slack the loop has. **Rank: Medium**, but it is the fact that decides the task
structure of the whole real-time image.

`carrier.md` §2 also flags a term neither budget carries:

> **τ = 282 µs exceeds the 250 µs loop period, and the note-on threshold is read
> through it.** `latency-budget.md` and ADR 0003 book "SAR ADC conversion
> ~50–200 µs" and no RC term at all `[repo]`. About 5.6 % of the 5 ms budget —
> not fatal, but it belongs in the table that chose 4 kHz over 8 kHz. Found by
> `R10-keyscan-and-adc.md` §B-2 and **still unapplied**.

The anti-alias filter *is* in the breath-digital table (`282 µs`), but not in the
rule-1 sum that chose 4 kHz. **Rank: Medium.**

### F5 — The ADC costs 24 µs or 50–200 µs, and at 200 µs the loop does not close

`docs/reference/latency-budget.md` carries both figures and knows it:

> | SAR ADC conversion | **~24 µs** | 18 clocks at the MCP3202's ~0.9 MHz ceiling
> on 3.3 V. **This row said 50–200 µs**, which is a generic SAR allowance and not
> this part…

> **⚠ This page gave two different figures for the same ADC read, and the gap
> decides whether 4 kHz is buildable.** The table above said 50–200 µs and this
> rule says 24 µs. At 200 µs a pass costs **312 µs against a 250 µs period and
> the loop does not close**; even a mid-range 125 µs leaves no margin.

The budget resolved this in its own favour. **`docs/decisions/0003-breath-sensing-path.md`
did not:**

> | Stage | Time |
> |---|---|
> | Pressure transducer response | **~1 ms** |
> | SAR ADC conversion | ~50–200 µs |
> | SPI to MCU, firmware | < 20 µs |
> | SPI to DAC over the umbilical | ~50 µs |
> | DAC settling | ~10 µs |
> | Op-amp and reconstruction filter | ~160 µs |
> | **Total** | **< 1.5 ms** |

Every row of that table is now superseded: 50–200 µs → 24 µs; ~50 µs → ~96 µs
(six 32-bit words at 2 MHz); ~160 µs → ~82 µs (mod reconstruction at 1.94 kHz per
`mod-channels.md`); and the total `< 1.5 ms` against the budget's `~2.9–3.1 ms`.
ADR 0003's *own prose*, six lines later, contradicts its *own table*:

> The digitised path comes to **~3.1 ms** against a 5 ms target — **about 1.6×,
> not the 10× this sentence used to claim**.

**Rank: Showstopper** (F5) for the 50–200 µs figure specifically, because it is
the number that decides whether the architecture is buildable, and it is still
sitting in an Accepted ADR with no correction marker on the row. **Rank: Medium**
(F17) for the rest of the table.

**Which would firmware be written from?** ADR 0003 is the breath-path ADR; anyone
implementing breath opens it. It is also the document `carrier.md` §2 names as
still carrying the wrong ADC figure.

### F18 — ADR 0003 books seven DAC channels

> | | Payload | SPI clock |
> |---|---|---|
> | **Breath analog, 7 channels at 4 kHz** | **0.90 Mbit/s** | **2 MHz** |
>
> *(The 0.6 MHz this table used to give came from a 2 kHz mod rate and five
> channels; ADR 0006 moved to 4 kHz and **the loop refreshes seven**.)*

Everything else books six. ADR 0004:

> | **Breath analog, 6 channels at 4 kHz** | **0.77 Mbit/s** | **≥1.5 MHz → specify 2 MHz** |
> … (Seven channels were populated until the breath ambient-zero was deleted —
> ADR 0003 — which is slack, not a reason to drop the clock…)

`latency-budget.md`: *"Six channels means *all* the populated ones… The breath
ambient-zero channel that briefly made it seven is deleted (ADR 0003)."*
ADR 0006: *"**Six of eight channels used, two spare.**"*

ADR 0003 is the ADR that deleted the seventh channel and is the one still
counting it. 0.90 vs 0.77 Mbit/s, and 7 × 32 bits at 2 MHz = 112 µs vs 96 µs.
**Rank: Medium** — it inflates the budget rather than deflating it, so firmware
written from it is conservative, not broken.

### F16 — Totals that do not match their own rows

Two, both in `latency-budget.md`.

**(a) 632 vs 662 µs.** The filter rows are:

> | Receive filter, **482 Hz** | **330 µs** |
> | Output RC at the jack, 480 Hz | **332 µs** |

The prose beneath:

> a 500 Hz pole has 318 µs of group delay by definition, and this path has two of
> them. The real figure is **632 µs** — three times what was written…

330 + 332 = **662**. 632 is 2 × 316, i.e. the pre-correction 500 Hz pair, kept
after the corners moved to 482/480 Hz. **Rank: Medium.**

**(b) "~2.9–3.1 ms" against rows giving 2.68–2.93 ms.** The breath-digital table
sums to:

```
2.17 (to sensor output)
+ 0.282  anti-alias
+ 0–0.250 sampling period
+ 0.024  ADC
+ <0.020 SPI to MCU + firmware
+ 0.096  SPI to DAC
+ 0.010  DAC settling
+ 0.082  reconstruction
= 2.684 … 2.934 ms
```

Stated total: **`~2.9–3.1 ms + restrictor`**. The low end is 0.22 ms out and the
high end 0.17 ms out; the stated range does not overlap the computed one for most
of its width. The breath-CV table has a third-order version of the same problem:
rows give 2.842 ms, the total row says `~2.83 ms`, and the prose says
*"**2.80 ms against a 5 ms target**"*.

**Rank: Medium.** It biases pessimistic, so it is a credibility defect rather
than a design defect — but this is the page that claims *"The margin is about
1.6×"*, and a 1.6× claim made of rows that do not add is not a constraint.

**Conclusion for §2: no single coherent budget exists.** The best-arithmetic
version in the corpus is `carrier.md` §4 (SPI2 122.7 µs / 49 %, SPI3 32 µs
concurrent), and it is the one document of the three that firmware is least
likely to be written from.

---

## 3. The SPI contract

### F6 — The umbilical clock is 2 MHz or 1 MHz

ADR 0004 gives both, in two code blocks describing the same cable.

*What goes over the cable*:

> ```
> SCLK, MOSI, CS      SPI to the DAC, ~2 MHz
> MISO                unused today — module ID and presence detect
> ```

*Revised conductor budget*, ninety lines later:

> ```
> +12V      / PWR_GND     power, and the presence signal
> SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
> MOSI      / CS
> BREATH    / AGND        analog, band-limited ~500 Hz, sense return
> ```

Two defects in one block. **The clock is wrong** — the same ADR's own bandwidth
table specifies 2 MHz and shows that anything slower does not close:

> **The 0.6 MHz figure was stale and it did not close.** … Six 32-bit words is
> 192 bits; at 0.6 MHz that is 320 µs against a 250 µs loop period. **The loop
> would simply not have completed.** Five agents found it.
> At 2 MHz the same six words take 96 µs, which is 38 % of the period…

At 1 MHz, six 32-bit words take **192 µs of a 250 µs period** — 77 % duty on
SPI2 before the ADC's 26.7 µs, i.e. 218.7 µs of 250. That is not a loop, it is a
loop that misses on the first jitter event. **And the pairing is also the
superseded one**: `MOSI/CS` share a pair here, which is exactly the arrangement
`digital-and-supervision.md` records as corrected —

> **4. The umbilical pin map is the corrected one.** `SCLK` and `MOSI` now share
> pair (4,5); **`CS` is paired with `DIG_GND` on (7,8)**. Previously `MOSI` and
> `CS` shared a pair with **no return conductor between them**…

ROADMAP E11 and `carrier.md` §4 both carry 2 MHz and the corrected pairing.
`carrier.md` §4: *"| **SPI2** | DAC8568 down the umbilical, **and** MCP3202 …
| **2 MHz for the DAC, 900 kHz for the ADC — not one clock** |"*.

**Rank: High.** 2 MHz wins on weight of evidence and on arithmetic; but the stale
block is in the *conductor budget*, which is the block someone reads when
wiring or configuring the link.

### F7 — The per-device clock for the MCP3202 is stated nowhere firmware reads

`carrier.md` §4, and it says so itself:

> **The MCP3202 cannot run at 2 MHz.** `[from memory]`, via `R10` §B-3: 100 ksps
> at 5 V and 50 ksps at 2.7 V, 18 clocks per 12-bit conversion → **1.8 MHz at
> 5 V, 0.9 MHz at 2.7 V**, and 3.3 V is not specified, so 0.9 MHz is the number
> to design to. ADR 0003, ADR 0004, `latency-budget.md` and `power-entry.md` all
> say "SPI2 at 2 MHz", and ADR 0004 explicitly says that leaves room "for the
> MCP3202 sharing the host" `[repo]`.
>
> ESP-IDF sets `clock_speed_hz` per *device* on a shared host, so this is a
> firmware line and not a part change. **It is written nowhere.**

This is the sharpest single firmware-facing finding in the corpus, and it is
correctly diagnosed on the page that found it and nowhere else. Four documents
say "SPI2 at 2 MHz" without qualification; a driver written from any of them
clocks the ADC at 2.2× its rated ceiling at 2.7 V. There is no readback on the
ADC either, so the failure presents as a breath channel that is subtly wrong.

**Rank: High.** It belongs in `firmware/README.md` and is not there.

Two secondary inconsistencies in the same fact: the clock *count* is 18 in
`latency-budget.md` (*"18 clocks at the MCP3202's ~0.9 MHz ceiling"*, giving
20 µs and a stated ~24 µs with framing) and 24 in `carrier.md`
(*"SPI2 ADC 24 clocks @ 0.9 MHz = 26.7 µs"* — the byte-aligned figure an ESP-IDF
transaction actually produces). Both are plausible; they are not reconciled.
**Rank: Low**, 2.7 µs.

### F1 — DAC channel 7 update cadence: the contradiction is inside `firmware/README.md`

Confirmed, and it is the worst one in the slice because both halves are in the
file firmware is written from, three paragraphs apart.

`firmware/README.md`, *Architecture constraints*:

> - **Refresh everything, every pass. Never write-on-change.** The umbilical is
>   write-only — `MISO` was deleted from the cable (ADR 0004) — so nothing
>   downstream can ever be read back. *With no readback, shared state can only be
>   made safe by being made stateless.* **This is the rule, not an optimisation
>   note**…

`firmware/README.md`, *Why statelessness, specifically*, the very next section:

> The mod channels are `Vout = 4·Vdac − 3·V_ref`, with `V_ref` the shared
> **3.3333 V** from DAC channel 7 — **written once at boot** (ADR 0006).

and then the fix, which is the opposite of what that sentence just said:

> The fix costs nothing. **The latency budget already books six DAC words per
> pass while five are written**, so the sixth channel fits inside a budget that
> was already paid…

**"Written once at boot" is the stale description of the bug, left in the
present tense inside the description of the fix.** It reads as a statement of
current design. A firmware author skim-reading the section that explains why
channel 7 matters is handed the sentence that causes the failure the section
exists to prevent.

The source it cites agrees with the stale half. `docs/decisions/0006-cv-channel-allocation.md`,
*Channels do not share an update rate*:

> | Channel | Rate | Why |
> |---|---|---|
> | Pitch | **4 kHz**, plus **immediate update on note change** | … |
> | Mod 1–4 | **4 kHz** | … |
> | Breath zero offset | continuous, slow | See the auto-zero rule below |
> | **Mod offset** | **written once at boot** | **The shared 2.5 V reference point** |

That row is wrong twice — cadence and value — and it is the row `firmware/README.md`
cites. The table also still lists *"Breath zero offset"* as a channel, which
ADR 0006's own decision table deleted (*"Channel 6 was freed deliberately"*).

Against it, `hardware/module/mod-channels.md` states the correct rule and names
the failure:

> The mirror-image failure is the one the review actually found: firmware
> refreshing the five signal channels after a `CLR` and *not* channel 7, which
> pins the jacks at `4 × Vdac` ≈ **+11.45 V**. That is closed by the
> statelessness rule in `firmware/README.md` — **refresh all six populated
> channels every pass** — and the latency budget already paid for it.

**Rank: Showstopper.** Firmware written to "written once at boot" puts +11.45 V
on four Eurorack outputs, indefinitely, with no `MISO` to notice.

### F2 — And the value written to channel 7 is given as both 2.5 V and 3.3333 V

Same fault line, different axis. ADR 0006's decision table is current:

> | *(internal)* | DAC ch 7 | — | — | Shared **3.3333 V** offset for mod 1–4 |

ADR 0006's worked example, its update-rate table, and its topology section are not:

> ```
> Vout = 4 × (Vdac − 2.5 V)
>
>   Vdac 0.00 V  →  −10 V
>   Vdac 2.50 V  →    0 V
>   Vdac 5.00 V  →  +10 V
> ```

> - **The 2.5 V reference point comes from a buffered DAC channel**…

> **The mod channels can take the same form** at `k = 3` with the offset channel
> writing 3.3333 V; whether they do is **open** (`mod-channels.md`).

`hardware/module/mod-channels.md` closed it:

> **Adopted, and it is drawn above.** Eight resistors instead of sixteen, and it
> lands on **exactly ±10.000 V**… The offset channel writes 3.3333 V instead of
> 2.500 V

> | **V_ref** | **3.3333 V** from DAC ch7, buffered | Shared by all four. Intercept is `k · V_ref` = 10.000 V |

`firmware/README.md` has the consequence exactly right and it is the only place
it is written:

> *(The value changed with the two-resistor redraw in `mod-channels.md`; writing
> the old 2.5 V into channel 7 against the current 10 k/30 k network gives a
> −7.5…+12.5 V window — wrong span, and it clips positive.)*

**Rank: Showstopper.** ADR 0006 is the *CV channel allocation* ADR — the obvious
place to look up what to write to a channel — and it contains a complete, wrong,
worked example with three numeric rows, plus a live "whether they do is open".

### F19 — `LDAC`, and the absence of atomic update

Stated in exactly two places, neither in `firmware/`.

`hardware/module/digital-and-supervision.md`, *Still open*:

> - **`LDAC` is not in this design anywhere**, which leaves a CMOS input floating
>   on the DAC and means six channels cannot update atomically. **Tie it.** The
>   consequence of not having it: every exit from `CLR` — hot-plug, watchdog
>   recovery, reboot, an OTA stall — throws intermediate values at the mod jacks
>   for 100–200 µs, and **no write order avoids it.**

`bom.csv` row `R-LDAC` (status `candidate`): *"Tied, not driven: a hardware LDAC
was considered and declined… If E10 finds that audible, this becomes a GPIO and
the pin is already broken out."*

Firmware-facing consequences, none of them written down for firmware: each
channel goes live on its own write; there is no synchronous six-channel update;
pitch's *"immediate update on note change"* (ADR 0006) therefore lands
immediately by construction, which is convenient; and `LDAC` may later become a
GPIO, which changes the driver. **Rank: Medium**, and the status is `candidate`
and `open` — firmware cannot rely on `LDAC` being tied.

### F8 — The `CLR` trigger firmware is told about no longer exists

`firmware/README.md`'s entire statelessness argument is built on a watchdog:

> **When the module watchdog asserts `CLR`, every DAC channel including channel 7
> goes to zero scale.** Firmware then rewrites the five signal channels, because
> those are the ones it thinks of as signals, and `Voffset` stays at 0.

**The watchdog was deleted.** `hardware/module/digital-and-supervision.md`, in the
schematic itself:

> ```
>    NOT HERE ANY MORE: the 74HC123 frame watchdog and the LM311 presence
>    comparator. Both deleted; see "What this redraw changed".
> ```

> **2. `CLR` was drawn as a pull-DOWN on an active-low pin.** … With the watchdog
> deleted **nothing else drives that pin**…

and ADR 0004:

> > **Withdrawn 2026-09-21.** The mechanism below was built and then deleted,
> > because it could not catch the failure this section describes. It retriggers
> > on `CS` edges, and firmware refreshes every channel every pass — so a hang
> > *above* the output loop emits healthy edges forever.

`CLR` is now held inactive by `R-CLR-PU` with a bring-up-only solder pad
(`LK-CLR`). **The statelessness rule survives** — the real triggers are rack
power-cycle, hot-plug, module reboot, `LK-CLR` at bring-up, and a mis-framed `CS`
word hitting the software-reset / clear-code / reference-enable bits
(`digital-and-supervision.md`: *"a mis-framed word is a **sticky** failure that
the 4 kHz refresh does not clear"*). **Its stated justification does not.**

Stale survivors of the deletion, all in the present tense:
- `firmware/README.md` — *"When the module watchdog asserts `CLR`…"*
- `hardware/module/mod-channels.md` — *"On a watchdog `CLR`, the C-grade DAC8568 … clears **every** channel"* and *"firmware refreshing the five signal channels after a `CLR`"*
- ADR 0004 §*The watchdog's scope is the DAC channels* — *"the MCU dies, SPI stops, `CLR` fires, and breath keeps working"*
- ROADMAP E10 — *"the watchdog has no authority over it by design"*
- `digital-and-supervision.md`'s own *Still open* — *"every exit from `CLR` — hot-plug, **watchdog recovery**, reboot…"*

**Rank: High**, not Showstopper: firmware that implements the rule is correct
either way. But a firmware author who reasons from the stated trigger will
conclude the module self-protects against a hang — ADR 0004's withdrawal notice
says the opposite and names the uncovered case: *"pull the umbilical mid-note and
the rack holds the note until the module's toggle is flipped."*

---

## 4. Firmware rules the hardware now depends on

For each: where it is written, and whether the hardware page that depends on it
points there.

| Rule | Written where | Hardware page that depends on it | Does it point there? |
|---|---|---|---|
| **Two agreeing samples before note-on** | ADR 0001 only | ADR 0001 §*Key-line signal integrity* | n/a — same doc. **Absent from `firmware/`** |
| **Marker check + error counter** | ADR 0001; `cluster-boards.md` §4 | `cluster-boards.md` §4, `carrier.md` §3, ADR 0014 alarms | Points to ADR 0001/§4. **Absent from `firmware/`** |
| **Breath auto-zero at power-on** | ADR 0006 (full rule); ADR 0003 (partial); ROADMAP F2 | `carrier.md` §2, `breath-receive-stage.md`, `bom.csv` `TRIM-BREATH-ZERO` | Points to ADR 0003/0006. **Partially in `firmware/`** |
| **LED blanking at boot** | ADR 0014 only | `carrier.md` §5 (`R-LED-PD` exists *because* it can't run in time) | Points to ADR 0014. **Absent from `firmware/`** |
| **Lighting current clamp ~3 W** | ADR 0014 only | ADR 0007 idle-current, ADR 0005 regulator, M8 soak | Points to ADR 0014. **Absent from `firmware/`** |
| **USB MIDI opt-in** | `firmware/README.md` | `bom.csv` `HDR-SERVICE`, ADR 0009, `carrier.md` | **Yes** — ADR 0009 cites `firmware/README.md` by name |
| **OTA rollback as recovery rung 1** | `firmware/README.md`, ADR 0009 | `bom.csv` `HDR-SERVICE`, `carrier.md` | **Yes** |

### F3 — Two agreeing samples before a note-on

Stated once, in ADR 0001:

> **Require two consecutive agreeing samples before a note-on.** At the 4 kHz loop
> rate that is 250 µs of added latency — inaudible, and a twentieth of the 5 ms
> budget. … Note-*off* stays filtered as before. This keeps the asymmetric
> debounce's fast attack while removing its single-sample credulity.

It exists because of a hardware property ADR 0001 states in the same section:

> **Asymmetric debounce fires on the first closed sample** (below), so one
> corrupted 32-bit word becomes **one spurious note-on at full velocity, with no
> filtering**.

**Every other statement of the debounce rule contradicts it**, including the one
in `firmware/`:

`firmware/README.md`:
> - **Asymmetric key debounce** — fire immediately on press, filter only the
>   release.

`latency-budget.md`, *Key path*:
> | Debounce (press) | 0 — fire immediately |

> **Debounce asymmetrically.** Fire on the leading edge and filter only the
> release.

ROADMAP E4:
> 74HC165 chain reads all switches; debounce asymmetric (instant press, filtered
> release)

Grep confirms the string appears in exactly one file in the whole corpus.
**Rank: Showstopper.** `firmware/README.md` is where the debounce rule is
written for firmware, and it states the pre-correction version. The failure it
removes is the one ADR 0001 calls the reason the signal-integrity rules are not
optional.

A second ROADMAP rule is in the same position — stated once, outside `firmware/`,
and contradicted by nothing but also carried by nothing:

> So: **apply the release filter to the note decision, not to each key
> independently.** A key that opens while others close is part of a transition,
> not a release, and should not be filtered as though the phrase were ending.

That is a structural requirement on the fingering engine (F1 milestone), it is
load-bearing (*"lifting a finger is how you start the next note"*), and it is in
`ROADMAP.md` under a prose heading. **Rank: High as a gap** — see G6.

### Marker check and error counter

ADR 0001:

> Firmware checks the marker on every read; a frame that fails it **holds the
> previous frame** rather than acting on garbage, and increments a **visible
> error counter**.

`cluster-boards.md` §4 adds the calibration firmware needs to interpret it:

> **What the marker still cannot see**, stated plainly because firmware needs
> it: a single-bit flip is caught **8 times in 32**, and the 24 bits that carry
> the music are never among them — so **the visible error counter undercounts
> true corruption about 4×**. A mid-shift `SH/LD` reload passes at 11 of 31
> reload points.

and closes with the dependency:

> **This is hard-wired copper on boards that bond into the instrument. It has to
> be right before the boards are ordered, and firmware has to be told the
> pattern.**

ADR 0014 makes the counter a non-configurable alarm (*"the key-chain marker error
count to be visible"*, *"alarm states preempt whatever is assigned"*) and ROADMAP
makes it a gate (*"Key-chain error counter over an hour, LEDs and WiFi active | E4
| The marker pattern's whole purpose"*).

**`firmware/README.md` does not mention the marker, the error counter, or
hold-previous-frame anywhere.** The hardware pages point correctly at ADR 0001 and
§4; the firmware page does not receive the pointer. **Rank: High.**

### Breath auto-zero at power-on

The full rule is in ADR 0006 only:

> **Seed it from an ADC capture at power-on**, then **decay it toward the current
> reading whenever breath has been sub-threshold for about 2 seconds**…
> **Gate the decay on "sub-threshold *and* quiet".** Quiet means the signal's
> standard deviation is below about 2× what it measured at commissioning…
> **And log the accumulated correction.** The zero is allowed to move; it is not
> allowed to move silently.

ADR 0003 restates it **without the quiet gate**:

> - **Continuous auto-zero absorbs anything slow** (ADR 0006). The zero decays
>   toward the current reading whenever breath has been sub-threshold for ~2 s…

ADR 0006 is explicit that the un-gated version is defective (*"Sub-threshold is
not enough of a condition, and an auto-zero that never reports is a
fault-concealment machine"*, *"The rule as written eats a sustained pianissimo"*).
ROADMAP F2 has it right: *"gated on sub-threshold AND quiet"*.

`firmware/README.md` mentions only the seed, and only as an input to the lights:

> - **Zero** — the power-on ADC capture, shared with the note-gating zero.
> … the auto-zero's "quiet" gate needs the same figure.

It references the quiet gate without ever stating the rule that uses it, and says
nothing about the 2 s decay or the logged correction. **Rank: Medium** for the
ADR 0003/0006 mismatch, **High** for the absence from `firmware/`.

Three hardware pages depend on the rule: `carrier.md` §2 discharges a 2 LSB
gain error against it (*"Invisible: the zero is auto-tracked in firmware"*),
`bom.csv` `TRIM-BREATH-ZERO` partitions calibration-vs-performance against it,
and ADR 0003 makes the *logged* correction the only diagnostic for a blocked
restrictor. All three cite ADR 0003 or 0006; none cite `firmware/`.

### F14 — LED blanking at boot

ADR 0014, twice:

> - **Blank both strips *and the matrix* as the first act at boot**, before
>   anything else initialises.

> **And the blank-at-boot rule matters more here than for the strips.** … The
> matrix is physically *on* the MCU that resets, so it latches too… Blanking both
> is the first act at boot.

`carrier.md` §5 is the hardware page that depends on it, and it depends on it by
*disbelieving* it — `R-LED-PD` exists because the firmware rule cannot run in the
window that matters:

> **`R-LED-PD` is new and it is the fix for a real hole.** ADR 0014's defence
> against latched strips is "blank both strips and the matrix as the first act at
> boot" `[repo] 0014` — **a firmware rule that cannot run in the window it
> matters.** On reset GPIO1 and GPIO2 are high-impedance inputs for the bootloader
> window (order 100–300 ms `[from memory]`)…

So the rule is still required (it clears a latched strip after a brownout) *and*
is known insufficient (it cannot cover the bootloader window). **Neither half is
in `firmware/README.md`**, whose lighting section covers only zero, deadband and
span. **Rank: High** — this is a boot-order requirement, and boot order is decided
early and changed late.

### F15 — The lighting current clamp

ADR 0014:

> **A single instrument-wide lighting budget of ~3 W**, summed across both strips
> and the matrix, **enforced in firmware before any write**. When the commanded
> total exceeds it, **scale everything down proportionally** rather than refusing
> the write.

> **So the clamp is the shared thermal budget above, not a per-device brightness
> cap.** This ADR previously clamped only the strips, which was wrong in two ways:
> it left the matrix uncovered, and a per-device cap cannot see that both are
> drawing at once.

> the brightness cap below is a hard limit rather than a setting.

This is a firmware algorithm — sum both surfaces, compare to a budget, scale
proportionally, before every write — and `firmware/README.md`'s lighting section
lists only *"Three numbers, all firmware"*: zero, deadband, span. The clamp is not
among them, nor is the alarm-preemption rule (*"alarm states preempt whatever is
assigned … it cannot be configured off"*), which ROADMAP F9 does carry.
ADR 0005's regulator sizing and M8's thermal soak both hang off the clamp holding.
**Rank: Medium**, High if the strips are populated before anyone re-reads ADR 0014.

One rule from ADR 0014 that *is* a single firmware line and is written down
nowhere in `firmware/`:

> - **Drive the LEDs from the post-gate, slew-limited breath value, not from the
>   raw ADC sample.** The strips then cannot respond fast enough to close the loop
>   within a gate decision.
> The second one is the real fix and it is a single line about which variable
> feeds the animation.

`firmware/README.md` says the lights *"read the MCU's own digitised breath value"*
— which is the correct source but the wrong tap point: pre-gate raw ADC is also
"the MCU's own digitised breath value", and that is precisely the version ADR 0014
says causes note-gate chatter. **Rank: Medium.**

### USB MIDI opt-in and OTA rollback — both clean

These are the two that work, and they are worth recording as the pattern the
others should follow. `firmware/README.md` states both:

> - **USB MIDI is opt-in, not the default.** On the ESP32-S3 the internal PHY
>   routes to USB-Serial-JTAG *or* USB-OTG, never both. …
> - **The recovery ladder, in order.** (1) OTA rollback. (2) USB-Serial-JTAG
>   through the tail USB-C slot — which is why MIDI is opt-in. (3) The console
>   header under the service cover (ADR 0009)…

and the hardware that depends on them points back by name. ADR 0009:

> 2. **USB-Serial-JTAG through the tail USB-C slot**, which is a designed opening
>    … **opt-in rather than default** (`firmware/README.md`) — it keeps the
>    download path alive…

`bom.csv` `HDR-SERVICE` restates the whole ladder in its note, and `carrier.md`
does too (*"OTA rollback first, USB-Serial-JTAG through the tail slot second,
this header"*). Three hardware artefacts, one firmware rule, consistent
everywhere. **No finding.**

One minor tension worth noting: ROADMAP's *"shortest path to a playable
instrument"* (E1→E2→E4→E5, USB MIDI into a DAW) and `firmware/README.md`'s
*"A **bring-up tool, not a feature**"* both assume MIDI is routinely enabled
during bring-up, i.e. that the serial-JTAG reset path is routinely unavailable on
the bench. Nothing says how the opt-in is toggled when MIDI is on and the board
is unresponsive. **Rank: Low**, and it is a bring-up ergonomics question, not a
design contradiction.

### F13 — `firmware/README.md` still allocates a core and an SPI host to the display

> - **Display renders on the other core, on its own SPI host.** A display refresh
>   must never block the output loop.

Four bullets later, the same file:

> - **WiFi and the display are on the other MCU.** They cannot preempt the output
>   loop.

ADR 0013 is unambiguous (*"Two microcontrollers, joined by a UART"*; display owns
*"AMOLED panel, WiFi, web app"*), and the real-time board's two SPI hosts are
fully claimed: SPI2 = DAC + ADC, SPI3 = key chain alone (ADR 0001, ADR 0007,
`carrier.md` §4). **There is no third host and no display on that MCU.**

The same pair sits in `latency-budget.md`'s *Rules that follow*:

> 3. **Display rendering never blocks the output loop.** Separate SPI host,
>    separate core. …
> 4. **The WiFi stack and display are on a different MCU entirely** (ADR 0013).

and in ADR 0001's *"The core split carries the WiFi stack too. Sensor read, key
scan and DAC output own one core; display, radio and web server own the other."*

**Rank: High.** This is the opening of the architecture-constraints list in the
firmware README — the first thing a firmware author reads — and it describes the
superseded single-MCU partitioning.

### F20 — `IO33` is both the chain `SER` driver and a spare pin

`carrier.md` §3 assigns it:

> ```
>    IO33  SER out  ──[R-CHAIN-SER 100R]─────►  6  SER     (into the far device)
> ```

`cluster-boards.md` builds the self-test around it:

> If firmware *does* drive `IO33`, the carrier's output wins through its 100 Ω
> series resistor against a 10 kΩ pull `[calc]`… **The self-test becomes a
> firmware choice rather than a board choice**

ADR 0007's pin assignment does not:

> | SPI3 — 74x165 chain alone (ADR 0001) | 2 | 38, 40 |
> | Shift register latch | 1 | 7 |
> | **Used** | **14 of 17** | spare: 3, 4, 33 |
> GPIO 3, 4 and 33 stay free.

ADR 0013's budget likewise books two pins for SPI3 plus one latch, no `SER`.
So the chain needs **four** carrier pins (SCK, QH, SH/LD, SER-out), the pin
tables book three, and `IO33` is listed as spare in the ADR that owns the pin map.
**Rank: Medium** — the pin is free either way, so nothing breaks; but the
end-to-end chain self-test is a firmware feature whose pin is not allocated to it.

Related, and unresolved in the same direction: `carrier.md` §3 says
*"**`CLK INH` is tied low and `SER` is terminated at the far device**"* while
`cluster-boards.md` makes termination a fitted pull-up (`R-SER-TERM`, *proposed*,
`bom.csv` status `open`) that firmware may override. Firmware cannot yet know
whether the self-test is available. **Rank: Low.**

---

## 5. Gaps — facts firmware must have that no document states

These are as actionable as the contradictions, and several are larger.

### G1 — The breath note-on threshold value. **Showstopper.**

The threshold is named as load-bearing in at least six places —
ADR 0003 (*"the threshold that starts a note is on the latency-critical path"*,
*"**Threshold logic.** Breath crossing a threshold is what starts a note"*),
ADR 0006 (the auto-zero decay gates on it), `latency-budget.md`
(*"thresholds, note gating, mod routing and MIDI"*), `carrier.md` §2
(*"the note-on threshold is read through it"*), ADR 0014 (gate chatter),
ROADMAP F2 — and **its value is given nowhere**, in any unit.

The corpus supplies everything needed to express it except the number.
`carrier.md` §2 gives the full ADC scale:

> ```
> full scale = 4.7 V × 0.6 = 2.82 V  against VREF 3.3 V → 85 % of range, 3502 counts
> real play  = 2.8 kPa → 0.2 + 0.766 × 2.8 = 2.34 V → 1.40 V → 1743 counts
> playable span above rest ≈ 1594 counts of 4096
> ```

Rest is ~149 counts; playing tops out at ~1743. The threshold is some number in
between and nothing says which, nor whether it is a constant, a setting, or
derived from the tracked zero. Given that the auto-zero's decay condition is
"sub-threshold and quiet", the threshold is also an input to the zero that the
threshold is measured against — a loop nobody has closed on paper.

### G2 — Gate hysteresis. **Showstopper.**

ADR 0014 requires it and explicitly declines to size it:

> - **Size the note-on/note-off hysteresis from the measured LED-induced step**,
>   not from a guessed value. Measure the step at E4 with the strips running.

No provisional value, no E-milestone row in `latency-budget.md`'s
characterisation table, and no ROADMAP *Bench measurements* row for it (the
nearest is *"Pitch jack while sweeping the LEDs"*, which is a different
measurement on a different channel). Without hysteresis the positive-feedback
path ADR 0014 identifies (LED current → shared-ground reference depression →
reading moves in the direction that keeps the LEDs lit) chatters the gate at the
threshold. **This is a required firmware constant with no value and no scheduled
measurement.**

### G3 — Fingering deglitch time. **High.**

Fingerings are combinational — ADR 0010: *"A control switch inside the fingering
table would produce phantom notes"*; ROADMAP: *"lifting a finger is how you start
the next note."* Real fingers do not move simultaneously, so a transition passes
through intermediate key states that are themselves valid table entries. Nothing
in the corpus states a settle/deglitch window for the *combination*, or how it
interacts with the two-agreeing-samples rule (F3) and the release filter.

The closest the corpus comes is ROADMAP's *"apply the release filter to the note
decision, not to each key independently"* — which names the right mechanism and
gives no duration. M1 measures per-switch bounce and the actuation/reset gap; it
does not measure inter-key skew during a real fingering change, and no milestone
does. **Rank: High**, because it is the difference between a clean legato and a
grace note on every transition, and the measurement would have to happen at M2
with a playable mule.

### G4 — Which bits firmware must mask. **High.**

Three classes of non-key bit will read as steady levels and no document tells
firmware to exclude them:

- **The 3 free bits (22, 23, 31)** carry `R-KEY-PU` and nothing else
  (`cluster-boards.md` §4: *"**Each gets an `R-KEY-PU` and nothing else** — no
  switch, no series resistor, no capacitor"*), so they read permanently **1**.
- **The 3 reserved spare-switch bits (3, 4, 5)** have the full network fitted and
  no switch (*"**Every position above gets the full `R-KEY-PU`/`R-KEY-SER`/`C-KEY`
  network**, including the three unfitted spares"*), so they also read
  permanently **1** — until someone fits a switch, at which point they must
  become live inputs.
- **`key-layout.yaml` has no entries for any of the six.** Its `keys:` list is
  the 18 fitted switches only. A generator that walks that list produces holes at
  bits 3, 4, 5, 22, 23, 31 with nothing saying what belongs in them.

`cluster-boards.md` also leaves open whether the three free bits become markers
too (*"**Whether the last 3 free bits should be marker bits too**, making it 11 …
Left at 8/3 rather than drifting"*), so their expected value is not even stable.

### G5 — The marker pattern in a machine-readable place. **High.**

ADR 0010 says the layout is data and firmware generates from it. ADR 0001 says
the marker lives somewhere else:

> The bit-by-bit assignment and levels are in
> `hardware/controller/cluster-boards.md` §4.

`key-layout.yaml` carries `spare_bits_marker: 8` and a prose pointer
(*"See hardware/controller/cluster-boards.md section 4 for the bit assignment"*)
— a count and a URL, not a pattern. So the answer to the brief's question is
**no**: the marker does not live in `key-layout.yaml`, and neither does the
within-device `H`…`A` mapping, nor the per-cluster bit ranges as data (they are
YAML *comments* on the `chain:` entries).

The consequence is concrete: the two values firmware must hard-code to check
every frame — a 32-bit mask and a 32-bit expected pattern — exist only as a
Markdown table in a hardware page marked **"First draft, 2026-09-21"**, on a page
whose §4 is contingent on a chain order listed under *Still open*. `key-layout.yaml`'s
own header says *"Do not hand-edit … the firmware mapping"*, which is exactly what
generating it from `cluster-boards.md` would require.

### G6 — The note-decision release rule. **High.**

See F3. ROADMAP states it; `firmware/README.md`, which states the debounce rule
firmware implements, does not. It is a structural constraint on F1, discovered
under a ROADMAP prose heading titled *"Why M1 measures slow presses, not just
bounce"* — not a place a firmware author would look for a fingering-engine rule.

### G7 — Which fingering equals 0 V pitch. **Showstopper.**

The pitch chain is fully specified up to this point and stops one step short.
`pitch-stage.md` gives the transfer function exactly:

> | DAC usable window | 0.25 → 4.75 V |
> | Jack range | −2 → +7 V |
> | Slope | 9 V / 4.5 V = **exactly 2.000** |
> | Intercept | −2 − 2(0.25) = **−2.500 V** |
>
> So `Vout = 2·Vdac − 2.500`

so 0 V at the jack is `Vdac` = 1.250 V. ADR 0010 gives the table's contents:

> So the fingering table stores **a note index**, which is what a MIDI note number
> already is, and the pitch for a fingering is that index against **a single
> reference**.
> - **A master tune**, because A = 440 is a convention and not a law.

**The single reference is never given.** Nothing states which note index lands at
0 V, or at −2 V, or what the anchor is. −2…+7 V at 1 V/oct is nine octaves and
108 semitones, and the corpus does not say where in that span the instrument
sits. ADR 0004 mentions *"three left-thumb inputs across a four-octave span"* in
the 2021 firmware, which is history, not a specification; ADR 0010 leaves *"What
the left thumb keys actually do"* open.

E9's calibration (*"Multi-point fit — one point per octave … 1V/oct verified
against a real VCO"*) corrects the hardware, not the anchor. **This is the single
most consequential missing number in the slice**: every fingering in the table is
relative to it, and getting it wrong transposes the whole instrument.

### G8 — The DAC channel numbering is ambiguous, on the channel that matters most. **Showstopper.**

The DAC8568 addresses channels **A–H** in a 4-bit field of the 32-bit command
word. The corpus names them **"ch 1"** through **"ch 7"** throughout — ADR 0006's
allocation table, `pitch-stage.md` (`DAC ch1`), `mod-channels.md` (`DAC ch2`,
`DAC ch7`), `firmware/README.md` (*"DAC channel 7"*) — and **no document maps that
numbering onto A–H or onto the address nibble.**

Under 1-based naming, `ch 7` = channel **G** (address `0110`); under 0-based it is
channel **H** (`0111`). ADR 0006's own accounting makes both readings survivable
on paper — *"**Six of eight channels used, two spare**"* with `ch 6` explicitly
freed — so the spare channels bracket `ch 7` on both sides and an off-by-one
lands on a spare, silently, with no `MISO` to detect it. The visible symptom
would be four mod jacks pinned at `4 × Vdac` ≈ +11.45 V: exactly the failure
`firmware/README.md`'s statelessness section exists to prevent, arriving by a
different route.

`bom.csv` is locked to `DAC8568CIPW` and ADR 0006 says *"**confirm the gain/grade
mapping against SBAS430**, which no browser in this sandbox could reach"* — so the
datasheet has not been opened, and neither the channel addressing nor the command
word's structure (command bits, address, data, feature bits) is recorded
anywhere. ADR 0006 does record two registers firmware must write and does not say
how: *"the internal reference is disabled by default and needs an explicit enable
write at boot"*, and the clear-code register.

### G9 — The write order for DAC channel 7. **Medium.**

`firmware/README.md` mandates six words per pass and says nothing about their
order. `digital-and-supervision.md` says no order helps the `CLR`-exit transient
(*"throws intermediate values at the mod jacks for 100–200 µs, and no write order
avoids it"*) — but that is about the transient, not about steady state, and it
leaves three narrower questions unanswered:

- **Within a pass**, should `ch 7` be written before or after the four mod
  channels? With no `LDAC` each channel goes live on its own write, so a pass
  that writes signals-then-offset computes four jacks against the previous
  `V_ref` for the duration of five words (~80 µs). In steady state `V_ref` is
  constant and it does not matter; on the first pass after any clear it does.
- **At boot**, must the internal-reference enable precede the first channel write?
  ADR 0006 requires the enable *"at boot"* and does not order it against anything.
- **How often** are the housekeeping registers refreshed? `firmware/README.md`
  says *"refreshing the reference-enable and clear-code registers periodically
  costs a word every few thousand passes"* — "a few thousand" is not a
  specification, and that word is not in the six-word budget.

ADR 0006 also specifies a rate rule that interacts with the write order and is
not reconciled with the round-robin: *"Pitch is the subtle one: it needs no
*rate*, but it must not wait for its turn in a round-robin. **Push it the instant
the note resolves.**"* A six-word refresh loop plus an asynchronous out-of-band
pitch write is a different driver shape from a six-word refresh loop, and only one
sentence in the corpus asks for it.

---

## 6. Where firmware would most likely be written from

The brief asks, where two documents disagree, which one firmware would be written
from. The general answer is uncomfortable: **`firmware/README.md` names ADR 0001
and `latency-budget.md` as its two non-negotiable sources**, and on the four
highest-ranked facts in this report, the document firmware would consult is the
one carrying the stale value.

| Fact | Firmware would read | It says | Correct source |
|---|---|---|---|
| Channel-7 cadence | `firmware/README.md`, ADR 0006 | "written once at boot" | `firmware/README.md`'s own rule; `mod-channels.md` |
| Channel-7 value | ADR 0006 | 2.5 V, and "open" | `mod-channels.md` (3.3333 V, adopted) |
| Note-on debounce | `firmware/README.md` | "fire immediately on press" | ADR 0001 (two agreeing samples) |
| Key-chain read cost | `latency-budget.md` | 10 µs / 16 µs | ADR 0001, `carrier.md` (32 µs at 1 MHz) |
| ADC cost | ADR 0003 | 50–200 µs | `latency-budget.md` (24 µs) |
| Umbilical clock | ADR 0004 conductor budget | ~1 MHz | ADR 0004 bandwidth table, `carrier.md` (2 MHz) |
| ADC device clock | ADR 0003/0004/latency-budget | "SPI2 at 2 MHz" | `carrier.md` §4 (0.9 MHz per device) |
| Marker bits | `key-layout.yaml`, ADR 0010, `carrier.md` | 6 / "4–6" / "undecided" | `cluster-boards.md` §4 (8, decided) |
| Bit allocation | `key-layout.yaml` (per ADR 0010) | not present | `cluster-boards.md` §4 |
| MCU partitioning | `firmware/README.md` bullet 2 | display on the other core | ADR 0013 (other MCU) |

**The pattern is consistent and worth naming:** corrections have been landing in
the *hardware* pages (`cluster-boards.md`, `carrier.md`, `mod-channels.md`,
`digital-and-supervision.md`), which are drafted last and reviewed hardest, while
the ADRs and `firmware/README.md` retain the superseded text. The hardware pages
are right about nearly everything and firmware will not read them.

The cheapest structural fix is a single firmware-facing contract page — bit map
and marker mask/pattern, loop schedule with per-host clocks, DAC channel map with
addresses and per-channel cadence, and the seven firmware rules from §4 — owned by
`firmware/` and cited by the hardware pages that depend on each item, the way
ADR 0009 already cites `firmware/README.md` for USB MIDI opt-in. That pointer is
the one place in this slice where the dependency is recorded in both directions,
and it is the only rule in the set with no staleness finding against it.
