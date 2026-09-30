#!/usr/bin/env python3
"""Schematic sheets generated from the netlists: netlist.yaml in, KiCad out.

    python3 tools/sch.py build hardware/carrier/led-strip-drive   # write the sheet, check it, render it
    python3 tools/sch.py check hardware/carrier/led-strip-drive   # exit 1 if the sheet or render is stale

WHAT IS THE SOURCE. `netlist.yaml` stays AUTHORITATIVE for connectivity, as
it is for the whole of hardware/ (CLAUDE.md). The sheet is a representation of
it, exactly as the ASCII drawing is. The only new input is `schematic.yaml`
beside it: which KiCad symbol draws each part, which pin number each named pin
is (a package fact, with provenance), and where things sit on the sheet.
Placement is data, like config/body.yaml is for the body - never hand-edit
the .kicad_sch.

WHAT IS GENERATED, and must never be edited by hand:
    <circuit>/<name>.kicad_sch     the sheet (KiCad 7 format; opens in KiCad 7, 8, 9)
    <circuit>/<name>.sch.png       its render, fingerprint in the title block

WHY IT CHECKS ITSELF. A drawing that disagrees with its netlist is this
repository's named failure in a new medium. So `build` does not trust the
generator: it asks KiCad for the netlist of the sheet it just wrote
(`kicad-cli sch export netlist`) and compares every net, pin by pin, with
netlist.yaml. A wire drawn to the wrong point, a label on the wrong stub or a
net that is split or merged fails the build. What it CANNOT prove is the
pin-number map: the wires go wherever the map says, so a wrong map draws a
consistent wrong sheet. The map is a package fact, cited to its datasheet in
schematic.yaml; the one check possible here is that pins the library NAMES
(VCC, GND...) carry the same name in netlist.yaml. KiCad's own ERC runs on the
sheet too (kicad-cli 8 or later; KiCad 7's has none, and a small pin-type
check stands in and says so).

NEEDS KiCad 9 (the sheets are written in its format) and its symbol library:
`sudo bash tools/setup-env.sh` installs it, and docs/reference/tooling.md is
the user's guide. By hand, on Ubuntu 24.04, from the KiCad project's archive:
    key=$(curl -s https://api.launchpad.net/1.0/~kicad/+archive/ubuntu/kicad-9.0-releases \
          | python3 -c "import sys,json;print(json.load(sys.stdin)['signing_key_fingerprint'])")
    curl -s "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x$key" | gpg --dearmor \
          > /etc/apt/trusted.gpg.d/kicad-9.gpg
    echo "deb https://ppa.launchpadcontent.net/kicad/kicad-9.0-releases/ubuntu noble main" \
          > /etc/apt/sources.list.d/kicad-9.list
    apt-get update && apt-get install -y --no-install-recommends kicad kicad-symbols

HOW PINS CONNECT. A pin named in a `wires` polyline is joined by that wire. A
pin that is not gets a short stub and a label with its net name (a power
symbol if the net is in `power`, a no-connect flag if it is the only pin on
an `external_endpoints` net). So every connection is either drawn or named,
and never both inconsistently - KiCad's netlist is the proof.

THE FINGERPRINT is a hash over the git blob ids of the inputs (netlist.yaml,
schematic.yaml, this tool, and the KiCad symbol libraries used), stamped into
the title block and recorded in the sheet. `check` recomputes it.
"""
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import uuid

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYMDIR = "/usr/share/kicad/symbols"
GRID = 1.27
STUB = 2.54
NS = uuid.UUID("7d1e0a3c-5b1e-4c55-9d0e-6f0c2a1b9e11")


# ---------------------------------------------------------------- s-expressions

def tokenize(s):
    return re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', s)


class Str(str):
    """A quoted string in an s-expression, so it is written back quoted."""


def parse(s):
    toks = tokenize(s)
    stack = [[]]
    for t in toks:
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(Str(t[1:-1].replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\"))
                             if t.startswith('"') else t)
    return stack[0]


def dump(node, ind="    "):
    if isinstance(node, Str):
        return q(node)
    if not isinstance(node, list):
        return node
    head = [c for c in node if not isinstance(c, list)]
    kids = [c for c in node if isinstance(c, list)]
    if not kids:
        return "(" + " ".join(dump(c) for c in node) + ")"
    # atoms stay on the opening line: "(symbol "NAME"" is matched as text later
    inner = "\n".join(ind + "  " + dump(c, ind + "  ") for c in kids)
    return "(" + " ".join(dump(c) for c in head) + "\n" + inner + ")"


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def sym_path(lib):
    """KiCad's own libraries, or this project's (`woody`, hardware/lib/woody.kicad_sym) for a
    part KiCad does not draw - hardware/lib/README.md."""
    if lib == "woody":
        return os.path.join(ROOT, "hardware", "lib", "woody.kicad_sym")
    return os.path.join(SYMDIR, lib + ".kicad_sym")


def lib_symbol_text(lib, name):
    """The raw text of one symbol in a .kicad_sym, by bracket matching."""
    path = sym_path(lib)
    text = open(path).read()
    m = re.search(r'\n(?:\t|  )\(symbol "%s"\s' % re.escape(name), text)
    if not m:
        sys.exit(f"sch: symbol {lib}:{name} not in {path}")
    i, depth = text.index("(", m.start()), 0
    for j in range(i, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                body = text[i:j + 1]
                node = parse(body)[0]
                ext = find(node, "extends")
                if ext:
                    # A derived symbol: the parent's graphics and pins, the child's fields.
                    parent = parse(lib_symbol_text(lib, ext[0][1])[0])[0]
                    pname = parent[1]
                    kids = {c[1]: c for c in find(node, "property")}
                    flat = [node[0], Str(name)]
                    for c in parent[2:]:
                        if isinstance(c, list) and c[0] == "property" and c[1] in kids:
                            flat.append(kids.pop(c[1]))
                        elif isinstance(c, list) and c[0] == "symbol":
                            flat.append([c[0], Str(c[1].replace(pname + "_", name + "_", 1))] + c[2:])
                        else:
                            flat.append(c)
                    flat[2:2] = list(kids.values())
                    body = dump(flat)
                return body, path
    sys.exit(f"sch: unbalanced symbol {lib}:{name}")


def lib_pins(symtext):
    """{(unit, number): (x, y, angle, type, name)} in library coordinates (y up)."""
    top = parse(symtext)[0]
    name = top[1]
    out = {}
    for sub in find(top, "symbol"):
        m = re.fullmatch(re.escape(name) + r"_(\d+)_(\d+)", sub[1])
        unit = int(m.group(1))
        for p in find(sub, "pin"):
            at = find(p, "at")[0]
            num = find(p, "number")[0][1]
            pname = find(p, "name")[0][1]
            out[(unit, num)] = (float(at[1]), float(at[2]), float(at[3]), p[1], pname)
    return out


def lib_props(symtext):
    top = parse(symtext)[0]
    out = {}
    for p in find(top, "property"):
        at = find(p, "at")[0]
        out[p[1]] = (float(at[1]), float(at[2]), float(at[3]))
    return out


# ---------------------------------------------------------------- geometry

def rot(x, y, r):
    r = r % 360
    return {0: (x, y), 90: (-y, x), 180: (-x, -y), 270: (y, -x)}[r]


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def place(sym_at, lx, ly):
    """Library point -> sheet point for a symbol at (X, Y, rotation)."""
    X, Y, r = sym_at
    x, y = rot(lx, ly, r)
    return (snap(X + x), snap(Y - y))


def outward(angle, r):
    """Unit vector on the sheet pointing away from the body at a pin."""
    a = (angle + 180 + r) % 360
    return {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[a]


def u(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


# ---------------------------------------------------------------- the build

def git_blob(path):
    try:
        return subprocess.run(["git", "hash-object", path], capture_output=True, text=True, check=True,
                              cwd=ROOT).stdout.strip()
    except subprocess.CalledProcessError:
        return hashlib.sha1(open(path, "rb").read()).hexdigest()


def load(circuit_dir):
    d = os.path.join(ROOT, circuit_dir)
    lay = yaml.safe_load(open(os.path.join(d, "schematic.yaml")))
    net = yaml.safe_load(open(os.path.join(d, lay.get("netlist", "netlist.yaml"))))
    return d, net, expand(lay)


def fingerprint(d, lay):
    files = [os.path.join(d, lay.get("netlist", "netlist.yaml")), os.path.join(d, "schematic.yaml"),
             os.path.abspath(__file__)]
    libs = sorted({c["symbol"].split(":")[0] for c in lay["components"].values()} | {"power"})
    files += [sym_path(l) for l in libs]
    for f in files:
        if not os.path.exists(f):
            sys.exit(f"sch: {f} missing - install KiCad and its symbols (apt-get install kicad kicad-symbols)")
    h = hashlib.sha1()
    for f in files:
        h.update((os.path.basename(f) + git_blob(f)).encode())
    return h.hexdigest()[:12]


def expand(lay):
    """`repeat` blocks: one placement written once, laid down per instance. Every string
    has {k} replaced by the instance; every [x, y] is relative to at + i * step."""
    lay = dict(lay)
    comps = dict(lay.get("components", {}))
    wires, labels = list(lay.get("wires", [])), list(lay.get("labels", []))
    for blk in lay.get("repeat", []):
        for i, k in enumerate(blk["for"]):
            ox = blk["at"][0] + i * blk["step"][0]
            oy = blk["at"][1] + i * blk["step"][1]
            sub = lambda t: t.replace("{k}", str(k))
            for ref, c in blk.get("components", {}).items():
                c = dict(c)
                c["at"] = [ox + c["at"][0], oy + c["at"][1]] + list(c["at"][2:])
                comps[sub(ref)] = c
            for poly in blk.get("wires", []):
                wires.append([sub(p) if isinstance(p, str) else [ox + p[0], oy + p[1]] for p in poly])
            for lb in blk.get("labels", []):
                labels.append(dict(lb, net=sub(lb["net"]), at=[ox + lb["at"][0], oy + lb["at"][1]]))
    lay["components"], lay["wires"], lay["labels"] = comps, wires, labels
    return lay


def pin_ref(s):
    ref, pin = s.rsplit(".", 1)
    return ref, pin


class Sheet:
    def __init__(self, d, net, lay):
        self.d, self.net, self.lay = d, net, lay
        self.name = lay.get("name", os.path.basename(d))
        self.items = []
        self.libs = {}
        self.pinpos = {}      # "REF.pin" -> (x, y, outward dx, dy, type)
        self.pinnum = {}      # "REF.pin" -> (ref, number)
        self.pinname = {}     # "REF.pin" -> the library's name for that pin
        self.wired = set()
        self.power = lay.get("power", {})
        self.n_power = 0
        self.ports_in = set(net.get("ports", {}))
        self.hier = bool(lay.get("hierarchical"))   # a SOURCE circuit sheet: ports are hierarchical labels
        self.extra_inst = {}                         # ref -> [(project, path, ref)] for boards using this sheet

    def lib(self, lib_id):
        if lib_id not in self.libs:
            lib, name = lib_id.split(":")
            text, _ = lib_symbol_text(lib, name)
            self.libs[lib_id] = (text, lib_pins(text), lib_props(text))
        return self.libs[lib_id]

    # -- symbols
    def text_spots(self, lib_id, at, unit, over=None):
        """Where the Reference and Value go: just outside the unit, clear of its pins.
        A two-pin part standing up gets them to its right; lying down, above and below;
        a gate, above it. Anything else keeps the library's own spots. `ref_at` and
        `value_at` in schematic.yaml ([dx, dy] from the unit) override."""
        text, pins, props = self.lib(lib_id)
        pts = [place(at, lx, ly) for (un, _), (lx, ly, *_r) in pins.items() if un in (unit, 0)]
        X, Y = at[0], at[1]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        spots = {}
        if len(pts) == 2 and xs[0] == xs[1]:
            spots = {"Reference": (X + 2.54, Y - 1.27, "left"), "Value": (X + 2.54, Y + 1.27, "left")}
        elif len(pts) == 2 and ys[0] == ys[1]:
            spots = {"Reference": (X, Y - 2.54, None), "Value": (X, Y + 2.54, None)}
        elif len(pts) <= 3 and not lib_id.startswith("power:"):
            top = min(ys + [Y - 3.81])
            spots = {"Reference": (X, top - 3.81, None), "Value": (X, top - 1.27, None)}
        for k, key in (("Reference", "ref_at"), ("Value", "value_at")):
            if over and key in over:
                spots[k] = (X + over[key][0], Y + over[key][1], over.get(key + "_justify"))
        return spots

    def symbol(self, lib_id, ref, value, at, unit, key, fields=None, hide_ref=False, footprint="", over=None):
        text, pins, props = self.lib(lib_id)
        X, Y, r = at
        spots = self.text_spots(lib_id, at, unit, over)
        out = [f"  (symbol (lib_id {q(lib_id)}) (at {X} {Y} {r}) (unit {unit})",
               "    (in_bom yes) (on_board yes) (dnp no)",
               f"    (uuid {u(self.name, 'sym', key)})"]
        for pname, pval, hide in (("Reference", ref, hide_ref), ("Value", value, False),
                                  ("Footprint", footprint, True), ("Datasheet", "", True)):
            if pname in spots:
                px, py, just = spots[pname]
                px, py = snap(px), snap(py)
            else:
                lx, ly, _ = props.get(pname, (0, 0, 0))
                (px, py), just = place(at, lx, ly), None
            if just and pname in spots and r % 360 != 0:
                # KiCad reads a field's justification in the ROTATED symbol's frame
                just = {"left": "right", "right": "left"}[just]
            j = f" (justify {just})" if just else ""
            eff = "(effects (font (size 1.27 1.27))" + j + (" hide" if hide else "") + ")"
            # KiCad stores a field's angle as the symbol's rotation plus the field's own;
            # keep every field reading horizontally whatever the symbol's rotation
            ang = r if pname in spots else 0
            out.append(f"    (property {q(pname)} {q(pval)} (at {px} {py} {ang}) {eff})")
        for k, v in (fields or {}).items():
            out.append(f"    (property {q(k)} {q(v)} (at {X} {Y} 0) (effects (font (size 1.27 1.27)) hide))")
        for (un, num) in sorted(pins):
            if un in (unit, 0):
                out.append(f"    (pin {q(num)} (uuid {u(self.name, 'pin', key, num)}))")
        inst = [f"(project {q(self.name)} (path \"/{u(self.name, 'root')}\" (reference {q(ref)}) (unit {unit})))"]
        for proj, path, nref in self.extra_inst.get(ref, []):
            inst.append(f"(project {q(proj)} (path {q(path)} (reference {q(nref)}) (unit {unit})))")
        out.append("    (instances " + " ".join(inst) + ")")
        out.append("  )")
        self.items.append("\n".join(out))

    def wire(self, a, b):
        if a == b:
            return
        self.items.append(f"  (wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default))"
                          f" (uuid {u(self.name, 'wire', a, b)}))")
        self.segments.append((a, b))

    def label(self, netname, at, d, glob=False, hier=None):
        # d is the outward direction of the stub the label sits at the end of
        ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[d]
        just = "left" if ang in (0, 90) else "right"
        if hier is not None:
            # A PORT of a source circuit sheet. Its netlist.yaml metadata rides as hidden fields,
            # which tools/kicad.py exports back: Dir, From/To, Figure; Kind=endpoint for an
            # external endpoint a board wires up (the register's eight inputs).
            shape = {"in": "input", "out": "output", "ref": "passive"}.get(hier.get("dir"), "passive")
            props = "".join(f"\n    (property {q(k)} {q(v)} (at {at[0]} {at[1]} 0) (effects (font (size 1.27 1.27)) hide))"
                            for k, v in hier.get("fields", {}).items())
            self.items.append(f"  (hierarchical_label {q(netname)} (shape {shape}) (at {at[0]} {at[1]} {ang})"
                              f" (effects (font (size 1.27 1.27)) (justify {just}))"
                              f" (uuid {u(self.name, 'hlabel', netname, at)}){props})")
            return
        if glob:
            shape = self.lay.get("ports", {}).get(netname, {}).get("shape", "input")
            self.items.append(f"  (global_label {q(netname)} (shape {shape}) (at {at[0]} {at[1]} {ang})"
                              f" (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just}))"
                              f" (uuid {u(self.name, 'glabel', netname, at)})\n"
                              f"    (property \"Intersheetrefs\" \"${{INTERSHEET_REFS}}\" (at {at[0]} {at[1]} 0)"
                              f" (effects (font (size 1.27 1.27)) hide)))")
        else:
            self.items.append(f"  (label {q(netname)} (at {at[0]} {at[1]} {ang}) (fields_autoplaced)"
                              f" (effects (font (size 1.27 1.27)) (justify {just} bottom))"
                              f" (uuid {u(self.name, 'label', netname, at)}))")

    def power_lib(self, netname):
        """KiCad 8 and later name a power net after the power symbol's VALUE, so the stock
        library symbol is used unchanged, with the value set to this repository's net name."""
        lid = f"power:{self.power[netname]}"
        self.lib(lid)
        return lid

    def power_symbol(self, netname, at, key, point=None, down=None):
        """`point` is the direction the symbol should extend: a supply symbol extends up and a
        ground symbol down at rotation 0, so rotate to match."""
        self.n_power += 1
        ref = f"#PWR{self.n_power:02d}"
        r = 0
        if point is not None:
            natural = (0, 1) if down else (0, -1)
            turns = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}
            r = (turns[tuple(point)] - turns[natural]) % 360
        over = None
        if point is not None and point[1] == 0:
            # lying sideways: the net name reads horizontally, just past the symbol's tip
            d = 6.35 if point[0] > 0 else -6.35
            over = {"value_at": [d, 0], "value_at_justify": "left" if d > 0 else "right"}
        self.symbol(self.power_lib(netname), ref, netname, (at[0], at[1], r), 1, ("pwr", key), hide_ref=True,
                    over=over)

    def meta_comments(self):
        if not self.hier:
            return ""
        n = self.net
        meta = [("circuit", n.get("circuit")), ("page", n.get("page")), ("title", n.get("title")),
                ("replicated", n.get("replicated"))]
        return "\n".join(f"    (comment {5 + i} {q(f'{k}: {v}')})" for i, (k, v) in enumerate(meta) if v is not None)

    def port_fields(self, nname):
        pd = self.net.get("ports", {}).get(nname)
        if pd is None:
            return {"dir": "ref", "fields": {"Kind": "endpoint"}}
        f = {"Dir": pd.get("dir", "")}
        for k in ("from", "to", "figure", "note"):
            if k in pd:
                f[k.capitalize()] = str(pd[k])
        return {"dir": pd.get("dir"), "fields": f}

    def power_flags(self):
        """Power nets SUPPLIED BY ANOTHER CIRCUIT (ports in netlist.yaml). On a sheet drawn
        alone KiCad's ERC cannot see their source, so each gets a PWR_FLAG - the standard
        way - grouped at `flags_at` under a note saying where the supply comes from."""
        nets = [n for n in self.power if n in self.ports_in or n in self.lay.get("supplied", [])]
        if not nets:
            return
        x0, y0 = self.lay.get("flags_at", [20.32, 30.48])
        self.text("Supplied by other circuits (PWR_FLAG):", (x0, y0 - 10.16))
        for i, n in enumerate(nets):
            y = snap(y0 + i * 12.7)
            a, b = (snap(x0 + 2.54), y), (snap(x0 + 20.32), y)
            self.power_symbol(n, a, ("flaggroup", n))
            self.wire(a, b)
            self.n_power += 1
            self.symbol("power:PWR_FLAG", f"#FLG{self.n_power:02d}", "PWR_FLAG", (b[0], b[1], 0), 1,
                        ("flag", n), hide_ref=True)

    def no_connect(self, at):
        self.items.append(f"  (no_connect (at {at[0]} {at[1]}) (uuid {u(self.name, 'nc', at)}))")

    def text(self, s, at, size=1.27):
        self.items.append(f"  (text {q(s)} (at {at[0]} {at[1]} 0) (effects (font (size {size} {size})) "
                          f"(justify left top)) (uuid {u(self.name, 'text', at)}))")

    # -- the sheet
    def build(self, fp):
        net, lay = self.net, self.lay
        self.segments = []
        comps = lay["components"]
        # pin positions
        for ref, c in comps.items():
            if ref not in net["components"]:
                sys.exit(f"sch: {ref} is placed in schematic.yaml but not in netlist.yaml")
            text, pins, props = self.lib(c["symbol"])
            units = {int(k): v for k, v in c["units"].items()} if "units" in c else {1: c["at"]}
            pinmap, libname = {}, {}
            for k, v in c.get("pins", {}).items():
                if isinstance(v, list):
                    pinmap[str(k)], libname[str(k)] = str(v[0]), str(v[1])
                else:
                    pinmap[str(k)] = str(v)
            names = [str(p) for p in net["components"][ref]["pins"]]
            for n in names:
                num = pinmap.get(n, n)
                hit = [(un, lp) for (un, nm), lp in pins.items() if nm == num]
                if not hit:
                    sys.exit(f"sch: {ref}.{n} maps to pin {num}, which {c['symbol']} does not have")
                un, (lx, ly, ang, typ, lname) = hit[0]
                self.pinname[f"{ref}.{n}"] = lname
                if n in libname and libname[n] != lname:
                    sys.exit(f"sch: {ref}.{n} maps to pin {num}, which the library names {lname!r}, "
                             f"not {libname[n]!r} as schematic.yaml says")
                if n in libname:
                    self.pinname[f"{ref}.{n}"] = "~"   # the map named it; the name check is done
                at = units.get(un) if un else units[min(units)]
                if at is None:
                    sys.exit(f"sch: {ref} pin {n} is on unit {un}, which schematic.yaml does not place")
                at = tuple(at) + (0,) * (3 - len(at))
                x, y = place(at, lx, ly)
                self.pinpos[f"{ref}.{n}"] = (x, y) + outward(ang, at[2]) + (typ,)
                self.pinnum[f"{ref}.{n}"] = (ref, num)
            fields = dict(c["fields"]) if c.get("fields") else None
            if self.hier:
                nc = net["components"][ref]
                fields = {"Row": nc.get("of", ref),
                          "Pins": " ".join(n + "=" + (pinmap.get(n, n) + (f"({libname[n]})" if n in libname else ""))
                                           for n in names)}
                for k in ("drawn_as", "note"):
                    if nc.get(k):
                        fields[k.capitalize() if k == "note" else "Drawn_as"] = str(nc[k])
                if c.get("pins_source"):
                    fields["Pins_source"] = c["pins_source"]
            for un, at in units.items():
                at = tuple(at) + (0,) * (3 - len(at))
                self.symbol(c["symbol"], ref, c.get("value", net["components"][ref].get("value", "")),
                            at, un, (ref, un), footprint=c.get("footprint", ""), over=c, fields=fields)
        for k, v in getattr(self, "extra_pins", {}).items():
            self.pinpos[k] = v
        missing = [r for r in net["components"] if r not in comps]
        if missing:
            sys.exit(f"sch: not placed in schematic.yaml: {', '.join(missing)}")

        # explicit wires: polylines of pin refs and [x, y] points
        for poly in lay.get("wires", []):
            pts = []
            for p in poly:
                if isinstance(p, str):
                    if p not in self.pinpos:
                        sys.exit(f"sch: wire names {p}, which is not a pin in netlist.yaml")
                    self.wired.add(p)
                    pts.append(self.pinpos[p][:2])
                else:
                    pts.append((snap(p[0]), snap(p[1])))
            for a, b in zip(pts, pts[1:]):
                if a[0] != b[0] and a[1] != b[1]:
                    sys.exit(f"sch: wire {a} -> {b} is not orthogonal")
                self.wire(a, b)

        # explicit labels and power symbols on wires
        ports = net.get("ports", {})
        for lb in lay.get("labels", []):
            at = (snap(lb["at"][0]), snap(lb["at"][1]))
            d = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}[lb.get("dir", "left")]
            # `local: true`: a local label even on a port's net - it names a net carrying two ports
            if self.hier and not lb.get("local") and (lb["net"] in ports or lb["net"] in self.lay.get("hier_endpoints", [])):
                self.label(lb["net"], at, d, hier=self.port_fields(lb["net"]))
            else:
                self.label(lb["net"], at, d, glob=lb["net"] in ports and not lb.get("local"))
        for i, ps in enumerate(lay.get("power_symbols", [])):
            self.power_symbol(ps["net"], (snap(ps["at"][0]), snap(ps["at"][1])), ("placed", i))

        # every pin not wired: a stub, then a label, a power symbol or a no-connect
        members = {}
        for nname, plist in net["nets"].items():
            for m in plist:
                if isinstance(m, str):
                    members.setdefault(nname, []).append(m)
        ext = set(net.get("external_endpoints", []))
        for nname, plist in members.items():
            for p in plist:
                if p in self.wired:
                    continue
                x, y, dx, dy, typ = self.pinpos[p]
                # On a source sheet a spare whose net has its own name keeps it, as a label:
                # tools/kicad.py exports a lone labelled pin as an external endpoint.
                if nname in ext and len(plist) == 1 and not (self.hier and nname in self.lay.get("hier_endpoints", [])) \
                        and not (self.hier and nname != p.rsplit(".", 1)[1]):
                    self.no_connect((x, y))
                    continue
                end = (snap(x + dx * STUB), snap(y + dy * STUB))
                self.wire((x, y), end)
                if nname in self.power:
                    # the symbol points along its stub, away from the part, so it never
                    # turns into a neighbouring pin's stub or label
                    down = self.power[nname] in ("GND", "GNDA", "GNDD", "Earth")
                    self.power_symbol(nname, end, ("auto", p), point=(dx, dy), down=down)
                elif self.hier and (nname in ports or nname in self.lay.get("hier_endpoints", [])):
                    self.label(nname, end, (dx, dy), hier=self.port_fields(nname))
                else:
                    self.label(nname, end, (dx, dy), glob=nname in ports)

        # junctions: a point where three or more wire ends meet, or an end lands mid-segment
        ends = {}
        for a, b in self.segments:
            for p in (a, b):
                ends[p] = ends.get(p, 0) + 1
        pins_at = {v[:2] for v in self.pinpos.values()}
        for p, n in ends.items():
            mid = sum(1 for a, b in self.segments if p not in (a, b) and
                      min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))
            if n + 2 * mid + (1 if p in pins_at else 0) >= 3:
                self.items.append(f"  (junction (at {p[0]} {p[1]}) (diameter 0) (color 0 0 0 0)"
                                  f" (uuid {u(self.name, 'junction', p)}))")

        self.power_flags()
        for t in lay.get("notes", []):
            self.text(t["text"], t["at"])

        tb = lay.get("title", {})
        libsyms = "\n".join("    " + t.replace(f'(symbol "{lid.split(":")[1]}"', f'(symbol {q(lid)}', 1)
                            .replace("\n  ", "\n    ")
                            for lid, (t, _, _) in sorted(self.libs.items()))
        head = f"""(kicad_sch (version 20250114) (generator "sch.py") (generator_version "9.0")
  (uuid {u(self.name, 'root')})
  (paper {q(lay.get('paper', 'A4'))})
  (title_block
    (title {q(tb.get('title', net.get('title', self.name)))})
{self.meta_comments()}
    (date "")
    (rev {q(fp)})
    (company "Woody")
    (comment 1 {q('GENERATED by tools/sch.py - do not edit; connectivity: ' + os.path.relpath(self.d, ROOT) + '/' + lay.get('netlist', 'netlist.yaml'))})
    (comment 2 {q('placement: schematic.yaml; checked against ' + lay.get('netlist', 'netlist.yaml') + ' by kicad-cli netlist export')})
    (comment 3 {q(tb.get('comment', ''))})
    (comment 4 {q('fingerprint ' + fp + ' - verify: python3 tools/sch.py check ' + os.path.relpath(self.d, ROOT))})
  )
  (lib_symbols
{libsyms}
  )
"""
        tail = f"""  (sheet_instances (path "/" (page "1")))
)
"""
        return head + "\n".join(self.items) + "\n" + tail


def kicad_netlist(sch_path):
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "n.net")
        r = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, sch_path],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"sch: kicad-cli netlist export failed:\n{r.stdout}{r.stderr}")
        tree = parse(open(out).read())[0]
    nets = {}
    kicad_netlist.nc = set()     # pins the LIBRARY marks not connected (an N/C lead of a package)
    for n in find(find(tree, "nets")[0], "net"):
        name = find(n, "name")[0][1]
        nodes = {(find(x, "ref")[0][1], find(x, "pin")[0][1]) for x in find(n, "node")}
        for x in find(n, "node"):
            t = find(x, "pintype")
            if t and t[0][1].startswith("no_connect"):
                kicad_netlist.nc.add((find(x, "ref")[0][1], find(x, "pin")[0][1]))
        nets[name] = nodes
    return nets


def compare(sheet, net, knets):
    """Every netlist.yaml net must be exactly one KiCad net with the same pins."""
    problems = []
    by_pins = {}
    for kname, nodes in knets.items():
        real = {n for n in nodes if not n[0].startswith("#")}
        if real:
            by_pins[frozenset(real)] = kname
    seen = set()
    for nname, plist in net["nets"].items():
        want = frozenset(sheet.pinnum[m] for m in plist if isinstance(m, str))
        if not want:
            # ports and no pin: not in KiCad's netlist; tools/kicad.py export reads it off the labels
            continue
        kname = by_pins.get(want)
        if kname is None:
            got = [k for k, v in knets.items() if want & v]
            problems.append(f"net {nname}: pins {sorted(want)} are not one KiCad net (touch {got})")
            continue
        seen.add(kname)
        bare = kname.lstrip("/")
        if len(want) > 1 and bare != nname and not kname.startswith("unconnected-"):
            problems.append(f"net {nname}: KiCad names it {kname!r}")
    named = set(sheet.pinnum.values())
    nc = getattr(kicad_netlist, "nc", set())
    for kname, nodes in knets.items():
        # a package's N/C lead the netlist does not name (the library types it no_connect) is no net
        real = {n for n in nodes if not n[0].startswith("#") and (n in named or n not in nc)}
        if real and kname not in seen:
            problems.append(f"KiCad net {kname} {sorted(real)} is not in netlist.yaml")
    return problems


def pin_types(sheet, net):
    """KiCad 7's command line has no ERC (it arrived in KiCad 8), so this is a small one of our own,
    on the library's pin types. It is not KiCad's ERC: open the sheet in KiCad 8 or 9 for that."""
    ports = net.get("ports", {})
    drivers = {"output", "tri_state", "power_out", "bidirectional", "passive"}
    problems = []
    for nname, plist in net["nets"].items():
        pins = [m for m in plist if isinstance(m, str)]
        types = [sheet.pinpos[p][4] for p in pins]
        is_port = any(isinstance(m, dict) and "port" in m for m in plist) or nname in ports \
            or nname in sheet.lay.get("supplied", [])
        powered = is_port or nname in sheet.power
        outs = [p for p, t in zip(pins, types) if t in ("output", "power_out")]
        if len(outs) > 1:
            problems.append(f"error: {nname} has {len(outs)} outputs driving it: {outs}")
        if any(t == "power_in" for t in types) and not powered:
            problems.append(f"error: {nname} feeds a power pin but is neither a port nor a power net")
        ins = [p for p, t in zip(pins, types) if t == "input"]
        if ins and not powered and not any(t in drivers for t in types):
            problems.append(f"warning: {nname} has inputs {ins} and nothing driving it")
    return problems + pin_names(sheet)


def pin_names(sheet):
    """The one check a pin-number map allows: pins the library NAMES must match netlist.yaml's name."""
    problems = []
    for p, (ref, num) in sheet.pinnum.items():
        lname = sheet.pinname.get(p, "~")
        ours = p.rsplit(".", 1)[1]
        if lname not in ("~", "") and not re.fullmatch(r"Pin_\d+", lname) and not ours.isdigit() \
                and lname.upper() != ours.upper():
            problems.append(f"error: {p} maps to pin {num}, which the library names {lname!r}")
    return problems


def kicad_env():
    env = dict(os.environ)
    for v in ("KICAD9_SYMBOL_DIR", "KICAD8_SYMBOL_DIR", "KICAD7_SYMBOL_DIR"):
        env.setdefault(v, SYMDIR)
    env.setdefault("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
    env.setdefault("KICAD9_3DMODEL_DIR", "/usr/share/kicad/3dmodels")
    return env


def kicad_erc(sch_path):
    """KiCad's own ERC, as 'error: ...'/'warning: ...' lines; None if kicad-cli has none (KiCad 7)."""
    import json
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "erc.json")
        r = subprocess.run(["kicad-cli", "sch", "erc", "--severity-all", "--format", "json", "-o", out, sch_path],
                           capture_output=True, text=True, env=kicad_env())
        if not os.path.exists(out):
            return None
        d = json.load(open(out))
    lines = []
    for sh in d.get("sheets", []):
        for v in sh.get("violations", []):
            items = "; ".join(i["description"] for i in v.get("items", []))
            lines.append(f"{v['severity']}: [{v['type']}] {v['description']} - {items}")
    return lines


def render(sch_path, png):
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["kicad-cli", "sch", "export", "pdf", "-o", os.path.join(t, "s.pdf"), sch_path],
                       capture_output=True, text=True, check=True)
        subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", os.path.join(t, "s.pdf"),
                        os.path.join(t, "s")], check=True)
        os.replace(os.path.join(t, "s.png"), png)


def outputs(d, lay):
    name = lay.get("name", os.path.basename(d))
    return os.path.join(d, name + ".kicad_sch"), os.path.join(d, name + ".sch.png")


def cmd_build(circuit_dir):
    d, net, lay = load(circuit_dir)
    fp = fingerprint(d, lay)
    sheet = Sheet(d, net, lay)
    text = sheet.build(fp)
    sch, png = outputs(d, lay)
    open(sch, "w").write(text)
    problems = compare(sheet, net, kicad_netlist(sch))
    checks = kicad_erc(sch)
    erc_name = "KiCad ERC + pin names"
    if checks is not None:
        checks += pin_names(sheet)
    else:
        checks, erc_name = pin_types(sheet, net), "pin-type check (kicad-cli has no ERC before KiCad 8)"
    render(sch, png)
    rel = os.path.relpath(sch, ROOT)
    print(f"sch: wrote {rel} and {os.path.relpath(png, ROOT)} (fingerprint {fp})")
    n_err = sum(1 for c in checks if c.startswith("error"))
    print(f"sch: netlist match: {'PASS' if not problems else 'FAIL'} - {len(net['nets'])} nets compared pin by pin")
    for p in problems:
        print("  " + p)
    print(f"sch: {erc_name}: {n_err} error(s), {len(checks) - n_err} warning(s)")
    for c in checks:
        print("  " + c)
    return 1 if problems or n_err else 0


def cmd_check(circuit_dir):
    d, net, lay = load(circuit_dir)
    fp = fingerprint(d, lay)
    sch, png = outputs(d, lay)
    if not os.path.exists(sch) or not os.path.exists(png):
        print(f"sch: {os.path.relpath(d, ROOT)}: not built")
        return 1
    stamped = re.search(r'\(rev "([0-9a-f]+)"\)', open(sch).read())
    if not stamped or stamped.group(1) != fp:
        print(f"sch: {os.path.relpath(sch, ROOT)} is STALE (built {stamped and stamped.group(1)}, inputs now {fp})")
        return 1
    print(f"sch: PASS {os.path.relpath(sch, ROOT)} matches its inputs ({fp})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("build", "check"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"build": cmd_build, "check": cmd_check}[sys.argv[1]](sys.argv[2].rstrip("/")))
