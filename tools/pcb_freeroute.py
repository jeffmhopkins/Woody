"""The Freerouting round trip for tools/pcb.py's `route: freerouting` (the main board).

    board (saved, its net classes in the .kicad_pro)
      -> Specctra DSN (KiCad's own export)       planes, fixed wiring, keep-outs
      -> Freerouting, headless, in batch          every connection not yet made
      -> Specctra SES -> back into the board      KiCad's own import

WHAT GOES TO THE ROUTER. KiCad exports every copper zone as a plane, the plane
layers (LT_POWER) as `type power`, so Freerouting routes only on layers 1 and 4,
and every track and via already on the board as wiring - the fanout and the
breath pair are LOCKED, so they go as `(type fix)` and stay. A rule area that
keeps only FOOTPRINTS out (a ribbon plug's room, the regulator block) is not a
routing keep-out, but KiCad exports it as one: those are taken off the copy that
is exported, never off the board.

THE ROUTER. Freerouting v2.1.0, the last release that runs on Java 21 (from 2.2.0
it needs Java 25: docs/review/2026-09-21-pcb-pipeline-review/P4-freerouting.md).
It is fetched once by tools/setup-env.sh into ~/.cache/woody/, and checked
against its SHA-256 here. Headless (--gui.enabled=false), analytics off (-da).

It proves nothing about itself: pcb.py check runs KiCad's DRC over the result,
and every connection left unrouted is reported by name.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

import pcbnew

JAR_URL = "https://github.com/freerouting/freerouting/releases/download/v2.1.0/freerouting-2.1.0.jar"
JAR_SHA256 = "2c07d58f75dac03782664081e7a58b41c25400d871a9fcf166a2ea6fe60d5def"
JAR = os.path.join(os.path.expanduser("~"), ".cache", "woody", "freerouting-2.1.0.jar")
PASSES = 25           # asked for; Freerouting 2.1.0 does not honour it in batch (a run went to pass 52) - the job timeout bounds it
JOB_TIMEOUT = "00:20:00"   # Freerouting's own bound: it stops the job and still writes the session
                           # (a shell timeout's kill writes nothing); HH:MM:SS - "25m" parses as no timeout
TIMEOUT_S = 20 * 60 + 180  # the backstop, for a hung JVM
# Its costs, left at its own defaults. Tried on the first main-board layout: a flatter
# direction cost (1.2 against 2.5) and cheaper vias (20 against 50) left 25-31
# connections unrouted where the defaults left 16-18, in the same time. What it leaves
# goes to pcb_route.complete.
SCORING = {}


def jar():
    if not os.path.exists(JAR):
        sys.exit(f"pcb: Freerouting is not installed at {JAR} - run tools/setup-env.sh (it fetches {JAR_URL})")
    h = hashlib.sha256(open(JAR, "rb").read()).hexdigest()
    if h != JAR_SHA256:
        sys.exit(f"pcb: {JAR} is not the Freerouting v2.1.0 this tool was proven with (sha256 {h})")
    return JAR


def route(path, edge):
    """Route the saved board at `path` in place; `edge` its copper-to-edge clearance, mm."""
    j = jar()
    t = tempfile.mkdtemp(prefix="freeroute-")
    try:
        dsn, ses = os.path.join(t, "board.dsn"), os.path.join(t, "board.ses")
        exp = pcbnew.LoadBoard(path)
        for z in list(exp.Zones()):
            if z.GetIsRuleArea() and not (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
                exp.Delete(z)          # Delete, not Remove: a Remove from a loaded board breaks the next walk of it
        # the DSN carries no copper-to-edge clearance (the board outline is the router's
        # boundary, copper allowed to its line): a keep-out band inside every edge,
        # outline and cut-outs, as wide as the board's edge clearance
        import pcb_main
        import pcb_route
        outline = pcb_route.board_outline_with_holes(exp)
        band = outline.difference(outline.buffer(-edge, join_style=2))
        to_body = lambda g: __import__("shapely").ops.transform(lambda x, y, z=None: pcb_main.to_body(x, y), g)
        pcb_main.rule_area(exp, to_body(band.buffer(0.01)), "edge clearance (router only)", ["F.Cu", "B.Cu"])
        # a footprint's own copper shapes (a net tie's bridge between its pads) are not in
        # the DSN at all: a keep-out over each, grown by the edge clearance's margin
        import pcb
        for fp in exp.GetFootprints():
            for g in fp.GraphicalItems():
                for name, lid in (("F.Cu", pcbnew.F_Cu), ("B.Cu", pcbnew.B_Cu)):
                    if g.GetLayer() == lid:
                        ps = pcbnew.SHAPE_POLY_SET()
                        g.TransformShapeToPolygon(ps, lid, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_OUTSIDE)
                        # less its own pads and a margin round them, so the router can still reach them
                        own = __import__("shapely.ops").ops.unary_union([pcb_route.pad_geom_on(p, lid) for p in fp.Pads() if p.IsOnLayer(lid)]).buffer(edge)
                        keep = pcb.shapely_of(ps).buffer(edge).difference(own)
                        if not keep.is_empty:
                            pcb_main.rule_area(exp, to_body(keep), f"{fp.GetReference()} copper (router only)", [name])
        if not pcbnew.ExportSpecctraDSN(exp, dsn):
            sys.exit("pcb: KiCad's Specctra DSN export failed")
        r = subprocess.run(["java", f"-Duser.home={t}", "-jar", j, "-de", dsn, "-do", ses, "-mp", str(PASSES),
                            f"--router.max_passes={PASSES}", "--gui.enabled=false", "-da",
                            f"--router.job_timeout={JOB_TIMEOUT}"] + [f"--router.scoring.{k}={v}" for k, v in SCORING.items()],
                           capture_output=True, text=True, timeout=TIMEOUT_S, cwd=t)
        log = (r.stdout + r.stderr).splitlines()
        if not os.path.exists(ses):
            sys.exit("pcb: Freerouting wrote no session file:\n" + "\n".join(log[-30:]))
        board = pcbnew.LoadBoard(path)
        if not pcbnew.ImportSpecctraSES(board, ses):
            sys.exit("pcb: KiCad's Specctra SES import failed")
        # what came back from the router's own fixed wiring stays locked
        pcbnew.SaveBoard(path, board)
        tail = [l for l in log if "INFO" in l][-6:]
        for l in tail:
            print("freerouting: " + l.split("INFO", 1)[-1].strip())
        return []
    finally:
        shutil.rmtree(t, ignore_errors=True)
