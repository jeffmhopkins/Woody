---
name: pcb-routing
description: Route a Woody board (route: astar) in families - plan a layout.yaml `families:` block, run the router, inspect each family with a 2D plot, adjust, and leave a replay record. Use for any routing trial or re-route of a board under hardware/boards/.
---

# Routing a board in families

**The owner, 2026-10-05:** *"we should do families of traces... then do those and
then do the next ones then do the next ones instead of just letting the auto router
go Willy-nilly"* (`docs/reference/tooling.md`, *The routing policy*). The mechanism
is `layout.yaml` `families:` (`tooling.md` §4, *The router: families*); this page
is the method. Read CLAUDE.md first: the commit gate, `Gate-Red`, and no figure
restated here.

## The order

1. **Power and rails.** The nets of the power net classes, which route on the
   outer layer their class allows and cannot hop a signal via. `route_first:`
   already leads as a family; fold it into this one.
2. **Sensitive analog**, with its guard and its return: the pair (`pairs:`
   `guard:`) and the island are laid by `prepare` before any family; the
   family is the analog classes' remaining nets, kept over their island.
3. **Buses as bundles** (`bundle: true`): lines that run together between the
   same two ends - a chain, a connector fan-in - one corridor, one pitch.
4. **The rest**, last, with the largest `time_s`.

Give a constrained region its own family before the general ones (`region:`),
when a section is being re-routed on its own.

## House rules - cite them, never restate their values

- **Locked copper stays.** Hand routes are locked so `finish`, `rescue` and
  every family leave them (the main board's `README.md`, *The analog block*,
  #33). Never unlock to make a family fit; say what blocks it.
- **Layer-limited rails** come from `net_classes:` (`layers:`, `layer_cost:`);
  a family's `layers:` only narrows them.
- **Star ground:** one tie per island (ADR 0001; `islands:`; `pcb.py check`
  fails a second). No family routes a plane net; ground is the planes.
- **Power vias, #8-6:** a power class changes layers only through its class's
  `via:`; a power pad meets its plane by `fanout_count:`. Never give a power
  family a low `via_cost` to get it through.

## Plan, then execute

1. **Plan.** Plot what is there: `python3 tools/pcb_plot.py <board> -o
   <scratch>/before.png --nets <globs>`. Write the `families:` block into
   `layout.yaml`, each family with a one-line comment saying why it is there and
   in that place.
2. **Run** on a scratch copy unless the task is the board itself: `nice -n 19`,
   one heavy job at a time, no worker pools; `pcb.py route <board>` goes family
   by family and resumes after a kill. Read each `route: family` line: routed,
   negotiated, by complete, failed, vias, length, rounds, cells still shared.
3. **Inspect** every family: `pcb_plot.py <board> --family <name> -o ...`,
   `--window` on the region in question. Look for detours, via chains, a bundle
   that split, a family walling in the next.
4. **Adjust** one thing at a time - the order, a `region:`, a `via_cost:`, a
   family split in two, `rip_up: true` for a family that must move earlier
   copper - and run again. Stop when `pcb.py check` passes, or say what is left.

## The replay record

A run is replayable from three things: the `layout.yaml` `families:` block, the
`tools/` revision, and the command. In the commit (and the issue comment, by
finding id) give all three, each family's `route: family` line, before and
after vias and length for the nets in question, and the plots. Same inputs give
the same copper: the router is deterministic in geometry.
