"""Small constructed boards for the cluster packer and the centreline router (issue #46):
built in memory from synthetic footprints - no footprint library, no board under
hardware/ - and saved only where the caller says.

Footprints (all on the front unless said; courtyard on F.CrtYd):
  passive(ref, a, b)          0805: two 1.0 x 1.3 pads 1.9 apart, courtyard 3.4 x 1.9
  soic(ref, n, nets)          SOIC-n narrow: 1.95 x 0.6 pads at x +-2.475, 1.27 pitch
  header(ref, nets)           2 x 5, 1.27 mm SMD header: 2.4 x 0.74 pads at x +-1.95
  switch(ref, leg, gnd)       a key switch from the parts side: two plated pins and an
                              unplated centre pole; courtyard only round the three holes,
                              because parts sit under a switch body on the other face
  jack(ref, nets)             three 1.5 x 1.5 SMD pads in a row, 2.5 mm pitch
  hole(ref)                   2.7 mm unplated mount hole, courtyard 3.5 mm round

Boards:
  minikey()   a three-key cousin of key-board-lh: switches, header, register, mounts
              placed by the "body CAD" (locked); twelve passives dumped in a heap
  island()    a cousin of the main board's MIDI corner: a jack beside an analog island
              with its moat, a mount hole, and passives dropped on the moat and the
              island; an island cluster (U2 and its filter) dumped outside the island
"""
import pcbnew

MM = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def new_board(w, h, layers=2):
    b = pcbnew.BOARD()
    b.SetCopperLayerCount(layers)
    for (x0, y0), (x1, y1) in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(V(x0, y0))
        s.SetEnd(V(x1, y1))
        s.SetWidth(MM(0.1))
        b.Add(s)
    ds = b.GetDesignSettings()
    ds.m_MinClearance = MM(0.2)
    ds.m_TrackMinWidth = MM(0.2)
    ds.m_ViasMinSize = MM(0.6)
    ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.3)
    ds.m_HoleClearance = MM(0.25)
    ds.m_HoleToHoleMin = MM(0.25)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(MM(0.2))
    nc.SetTrackWidth(MM(0.25))
    nc.SetViaDiameter(MM(0.7))
    nc.SetViaDrill(MM(0.3))
    return b


def net(b, name):
    n = b.FindNet(name)
    if n is None or n.GetNetCode() <= 0 and name:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
    return n


def _fp(b, ref, value=""):
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference(ref)
    fp.SetValue(value or ref)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.SetFPID(pcbnew.LIB_ID("woody_test", value or ref))
    return fp


def _smd(b, fp, num, x, y, w, h, n, shape=pcbnew.PAD_SHAPE_RECT):
    p = pcbnew.PAD(fp)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetShape(shape)
    p.SetSize(V(w, h))
    ls = pcbnew.LSET()
    for l in (pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste):
        ls.AddLayer(l)
    p.SetLayerSet(ls)
    p.SetNumber(str(num))
    p.SetFPRelativePosition(V(x, y))
    fp.Add(p)
    if n:
        p.SetNet(net(b, n))
    return p


def _tht(b, fp, num, x, y, dia, drill, n):
    p = pcbnew.PAD(fp)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(V(dia, dia))
    p.SetDrillSize(V(drill, drill))
    p.SetLayerSet(pcbnew.PAD.PTHMask())
    p.SetNumber(str(num))
    p.SetFPRelativePosition(V(x, y))
    fp.Add(p)
    if n:
        p.SetNet(net(b, n))
    return p


def _npth(b, fp, x, y, dia):
    p = pcbnew.PAD(fp)
    p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(V(dia, dia))
    p.SetDrillSize(V(dia, dia))
    p.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
    p.SetNumber("")
    p.SetFPRelativePosition(V(x, y))
    fp.Add(p)
    return p


def _court_rect(fp, w, h):
    for (x0, y0), (x1, y1) in (((-w / 2, -h / 2), (w / 2, -h / 2)), ((w / 2, -h / 2), (w / 2, h / 2)),
                               ((w / 2, h / 2), (-w / 2, h / 2)), ((-w / 2, h / 2), (-w / 2, -h / 2))):
        s = pcbnew.PCB_SHAPE(fp)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.F_CrtYd)
        s.SetStart(V(x0, y0))
        s.SetEnd(V(x1, y1))
        s.SetWidth(MM(0.05))
        fp.Add(s)


def _court_circle(fp, x, y, r):
    s = pcbnew.PCB_SHAPE(fp)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetLayer(pcbnew.F_CrtYd)
    s.SetCenter(V(x, y))
    s.SetEnd(V(x + r, y))
    s.SetWidth(MM(0.05))
    fp.Add(s)


def _place(b, fp, x, y, rot=0.0, locked=False):
    b.Add(fp)
    fp.SetPosition(V(x, y))
    if rot:
        fp.SetOrientationDegrees(rot)
    fp.SetLocked(locked)
    return fp


def passive(b, ref, a, c, x, y, rot=0.0, value="0805", locked=False):
    fp = _fp(b, ref, value)
    _smd(b, fp, 1, -0.95, 0, 1.0, 1.3, a)
    _smd(b, fp, 2, 0.95, 0, 1.0, 1.3, c)
    _court_rect(fp, 3.4, 1.9)
    return _place(b, fp, x, y, rot, locked)


def soic(b, ref, nets, x, y, rot=0.0, locked=False):
    """nets: list, pin 1 first; pins down the left then up the right."""
    n = len(nets)
    fp = _fp(b, ref, f"SOIC-{n}")
    half = n // 2
    for k in range(n):
        if k < half:
            px, py = -2.475, (k - (half - 1) / 2) * 1.27
        else:
            px, py = 2.475, ((n - 1 - k) - (half - 1) / 2) * 1.27
        _smd(b, fp, k + 1, px, py, 1.95, 0.6, nets[k])
    _court_rect(fp, 7.4, half * 1.27 + 1.0)
    return _place(b, fp, x, y, rot, locked)


def header(b, ref, nets, x, y, rot=0.0, locked=False):
    fp = _fp(b, ref, "HDR-2x5-1.27")
    for k, n in enumerate(nets):
        row = k // 2
        side = -1 if k % 2 == 0 else 1
        _smd(b, fp, k + 1, side * 1.95, (row - 2) * 1.27, 2.4, 0.74, n)
    _court_rect(fp, 6.6, 7.4)
    return _place(b, fp, x, y, rot, locked)


def switch(b, ref, leg, gnd, x, y, locked=True):
    fp = _fp(b, ref, "KEYSWITCH")
    _tht(b, fp, 1, -4.4, -4.7, 2.2, 1.3, leg)
    _tht(b, fp, 2, 2.6, -5.75, 2.2, 1.3, gnd)
    _npth(b, fp, 0, 0, 3.0)
    for (cx, cy, r) in ((-4.4, -4.7, 1.35), (2.6, -5.75, 1.35), (0, 0, 1.75)):
        _court_circle(fp, cx, cy, r)
    return _place(b, fp, x, y, 0, locked)


def jack(b, ref, nets, x, y, rot=0.0, locked=True):
    fp = _fp(b, ref, "JACK-3")
    for k, n in enumerate(nets):
        _smd(b, fp, k + 1, 0, (k - 1) * 2.5, 1.5, 1.5, n)
    _court_rect(fp, 3.0, 8.0)
    return _place(b, fp, x, y, rot, locked)


def hole(b, ref, x, y, dia=2.7):
    fp = _fp(b, ref, "MOUNT")
    _npth(b, fp, 0, 0, dia)
    _court_circle(fp, 0, 0, dia / 2 + 0.8)
    return _place(b, fp, x, y, 0, True)


def zone(b, netname, layer, pts, rule_area=False, no_tracks=False, no_vias=False, no_footprints=False, layers=None,
         holes=(), no_pour=True):
    z = pcbnew.ZONE(b)
    if rule_area:
        z.SetIsRuleArea(True)
        ls = pcbnew.LSET()
        for l in (layers or [layer]):
            ls.AddLayer(l)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(no_tracks)
        z.SetDoNotAllowVias(no_vias)
        z.SetDoNotAllowCopperPour(no_pour)
        z.SetDoNotAllowFootprints(no_footprints)
        z.SetDoNotAllowPads(False)
    else:
        z.SetLayer(layer)
        z.SetNet(net(b, netname))
        z.SetLocalClearance(MM(0.2))
        z.SetMinThickness(MM(0.25))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(x), MM(y))
    for k, h in enumerate(holes):
        ol.NewHole()
        for x, y in h:
            ol.Append(MM(x), MM(y), -1, k)
    b.Add(z)
    return z


# ------------------------------------------------------------------ the boards

# The 74HC165 as key-board-lh uses it: inputs E..H (pins 3-6) face the keys
HC165 = ["SHLD", "SCK", "KEY1", "KEY2", "KEY3", "FREE", "", "GND",
         "QH", "SER", "V3V3", "V3V3", "V3V3", "V3V3", "GND", "V3V3"]

MINIKEY = {
    "size": (64.0, 36.0),
    "switches": {"SW1": (14.0, 12.0), "SW2": (32.0, 12.0), "SW3": (50.0, 12.0)},
    "header": ("J1", (55.0, 26.0)),
    "register": ("U1", (32.0, 27.5, 90.0)),
    "holes": {"H1": (3.5, 3.5), "H2": (60.5, 3.5), "H3": (3.5, 32.5), "H4": (60.5, 32.5)},
    # each key's network: series R (switch leg -> KEY), pull-up R (KEY -> 3V3), C (KEY -> GND)
    "keys": {1: ("R1", "R2", "C1"), 2: ("R3", "R4", "C2"), 3: ("R5", "R6", "C3")},
    "others": {"C6": ("V3V3", "GND"), "R11": ("FREE", "V3V3"), "C7": ("V3V3", "GND")},
    "heap": (8.0, 27.0),
}


def minikey(heap=True):
    """The three-key board. Body-owned (locked): SW1-3, J1, H1-4. U1 is placed by us (an
    anchor, locked so the router keeps it). With `heap`, every passive is dumped
    on one spot - overlapping - for the packer to seat."""
    S = MINIKEY
    b = new_board(*S["size"])
    for k, (ref, (x, y)) in enumerate(S["switches"].items(), 1):
        switch(b, ref, f"SWL{k}", "GND", x, y)
    ref, (x, y) = S["header"]
    header(b, ref, ["V3V3", "GND", "SCK", "GND", "SHLD", "GND", "QH", "GND", "SER", "GND"], x, y, locked=True)
    ref, (x, y, rot) = S["register"]
    soic(b, ref, HC165, x, y, rot, locked=True)
    for ref, (x, y) in S["holes"].items():
        hole(b, ref, x, y)
    hx, hy = S["heap"]
    k = 0
    for key, (rs, rp, c) in S["keys"].items():
        passive(b, rs, f"SWL{key}", f"KEY{key}", hx + (k % 4) * 0.5, hy, value="R")
        passive(b, rp, f"KEY{key}", "V3V3", hx + (k % 4) * 0.5, hy, value="R")
        passive(b, c, f"KEY{key}", "GND", hx + (k % 4) * 0.5, hy, value="C")
        k += 1
    for ref, (a, c) in S["others"].items():
        passive(b, ref, a, c, hx, hy, value=ref[0])
    return b


ISLAND = {
    "size": (56.0, 34.0),
    # the analog island (AGND on B.Cu) and its moat keep-out ring
    "island": [(6.0, 5.0), (26.0, 5.0), (26.0, 13.0), (20.0, 13.0), (20.0, 21.0), (26.0, 21.0), (26.0, 29.0), (6.0, 29.0)],
    "moat": 0.6,
    "jack": ("J7", (30.0, 17.0)),
    "hole": ("H11", (23.0, 17.0)),
    "uart": ("U3", (46.0, 17.0, 0.0)),
    "adc": ("U2", (13.0, 17.0, 0.0)),
}


def island(bad=True):
    """J7 (body-owned) beside an analog island shaped like a U round H11. R50/R51 (series)
    and FB3/FB4 (ferrites) join J7 to U3. With `bad`, they are dropped where the recorded
    bug had them: on the moat and inside the island's mouth. U2 (the island's ADC) is
    the anchor of an island cluster - R10, C10, C11 on AGND nets - dumped outside it."""
    S = ISLAND
    b = new_board(*S["size"])
    isl = S["island"]
    zone(b, "AGND", pcbnew.B_Cu, isl)
    from shapely.geometry import Polygon
    P = Polygon(isl)
    ring = P.buffer(S["moat"], join_style="mitre").difference(P)
    # the moat keep-out: no footprint over it on either face, and no track on the plane's layer
    # (signals cross it on the front, as the main board's do at its tie)
    for poly in ([ring] if ring.geom_type == "Polygon" else list(ring.geoms)):
        holes = [list(r.coords)[:-1] for r in poly.interiors]
        zone(b, "", pcbnew.B_Cu, list(poly.exterior.coords)[:-1], rule_area=True, no_footprints=True,
             layers=[pcbnew.F_Cu, pcbnew.B_Cu], holes=holes)
        zone(b, "", pcbnew.B_Cu, list(poly.exterior.coords)[:-1], rule_area=True, no_tracks=True, no_vias=True,
             layers=[pcbnew.B_Cu], holes=holes)
    ref, (x, y) = S["jack"]
    jack(b, ref, ["MIDI_TIP", "MIDI_RING", "GND"], x, y)
    ref, (x, y) = S["hole"]
    hole(b, ref, x, y)
    ref, (x, y, r) = S["uart"]
    soic(b, ref, ["TX_DRV", "RX_DRV", "", "GND", "V3V3", "", "", "V3V3"], x, y, r, locked=True)
    ref, (x, y, r) = S["adc"]
    soic(b, ref, ["AIN", "", "", "AGND", "", "", "", "AREF"], x, y, r, locked=True)
    for h, (hx, hy) in {"H1": (3.0, 3.0), "H2": (53.0, 3.0), "H3": (3.0, 31.0), "H4": (53.0, 31.0)}.items():
        hole(b, h, hx, hy)
    if bad:
        # the recorded fault's shape: the series parts on the moat, and the ferrites on the far
        # side of the island, so their connections to them must go the long way round it
        passive(b, "R50", "MIDI_TIP", "MIDI_T_R", 26.0, 10.5, 90, "R")
        passive(b, "R51", "MIDI_RING", "MIDI_R_R", 26.0, 24.0, 90, "R")
        passive(b, "FB3", "MIDI_T_R", "TX_DRV", 3.2, 10.0, 90, "FB")
        passive(b, "FB4", "MIDI_R_R", "RX_DRV", 3.2, 24.0, 90, "FB")
        passive(b, "R10", "AIN_RAW", "AIN", 34.0, 30.0, 0, "R")
        passive(b, "C10", "AIN", "AGND", 37.0, 30.0, 0, "C")
        passive(b, "C11", "AREF", "AGND", 40.0, 30.0, 0, "C")
    # AIN_RAW comes in at a test point at the island's far edge
    tp = _fp(b, "TP1", "TP")
    _smd(b, tp, 1, 0, 0, 1.2, 1.2, "AIN_RAW", pcbnew.PAD_SHAPE_CIRCLE)
    _place(b, tp, 9.0, 8.0, 0, True)
    return b


def tp(b, ref, n, x, y, w=1.0, h=1.0, back=False, locked=True):
    """A bare SMD pad (a test point) on the front, or the back with `back`."""
    fp = _fp(b, ref, "TP")
    p = _smd(b, fp, 1, 0, 0, w, h, n)
    if back:
        ls = pcbnew.LSET()
        for l in (pcbnew.B_Cu, pcbnew.B_Mask, pcbnew.B_Paste):
            ls.AddLayer(l)
        p.SetLayerSet(ls)
    return _place(b, fp, x, y, 0, locked)


def keepout(b, x0, y0, x1, y1, layers=("F",), tracks=True, vias=True, footprints=False, pour=False):
    L = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    return zone(b, "", L[layers[0]], [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], rule_area=True, no_tracks=tracks,
                no_vias=vias, no_footprints=footprints, layers=[L[l] for l in layers], no_pour=not pour)


def track(b, n, pts, layer="F", w=0.25, locked=False):
    L = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}[layer]
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(V(x0, y0))
        t.SetEnd(V(x1, y1))
        t.SetWidth(MM(w))
        t.SetLayer(L)
        t.SetNet(net(b, n))
        t.SetLocked(locked)
        b.Add(t)
        out.append(t)
    return out


def via(b, n, x, y, d=0.7, drill=0.3, locked=False):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(x, y))
    v.SetWidth(MM(d))
    v.SetDrill(MM(drill))
    v.SetNet(net(b, n))
    v.SetLocked(locked)
    b.Add(v)
    return v
