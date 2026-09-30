#!/usr/bin/env python3
"""The KiCad sheets are the source of truth; this tool exports what the rest of the repo reads.

    python3 tools/kicad.py export hardware/cluster/key-register     # write netlist.yaml from the sheet
    python3 tools/kicad.py export hardware/boards/key-board-rh      # write board-netlist.yaml, ERC it
    python3 tools/kicad.py render hardware/boards/key-board-rh      # PNG of every page
    python3 tools/kicad.py check                                    # exit 1 if any export or render is stale
    python3 tools/kicad.py set-field <sheet> <REF> <field> <value>  # edit one field on a sheet (the source)

WHAT IS THE SOURCE. For every circuit directory holding a `<name>.kicad_sch`
whose title block names a circuit (`circuit: ...`), THAT SHEET IS
AUTHORITATIVE - for connectivity, and for each part's identity: the BOM row it
buys from (field `Row`), its pin map with the datasheet page that proves it
(`Pins`, `Pins_source`) and its notes (`Note`). Ports are hierarchical labels;
their direction, peer and register figure ride on the label as fields (`Dir`,
`From`/`To`, `Figure`). A label with `Kind = endpoint` is an input a board
wires up (a register's A..H), not a port.

Edit the sheet in KiCad 9 (or as text - it is an s-expression), then run
`export`. The circuit's `netlist.yaml` is REGENERATED from it and must not be
edited: tools/check-netlist.py, hardware/nets.yaml and the BOM checks read
netlist.yaml exactly as before, so every existing check still runs - on the
sheet's truth.

A BOARD is a KiCad project under hardware/boards/<board>/ whose root sheet
places the circuit sheets as sub-sheets, one per instance (a key board: one
key-register, one key-switch-network per key). `export` writes its flattened
netlist to board-netlist.yaml - what a PCB will be laid out from - and runs
KiCad's ERC over the whole hierarchy. A circuit sheet opened on its own
cannot pass ERC (its ports have no parent); a board is where ERC means
something.

`check` re-exports everything into a scratch directory and compares it with
what is committed, and recomputes each render's inputs, so a sheet edited
without re-exporting is reported by name - the same contract as
tools/cad.py for the body. It also runs tools/pcb.py check on every board
with a layout, holds each key board's J-CHAIN pins to the ribbon's netlist
(hardware/interfaces/key-chain-loom), and fails on any render or fab/ file
the ledger does not know - a stray Gerber is uploaded with the rest.

Circuits not yet migrated keep a hand-written netlist.yaml and are untouched.
"""
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sch import parse, find, Str, kicad_env  # noqa: E402

yaml.SafeDumper.add_representer(Str, lambda dumper, v: dumper.represent_str(str(v)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "hardware", "SHEETS.csv")


# ------------------------------------------------------------------ reading a sheet

def title_meta(tree):
    meta = {}
    for tb in find(tree, "title_block"):
        for c in find(tb, "comment"):
            m = re.match(r"(circuit|page|title|replicated): (.*)", c[2])
            if m:
                meta[m.group(1)] = int(m.group(2)) if m.group(1) == "replicated" else m.group(2)
    return meta


def props(node):
    return {p[1]: p[2] for p in find(node, "property")}


def sheet_labels(tree):
    out = []
    for hl in find(tree, "hierarchical_label"):
        out.append((hl[1], props(hl)))
    return out


def label_groups(tree):
    """Which labels sit on one net, read off the sheet's own wires: [(local names, port names)].

    KiCad's netlist names a net after ONE label and lists pins only, so a net that carries two
    ports (a hop of the key chain: one register's QH is the next one's SER), or ports and no pin
    at all (two ports joined by a trace), cannot be read from it. Labels are joined by the wires
    they sit on - an end, or anywhere along one - by wires meeting end to end or end on segment,
    and by name. Pins play no part: KiCad's netlist still decides every pin."""
    segs = []
    for w in find(tree, "wire"):
        pts = [(float(p[1]), float(p[2])) for p in find(find(w, "pts")[0], "xy")]
        segs += list(zip(pts, pts[1:]))
    labels = [("local", l[1], (float(find(l, "at")[0][1]), float(find(l, "at")[0][2]))) for l in find(tree, "label")]
    labels += [("port", l[1], (float(find(l, "at")[0][1]), float(find(l, "at")[0][2])))
               for l in find(tree, "hierarchical_label")]

    def on(p, s):
        (x1, y1), (x2, y2) = s
        return (min(x1, x2) - 1e-6 <= p[0] <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= p[1] <= max(y1, y2) + 1e-6
                and abs((x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1)) < 1e-6)
    parent = list(range(len(segs) + len(labels)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def join(a, b):
        parent[root(a)] = root(b)
    for i, s in enumerate(segs):
        for j, t in enumerate(segs[:i]):
            if any(on(p, t) for p in s) or any(on(p, s) for p in t):
                join(i, j)
    by_name = {}
    for k, (kind, name, at) in enumerate(labels):
        n = len(segs) + k
        for i, s in enumerate(segs):
            if on(at, s):
                join(n, i)
        if (kind, name) in by_name:
            join(n, by_name[(kind, name)])
        by_name[(kind, name)] = n
    groups = {}
    for k, (kind, name, _) in enumerate(labels):
        g = groups.setdefault(root(len(segs) + k), (set(), set()))
        g[0 if kind == "local" else 1].add(name)
    return list(groups.values())


def is_source(d):
    name = os.path.basename(d)
    p = os.path.join(d, name + ".kicad_sch")
    return os.path.exists(p) and "circuit" in title_meta(parse(open(p).read())[0])


def kicad_netlist(sch):
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "n.net")
        r = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, sch],
                           capture_output=True, text=True, env=kicad_env())
        if r.returncode or not os.path.exists(out):
            sys.exit(f"kicad: netlist export of {sch} failed:\n{r.stdout}{r.stderr}")
        tree = parse(open(out).read())[0]
    comps = {}
    for c in find(find(tree, "components")[0], "comp"):
        ref = find(c, "ref")[0][1]
        fields = {}
        for fs in find(c, "fields"):
            for f in find(fs, "field"):
                if len(f) > 2:
                    fields[find(f, "name")[0][1]] = f[2]
        fp = find(c, "footprint")
        # a symbol with "Exclude from BOM" ticked (in_bom no): a test pad, a fiducial - board-only
        in_bom = not any(find(p, "name")[0][1] == "exclude_from_bom" for p in find(c, "property"))
        # the hierarchical sheet it sits on ("LH1", "REG"; "" at the root): with its Row,
        # that is what a numeric reference (R1, C6) is looked up by
        sp = find(c, "sheetpath")
        sheet = find(sp[0], "names")[0][1].strip("/").rsplit("/", 1)[-1] if sp else ""
        comps[ref] = {"value": find(c, "value")[0][1], "fields": fields, "footprint": fp[0][1] if fp else "",
                      "in_bom": in_bom, "sheet": sheet}
    nets = []
    kicad_netlist.nc = set()     # pins the LIBRARY marks not connected (an N/C lead of a package)
    for n in find(find(tree, "nets")[0], "net"):
        nodes = [(find(x, "ref")[0][1], find(x, "pin")[0][1]) for x in find(n, "node")]
        for x in find(n, "node"):
            t = find(x, "pintype")
            if t and t[0][1].startswith("no_connect"):
                kicad_netlist.nc.add((find(x, "ref")[0][1], find(x, "pin")[0][1]))
        nets.append((find(n, "name")[0][1], nodes))
    return comps, nets


# ------------------------------------------------------------------ circuit export

def pinmap_of(fields):
    """'SHLD=1(~{PL}) CLK=2(CP)' -> {'1': 'SHLD', '2': 'CLK'}, and the names in order."""
    names, num2name = [], {}
    for tok in fields.get("Pins", "").split():
        name, rest = tok.split("=", 1)
        num = rest.split("(", 1)[0]
        names.append(name)
        num2name[num] = name
    return names, num2name


def export_circuit(d):
    name = os.path.basename(d)
    sch = os.path.join(d, name + ".kicad_sch")
    tree = parse(open(sch).read())[0]
    meta = title_meta(tree)
    labels = sheet_labels(tree)
    ports, endpoints = {}, set()
    for lname, p in labels:
        if p.get("Kind") == "endpoint":
            endpoints.add(lname)
            continue
        if lname in ports:
            continue
        spec = {"dir": p.get("Dir", "ref")}
        for k in ("From", "To", "Figure", "Note"):
            if p.get(k):
                spec[k.lower()] = p[k]
        ports[lname] = spec
    comps, nets = kicad_netlist(sch)
    out_comps, maps = {}, {}
    problems = []
    for ref in sorted(comps):
        if ref.startswith("#"):
            continue
        f = comps[ref]["fields"]
        names, num2name = pinmap_of(f)
        maps[ref] = num2name
        c = {}
        if f.get("Row", ref) != ref:
            c["of"] = f["Row"]
        if comps[ref]["value"] not in ("", "~"):
            c["value"] = comps[ref]["value"]      # a part not yet chosen has none (Q-LOADSW)
        if f.get("Drawn_as"):
            c["drawn_as"] = f["Drawn_as"]
        c["pins"] = [int(n) if n.isdigit() else n for n in names]
        if f.get("Note"):
            c["note"] = f["Note"]
        if not names:
            problems.append(f"{ref}: no Pins field - every part on a source sheet names its pins")
        out_comps[ref] = c
    # the ports on each net, by the net's name: a local label names the net (KiCad ranks it
    # above a hierarchical one), else its one port does
    net_ports = {}
    for local, hier in label_groups(tree):
        if not hier:
            continue
        if len(local) > 1 or (not local and len(hier) > 1):
            problems.append(f"labels {sorted(local | hier)} are one net - name it with exactly one local label")
            continue
        net_ports.setdefault(next(iter(local)) if local else next(iter(hier)), set()).update(hier)
    out_nets, ext = {}, []
    nc = kicad_netlist.nc
    for kname, nodes in nets:
        # a package's N/C lead that the part's Pins field does not name (the library types it
        # no_connect: the MPXV4006DP's pins 1 and 5-8) is no pin of the circuit and no net
        pins = [f"{r}.{maps.get(r, {}).get(p, p)}" for r, p in nodes
                if not r.startswith("#") and (p in maps.get(r, {}) or (r, p) not in nc)]
        if not pins:
            continue
        # a net named on a sub-sheet of a circuit drawn as two pages (one per board -
        # module/pitch-stage) carries its sheet path: the circuit's name is the last part
        bare = kname if kname.startswith(("unconnected-", "Net-(")) else kname.rsplit("/", 1)[-1]
        if kname.startswith("unconnected-") or kname.startswith("Net-("):
            if len(pins) == 1:
                bare = pins[0].split(".", 1)[1]       # a lone no-connect pin is named after the pin
                ext.append(bare)
            else:
                problems.append(f"net of {pins} has no label - name every net on a source sheet")
                continue
        on_net = sorted(p for p in net_ports.get(bare, ()) if p in ports) or ([bare] if bare in ports else [])
        members = [{"port": p} for p in on_net]
        members += pins
        out_nets[bare] = members
        if bare in endpoints:
            ext.append(bare)
        elif len(pins) == 1 and not on_net and not kname.startswith(("unconnected-", "Net-(")):
            ext.append(bare)          # a lone pin named by a label: a spare, left open on purpose
    # a net of ports and no pin (two ports joined by a trace) is not in KiCad's netlist at all
    for name, hier in net_ports.items():
        if name not in out_nets and any(p in ports for p in hier):
            out_nets[name] = [{"port": p} for p in sorted(hier) if p in ports]
    carried = {m["port"] for ms in out_nets.values() for m in ms if isinstance(m, dict)}
    for pname in ports:
        if pname not in carried:
            problems.append(f"port {pname} labels no net")
    doc = {k: meta[k] for k in ("circuit", "title", "page", "replicated") if k in meta}
    doc["ports"] = ports
    # parts the page's drawing shows and another circuit owns: one sheet-text line each,
    # `FOREIGN <label>: owner <circuit>, row <BOM row>` (check-netlist resolves them by row)
    foreign = {}
    for t in find(tree, "text"):
        for line in t[1].split("\n"):
            m = re.match(r"FOREIGN (\S+): owner (\S+), row (\S+)$", line.strip())
            if m:
                foreign[m.group(1)] = {"owner": m.group(2), "row": m.group(3)}
    if foreign:
        doc["foreign"] = foreign
    doc["components"] = out_comps
    doc["nets"] = out_nets
    if ext:
        doc["external_endpoints"] = sorted(ext)
    rel = os.path.relpath(sch, ROOT)
    head = (f"# GENERATED from {rel} by tools/kicad.py - DO NOT EDIT.\n"
            f"# The KiCad sheet is authoritative for this circuit: edit it in KiCad 9, then run\n"
            f"#   python3 tools/kicad.py export {os.path.relpath(d, ROOT)}\n"
            f"# Every note and argument that used to live in this file is on the sheet\n"
            f"# (part fields, sheet text) or on {meta.get('page', 'the circuit page')}.\n\n")
    return head + yaml.safe_dump(doc, sort_keys=False, width=110, allow_unicode=True), problems


# ------------------------------------------------------------------ board export

def board_sheet(d):
    return os.path.join(d, os.path.basename(d) + ".kicad_sch")


def export_board(d):
    sch = board_sheet(d)
    comps, nets = kicad_netlist(sch)
    # pin names come from each part's own Pins field, exactly as for a circuit
    out_comps, maps = {}, {}
    for ref in sorted(comps):
        if ref.startswith("#"):
            continue
        f = comps[ref]["fields"]
        names, num2name = pinmap_of(f)
        maps[ref] = num2name
        out_comps[ref] = {"of": f.get("Row", ref), "value": comps[ref]["value"],
                          "pins": [int(n) if n.isdigit() else n for n in names]}
        if comps[ref]["sheet"]:
            out_comps[ref]["sheet"] = comps[ref]["sheet"]
    out_nets, ext = {}, []
    for kname, nodes in nets:
        pins = [f"{r}.{maps.get(r, {}).get(p, p)}" for r, p in nodes if not r.startswith("#")]
        if not pins:
            continue
        name = kname
        if kname.startswith("unconnected-"):
            name = pins[0]
            ext.append(name)
        out_nets[name] = pins
    tree = parse(open(sch).read())[0]
    title = find(find(tree, "title_block")[0], "title")[0][1] if find(tree, "title_block") else ""
    doc = {"board": os.path.basename(d), "title": title, "components": out_comps,
           "nets": dict(sorted(out_nets.items())), "external_endpoints": sorted(ext)}
    head = (f"# GENERATED from the KiCad project {os.path.relpath(sch, ROOT)} by tools/kicad.py - DO NOT EDIT.\n"
            f"# The flattened netlist of this board, every sub-sheet instance expanded.\n\n")
    return head + yaml.safe_dump(doc, sort_keys=False, width=110, allow_unicode=True), erc(sch)


def erc(sch):
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "erc.json")
        subprocess.run(["kicad-cli", "sch", "erc", "--severity-all", "--format", "json", "-o", out, sch],
                       capture_output=True, text=True, env=kicad_env())
        d = json.load(open(out))
    return [f"{v['severity']}: [{v['type']}] {v['description']} - "
            + "; ".join(i["description"] for i in v.get("items", []))
            for sh in d.get("sheets", []) for v in sh.get("violations", [])]


# ------------------------------------------------------------------ renders

def sheet_files(sch, seen=None):
    """The sheet and every sub-sheet file it places, recursively."""
    seen = seen if seen is not None else []
    sch = os.path.normpath(sch)
    if sch in seen:
        return seen
    seen.append(sch)
    tree = parse(open(sch).read())[0]
    for sh in find(tree, "sheet"):
        f = props(sh).get("Sheetfile")
        if f:
            sheet_files(os.path.join(os.path.dirname(sch), f), seen)
    return seen


def blob(path):
    r = subprocess.run(["git", "hash-object", path], capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip()


def render(d):
    """One PNG per page, named <sheet>.sch.png (page 1) and <sheet>.p<N>.sch.png."""
    name = os.path.basename(d)
    sch = os.path.join(d, name + ".kicad_sch")
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["kicad-cli", "sch", "export", "pdf", "-o", os.path.join(t, "s.pdf"), sch],
                       capture_output=True, text=True, check=True, env=kicad_env())
        subprocess.run(["pdftoppm", "-png", "-r", "150", os.path.join(t, "s.pdf"), os.path.join(t, "p")], check=True)
        pages = sorted(f for f in os.listdir(t) if f.startswith("p") and f.endswith(".png"))
        for f in os.listdir(d):
            if re.fullmatch(re.escape(name) + r"(\.p\d+)?\.sch\.png", f):  # this sheet's own renders only
                os.remove(os.path.join(d, f))
        outs = []
        for i, f in enumerate(pages, 1):
            dst = os.path.join(d, name + (".sch.png" if i == 1 else f".p{i}.sch.png"))
            os.replace(os.path.join(t, f), dst)
            outs.append(dst)
    ledger_set(d, outs, sheet_files(sch))
    return outs


def ledger_rows():
    if not os.path.exists(LEDGER):
        return {}
    return {r["render"]: r for r in csv.DictReader(open(LEDGER))}


def ledger_set(d, outs, inputs, kind="sch"):
    """Record renders (kind 'sch' or 'pcb') and the blobs they were made from."""
    rows = ledger_rows()
    rel = os.path.relpath(d, ROOT)
    # this directory's own renders and its fab/ - not a circuit nested under it
    # (hardware/carrier holds five circuits of its own)
    mine = lambda k: os.path.dirname(k) in (rel, os.path.join(rel, "fab"))
    for k in [k for k in rows if mine(k) and (".pcb-" in k or "/fab/" in k) == (kind == "pcb")]:
        del rows[k]
    ins = " ".join(f"{os.path.relpath(p, ROOT)}@{blob(p)}" for p in inputs)
    for o in outs:
        rows[os.path.relpath(o, ROOT)] = {"render": os.path.relpath(o, ROOT), "sha1": hashlib.sha1(open(o, "rb").read()).hexdigest(),
                                          "inputs": ins}
    with open(LEDGER, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["render", "sha1", "inputs"])
        w.writeheader()
        for k in sorted(rows):
            w.writerow(rows[k])


# ------------------------------------------------------------------ editing a sheet as text

def set_field(sch, ref, field, value):
    """Set one field on the symbol(s) whose default Reference is `ref` - every unit.
    The sheet is the source; this is the scripted way to edit it, same as KiCad would."""
    text = open(sch).read()
    tree = parse(text)[0]
    hits = 0
    for sym in find(tree, "symbol"):
        if not find(sym, "lib_id"):
            continue
        pr = {p[1]: p for p in find(sym, "property")}
        if pr.get("Reference", [None, None, None])[2] != ref:
            continue
        uid = find(sym, "uuid")[0][1]
        i = text.index(f"(uuid {uid})")
        end = text.index("\n  )", i)
        block = text[i:end]
        m = re.search(r'\(property "%s" "((?:\\.|[^"\\])*)"' % re.escape(field), block)
        esc = value.replace("\\", "\\\\").replace('"', '\\"')
        if m:
            block = block[:m.start()] + f'(property "{field}" "{esc}"' + block[m.end():]
        else:
            at = find(sym, "at")[0]
            block = block.replace("\n    (pin ", f'\n    (property "{field}" "{esc}" (at {at[1]} {at[2]} 0) (effects (font (size 1.27 1.27)) hide))\n    (pin ', 1)
        text = text[:i] + block + text[end:]
        hits += 1
    if not hits:
        sys.exit(f"kicad: no symbol {ref} in {sch}")
    open(sch, "w").write(text)
    return hits


# ------------------------------------------------------------------ commands

def migrated_circuits():
    out = []
    for dirpath, _, files in os.walk(os.path.join(ROOT, "hardware")):
        if os.path.basename(dirpath) + ".kicad_sch" in files and "boards" not in dirpath.split(os.sep) and is_source(dirpath):
            out.append(dirpath)
    return sorted(out)


def boards():
    b = os.path.join(ROOT, "hardware", "boards")
    return sorted(os.path.join(b, x) for x in os.listdir(b) if os.path.exists(board_sheet(os.path.join(b, x)))) \
        if os.path.isdir(b) else []


def cmd_export(target):
    d = os.path.join(ROOT, target.rstrip("/"))
    if os.sep + "boards" + os.sep in d + os.sep:
        text, checks = export_board(d)
        open(os.path.join(d, "board-netlist.yaml"), "w").write(text)
        n_err = sum(1 for c in checks if c.startswith("error"))
        print(f"kicad: wrote {target}/board-netlist.yaml; ERC {n_err} error(s), {len(checks) - n_err} warning(s)")
        for c in checks:
            print("  " + c)
        return 1 if n_err else 0
    text, problems = export_circuit(d)
    if problems:
        print(f"kicad: {target}: FAIL")
        for p in problems:
            print("  " + p)
        return 1
    open(os.path.join(d, "netlist.yaml"), "w").write(text)
    print(f"kicad: wrote {target}/netlist.yaml from {os.path.basename(d)}.kicad_sch")
    return 0


def cmd_render(target):
    d = os.path.join(ROOT, target.rstrip("/"))
    for o in render(d):
        print(f"kicad: rendered {os.path.relpath(o, ROOT)}")
    return 0


ALLOC = os.path.join(ROOT, "hardware", "cluster", "key-marker-and-bits", "allocation.yaml")
ALLOC_PAGE = os.path.join(ROOT, "hardware", "cluster", "key-marker-and-bits", "key-marker-and-bits.md")


def check_allocation(board_docs):
    """allocation.yaml is the 32-bit allocation as data. It must agree with the table in
    key-marker-and-bits.md §4 (its written form) and with every KiCad board that carries a
    register (which is where the wiring actually is). Read off the board by what each input
    is wired TO, not by net names: a key network's pull-up, a free-bit pull-up, or a rail."""
    alloc = yaml.safe_load(open(ALLOC))
    problems = []
    text = open(ALLOC_PAGE).read()
    sec = text[text.index("### Allocation"):]
    for cluster, row in alloc["registers"].items():
        m = re.search(r"^\| `%s` \| [^|]+\|(.*)\|\s*$" % cluster, sec, re.M)
        if not m:
            problems.append(f"allocation: {cluster} has no row in key-marker-and-bits.md §4")
            continue
        cells = [c.strip().strip("*") for c in m.group(1).split("|")]
        for cell, item in zip(cells, row):
            want = {"M0": "M", "M1": "M", "sw+": "sw+", "sw-": "sw−"}.get(item, "free" if item.startswith("FREE") else item)
            if cell != want:
                problems.append(f"allocation: {cluster}: allocation.yaml says {item}, the page's table says {cell}")
    layout = {k["id"]: k for k in yaml.safe_load(open(os.path.join(ROOT, "config", "key-layout.yaml")))["keys"]}
    for cluster, row in alloc["registers"].items():
        for item in row:
            if item in ("M0", "M1", "sw+", "sw-") or item.startswith("FREE"):
                continue
            if layout.get(item, {}).get("cluster") != cluster:
                problems.append(f"allocation: {item} is not a {cluster} key in config/key-layout.yaml")
    rows = {tuple(r): c for c, r in alloc["registers"].items()}
    for bname, doc in board_docs:
        comps = doc["components"]
        regs = [r for r, c in comps.items() if c.get("of") == "U-KEYS"]
        if not regs:
            # a board that carries registers (the key boards, the main board) without one
            # would pass this check by having nothing to check; the adapter carries none
            if bname.startswith("key-board") or bname == "main-board":
                problems.append(f"allocation: {bname} has no U-KEYS register - nothing to hold to allocation.yaml")
        for u in regs:
            where = {}
            for pins in doc["nets"].values():
                for p in pins:
                    where[p] = pins
            got = []
            for inp in alloc["order"]:
                net = where.get(f"{u}.{inp}", [])
                if f"{u}.VCC" in net:
                    got.append("M1")
                elif f"{u}.GND" in net:
                    got.append("M0")
                else:
                    # a pull-up's key is the sheet it sits on (LH1, FREE3)
                    pu = [p for p in net if p.endswith(".2") and comps.get(p[:-2], {}).get("of") == "R-KEY-PU"]
                    got.append(comps[pu[0][:-2]].get("sheet", "?") if len(pu) == 1 else "?")
            if tuple(got) not in rows:
                problems.append(f"allocation: {bname} wires {u} as {' '.join(got)} (H..A), which is no row of allocation.yaml")
    return problems


LOOM = os.path.join(ROOT, "hardware", "interfaces", "key-chain-loom", "netlist.yaml")


def check_chain(board_docs):
    """Each key board's J-CHAIN against the ribbon's other end (K7-1). The two ends are
    recorded apart: the board's pin map in its sheet (board-netlist.yaml), the ribbon's in
    the loom's netlist.yaml (exported from its sheet), as J-CHAIN-KEY-<LH|RH>. Pin k of the key board
    must be on the net the loom puts J-CHAIN-KEY-<x>.k on, by name, and a pin the board
    leaves unconnected must be a spare conductor there. The loom's own -RN2 map is held
    to its rule too: key-board pin k shares a net with main-board pin 13 - k. A swapped
    pin on either side is a wrong conductor, and on the rail and ground pins a short."""
    loom = yaml.safe_load(open(LOOM))
    lnet = {}
    for net, nodes in loom["nets"].items():
        for n in nodes:
            if isinstance(n, str):
                lnet[n] = net
    rel = os.path.relpath(LOOM, ROOT)
    problems = []
    for bname, doc in board_docs:
        js = [r for r, c in doc["components"].items() if c.get("of") == "J-CHAIN"]
        if not js:
            continue
        if bname == "main-board":
            problems += check_chain_main(doc, js, loom, lnet, rel)
            continue
        jref = js[0]
        side = bname.rsplit("-", 1)[-1].upper()
        key = f"J-CHAIN-KEY-{side}"
        if key not in loom["components"]:
            problems.append(f"chain: {bname} has a J-CHAIN but {rel} has no {key}")
            continue
        bnet = {}
        for net, pins in doc["nets"].items():
            for p in pins:
                bnet[p] = (net.lstrip("/"), len(pins))
        for k in range(1, 13):
            want = lnet.get(f"{key}.{k}")
            main = lnet.get(f"J-CHAIN-MAIN-{side}.{13 - k}")
            if want is None or want != main:
                problems.append(f"chain: {rel} puts {key}.{k} on {want}, but J-CHAIN-MAIN-{side}.{13 - k} "
                                f"(the same conductor, -RN2) on {main}")
            got, size = bnet.get(f"{jref}.{k}", (None, 0))
            if size == 1:
                # unconnected on the board: fine only on a conductor nothing else uses
                spare = want is not None and all(isinstance(n, str) and n.startswith("J-CHAIN-")
                                                 for n in loom["nets"][want])
                if not spare:
                    problems.append(f"chain: {bname} leaves {jref}.{k} (J-CHAIN) unconnected; {rel} puts {key}.{k} on {want}")
            elif got != want:
                problems.append(f"chain: {bname} wires {jref}.{k} (J-CHAIN) to {got}; {rel} puts {key}.{k} "
                                f"(main-board pin {13 - k}) on {want}")
    return problems


# The main board's names for the loom's conductors: the chain's return IS its ground
# pour (hardware/nets.yaml GND_CHAIN).
MAIN_ALIAS = {"GND_CHAIN": "PWR_GND"}


def check_chain_main(doc, js, loom, lnet, rel):
    """The main board's two J-CHAIN headers against the loom's J-CHAIN-MAIN-<LH|RH>: pin k
    on the net the loom puts it on (under the main board's name for it), a pin left
    unconnected only on a spare conductor. Which header is which is read from its rail
    pin, so a swapped pair of headers is two wrong rails, not a pass."""
    problems = []
    bnet = {}
    for net, pins in doc["nets"].items():
        for p in pins:
            bnet[p] = (net.lstrip("/"), len(pins))
    seen = set()
    for jref in js:
        rail = bnet.get(f"{jref}.10", (None, 0))[0]
        side = {"V3V3_CHAIN_LH": "LH", "V3V3_CHAIN_RH": "RH"}.get(rail)
        if side is None or side in seen:
            problems.append(f"chain: main-board {jref} (J-CHAIN) pin 10 is on {rail}, not one ribbon's own rail")
            continue
        seen.add(side)
        key = f"J-CHAIN-MAIN-{side}"
        for k in range(1, 13):
            want = lnet.get(f"{key}.{k}")
            want = MAIN_ALIAS.get(want, want)
            got, size = bnet.get(f"{jref}.{k}", (None, 0))
            if size == 1:
                spare = want is not None and all(isinstance(n, str) and n.startswith("J-CHAIN-")
                                                 for n in loom["nets"].get(want, []))
                if not spare:
                    problems.append(f"chain: main-board leaves {jref}.{k} (J-CHAIN) unconnected; {rel} puts {key}.{k} on {want}")
            elif got != want:
                problems.append(f"chain: main-board wires {jref}.{k} (J-CHAIN) to {got}; {rel} puts {key}.{k} on {want}")
    if seen != {"LH", "RH"}:
        problems.append(f"chain: main-board has J-CHAIN for {sorted(seen)}, not both ribbons")
    return problems


# A header soldered through two boards is one conductor per pin: pin k on one board is pin k
# on the other (ADR 0023). Each pair of boards it joins, by BOM row.
THROUGH = {"J-B2B-MOD": ("module-main", "module-jack")}
SPI_LINK = os.path.join(ROOT, "hardware", "interfaces", "spi-link", "netlist.yaml")


def check_through(board_docs):
    """J-B2B-MOD: every pin on the same net, by name, on both boards it is soldered into, and
    no pin left open on one board that the other uses. A pin moved on one sheet only is a
    wrong conductor on the other board, which no ERC sees - each board is clean alone."""
    docs = dict(board_docs)
    problems = []
    for row, (a, b) in THROUGH.items():
        pins = []
        for bname in (a, b):
            doc = docs.get(bname)
            if doc is None:
                problems.append(f"through: {row} joins {a} and {b}, but there is no board {bname}")
                pins = None
                break
            js = [r for r, c in doc["components"].items() if c.get("of") == row]
            if len(js) != 1:
                problems.append(f"through: {bname} has {len(js)} {row} parts, not one")
                pins = None
                break
            m = {}
            for net, members in doc["nets"].items():
                for p in members:
                    if isinstance(p, str) and p.startswith(js[0] + "."):
                        m[p.split(".", 1)[1]] = (net.lstrip("/"), len(members))
            pins.append((js[0], m))
        if not pins:
            continue
        (ja, ma), (jb, mb) = pins
        for k in sorted(set(ma) | set(mb), key=lambda x: (len(x), x)):
            na, sa = ma.get(k, (None, 0))
            nb, sb = mb.get(k, (None, 0))
            if na != nb and not (sa <= 1 and sb <= 1):
                problems.append(f"through: {row} pin {k} is {na} on {a} ({ja}) but {nb} on {b} ({jb})")
    return problems


def check_umbilical_mod(board_docs):
    """The module main board's etherCON against the umbilical's own sheet: pin k of J-UMB-MOD
    (row J-UMBILICAL) on the net hardware/interfaces/spi-link puts J-UMB-MOD.k on, by name."""
    doc = dict(board_docs).get("module-main")
    if doc is None:
        return []
    link = yaml.safe_load(open(SPI_LINK))
    want = {}
    for net, members in link["nets"].items():
        for p in members:
            if isinstance(p, str) and p.startswith("J-UMB-MOD."):
                want[p.split(".", 1)[1]] = net
    js = [r for r, c in doc["components"].items() if c.get("of") == "J-UMBILICAL"]
    if len(js) != 1:
        return [f"umbilical: module-main has {len(js)} J-UMBILICAL parts, not one"]
    got = {}
    for net, members in doc["nets"].items():
        for p in members:
            if isinstance(p, str) and p.startswith(js[0] + "."):
                got[p.split(".", 1)[1]] = net.lstrip("/")
    rel = os.path.relpath(SPI_LINK, ROOT)
    return [f"umbilical: module-main wires {js[0]}.{k} (J-UMBILICAL) to {got.get(k)}; {rel} puts J-UMB-MOD.{k} on {w}"
            for k, w in sorted(want.items()) if got.get(k) != w]


def board_outputs(d):
    """Every generated file beside a board: renders and fab/. What the ledger must know."""
    out = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".sch.png") or ".pcb-" in f]
    fab = os.path.join(d, "fab")
    if os.path.isdir(fab):
        out += [os.path.join(fab, f) for f in os.listdir(fab)]
    return out


def cmd_check():
    bad = []
    board_docs = []
    for d in migrated_circuits():
        text, problems = export_circuit(d)
        bad += [f"{os.path.relpath(d, ROOT)}: {p}" for p in problems]
        if open(os.path.join(d, "netlist.yaml")).read() != text:
            bad.append(f"{os.path.relpath(d, ROOT)}/netlist.yaml is STALE against its sheet - run: "
                       f"python3 tools/kicad.py export {os.path.relpath(d, ROOT)}")
    for d in boards():
        text, checks = export_board(d)
        p = os.path.join(d, "board-netlist.yaml")
        if not os.path.exists(p) or open(p).read() != text:
            bad.append(f"{os.path.relpath(p, ROOT)} is STALE - run: python3 tools/kicad.py export {os.path.relpath(d, ROOT)}")
        bad += [f"{os.path.relpath(d, ROOT)}: ERC {c}" for c in checks if c.startswith("error")]
        board_docs.append((os.path.basename(d), yaml.safe_load(text)))
        pcbfile = os.path.join(d, os.path.basename(d) + ".kicad_pcb")
        if os.path.exists(pcbfile):
            # the board's layout: KiCad's DRC with schematic parity, and the body CAD's
            # switch places (tools/pcb.py check) - any error is this check's error too
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "pcb.py"), "check", os.path.relpath(d, ROOT)],
                               capture_output=True, text=True)
            bad += [f"{os.path.relpath(pcbfile, ROOT)}: {l.strip()}" for l in r.stdout.splitlines() if l.strip().startswith("error")]
            if r.returncode and not any(l.strip().startswith("error") for l in r.stdout.splitlines()):
                bad.append(f"{os.path.relpath(pcbfile, ROOT)}: pcb check failed:\n{r.stdout}{r.stderr}")
    bad += check_allocation(board_docs)
    bad += check_chain(board_docs)
    bad += check_through(board_docs)
    bad += check_umbilical_mod(board_docs)
    rows = ledger_rows()
    stale = {}
    for r in rows.values():
        png = os.path.join(ROOT, r["render"])
        if not os.path.exists(png):
            bad.append(f"{r['render']} is missing")
            continue
        if hashlib.sha1(open(png, "rb").read()).hexdigest() != r["sha1"]:
            bad.append(f"{r['render']} was edited after it was rendered")
        for item in r["inputs"].split():
            path, b = item.rsplit("@", 1)
            if blob(os.path.join(ROOT, path)) != b:
                # a PCB render or fab/ file is remade by pcb.py from the BOARD's directory;
                # a sheet render by this tool from its own. One line per remedy (K7-4).
                d = os.path.dirname(r["render"])
                if ".pcb-" in r["render"] or "/fab/" in r["render"]:
                    fix = "python3 tools/pcb.py render " + (os.path.dirname(d) if d.endswith("/fab") else d)
                else:
                    fix = "python3 tools/kicad.py render " + d
                stale.setdefault(fix, []).append((r["render"], path))
                break
    for fix, items in sorted(stale.items()):
        why = sorted({p for _, p in items})
        bad.append(f"{items[0][0]}{f' and {len(items) - 1} more' if len(items) > 1 else ''} STALE: "
                   f"{', '.join(why)} changed - run: {fix}")
    # a generated file nobody generated: a stray Gerber is uploaded with the rest (K7-6)
    for d in boards() + migrated_circuits():
        for f in board_outputs(d):
            if os.path.relpath(f, ROOT) not in rows:
                bad.append(f"{os.path.relpath(f, ROOT)} is in no ledger row - no tool made it; delete it, "
                           f"or re-render: python3 tools/{'pcb' if '.pcb-' in f or '/fab/' in f else 'kicad'}.py render "
                           f"{os.path.relpath(d, ROOT)}")
    n = len(migrated_circuits()), len(boards()), len(rows)
    if bad:
        print(f"kicad: FAIL - {len(bad)} problem(s) over {n[0]} source sheet(s), {n[1]} board(s), {n[2]} render(s)")
        for b in bad:
            print("  " + b)
        return 1
    print(f"kicad: PASS - {n[0]} source sheet(s), {n[1]} board(s), {n[2]} render(s) match their sources")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "set-field":
        n = set_field(os.path.join(ROOT, sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5])
        print(f"kicad: set {sys.argv[4]} on {sys.argv[3]} ({n} unit(s)) in {sys.argv[2]}")
        sys.exit(0)
    if len(sys.argv) >= 2 and sys.argv[1] == "check":
        sys.exit(cmd_check())
    if len(sys.argv) == 3 and sys.argv[1] in ("export", "render"):
        sys.exit({"export": cmd_export, "render": cmd_render}[sys.argv[1]](sys.argv[2]))
    print(__doc__)
    sys.exit(2)
