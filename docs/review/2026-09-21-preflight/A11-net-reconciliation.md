# A11 — Canonical net list and name reconciliation

**Wave:** 2026-09-21 preflight (pre-SKiDL transcription)
**Slice:** every net name on every schematic page; every name used for two nets;
every net called by two names.
**Method:** cold. No `docs/review/**` was read. Sources are the eight schematic
pages, `docs/decisions/0004-cv-interface-module.md`, `hardware/bom.csv`,
`config/figures.yaml`, and the corpus files that cite them
(`docs/reference/pcb-pipeline.md`, `ROADMAP.md`, `firmware/README.md`).
**Provenance:** every alias carries `[repo file:line]`. Arithmetic is `[calc]`.
Nothing here is `[from memory]` or `[web]`.

---

## 0. What this document is

This is **the artifact**, not a report about it. §4 is the net table, §5 is the
per-page rename list, §6 is the naming convention. §1–§3 are the findings that
justify the renames; §7 is what I found but am deliberately **not** resolving.

The transcription must take net names from **§4 and §5 of this file**, not from
the drawings. The drawings are correct as circuits and wrong as netlists.

**Headline count.** Across the eight pages there are **11 names that each mean
two or more different nets** (§1) and **23 nets that carry two or more names**
(§2). Two of the eleven were already known (`AGND`, `BREATH`,
`docs/reference/pcb-pipeline.md:58-59`). **Nine are new**, and three of the nine
are shorts as severe as the breath short:

- `+12V` merges the Eurorack bus rail, the module analog rail and the umbilical
  export rail — **three nets, one name, across the diode split whose entire
  purpose is to keep them apart** (§1.3).
- `SCLK` / `MOSI` / `CS` name both the **input** and the **output** of the
  module's 74AHCT125 — a naive transcription shorts across the buffer, which
  deletes the buffer (§1.4).
- `MISO` names the MCP3202's `DOUT` (IO37) **and** the key chain's `QH` (IO40),
  two independent SPI hosts (§1.6).

And one drawing ambiguity is worse than any naming collision, because it is a
**power short** rather than a signal short: `power-entry.md`'s `D2` branch
appears to run from the Eurorack `+12V` pin into `PWR_GND` (§3.1).

---

## 1. Names that mean two or more different nets

Ordered by consequence.

### 1.1 `AGND` — the umbilical sense conductor **and** the module analog return

Known (`docs/reference/pcb-pipeline.md:58`), and confirmed exhaustively here.
Fifteen occurrences split across two electrically unrelated nets that live on
two different boards two metres apart.

**Meaning A — umbilical conductor, pin 2, an in-amp *input*:**

| Where | Text |
|---|---|
| `docs/decisions/0004-cv-interface-module.md:99` | `BREATH    / AGND        analog, band-limited ~500 Hz, sense return` |
| `docs/decisions/0004-cv-interface-module.md:108` | "**`AGND` carries no power current**" |
| `docs/decisions/0004-cv-interface-module.md:611` | "`AGND`, from the etherCON \| **Nothing.** It is an in-amp input, not a ground" |
| `docs/decisions/0004-cv-interface-module.md:630` | "**`AGND` is not in this list.** It terminates at the in-amp's IN+ and at the two 1 MΩ bias resistors" |
| `docs/decisions/0004-cv-interface-module.md:798` | "**BREATH/AGND ↔ +12 V/PWR_GND**" |
| `docs/decisions/0004-cv-interface-module.md:828` | "1, 2 \| ✓ \| **BREATH / AGND**" |
| `hardware/module/breath-receive-stage.md:28` | `analog star ──[R1b 1k]──── AGND   (pin 2)` |
| `hardware/module/breath-receive-stage.md:57` | `Vout = −2.185·(V_BREATH − V_AGND) + V_REF` |
| `hardware/module/breath-receive-stage.md:157` | "**Its twin in the `AGND` leg.**" |
| `hardware/module/breath-receive-stage.md:209` | "`R1` sits in the `BREATH` leg with nothing opposite it in the `AGND` leg" |
| `hardware/module/breath-receive-stage.md:221` | "**`R1b` fixes it for nothing.** The `AGND` leg carries no signal current" |
| `hardware/module/power-entry.md:498` | "`AGND` is not a ground at all — it is an in-amp input (ADR 0003)" |
| `hardware/controller/carrier.md:199` | `J-UMB pin 2 AGND ──[R-SER-BREATH-INST 1k]──┴── analog star point` |
| `hardware/controller/carrier.md:212` | "`R1b` — the twin 1 kΩ in the `AGND` leg" |
| `hardware/controller/carrier.md:298` | "the analog star point is on this board, and `AGND` is sense-only" |
| `hardware/controller/carrier.md:304` | "`AGND` leaves the board carrying nothing but the in-amp sense reference" |
| `hardware/controller/carrier.md:845` | ``D-TVS-BREATH`` ×2 … "`BREATH` and `AGND` legs" |
| `hardware/bom.csv:28` | "senses against AGND … AGND drives IN+" |
| `hardware/bom.csv:55` | "`PWR_GND`, never `AGND`. … AGND would put body capacitance on the breath reference" |
| `hardware/bom.csv:65` | "`R1b` its twin in the AGND leg" |
| `hardware/bom.csv:104` | "ESD protection on the BREATH and AGND legs" |
| `hardware/bom.csv:125` | "Clamp diodes on the BREATH and AGND legs at the in-amp inputs" |
| `ROADMAP.md:53` | "`AGND` not a return at all" |

**Meaning B — the module's local analog return, a ground:**

| Where | Text |
|---|---|
| `hardware/module/breath-receive-stage.md:39` | `├──[C_cm 1.5nF]── AGND(module)` |
| `hardware/module/breath-receive-stage.md:43` | `├──[C_cm 1.5nF]── AGND(module)` |
| `hardware/module/breath-receive-stage.md:47` | `AGND(module)    │       │      AGND(module)` — **two on one line** (R4 return, R5 return) |
| `hardware/module/breath-receive-stage.md:70` | `[1k]─┼─[C 330nF]── AGND(module)` |
| `hardware/module/breath-output-stage.md:41` | `AGND(module)` — `R-GAIN-FLOOR` return |
| `hardware/module/breath-output-stage.md:55` | `AGND   │` — summer's **(+) input** |
| `hardware/module/breath-output-stage.md:62` | `├──[C-OUT-BREATH 330nF film]── AGND` |
| `hardware/module/pitch-stage.md:202` | "`C-AA-PITCH`, 10 nF from the `R-OPAMP-IN` node to `AGND`" |
| `hardware/module/mod-channels.md:43` | `├──[C-FILT-MOD 82nF]── AGND` |
| `hardware/module/digital-and-supervision.md:73` | "`[R-CLR-PD 10k]` to `AGND`" (describing the superseded drawing) |
| `hardware/module/breath-receive-stage.md:232` | "1 MΩ to module analog ground" |

**Severity: fatal.** `M_ARET` is a ground carrying the module's entire analog
supply return; `UMB_BREATH_N` is a high-impedance differential *input* that
`docs/decisions/0004-cv-interface-module.md:632` says must carry **no** return
current at all. Merging them defeats the sole reason a 2 m analog run works.
Note also that four of the Meaning-B sites are written as bare `AGND`
(`pitch-stage.md:202`, `mod-channels.md:43`, `breath-output-stage.md:55,62`) —
**a regex for `AGND(module)` does not find them.**

### 1.2 `BREATH` — the umbilical conductor **and** the output jack

Known (`docs/reference/pcb-pipeline.md:59`). Both meanings live inside
`breath-receive-stage.md`, 52 lines apart.

| Meaning | Where |
|---|---|
| **Umbilical conductor / in-amp input** | `hardware/module/breath-receive-stage.md:22` (`BREATH (pin 1)`), `:57` (`V_BREATH`), `:182` ("a sustained +12 V fault on the `BREATH` conductor"), `:209`; `docs/decisions/0004-cv-interface-module.md:99,110,828,864,868`; `hardware/controller/carrier.md:50,182,322,845`; `hardware/bom.csv:65,104` |
| **Output jack** | `hardware/module/breath-receive-stage.md:74` (`BREATH jack`); `hardware/module/breath-output-stage.md:64` (`BREATH jack`); `hardware/module/pitch-stage.md:269` ("BREATH (330 nF) jacks"); `docs/decisions/0004-cv-interface-module.md:643` ("**PITCH** and **BREATH** silkscreened") |

**Severity: fatal.** Merging shorts the in-amp input to its own amplified
output — a ~2.2× positive-feedback loop around the whole breath chain.

### 1.3 `+12V` — three different nets, across the diode split that exists to separate them — **NEW**

`power-entry.md`'s opening drawing has all three on adjacent lines.

| Meaning | Where |
|---|---|
| **A. Eurorack bus +12 V**, at `J-PWR-EURO`, *before* `D1`/`D2` | `hardware/module/power-entry.md:15` (`+12V ├───┬──[D1 1N5817]`); `:115` ("The bus +5 V pin"); `docs/decisions/0004-cv-interface-module.md:299` (`bus +12V ──┬──[1N5817]`) |
| **B. Module analog +12 V**, after `D1`/`FB1`/`C1` | `hardware/module/power-entry.md:15` (`── MODULE ANALOG +12V`); `:468` ("2.2 kOhm from +12 V analog"); `hardware/module/pitch-stage.md:31,153` (`±12 V`); `hardware/module/mod-channels.md:39,107` (`±12 V`); `hardware/module/breath-receive-stage.md:33,72` (`±12 V`); `hardware/module/breath-output-stage.md:58` (`±12 V`) |
| **C. Umbilical +12 V**, the LT1641's switched output | `hardware/module/power-entry.md:46` (`UMBILICAL +12V ────► instrument`); `hardware/controller/carrier.md:50` (`3 +12V`), `:59`, `:85` (`J-UMB pin 3  +12V`), `:89`, `:93`, `:97`, `:164` (`+12V ──[REF5050]`) |

**Severity: fatal, and specifically ironic.** `power-entry.md:57-90` spends
thirty lines arguing that `D1` and `D2` must be two diodes so that B and C do
**not** share a forward drop. Transcribing `+12V` as one net puts B and C on
the same node, shorts out `D1`, `D2`, `FB1`, `FB2`, `C1`, `C2` **and** the
entire LT1641 load switch, and every ERC and DRC downstream passes.

`−12V` has the same two-way version of this (bus vs. module analog):
`hardware/module/power-entry.md:48` (`-12V ├───[D3 …]── MODULE ANALOG −12V`)
against `hardware/module/breath-output-stage.md:48,102,110,126` (`−12 V`,
`R-OFFNEG`'s source, which is the *analog* rail).

### 1.4 `SCLK` / `MOSI` / `CS` — the 74AHCT125's inputs **and** its outputs — **NEW**

`digital-and-supervision.md`'s drawing labels the pull resistors on **both**
sides of the buffer with the same three names:

```
        │    [R-SPI-PULL x3]          │  74AHCT125   │      ← cable side
        │     SCLK↓ MOSI↓ CS↑         │  bus +5V     │
...
        │                        [R-SPI-PULL x3]            ← DAC side
        │                         SCLK↓ MOSI↓ CS↑
```
`[repo hardware/module/digital-and-supervision.md:30-36]`

The page's own prose names the far side differently — "the pins actually
floating in that state are the **DAC's** `SCLK`, `DIN` and `SYNC`"
`[repo hardware/module/digital-and-supervision.md:123]` — and `bom.csv` agrees:
"DAC side: … it is then the DAC's SCLK/DIN/SYNC that float"
`[repo hardware/bom.csv:49]`. So the **input** names are `SCLK`/`MOSI`/`CS` and
the **output** names are `SCLK`/`DIN`/`SYNC`, with `SCLK` colliding outright
and `MOSI`/`CS` colliding only in the drawing.

**Severity: fatal.** Merging shorts input to output on all three lines, which
deletes the buffer, defeats the 5 V→5.21 V level translation, and re-exposes
the DAC's `SYNC` pin directly to 2 m of Cat5.

### 1.5 `CS` — the DAC's chip select **and** the MCP3202's chip select — **NEW**

| Meaning | Where |
|---|---|
| Umbilical conductor to the DAC, from IO34 | `hardware/controller/carrier.md:576` (`IO34 CS ──[R-SPI-SER 100R]──── J-UMB pin 7`) |
| MCP3202 chip select, from IO39, never leaves the board | `hardware/controller/carrier.md:581` (`IO39 CS   ── MCP3202 CS`) |

Both are in the **same ten-line drawing**, five lines apart. Both are `CS`.

**Severity: fatal.** Merging makes every DAC word also address the ADC and
vice versa, on a host (`SPI2`) that `carrier.md:616` explicitly shares between
the two devices at two different clock rates.

### 1.6 `MISO` — the ADC's `DOUT`, the key chain's `QH`, and a deleted conductor — **NEW**

| Meaning | Where |
|---|---|
| SPI3 input from the 74HC165 chain, IO40 | `hardware/controller/carrier.md:445` (`IO40 MISO ◄──── 8 QH`) |
| SPI2 input from the MCP3202, IO37 | `hardware/controller/carrier.md:580` (`IO37 MISO ── MCP3202 DOUT only`) |
| The **deleted** umbilical conductor | `docs/decisions/0004-cv-interface-module.md:38,113,846`; `firmware/README.md:39,70`; `hardware/module/digital-and-supervision.md:99` |

**Severity: fatal for the first two** (they are on different SPI hosts and
would be shorted together). The third is a ghost: it must produce **no net at
all**, and a transcriber who sees `MISO` three times may reasonably conclude
there is one.

### 1.7 `SCK` — the umbilical SPI clock **and** the key chain clock — **NEW**

| Meaning | Where |
|---|---|
| Key chain clock, SPI3, IO38 | `hardware/controller/carrier.md:439` (`IO38 SPI3 SCK ──[R-CHAIN-SER 100R]──► 2 SCK`); `:875`; `hardware/controller/cluster-boards.md:243,254,277`; `hardware/bom.csv:73,94,95` |
| Umbilical SPI clock, SPI2, IO35 | `hardware/controller/carrier.md:574` (`IO35 SCK ──[R-SPI-SER 100R]──── J-UMB pin 4`) |

**Severity: fatal.** Two SPI hosts, one at 1 MHz and one at 2 MHz
(`hardware/controller/carrier.md:616-617`), shorted together.

### 1.8 `GND` — at least five different nets — **NEW**

`GND` is used bare on five pages and never means the same thing twice.

| Where | What it actually is |
|---|---|
| `hardware/module/power-entry.md:52` (`GND └── STAR POINT`) | Eurorack bus ground pin = the `PWR_GND` star origin |
| `hardware/module/digital-and-supervision.md:32` (`OE x4 → GND`) | The 74AHCT125's ground — `DIG_GND` |
| `hardware/module/digital-and-supervision.md:45,47` (`LK-CLR pad` / `GND`) | Undeclared. The DAC's return is the module analog return (`docs/decisions/0004-cv-interface-module.md:629`), so it should be `M_ARET` |
| `hardware/module/breath-output-stage.md:199` (§4 response divider) | Module analog return |
| `hardware/controller/carrier.md:438-446` (`J-CHAIN` ×5), `:666,669,672,675` (`R-LED-PD`, `J-LED BI`), `:763,767,775,776` (`J-DISP`, `HDR-SERVICE`) | Instrument-side return — undeclared which one |
| `hardware/controller/cluster-boards.md:95,101,137,139,257,262,499` | Cluster-board return — undeclared which one |

**Severity: fatal on the module** (it merges `M_PWR_GND`, `M_DIG_GND` and
`M_ARET`, which is precisely the failure
`docs/decisions/0004-cv-interface-module.md:613-632` exists to prevent).
**Unresolved on the instrument** — see §7.2.

### 1.9 `V_ref` — pitch's 2.500 V **and** the mods' 3.3333 V — **NEW**

| Meaning | Where |
|---|---|
| 2.500 V, trimmed and buffered from `VREFOUT` | `hardware/module/pitch-stage.md:14` (`V_ref ≈ 2.500 V`), `:57,58,72,76,129,280` |
| 3.3333 V, buffered from DAC ch7 | `hardware/module/mod-channels.md:6` (`V_ref` = **3.3333 V**), `:20,54,57,66,101` |
| Generic symbol in shared derivations | `hardware/module/pitch-stage.md:72,76,85`; `hardware/module/mod-channels.md:57` |

`docs/reference/pcb-pipeline.md:184` lists "`VREFOUT`, `V_ref`, the three
trimmer wipers, the mods' shared 3.3333 V" as four separate hand-routed items —
which reads as though `V_ref` and the 3.3333 V node are different things, and
they are, but the corpus calls them both `V_ref`.

**Severity: fatal, and the most expensive millivolt on the board.**
`docs/reference/pcb-pipeline.md:185` — "**1 mV on `V_ref` is 1.2 cents**".
Merging them puts 3.3333 V on the pitch intercept: the jack sits at
`2·Vdac − 3.3333` instead of `2·Vdac − 2.500`, i.e. **833 mV = ~10 semitones
flat** `[calc]`, and the mods sit at `4·Vdac − 7.500` instead of
`4·Vdac − 10.000`, i.e. **+2.5 V offset on four jacks** `[calc]`.

### 1.10 `5V` — three nets on the instrument, one on the module — **NEW**

| Meaning | Where |
|---|---|
| Eurorack bus +5 V (module) | `hardware/module/power-entry.md:50` (`+5V ├───[FB4]…`), `:115,466`; `hardware/module/digital-and-supervision.md:31,80,108,110` ("bus +5V") |
| Instrument buck A output → dev board + 74AHCT125 | `hardware/controller/carrier.md:60,64` (`5V`), `:99` (`dev board 5V`) |
| Instrument buck B output → display board | `hardware/controller/carrier.md:104` (`J-DISP 5V`), `:762` |

Bus +5 V and instrument 5 V are two metres apart, never connected (no 5 V
conductor is in the umbilical — `docs/decisions/0004-cv-interface-module.md:96-99`),
and both are written `+5V`/`5 V`. The two buck outputs are also separated by
two `D-USBOR` diodes (`hardware/controller/carrier.md:99,104`), so the OR node
on each dev board is a fourth and fifth net again.

**Severity: fatal if the module and instrument are transcribed into one
project**, which `docs/reference/pcb-pipeline.md:249` ("Seven rails, six
modules") implies they are.

### 1.11 `REF` — the in-amp's `REF` pin **and** the 5 V voltage reference — **NEW**

| Meaning | Where |
|---|---|
| INA828 `REF` pin, driven by the buffered `TRIM-BREATH-ZERO` | `hardware/module/breath-receive-stage.md:54,77,80,93,115,141,146,163,258,295,329`; `hardware/bom.csv:28` |
| The REF5050's 5.000 V output (instrument) | `hardware/controller/carrier.md:164,166` (`[REF5050]── 5.000 V`, `C-REF-OUT`); `hardware/module/breath-receive-stage.md:24` (`VS = REF5050 5.000 V`) |
| The DAC's `VREFOUT` | `hardware/module/pitch-stage.md:8,14,…` |

Lower severity than the rest because the two live on different boards and the
prose usually disambiguates, but `R-ISO-REF`, `C-REF-OUT`, `U-REF-BREATH`,
`R-BIAS-INAMP`'s "REF tie" and `V_REF` all share the token, and
`docs/decisions/0004-cv-interface-module.md:629` ("the in-amp's `REF` tie")
is on the module side while `C-REF-OUT`/`R-ISO-REF` are instrument-side.
**Severity: moderate — disambiguate by prefix, no short results.**

---

## 2. Nets called by two or more names

The mirror defect. Every row here is one net; the transcription must **not**
create two.

| Canonical | Aliases found, with provenance |
|---|---|
| `M_ARET` (module analog return) | `AGND(module)` `[hardware/module/breath-receive-stage.md:39,43,47,47,70]`, `[hardware/module/breath-output-stage.md:41]`; bare `AGND` `[hardware/module/pitch-stage.md:202]`, `[hardware/module/mod-channels.md:43]`, `[hardware/module/breath-output-stage.md:55,62]`, `[hardware/module/digital-and-supervision.md:73]`; `analog star` `[hardware/module/digital-and-supervision.md:53]`; `module analog ground` `[hardware/module/breath-receive-stage.md:232-233]`, `[docs/decisions/0003-breath-sensing-path.md:384]`; `The analog return` / `Module analog return` `[docs/decisions/0004-cv-interface-module.md:610,614,628]`, `[hardware/module/power-entry.md:494-495]`; `the analog return` `[docs/reference/pcb-pipeline.md:225-226,247]`; bare `GND` `[hardware/module/breath-output-stage.md:199]`, `[hardware/module/digital-and-supervision.md:45,47]`. **Six spellings.** |
| `I_ARET` (instrument analog return) | `AGND-local` `[hardware/controller/carrier.md:168,168,172,172,187-188]`; `analog star point` `[hardware/controller/carrier.md:199,298]`; `the analog star` `[hardware/controller/carrier.md:248]`; `analog star` `[hardware/module/breath-receive-stage.md:28]`, `[config/figures.yaml:256]`; `the analog ground pour on the bottom cluster board` `[docs/decisions/0003-breath-sensing-path.md:681]`, quoted `[hardware/controller/carrier.md:299]`. **Five spellings.** |
| `M_PWR_GND` | `PWR_GND` (passim); `PWR_GND (star)` `[hardware/module/power-entry.md:22]`; `STAR POINT` `[hardware/module/power-entry.md:52]`; bare `GND` at the bus pin `[hardware/module/power-entry.md:52]`; `the star point` `[docs/decisions/0004-cv-interface-module.md:624]`; `the IDC's ground pin` `[hardware/module/power-entry.md:493]`; `the Eurorack power inlet's ground pin` `[docs/decisions/0004-cv-interface-module.md:599]` |
| `UMB_BREATH_P` | `BREATH` `[docs/decisions/0004-cv-interface-module.md:99,110,828,864,868]`; `BREATH (pin 1)` `[hardware/module/breath-receive-stage.md:22]`; `V_BREATH` `[hardware/module/breath-receive-stage.md:57]`; `the BREATH leg` `[hardware/module/breath-receive-stage.md:209]`, `[hardware/bom.csv:65,104,125]`; `J-UMB pin 1 BREATH` `[hardware/controller/carrier.md:50,181-182]` |
| `UMB_BREATH_N` | `AGND` (all of §1.1 Meaning A); `AGND (pin 2)` `[hardware/module/breath-receive-stage.md:28]`; `V_AGND` `[hardware/module/breath-receive-stage.md:57]`; `the sense return` `[docs/decisions/0004-cv-interface-module.md:99]`; `the in-amp sense reference` `[hardware/controller/carrier.md:304]` |
| `UMB_P12V` | `UMBILICAL +12V` `[hardware/module/power-entry.md:46]`; `+12V` `[hardware/controller/carrier.md:50,59,85,164]`; `J-UMB pin 3` `[hardware/controller/carrier.md:85]`; `+12 V on the umbilical` `[docs/decisions/0004-cv-interface-module.md:105,114]`; "a node downstream of the module's own load switch" `[hardware/module/digital-and-supervision.md:136-137]` |
| `M_P12V_A` | `MODULE ANALOG +12V` `[hardware/module/power-entry.md:15]`; `+12 V analog` `[hardware/module/power-entry.md:468]`; `+12 V` `[hardware/module/digital-and-supervision.md:84]`; the `+` half of `±12 V` `[hardware/module/pitch-stage.md:31]`, `[hardware/module/mod-channels.md:39]`, `[hardware/module/breath-receive-stage.md:33,72]`, `[hardware/module/breath-output-stage.md:58]`; `module analog (op-amps)` `[docs/decisions/0004-cv-interface-module.md:299]` |
| `M_N12V_A` | `MODULE ANALOG −12V` `[hardware/module/power-entry.md:48]`; `−12 V` `[hardware/module/breath-output-stage.md:48,102,110,126]`; the `−` half of `±12 V` (same five sites); `module analog` `[docs/decisions/0004-cv-interface-module.md:310]` |
| `M_AVDD` | `DAC AVDD 5.21V` `[hardware/module/power-entry.md:18]`; `AVDD 5.21V` `[hardware/module/digital-and-supervision.md:40,43,50]`; `AVDD` `[hardware/module/digital-and-supervision.md:42,49,247]`, `[docs/decisions/0004-cv-interface-module.md:610]`, `[hardware/bom.csv:12,38,43,49]`; `the LM317 5.21 V` `[hardware/module/breath-receive-stage.md:55]`; `the LM317 rail` `[hardware/module/breath-receive-stage.md:163,296,319]`; `buffered +5.21 V (LM317 rail)` `[hardware/module/breath-output-stage.md:43-44]`; `5.21 V` `[hardware/module/breath-output-stage.md:100]`. ⚠ the word **buffered** at `breath-output-stage.md:43` may name a *different* net — see §7.4 |
| `M_DAC_SCLK` | `SCLK` (buffer output) `[hardware/module/digital-and-supervision.md:36]`; `the DAC's SCLK` `[hardware/module/digital-and-supervision.md:123]`, `[hardware/bom.csv:49]` |
| `M_DAC_DIN` | `MOSI` (buffer output) `[hardware/module/digital-and-supervision.md:36]`; `DIN` `[hardware/module/digital-and-supervision.md:123]`, `[hardware/bom.csv:10,49,85,100,117]` |
| `M_DAC_SYNC` | `CS` (buffer output) `[hardware/module/digital-and-supervision.md:36]`; `SYNC` `[hardware/module/digital-and-supervision.md:123]`, `[hardware/bom.csv:49,49]` |
| `UMB_SCLK` | `SCLK` `[docs/decisions/0004-cv-interface-module.md:83,97,830]`, `[hardware/module/digital-and-supervision.md:23,31,86]`, `[hardware/bom.csv:49,50,103]`; `SCK` `[hardware/controller/carrier.md:574]` |
| `UMB_MOSI` | `MOSI` (passim); no second spelling found — the one clean one, apart from the buffer-output collision |
| `UMB_CS` | `CS` `[docs/decisions/0004-cv-interface-module.md:84,98,831,843]`, `[hardware/module/digital-and-supervision.md:27,88,96]`, `[hardware/controller/carrier.md:576,846]` |
| `I_CHAIN_SCK` | `SCK` `[hardware/controller/carrier.md:439,875]`, `[hardware/controller/cluster-boards.md:243,254,277]`, `[hardware/bom.csv:73,94,95]`; `CLK` (74HC165 pin 2) `[hardware/controller/cluster-boards.md:95,262]`; `SPI3 SCK` `[hardware/controller/carrier.md:439]` |
| `I_CHAIN_SHLD` | `SH/LD` `[hardware/controller/carrier.md:441,511,833,875]`, `[hardware/controller/cluster-boards.md:94,243,255,262,393]`; `latch` `[hardware/controller/carrier.md:441,69]` |
| `I_CHAIN_SER` | `SER` `[hardware/controller/carrier.md:443,465,479,833,859,875]`, `[hardware/controller/cluster-boards.md:100,243,258,266,296]`; `SER out` `[hardware/controller/carrier.md:443]`; `serial in` `[hardware/controller/cluster-boards.md:100]`; `IO33` `[hardware/controller/cluster-boards.md:304]` |
| `I_CHAIN_QH_RT` | `QH` `[hardware/controller/carrier.md:445]`, `[hardware/controller/cluster-boards.md:244,264]`; `MISO` `[hardware/controller/carrier.md:445]`; `serial out` `[hardware/controller/cluster-boards.md:101]`; `IO40` `[hardware/controller/carrier.md:445]` |
| `I_3V3` | `3V3` `[hardware/controller/carrier.md:64,69,447]`, `[hardware/controller/cluster-boards.md:94,131,244,256,300]`; `VDD/VREF = 3V3` `[hardware/controller/carrier.md:192]`; "the dev board's LDO" `[hardware/controller/carrier.md:193-194,496]`; "`VDD` **is** `VREF`" `[hardware/controller/carrier.md:836]`; "the MCP3202's voltage reference" `[hardware/controller/cluster-boards.md:230]` |
| `I_VREF5` | `5.000 V` `[hardware/controller/carrier.md:164]`; `REF5050` output `[hardware/controller/carrier.md:93,164]`; `VS = REF5050 5.000 V` `[hardware/module/breath-receive-stage.md:24]` — ⚠ that last one conflates `I_VREF5` with `I_VS`, which `R-ISO-REF` separates `[hardware/controller/carrier.md:166,228-250]` |
| `M_INA_OUT` | `Vout` `[hardware/module/breath-receive-stage.md:57]`; `from the INA828` `[hardware/module/breath-output-stage.md:34]`; `in-amp output` `[hardware/module/breath-output-stage.md:20]`; `in-amp out` `[hardware/module/breath-output-stage.md:190]`; `0 … −4.7 V` `[hardware/module/breath-output-stage.md:35]`; `In-amp` column `[hardware/module/breath-output-stage.md:238-244]` |
| `M_BREATH_JACK` | `BREATH jack` `[hardware/module/breath-receive-stage.md:74]`, `[hardware/module/breath-output-stage.md:64]`; `BREATH` `[hardware/module/pitch-stage.md:269]`, `[docs/decisions/0004-cv-interface-module.md:643]`; "the jack" `[hardware/module/breath-output-stage.md:96-100]` |

---

## 3. Drawing defects that a name-driven transcription would import

Not naming collisions, but they land in the same place: a netlist that passes
every downstream check and is wrong.

### 3.1 `power-entry.md`'s `D2` branch appears to short bus +12 V to `PWR_GND`

```
  +12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
       │   │
       │   └──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)
```
`[repo hardware/module/power-entry.md:15,22]`

Read literally, `D2`+`FB2`+`C2` run from the `+12V` bus pin to `PWR_GND`.
That is a hard short through two passives and a Schottky.

The text says what it must actually be: `D2` feeds the **load-switch input**,
and the page's own argument is that the instrument's current must not share
`D1` `[repo hardware/module/power-entry.md:57-62]`; the LT1641 block with
`R-ILIM` hangs off that same node three lines below
`[repo hardware/module/power-entry.md:24-28]`; and `C2`'s *other* terminal is
what returns to `PWR_GND`.

**The node after `D2`/`FB2` has no name anywhere in the corpus.** It is the
LT1641's `VCC` and the high side of `R-ILIM`. Named `M_P12V_SW` in §4.
**Do not transcribe line 22 as drawn.**

### 3.2 `PWRGD` is designed in prose and exists on no drawing

`hardware/module/power-entry.md:231` gives the pinout including `3 PWRGD`, and
`:254,261-272,285-286` size the `FB` divider around where `PWRGD` releases —
but `PWRGD` appears in **no** drawing on the page and connects to nothing. The
drawing at `:27-38` shows `VCC SENSE / ON / TIMER GATE / FB` and omits pin 3
entirely.

**Netlist consequence:** `PWRGD` is an open-drain output. Left unconnected it
is harmless; but the page's §5 argument ("`FB` was not connected, and that is
what stops it starting") is the same class of defect one pin along. Transcribe
it as an explicitly unconnected pin with a `NC` marker, not as an omission.

### 3.3 The MCP3202's `CLK` and `DIN` are drawn nowhere

`hardware/controller/carrier.md:190-196` draws the MCP3202 with `CH0`, `CH1`,
`VDD/VREF` and decoupling. `:580-581` add `DOUT` and `CS`. **`CLK` and `DIN`
are never drawn**, although `:616` puts the part on SPI2 with the DAC.

This is a net question, not just an omission: SPI2's clock and data reach
`J-UMB` through `R-SPI-SER` `[repo hardware/controller/carrier.md:574-575]`,
and whether the ADC taps **before** or **after** those resistors is two
different netlists. Tapping after puts the ADC's input capacitance on the
far side of the source termination and detunes the 100 Ω match the page spends
twenty lines deriving `[repo hardware/controller/carrier.md:591-610]`.

**Recommended and used in §4:** tap **before** `R-SPI-SER` (`I_SPI2_SCK_RAW`,
`I_SPI2_MOSI_RAW`), so the termination sees only the cable. Flagged as a
decision, not a finding.

### 3.4 The instrument end of `DIG_GND` connects to nothing drawn

```
  IO34 CS   ──[R-SPI-SER 100R]───┬──── J-UMB pin 7   ┐ pair (7,8)
                                 │     J-UMB pin 8 ──┘ DIG_GND
                                 │
                        [U-TVS-SPI 4-ch array to PWR_GND]
```
`[repo hardware/controller/carrier.md:576-579]`

Pin 8's `┘` joins the vertical that runs down to `U-TVS-SPI`, whose stated
return is `PWR_GND`. So as drawn, either `DIG_GND` is shorted to `UMB_CS`, or
`DIG_GND` is shorted to `PWR_GND` at the connector, or it connects to nothing.
All three are different boards. Meanwhile `U-TVS-CHAIN` on the **same page**
returns to `DIG_GND` `[repo hardware/controller/carrier.md:451]` while
`U-TVS-SPI` returns to `PWR_GND` `[repo hardware/controller/carrier.md:579]`,
for two looms that both leave the same board.

**Not resolved here** — it is the instrument-side half of `dig-gnd-topology`.
See §7.2.

### 3.5 `R-SPI-PULL`'s cable-side rail does not exist on the module

`hardware/bom.csv:49` — "**CABLE-SIDE CS PULLS TO 3V3, NOT +5V**" and
"**DAC-SIDE CS PULLS TO AVDD** (the LM317's 5.21V), not bus +5V". The same
instruction is in `docs/decisions/0004-cv-interface-module.md:391`.

But the row's own `category` is `module`, and
`hardware/module/digital-and-supervision.md:30-36` draws **all six** on the
module — where **there is no 3V3 net at all**. The only 3V3 in the project is
the instrument dev board's LDO `[repo hardware/controller/carrier.md:64,193-194]`,
which does not cross the umbilical
`[repo docs/decisions/0004-cv-interface-module.md:96-99]`.

**Netlist consequence:** three pull-ups with no defined rail. Either they move
to the carrier (and `R-SPI-PULL` becomes two BOM rows on two boards), or the
module-side rail is `M_BUS_P5V` and the 430 µA clamp argument has to be
re-answered. **Flagged, not resolved** — it is a rail decision, and it is
entangled with `digital-and-supervision.md:108-116`'s open "drop the bus +5 V
rail" question.

### 3.6 ADR 0004 still carries the superseded pin pairing inside itself

`docs/decisions/0004-cv-interface-module.md:96-99` gives
`SCLK / DIG_GND` and `MOSI / CS`, which is exactly the pairing the same ADR
reverses at `:830-831` (`SCLK / MOSI` on (4,5), `CS / DIG_GND` on (7,8)) and
which `hardware/module/digital-and-supervision.md:86-94` calls the corrected
map. The block at `:93-100` is headed "**Revised** conductor budget" and is
introduced at `:42-43` as "the authoritative 8-of-8 mapping".

**Two authoritative pin maps, 730 lines apart, in one file.** The map in §4
below follows `:828-831`, which both later pages and
`hardware/controller/carrier.md:50-51` agree with. The block at `:96-99` must
be corrected — see §5.9.

---

## 4. The canonical net table

**Columns:** canonical name | what it is | pages that touch it | aliases found
(`file:line`) | crosses the umbilical | board(s).

Boards: **M** = `PCB-MODULE`; **C** = `PCB-CARRIER`; **K** = `PCB-CLUSTER`
(×4, one subcircuit instantiated four times).

### 4A. The umbilical — eight conductors, exactly eight nets

Every net here exists on **both** M and C and is the same copper. These are the
only nets in the project that may be constructed in more than one SKiDL module,
and per `docs/reference/pcb-pipeline.md:66-69` they must be `Net.fetch`ed from
one shared module, never `Net()`d twice.

| Canonical | What it is | Pin | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|---|
| `UMB_BREATH_P` | Buffered sensor output, instrument→module; the in-amp's **IN−** | 1 | breath-receive, carrier, ADR 0004 | `BREATH` `[docs/decisions/0004-cv-interface-module.md:99,110,828,864,868]`; `BREATH (pin 1)` `[hardware/module/breath-receive-stage.md:22]`; `V_BREATH` `[hardware/module/breath-receive-stage.md:57]`; `BREATH` leg `[hardware/module/breath-receive-stage.md:182,209]`, `[hardware/bom.csv:65,104,125]`; `J-UMB pin 1 BREATH` `[hardware/controller/carrier.md:50,181-182]` | **yes** | M, C |
| `UMB_BREATH_N` | Sense return from the instrument's analog star; the in-amp's **IN+**. **Not a ground** | 2 | breath-receive, carrier, power-entry, ADR 0004 | `AGND` — 23 sites, §1.1 Meaning A; `AGND (pin 2)` `[hardware/module/breath-receive-stage.md:28]`; `V_AGND` `[hardware/module/breath-receive-stage.md:57]` | **yes** | M, C |
| `UMB_P12V` | Switched +12 V export, module→instrument, downstream of the LT1641 FET | 3 | power-entry, carrier, digital-and-supervision, ADR 0004 | `UMBILICAL +12V` `[hardware/module/power-entry.md:46]`; `+12V` `[hardware/controller/carrier.md:50,59,85,89,93,97,164]`; `+12 V on the umbilical` `[docs/decisions/0004-cv-interface-module.md:105,114]` | **yes** | M, C |
| `UMB_SCLK` | SPI2 clock, instrument→module, 2 MHz | 4 | digital-and-supervision, carrier, ADR 0004 | `SCLK` `[docs/decisions/0004-cv-interface-module.md:83,97,830]`, `[hardware/module/digital-and-supervision.md:23,31,86]`, `[hardware/bom.csv:49,50,103]`, `[hardware/controller/carrier.md:846]`; **`SCK`** `[hardware/controller/carrier.md:574]` | **yes** | M, C |
| `UMB_MOSI` | SPI2 data, instrument→module | 5 | digital-and-supervision, carrier, ADR 0004 | `MOSI` `[docs/decisions/0004-cv-interface-module.md:83,98,830]`, `[hardware/module/digital-and-supervision.md:25,31,86]`, `[hardware/controller/carrier.md:575,846]` | **yes** | M, C |
| `UMB_PWR_GND` | ~360 mA instrument power return | 6 | power-entry, carrier, ADR 0004 | `PWR_GND` `[docs/decisions/0004-cv-interface-module.md:96,608,624,797-798,829]`, `[hardware/controller/carrier.md:50,106,106,201,579,862]`, `[hardware/module/power-entry.md:493,501]` | **yes** | M, C |
| `UMB_CS` | SPI2 frame, instrument→module. The DAC's `SYNC` **before** the buffer | 7 | digital-and-supervision, carrier, ADR 0004 | `CS` `[docs/decisions/0004-cv-interface-module.md:84,98,831,843,882]`, `[hardware/module/digital-and-supervision.md:27,31,88,96]`, `[hardware/controller/carrier.md:576,846]` | **yes** | M, C |
| `UMB_DIG_GND` | SPI switching return | 8 | digital-and-supervision, carrier, ADR 0004 | `DIG_GND` `[docs/decisions/0004-cv-interface-module.md:45,97,609,627,831]`, `[hardware/module/digital-and-supervision.md:26,29,33,88]`, `[hardware/module/power-entry.md:496]`, `[hardware/controller/carrier.md:51,451,577]` | **yes** | M, C |

**Deleted, must produce no net:** `MISO` on the umbilical
`[docs/decisions/0004-cv-interface-module.md:38,113,846]`,
`[firmware/README.md:39,70]`; the second `GND` and the `spare`
`[docs/decisions/0004-cv-interface-module.md:39,44]`. A `-12V` conductor is
explicitly excluded `[docs/decisions/0004-cv-interface-module.md:50]`.

### 4B. Module returns — four, and they are not interchangeable

`docs/decisions/0004-cv-interface-module.md:604-632` names four. **Only three
had names.** The fourth is named here.

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `M_PWR_GND` | Instrument power return, etherCON pin 6 → the star at the Eurorack IDC ground pin, **on its own copper, touching nothing** | power-entry, ADR 0004, ROADMAP, pcb-pipeline | `PWR_GND (star)` `[hardware/module/power-entry.md:22]`; `PWR_GND` `[hardware/module/power-entry.md:38,44,406,493,501]`; `STAR POINT` `[hardware/module/power-entry.md:52]`; bare `GND` at the bus pin `[hardware/module/power-entry.md:52]`; `the star point` `[docs/decisions/0004-cv-interface-module.md:624]`; `the IDC's ground pin` `[hardware/module/power-entry.md:493]` | yes (=`UMB_PWR_GND`) | M |
| `M_DIG_GND` | SPI return, etherCON pin 8 → its own path. Return for the 74AHCT125 and (disputed) the DAC's digital side | digital-and-supervision, power-entry, ADR 0004 | `DIG_GND` `[hardware/module/digital-and-supervision.md:26,29,33,88]`, `[hardware/module/power-entry.md:496]`; bare `GND` `[hardware/module/digital-and-supervision.md:32]` | yes (=`UMB_DIG_GND`) | M |
| **`M_ARET`** | **The module's local analog return** — op-amps, DAC `AVDD` return, the in-amp's `REF` tie, every jack shunt cap. Its own region, joining `M_PWR_GND` at the star and nowhere else | all six module pages, ADR 0004, ADR 0003, pcb-pipeline | **six spellings** — see §2 row 1 | no | M |
| `UMB_BREATH_N` | *Not a return.* Listed here only because ADR 0004's table lists it and because every reader has to be told once | §4A | §4A | yes | M, C |

**`M_ARET` is the name this wave was asked to invent.** Rationale in §6.3.

### 4C. Module rails

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `M_BUS_P12V` | Eurorack bus +12 V at `J-PWR-EURO`, **before** `D1`/`D2` | power-entry, ADR 0004 | `+12V` `[hardware/module/power-entry.md:15]`; `bus +12V` `[docs/decisions/0004-cv-interface-module.md:299]` | no | M |
| `M_BUS_N12V` | Bus −12 V, before `D3` | power-entry, ADR 0004 | `-12V` `[hardware/module/power-entry.md:48]`; `bus -12V` `[docs/decisions/0004-cv-interface-module.md:310]` | no | M |
| `M_BUS_P5V` | Bus +5 V, no diode. Feeds the 74AHCT125 only | power-entry, digital-and-supervision | `+5V` `[hardware/module/power-entry.md:50]`; `bus +5 V` `[hardware/module/power-entry.md:115,466]`, `[hardware/module/digital-and-supervision.md:80,108,110]`; `bus +5V` `[hardware/module/digital-and-supervision.md:31]` | no | M |
| `M_P12V_A` | Module analog +12 V, after `D1`/`FB1`/`C1`. OPA2197 ×6, INA828, LM317 in, `R-LED-PANEL` | power-entry, pitch, mods, breath-rx, breath-out | `MODULE ANALOG +12V` `[hardware/module/power-entry.md:15]`; `+12 V analog` `[hardware/module/power-entry.md:468]`; `+` of `±12 V` `[hardware/module/pitch-stage.md:31]`, `[hardware/module/mod-channels.md:39]`, `[hardware/module/breath-receive-stage.md:33,72]`, `[hardware/module/breath-output-stage.md:58]` | no | M |
| `M_N12V_A` | Module analog −12 V, after `D3`/`FB3`/`C3`. Op-amp `V−`, `R-OFFNEG` source | power-entry, breath-out, pitch, mods | `MODULE ANALOG −12V` `[hardware/module/power-entry.md:48]`; `−12 V` `[hardware/module/breath-output-stage.md:48,102,110,126]`; `−` of `±12 V` (as above) | no | M |
| **`M_P12V_SW`** | **After `D2`/`FB2`/`C2`: LT1641 `VCC` and the high side of `R-ILIM`. Unnamed in the corpus** | power-entry | *none* — `hardware/module/power-entry.md:22` mislabels it `PWR_GND` (§3.1) | no | M |
| `M_SENSE` | LT1641 `SENSE` pin = low side of `R-ILIM` = FET drain. **Kelvin pair with `M_P12V_SW`** | power-entry, pcb-pipeline | `SENSE` `[hardware/module/power-entry.md:28,231]`; `SENSE`/`R-ILIM` Kelvin pair `[docs/reference/pcb-pipeline.md:188-189]` | no | M |
| `M_AVDD` | LM317LZ output, 5.21 V. DAC `AVDD`, `R-CLR-PU`, `R-LDAC`, `TRIM-BREATH-ZERO` top, `POT-OFFSET` top | power-entry, digital-and-supervision, breath-rx, breath-out | nine spellings — see §2 row 9. ⚠ §7.4 | no | M |
| `M_LM317_ADJ` | LM317 `ADJ`, 150R/475R junction | power-entry | *none* `[hardware/module/power-entry.md:18-19]` | no | M |

### 4D. Module load switch

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `M_SW_ON` | LT1641 `ON` pin; panel toggle + the UV divider that is **still not designed** | power-entry | `ON` `[hardware/module/power-entry.md:29,198,239-240,434,442]`; `panel toggle` `[hardware/module/power-entry.md:29-30,440]` | no | M |
| `M_SW_TIMER` | LT1641 `TIMER`, `C-TIMER-LOADSW` | power-entry | `TIMER` `[hardware/module/power-entry.md:32,198,235,314,333,380,485]` | no | M |
| `M_SW_GATE` | LT1641 `GATE`, before `R-GATE-SER` | power-entry | `GATE` `[hardware/module/power-entry.md:32,400]` | no | M |
| `M_SW_GATE_FET` | After `R-GATE-SER`, at the FET gate | power-entry | `FET gate` `[hardware/module/power-entry.md:400]` | no | M |
| `M_SW_GATE_COMP` | `R-GATE-COMP` ↔ `C-GATE-LOADSW` junction | power-entry | *none* `[hardware/module/power-entry.md:402-404]` | no | M |
| `M_SW_FB` | LT1641 `FB`, the `R-FB-HI`/`R-FB-LO` tap | power-entry | `FB` `[hardware/module/power-entry.md:33,182-234,253,287,298,334]`; `V_FB` `[hardware/module/power-entry.md:194,253,284-287,303]` | no | M |
| `M_SW_PWRGD` | LT1641 `PWRGD`, open drain. **Drawn nowhere** (§3.2) | power-entry | `PWRGD` `[hardware/module/power-entry.md:231,254,261-266,285-286]` | no | M |
| `M_LED_PANEL_A` | `R-LED-PANEL` ↔ `LED-PANEL` anode | power-entry | *none* `[hardware/module/power-entry.md:468]` | no | M |

### 4E. Module digital

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `M_DAC_SCLK` | 74AHCT125 output → DAC `SCLK`. **Not `UMB_SCLK`** | digital-and-supervision | `SCLK` (drawing) `[hardware/module/digital-and-supervision.md:36]`; "the DAC's `SCLK`" `[hardware/module/digital-and-supervision.md:123]`, `[hardware/bom.csv:49]` | no | M |
| `M_DAC_DIN` | 74AHCT125 output → DAC `DIN`. **Not `UMB_MOSI`** | digital-and-supervision | `MOSI` (drawing) `[hardware/module/digital-and-supervision.md:36]`; `DIN` `[hardware/module/digital-and-supervision.md:123]`, `[hardware/bom.csv:10,49,85,100,117]` | no | M |
| `M_DAC_SYNC` | 74AHCT125 output → DAC `SYNC`. **Not `UMB_CS`** | digital-and-supervision | `CS` (drawing) `[hardware/module/digital-and-supervision.md:36]`; `SYNC` `[hardware/module/digital-and-supervision.md:123]`, `[hardware/bom.csv:49]` | no | M |
| `M_DAC_CLR` | DAC `CLR`, active low, `R-CLR-PU` to `M_AVDD`, `LK-CLR` pad to `M_ARET` | digital-and-supervision, mods, breath-rx, pitch | `CLR` `[hardware/module/digital-and-supervision.md:42,72-74,159,161,203,209]`, `[hardware/module/mod-channels.md:65,83,151,156,163,173,231-234]`, `[hardware/module/breath-receive-stage.md:292-308]`, `[hardware/module/pitch-stage.md:141]` | no | M |
| `M_DAC_LDAC` | DAC `LDAC`, tied via `R-LDAC` to `M_AVDD`, not driven | digital-and-supervision | `LDAC` `[hardware/module/digital-and-supervision.md:49,247]` | no | M |
| `M_BUF_OE` | 74AHCT125 `OE` ×4, tied to `M_DIG_GND`, permanently enabled | digital-and-supervision, power-entry, ADR 0004 | `OE` `[hardware/module/digital-and-supervision.md:32,79,82,147,179,210]`, `[hardware/module/power-entry.md:464,467]`, `[docs/decisions/0004-cv-interface-module.md:104,387]` | no | M |
| `M_VREFOUT` | DAC `VREFOUT` pin | pitch, mods, breath-rx, pcb-pipeline | `VREFOUT` `[hardware/module/pitch-stage.md:8,14,92,99-100,129,144,352,354]`, `[hardware/module/mod-channels.md:90,203,231]`, `[hardware/module/breath-receive-stage.md:163,319-324]`, `[hardware/bom.csv:13,51,111,113]` | no | M |

### 4F. Module pitch channel

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `M_DAC_CH1` | DAC channel 1 output | pitch | `DAC ch1` `[hardware/module/pitch-stage.md:21]` | no | M |
| `M_PITCH_INP` | `R-OPAMP-IN` ↔ op-amp (+); `C-AA-PITCH` to `M_ARET`; `R-BIAS-DAC` is at the **DAC pin**, not here | pitch | "the `R-OPAMP-IN` node" `[hardware/module/pitch-stage.md:202]` | no | M |
| `M_TRIM_OFF_W` | `TRIM-OFFSET` wiper → the `V_ref` follower's (+) | pitch | *none* `[hardware/module/pitch-stage.md:14]` | no | M |
| **`M_VREF_PITCH`** | **2.500 V, trimmed then buffered.** Pitch's intercept reference | pitch, pcb-pipeline | `V_ref ≈ 2.500 V` `[hardware/module/pitch-stage.md:14]`; `V_ref` `[hardware/module/pitch-stage.md:57-58,72,76,129,280]`; `V_ref` `[docs/reference/pcb-pipeline.md:184]` | no | M |
| `M_PITCH_FBN` | Op-amp (−): `R1`(LT5400) ↔ `C-FB-PITCH` ↔ `R2`(LT5400) | pitch | *none* `[hardware/module/pitch-stage.md:26-35]` | no | M |
| `M_PITCH_OUT` | Op-amp output; `C-FB-PITCH` source; `D-JACK-CLAMP`; `R-OUT-PROT` in | pitch | `op-amp output` `[hardware/module/pitch-stage.md:25]`; "the op-amp *output*" `[hardware/module/pitch-stage.md:179,207,216]` | no | M |
| `M_PITCH_TRIMW` | `R2`(LT5400) ↔ `TRIM-GAIN`, in series | pitch | *none* `[hardware/module/pitch-stage.md:35]` | no | M |
| `M_PITCH_JACK` | `R-OUT-PROT` out; `C-FILT-PITCH` to `M_ARET`; **the DC feedback tap** | pitch, ADR 0004 | `PITCH jack` `[hardware/module/pitch-stage.md:35]`; `PITCH` `[hardware/module/pitch-stage.md:269]`, `[docs/decisions/0004-cv-interface-module.md:643]` | no | M |
| `M_LT5400_PAD` | LT5400 exposed pad, pin 9, **floating, 5.5 pF to the network, destination undecided** | pitch, pcb-pipeline, figures | *none* `[hardware/module/pitch-stage.md:322-334]`, `[docs/reference/pcb-pipeline.md:95-101]` | no | M |

### 4G. Module mod channels 1–4

Four identical instances. `n` ∈ {1,2,3,4}, driven by DAC channels 2–5.

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `M_DAC_CH7` | DAC channel 7, the shared offset source | mods | `DAC ch7` `[hardware/module/mod-channels.md:20,198]` | no | M |
| `M_MODREF_INP` | `R-OPAMP-IN` ↔ the shared follower's (+) | mods | `[1k]` `[hardware/module/mod-channels.md:20]`; "its own `R-OPAMP-IN`" `[hardware/module/mod-channels.md:201]` | no | M |
| **`M_VREF_MOD`** | **3.3333 V buffered**, to four `R1` 10 k. ~1.3 mA | mods, pcb-pipeline | `V_ref = 3.3333 V` `[hardware/module/mod-channels.md:20]`; `V_ref` `[hardware/module/mod-channels.md:6,54,57,66,101]`; "the mods' shared 3.3333 V" `[docs/reference/pcb-pipeline.md:184]` | no | M |
| `M_DAC_CH<2..5>` | Signal channels | mods | `DAC ch2` `[hardware/module/mod-channels.md:29]`; "(ch3, ch4, ch5 identical)" `[hardware/module/mod-channels.md:26-27]` | no | M |
| `M_MODn_INP` | `R-OPAMP-IN` ↔ op-amp (+) | mods | `[1k]` `[hardware/module/mod-channels.md:29]` | no | M |
| `M_MODn_FBN` | Op-amp (−): `R1` 10 k ↔ `R2` 30 k | mods | *none* `[hardware/module/mod-channels.md:34-37]` | no | M |
| `M_MODn_OUT` | Op-amp output; `R2` tap; `D-JACK-CLAMP`; `R-OUT-PROT` in | mods | `op-amp output` `[hardware/module/mod-channels.md:33]` | no | M |
| `M_MODn_JACK` | `R-OUT-PROT` out; `C-FILT-MOD` 82 nF to `M_ARET` | mods, pitch, ADR 0004 | `MOD n jack` `[hardware/module/mod-channels.md:45]`; `MOD` `[hardware/module/pitch-stage.md:269]`; `MOD 1–4` `[docs/decisions/0004-cv-interface-module.md:643]` | no | M |

### 4H. Module breath receive

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `M_INA_INN` | INA828 `IN−`, after `R3` 10 k 0.1 %; `C_cm` to `M_ARET`; `R5` 1 M to `M_ARET`; `D-CLAMP-BREATH` | breath-rx | `IN−` `[hardware/module/breath-receive-stage.md:50]`; "↓ to IN−, via R3" `[hardware/module/breath-receive-stage.md:23]` | no | M |
| `M_INA_INP` | INA828 `IN+`, after `R2` 10 k 0.1 %; `C_cm` to `M_ARET`; `R4` 1 M to `M_ARET`; `D-CLAMP-BREATH` | breath-rx, bom | `IN+` `[hardware/module/breath-receive-stage.md:50]`; "↑ to IN+, via R2" `[hardware/module/breath-receive-stage.md:29]`; "AGND drives IN+" `[hardware/bom.csv:28]` | no | M |
| `M_INA_RG_A` / `_B` | `R_G` 42.2 k across the two `R_G` pins | breath-rx | `R_G 42.2k` `[hardware/module/breath-receive-stage.md:52,162]` | no | M |
| `M_TRIM_BZ_W` | `TRIM-BREATH-ZERO` wiper → its buffer's (+). Ranged 0 → +1.0 V off `M_AVDD` | breath-rx | `[TRIM-BREATH-ZERO]` `[hardware/module/breath-receive-stage.md:54]` | no | M |
| `M_INA_REF` | INA828 `REF`, driven **hard by a buffer**; `R_REF` must be < 5 Ω `[hardware/bom.csv:28]` | breath-rx, ADR 0004 | `REF` `[hardware/module/breath-receive-stage.md:54,77,93,115,141,146,163]`; `V_REF` `[hardware/module/breath-receive-stage.md:57,80]`; "the in-amp's `REF` tie" `[docs/decisions/0004-cv-interface-module.md:629]` | no | M |
| `M_INA_OUT` | INA828 output. 0 V at rest, −9.94 V at sensor FS | breath-rx, breath-out | six spellings — §2 row 22 | no | M |

### 4I. Module breath gain/offset and response

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `M_BR_GAIN_W` | `POT-GAIN` wiper → follower (+) | breath-out | `[POT-GAIN 50k]` `[hardware/module/breath-output-stage.md:35]` | no | M |
| `M_BR_GAIN_LO` | `POT-GAIN` bottom ↔ `R-GAIN-FLOOR` 7.15 k | breath-out | *none* `[hardware/module/breath-output-stage.md:38]` | no | M |
| `M_BR_GAIN_BUF` | Follower out → `R-IN` 10 k | breath-out | `buffered attenuator` `[hardware/module/breath-output-stage.md:36-38]` | no | M |
| `M_BR_OFF_W` | `POT-OFFSET` wiper → `R-OFF` 21.0 k. **Unbuffered by decision** | breath-out | `wiper` `[hardware/module/breath-output-stage.md:44]` | no | M |
| `M_BR_SUM` | Summing node, op-amp (−): `R-IN`, `R-OFF`, `R-OFFNEG`, `R-FB` | breath-out | *none* `[hardware/module/breath-output-stage.md:46-51]` | no | M |
| `M_BR_OUT` | Summer output; `R-FB` source; `D-JACK-CLAMP`; `R-OUT-PROT` in | breath-out | *none* `[hardware/module/breath-output-stage.md:54-56]` | no | M |
| `M_BREATH_JACK` | `R-OUT-PROT` out; `C-OUT-BREATH` 330 nF to `M_ARET` | breath-out, breath-rx, pitch | `BREATH jack` `[hardware/module/breath-output-stage.md:64]`, `[hardware/module/breath-receive-stage.md:74]`; `BREATH` `[hardware/module/pitch-stage.md:269]`, `[docs/decisions/0004-cv-interface-module.md:643]` | no | M |
| `M_RESP_HALF` | `V_in/2`, the 10 k/10 k divider off `M_INA_OUT`, one end of `POT-RESP` | breath-out §4 | `V_in/2` `[hardware/module/breath-output-stage.md:201,211]` | no | M |
| `M_RESP_X` | Shaper's virtual ground, op-amp (−): `R1` 20 k, `R2` 10 k, `R-RESP` | breath-out §4 | `X (virtual gnd)` `[hardware/module/breath-output-stage.md:190,207]` | no | M |
| `M_RESP_OUT` | Shaper output, `−V_in/2`, other end of `POT-RESP` | breath-out §4 | `V_shaped` `[hardware/module/breath-output-stage.md:193,201]` | no | M |
| `M_RESP_W` | `POT-RESP` wiper → `R-RESP` 15 k | breath-out §4 | `wiper` `[hardware/module/breath-output-stage.md:203]` | no | M |
| `M_RESP_D` | `R-RESP` ↔ `D-RESP` antiparallel pair | breath-out §4 | *none* `[hardware/module/breath-output-stage.md:205-207]` | no | M |
| **`M_RESP_RESTORE`** | **The ×2 inverting restore stage's output**, which is what actually reaches `POT-GAIN` once §4 is fitted | breath-out §4 | *none* — `[hardware/module/breath-output-stage.md:265]` states the half exists; `:298-301` states the insertion point; **no drawing connects them** | no | M |

⚠ `breath-output-stage.md:35` draws `POT-GAIN`'s input as "from the INA828",
but `:298-301` inserts the response shaper *between* the in-amp and the
attenuator. **With §4 fitted, `POT-GAIN`'s input is `M_RESP_RESTORE`, not
`M_INA_OUT`.** Two drawings on one page, contradicting each other about one
net. See §5.6.

### 4J. Instrument (carrier) — power

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `I_P12V` | = `UMB_P12V`. LED strips, REF5050, OPA2197 `V+`, `L-BUCK-IN` | carrier | `+12V` `[hardware/controller/carrier.md:50,59,85,89,93,97,164]`; `12 V` `[hardware/controller/carrier.md:860,880]` | yes | C |
| `I_PWR_GND` | = `UMB_PWR_GND`. The instrument's power return pour, and `MECH-GNDBOND` | carrier, bom | `PWR_GND` `[hardware/controller/carrier.md:50,106,106,119,201,579,862]`; `PWR_GND pour` `[hardware/controller/carrier.md:106]` | yes | C |
| `I_BUCK_IN` | After `L-BUCK-IN`; `C-BUCK-IN` 100 µF electrolytic; both `R-78E5.0` inputs | carrier | *none* `[hardware/controller/carrier.md:99-104]` | no | C |
| `I_5V_A` | `R-78E5.0 A` output, before `D-USBOR` | carrier | `5V` `[hardware/controller/carrier.md:60]` | no | C |
| `I_5V_DEV` | Dev-board 5 V pin: the OR node of `D-USBOR` A and USB VBUS. Also the 74AHCT125 rail and the 8×8 matrix | carrier | `dev board 5V` `[hardware/controller/carrier.md:99]`; `5V` `[hardware/controller/carrier.md:64]`; "74AHCT125 rail = 5 V" `[hardware/controller/carrier.md:677]` | no | C |
| `I_5V_B` | `R-78E5.0 B` output, before `D-USBOR` | carrier | *none* `[hardware/controller/carrier.md:104]` | no | C |
| `I_5V_DISP` | OR node at the display board | carrier | `J-DISP 5V` `[hardware/controller/carrier.md:104]`; `5 V` `[hardware/controller/carrier.md:762]` | no | C |
| `I_3V3` | Dev-board LDO output. **Also the MCP3202's voltage reference**, and the 24 key pull-ups | carrier, cluster | `3V3` `[hardware/controller/carrier.md:64,69,447]`, `[hardware/controller/cluster-boards.md:94,131,244,256,300]`; `VDD/VREF = 3V3` `[hardware/controller/carrier.md:192]` | no | C, K |
| `I_PLATE` | Aluminium key plate, bonded to `I_PWR_GND` via `MECH-GNDBOND` | carrier, cluster, bom | "aluminium key plate" `[hardware/controller/carrier.md:108]`; `[hardware/bom.csv:55]` | no | C, K |

### 4K. Instrument — analog front end

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| **`I_ARET`** | **The instrument's local analog return / analog star point.** Joins `I_PWR_GND` at **one** tie, at `J-UMB` | carrier, breath-rx, ADR 0003 | **five spellings** — §2 row 2 | no | C |
| `I_VREF5` | REF5050 output, 5.000 V, → the buffer's (+) | carrier | `5.000 V` `[hardware/controller/carrier.md:164]` | no | C |
| `I_VS` | Sensor `VS` pin, after `R-ISO-REF`; `C-DECOUPLE-CARRIER` 100 nF; the in-loop feedback tap | carrier, breath-rx | `SKT-BREATH pin VS` `[hardware/controller/carrier.md:168]`; `VS` `[hardware/controller/carrier.md:241,247]`, `[hardware/module/breath-receive-stage.md:343,351]`; ⚠ `VS = REF5050 5.000 V` `[hardware/module/breath-receive-stage.md:24]` conflates it with `I_VREF5` | no | C |
| `I_SENSOR_OUT` | MPXV4006DP `Vout`, 0.2–4.80 V → the breath buffer's (+) | carrier | `MPXV4006DP Vout  0.2 – 4.80 V` `[hardware/controller/carrier.md:179]`; `MPXV4006DP` `[hardware/module/breath-receive-stage.md:22]` | no | C |
| `I_BREATH_BUF` | Breath buffer output (on +12 V) → `R-SER-BREATH-INST` (R1) and the ADC divider | carrier, breath-rx | "½ OPA2197" `[hardware/controller/carrier.md:181]`, `[hardware/module/breath-receive-stage.md:22]` | no | C |
| `I_ADC_DIV` | `R-ADCDIV-U` ↔ `R-ADCDIV-L` tap; `C-AA-ADC` 47 nF to `I_ARET`; MCP3202 `CH0` | carrier | *none* `[hardware/controller/carrier.md:185-191]` | no | C |
| `I_ADC_CH1` | MCP3202 `CH1`, spare | carrier | `CH1 = spare` `[hardware/controller/carrier.md:195]` | no | C |
| `I_ADC_DOUT` | MCP3202 `DOUT` → IO37. **Never leaves the board** | carrier | **`MISO`** `[hardware/controller/carrier.md:580]` | no | C |
| `I_ADC_CS` | IO39 → MCP3202 `CS` | carrier | **`CS`** `[hardware/controller/carrier.md:581]` | no | C |
| `I_SPI2_SCK_RAW` | IO35, **before** `R-SPI-SER`. Also the MCP3202's `CLK` (§3.3 — decision) | carrier | `IO35 SCK` `[hardware/controller/carrier.md:574]` | no | C |
| `I_SPI2_MOSI_RAW` | IO36, **before** `R-SPI-SER`. Also the MCP3202's `DIN` | carrier | `IO36 MOSI` `[hardware/controller/carrier.md:575]` | no | C |
| `I_SPI2_CS_RAW` | IO34, before `R-SPI-SER` | carrier | `IO34 CS` `[hardware/controller/carrier.md:576]` | no | C |

### 4L. Instrument — key chain and LEDs

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `I_CHAIN_SCK_RAW` | IO38, before `R-CHAIN-SER` | carrier | `IO38 SPI3 SCK` `[hardware/controller/carrier.md:439]` | no | C |
| `I_CHAIN_SCK` | After `R-CHAIN-SER`. `J-CHAIN` pin 2 → all four 74HC165 `CLK` pins. **A bus** | carrier, cluster, bom | `SCK` `[hardware/controller/carrier.md:439,875]`, `[hardware/controller/cluster-boards.md:243,254,277]`, `[hardware/bom.csv:73,94,95]`; `CLK` `[hardware/controller/cluster-boards.md:95,262]` | no | C, K |
| `I_CHAIN_SHLD_RAW` | IO7, before `R-CHAIN-SER` | carrier | `IO7 latch` `[hardware/controller/carrier.md:69,441]` | no | C |
| `I_CHAIN_SHLD` | After `R-CHAIN-SER`. `J-CHAIN` pin 4 → all four `SH/LD`. **A bus** | carrier, cluster, bom | `SH/LD` `[hardware/controller/carrier.md:441,511,833,875]`, `[hardware/controller/cluster-boards.md:94,243,255,262]` | no | C, K |
| `I_CHAIN_SER_RAW` | IO33, before `R-CHAIN-SER` | carrier, cluster | `IO33 SER out` `[hardware/controller/carrier.md:443]`; `IO33` `[hardware/controller/cluster-boards.md:304]` | no | C |
| `I_CHAIN_SER` | After `R-CHAIN-SER`. `J-CHAIN` pin 6, **a pass-through** to the chain-end board's `SER`, where `R-SER-TERM` 10 k pulls to `I_3V3` | carrier, cluster | `SER` `[hardware/controller/carrier.md:443,465,875]`, `[hardware/controller/cluster-boards.md:243,258,266,296]`; `serial in` `[hardware/controller/cluster-boards.md:100]` | no | C, K |
| `I_CHAIN_QH_RT` | `right_thumb` `QH` → `J-CHAIN` IN pin 8 → **IO40**. The chain's only output to the MCU | carrier, cluster | `QH` `[hardware/controller/carrier.md:445]`, `[hardware/controller/cluster-boards.md:244,264]`; **`MISO`** `[hardware/controller/carrier.md:445]`; `serial out` `[hardware/controller/cluster-boards.md:101]` | no | C, K |
| `I_CHAIN_QH_RH` | `right_hand` `QH` → `right_thumb` `SER` | cluster | `QH` / pin 8 `[hardware/controller/cluster-boards.md:264-267,280-284]` | no | K |
| `I_CHAIN_QH_LT` | `left_thumb` `QH` → `right_hand` `SER` | cluster | as above | no | K |
| `I_CHAIN_QH_LH` | `left_hand` `QH` → `left_thumb` `SER` | cluster | as above | no | K |
| `I_CHAIN_GND` | `J-CHAIN` pins 1,3,5,7,9 — **five conductors, one net.** Which of the four returns is undeclared (§7.2) | carrier, cluster, bom | `GND` `[hardware/controller/carrier.md:438,440,442,444,446]`, `[hardware/controller/cluster-boards.md:243-244,257]`; `GND ×5` `[hardware/controller/cluster-boards.md:257]` | no | C, K |
| `I_LED_DATA_L` | IO1 → `R-LED-PD` 10 k and 74AHCT125 gate A in | carrier | `IO1` `[hardware/controller/carrier.md:666,668]` | no | C |
| `I_LED_DATA_R` | IO2 → `R-LED-PD` and gate C in | carrier | `IO2` `[hardware/controller/carrier.md:672,674]` | no | C |
| `I_LED_L_DI` | Gate A out → `R-LED-SER` 220 R → `J-LED-L` `DI` | carrier | `J-LED-L DI` `[hardware/controller/carrier.md:668]` | no | C |
| `I_LED_R_DI` | Gate C out → 220 R → `J-LED-R` `DI` | carrier | `J-LED-R DI` `[hardware/controller/carrier.md:674]` | no | C |
| `I_LED_BI` | `J-LED-L`/`-R` `BI` pins, **tied to the strip's ground at the strip end** — not a driven net | carrier | `BI ──► GND` `[hardware/controller/carrier.md:669,675]`; `[hardware/controller/carrier.md:716-721,860]` | no | C |
| `I_DISP_RX` / `I_DISP_TX` | IO5 → display RX, IO6 ← display TX. UART1 | carrier | `IO5 → display RX, IO6 ← display TX` `[hardware/controller/carrier.md:764]` | no | C |
| `I_U0TXD` / `I_U0RXD` | IO43 / IO44 → `HDR-SERVICE` | carrier | `U0TXD(IO43)  U0RXD(IO44)` `[hardware/controller/carrier.md:775]`; `IO43/IO44` `[hardware/controller/carrier.md:69]` | no | C |

### 4M. Cluster board (×4) — one subcircuit, four instances

| Canonical | What it is | Pages | Aliases `[file:line]` | Umb | Board |
|---|---|---|---|---|---|
| `K_VCC` | 74HC165 pin 16 = `I_3V3`; `C-DECOUPLE-165` at the package | cluster | `3V3` `[hardware/controller/cluster-boards.md:94,131]` | no | K |
| `K_CLK_INH` | 74HC165 pin 15, **tied low permanently** | cluster | `CLK INH` `[hardware/controller/cluster-boards.md:95,104,262,490]`, `[hardware/controller/carrier.md:479]` | no | K |
| `K_QH_BAR` | 74HC165 pin 7, an output, **left open — do not ground** | cluster | `QH_bar` `[hardware/controller/cluster-boards.md:100,105,490]` | no | K |
| `K_KEY_<A..H>` | The eight parallel inputs. `R-KEY-PU` to `I_3V3`, `C-KEY` to `K_GND`, `R-KEY-SER` to the switch — **or** a marker strap straight to a rail | cluster | `A`…`H` `[hardware/controller/cluster-boards.md:96-99,319-324,365-370]`; `E (D4)` … `H (D7)` `[hardware/controller/cluster-boards.md:96-99]` | no | K |
| `K_SW_<n>` | `R-KEY-SER` ↔ the KS-33 switch pin | cluster | `SW  KS-33` `[hardware/controller/cluster-boards.md:137]` | no | K |
| `K_GND` | 74HC165 pin 8, `C-KEY` returns, switch returns, `C-DECOUPLE-165` return, `CLK INH` tie, low markers | cluster | `GND` `[hardware/controller/cluster-boards.md:95,97,101,137,139,262,499]` | no | K |

⚠ `K_GND` and `I_CHAIN_GND` are almost certainly one net, but **nothing in the
corpus says so** and nothing says which of the four returns either is. §7.2.

---

## 5. The rename list — per page, exactly which strings change

Each row is: the literal string, its line, and its replacement. Where a string
occurs more than once on a line, the count is given. These are edits to the
**drawings and their labels**; prose that *discusses* a name may keep it if it
is disambiguated in the same sentence, but the tables below mark prose edits
that are load-bearing.

### 5.1 `hardware/module/power-entry.md`

| Line | From | To |
|---|---|---|
| 15 | `+12V` (bus pin label) | `M_BUS_P12V` |
| 15 | `MODULE ANALOG +12V` | `M_P12V_A` |
| 18 | `DAC AVDD 5.21V` | `M_AVDD  (5.21 V)` |
| 22 | `──┬──────── PWR_GND (star)` | **redraw.** `D2`/`FB2`/`C2` output is `M_P12V_SW`; `C2`'s return is `M_PWR_GND`. See §3.1 — this is a circuit fix, not a rename |
| 38, 44 | `PWR_GND` | `M_PWR_GND` |
| 46 | `UMBILICAL +12V` | `UMB_P12V` |
| 48 | `-12V` (bus) → `M_BUS_N12V`; `MODULE ANALOG −12V` | `M_N12V_A` |
| 50 | `+5V` | `M_BUS_P5V` |
| 52 | `GND` … `STAR POINT` | `M_PWR_GND  ← star origin` |
| 400 | `GATE` / `FET gate` | `M_SW_GATE` / `M_SW_GATE_FET` |
| 406 | `PWR_GND` | `M_PWR_GND` |
| 468 (prose) | "+12 V analog" | "`M_P12V_A`" |
| 493-502 (prose) | `PWR_GND`, "The analog return", `DIG_GND`, `AGND` | `M_PWR_GND`, `M_ARET`, `M_DIG_GND`, `UMB_BREATH_N` |

**Add:** a label for `M_P12V_SW`, `M_SENSE`, `M_SW_GATE_COMP`, `M_LM317_ADJ`,
and an explicit `NC` on `PWRGD` (§3.2).

### 5.2 `hardware/module/digital-and-supervision.md`

| Line | From | To |
|---|---|---|
| 23 | `4 SCLK` | `4 UMB_SCLK` |
| 25 | `5 MOSI` | `5 UMB_MOSI` |
| 26 | `SCLK+MOSI share pair (4,5)` | keep; names updated |
| 26 | `CS+DIG_GND share pair (7,8)` | `UMB_CS + UMB_DIG_GND` |
| 27 | `7 CS` | `7 UMB_CS` |
| 29 | `8 DIG_GND` | `8 UMB_DIG_GND` |
| 31 | `SCLK↓ MOSI↓ CS↑` (**cable side**) | `UMB_SCLK↓ UMB_MOSI↓ UMB_CS↑` |
| 31 | `bus +5V` | `M_BUS_P5V` |
| 32 | `OE x4 → GND` | `OE x4 → M_DIG_GND` |
| 33 | `DIG_GND` | `M_DIG_GND` |
| **36** | `SCLK↓ MOSI↓ CS↑` (**DAC side**) | **`M_DAC_SCLK↓ M_DAC_DIN↓ M_DAC_SYNC↑`** ← *the single highest-value edit on this page* |
| 40, 42, 43, 49, 50 | `AVDD 5.21V` / `AVDD` | `M_AVDD` |
| 45, 47 | `solder pad to GND` / `GND` | `LK-CLR pad to M_ARET` / `M_ARET` |
| 53 | `analog star, single tie (ADR 0004)` | `M_ARET, single tie to M_PWR_GND at the star (ADR 0004)` |
| 73 (prose) | `` `[R-CLR-PD 10k]` to `AGND` `` | "…to `M_ARET`" |
| 123 (prose) | "the DAC's `SCLK`, `DIN` and `SYNC`" | "`M_DAC_SCLK`, `M_DAC_DIN`, `M_DAC_SYNC`" |

**Also add:** the DAC's `SCLK`/`DIN`/`SYNC` pin names beside the buffer
outputs, so the drawing and the prose agree without a cross-reference.

### 5.3 `hardware/module/pitch-stage.md`

| Line | From | To |
|---|---|---|
| 14 | `VREFOUT` | `M_VREFOUT` |
| 14 | `V_ref ≈ 2.500 V` | **`M_VREF_PITCH` ≈ 2.500 V** |
| 21 | `DAC ch1` | `M_DAC_CH1` |
| 25 | `op-amp output` | `M_PITCH_OUT` |
| 31 | `±12 V` | `M_P12V_A / M_N12V_A` |
| 35 | `PITCH jack` | `M_PITCH_JACK` |
| **202** | ``10 nF from the `R-OPAMP-IN` node to `AGND` `` | **"…to `M_ARET`"** |
| 128-136 (value table) | `V_ref` | `M_VREF_PITCH` |
| 269 (prose) | "joining PITCH to the MOD (82 nF) or BREATH (330 nF) jacks" | "`M_PITCH_JACK` to `M_MODn_JACK` … or `M_BREATH_JACK`" |
| 322-334 | (exposed pad) | add the label `M_LT5400_PAD` so it has a net to be assigned to |

### 5.4 `hardware/module/mod-channels.md`

| Line | From | To |
|---|---|---|
| 6, 101 (prose) | `V_ref` = **3.3333 V** | **`M_VREF_MOD`** |
| 20 | `DAC ch7` | `M_DAC_CH7` |
| 20 | `V_ref = 3.3333 V` | **`M_VREF_MOD` = 3.3333 V** |
| 29 | `DAC ch2` | `M_DAC_CH2` |
| 33 | `op-amp output` | `M_MODn_OUT` |
| 39 | `±12 V` | `M_P12V_A / M_N12V_A` |
| **43** | ``[C-FILT-MOD 82nF]── AGND`` | **`── M_ARET`** |
| 45 | `MOD n jack` | `M_MODn_JACK` |

### 5.5 `hardware/module/breath-receive-stage.md`

The densest page. Six distinct renames in the drawing alone.

| Line | From | To |
|---|---|---|
| 22 | `BREATH (pin 1)` | **`UMB_BREATH_P` (pin 1)** |
| 22 | `[R1 1k]` | `[R-SER-BREATH-INST · R1]` (refdes, §8) |
| 24 | `(VS = REF5050 5.000 V)` | `(I_VS, from I_VREF5 through R-ISO-REF)` — **the two are separated by `R-ISO-REF`** `[hardware/controller/carrier.md:166,228-250]` |
| **28** | `analog star ──[R1b 1k]──── AGND (pin 2)` | **`I_ARET ──[R-SER-BREATH-INST · R1b]──── UMB_BREATH_N (pin 2)`** |
| 26 | `MCP3202 CH0` | `I_ADC_DIV → MCP3202 CH0` |
| 33 | `BAV99 to ±12 V, both legs` | `D-CLAMP-BREATH to M_P12V_A / M_N12V_A` |
| **39, 43, 47 (×2), 70** | `AGND(module)` | **`M_ARET`** (five sites) |
| 54 | `REF` | `M_INA_REF` |
| 55 | `from the LM317 5.21 V` | `from M_AVDD` |
| 57 | `Vout = −2.185·(V_BREATH − V_AGND) + V_REF` | `… −2.185·(UMB_BREATH_P − UMB_BREATH_N) + M_INA_REF` |
| 70 | `[1k]─┼─[C 330nF]` | `[R-OUT-PROT]─┼─[C-OUT-BREATH 330nF]` |
| 72 | `[BAV99]── ±12 V` | `[D-JACK-CLAMP]── M_P12V_A / M_N12V_A` |
| **74** | `BREATH jack` | **`M_BREATH_JACK`** |
| 156-164 (value table) | `AGND` leg / `BREATH` leg | `UMB_BREATH_N` leg / `UMB_BREATH_P` leg |
| 182, 209, 221 (prose) | `` `BREATH` conductor``, `` `AGND` leg`` | `UMB_BREATH_P`, `UMB_BREATH_N` |
| 232 (prose) | "`AGND` carries no power current … 1 MΩ to module analog ground" | "`UMB_BREATH_N` … 1 MΩ to `M_ARET`" |
| 60-70 | the block "INVERTING gain + offset" | label its input `M_INA_OUT` and its output `M_BR_OUT` |

### 5.6 `hardware/module/breath-output-stage.md`

| Line | From | To |
|---|---|---|
| 34-35 | `from the INA828 / 0 … −4.7 V` | **`M_INA_OUT`** — *and see the §4 conflict below* |
| 36-38 | `buffered attenuator` | `M_BR_GAIN_BUF` |
| **41** | `AGND(module)` | **`M_ARET`** |
| 43-44 | `buffered +5.21 V (LM317 rail)` | **`M_AVDD`** — *or name the buffer, §7.4* |
| 48 | `−12 V` | `M_N12V_A` |
| **55** | `AGND` (summer's **(+) input**) | **`M_ARET`** |
| 58 | `±12 V` | `M_P12V_A / M_N12V_A` |
| **62** | `[C-OUT-BREATH 330nF film]── AGND` | **`── M_ARET`** |
| **64** | `BREATH jack` | **`M_BREATH_JACK`** |
| 190 | `in-amp out (0…−9.94V)` | `M_INA_OUT` |
| 190, 207 | `X (virtual gnd)` | `M_RESP_X` |
| 193, 201 | `V_shaped` | `M_RESP_OUT` |
| 201, 211 | `V_in/2` | `M_RESP_HALF` |
| **199** | `GND` | **`M_ARET`** |
| 203 | `wiper` | `M_RESP_W` |
| 189, 266 | `R1 20k`, `R2 10k` | `R-RESP-IN`, `R-RESP-FB` (§8) |

**⚠ Also fix the §4-insertion conflict.** `:298-301` inserts the shaper
*between* the in-amp and `POT-GAIN`, but `:34-35` still draws `POT-GAIN` fed
from the in-amp, and `:265` says a **second** half restores ×2 — a stage that
is described but drawn nowhere. With §4 fitted the correct chain is
`M_INA_OUT → M_RESP_X → M_RESP_OUT → [×2 restore] → M_RESP_RESTORE →
POT-GAIN`. **Draw the restore stage or delete §4's claim to a second half
before transcription**, because the difference is one net and one op-amp.

### 5.7 `hardware/controller/carrier.md`

| Line | From | To |
|---|---|---|
| 50-51 | `1 BREATH  2 AGND  3 +12V  6 PWR_GND  4 SCLK  5 MOSI  7 CS  8 DIG_GND` | `1 UMB_BREATH_P  2 UMB_BREATH_N  3 UMB_P12V  6 UMB_PWR_GND  4 UMB_SCLK  5 UMB_MOSI  7 UMB_CS  8 UMB_DIG_GND` |
| 59, 60 | `+12V`, `5V` | `I_P12V`, `I_5V_DEV` |
| 85 | `J-UMB pin 3  +12V` | `J-UMB pin 3  UMB_P12V` |
| 99 | `dev board 5V` | `I_5V_DEV` (and label `I_5V_A` before `D-USBOR`) |
| 104 | `J-DISP 5V` | `I_5V_DISP` (and `I_5V_B` before `D-USBOR`) |
| 106 | `PWR_GND ┴ … PWR_GND pour` | `UMB_PWR_GND ┴ … I_PWR_GND pour` |
| 164 | `+12V ──[REF5050]── 5.000 V` | `I_P12V ──[REF5050]── I_VREF5` |
| **168, 172 (×2 each)** | `AGND-local` | **`I_ARET`** |
| 168 | `SKT-BREATH pin VS` | `I_VS` |
| 179 | `MPXV4006DP Vout` | `I_SENSOR_OUT` |
| 181-182 | `J-UMB pin 1 / BREATH` | `UMB_BREATH_P` |
| 185-188 | divider tap; `AGND -local` | `I_ADC_DIV`; **`I_ARET`** |
| **199** | `J-UMB pin 2 AGND ──[…]──┴── analog star point` | **`UMB_BREATH_N ──[R-SER-BREATH-INST · R1b]──┴── I_ARET`** |
| 201 | `└──[single tie]── PWR_GND` | `└──[single tie]── I_PWR_GND` |
| 248 (prose) | "the analog star" | "`I_ARET`" |
| 298-308 (prose) | "The analog star point", `AGND`, `PWR_GND` | `I_ARET`, `UMB_BREATH_N`, `I_PWR_GND` |
| **439** | `IO38 SPI3 SCK` → `2 SCK` | **`I_CHAIN_SCK_RAW` → `I_CHAIN_SCK`** |
| 441 | `IO7 latch` → `4 SH/LD` | `I_CHAIN_SHLD_RAW` → `I_CHAIN_SHLD` |
| 443 | `IO33 SER out` → `6 SER` | `I_CHAIN_SER_RAW` → `I_CHAIN_SER` |
| **445** | `IO40 MISO ◄── 8 QH` | **`IO40 ◄── I_CHAIN_QH_RT`** |
| 438-446 | `GND` ×5 | `I_CHAIN_GND` ×5 |
| 447 | `3V3` | `I_3V3` |
| 451 | `[U-TVS-CHAIN 4-ch array to DIG_GND]` | **unresolved — see §7.2.** Do not transcribe as `UMB_DIG_GND` |
| **574** | `IO35 SCK ──[R-SPI-SER]──── J-UMB pin 4` | **`IO35 → I_SPI2_SCK_RAW ──[R-SPI-SER]──── UMB_SCLK`** |
| 575 | `IO36 MOSI` → pin 5 | `I_SPI2_MOSI_RAW ──[R-SPI-SER]──── UMB_MOSI` |
| 576 | `IO34 CS` → pin 7 | `I_SPI2_CS_RAW ──[R-SPI-SER]──── UMB_CS` |
| 577 | `J-UMB pin 8 ──┘ DIG_GND` | **redraw — §3.4.** Terminate it explicitly |
| **580** | `IO37 MISO ── MCP3202 DOUT only` | **`IO37 ── I_ADC_DOUT ── MCP3202 DOUT`** |
| **581** | `IO39 CS ── MCP3202 CS` | **`IO39 ── I_ADC_CS ── MCP3202 CS`** |
| 666, 672 | `IO1`/`IO2 ──┬──[R-LED-PD]── GND` | `I_LED_DATA_L`/`_R … ── I_PWR_GND` |
| 668, 674 | `J-LED-L DI` / `J-LED-R DI` | `I_LED_L_DI` / `I_LED_R_DI` |
| 669, 675 | `BI ──► GND` | `I_LED_BI ──► I_PWR_GND` |
| 763, 767 | `GND` (J-DISP ×2) | `I_PWR_GND` |
| 775, 776 | `GND` (HDR-SERVICE) | `I_PWR_GND` |
| 846 | `` on `SCLK`, `MOSI`, `CS` `` | `` on `UMB_SCLK`, `UMB_MOSI`, `UMB_CS` `` |
| 875 | `` `SCK`, `SH/LD`, `SER`, `QH` `` | `I_CHAIN_*` |

**Add to §2's drawing:** the MCP3202's `CLK` and `DIN` connections (§3.3).

### 5.8 `hardware/controller/cluster-boards.md`

| Line | From | To |
|---|---|---|
| 94 | `SH/LD` → pin 1; `3V3` → pin 16 | `I_CHAIN_SHLD`; `I_3V3` |
| 95 | `SCK` → pin 2 `CLK`; `CLK INH 15 ──── GND` | `I_CHAIN_SCK`; `K_CLK_INH ── K_GND` |
| 96-99 | `E`, `F`, `G`, `H`, `key A..D` | `K_KEY_E` … `K_KEY_H`, `K_KEY_A` … `K_KEY_D` |
| 100 | `SER 10 ◄── serial in` | `◄── K_SER` (`I_CHAIN_SER` or the next board's `QH` via `LK-SER`) |
| 101 | `GND ─│ 8 GND    QH 9 ──► serial out` | `K_GND`; `► K_QH` |
| 131 | `3V3 (from the loom, pin 10 of J-CHAIN)` | `I_3V3` |
| 133 | `► 74HC165 parallel input` | `► K_KEY_<n>` |
| 137, 139 | `GND` ×2 | `K_GND` ×2 |
| 137 | `SW  KS-33` | `K_SW_<n> ── SW<n> KS-33` |
| 243-244 | `1 GND  2 SCK  3 GND  4 SH/LD  5 GND  6 SER / 7 GND  8 QH  9 GND  10 3V3` | `I_CHAIN_GND / I_CHAIN_SCK / I_CHAIN_SHLD / I_CHAIN_SER / I_CHAIN_QH_<this board> / I_3V3` |
| 254-258 | `SCK`, `SH/LD`, `3V3`, `GND ×5`, `SER` IN→OUT | prefix all; mark them explicitly **bus** |
| **264-267** | `8 QH` on IN vs `8 QH` on OUT | **two different nets.** IN pin 8 = `I_CHAIN_QH_<this>`; OUT pin 8 = `I_CHAIN_QH_<next>`. The page says so at `:280-284`; the drawing does not |
| 300 | `3V3` (`R-SER-TERM` top) | `I_3V3` |
| 499 | "Straight to GND or 3V3" | "Straight to `K_GND` or `I_3V3`" |

### 5.9 `docs/decisions/0004-cv-interface-module.md`

| Line | From | To |
|---|---|---|
| **96-99** | the "Revised conductor budget" block, which pairs `SCLK / DIG_GND` and `MOSI / CS` | **Strike through and point at `:826-831`.** It is superseded by the same ADR and contradicts `hardware/module/digital-and-supervision.md:86-94` (§3.6) |
| 610 | "Module analog return" | **"`M_ARET` (module analog return)"** — this is the row that gives the net its name |
| 611 | "`AGND`, from the etherCON" | "`UMB_BREATH_N` (was `AGND`), from the etherCON" |
| 628-632 | "The analog return", "`AGND` is not in this list" | `M_ARET`, `UMB_BREATH_N` |
| 828 | `BREATH / AGND` | `UMB_BREATH_P / UMB_BREATH_N` |
| 829-831 | `+12V / PWR_GND`, `SCLK / MOSI`, `CS / DIG_GND` | `UMB_*` |
| 391 | "the cable-side `CS` pulls to **3V3, not +5 V**" | **unresolved — §3.5.** There is no 3V3 on the module |

### 5.10 `hardware/bom.csv` — notes only, no column changes

Rows 28, 49, 55, 60, 65, 104, 125 carry `AGND`/`BREATH` in the
umbilical-conductor sense; rows 49 carries `SCLK/DIN/SYNC`. Update the note
text to the canonical names in the same commit, per CLAUDE.md rule 2. **No
`ref`, `qty` or `status` field changes.** The 11-column count and the
duplicate-refdes check are untouched.

### 5.11 `docs/reference/pcb-pipeline.md`

`:58-59` states the `AGND`/`BREATH` problem and `:225-226` re-states the four
returns. Both should cite this file by name once the renames land, so the
statement of the problem and its resolution are one hop apart.

---

## 6. Naming convention for the transcription

Six rules. They are mechanical on purpose, in the spirit of CLAUDE.md.

### 6.1 Every net has a board-scope prefix, and there are exactly four

| Prefix | Scope | Constructed in |
|---|---|---|
| `UMB_` | The eight umbilical conductors. **The only nets that exist on two boards.** | `umbilical.py`, once |
| `M_` | Module-local (`PCB-MODULE`) | the six module modules |
| `I_` | Instrument-local (`PCB-CARRIER`) | the carrier modules |
| `K_` | Cluster-board-local (`PCB-CLUSTER`), four instances of one subcircuit | `cluster.py` |

**A net with no prefix is a defect.** This is checkable: assert that every net
name matches `^(UMB|M|I|K)_[A-Z0-9_]+$`. That single assertion would have
caught nine of the eleven collisions in §1 before any of them reached a board.

`docs/reference/pcb-pipeline.md:66-69` already requires `Net.fetch` and
"assert no net name ends in a digit". Add: **assert no net name lacks a
prefix**, and **assert the set of `UMB_*` nets has exactly eight members**.

### 6.2 A net that crosses a connector keeps one name, and the connector does not rename it

`UMB_SCLK` is one net whether it is at IO35's series resistor, in the cable,
or at the 74AHCT125's input pin. The connector is a part on the net, not a
boundary between two nets.

**But a net that is *transformed* by a part changes name**, and a connector is
not a transformation while a buffer, a resistor, a diode or a regulator is:

- `I_SPI2_SCK_RAW` **→** `R-SPI-SER` **→** `UMB_SCLK` **→** `74AHCT125`
  **→** `M_DAC_SCLK`. Three nets, and every one of them was called `SCLK` or
  `SCK` somewhere.
- `I_5V_A` **→** `D-USBOR` **→** `I_5V_DEV`. Two nets, both called `5V`.
- `M_BUS_P12V` **→** `D1` **→** `M_P12V_A`, and `M_BUS_P12V` **→** `D2` **→**
  `M_P12V_SW` **→** `FET` **→** `UMB_P12V`. Four nets, all called `+12V`.

**Rule: if a two-terminal part sits between two nodes, they are two nets and
they get two names.** The `_RAW` suffix is the house style for "the driver
side of a series element".

### 6.3 The four returns, and how to tell them apart

| Net | What it carries | Never |
|---|---|---|
| `M_PWR_GND` / `UMB_PWR_GND` | ~360 mA of instrument current | shares copper with anything `[docs/decisions/0004-cv-interface-module.md:624-626]` |
| `M_DIG_GND` / `UMB_DIG_GND` | SPI switching current | (destination disputed — §7.1) |
| **`M_ARET`** | Module analog supply return: op-amps, DAC `AVDD`, `M_INA_REF`'s tie, every jack shunt | touches `M_PWR_GND` except at the star |
| `UMB_BREATH_N` | **Nothing.** An in-amp input | is used as a return `[docs/decisions/0004-cv-interface-module.md:630-632]` |

Plus, on the instrument: `I_PWR_GND`, `I_ARET`, and `I_CHAIN_GND`/`K_GND`
(§7.2).

**Why `M_ARET` and not `M_AGND`.** The whole defect is that four letters —
`AGND` — attach to both a return and a non-return. Keeping those letters for
either meaning leaves the next reader one typo away from the same short. `ARET`
is unambiguous, greppable, and appears nowhere in the corpus today, so
`grep -rn AGND` after the rename finds **only** the sites that still need
fixing. That property is worth more than familiarity.

**Why `UMB_BREATH_P` / `UMB_BREATH_N` and not `UMB_AGND`.** Naming the pair
after what it is — a differential pair into an in-amp — makes the "not a
ground" fact structural rather than a note someone has to have read.
`docs/decisions/0004-cv-interface-module.md:611` has to *assert* that `AGND`
carries nothing; nobody has to assert that `UMB_BREATH_N` carries nothing,
because its name does not promise a ground.

*Accepted cost:* `AGND` appears in ADR 0004, ADR 0003, the BOM, the ROADMAP and
`pcb-pipeline.md`. That is 23 sites (§1.1) and they are enumerated, so the edit
is mechanical. If the author prefers to keep `AGND` in ADR prose as a
historical term, the netlist name must still be `UMB_BREATH_N`, and the ADR
must say "`UMB_BREATH_N`, historically `AGND`" at first use.

### 6.4 Signal nets are named for their **source stage**, not their destination

`M_PITCH_OUT` is the op-amp's output; `M_PITCH_JACK` is what reaches the
connector. The pitch stage's DC feedback is tapped at the second, which is the
whole argument of `hardware/module/pitch-stage.md:159-233` — and a netlist that
calls both "the output" loses that argument silently. Same for
`M_BR_OUT` / `M_BREATH_JACK` and `M_MODn_OUT` / `M_MODn_JACK`.

### 6.5 Repeated stages are suffixed, never re-used

Four mod channels, four cluster boards, four `QH` hops. `M_MOD1_JACK` …
`M_MOD4_JACK`; `I_CHAIN_QH_RT/RH/LT/LH`; `K_*` scoped per subcircuit instance.

**`I_CHAIN_QH_*` is the trap.** `hardware/controller/cluster-boards.md:280-284`
is explicit that "Pin 8 therefore carries a different net on each side of the
board", but the drawing at `:264-267` labels both `8 QH`. Four nets, one label,
on four boards — and the failure mode is that all four registers' outputs are
tied together, which reads as a plausible 32-bit word right up until you press
a key.

### 6.6 Rails carry their voltage and their domain, in that order

`M_P12V_A` (module, +12 V, analog), `M_N12V_A`, `M_BUS_P5V`, `I_5V_DEV`,
`I_3V3`, `M_AVDD`. No bare `+12V`, no bare `5V`, no `±12 V` as a net — a clamp
to both rails is two connections to two nets, and writing `±12 V` in a drawing
is what let three `+12V` nets share a name (§1.3).

---

## 7. Flagged, deliberately not resolved

### 7.1 `dig-gnd-topology` — three destinations, three documents

`config/figures.yaml:235-246` records it as `disputed`, and the candidates are:

1. "Its own path to the star" `[docs/decisions/0004-cv-interface-module.md:627]`
2. "NOT its own path — the pour directly under its trace"
   `[hardware/module/power-entry.md:495-498]`
3. "The analog star, single tie"
   `[hardware/module/digital-and-supervision.md:53]`

`decided_by`: the 2-layer vs 4-layer decision
`[config/figures.yaml:244]`, which `docs/reference/pcb-pipeline.md:245-250`
confirms is upstream.

**Flagged, not resolved**, per this slice's brief. One thing this wave can add:
candidate 3 is **not** actually a `DIG_GND` claim. Read in context,
`digital-and-supervision.md:53`'s "analog star, single tie" is the line hanging
off the **`DIG_GND` conductor's `│`** in that drawing — so it is either a claim
that `M_DIG_GND` ties to `M_ARET`, or a mislabelled tie of `M_ARET` to the
`M_PWR_GND` star. The drawing cannot distinguish them.
**Whoever settles `dig-gnd-topology` must settle that ambiguity first**,
because candidate 3 may not exist.

`config/figures.yaml:246` is right that `power-entry.md` claims ADR 0004 was
corrected and it was not — `:627` still says the opposite. Verified here
independently: `docs/decisions/0004-cv-interface-module.md:627` reads
"**`DIG_GND` likewise** — its own path to the star."

### 7.2 The instrument has no declared return topology at all

Downstream of 7.1 and not separately tracked. On the carrier, `U-TVS-CHAIN`
returns to `DIG_GND` `[hardware/controller/carrier.md:451]` while `U-TVS-SPI`
returns to `PWR_GND` `[hardware/controller/carrier.md:579]`, for two looms
leaving the same board. `J-CHAIN`'s five grounds, `J-DISP`'s two, the
`HDR-SERVICE` ground, the `J-LED` grounds, `R-LED-PD`'s return, the 74HC165s'
pin 8 and every `C-KEY` return are all written `GND` with no domain. `I_ARET`
joins `I_PWR_GND` at one tie `[hardware/controller/carrier.md:306-307]`, which
is the only return rule the instrument has.

**Consequence for transcription:** `I_CHAIN_GND` and `K_GND` are placeholders.
Pick `I_PWR_GND` provisionally so the netlist is complete, **and mark it TBD
with what decides it** (the same layer decision), per CLAUDE.md's rule on
unresolved things. Do not silently merge them into `I_ARET`.

### 7.3 `R-SPI-PULL`'s cable-side rail (§3.5)

`3V3` does not exist on the module. Rail decision, entangled with
`hardware/module/digital-and-supervision.md:108-116`'s open "drop the bus +5 V
rail" item. **Flagged.**

### 7.4 Is `M_AVDD` one net or two?

`hardware/module/breath-output-stage.md:43-44` writes "**buffered** +5.21 V
(LM317 rail)" as `POT-OFFSET`'s top. `hardware/module/power-entry.md:18`,
`breath-receive-stage.md:55,163` and `digital-and-supervision.md:40` all treat
the LM317 output as a rail driven straight. If "buffered" is literal there is
an op-amp half that is not in `breath-output-stage.md:130-132`'s count of ten
of twelve; if it is loose wording, `POT-OFFSET`'s 10 kΩ loads `M_AVDD` directly
alongside the DAC's `AVDD` pin.

**One net or two, and one op-amp half either way.** Not resolvable from the
corpus. Transcribe as one net (`M_AVDD`) and flag.

### 7.5 `C-REF-OUT`'s node

`config/figures.yaml` tracks it as `cref-out-node`, and
`hardware/controller/carrier.md:290-294` states it plainly: this page draws the
10 µF on the REF5050 output (the buffer's **input**) while `bom.csv` and
`breath-receive-stage.md` say the buffer **drives** it. That is
`I_VREF5` vs `I_VS` — **two different nets for one capacitor**, and it changes
the compensation `[hardware/controller/carrier.md:294]`. **Flagged; already
tracked.**

### 7.6 The MCP3202's `CLK`/`DIN` tap point (§3.3)

Recommended `_RAW` side in §4K, flagged as a decision rather than a finding.

---

## 8. Refdes collisions — adjacent to this slice, and netlist-blocking

`docs/reference/pcb-pipeline.md:70-73` requires "**Explicit `ref=` and `tag=`
on every part**". Five parts are called `R1` and four are called `R2`:

| Refdes | Page | Part |
|---|---|---|
| `R1`, `R2` | `hardware/module/pitch-stage.md:18,35` | LT5400 sections, 10 k 1:1 |
| `R1`, `R2` | `hardware/module/mod-channels.md:26,37` | 10 k / 30 k 1 % discretes |
| `R1`, `R1b`, `R2`, `R3`, `R4`, `R5` | `hardware/module/breath-receive-stage.md:22,28,35,37,45` | `R-SER-BREATH-INST` ×2, `R-SER-BREATH` ×2, `R-BIAS-INAMP` ×2 |
| `R1`, `R2` | `hardware/module/breath-output-stage.md:189,266` | response shaper, 20 k / 10 k |

`R1` alone is four different parts on four pages, across three boards, and
`hardware/bom.csv` carries **none** of these names — it carries
`R-PRECISION`, `R-MODGAIN`, `R-SER-BREATH-INST`, `R-SER-BREATH`,
`R-BIAS-INAMP`, `R-GAIN-INAMP`. Likewise `C-TIMER`/`C-GATE` in
`hardware/module/power-entry.md:36-37,339-340,400-404` against
`C-TIMER-LOADSW`/`C-GATE-LOADSW` in the BOM, and `R-IN`/`R-FB`/`R-OFF` in
`hardware/module/breath-output-stage.md:46-48,122-126` against
`R-BREATH-SUM`/`R-BREATH-OFF`.

This is the same defect as §1, one layer down: `docs/reference/pcb-pipeline.md:72`
warns that "KiCad matches by reference, so a re-import silently misassigns
downstream footprints." **Out of this slice, but it must be reconciled in the
same pass** — the schematic pages' `R1`/`R2` labels should be replaced by the
BOM refdes with a positional suffix (`R-PRECISION-1`, `R-MODGAIN-1A`, …), or
the BOM has to grow the short names. It cannot be left as two naming schemes
"neither side aware of the other", which is exactly what
`hardware/controller/carrier.md:584-589` found for `R-SPI-SER` and fixed.

---

## 9. What I checked by hand, and where I could be wrong

- **Every alias in §1 and §2 was read in place**, not grepped for and assumed.
  The five `AGND(module)` sites and the four bare-`AGND`-meaning-the-return
  sites were counted from the rendered drawings, including the two on
  `hardware/module/breath-receive-stage.md:47`.
- **§3.1 is an inference, not a reading.** The ASCII at
  `hardware/module/power-entry.md:15-38` genuinely is ambiguous; I read it as a
  drawing error because the electrical alternative is a dead short and because
  the LT1641 block hangs off that node. **A reviewer with the author's intent
  should confirm before the redraw.** I have not edited the page.
- **§3.3 and §4K's `_RAW` tap recommendation is a design choice I am making on
  no authority.** It is marked as such. The finding (that `CLK` and `DIN` are
  drawn nowhere) is solid; the answer is a proposal.
- **I did not verify that `I_CHAIN_GND` and `K_GND` are the same net.** Nothing
  in the corpus says so. I have kept them as two names for what is probably one
  net rather than merge them, because merging is the failure this slice exists
  to prevent.
- **Line numbers are as of 2026-09-21** and will move the moment §5 is applied.
  Anyone auditing this should apply §5 in one commit and re-cite, not
  cross-check against a half-renamed tree.
- I did **not** read `docs/review/**`. If a previous wave already named the
  module analog return, this file has invented a second name for it, and that
  is the one thing here that would make the problem worse rather than better.
  **Check that before adopting §6.3.**
