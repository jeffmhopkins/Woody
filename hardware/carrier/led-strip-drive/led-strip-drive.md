# LED strip drive — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B). **One strip since
2026-09-26** ([ADR 0016](../../../docs/decisions/0016-one-strip-on-the-centre-board.md)):
it lies on the main board and lights both acrylic sides, so there is one
data line, one connector and one set of parts. The two-strip version is in
[`notes.md`](notes.md).

The 74AHCT125 that lifts the ESP32-S3's 3.3 V data to the WS2815 strip, the
pull-down that holds it quiet through reset, and the series damping to the
strip connector. **The 12 V strip power and `C-STRIP-BULK` are not here** —
they belong to
[`power-entry-instrument`](../power-entry-instrument/power-entry-instrument.md).

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| IO1 | in | `J-MCU` | — | High-impedance through the bootloader window; `R-LED-PD` is what holds it down in it. IO2 is spare (ADR 0016) |
| 5 V | in | `carrier/power-entry-instrument` | — | The buck. The 74AHCT125's rail; TTL thresholds on this rail are why 3.3 V in reads high |
| `J-LED` `DI` | out | the WS2815 strip | — | Through `R-LED-SER` |
| `J-LED` `BI` | ref | the head of the strip | — | A **ground** connection, not a driven one — see below |
| `+12V`, GND at `J-LED` | — | `carrier/power-entry-instrument` | — | Strip power passes through this connector but is that circuit's net |
| `OE_INST` ×4 | ref | — | — | `U-LVLSHIFT`'s four enables, tied LOW on this board, which is why the pull-downs are needed rather than optional. **Not `OE_MOD`**, the module buffer's |

## §5 LED data

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*


```
  IO1 ──┬──[R-LED-PD 10k]── GND   ** PROPOSED **
        │
        └──►│ 74AHCT125 gate A ├──[R-LED-SER 330R]── J-LED  DI   ** R PROPOSED **
                                                     J-LED  BI ──► GND
                                          (vendor's recommended circuit)

  gates B, C, D SPARE, inputs tied to GND

  74AHCT125 rail = 5 V (TTL thresholds, so 3.3 V in reads high)  [repo] 0014
  OE ×4 tied LOW
  [C-DECOUPLE-CARRIER 100 nF] at the package
```

**`R-LED-PD` is new and it is the fix for a real hole.** ADR 0014's defence
against latched strips is "blank the strip and the matrix as the first act at
boot" `[repo] 0014` — a firmware rule that cannot run in the window it matters.
On reset GPIO1 is high-impedance inputs for the bootloader window
(order 100–300 ms `[from memory]`), `OE` is tied low so the buffer is enabled,
and an AHCT input floating near its threshold does not sit still. The buffer
squares up whatever it sees into clean 5 V edges and sends it to every
addressable LED on the strip, on a 12 V rail. WS281x has no framing beyond a reset gap, so that is random
pixel data — the exact state the thermal clamp exists to prevent, at the moment
no firmware is running to clamp it. One 0805, and it cannot be added later.

The module page has the same idea for the same reason: `R-SPI-PULL`, six of them,
both sides of its 74AHCT125 `[repo] digital-and-supervision.md`. The instrument
end has none.

**Both open questions here are closed, 2026-09-21**, against the genuine
Worldsemi WS2815 datasheet V1.1 now at
`datasheets/led/WS2815.pdf` `[repo, verified]`:

- **Yes, the WS2815 accepts 5 V logic, and the 74AHCT125 is the right part.**
  The Electrical Characteristics table gives `V_IH ≥ 0.7 VDD` — and **the table
  declares its own conditions in the header: `VDD = 4.5…5.5 V`.** So `V_IH` is
  **3.15 V to 3.85 V**, nominally 3.5 V, and the 74AHCT125 at 5 V delivers
  ~4.4 V minimum into it.

  > **Where "12 V logic" came from.** The datasheet reuses the symbol `VDD` for
  > two different nets: pin 2 `VDD` is the +12 V LED supply, while the
  > Electrical Characteristics table's `VDD` is the 4.5–5.5 V logic rail it
  > names in its own header. Reading `0.7 × VDD` with the pin-2 meaning gives
  > **8.4 V**, which is how a 12 V part acquires an impossible threshold. The
  > conditions line governs. *(Absolute Maximum Ratings muddles it further —
  > "Logic input high voltage VI: VDD−0.5 … VCC+0.5 V" — which is why this
  > needed reading rather than recalling.)*

- **No, the first pixel's `BI` does not need driving — ground it.** The
  datasheet's own "Recommended application circuit" ties **L1's pin 6 (`BI`) to
  pin 5 (`GND`)**. From L2 onward each pixel's `BI` comes from the *previous*
  pixel's `DI` node, internal to the tape — so the backup line lags the main
  line by one pixel, which is exactly what lets a dead pixel be bypassed, and
  the head of the strip has nothing to lag.

  **So `BI` needs no gate**, and with one strip gates B, C and D are all
  spare. *(The figure
  is a raster image with no text layer and was read by rendering the page at
  700 dpi — confirm visually against the PDF before the connector is wired.)*

  The bypass latch is **sticky until power-off**: *"...make the BIN in state of
  receiving signal until restart after power-off."*

**`R-LED-SER` is proposed** on the same grounds as §4: the gate drives the
strip's data line and nothing damps it. The strip now lies on the same board,
so the run is short (ADR 0016) and the case for it is weaker than it was;
it stays because it costs one 0805 and protects the buffer's output. The useful range is 100–330 Ω at
the buffer; **the BOM carries 330 Ω, the top of it**, and the drawings show
that value — do not re-introduce a different number into the drawing.

*(The record of the two questions that closed here on 2026-09-21 is in
[`notes.md`](notes.md).)*

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-LVLSHIFT` | 74AHCT125 SOIC-14 | LED data, 5 V rail. **Gate count depends on `BI`** | `[repo]`; `BI` `[from memory]` |
| **`R-LED-PD`** | **10 kΩ** | **Proposed — holds the strip's data low through reset** | proposed |
| **`R-LED-SER`** | **330 Ω** (useful range 100–330) | **Proposed — damps the data line at its source** | proposed |
| **`J-LED`** | **4-way** | **Proposed — 12 V, GND, `DI`, `BI`.** `BI` is a **ground** connection at the head of the strip, not a driven one (§5, verified against the datasheet 2026-09-21) — so it is still a 4-way connector but only three nets, and `BI` can tie to the same GND pin's net at the strip end | proposed |
