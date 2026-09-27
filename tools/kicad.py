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
tools/cad.py for the body.

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
        comps[ref] = {"value": find(c, "value")[0][1], "fields": fields}
    nets = []
    for n in find(find(tree, "nets")[0], "net"):
        nodes = [(find(x, "ref")[0][1], find(x, "pin")[0][1]) for x in find(n, "node")]
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
        for k in ("From", "To", "Figure"):
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
        c["value"] = comps[ref]["value"]
        if f.get("Drawn_as"):
            c["drawn_as"] = f["Drawn_as"]
        c["pins"] = [int(n) if n.isdigit() else n for n in names]
        if f.get("Note"):
            c["note"] = f["Note"]
        if not names:
            problems.append(f"{ref}: no Pins field - every part on a source sheet names its pins")
        out_comps[ref] = c
    out_nets, ext = {}, []
    for kname, nodes in nets:
        pins = [f"{r}.{maps.get(r, {}).get(p, p)}" for r, p in nodes if not r.startswith("#")]
        if not pins:
            continue
        bare = kname.lstrip("/")
        if kname.startswith("unconnected-") or kname.startswith("Net-("):
            if len(pins) == 1:
                bare = pins[0].split(".", 1)[1]       # a lone no-connect pin is named after the pin
                ext.append(bare)
            else:
                problems.append(f"net of {pins} has no label - name every net on a source sheet")
                continue
        members = [{"port": bare}] if bare in ports else []
        members += pins
        out_nets[bare] = members
        if bare in endpoints:
            ext.append(bare)
    for pname in ports:
        if pname not in out_nets:
            problems.append(f"port {pname} labels no net with a pin")
    doc = {k: meta[k] for k in ("circuit", "title", "page", "replicated") if k in meta}
    doc["ports"] = ports
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
    for k in [k for k in rows if os.path.dirname(k).startswith(rel) and (".pcb-" in k or "/fab/" in k) == (kind == "pcb")]:
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
        for u in [r for r in doc["components"] if r.startswith("U-KEYS-")]:
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
                    pu = [p for p in net if p.startswith("R-KEY-PU-") and p.endswith(".2")]
                    got.append(pu[0][len("R-KEY-PU-"):-2] if len(pu) == 1 else "?")
            if tuple(got) not in rows:
                problems.append(f"allocation: {bname} wires {u} as {' '.join(got)} (H..A), which is no row of allocation.yaml")
    return problems


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
    rows = ledger_rows()
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
                bad.append(f"{r['render']} is STALE: {path} changed - run: python3 tools/kicad.py render "
                           f"{os.path.dirname(r['render'])}")
                break
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
