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

VENDOR MODELS. `models:` names SPICE libraries banked in datasheets/ (each with its
MANIFEST row and SHA-256); each is `.include`d by path, verbatim and unfilled, and its
hash is an input. TI's PSpice macromodels need `spiceinit: [set ngbehavior=psa]`,
which is written to the run's .spiceinit - inside .control is too late. A part with no
runnable vendor model is behavioural, built from its banked datasheet, and sims.yaml
says which figure each parameter comes from. `values: netlist:` may be a list, for a
sim that spans circuits; every component is also addressable by its own reference
({{R2}}, {{C-CM-IN+}}), so two parts of one row can sit at opposite tolerance ends.

SWEEPS. A sim's `sweep: {param: [v1, v2, ...]}` runs it once per value (and per
combination, for several), each as its own sim named `name[param=v]`, with its own
corners and asserts: a stability sim sweeps the page's load-capacitance range this way.

MEASURES ON WAVEFORMS (`post:`, over files the deck writes with `wrdata <name>.dat`):
  phase_margin(w['tdb'], w['tph'])  the loop's phase margin in degrees, the least at
      any 0 dB crossing of |T|; `tdb` is 20log|T| and `tph` its phase in degrees, of
      T = -V(return)/V(injected). THE STATED BREAK: the loop is opened at a high-
      impedance node - an op-amp input - by a 1 GH inductor that carries the DC
      operating point, and the AC test signal enters through a 1 GF capacitor, so the
      feedback network stays loaded by the input it drives and nothing else.
  crossover(w['tdb'])        the frequency of the first 0 dB crossing of |T|
  overshoot(w['v'], t0, t1)  percent, of a step at t0: the largest excursion past the
      final value (the mean of the last 5 % before t1) over the step's size
  settling(w['v'], t0, t1, band)  seconds from t0 until v stays within +-band of final
  at(w['x'], x0)             a waveform's value at x0, interpolated (a CMRR in dB at
      50 Hz, say)
  peak(w['v'], t0, t1) / trough(...)  the largest / smallest value in a window
  cross(w['v'], level, t0)   the first time after t0 that v crosses level (either way)
A SIMULATED PHASE MARGIN IS A SCREEN WITH A +-10 DEGREE BAR, not a spec: a vendor
macromodel runs optimistic against its own tabulated figures. Assert against it so.
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


def netlists(spec):
    n = spec["values"]["netlist"]
    return [n] if isinstance(n, str) else list(n)


def netlist_parts(spec):
    """{row: {'value': number, 'tol': fraction or None, 'text': ...}} from the circuit's netlist.yaml
    (a circuit's components are keyed by row) or a board's (keyed by reference, with `of:`).
    Several netlists merge: rows are unique across the corpus. Every component is also
    keyed by its own reference where that differs from its row, so a deck can put two
    parts of one row at opposite ends of their tolerance ({{R2}}, {{R3}})."""
    out, docs = {}, []
    for path in netlists(spec):
        doc = yaml.safe_load(open(os.path.join(ROOT, path)))
        docs.append(doc)
        for ref, c in doc["components"].items():
            row = c.get("of", ref)
            if "value" not in c:
                continue                      # a row with no value yet (R-ILIM: "from E6")
            try:
                v = part_value(str(c["value"]))
            except ValueError:
                continue
            entry = {"value": v, "tol": part_tol(str(c["value"])), "text": str(c["value"])}
            out.setdefault(row, entry)
            if ref != row:
                out.setdefault(ref, dict(entry))
    for row in spec["values"].get("bom", []):
        text = bom_value(row)
        out[row] = {"value": part_value(text), "tol": part_tol(text), "text": text}
    # counts by row, for derived values: v['n:SW1-n']
    from collections import Counter
    doc = docs[0] if len(docs) == 1 else {"components": {f"{i}:{r}": c for i, d in enumerate(docs)
                                                         for r, c in d["components"].items()}}
    for row, k in Counter(c.get("of", r.split(":", 1)[-1]) for r, c in doc["components"].items()).items():
        out.setdefault(f"n:{row}", {"value": float(k), "tol": None, "text": str(k)})
    return out, doc


def inputs_of(spec):
    """Every file the results depend on, with its hash: this tool, sims.yaml, the decks, the
    netlist and anything generated from; and the value of every figure the sims cite."""
    d = spec["_dir"]
    files = [os.path.abspath(__file__), os.path.join(d, "sims.yaml")] + \
            [os.path.join(ROOT, n) for n in netlists(spec)]
    for s in spec["sims"]:
        if s.get("deck") and os.path.join(d, s["deck"]) not in files:
            files.append(os.path.join(d, s["deck"]))
    for inc in spec.get("include", []):
        files.append(inc_path(d, inc))
    for m in spec.get("models", []):
        files.append(os.path.join(ROOT, m))
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


def _interp(x0, x1, y0, y1, y):
    return x0 if y1 == y0 else x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def _unwrap(ph):
    out, off = [], 0.0
    for i, p in enumerate(ph):
        if i:
            d = p + off - out[-1]
            while d > 180:
                off -= 360
                d -= 360
            while d < -180:
                off += 360
                d += 360
        out.append(p + off)
    return out


def crossings(wave, level=0.0):
    """Every x at which a waveform crosses `level`, interpolated (log-x for an AC sweep)."""
    x, y = wave
    out = []
    for i in range(1, len(x)):
        if (y[i - 1] - level) * (y[i] - level) < 0 or (y[i] == level and y[i - 1] != level):
            if x[i - 1] > 0 and x[i] > 0 and x[i] / x[i - 1] > 1.0001:
                lx = _interp(math.log10(x[i - 1]), math.log10(x[i]), y[i - 1], y[i], level)
                out.append(10 ** lx)
            else:
                out.append(_interp(x[i - 1], x[i], y[i - 1], y[i], level))
    return out


def at(wave, x0):
    """A waveform's value at x0, interpolated linearly between its samples."""
    x, y = wave
    for i in range(1, len(x)):
        if x[i - 1] <= x0 <= x[i]:
            return _interp(y[i - 1], y[i], x[i - 1], x[i], x0) if x[i] != x[i - 1] else y[i]
    raise SystemExit(f"sim: at({x0:g}) is outside the waveform ({x[0]:g} to {x[-1]:g})")


def crossover(tdb):
    c = crossings(tdb, 0.0)
    if not c:
        return float("inf")          # never crosses: refused as a measure, which is right
    return c[0]


def phase_margin(tdb, tph):
    """The least phase margin at any 0 dB crossing of |T|: 180 + the (unwrapped) phase of
    T = -V(return)/V(injected), in degrees. At DC T's phase is 0 for negative feedback."""
    ph = _unwrap(tph[1])
    fs = crossings(tdb, 0.0)
    if not fs:
        return float("inf")
    return min(180.0 + at((tph[0], ph), f) for f in fs)


def _final(wave, t1):
    t, v = wave
    t0 = t1 - 0.05 * (t1 - t[0])
    pts = [vi for ti, vi in zip(t, v) if t0 <= ti <= t1]
    return sum(pts) / len(pts)


def overshoot(wave, t0, t1):
    """Percent overshoot of a step at t0: the largest excursion past the final value (the
    mean of the last 5 % before t1), over the step's size (final less the value at t0)."""
    t, v = wave
    v0 = at(wave, t0)
    vf = _final(wave, t1)
    step = vf - v0
    if step == 0:
        return float("inf")
    win = [vi for ti, vi in zip(t, v) if t0 <= ti <= t1]
    ex = (max(win) - vf) if step > 0 else (vf - min(win))
    return max(0.0, ex) / abs(step) * 100.0


def settling(wave, t0, t1, band):
    """Seconds from t0 until the waveform stays within +-band of its final value."""
    t, v = wave
    vf = _final(wave, t1)
    last = t0
    for ti, vi in zip(t, v):
        if t0 <= ti <= t1 and abs(vi - vf) > band:
            last = ti
    return last - t0


def peak(wave, t0, t1):
    return max(vi for ti, vi in zip(*wave) if t0 <= ti <= t1)


def trough(wave, t0, t1):
    return min(vi for ti, vi in zip(*wave) if t0 <= ti <= t1)


def cross(wave, level, t0=0.0):
    """The first time at or after t0 that a waveform crosses `level`; inf if it never does."""
    t, v = wave
    c = [x for x in crossings((t, v), level) if x >= t0]
    return c[0] if c else float("inf")


POST = {"backswing": backswing, "phase_margin": phase_margin, "crossover": crossover,
        "overshoot": overshoot, "settling": settling, "at": at, "peak": peak,
        "trough": trough, "cross": cross, "math": math, "abs": abs, "min": min, "max": max}


def ngspice(deck, post=None, values=None, spiceinit=None):
    """Run a deck; return its measures (and `post:` ones, computed on waveforms the deck
    writes with `wrdata <name>.dat <vector>`). `spiceinit` lines go in the run's .spiceinit."""
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "deck.cir")
        open(p, "w").write(deck)
        if spiceinit:
            open(os.path.join(t, ".spiceinit"), "w").write("\n".join(spiceinit) + "\n")
        r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True, cwd=t, timeout=300)
        waves = {}
        for f in glob.glob(os.path.join(t, "*.dat")):
            rows = [l.split() for l in open(f) if l.strip()]
            rows = [x for x in rows if len(x) >= 2]
            waves[os.path.basename(f)[:-4]] = ([float(x[0]) for x in rows], [float(x[1]) for x in rows])
    out = r.stdout + "\n" + r.stderr
    meas = {}
    for line in out.splitlines():
        m = re.match(r"^\s*([a-z][a-z0-9_]*)\s*=\s*([-+]?\d[\d.]*(?:e[-+]?\d+)?)", line.strip(), re.I)
        if m:
            meas[m.group(1).lower()] = float(m.group(2))
    errors = [l for l in out.splitlines() if re.search(r"error|failed|not found|singular|too small|aborted", l, re.I)
              and "no error" not in l.lower()]
    # A vendor macromodel's operating point often needs gmin or source stepping (a noise
    # diode's node starts singular). The warnings on the way are not failures when the
    # stepping then completes; an operating point that cannot be found still prints an
    # Error, which stays.
    if re.search(r"(gmin|source) stepping completed|transient op finished successfully", out, re.I):
        errors = [l for l in errors if not re.match(
            r"\s*Warning: (singular matrix|dynamic gmin stepping failed|true gmin stepping failed|"
            r"gmin stepping failed|source stepping failed)", l, re.I)]
    for name, expr in (post or {}).items():
        env = {"w": waves, "p": values or {}, **POST}
        try:
            meas[name] = float(eval(expr, {"__builtins__": {}}, env))
        except KeyError as e:
            # a waveform the deck should have written is missing: the analysis did not run
            errors.append(f"post: {name} needs waveform {e}, which the run did not write")
        except (SystemExit, ValueError) as e:
            # a waveform that stops short (an aborted run) cannot answer the question
            errors.append(f"post: {name}: {e}")
    return meas, errors, out


def ngspice_version():
    r = subprocess.run(["ngspice", "-v"], capture_output=True, text=True)
    m = re.search(r"ngspice-(\S+)", r.stdout + r.stderr)
    return m.group(1) if m else "?"


def expand(sims):
    """A sim with `sweep: {param: [values]}` becomes one sim per value (per combination),
    named name[param=value], each with the value `set:`."""
    out = []
    for s in sims:
        sw = s.get("sweep")
        if not sw:
            out.append(s)
            continue
        names = list(sw)
        for combo in itertools.product(*(sw[n] for n in names)):
            t = dict(s)
            t.pop("sweep")
            t["set"] = dict(s.get("set") or {})
            label = []
            for n, val in zip(names, combo):
                t["set"][n] = val if isinstance(val, (int, float)) else part_value(str(val))
                label.append(f"{n}={val}")
            t["name"] = f"{s['name']}[{','.join(label)}]"
            out.append(t)
    return out


def run(simdir):
    spec = load(simdir)
    parts, doc = netlist_parts(spec)
    figs = {k: figure_value(str(v["value"])) for k, v in figures().items()
            if re.match(r"\s*-?\d", str(v["value"]))}
    results = {}
    # vendor models, included by path (banked, verbatim - never filled)
    models = "".join(f'.include "{os.path.join(ROOT, m)}"\n' for m in spec.get("models", []))
    for s in expand(spec["sims"]):
        template = open(os.path.join(simdir, s["deck"])).read()
        if spec.get("generate") == "board":
            template = board_deck(spec, doc, template)
        # model libraries, inlined (the deck runs in a scratch directory), filled like the deck,
        # ahead of the deck's final .end (not a .endc)
        lib = "".join(open(inc_path(simdir, inc)).read() + "\n" for inc in spec.get("include", []))
        if lib:
            if re.search(r"\n\.end\s*$", template):
                template = re.sub(r"\n\.end\s*$", lambda m: "\n" + lib + ".end\n", template)
            else:
                template += "\n" + lib
        if models:
            first, _, rest = template.partition("\n")
            template = first + "\n" + models + rest
        per = {}
        for label, values in corners(spec, parts, s.get("vary")):
            v = derive(spec, {**values, **{k: (fv if isinstance(fv, (int, float)) else part_value(str(fv)))
                                           for k, fv in (s.get("set") or {}).items()}})
            meas, errors, out = ngspice(fill(template, v), s.get("post"), v, spec.get("spiceinit"))
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
               "n": Counter(c.get("of", r.split(":", 1)[-1]) for r, c in doc["components"].items()),
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
