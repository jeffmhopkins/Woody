# Woody

A custom electronic woodwind instrument: a wooden body with mechanical key
switches, breath and motion sensing, driving control voltage into a Eurorack
system.

This is the second iteration of the
[Open Woodwind Project](https://github.com/jeffmhopkins/Open-Woodwind-Project)
(2021), rebuilt from scratch with modern components. The previous version was a
Teensy 3.2 with capacitive touch keys and an onboard synthesizer. This one keeps
almost none of that: mechanical switches instead of capacitive pads, an ESP32-S3
instead of a Teensy, CV output instead of an onboard synth engine.

**Status: Phase 0.** Design decisions are being recorded; no hardware has been
built. Switches and keycaps are purchased. See [ROADMAP.md](ROADMAP.md).

## What it is

The project splits into two physical deliverables that meet over a single cable:

| | **Controller** | **Interface module** |
|---|---|---|
| Form | Laminated wood/aluminium/acrylic body | 10HP Eurorack module |
| Contains | Keys, breath sensor, IMU, display, MCU | DAC, analog scaling, jacks, knobs |
| Domain | Digital | Analog, ±12V |
| Primary risk | Mechanical and ergonomic | Analog precision |

The controller carries no battery and no output jacks, and all CV **scaling,
conversion and output** happens in the module. It is **not** purely digital —
it holds the pressure sensor, a precision reference, two op-amp stages and the
analog drive onto the umbilical, which is where most of the project's analog
risk lives (ADR 0003). An earlier version of this sentence said otherwise, and
ADR 0004 records that the claim let a review finding through unchallenged.

It takes power from the rack over the umbilical and sends channel data
down the same cable as SPI. The module's analog sits inches from
the jacks it drives.

These two can be developed and tested independently, and the module can be
brought up standalone on a bench long before the instrument exists.

### Output

Six CV channels from the module:

- **Pitch** — dedicated, 1V/oct, −2V to +7V, per-unit calibrated
- **Breath** — dedicated, 0–10V, with panel knobs for gain and offset
- **Mod 1–4** — assignable; source, scale, offset, curve and slew configured
  on the instrument's own display

## Design scope

**This is a tethered rack instrument.** It is powered by a Eurorack system,
patched into one, and played in front of one. That is the design case, and
decisions get made for it.

It is explicitly **not**: battery powered, wireless, standalone, a USB MIDI
controller product, or a touring instrument. Requirements that only make sense
away from the rack do not belong here, and past versions of these documents
drifted into arguing for some of them.

USB exists for flashing, and USB MIDI on top of it is a **bring-up tool** — it
is how keys, fingering and breath response get validated in a DAW before any
analog hardware is built (milestone E5). It is not a feature and it does not
get to constrain anything.

There is no onboard synthesizer. There is no battery.

**The target rack has a generous supply and a regulated +5 V rail.** Both are
stated properties of the system this is built for, not assumptions to be
defended. Rack current budget is therefore **not** a design constraint here, and
arguments of the form "a small Eurorack PSU might not cope" do not apply.

That relief is narrower than it sounds, and worth stating precisely so nobody
re-derives the wrong caution later. What still binds:

- **Heat.** The body is oak and acrylic — insulators — and sealed. Every watt
  leaves through the aluminium plate, part of which is under the player's hands.
- **The instrument's own 5 V regulator**, which is a 1 A part at the end of a
  2 m cable, not the rack supply.
- **Fault current**, which a larger supply makes *worse*, not better.

## Licence

Three share-alike licences, one per kind of work — **GPL-3.0-only** for
firmware, **CERN-OHL-S-2.0** for hardware and mechanical design,
**CC-BY-SA-4.0** for documentation. Derivatives stay open on the same terms.

See [`LICENSE`](LICENSE) for the mapping and the reasoning, and
[ADR 0011](docs/decisions/0011-licensing.md) for why it is three rather than
one.

## Repository layout

```
docs/decisions/   Architecture decision records — the important stuff
docs/log/         Dated build log
docs/reference/   Latency budgets, fingering notes, specs
docs/research/    Component comparisons and datasheet notes
docs/review/      Cold review waves. A dated record, never corrected
datasheets/       The actual vendor PDFs, one MANIFEST.csv row each
hardware/         Schematics, split by CIRCUIT under each board:
                    <board>/<circuit>/<circuit>.md  the drawing + derivations
                                      bom.csv       fragment; generates the BOM
                                      circuit.yaml  declared dependencies
                                      notes.md      what it used to be
                  interfaces/  the three circuits that cross a board boundary
                  bom.csv      GENERATED from the fragments - do not edit
firmware/         ESP32-S3 firmware (PlatformIO)
mechanical/       CAD source, 2D cut exports, drawings
config/           Key layout and routing, as data
tools/            Host-side utilities
```

*(`docs/review/` and `datasheets/` were missing from this tree until
2026-09-21. `datasheets/` is the largest directory in the repository;
`docs/review/` holds nine waves. Both were invisible in the one file a new
reader opens first. The counts that used to sit in this sentence — "77
banked documents", "seven waves" — were true when written and wrong within
the week, which is the whole reason this repository cites rather than
restates.)*

## Where to start reading

1. [ROADMAP.md](ROADMAP.md) — the three tracks and what "done" means for each
2. [hardware/README.md](hardware/README.md) — **how the schematics are
   organised**: one circuit per directory, what the four files in each are,
   and the two rules that will bite you. Start here before opening any
   circuit page.
3. [docs/decisions/](docs/decisions/) — every choice made so far, and why
4. [docs/reference/latency-budget.md](docs/reference/latency-budget.md) — the
   constraint that shapes most of the electrical design
5. [docs/reference/repo-maintenance.md](docs/reference/repo-maintenance.md) —
   which files are generated, which are history, what each tool owns

*(Entry 2 was missing until 2026-09-21. `hardware/README.md` — the page that
explains the whole `<board>/<circuit>/` scheme the restructure exists to
create — had **zero inbound links from anywhere in the corpus**, so the tree
was navigable by `grep` and by already knowing where things were, which is
the condition the restructure was meant to end.)*

*(This file carried a second "Licensing" section here saying the licence was
"not yet decided", contradicting the "Licence" section above it, which states
the three that were chosen. ADR 0011 has read `Accepted` since it was written
and `LICENSE` has held the mapping the whole time. Deleted 2026-09-21 — the
licence is stated once, above, and nowhere else.)*
