# 0029 — A topological router: plan each line's way first, then lay elastic copper

**Status:** Accepted, 2026-10-11. Decided by the owner, in the working chat,
from four options put to them (below). Tracked in #47, under #46. **Amended
2026-10-11** (the copper is laid by the grid router along the plan: *Amendment*
below).

## Context

`tools/pcb_route2.py` (#46) is a grid router. It lays one net at a time with
an A* search, and every net it lays is a wall to every net after it. Its
push-and-shove (`Router.reroute`) runs only after a net has failed, and moves
that net's neighbours at most two deep. Its liquid pass (rubber band, slide,
equalise) runs after routing and is guarded never to change which side of
anything a line passes. Nothing is fluid while the copper is being laid.

The main board's cold trial, 2026-10-11, measured what that costs. The
J-MCU fan-in has about twenty lines leaving a 1.27 mm header and two
neighbouring ICs on two signal layers. It was routed eight times, with hand
edits, three net orders, a family by place (`near:`), a placement band in
front of the header, and a placement rescue (`pcb_pack.reseat`). Each fix
closed the pin that was failing, and every run walled in a different pin of
the same crowd instead. Rip-up rescues took 7–21 min each and mostly failed.
The run records are in the session's scratchpad and the commits of #46
between 59d0c147 and 3f5c2d42.

The owner, 2026-10-11: *"We should be able to have things much more fluid
during the process and allow things to kind of push traces out of the way and
merge between traces."*

## Options

1. **Benchmark Freerouting** (open source, Specctra round trip from KiCad;
   push-and-shove while routing, then optimisation). It would show whether the
   board is cleanly routable at this placement, but it is an outside engine
   with its own rules, not something the families-and-review loop can steer.
2. **Negotiated congestion on the grid** (PathFinder). Every net of a family is
   routed at once, overlap is allowed at a cost, and contested cells grow dearer
   each round until nothing overlaps. Proven and a moderate change, but still
   cells: a line moves only when it is routed again.
3. **A topological router.** Chosen.
4. **Pause the engine and finish the board** with a partial fan-in.

## Decision

Build a topological router, `tools/pcb_topo.py`, as an engine the staged
family loop (`Router.stage`) can use. Each line is planned first as a
topology, meaning which side of each obstacle it passes, in what order among
its neighbours, and on which layer. Its geometry follows from that plan.

1. **The map.** Each copper layer is a constrained Delaunay triangulation
   (`triangle`, Shewchuk's) of the routing space. Its vertices are pad
   centres, the corners of keep-outs, locked copper and the board edge. Each
   triangle edge has a **capacity**: its length less the clearances of its
   two ends, in track pitches.
2. **A route is a path through triangles,** the edges it crosses and on each
   edge its place in that edge's **order** of lines. A new line squeezes
   between two lines already on an edge by taking a place in its order.
   Nothing is moved, because geometry is not laid yet. This is the
   "merge between traces" the owner asked for, and it is where shoving
   happens: one line's place on an edge pushes the lines beyond it over.
3. **Crossings are counted, not forbidden, until they are resolved.** Two lines
   on one layer whose orders swap between edges cross. The search prices a
   crossing, then layer assignment and rip-up resolve them, dearer each round
   (option 2's negotiation, on topology rather than cells). A via is a
   place in a triangle, with its own capacity.
4. **Geometry last, as rubber bands.** *(2026-10-11: for a family's copper, superseded
   by the Amendment below - the grid router lays it along the plan. The bands remain as
   an engine of their own.)* Each line is the shortest path in its
   sleeve of triangles (the funnel algorithm), held off each vertex by that
   vertex's clearance plus the widths of the lines ordered inside it. Then it
   is cut to 45° and written as tracks. A capacity that holds means the bands
   fit. `fits()`, KiCad's DRC and `pcb.py check` prove it.
5. **Same contract as the grid router.** It honours net classes, `layers:`,
   locked copper, keep-outs, planes and their fanout, islands and moats. It
   has the bench's DRC-clean standard and the stage's checkpoints, edits and
   review. The grid router stays for what it does well, power and fanout,
   until the bench shows the new one does it better.

Built in stages, each proven on a constructed board before the next starts:
single layer with two-pin nets and orders; two layers with vias and
crossings; multi-pin nets; the stage's engine option; then the main board's
J-MCU fan-in as its benchmark.

## Consequences

- A new dependency, `triangle` (pinned in `tools/requirements.txt`).
- The main board's routing waits on the new engine. The cold trial's
  placement work (the header band, `reseat`) stands either way, because it is
  about the placement and not the engine.
- If the topological router fails its benchmark, option 1 is the next step.
  Freerouting shows whether the placement is the problem.

## Amendment, 2026-10-11 — the plan guides; the grid router lays the copper

**Decided by the owner, 2026-10-11**, from three options put to them in the
working chat: exact rubber-band geometry; a hybrid; or the hybrid now and the
bands later. They chose the hybrid.

**Why.** The planner and the negotiation worked. On the crowd board (the
J-MCU crowd, small; four layers with planes) the planner alone routed all 18
nets once each layer was laid along the negotiated plan. The drawing did not
hold up. Capacity is checked on the triangulation's edges, and the narrowest
real gap between two obstacles is often not one of them. A planned line was
then drawn a fraction of a millimetre into a neighbour. Each repair to the
geometry moved the miss to another net, and between commits 0c576608 and
09dfb11e the crowd and stagemix cells flipped between passing and failing with
each change. That is the same whack-a-mole the topological router was built
to end, moved from the plan into the drawing.

**What changes.** For a family with `engine: topo` the planner does the
global work:
- it plans every net together;
- it negotiates crossings;
- it chooses each net's layer;
- it produces a guide, the way each net's line goes.

The grid router (`pcb_route2`) lays the copper. Each net is given a corridor
along its guide, cheap inside and dear outside, and its other layers are
made dearer. Rip-up, rescue and push all stay. Legality is the grid
router's, through `fits()`, as for every other family. Planner and detailed
router is the split most autorouters make.

**What stays.** Steps 1 to 3 of the Decision (the map, routes as places in
edge orders, negotiated crossings) stand. The rubber-band drawing stays in
`pcb_topo` as the engine `topo-bands`, with its bench cells. It may replace
the grid laying where it proves itself, as a later stage.


## Amendment, 2026-10-12: the cold trial drops locked copper on the parts it moves

**Decided by the owner, 2026-10-12**, from three options put to them in the
working chat. The other two were: pin every part that has locked copper,
or strip all locked copper. They chose to drop the locked copper on the
parts the placement moves.

**Why.** The cold trial re-places most of the main board. Its first run
under the topological engine moved 82 of 170 parts. It kept a locked track
unless that track reached a moved part's pad. Two kinds of locked copper
were left in open board:
- locked middles of routes whose unlocked ends were stripped;
- locked stubs from a fixed part's pad toward where a moved part had been.
That is 40 dangling ends on 13 nets. Families 1 to 3 were routed round
them, and joined some of their own lines to them.

**What changes.** `strip` in the trial (`hardware/boards/main-board/cold_trial.py`)
also drops a locked island:
- that reaches no pad and no zone of its net; or
- that touched unlocked copper of its net and reaches fewer than two pads.
An island that joins two pads by itself is a whole route and stays. The
breath pair is one; an unlocked branch also touched it.

What stays is the copper of the fixed parts: the analog block's hand routes,
the pair and its guards, and the fixed parts' plane vias. The source board's
locked copper is not touched. This applies to the trial only, which copies
the board.

## Amendment, 2026-10-13: Freerouting routes; development goes to placement

**Decided by the owner, 2026-10-13**, in the working chat. The owner, of the
router: *"it's obviously apparent that this Auto is slow and also not very
good"*. Of the way forward: *"we should focus more on the original placement
and using free router … if we're going to do any more development we should do
it on the placement side of the components … only some components need be
locked, and if we're routing and we're finding issues with being able to find
good routes on a family, we should be able to just move some of the components
around and push and shove traces to get where we want."* Starting point: the
cold trial's clean placement. What stays: the analog hand routes and the parts
a rule fixes (the connectors among them).

**Why.** The measurements of 2026-10-12, on one placement (#47):

| | This router | Freerouting |
|---|---|---|
| The whole board | about 45 min for 26 of its 89 signal nets | 89 nets in 49 min, 5 left open |
| On the same 26 nets, length / airwire | 1.13x | 1.17x |
| On the same 26 nets, vias | 39 | 55 |

So this router's copper was as good or better, but it was far slower. Its
fixes had become the patch-and-rerun loop this ADR was written to end, at 1 to
2 hours a cycle. The push-and-shove the owner asked for in the Context is
Freerouting's core, and KiCad's interactive router does it too. The board's
hard places proved to be placement and constraints, not the router:
- J-MCU's back row escapes only through a 3 mm strip;
- the SPI bus runs 220 mm between two fixed parts;
- the chain's length is its airwire.

**What changes.**
- **Routing is Freerouting's.** This means `tools/pcb_freeroute.py`, the
  pinned release, with automatic neck-down now off.
- **The main board's driver is `hardware/boards/main-board/fr_trial.py`.** It
  strips the placement's copper but for the analog hand routes, lays the moat
  keep-out and the plane fanout, routes with Freerouting, runs `post_route`,
  then scores the result (`tools/pcb_score.py`) and runs KiCad's DRC.
- **Development goes to placement.** Where a family will not route cleanly,
  the parts in its way move (`pcb_pack`), and the board is routed again.

**What stays.**
- `pcb_route2` and `pcb_topo` stay as they are, with their benches, but are
  not developed further for this board.
- So do the scorecard, `skip_pads` and `rescue_s`, the acid-trap repairs, and
  the cold trial's placement and copper rules.
