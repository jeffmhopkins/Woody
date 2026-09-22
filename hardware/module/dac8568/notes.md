# DAC8568C — decision history

**Past tense only.** The live `LDAC` and `CLR` nets are drawn in
[`dac8568.md`](dac8568.md); every live value is there or in `hardware/bom.csv`.
If a number here is still true, it is in the wrong file.

Nothing is deleted from this shelf: a deleted superseded value stops warning
the next person, and the refutation wording is what lets
`tools/check-staleness.py` tell a quoted old value from a live one.

---

*Moved verbatim from `../digital-and-supervision/digital-and-supervision.md`,
2026-09-21, when that page was split into three circuit directories. Both
bullets below are the `LDAC` one; the second of the "two" — the `SCLK`/`MOSI`
series-resistor bullet — went to
[`../digital-and-supervision/notes.md`](../digital-and-supervision/notes.md).
The redraw record that corrected the `CLR` net is there too.*

### Two bullets closed here, 2026-09-21

- **`LDAC` — corrected 2026-09-21, and it was drawn wrong.** SBAS430E p.38,
  verbatim: *"For such synchronous updates, the LDAC pin is not required and
  **it must be connected to GND permanently**."* The same page: the internal
  LDAC register defaults to `0x00`, and *"if the LDAC register bit is set to
  '0', the DAC channel is controlled by the LDAC pin."* So with the register at
  its default and the pin pulled **high**, the buffer-to-DAC-register transfer
  is **gated** — and with no `MISO`, firmware can never discover it. A module
  that accepts every word and moves no output.

  This is the pull-down-on-`CLR` defect mirrored: same page, same redraw, same
  class, opposite polarity. `R-LDAC` is now a **0 Ω strap to GND**.

  *(The old escape hatch — "it becomes a GPIO, and the pin is already broken
  out" — was false twice: there is no pad, and all eight umbilical conductors
  are allocated, so there is nothing at the module end to drive it.)*

- ~~`LDAC` — closed. `R-LDAC`, 10 kΩ to `AVDD`, is drawn above and carries a
  `bom.csv` row. Tied, not driven: a hardware `LDAC` was considered and
  declined, so the six populated channels update as each word lands rather than
  together. The cost is real and accepted — every exit from `CLR` throws
  intermediate values at the mod jacks for 100–200 µs and no write order avoids
  it. If E10 finds that audible it becomes a GPIO, and the pin is already
  broken out.
