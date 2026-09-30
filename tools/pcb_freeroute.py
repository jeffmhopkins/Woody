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
JOB_TIMEOUT = "00:40:00"   # Freerouting's own bound: it stops the job and still writes the session
                           # (a shell timeout's kill writes nothing); HH:MM:SS - "25m" parses as no timeout
TIMEOUT_S = 40 * 60 + 180  # the backstop, for a hung JVM
# Its costs. Its defaults give each signal layer a preferred direction and charge 2.5x
# against it, and a via 50: on a board 300 mm long and 42 across nearly every run is
# along it, so the defaults crowd everything onto layer 1 and leave layer 4 empty (the
# first main-board run: 18 connections unrouted, layer 4 all but bare). Along or across
# is nearly even here, and a via is cheap.
SCORING = {"default_undesired_direction_trace_cost": 1.2, "via_costs": 20}


def jar():
    if not os.path.exists(JAR):
        sys.exit(f"pcb: Freerouting is not installed at {JAR} - run tools/setup-env.sh (it fetches {JAR_URL})")
    h = hashlib.sha256(open(JAR, "rb").read()).hexdigest()
    if h != JAR_SHA256:
        sys.exit(f"pcb: {JAR} is not the Freerouting v2.1.0 this tool was proven with (sha256 {h})")
    return JAR


def route(path):
    """Route the saved board at `path` in place. Returns Freerouting's own last lines."""
    j = jar()
    t = tempfile.mkdtemp(prefix="freeroute-")
    try:
        dsn, ses = os.path.join(t, "board.dsn"), os.path.join(t, "board.ses")
        exp = pcbnew.LoadBoard(path)
        for z in list(exp.Zones()):
            if z.GetIsRuleArea() and not (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
                exp.Remove(z)
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
