# LED strip drive — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B). Every line below was
moved verbatim; nothing was reworded and no value was touched in the move.

The 74AHCT125 that lifts the ESP32-S3's 3.3 V data to the WS2815 strips, the
pull-downs that hold it quiet through reset, and the series damping to the two
strip connectors. **The 12 V strip power and `C-STRIP-BULK` are not here** —
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
| IO1, IO2 | in | `HDR-DEV` | — | High-impedance through the bootloader window; `R-LED-PD` is what holds them down in it |
| 5 V | in | `carrier/power-entry-instrument` | — | Buck A. The 74AHCT125's rail; TTL thresholds on this rail are why 3.3 V in reads high |
| `J-LED-L` `DI`, `J-LED-R` `DI` | out | the two WS2815 strips | — | Through `R-LED-SER` |
| `J-LED-L` `BI`, `J-LED-R` `BI` | ref | the head of each strip | — | A **ground** connection, not a driven one — see below |
| `+12V`, GND at `J-LED-L/-R` | — | `carrier/power-entry-instrument` | — | Strip power passes through this connector but is that circuit's net |
| `OE_INST` ×4 | ref | — | — | `U-LVLSHIFT`'s four enables, tied LOW on this board, which is why the pull-downs are needed rather than optional. **Not `OE_MOD`**, the module buffer's |

## §5 LED data

```
  IO1 ──┬──[R-LED-PD 10k]── GND   ** PROPOSED **
        │
        └──►│ 74AHCT125 gate A ├──[R-LED-SER 220R]── J-LED-L  DI   ** R PROPOSED **
                                                     J-LED-L  BI ──► GND
                                          (vendor's recommended circuit; gate B SPARE)

  IO2 ──┬──[R-LED-PD 10k]── GND   ** PROPOSED **
        │
        └──►│ gate C ├──[220R]── J-LED-R DI
                                          J-LED-R BI ──► GND   (gate D SPARE)

  74AHCT125 rail = 5 V (TTL thresholds, so 3.3 V in reads high)  [repo] 0014
  OE ×4 tied LOW
  [C-DECOUPLE-CARRIER 100 nF] at the package
```

**`R-LED-PD` is new and it is the fix for a real hole.** ADR 0014's defence
against latched strips is "blank both strips and the matrix as the first act at
boot" `[repo] 0014` — a firmware rule that cannot run in the window it matters.
On reset GPIO1 and GPIO2 are high-impedance inputs for the bootloader window
(order 100–300 ms `[from memory]`), `OE` is tied low so the buffer is enabled,
and an AHCT input floating near its threshold does not sit still. The buffer
squares up whatever it sees into clean 5 V edges and sends it to 25 addressable
LEDs on a 12 V rail. WS281x has no framing beyond a reset gap, so that is random
pixel data — the exact state the thermal clamp exists to prevent, at the moment
no firmware is running to clamp it. Two 0805s, and they cannot be added later.

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

  **So gates B and D are not needed**, the BOM's "two spare gates" is right
  after all, and the LED loom stays at 6 conductors rather than 8. *(The figure
  is a raster image with no text layer and was read by rendering the page at
  700 dpi — confirm visually against the PDF before the loom is crimped.)*

  The bypass latch is **sticky until power-off**: *"...make the BIN in state of
  receiving signal until restart after power-off."*

**`R-LED-SER` is proposed** on the same grounds as §4: each gate drives ~420 mm
of wire to a strip, and nothing damps it. 100–330 Ω at the buffer.

*(The record of the two questions that closed here on 2026-09-21 is in
[`notes.md`](notes.md).)*

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-LVLSHIFT` | 74AHCT125 SOIC-14 | LED data, 5 V rail. **Gate count depends on `BI`** | `[repo]`; `BI` `[from memory]` |
| **`R-LED-PD`** ×2 | **10 kΩ** | **Proposed — holds the strips' data low through reset** | proposed |
| **`R-LED-SER`** ×2–4 | **100–330 Ω** | **Proposed — damps ~420 mm to each strip** | proposed |
| **`J-LED-L/-R`** | **4-way each** | **Proposed — 12 V, GND, `DI`, `BI`.** `BI` is a **ground** connection at the head of the strip, not a driven one (§5, verified against the datasheet 2026-09-21) — so it is still a 4-way connector but only three nets, and `BI` can tie to the same GND pin's net at the strip end | proposed |
