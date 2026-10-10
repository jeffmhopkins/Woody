"""The bench for the centreline router and its tools (issue #46): small constructed boards,
one behaviour each, every cell in its OWN PROCESS (a new pcbnew.BOARD() switches KiCad's
current project) and every routed result proved by KiCad's own DRC on the saved board -
the router's own model proves nothing about itself.

    python3 tools/pcb_route2_test.py                 # every cell; exit 1 on a failure
    python3 tools/pcb_route2_test.py pinch bus       # some cells
    python3 tools/pcb_route2_test.py --plot DIR      # ...and a 2D plot of each result

Each cell prints what it measured and PASS or FAIL against what it declares. A cell that
writes a board also requires 0 DRC errors, 0 unconnected items and 0 of pcb.py check's
acid traps (check_tracks: KiCad's DRC has no such test), unless it says why not.

  fanout       a 2 x 5, 1.27 mm header fanned out to ten pads: all route
  pinch        three nets through a 1.30 mm gap on one layer: all route at pitch 0.1
  updown       a wall across the front: the net goes under it, exactly two vias
  bus          a four-net bus family: one reserved corridor, members at an even pitch
  nonplanar    two nets that must cross on one layer: "no path", fast, not "budget"
  locked       a locked wall with a gap: the net goes through it, the wall is untouched
  offgrid      pads off the sketch grid: off-grid stubs, legal, DRC clean
  via_ratio    a front-only detour 1.12x the via path is taken; one 1.36x is not
  field        a heading field turns a diagonal route onto its axis; an avoid field empties a band
  shove        reroute --pull: the blocking net is shoved, the locked one is not, the net shortens
  slide        a via slid along its runs: the run shortens, crossings do not rise
  fold         an up-then-down pair 1 mm long folded onto one face: two vias gone
  jogs         a staircase rubber-banded: fewer segments, shorter
  equalise     a track off-centre between two neighbours moved to the middle of its gap
  fillet       corners filleted into arcs: arcs written, DRC clean
  ground       ground routed as a net, stitched and poured: every ground pad met after the fill
  enclosed     a ground pad walled in on the front by a signal loop: met through the back
  stitch       a ground pad no track can reach (walled in on the front, the back closed to
               tracks but not to the pour): a stitching via beside it, and one in the main group
               so the two faces' pours are one net - every pad met after the fill
  pourcut      a locked loop on the back cuts off a piece of the back pour holding one ground
               pad - legal to fits, which cannot see a pour: the pour pass finds that group
               after the fill and ties it to the main one with a via; 0 unconnected
  planes4      four layers, GND the plane on In1.Cu and POS on In2.Cu: no other net's track on a
               plane layer, every plane pad its own locked via, pcb_main.check_planes clean
  island4      ...with an AGND island in In1.Cu, its moat and tie NT1: the island's vias on it,
               GND's off it and its moat, the signal leaving the island crosses the moat only
               in the tie's window - check_planes clean
  optin4       a net whose class names [F.Cu, In2.Cu] routes under a wall on both outer layers
               through In2.Cu; no other net uses it
  orphan4      a locked loop of another net in In1.Cu cuts a GND pad's via off the plane: the
               orphan pass finds it after the fill and fans the pad out again into the body
  fragments    a net whose pads each carry a LOCKED stub (an escape, a hand route): two
               fragments, each touching a pad, joined to nothing - the router must join them
               (found on the main board: 28 connections left open by treating "touches the
               net's copper" as "joined")
  lockedvia    a hand route locked track by track with its via left unlocked (#45's /IO2 on
               the main board): taking up "the unlocked copper" keeps that via - it is the
               locked route's own - and the route stays whole
  guard        a locked pair leg (layout.yaml pairs: guard) and a net whose straight way runs
               inside its guard: routed off it by the clearance plus the guard - pcb.py's own
               check_pair_guard clean
  rescue       a net walled out by an earlier one: rescue takes that one up and both route
  minikey      a three-key board: packed (pcb_pack) then routed, liquid pass, DRC clean
"""
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

LAY = {"rules": {"track": 0.25, "track_min": 0.2, "clearance": 0.2, "via": 0.7, "via_drill": 0.3, "edge_clearance": 0.3,
                 "power_track": 0.4}, "fab": {"hole_to_hole": 0.25, "hole_clearance": 0.25}}
CELLS = ["fanout", "pinch", "updown", "bus", "nonplanar", "locked", "offgrid", "via_ratio", "field", "shove", "slide",
         "fold", "jogs", "equalise", "fillet", "ground", "enclosed", "stitch", "pourcut", "rescue", "minikey",
         "planes4", "island4", "optin4", "orphan4", "fragments", "lockedvia", "guard"]


def _setup():
    import pcbnew
    import pcb_route2 as R2
    import pcb_testboards as T
    return pcbnew, R2, T


def finish(name, b, m, r, out, plot=None, pour=None, nets=None, drc=True):
    """Write the router's runs to the board, save it, DRC it, plot it."""
    pcbnew, R2, _ = _setup()
    R2.write(b, m, r.runs, pour=pour)
    p = os.path.join(out, f"{name}.kicad_pcb")
    pcbnew.SaveBoard(p, b)
    res = {}
    if drc:
        errs, unc = R2.drc(p)
        # and pcb.py check's own track test, which KiCad's DRC has no form of: two tracks of
        # a net meeting under 90 degrees, at 0 degrees included (an overlap doubling back)
        import pcb
        acid = pcb.check_tracks(pcbnew.LoadBoard(p))
        res = {"drc_errors": len(errs), "unconnected": unc, "drc": [e[:2] for e in errs[:5]], "acid_traps": len(acid)}
    if plot:
        import pcb_plot
        pcb_plot.plot(p, os.path.join(plot, f"route2-{name}.png"), nets=nets or ["*"], title=f"route2 bench: {name}")
    return res


def clean(res):
    return res.get("drc_errors") == 0 and res.get("unconnected") == 0 and res.get("acid_traps", 0) == 0


# ------------------------------------------------------------------ cells

def cell_fanout(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(44.0, 24.0)
    nets = [f"N{k}" for k in range(10)]
    T.header(b, "J1", nets, 8.0, 12.0, locked=True)
    for k, n in enumerate(nets):
        T.tp(b, f"TP{k}", n, 38.0, 2.5 + 2.1 * k)
    m = R2.model_from_board(b, LAY)
    r = R2.Router(m, pitch=0.2)
    failed = r.route()
    res = finish("fanout", b, m, r, out, plot)
    res.update(failed=sorted(failed), **r.summary())
    res["pass"] = not failed and clean(res)
    return res


def cell_pinch(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0)
    # a wall across the board at x 18-22, both layers, but for a gap y 8.35-9.65 (1.30 mm)
    T.keepout(b, 18.0, 0.0, 22.0, 8.35, layers=("F", "B"))
    T.keepout(b, 18.0, 9.65, 22.0, 20.0, layers=("F", "B"))
    for k, n in enumerate(["A", "B", "C"]):
        T.tp(b, f"TPL{k}", n, 4.0, 5.0 + 4.0 * k)
        T.tp(b, f"TPR{k}", n, 36.0, 5.0 + 4.0 * k)
    lay = dict(LAY, net_classes={"front": {"nets": ["A", "B", "C"], "layers": ["F.Cu"]}})
    m = R2.model_from_board(b, lay)
    r = R2.Router(m, pitch=0.1)
    failed = r.route(rescue=False)       # rescue called by hand below, to show it
    first = sorted(failed)
    for n in list(failed):              # the router's own pipeline: route, then rescue
        if r.rescue(n):
            failed.pop(n)
    res = finish("pinch", b, m, r, out, plot)
    res.update(failed_first=first, failed=sorted(failed), log=r.log, **r.summary())
    # three tracks of 0.25 at 0.2 clearance need 1.15 mm, and fits keeps its few microns'
    # margin past each clearance: at pitch 0.1 the lanes stand 0.5 apart, in a 1.30 mm gap
    res["pass"] = not failed and clean(res)
    return res


def cell_updown(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0)
    T.keepout(b, 18.0, 0.0, 22.0, 20.0, layers=("F",), vias=False)
    T.tp(b, "TP1", "S", 5.0, 10.0)
    T.tp(b, "TP2", "S", 35.0, 10.0)
    m = R2.model_from_board(b, LAY)
    r = R2.Router(m)
    failed = r.route()
    res = finish("updown", b, m, r, out, plot)
    res.update(failed=sorted(failed), **r.summary())
    res["pass"] = not failed and res["vias"] == 2 and clean(res)
    return res


def cell_bus(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(50.0, 24.0)
    nets = ["D0", "D1", "D2", "D3"]
    for k, n in enumerate(nets):
        T.tp(b, f"L{k}", n, 4.0, 6.0 + 1.2 * k, 0.8, 0.8)
        T.tp(b, f"R{k}", n, 46.0, 14.0 + 1.2 * k, 0.8, 0.8)
    T.hole(b, "H1", 25.0, 11.8, 3.0)
    lay = dict(LAY, net_classes={"bus": {"nets": nets, "layers": ["F.Cu"]}})
    m = R2.model_from_board(b, lay)
    r = R2.Router(m, pitch=0.15)
    fam = {"name": "data", "nets": nets, "bus": True, "pitch": 0.6}
    failed = r.route(families=[fam])
    res = finish("bus", b, m, r, out, plot)
    res.update(failed=sorted(failed), **r.summary())
    # at the corridor's middle the members stand one pitch apart, measured across it
    from shapely.geometry import LineString
    gaps = []
    if "family:data" in getattr(r, "corridors", {}):
        line = r.corridors["family:data"][0]
        mid = line.interpolate(0.5, normalized=True)
        a = line.interpolate(max(0.0, line.project(mid) - 0.5))
        c = line.interpolate(min(line.length, line.project(mid) + 0.5))
        offs = []
        for n in nets:
            g = LineString([p for run in r.runs_of(n) for p in [q[:2] for q in run.pts]])
            q = g.interpolate(g.project(mid))
            sgn = 1 if (c.x - a.x) * (q.y - a.y) - (c.y - a.y) * (q.x - a.x) > 0 else -1
            offs.append(sgn * mid.distance(q))
        offs.sort()
        gaps = [round(b_ - a_, 3) for a_, b_ in zip(offs, offs[1:])]
    res.update(corridor="family:data" in getattr(r, "corridors", {}), lane_gaps=gaps)
    res["pass"] = not failed and clean(res) and res["corridor"] and len(gaps) == 3 and all(abs(g - 0.6) <= 0.08 for g in gaps)
    return res


def cell_nonplanar(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 12.0)
    # a channel y 3-9 between x 8 and 32; each pad in a pocket open only into it: A goes
    # top-left to bottom-right, B bottom-left to top-right, front only - they must cross
    for x0, y0, x1, y1 in ((8.0, 0.0, 32.0, 3.0), (8.0, 9.0, 32.0, 12.0), (0.0, 0.0, 3.3, 12.0), (36.7, 0.0, 40.0, 12.0),
                           (0.0, 0.0, 8.0, 3.3), (0.0, 8.7, 8.0, 12.0), (32.0, 0.0, 40.0, 3.3), (32.0, 8.7, 40.0, 12.0),
                           (0.0, 5.6, 8.0, 6.4), (32.0, 5.6, 40.0, 6.4)):
        T.keepout(b, x0, y0, x1, y1, layers=("F", "B"))
    T.tp(b, "A1", "A", 4.0, 4.3)
    T.tp(b, "A2", "A", 36.0, 7.7)
    T.tp(b, "B1", "B", 4.0, 7.7)
    T.tp(b, "B2", "B", 36.0, 4.3)
    lay = dict(LAY, net_classes={"front": {"nets": ["A", "B"], "layers": ["F.Cu"]}})
    m = R2.model_from_board(b, lay)
    r = R2.Router(m, budget=2_000_000)
    t0 = time.monotonic()
    failed = r.route(first=["A"])
    dt = time.monotonic() - t0
    res = finish("nonplanar", b, m, r, out, plot, drc=False)
    res.update(failed=failed, seconds=round(dt, 1), **r.summary())
    res["pass"] = list(failed) == ["B"] and failed["B"] == "none" and dt < 60
    return res


def cell_locked(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0)
    T.tp(b, "TP1", "T", 5.0, 10.0)
    T.tp(b, "TP2", "T", 35.0, 10.0)
    T.tp(b, "W1", "W", 20.0, 1.5)
    T.tp(b, "W2", "W", 20.0, 18.5)
    # W's locked wall down x 20, under the board for y 13-15 through two locked vias: the only
    # front-layer way for T is between those vias
    T.track(b, "W", [(20.0, 1.5), (20.0, 13.0)], locked=True)
    T.track(b, "W", [(20.0, 15.0), (20.0, 18.5)], locked=True)
    T.track(b, "W", [(20.0, 13.0), (20.0, 15.0)], layer="B", locked=True)
    T.via(b, "W", 20.0, 13.0, locked=True)
    T.via(b, "W", 20.0, 15.0, locked=True)
    before = sorted((t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y) for t in b.GetTracks())  # W's alone
    lay = dict(LAY, net_classes={"front": {"nets": ["T"], "layers": ["F.Cu"]}})
    m = R2.model_from_board(b, lay)
    took = R2.take_up(m, {"W"})          # locked: nothing comes up
    try:
        locked_refused = False
        e = next(e for e in m.index.e.values() if e.net == "W" and e.kind == "track")
        m.index.remove(e.id)
    except R2.LockedError:
        locked_refused = True
    r = R2.Router(m)
    failed = r.route(["T"])
    res = finish("locked", b, m, r, out, plot)
    after = sorted((t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y) for t in b.GetTracks() if t.GetNetname() == "W")
    res.update(failed=sorted(failed), taken_up=took, locked_refused=locked_refused, wall_untouched=after == before, **r.summary())
    res["pass"] = not failed and took == 0 and locked_refused and after == before and clean(res)
    return res


def cell_offgrid(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0)
    T.tp(b, "TP1", "S", 5.137, 7.263, 0.6, 0.9)
    T.tp(b, "TP2", "S", 30.411, 12.917, 0.9, 0.6)
    T.tp(b, "TP3", "S", 18.023, 15.551, 0.6, 0.6)
    m = R2.model_from_board(b, LAY)
    r = R2.Router(m)
    failed = r.route()
    offs = [p for run in r.runs for p in (run.pts[0], run.pts[-1])]
    res = finish("offgrid", b, m, r, out, plot)
    res.update(failed=sorted(failed), **r.summary(), ends=[(round(x, 3), round(y, 3)) for x, y, _ in offs])
    res["pass"] = not failed and clean(res)
    return res


def cell_via_ratio(out, plot):
    pcbnew, R2, T = _setup()
    res = {}
    # short: a front-only wall the net passes at 45 degrees for a few mm; long: a wall down
    # almost the whole board from pads near its top, so the way round is 1.5x the way under
    for tag, (h, y0, y1, py) in (("short", (20.0, 6.0, 14.0, 10.0)), ("long", (30.0, 0.0, 28.0, 3.0))):
        b = T.new_board(40.0, h)
        T.keepout(b, 15.0, y0, 25.0, y1, layers=("F",), vias=False)
        T.tp(b, "TP1", "S", 5.0, py)
        T.tp(b, "TP2", "S", 35.0, py)
        m = R2.model_from_board(b, LAY)
        r = R2.Router(m)
        failed = r.route()
        rr = finish(f"via_ratio_{tag}", b, m, r, out, plot)
        res[tag] = dict(failed=sorted(failed), vias=r.summary()["vias"], length=r.summary()["length_mm"], clean=clean(rr))
    res["pass"] = res["short"]["vias"] == 0 and res["long"]["vias"] == 2 and res["short"]["clean"] and res["long"]["clean"] \
        and not res["short"]["failed"] and not res["long"]["failed"]
    return res


def cell_field(out, plot):
    pcbnew, R2, T = _setup()
    res = {}
    from shapely.geometry import box, LineString
    start = box(3, 0, 7, 20)
    def vertical_share(runs, region):
        tot = on = 0.0
        for run in runs:
            for _, p, q, _ in run.segments():
                ln = LineString([p, q]).intersection(region).length
                if ln <= 0:
                    continue
                tot += ln
                if abs(q[0] - p[0]) < 1e-6:
                    on += ln
        return on / tot if tot else 0.0
    # control: the diagonal-and-straight shortest way. heading: a lane down the start region
    # (heading 90 degrees, weight 0.3) - the route does its descent in it, vertically, and only
    # then turns along the board. avoid: a band weighted 4x is left.
    for tag, fields in (("control", []), ("heading", [{"rect": [3, 0, 7, 20], "heading": 90.0, "weight": 0.3, "k": 2.0}]),
                        ("avoid", [{"rect": [12, 0, 28, 13], "weight": 4.0}])):
        b = T.new_board(40.0, 20.0)
        T.tp(b, "TP1", "S", 5.0, 3.0)
        T.tp(b, "TP2", "S", 35.0, 15.0)
        lay = dict(LAY, net_classes={"front": {"nets": ["S"], "layers": ["F.Cu"]}})
        m = R2.model_from_board(b, lay)
        r = R2.Router(m, fields=fields)
        failed = r.route()
        rr = finish(f"field_{tag}", b, m, r, out, plot)
        band = box(12, 0, 28, 13)
        inband = sum(LineString([p, q]).intersection(band).length for run in r.runs for _, p, q, _ in run.segments())
        res[tag] = dict(failed=sorted(failed), vertical_in_start=round(vertical_share(r.runs, start), 2),
                        in_band_mm=round(inband, 1), length=r.summary()["length_mm"], clean=clean(rr))
    res["pass"] = all(res[t]["clean"] and not res[t]["failed"] for t in ("control", "heading", "avoid")) \
        and res["heading"]["vertical_in_start"] >= 0.6 and res["control"]["vertical_in_start"] <= 0.2 \
        and res["avoid"]["in_band_mm"] < res["control"]["in_band_mm"] - 2
    return res


def cell_shove(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(50.0, 20.0)
    T.tp(b, "A1", "A", 5.0, 10.0)
    T.tp(b, "A2", "A", 45.0, 10.0)
    T.tp(b, "B1", "B", 15.0, 5.0)
    T.tp(b, "B2", "B", 35.0, 5.0)
    T.tp(b, "C1", "C", 6.0, 13.5)
    T.tp(b, "C2", "C", 44.0, 13.5)
    T.track(b, "C", [(6.0, 13.5), (8.0, 11.0), (42.0, 11.0), (44.0, 13.5)], locked=True)
    lay = dict(LAY, net_classes={"front": {"nets": ["A", "B", "C"], "layers": ["F.Cu"]}})
    m = R2.model_from_board(b, lay)
    r = R2.Router(m)
    # B laid (unlocked) the long way, down along y 10 where A wants to run
    runB = R2.Run("B", [(15.0, 5.0, 0), (15.0, 10.0, 0), (35.0, 10.0, 0), (35.0, 5.0, 0)], 0.25, (0.7, 0.3))
    assert not R2.fits(runB, m)
    R2.lay(runB, m)
    r.runs.append(runB)
    okA, _, _ = r.route_net("A")
    lenA0 = sum(x.length() for x in r.runs_of("A"))
    lenB0 = sum(x.length() for x in r.runs_of("B"))
    rep = r.reroute("A", pull=1.0)
    lenA1 = sum(x.length() for x in r.runs_of("A"))
    c_before = [(round(t.GetStart().x), round(t.GetEnd().x)) for t in b.GetTracks() if t.GetNetname() == "C"]
    res = finish("shove", b, m, r, out, plot)
    c_after = [(round(t.GetStart().x), round(t.GetEnd().x)) for t in b.GetTracks() if t.GetNetname() == "C"]
    res.update(first_route_ok=okA, A_before=round(lenA0, 1), A_after=round(lenA1, 1), B_before=round(lenB0, 1),
               B_after=round(sum(x.length() for x in r.runs_of("B")), 1), report=rep, C_untouched=c_before == c_after)
    res["pass"] = okA and rep["mode"] == "shove" and "B" in rep["shoved"] and lenA1 < lenA0 - 3 and c_before == c_after and clean(res)
    return res


def _single(R2, T, pts, nets_pads, lay=LAY, extra=None, w=50.0, h=20.0):
    b = T.new_board(w, h)
    for ref, n, x, y, back in nets_pads:
        T.tp(b, ref, n, x, y, back=back)
    if extra:
        extra(b)
    m = R2.model_from_board(b, lay)
    r = R2.Router(m)
    runs = []
    for n, p in pts:
        run = R2.Run(n, p, 0.25, (0.7, 0.3))
        bad = R2.fits(run, m)
        assert not bad, bad
        R2.lay(run, m)
        r.runs.append(run)
        runs.append(run)
    return b, m, r


def cell_slide(out, plot):
    pcbnew, R2, T = _setup()
    b, m, r = _single(R2, T, [("S", [(5.0, 5.0, 0), (25.0, 5.0, 0), (25.0, 5.0, 1), (25.0, 15.0, 1), (35.0, 15.0, 1)])],
                      [("TP1", "S", 5.0, 5.0, False), ("TP2", "S", 35.0, 15.0, True)])
    l0, x0 = r.summary()["length_mm"], r.summary()["crossings"]
    n = r.slide_vias()
    s = r.summary()
    res = finish("slide", b, m, r, out, plot)
    res.update(moved=n, length_before=l0, length_after=s["length_mm"], crossings_before=x0, crossings_after=s["crossings"],
               pts=r.runs[0].pts)
    res["pass"] = n >= 1 and s["length_mm"] < l0 - 1 and s["crossings"] <= x0 and clean(res)
    return res


def cell_fold(out, plot):
    pcbnew, R2, T = _setup()
    b, m, r = _single(R2, T, [("S", [(5.0, 10.0, 0), (15.0, 10.0, 0), (15.0, 10.0, 1), (16.0, 10.0, 1), (16.0, 10.0, 0),
                                     (35.0, 10.0, 0)])],
                      [("TP1", "S", 5.0, 10.0, False), ("TP2", "S", 35.0, 10.0, False)])
    v0 = r.summary()["vias"]
    n = r.uncross()
    res = finish("fold", b, m, r, out, plot)
    res.update(folded=n, vias_before=v0, vias_after=r.summary()["vias"])
    res["pass"] = n == 1 and v0 == 2 and r.summary()["vias"] == 0 and clean(res)
    return res


def cell_jogs(out, plot):
    pcbnew, R2, T = _setup()
    stair = [(5.0, 10.0, 0), (10.0, 10.0, 0), (10.0, 11.0, 0), (15.0, 11.0, 0), (15.0, 10.0, 0), (20.0, 10.0, 0),
             (20.0, 11.0, 0), (25.0, 11.0, 0), (26.0, 12.0, 0), (35.0, 12.0, 0)]
    b, m, r = _single(R2, T, [("S", stair)], [("TP1", "S", 5.0, 10.0, False), ("TP2", "S", 35.0, 12.0, False)])
    s0 = r.summary()
    n = r.rubber_band()
    s1 = r.summary()
    res = finish("jogs", b, m, r, out, plot)
    res.update(changed=n, segments_before=s0["segments"], segments_after=s1["segments"], length_before=s0["length_mm"],
               length_after=s1["length_mm"])
    res["pass"] = n >= 1 and s1["segments"] < s0["segments"] and s1["length_mm"] < s0["length_mm"] and clean(res)
    return res


def cell_equalise(out, plot):
    pcbnew, R2, T = _setup()
    # A along y 9.5 and C along y 12; B between them at y 10.55, nearer A: equalise moves it to
    # the middle of its gap, its diagonals' joints sliding along them
    pads = [("A1", "A", 10.0, 9.5, False), ("A2", "A", 40.0, 9.5, False), ("C1", "C", 10.0, 12.0, False),
            ("C2", "C", 40.0, 12.0, False), ("B1", "B", 5.0, 6.0, False), ("B2", "B", 45.0, 6.0, False)]
    runs = [("A", [(10.0, 9.5, 0), (40.0, 9.5, 0)]), ("C", [(10.0, 12.0, 0), (40.0, 12.0, 0)]),
            ("B", [(5.0, 6.0, 0), (5.0, 8.0, 0), (7.55, 10.55, 0), (42.45, 10.55, 0), (45.0, 8.0, 0), (45.0, 6.0, 0)])]
    b, m, r = _single(R2, T, runs, pads)
    def gaps():
        run = r.runs_of("B")[0]
        y = [p[1] for p in run.pts if 9.6 < p[1] < 12.0][0]
        return round(y - 9.5 - 0.25, 3), round(12.0 - y - 0.25, 3)
    g0 = gaps()
    n = r.equalise()
    g1 = gaps()
    res = finish("equalise", b, m, r, out, plot)
    res.update(moves=n, gaps_before=g0, gaps_after=g1)
    res["pass"] = n >= 1 and abs(g1[0] - g1[1]) < abs(g0[0] - g0[1]) and abs(g1[0] - g1[1]) <= 0.1 and clean(res)
    return res


def cell_fillet(out, plot):
    pcbnew, R2, T = _setup()
    zig = [(5.0, 5.0, 0), (15.0, 5.0, 0), (20.0, 10.0, 0), (30.0, 10.0, 0), (30.0, 15.0, 0), (40.0, 15.0, 0)]
    b, m, r = _single(R2, T, [("S", zig)], [("TP1", "S", 5.0, 5.0, False), ("TP2", "S", 40.0, 15.0, False)])
    n = r.fillet_all(1.5)
    res = finish("fillet", b, m, r, out, plot)
    arcs = sum(1 for t in b.GetTracks() if type(t) is pcbnew.PCB_ARC)
    res.update(filleted=n, arcs=arcs)
    res["pass"] = n == 1 and arcs == 4 and clean(res)
    return res


def cell_ground(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 24.0)
    T.soic(b, "U1", ["S1", "S2", "S3", "GND", "S4", "", "", "V3V3"], 14.0, 12.0, 0, True)
    T.passive(b, "C1", "V3V3", "GND", 22.0, 6.0, locked=True)
    T.passive(b, "C2", "V3V3", "GND", 8.0, 19.0, locked=True)
    for k, (x, y) in enumerate([(34.0, 4.0), (34.0, 9.0), (34.0, 14.0), (34.0, 19.0)]):
        T.tp(b, f"TP{k}", f"S{k + 1}", x, y)
    T.tp(b, "TPG", "GND", 30.0, 21.0)
    T.tp(b, "TPV", "V3V3", 4.0, 4.0)
    lay = dict(LAY, power_nets=["V3V3"])
    m = R2.model_from_board(b, lay)
    r = R2.Router(m)
    failed = r.route(ground="GND")
    res = finish("ground", b, m, r, out, plot, pour="GND")
    res.update(failed=sorted(failed), log=r.log, **r.summary())
    res["pass"] = not failed and clean(res)
    return res


def cell_enclosed(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 24.0)
    T.tp(b, "G1", "GND", 20.0, 12.0)
    T.tp(b, "G2", "GND", 5.0, 5.0)
    T.tp(b, "L1", "LOOP", 14.0, 6.0)
    T.tp(b, "L2", "LOOP", 26.0, 18.0)
    # LOOP walls G1 in on the front, locked
    T.track(b, "LOOP", [(14.0, 6.0), (26.0, 6.0), (26.0, 18.0), (14.0, 18.0), (14.0, 6.0)], locked=True)
    m = R2.model_from_board(b, LAY)
    r = R2.Router(m)
    failed = r.route([], ground="GND")
    res = finish("enclosed", b, m, r, out, plot, pour="GND")
    res.update(failed=sorted(failed), log=r.log, **r.summary())
    res["pass"] = not failed and clean(res) and res["vias"] >= 1
    return res


def cell_stitch(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 24.0)
    T.tp(b, "G1", "GND", 20.0, 12.0)
    T.tp(b, "G2", "GND", 5.0, 5.0)
    T.tp(b, "L1", "LOOP", 14.0, 6.0)
    T.tp(b, "L2", "LOOP", 26.0, 18.0)
    T.track(b, "LOOP", [(14.0, 6.0), (26.0, 6.0), (26.0, 18.0), (14.0, 18.0), (14.0, 6.0)], locked=True)
    # the back under the loop: no tracks, but vias and the pour may go in
    T.keepout(b, 13.0, 5.0, 27.0, 19.0, layers=("B",), tracks=True, vias=False, pour=True)
    m = R2.model_from_board(b, LAY)
    r = R2.Router(m)
    failed = r.route([], ground="GND")
    res = finish("stitch", b, m, r, out, plot, pour="GND")
    res.update(failed=sorted(failed), log=r.log, **r.summary())
    import re
    stitched = sum(int(m_) for l in r.log for m_ in re.findall(r"(\d+) stitching via", l))
    res["pass"] = clean(res) and stitched >= 1
    return res


def cell_pourcut(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 24.0)
    T.tp(b, "G1", "GND", 5.0, 5.0)
    T.tp(b, "G2", "GND", 35.0, 19.0)
    T.tp(b, "G3", "GND", 20.0, 12.0, back=True)      # inside the loop: it keeps that piece alive, and alone
    T.tp(b, "L1", "LOOP", 14.0, 6.0, back=True)
    T.tp(b, "L2", "LOOP", 26.0, 18.0, back=True)
    T.track(b, "LOOP", [(14.0, 6.0), (26.0, 6.0), (26.0, 18.0), (14.0, 18.0), (14.0, 6.0)], layer="B", locked=True)
    m = R2.model_from_board(b, LAY)
    r = R2.Router(m)
    # G3 is reached by no track (the loop walls it in on the back): the ground step leaves
    # it to the pour, as a key board's does
    failed = r.route([], ground="GND")
    for run in [x for x in r.runs if x.net == "GND" and any(abs(p[0] - 20.0) < 3 and abs(p[1] - 12.0) < 3 for p in x.pts)]:
        R2.unlay(run, m)
        r.runs.remove(run)
    R2.write(b, m, r.runs, pour="GND")
    p = os.path.join(out, "pourcut.kicad_pcb")
    pcbnew.SaveBoard(p, b)
    before = R2.drc(p)
    code = (f"import sys, json; sys.path.insert(0, {HERE!r}); import pcb_route2; "
            f"print('TIE ' + json.dumps(pcb_route2.tie_pour_islands({p!r}, {LAY!r}, 'GND')))")
    t = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    tie = [json.loads(l[4:]) for l in t.stdout.splitlines() if l.startswith("TIE ")]
    errs, unc = R2.drc(p)
    if plot:
        import pcb_plot
        pcb_plot.plot(p, os.path.join(plot, "route2-pourcut.png"), nets=["*"], title="route2 bench: pourcut")
    res = {"failed": sorted(failed), "unconnected_before": before[1], "tie": tie[0] if tie else t.stderr[-500:],
           "drc_errors": len(errs), "unconnected": unc}
    res["pass"] = before[1] >= 1 and bool(tie) and tie[0][0] >= 1 and not tie[0][1] and not errs and unc == 0
    return res


def _four_checks(R2, b, lay, p):
    """check_planes (pcb_main, the repository's own) and the plane-layer rule on a saved board."""
    import pcbnew
    import pcb_main
    bb = pcbnew.LoadBoard(p)
    planes_bad = pcb_main.check_planes(bb, lay)
    plane_layers = {pl["layer"]: pl["net"] for pl in lay["planes"]}
    named = {n for c in (lay.get("net_classes") or {}).values() for n in c.get("nets", []) if c.get("layers")}
    on_plane = sorted({t.GetNetname() for t in bb.GetTracks() if type(t) is pcbnew.PCB_TRACK
                       and bb.GetLayerName(t.GetLayer()) in plane_layers and t.GetNetname() not in named})
    vias = {}
    for t in bb.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            vias.setdefault(t.GetNetname(), []).append(t)
    return planes_bad, on_plane, vias


def cell_planes4(out, plot):
    pcbnew, R2, T = _setup()
    b, lay = T.four_layer(False)
    m = R2.model_from_board(b, lay)
    r = R2.Router(m)
    failed = r.route()
    res = finish("planes4", b, m, r, out, plot)
    p = os.path.join(out, "planes4.kicad_pcb")
    bad, on_plane, vias = _four_checks(R2, b, lay, p)
    smd_plane_pads = [q for q in m.pads if q.net in ("GND", "POS") and q.smd]
    locked = all(v.IsLocked() for n in ("GND", "POS") for v in vias.get(n, []))
    res.update(failed=sorted(failed), check_planes=bad[:5], tracks_on_plane_layers=on_plane, plane_pads=len(smd_plane_pads),
               plane_vias=sum(len(vias.get(n, [])) for n in ("GND", "POS")), fanout_locked=locked, log=r.log[:3], **r.summary())
    res["pass"] = not failed and clean(res) and not bad and not on_plane and res["plane_vias"] >= len(smd_plane_pads) and locked
    return res


def cell_island4(out, plot):
    pcbnew, R2, T = _setup()
    b, lay = T.four_layer(True)
    m = R2.model_from_board(b, lay)
    r = R2.Router(m)
    failed = r.route()
    res = finish("island4", b, m, r, out, plot)
    p = os.path.join(out, "island4.kicad_pcb")
    bad, on_plane, vias = _four_checks(R2, b, lay, p)
    isl = m.planes.islands[0]
    agnd_on = all(isl["poly"].contains(Point_(v)) for v in vias.get("AGND", []))
    gnd_off = not any(isl["moat"].contains(Point_(v)) for v in vias.get("GND", []))
    # where SIG_A crosses the moat on the front: inside the tie's window
    from shapely.geometry import LineString
    cross = [LineString([(pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)), (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))])
             for t in pcbnew.LoadBoard(p).GetTracks() if type(t) is pcbnew.PCB_TRACK and t.GetNetname() == "SIG_A"]
    over = [c.intersection(isl["ring"]) for c in cross if c.intersects(isl["ring"])]
    in_window = all(o.within(isl["windows"].buffer(0.3)) for o in over) if over else None
    res.update(failed=sorted(failed), check_planes=bad[:5], tracks_on_plane_layers=on_plane, agnd_vias_on_island=agnd_on,
               gnd_vias_off_moat=gnd_off, sig_crosses_moat_in_window=in_window, **r.summary())
    res["pass"] = not failed and clean(res) and not bad and not on_plane and agnd_on and gnd_off and in_window is True
    return res


def Point_(v):
    import pcbnew
    from shapely.geometry import Point
    return Point(pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y))


def cell_optin4(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0, layers=4)
    rect = [(0.3, 0.3), (39.7, 0.3), (39.7, 19.7), (0.3, 19.7)]
    T.zone(b, "GND", pcbnew.In1_Cu, rect)
    T.zone(b, "POS", pcbnew.In2_Cu, rect)
    T.keepout(b, 18.0, 0.0, 22.0, 20.0, layers=("F", "B"), vias=False)
    T.tp(b, "C1", "CH", 5.0, 7.0)
    T.tp(b, "C2", "CH", 35.0, 7.0)
    T.tp(b, "O1", "OTHER", 5.0, 13.0)
    T.tp(b, "O2", "OTHER", 15.0, 13.0)
    lay = {"rules": {"track": 0.25, "clearance": 0.2, "via": 0.7, "via_drill": 0.3, "edge_clearance": 0.3},
           "planes": [{"layer": "In1.Cu", "net": "GND"}, {"layer": "In2.Cu", "net": "POS"}],
           "net_classes": {"channel": {"nets": ["CH"], "layers": ["F.Cu", "In2.Cu"]}}}
    m = R2.model_from_board(b, lay)
    r = R2.Router(m)
    failed = r.route()
    res = finish("optin4", b, m, r, out, plot, drc=False)
    used = {n: sorted({m.layer_names[L] for run in r.runs_of(n) for L, *_ in run.segments()}) for n in ("CH", "OTHER")}
    errs, _ = R2.drc(os.path.join(out, "optin4.kicad_pcb"))
    res.update(failed=sorted(failed), layers_used=used, drc_errors=len(errs))
    res["pass"] = not failed and "In2.Cu" in used["CH"] and not set(used["OTHER"]) & {"In1.Cu", "In2.Cu"} and not errs
    return res


def cell_orphan4(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0, layers=4)
    rect = [(0.3, 0.3), (39.7, 0.3), (39.7, 19.7), (0.3, 19.7)]
    T.zone(b, "GND", pcbnew.In1_Cu, rect)
    T.zone(b, "POS", pcbnew.In2_Cu, rect)
    T.tp(b, "G1", "GND", 20.0, 10.0)
    T.tp(b, "G2", "GND", 5.0, 5.0)
    T.tp(b, "L1", "LOOP", 16.5, 7.5)
    T.tp(b, "L2", "LOOP", 23.5, 12.5)
    lay = {"rules": {"track": 0.25, "clearance": 0.2, "via": 0.7, "via_drill": 0.3, "edge_clearance": 0.3},
           "planes": [{"layer": "In1.Cu", "net": "GND"}, {"layer": "In2.Cu", "net": "POS"}], "fanout": ["GND", "POS"],
           "net_classes": {"inner": {"nets": ["LOOP"], "layers": ["F.Cu", "In1.Cu"]}}}
    m = R2.model_from_board(b, lay)
    r = R2.Router(m)
    r.route()                               # G1 and G2 fanned out
    R2.write(b, m, r.runs)
    # then a locked loop of LOOP in In1.Cu round G1's via - the plane inside it a fragment
    # (within fanout's 4 mm reach of G1, so the pad can be fanned out past it)
    T.via(b, "LOOP", 16.5, 7.5, locked=True)
    T.via(b, "LOOP", 23.5, 12.5, locked=True)
    loop = [(16.5, 7.5), (23.5, 7.5), (23.5, 12.5), (16.5, 12.5), (16.5, 7.5)]
    for (x0, y0), (x1, y1) in zip(loop, loop[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(T.V(x0, y0))
        t.SetEnd(T.V(x1, y1))
        t.SetWidth(pcbnew.FromMM(0.25))
        t.SetLayer(pcbnew.In1_Cu)
        t.SetNet(T.net(b, "LOOP"))
        t.SetLocked(True)
        b.Add(t)
    p = os.path.join(out, "orphan4.kicad_pcb")
    pcbnew.SaveBoard(p, b)
    before = R2.drc(p)[1]
    code = (f"import sys, json; sys.path.insert(0, {HERE!r}); import pcb_route2; "
            f"print('ORPH ' + json.dumps(pcb_route2.fix_plane_orphans({p!r}, {lay!r})))")
    t_ = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    fix = [json.loads(l[5:]) for l in t_.stdout.splitlines() if l.startswith("ORPH ")]
    errs, unc = R2.drc(p)
    if plot:
        import pcb_plot
        pcb_plot.plot(p, os.path.join(plot, "route2-orphan4.png"), nets=["*"], title="route2 bench: orphan4")
    res = {"unconnected_before": before, "fix": fix[0] if fix else t_.stderr[-600:], "drc_errors": len(errs), "unconnected": unc}
    res["pass"] = before >= 1 and bool(fix) and fix[0][0] >= 1 and not fix[0][1] and not errs and unc == 0
    return res


def cell_fragments(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0)
    T.tp(b, "P1", "N", 5.0, 10.0)
    T.tp(b, "P2", "N", 35.0, 10.0)
    T.tp(b, "P3", "N", 20.0, 16.0)
    T.track(b, "N", [(5.0, 10.0), (8.0, 10.0)], locked=True)          # P1's escape
    T.track(b, "N", [(35.0, 10.0), (32.0, 10.0)], locked=True)        # P2's
    m = R2.model_from_board(b, LAY)
    r = R2.Router(m)
    failed = r.route()
    res = finish("fragments", b, m, r, out, plot)
    res.update(failed=sorted(failed), **r.summary())
    res["pass"] = not failed and clean(res) and res["runs"] >= 2
    return res


def cell_lockedvia(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0)
    T.tp(b, "P1", "N", 5.0, 10.0)
    T.tp(b, "P2", "N", 35.0, 10.0, back=True)
    T.track(b, "N", [(5.0, 10.0), (20.0, 10.0)], locked=True)
    T.via(b, "N", 20.0, 10.0, locked=False)                     # the hand route's via, left unlocked
    T.track(b, "N", [(20.0, 10.0), (35.0, 10.0)], layer="B", locked=True)
    T.tp(b, "Q1", "M", 5.0, 4.0)
    T.tp(b, "Q2", "M", 35.0, 4.0)
    T.track(b, "M", [(5.0, 4.0), (35.0, 4.0)])                   # plain unlocked copper: taken up
    m = R2.model_from_board(b, LAY)
    took = R2.take_up(m, {"N", "M"})
    r = R2.Router(m)
    failed = r.route()
    res = finish("lockedvia", b, m, r, out, plot)
    vias_n = sum(1 for t in pcbnew.LoadBoard(os.path.join(out, "lockedvia.kicad_pcb")).GetTracks()
                 if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "N")
    res.update(failed=sorted(failed), taken_up=took, kept_for_locked=m.kept_for_locked, n_vias=vias_n)
    res["pass"] = not failed and clean(res) and took == 1 and m.kept_for_locked == 1 and vias_n == 1
    return res


def cell_guard(out, plot):
    pcbnew, R2, T = _setup()
    import pcb
    b = T.new_board(40.0, 20.0)
    T.tp(b, "S1", "SENS", 4.0, 10.0, 0.6, 0.6)
    T.tp(b, "S2", "SENS", 36.0, 10.0, 0.6, 0.6)
    T.track(b, "SENS", [(4.0, 10.0), (36.0, 10.0)], locked=True)
    # N's pads clear of the guard; a hole on their straight line. The short way round is
    # under it, between the hole and the leg - inside the guard; the legal way is over it
    T.tp(b, "N1", "N", 6.0, 12.0, 0.6, 0.6)
    T.tp(b, "N2", "N", 34.0, 12.0, 0.6, 0.6)
    T.hole(b, "H1", 20.0, 12.4, 2.4)        # under it: room by the clearance, not by the guard
    lay = dict(LAY, pairs=[{"nets": ["SENS", "AG"], "layer": "F.Cu", "width": 0.25, "gap": 0.25, "guard": 0.55}],
               net_classes={"front": {"nets": ["N"], "layers": ["F.Cu"]}})
    m = R2.model_from_board(b, lay)
    r = R2.Router(m)
    failed = r.route(["N"])
    res = finish("guard", b, m, r, out, plot)
    bad = pcb.check_pair_guard(pcbnew.LoadBoard(os.path.join(out, "guard.kicad_pcb")), lay)
    low = min((p[1] for run in r.runs_of("N") for p in run.pts), default=None)
    res.update(failed=sorted(failed), check_pair_guard=bad, lowest_y=low, **r.summary())
    res["pass"] = not failed and clean(res) and not bad and low is not None and low >= 11.0 - 1e-6
    return res


def cell_rescue(out, plot):
    pcbnew, R2, T = _setup()
    b = T.new_board(40.0, 20.0)
    # a front-only wall down x 19.5-20.5 with one gap a single track wide (y 9.6-10.4). Y is
    # front-only and has no other way; X could go under the wall, but routed first its
    # shortest way is the gap - and Y is walled out. Rescue takes X up, routes Y, then X.
    T.keepout(b, 19.5, 0.0, 20.5, 9.6, layers=("F",), vias=False)
    T.keepout(b, 19.5, 10.4, 20.5, 20.0, layers=("F",), vias=False)
    T.tp(b, "Y1", "Y", 5.0, 10.0)
    T.tp(b, "Y2", "Y", 35.0, 10.0)
    T.tp(b, "X1", "X", 13.0, 10.0)
    T.tp(b, "X2", "X", 27.0, 10.0)
    lay = dict(LAY, net_classes={"front": {"nets": ["Y"], "layers": ["F.Cu"]}})
    m = R2.model_from_board(b, lay)
    r = R2.Router(m, pitch=0.1)
    failed = r.route(first=["X"], rescue=False)       # rescue called by hand below, to show it
    first = dict(failed)
    for n in list(failed):
        if r.rescue(n):
            failed.pop(n)
    res = finish("rescue", b, m, r, out, plot)
    res.update(failed_first=first, failed_after=sorted(failed), log=r.log, **r.summary())
    res["pass"] = list(first) == ["Y"] and not failed and clean(res)
    return res


def cell_minikey(out, plot):
    pcbnew, R2, T = _setup()
    import pcb_pack as P
    b = T.minikey()
    bd = P.board_of(b)
    body = ["SW1", "SW2", "SW3", "J1", "H1", "H2", "H3", "H4"]
    pk = P.Packer(bd, body)
    reps = [pk.pack("U1", ["C6", "R11"]), pk.pack("J1", ["C7"]),
            pk.pattern(["SW1", "SW2", "SW3"], {f"SW{k}": list(T.MINIKEY["keys"][k]) for k in (1, 2, 3)})]
    pk.apply(b)
    lay = dict(LAY, power_nets=["V3V3"])
    m = R2.model_from_board(b, lay)
    r = R2.Router(m, flow=0.3)
    failed = r.route(ground="GND")
    s0 = r.summary()
    liq = r.liquid(fillet=0.8)
    s1 = r.summary()
    res = finish("minikey", b, m, r, out, plot, pour="GND")
    res.update(packed=[x["result"] for x in reps], failed=sorted(failed), routed=s0, liquid=liq, after_liquid=s1)
    res["pass"] = all(x["result"] == "packed" for x in reps) and not failed and clean(res) \
        and s1["crossings"] <= s0["crossings"] and s1["length_mm"] <= s0["length_mm"]
    return res


# ------------------------------------------------------------------ harness

def run_cell(name, out, plot):
    t0 = time.monotonic()
    res = globals()["cell_" + name](out, plot)
    res["seconds"] = round(time.monotonic() - t0, 1)
    return res


def main():
    args = [a for a in sys.argv[1:]]
    plot = None
    if "--plot" in args:
        i = args.index("--plot")
        plot = os.path.abspath(args[i + 1])
        os.makedirs(plot, exist_ok=True)
        del args[i:i + 2]
    if args and args[0] == "--cell":
        res = run_cell(args[1], args[2], plot)
        print("RESULT " + json.dumps(res, default=str))
        return 0
    cells = args or CELLS
    out = tempfile.mkdtemp(prefix="route2-bench-")
    ok = True
    for c in cells:
        cmd = [sys.executable, os.path.abspath(__file__), "--cell", c, out] + (["--plot", plot] if plot else [])
        p = subprocess.run(cmd, capture_output=True, text=True)
        line = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
        if p.returncode or not line:
            print(f"{c:10s} FAIL (crashed)\n{p.stderr[-1500:]}")
            ok = False
            continue
        res = json.loads(line[-1][7:])
        passed = res.pop("pass")
        ok &= passed
        print(f"{c:10s} {'PASS' if passed else 'FAIL'}  {json.dumps(res, default=str)}")
    print(f"boards in {out}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
