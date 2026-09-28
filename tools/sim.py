#!/usr/bin/env python3
"""SPICE simulations of the circuits, built from their own netlists (ngspice).

    python3 tools/sim.py run [<sim dir> ...]   # run every sim/sims.yaml (or those named); write results.yaml
    python3 tools/sim.py check                 # (no ngspice) every results.yaml matches its inputs and passed
    python3 tools/sim.py show <sim dir>        # print a results.yaml as a table

A circuit's `sim/` directory holds `sims.yaml` - what is simulated, what each run
must show, and why - and the deck templates it names. **No part value is written
in a sim.** Each deck's `{{R-KEY-PU}}` is read from the circuit's netlist.yaml
(exported from its KiCad sheet), so a value changed on the sheet reaches the
simulation, and `check` fails until the sims are re-run on it. Model parameters
that are not part values (a threshold ratio, an input capacitance) live in
`params:`, each with its source; figures are cited as `fig['key-release-time']`
from config/figures.yaml, never restated.

CORNERS, NOT A GUESS. Every parameter in `vary:` has a relative range about its
nominal. Each sim runs at the nominal and at every combination of the range ends
(2^n corners), and each measure is reported at the nominal, its minimum and its
maximum, with the corner that gave each. For these circuits - RC networks and
thresholds, monotonic in every parameter - the corners bound the result; a
Monte Carlo would only fill in the middle.

WHAT A RESULT IS WORTH. A SPICE run proves the arithmetic and the wiring against
the models it was given, no more. Where a model is behavioural (a Schmitt input
as its thresholds, a switch as two resistances) sims.yaml says so, and the
thresholds are the datasheet's, not a model's. `results.yaml` is GENERATED: it
records the ngspice version, a hash of every input, every measure and every
assertion's outcome; `check` recomputes the hashes, so a changed value, deck,
figure or this tool marks the results stale.

A board's sims.yaml may also `generate: board` a deck from its board-netlist.yaml:
every part on the board by its BOM row (`parts:` says what each row is in SPICE),
the nets the rest of the chain drives (`drive:`), so a wiring or value mistake on
the board shows up in the simulation of the board itself.
"""
import glob
import hashlib
import itertools
import math
import os
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(ROOT, "config", "figures.yaml")
SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "": 1.0,
      "k": 1e3, "K": 1e3, "M": 1e6, "meg": 1e6, "G": 1e9}


# ------------------------------------------------------------------ values

def part_value(text):
    """A part's value as a number: '2k2 1%' -> 2200, '47nF' -> 47e-9, '100R 1%' -> 100,
    '10uF DNP' -> 10e-6. The tolerance ('1%') is separate: part_tol()."""
    t = text.strip().split()[0]
    m = re.fullmatch(r"(\d+)([pnuµmkKMGR])(\d+)", t)          # 2k2, 4R7
    if m:
        mult = 1.0 if m.group(2) == "R" else SI[m.group(2)]
        return float(f"{m.group(1)}.{m.group(3)}") * mult
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(meg|[pnuµmkKMG])?(F|R|Ω|ohm|H)?", t)
    if not m:
        raise ValueError(f"cannot read a value from {text!r}")
    return float(m.group(1)) * SI[m.group(2) or ""]


def part_tol(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    return float(m.group(1)) / 100 if m else None


def figure_value(text):
    """A register figure's leading number in SI: '138.7 us' -> 1.387e-4, '1.43 mA per...' -> 1.43e-3."""
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*(meg|[pnuµmkMG])?\s*(s|us|µs|ms|ns|A|mA|uA|V|mV|Hz|kHz|MHz|ohm|Ω|F)?", text)
    if not m:
        raise ValueError(f"no number in {text!r}")
    v = float(m.group(1))
    unit = m.group(3) or ""
    pre = m.group(2) or ""
    if unit in ("us", "µs", "ms", "ns", "mA", "uA", "mV", "kHz", "MHz"):
        pre, unit = unit[0].replace("µ", "u"), unit[1:]
    return v * SI[pre]


def figures():
    f = yaml.safe_load(open(FIGURES))
    items = f["figures"] if isinstance(f, dict) and "figures" in f else f
    return {it["id"]: it for it in items}


def inc_path(simdir, inc):
    """An include beside the sims.yaml, or a banked model by its repo path (datasheets/...)."""
    here = os.path.join(simdir, inc)
    return here if os.path.exists(here) else os.path.join(ROOT, inc)


def spice_num(v):
    return f"{v:.6g}"


# ------------------------------------------------------------------ the sims

def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def load(simdir):
    """A sims.yaml. `params_from:` names other sims.yaml files whose params: and derived:
    this one takes (its own override them), so a model parameter - a threshold ratio, an
    input capacitance - is stated once, where the circuit it belongs to is simulated."""
    spec = yaml.safe_load(open(os.path.join(simdir, "sims.yaml")))
    spec["_dir"] = simdir
    params, derived = {}, {}
    for src in spec.get("params_from", []):
        other = yaml.safe_load(open(os.path.join(ROOT, src)))
        params.update(other.get("params") or {})
        derived.update(other.get("derived") or {})
    params.update(spec.get("params") or {})
    derived.update(spec.get("derived") or {})
    spec["params"], spec["derived"] = params, derived
    return spec


def bom_value(row):
    """A row's Value from hardware/bom.csv (generated from the fragments): for parts on
    another board, which this circuit's netlist does not carry (R-CHAIN-SER)."""
    import csv
    for r in csv.reader(open(os.path.join(ROOT, "hardware", "bom.csv"), newline="")):
        if r and r[0] == row:
            return r[2]
    raise SystemExit(f"sim: `values: bom:` names {row!r}, which hardware/bom.csv has no row for")


def drc_value(rule):
    """A number the body CAD prints in mechanical/drc.echo, by its rule's name: the
    first number after the name (a derived length, say), so it is cited, not restated."""
    for line in open(os.path.join(ROOT, "mechanical", "drc.echo")):
        if f'"{rule}"' in line:
            m = re.search(re.escape(f'"{rule}"') + r",\s*\[?\s*(-?[\d.]+(?:e[-+]?\d+)?)", line)
            if m:
                return float(m.group(1))
    raise SystemExit(f"sim: mechanical/drc.echo has no numeric rule {rule!r}")


def param_value(p):
    v = p["value"]
    if isinstance(v, dict) and "drc" in v:
        return drc_value(v["drc"]) * float(v.get("scale", 1))
    try:
        return float(v)
    except (TypeError, ValueError):
        return part_value(str(v))


def netlist_parts(spec):
    """{row: {'value': number, 'tol': fraction or None, 'text': ...}} from the circuit's netlist.yaml
    (a circuit's components are keyed by row) or a board's (keyed by reference, with `of:`)."""
    path = os.path.join(ROOT, spec["values"]["netlist"])
    doc = yaml.safe_load(open(path))
    out = {}
    for ref, c in doc["components"].items():
        row = c.get("of", ref)
        try:
            v = part_value(str(c["value"]))
        except ValueError:
            continue
        out.setdefault(row, {"value": v, "tol": part_tol(str(c["value"])), "text": str(c["value"])})
    for row in spec["values"].get("bom", []):
        text = bom_value(row)
        out[row] = {"value": part_value(text), "tol": part_tol(text), "text": text}
    # counts by row, for derived values: v['n:SW1-n']
    from collections import Counter
    for row, k in Counter(c.get("of", r) for r, c in doc["components"].items()).items():
        out[f"n:{row}"] = {"value": float(k), "tol": None, "text": str(k)}
    return out, doc


def inputs_of(spec):
    """Every file the results depend on, with its hash: this tool, sims.yaml, the decks, the
    netlist and anything generated from; and the value of every figure the sims cite."""
    d = spec["_dir"]
    files = [os.path.abspath(__file__), os.path.join(d, "sims.yaml"),
             os.path.join(ROOT, spec["values"]["netlist"])]
    for s in spec["sims"]:
        if s.get("deck"):
            files.append(os.path.join(d, s["deck"]))
    for inc in spec.get("include", []):
        files.append(inc_path(d, inc))
    for src in spec.get("params_from", []):
        files.append(os.path.join(ROOT, src))
    h = {os.path.relpath(f, ROOT): sha(f) for f in files}
    figs = figures()
    text = "".join(open(f).read() for f in files if f.endswith(".yaml") and "sims" in os.path.basename(f))
    cited = sorted(set(re.findall(r"fig\['([^']+)'\]", text)))
    for row in spec["values"].get("bom", []):
        h[f"bom:{row}"] = bom_value(row)
    for name, p in (spec.get("params") or {}).items():
        if isinstance(p.get("value"), dict) and "drc" in p["value"]:
            h[f"drc:{p['value']['drc']}"] = str(drc_value(p["value"]["drc"]))
    for fid in cited:
        if fid not in figs:
            raise SystemExit(f"sim: {os.path.relpath(d, ROOT)}/sims.yaml cites figure {fid!r}, which is not in config/figures.yaml")
        h[f"figure:{fid}"] = str(figs[fid]["value"])
    return h


def corners(spec, parts, only=None):
    """[(name, {param: value})]: the nominal, then every combination of the range ends.
    `only`, a sim's own `vary:` list, limits the corners to the parameters that move it."""
    nominal, ranges = {}, {}
    for name, p in (spec.get("params") or {}).items():
        nominal[name] = param_value(p)
    for name, v in (spec.get("vary") or {}).items():
        if only is not None and name not in only:
            continue
        if name in parts:
            base = parts[name]["value"]
        else:
            base = nominal[name]
        tol = v["tol"]
        if tol == "from-value":
            t = parts[name]["tol"]
            if t is None:
                raise SystemExit(f"sim: {name}'s value {parts[name]['text']!r} states no tolerance; give `tol:` a range")
            tol = [-t, t]
        ranges[name] = (base * (1 + tol[0]), base * (1 + tol[1]))
        nominal[name] = base
    for row, p in parts.items():
        nominal.setdefault(row, p["value"])
    out = [("nominal", dict(nominal))]
    names = sorted(ranges)
    for ends in itertools.product((0, 1), repeat=len(names)):
        c = dict(nominal)
        label = []
        for n, e in zip(names, ends):
            c[n] = ranges[n][e]
            label.append(f"{n}{'-' if e == 0 else '+'}")
        out.append((" ".join(label), c))
    return out


def derive(spec, values):
    """`derived:` entries, in order: python expressions over the values so far (math allowed)."""
    v = dict(values)
    for name, expr in (spec.get("derived") or {}).items():
        v[name] = eval(expr, {"__builtins__": {}, "math": math, "min": min, "max": max}, {"v": v})
    return v


def fill(template, values):
    def sub(m):
        k = m.group(1).strip()
        if k not in values:
            raise SystemExit(f"sim: the deck asks for {{{{{k}}}}}, which is no part row, param or derived value")
        return spice_num(values[k])
    return re.sub(r"\{\{([^}]+)\}\}", sub, template)


def spice_net(name, table):
    if name not in table:
        table[name] = "n" + re.sub(r"[^A-Za-z0-9_]", "_", name.lstrip("/")) if name not in ("GND", "0") else "0"
    return table[name]


def board_deck(spec, doc, body):
    """A deck for the whole board from its board-netlist.yaml: every part by its BOM row
    (`parts:` gives the SPICE line for each row, with {ref}, {value}, {sheet} and each pin's
    net as {pin}), the nets the rest of the chain drives (`drive:`), and `body` (the
    analysis and measures, from the sim's own deck). Nets are named n<name>; the ground
    net (`ground:`) is node 0. The sim's deck names a net as <net:/KEY_LH1>, and a
    `drive:` line its own net as <net>."""
    table = {spec["ground"]: "0"}
    pinnet = {}
    for net, pins in doc["nets"].items():
        for p in pins:
            pinnet[p] = spice_net(net, table)
    lines = [f"* {spec['title']} - generated by tools/sim.py from {spec['values']['netlist']}", "*"]
    for ref, c in sorted(doc["components"].items()):
        tmpl = spec["parts"].get(c["of"])
        if tmpl is None:
            raise SystemExit(f"sim: {ref} is a {c['of']}, which `parts:` does not say how to simulate "
                             f"(give it a SPICE line, or \"\" to leave it out and say why)")
        if not tmpl:
            lines.append(f"* {ref} ({c['of']}) not simulated: see sims.yaml")
            continue
        # {row} is the part's value as a corner varies it: {{R-KEY-PU}}, filled per run
        fields = {"ref": ref, "value": c["value"], "sheet": c.get("sheet", ""), "row": "{{" + c["of"] + "}}"}
        for p in c["pins"]:
            fields[str(p)] = pinnet.get(f"{ref}.{p}", f"nc_{ref}_{p}")
        try:
            fields["value"] = spice_num(part_value(str(c["value"])))
        except ValueError:
            pass
        def field(m):
            if m.group(1) not in fields:
                raise SystemExit(f"sim: `parts:` {c['of']}'s line asks for {{{m.group(1)}}}, which {ref} does not have "
                                 f"(its pins: {', '.join(map(str, c['pins']))})")
            return fields[m.group(1)]
        lines.append(re.sub(r"(?<!\{)\{([^{}]+)\}(?!\})", field, tmpl))
    for net, tmpl in (spec.get("drive") or {}).items():
        if net not in table:
            raise SystemExit(f"sim: `drive:` names net {net!r}, which the board does not have")
        lines.append(tmpl.replace("<net>", table[net]))
    lines.append("*")
    lines.append("* nets: " + ", ".join(f"{k}={v}" for k, v in sorted(table.items())))

    def net(m):
        if m.group(1) not in table:
            raise SystemExit(f"sim: the deck names net {m.group(1)!r}, which the board does not have")
        return table[m.group(1)]
    return "\n".join(lines) + "\n" + re.sub(r"<net:([^>]+)>", net, body)


def backswing(wave, level, rising, t_from, t_to):
    """How far a waveform swings BACK after it first crosses `level` (searched from
    `t_from`), until `t_to`: on a
    rising edge the most it falls below its own running maximum, on a falling edge the
    most it rises above its running minimum. A Schmitt input double-clocks only if an
    edge swings back through its hysteresis after crossing its threshold, wherever in
    the datasheet's spread that threshold sits - so this, against the hysteresis's
    minimum, is the test; a fixed pair of threshold extremes is not (they overlap)."""
    t, v = wave
    started, run, worst = False, None, 0.0
    for ti, vi in zip(t, v):
        if ti < t_from:
            continue
        if ti > t_to:
            break
        if not started:
            started = (vi >= level) if rising else (vi <= level)
            run = vi
            continue
        run = max(run, vi) if rising else min(run, vi)
        worst = max(worst, (run - vi) if rising else (vi - run))
    return worst if started else float("inf")


POST = {"backswing": backswing}


def ngspice(deck, post=None, values=None):
    """Run a deck; return its measures (and `post:` ones, computed on waveforms the deck
    writes with `wrdata <name>.dat <vector>`)."""
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "deck.cir")
        open(p, "w").write(deck)
        r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True, cwd=t, timeout=300)
        waves = {}
        for f in glob.glob(os.path.join(t, "*.dat")):
            rows = [l.split() for l in open(f) if l.strip()]
            waves[os.path.basename(f)[:-4]] = ([float(x[0]) for x in rows], [float(x[1]) for x in rows])
    out = r.stdout + "\n" + r.stderr
    meas = {}
    for line in out.splitlines():
        m = re.match(r"^\s*([a-z][a-z0-9_]*)\s*=\s*([-+]?\d[\d.]*(?:e[-+]?\d+)?)", line.strip(), re.I)
        if m:
            meas[m.group(1).lower()] = float(m.group(2))
    errors = [l for l in out.splitlines() if re.search(r"error|failed|not found|singular", l, re.I)
              and "no error" not in l.lower()]
    for name, expr in (post or {}).items():
        env = {"w": waves, "p": values or {}, **POST}
        meas[name] = float(eval(expr, {"__builtins__": {}}, env))
    return meas, errors, out


def ngspice_version():
    r = subprocess.run(["ngspice", "-v"], capture_output=True, text=True)
    m = re.search(r"ngspice-(\S+)", r.stdout + r.stderr)
    return m.group(1) if m else "?"


def run(simdir):
    spec = load(simdir)
    parts, doc = netlist_parts(spec)
    figs = {k: figure_value(str(v["value"])) for k, v in figures().items()
            if re.match(r"\s*-?\d", str(v["value"]))}
    results = {}
    for s in spec["sims"]:
        template = open(os.path.join(simdir, s["deck"])).read()
        if spec.get("generate") == "board":
            template = board_deck(spec, doc, template)
        # model libraries, inlined (the deck runs in a scratch directory), filled like the deck
        lib = "".join(open(inc_path(simdir, inc)).read() + "\n" for inc in spec.get("include", []))
        template = template.replace("\n.end", "\n" + lib + ".end") if lib else template
        per = {}
        for label, values in corners(spec, parts, s.get("vary")):
            v = derive(spec, {**values, **{k: fv for k, fv in (s.get("set") or {}).items()}})
            meas, errors, out = ngspice(fill(template, v), s.get("post"), v)
            missing = [m for m in s["measures"] if m not in meas]
            # a run that diverged reports a number too: never record one
            wild = [f"{m} = {meas[m]:g}" for m in s["measures"] if m in meas
                    and (not math.isfinite(meas[m]) or abs(meas[m]) > 1e12)]
            if wild:
                errors = errors + [f"the run diverged: {', '.join(wild)} - set .options method=gear, or a smaller step"]
            if errors or missing:
                raise SystemExit(f"sim: {os.path.relpath(simdir, ROOT)} {s['name']} at {label}: "
                                 f"{'; '.join(errors[:5])} {'missing measures ' + str(missing) if missing else ''}\n"
                                 + "\n".join(out.splitlines()[-30:]))
            per[label] = meas
        res = {"corners": len(per), "measures": {}}
        stats = {"nom": {}, "min": {}, "max": {}}
        for m in s["measures"]:
            vals = {lab: per[lab][m] for lab in per}
            lo = min(vals, key=vals.get)
            hi = max(vals, key=vals.get)
            res["measures"][m] = {"nominal": float(f"{vals['nominal']:.6g}"),
                                  "min": float(f"{vals[lo]:.6g}"), "min_at": lo,
                                  "max": float(f"{vals[hi]:.6g}"), "max_at": hi}
            stats["nom"][m], stats["min"][m], stats["max"][m] = vals["nominal"], vals[lo], vals[hi]
        from collections import Counter
        env = {"nom": stats["nom"], "min": stats["min"], "max": stats["max"], "fig": figs,
               "n": Counter(c.get("of", r) for r, c in doc["components"].items()),
               "p": derive(spec, corners(spec, parts)[0][1]), "abs": abs, "math": math}
        res["asserts"] = []
        for a in s.get("asserts") or []:
            ok = bool(eval(a["expr"], {"__builtins__": {}}, env))
            res["asserts"].append({"expr": a["expr"], "why": a["why"], "pass": ok})
        results[s["name"]] = res
    out = {"inputs": inputs_of(spec), "ngspice": ngspice_version(), "sims": results}
    path = os.path.join(simdir, "results.yaml")
    head = (f"# GENERATED by tools/sim.py run - DO NOT EDIT. The simulations in sims.yaml, at the\n"
            f"# nominal and every tolerance corner; `python3 tools/sim.py check` holds this file to\n"
            f"# its inputs (hashed below), so a value changed on the sheet makes it stale.\n\n")
    open(path, "w").write(head + yaml.safe_dump(out, sort_keys=False, width=120, allow_unicode=True))
    bad = [(n, a) for n, r in results.items() for a in r["asserts"] if not a["pass"]]
    print(f"sim: {os.path.relpath(simdir, ROOT)}: {sum(r['corners'] for r in results.values())} runs, "
          f"{sum(len(r['asserts']) for r in results.values())} assertions, {len(bad)} failed")
    for n, a in bad:
        print(f"  FAIL {n}: {a['expr']} - {a['why']}")
    return 1 if bad else 0


def sim_dirs():
    return sorted(os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, "hardware", "**", "sim", "sims.yaml"), recursive=True))


def check():
    problems = []
    for d in sim_dirs():
        rel = os.path.relpath(d, ROOT)
        path = os.path.join(d, "results.yaml")
        if not os.path.exists(path):
            problems.append(f"{rel}: never run - python3 tools/sim.py run {rel}")
            continue
        got = yaml.safe_load(open(path))
        try:
            want = inputs_of(load(d))
        except SystemExit as e:
            problems.append(str(e))
            continue
        moved = sorted(k for k in set(want) | set(got.get("inputs", {})) if want.get(k) != got.get("inputs", {}).get(k))
        if moved:
            problems.append(f"{rel}: results are stale - {', '.join(moved)} changed since the run; "
                            f"python3 tools/sim.py run {rel}")
        for name, r in (got.get("sims") or {}).items():
            for a in r.get("asserts", []):
                if not a["pass"]:
                    problems.append(f"{rel}: {name} failed: {a['expr']} - {a['why']}")
    for p in problems:
        print("  " + p)
    print(f"sim: {'FAIL' if problems else 'PASS'} - {len(sim_dirs())} sim dir(s), {len(problems)} problem(s)")
    return 1 if problems else 0


def show(simdir):
    r = yaml.safe_load(open(os.path.join(simdir, "results.yaml")))
    for name, s in r["sims"].items():
        print(f"== {name} ({s['corners']} runs)")
        for m, v in s["measures"].items():
            print(f"  {m:18} nominal {v['nominal']:<12.5g} min {v['min']:<12.5g} max {v['max']:<12.5g} (max at {v['max_at']})")
        for a in s["asserts"]:
            print(f"  {'PASS' if a['pass'] else 'FAIL'} {a['expr']}  - {a['why']}")


def main(argv):
    if not argv or argv[0] not in ("run", "check", "show"):
        print(__doc__)
        return 2
    if argv[0] == "check":
        return check()
    if argv[0] == "show":
        show(os.path.abspath(argv[1]))
        return 0
    dirs = [os.path.abspath(a) for a in argv[1:]] or sim_dirs()
    return max([run(d) for d in dirs] or [0])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
