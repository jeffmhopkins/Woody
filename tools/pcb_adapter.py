"""The UMBILICAL ADAPTER kind for tools/pcb.py - `kind: adapter` in a board's layout.yaml.

The adapter (hardware/boards/umb-adapter, ADR 0021) stands across the body, parallel to
the tail cap, so it has a frame of its own: its drawing's two axes are the body's y
(across, from the near side) and z (up), the board seen from the tail with the etherCON's
face toward the viewer. pcb x = body y + OX, pcb y = OY - body z (pcb.to_pcb, the same
arithmetic the other boards use on body x and y).

WHERE THINGS COME FROM (nothing is typed in twice):

  the netlist, footprints, references   the board's KiCad sheet (ADR 0019)
  the outline                           mechanical/export/umb-adapter.dxf
  the etherCON's axis, J-UMB's row,     mechanical/export/umb-adapter-geometry.echo
  the thickness                         (mechanical/cad/umb_adapter.scad)
  which end of J-UMB's row is pin 1     the main board's own J-UMB, pad by pad
                                        (hardware/boards/main-board/main-board.kicad_pcb)
"""
import math
import os
import re

import pcbnew
import yaml

import pcb

ROOT = pcb.ROOT
ECHO = os.path.join(ROOT, "mechanical", "export", "umb-adapter-geometry.echo")
MAIN = os.path.join(ROOT, "hardware", "boards", "main-board")


def geometry():
    """Every line of umb-adapter-geometry.echo, by kind (mechanical/cad/umb_adapter.scad says
    what each field is, beside the echo that writes it)."""
    g = {"levels": {}}
    for line in open(ECHO):
        m = re.match(r'ECHO: "PCB", "umb", "(\w+)", (.*)', line)
        if not m:
            continue
        rest = [t.strip().strip('"') for t in m.group(2).split(",")]
        f = [float(v) if re.match(r"^-?[\d.]+(e-?\d+)?$", v) else v for v in rest[1:]]
        if m.group(1) == "board":
            g["thickness"] = f[0]
        elif m.group(1) == "axis":
            g["axis"] = (f[0], f[1], f[2])              # across, up, the connector's turn
        elif m.group(1) == "row":
            g["row"] = ((f[0], f[1]), (f[2], f[3]), f[4])   # the near end pin, the far end pin, the pitch
        elif m.group(1) == "rear":
            g["rear_x"] = f[0]
        elif m.group(1) == "level":
            g["levels"][rest[0]] = f[0]
    return g


def to_own(px, py):
    """pcb mm -> the adapter's frame (across the body, up)."""
    return (px - pcb.OX, pcb.OY - py)


SKT_PAD_OFF = 1.65   # KiCad's PinSocket_1x08_P2.54mm_Vertical_SMD: pad centres from the row


def pad_own(p):
    q = p.GetPosition()
    return to_own(pcbnew.ToMM(q.x), pcbnew.ToMM(q.y))


def main_board_row():
    """The main board's J-UMB as it is laid out: {pin: (body x, body y, net)} - the tails
    the same header's posts continue. The adapter's J-UMB pad k is the post of this pin k."""
    comps, _ = pcb.sheet_netlist(os.path.join(MAIN, "main-board.kicad_sch"))
    ref = pcb.ref_of(comps, "J-UMB")
    board = pcbnew.LoadBoard(os.path.join(MAIN, "main-board.kicad_pcb"))
    fp = next(f for f in board.GetFootprints() if f.GetReference() == ref)
    out = {}
    for p in fp.Pads():
        q = p.GetPosition()
        out[p.GetNumber()] = (pcbnew.ToMM(q.x) - pcb.OX, pcb.OY - pcbnew.ToMM(q.y), p.GetNetname().lstrip("/"))
    return ref, out


def check_cad(board, lay, comps):
    """The body CAD and the main board still agree with the adapter: thickness, outline,
    the etherCON on the body CAD's axis on the face toward the tail, J-UMB's pads on the
    row the body CAD gives, on the rear face, and EACH PAD WHERE THE MAIN BOARD'S SAME
    PIN STANDS ACROSS THE BODY, on the same conductor - the header is one part in two
    boards, and a row numbered from the other end swaps every conductor of the umbilical
    side for side with no check on either board failing."""
    bad = []
    geo = geometry()
    body = yaml.safe_load(open(os.path.join(ROOT, "config", "body.yaml")))
    t_cfg = float(body["boards"]["umb_adapter_t"]["value"])
    t_pcb = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
    if abs(geo.get("thickness", -1) - t_cfg) > 1e-6:
        bad.append(f"error: [cad] umb-adapter-geometry.echo says the adapter is {geo.get('thickness')} mm, config/body.yaml boards.umb_adapter_t {t_cfg:g} - run: python3 tools/cad.py build")
    if abs(t_pcb - t_cfg) > 1e-6:
        bad.append(f"error: [cad] the board is {t_pcb:g} mm thick, the body CAD's adapter {t_cfg:g} (boards.umb_adapter_t)")
    ol = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(ol):
        bad.append("error: [cad] the Edge.Cuts outline is not closed")
    else:
        from shapely.geometry import MultiLineString
        segs = pcb.dxf_segments(os.path.join(ROOT, "mechanical", "export", lay["outline"]))
        cad = MultiLineString([(pcb.to_pcb(*a), pcb.to_pcb(*b)) for a, b in segs])
        off = pcb.shapely_of(ol).boundary.hausdorff_distance(cad)
        if off > 0.05:
            bad.append(f"error: [cad] the Edge.Cuts outline is up to {off:.2f} mm from the body CAD's (mechanical/export/{lay['outline']})")
    fp_of = {f.GetReference(): f for f in board.GetFootprints()}
    # the etherCON: its footprint's origin is the connector's axis, latch up, seen from the panel
    j1 = fp_of[pcb.ref_of(comps, "J-UMBILICAL-INST")]
    q = j1.GetPosition()
    got = to_own(pcbnew.ToMM(q.x), pcbnew.ToMM(q.y))
    ax, az, turn = geo["axis"]
    if turn:
        bad.append("error: [cad] the body CAD turns the etherCON (ethercon.rotated), which puts its contacts across J-UMB's row - this board is laid out for latch up")
    if math.hypot(got[0] - ax, got[1] - az) > 0.02 or j1.IsFlipped() or abs(j1.GetOrientationDegrees()) > 0.01:
        bad.append(f"error: [cad] {j1.GetReference()} (the etherCON) stands at {tuple(round(v, 2) for v in got)}, turned {j1.GetOrientationDegrees():g}"
                   f"{', on the REAR face' if j1.IsFlipped() else ''}; the body CAD puts its axis at ({ax}, {az}), latch up, on the face toward the tail")
    # J-UMB's posts: on the rear face, on the body CAD's row, each where the main board holds that pin
    j2 = fp_of[pcb.ref_of(comps, "J-UMB-SKT")]
    (y0, z0), (y1, z1), pitch = geo["row"]
    if not j2.IsFlipped():
        bad.append(f"error: [cad] {j2.GetReference()} (J-UMB-SKT) is on the face toward the tail; the socket stands on the REAR face")
    mref, row = main_board_row()
    for p in j2.Pads():
        n = p.GetNumber()
        py, pz = pad_own(p)
        # a surface-mount socket's pads stand either side of its row, turn about: the row is midway
        if abs(abs(pz - z0) - SKT_PAD_OFF) > 0.02 or not (y0 - 0.02 <= py <= y1 + 0.02):
            bad.append(f"error: [cad] {j2.GetReference()} pad {n} is at ({py:.2f}, {pz:.2f}); the body CAD's J-UMB row runs across {y0:g}..{y1:g} at {z0:g} up, the socket's pads {SKT_PAD_OFF} either side of it")
        if n not in row:
            bad.append(f"error: [cad] {j2.GetReference()} pad {n}: the main board's {mref} has no such pin")
            continue
        mx, my, mnet = row[n]
        if abs(py - my) > 0.02:
            bad.append(f"error: [cad] {j2.GetReference()} pad {n} stands {py:.2f} across the body; the main board's {mref} pin {n}, the same post, stands at {my:.2f}")
        if p.GetNetname().lstrip("/") != mnet:
            bad.append(f"error: [cad] {j2.GetReference()} pad {n} is {p.GetNetname()}; the main board's {mref} pin {n} is {mnet}")
    # the header's insulator ends on this board's rear face (ADR 0021): the main board's pad
    # row, the row's distance to the insulator's back and the insulator's depth say where
    back = (float(body["boards"]["umb_joint_row_back"]["value"]) + float(body["boards"]["umb_joint_d"]["value"])
            + float(body["boards"]["umb_socket_d"]["value"]))
    mx = next(iter(row.values()))[0]
    if abs(mx + back - geo["rear_x"]) > 0.02:
        bad.append(f"error: [cad] the main board's {mref} pad row stands at {mx:.2f} along the body, so its insulator's face and the socket (boards.umb_socket_d) end at {mx + back:.2f}; "
                   f"the body CAD puts the adapter's rear face at {geo['rear_x']:g}")
    return bad
