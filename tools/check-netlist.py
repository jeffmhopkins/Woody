#!/usr/bin/env python3
"""Prove each circuit's netlist against the BOM and against its own drawing.

WHY THIS EXISTS. An ASCII drawing is a picture. No tool in this repository
could read one, so nothing checked that a value in a drawing matched the BOM
row for the same refdes - and a 2026-09-22 review found four that did not:

    R-FB        drawn 40k     BOM 40.2k   (and 40k is not an E96 value)
    C1          drawn 47uF    BOM 100uF   (on the +12 V rail, so half)
    R-LED-SER   drawn 220R    BOM 330R
    N-FET       drawn nameless, BOM Q-LOADSW

Every one of those is a one-line diff against a netlist, and none of them was
reachable before. The netlist is AUTHORITATIVE; the drawing is a
representation of it (hardware/README.md says so, and ROADMAP tracks the
rollout).

WHAT IT CHECKS, per circuit that has a netlist.yaml:

    bom        every refdes exists in hardware/bom.csv, and its `value`
               matches that row
    nets       every net has at least two endpoints, unless it is declared
               in external_endpoints
    pins       every declared pin is used exactly once; no net references a
               pin a component does not declare
    drawing    every `[REFDES value]` label in the page's ASCII drawing names
               a component in the netlist AND agrees with it, against the
               row's `part` and `package` fields together; a bracketed label
               that names a known refdes in some OTHER order is reported
               rather than silently skipped
    ports      every port is used by a net, and every net port is declared
    instances  no row is placed more times ACROSS ALL netlists than the BOM
               buys - the count a per-circuit check structurally cannot do

A circuit with no netlist.yaml is REPORTED, NOT FAILED, while the rollout is
in progress - the count of pages still without one is printed on every run so
it cannot quietly stall. `--strict` turns that into a failure once the
rollout is done.

Usage:  python3 tools/check-netlist.py [--strict] [<circuit-dir> ...]
Exit:   0 clean, 1 problems
"""
import csv, os, re, sys, glob

try:
    import yaml
except ImportError:
    sys.exit("check-netlist.py needs PyYAML")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOX = set("│┬┴├┤┼└┘┌┐─►")
# `[R-FB 40.2k]` / `[FB1]` / `[D1 1N5817]` - a bracketed label in a drawing.
#
# THE SECOND CHARACTER MAY BE A HYPHEN, and the first version of this regex
# said `[A-Z][A-Z0-9][A-Z0-9-]*`, which requires it not to be. THIS REPO'S
# REFDES CONVENTION IS X-NAME: R-FB, D-JACK-CLAMP, C-OUT-BREATH, U-LOADSW. So
# the pattern matched POT-GAIN and POT-OFFSET and essentially nothing else -
# 2 labels out of 10 on the pilot page - and the checker reported 0 problems
# on a drawing with a deliberately injected R-FB 40k in it. A fail-open in the
# tool written to close fail-opens, caught by testing it against the defect it
# exists for rather than by reading it.
# AND A REFDES MAY BE ONE CHARACTER. The second version required at least
# two, so `[C 1uF]` on the power-entry page - the LM317's output capacitor,
# drawn `C` because the column has no room for C-REG-OUT - was invisible on a
# page that had already been converted and had already reported clean. Found
# by the unparsed-bracket check below, which exists precisely because a label
# the parser cannot read looks exactly like a label that passed.
# AND IT MAY CARRY AN UNDERSCORE SUBSCRIPT. `[C_cm 1.5nF]`, `[C_diff 15nF]`
# and `[R_G 42.2k]` are how the breath pages spell a subscript in ASCII, and a
# class without `_` in it matched just the `C`, turning three correct labels
# into three unknown refdes. The refdes token now runs to the first space.
# AND A DOT INSIDE A PART NUMBER IS PART OF IT. `[R-78E5.0 A]` labels the
# buck by its order code, and a class without `.` split it into a refdes
# `R-78E5` and a value `.0 A` - one unknown refdes and one value token that
# means nothing. Only between alphanumerics, so a label ending in a full stop
# is still a label ending in a full stop.
LABEL = re.compile(r"\[([A-Z][A-Za-z0-9_-]*(?:\.[A-Za-z0-9][A-Za-z0-9_-]*)*)\s*([^\]]*)\]")


MASTER = os.path.join(ROOT, "hardware/nets.yaml")


def master_nets():
    """The authoritative list of boundary-crossing nets, or {} if absent."""
    if not os.path.exists(MASTER):
        return {}
    return (yaml.safe_load(open(MASTER, encoding="utf-8")) or {}).get("nets") or {}


def check_master(master, seen, problems, have_netlist, deferred, per_board=None):
    """Both halves of every inter-circuit net.

    `seen` maps net -> {circuit: dir}, collected from the per-circuit ports.

    THE BIDIRECTIONAL HALF IS THE POINT. A per-circuit file can only ever
    declare its own side, so without this a circuit can name a peer that never
    names it back - which is exactly the defect that made the `circuit:`
    dependency edges untrustworthy until they were checked from both ends.
    """
    for net, spec in master.items():
        # A PER-BOARD BUNDLE IS NOT ONE NET AND CANNOT BE PORTED.
        #
        # KEY_BITS and MARKER_BITS are eight parallel inputs per 74HC165, and
        # WHICH of the eight is a switch, a marker strap or a free bit differs
        # on all four cluster boards - the allocation table on
        # key-marker-and-bits.md gives four different rows. One schematic, four
        # strappings, so no port assignment on the shared netlist is true of
        # every board. The receiving circuit declares those pins as unasserted
        # endpoints instead, and this is counted and printed so the gap is a
        # number rather than a silence.
        if spec.get("per_board"):
            if per_board is not None:
                per_board.append(net)
            continue
        drv = spec.get("driver")
        rcv = list(spec.get("receivers") or [])
        ref = list(spec.get("reference") or [])
        # A REFERENCE NET HAS AN ORIGIN, NOT A DRIVER. Nobody drives a ground:
        # the circuit that defines the star point references the net exactly
        # like every circuit that returns to it, so it belongs in `reference`
        # rather than being a driver with a mismatched direction.
        if spec.get("origin"):
            ref = [spec["origin"]] + [c for c in ref if c != spec["origin"]]
        # `external_driver:` is for a net driven from OUTSIDE this corpus - the
        # display board has no page, and whatever is plugged into the service
        # header is not a part of this instrument at all. Saying so is better
        # than either inventing a driver or calling the net undriven, which
        # would mean something else entirely.
        if not drv and not (spec.get("multi_driver") or spec.get("undriven")
                            or spec.get("origin") or spec.get("external_driver")):
            problems.append(f"nets.yaml: {net!r} has no driver")
        if spec.get("undriven") and not spec.get("pull"):
            # An undriven net is a real thing - CLR is held inactive by
            # R-CLR-PU and the watchdog that once drove it is deleted - but an
            # undriven net with nothing holding it is a floating input, which
            # is a defect rather than a design.
            problems.append(f"nets.yaml: {net!r} is undriven and declares no "
                            f"`pull:` - a net with neither is floating")
        if not rcv and not ref:
            problems.append(f"nets.yaml: {net!r} has no receivers and no "
                            f"reference circuits - it crosses no boundary")
        # every circuit this file names must declare the port back
        for circ, role in [(drv, "out")] + [(c, "in") for c in rcv] + \
                          [(c, "ref") for c in ref]:
            if not circ:
                continue
            got = seen.get(net, {}).get(circ)
            if got is None:
                # A CIRCUIT WITH NO NETLIST YET IS PENDING, NOT WRONG. Failing
                # on it would make the master unusable until the last of 23
                # circuits was converted, which is the kind of all-or-nothing
                # gate that gets switched off. It is counted and printed
                # instead, so the rollout cannot stall quietly.
                if circ in have_netlist:
                    problems.append(f"nets.yaml: {net!r} names {circ} as {role}, "
                                    f"and that circuit's netlist declares no "
                                    f"such port")
                else:
                    deferred.append((net, circ, role))
            elif got != role:
                problems.append(f"nets.yaml: {net!r} names {circ} as {role}, "
                                f"but that circuit declares dir {got!r}")
    # and the other direction: a port naming a net nobody owns, or naming one
    # that does not name it back.
    #
    # THIS HALF WAS MISSING. The forward loop walks the master's own lists, so
    # a circuit could declare a port on a net the master never associates with
    # it and nothing said a word - which is the same one-sided declaration the
    # master exists to stop, arriving from the other side.
    for net, by in seen.items():
        if net not in master:
            who = ", ".join(sorted(by))
            problems.append(f"{who}: port {net!r} is in no master net "
                            f"(add it to hardware/nets.yaml)")
            continue
        spec = master[net]
        named = {spec.get("driver"), spec.get("origin")}
        named |= set(spec.get("receivers") or [])
        named |= set(spec.get("reference") or [])
        named |= set(spec.get("multi_driver") or [])
        # `proposed:` is how a circuit that is DRAWN BUT NOT ADOPTED declares
        # a port without the master asserting the board has that connection.
        named |= set(spec.get("proposed") or [])
        for circ in by:
            if circ not in named:
                problems.append(f"{circ}: declares a port on {net!r} and "
                                f"hardware/nets.yaml does not name it on that "
                                f"net")


def check_global(specs, bom, problems):
    """Every instance of every row, summed ACROSS circuits.

    THE PER-CIRCUIT COUNT CANNOT SEE THIS. R-OUT-PROT is qty 6 and six
    different circuits each place one; each of them passes its own check
    while the board could still be short. The row that pays for this is
    R-OPAMP-IN: qty 7, and the six placed instances are pitch, the four mods
    and the mod reference buffer. The seventh is claimed by a sentence on
    mod-channels.md for the VREFOUT follower, which no drawing shows and no
    netlist places - so it is a real open question rather than a miscount, and
    it is one nothing in this repository could ask before.

    OVER-USE IS A DEFECT. UNDER-USE IS NOT, YET: circuits without a netlist
    place nothing, so every row would report short until the last conversion.
    It is printed rather than failed, and `--strict` is where that flips.
    """
    from collections import Counter
    used, sections = Counter(), Counter()
    for spec in specs:
        # A CIRCUIT CAN BE BUILT MORE THAN ONCE. The four cluster boards are
        # one schematic and four PCBs, so one netlist accounts for four of
        # every part on it. Without this the 74HC165 reports 1 placed against
        # a qty of 4 and the shortfall looks like an unfinished conversion.
        n = int(spec.get("replicated") or 1)
        for ref, c in (spec.get("components") or {}).items():
            row = c.get("of", ref)
            used[row] += n
            if c.get("section"):
                sections[row] += n
    exact, short = 0, []
    for row, n in sorted(used.items()):
        if row not in bom:
            continue
        try:
            have = int(bom[row]["qty"])
        except (ValueError, KeyError):
            continue
        if sections[row]:
            continue          # a package supplying sections is counted in prose
        if n > have:
            problems.append(f"instances: {row} is placed {n} time(s) across all "
                            f"netlists and the BOM buys {have}")
        elif n == have:
            exact += 1
        else:
            short.append(f"{row} {n}/{have}")
    return exact, short, sum(1 for r in used if sections[r])


def bom_rows():
    p = os.path.join(ROOT, "hardware/bom.csv")
    with open(p, newline="", encoding="utf-8") as fh:
        return {r["ref"]: r for r in csv.DictReader(fh)}


def drawing_lines(page_path):
    """Every line of that page that is inside an ASCII drawing.

    A FENCED BLOCK CONTAINING BOX CHARACTERS IS A DRAWING, and every line in
    it counts. Judging line by line on a box-character threshold missed the
    parts drawn on their own - `[D-JACK-CLAMP BAV99]` has two box characters
    and `[R-OUT-PROT 1k, 1206]` has none, because they hang off a rail rather
    than sitting in it. Those are exactly the rows a stuffing list gets wrong.
    """
    try:
        lines = open(page_path, encoding="utf-8").read().split("\n")
    except OSError:
        return []
    fence, start, blocks = False, 0, []
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            if fence:
                blocks.append((start, n))
            fence, start = not fence, n
    drawing = set()
    for a, b in blocks:
        body = lines[a:b - 1]
        if sum(sum(ch in BOX for ch in L) for L in body) >= 3:
            drawing.update(range(a + 1, b))
    return [(n, line) for n, line in enumerate(lines, 1)
            if n in drawing or sum(ch in BOX for ch in line) >= 3]


def drawing_labels(page_path):
    """Every [REFDES value] sitting inside an ASCII drawing on that page."""
    return [(n, ref, val.strip())
            for n, line in drawing_lines(page_path)
            for ref, val in LABEL.findall(line)]


BRACKET = re.compile(r"\[[^\]]*\]")


def unparsed_brackets(page_path):
    """Bracketed drawing labels that LABEL could not read as [REFDES value].

    WHY THIS IS A CHECK AND NOT A SHRUG. `[1k R-OPAMP-IN]` on the pitch page
    is a label written value-first. It is not a defect in the drawing - it
    reads perfectly well - but it is INVISIBLE to the comparison above, which
    is the fail-open shape this whole tool exists to stop: the checker says
    nothing and the silence reads like agreement. One spelling has to win, and
    refdes-first is the one the other pages use.
    """
    out = []
    for n, line in drawing_lines(page_path):
        spans = {m.span() for m in LABEL.finditer(line)}
        for m in BRACKET.finditer(line):
            if m.span() not in spans:
                out.append((n, m.group(0)))
    return out


# Unit spellings that mean the same thing. THIS IS CLAUDE.md 2's SPELLING TRAP
# IN UNIT FORM: a drawing types the real micro sign and a CSV types "u", and a
# comparison that does not fold them reports every capacitor on the page as a
# contradiction. Folding them is right; folding anything that changes a
# MAGNITUDE would not be.
UNITS = {"\u00b5": "u", "\u03bc": "u", "\u2126": "ohm", "\u03a9": "ohm", "\u00b0": "deg"}


def norm(v):
    """Compare values the way a human does: case, spacing and unit spelling."""
    # FOLD BEFORE LOWERING. lower() turns the ohm sign into a lowercase omega,
    # which is in no table here, so folding afterwards never fired and every
    # `10ohm` against a `10R` read as a contradiction. The one unit spelling
    # the case change touches was the one the table was written for.
    s = v or ""
    for a, b in UNITS.items():
        s = s.replace(a, b)
    s = s.lower()
    s = re.sub(r"\s+", "", s).rstrip(",")
    # `10R` and `10 ohm` are one value. The drawing types the ohm sign and the
    # BOM types R, which is ordinary resistor notation on both sides - and
    # without this the gate resistor reads as a contradiction with itself.
    # Only after a digit, and only when nothing wordlike follows, so `0R strap`
    # and every refdes with an r in it are left alone.
    s = re.sub(r"(?<=\d)r(?![a-z])", "ohm", s)
    # And a metric prefix makes the ohm redundant: a drawing types `10 kohm`
    # where the BOM types `10k`, and both mean the same resistor. Only after a
    # prefix - a bare `10ohm` stays, so it still matches `10R` above.
    return re.sub(r"(?<=\d)([kmg])ohm", r"\1", s)


VALTOK = re.compile(r"\d+(?:\.\d+)?\s*[a-zA-Z%\u03a9\u2126\u00b5\u03bc]*")
# A MULTIPLIER IS A COUNT, NOT A MAGNITUDE. `[R-SPI-PULL x3]` and
# `[C-REF-OUT 10uF x2]` say how many, and reading the 3 or the 2 as a value
# turns a correct label into a contradiction.
# AND SO IS AN INSTANCE INDEX. `[C-REF-OUT#1]` and `[C-REF-OUT#2]` are the two
# 10 uF, not a 1 uF and a 2 uF.
COUNT = re.compile(r"[x\u00d7#]\s*\d+", re.I)


def value_tokens(v):
    """The magnitudes in a value string, normalised.

    A DRAWING LABEL MAY SAY LESS THAN THE BOM, NEVER SOMETHING DIFFERENT.
    `[R-OUT-PROT 1k 500mW]` is a fair abbreviation of `1k 1%, >=500mW` - a
    drawing cannot carry the full part string without pushing every column to
    its right. But `[R-FB 40k]` against `40.2k 1%` is a contradiction, and it
    is the one that reached a review: 40k is not an E96 value, so a layout
    taken off that drawing orders a part nobody sells.

    So the test is SUBSET, not equality and not substring: every magnitude the
    drawing states must appear in the netlist's value.
    """
    return {norm(m) for m in VALTOK.findall(COUNT.sub(" ", v or ""))
            if any(c.isdigit() for c in m)}


def check_one(d, bom, problems, seen, elsewhere=None):
    rel = os.path.relpath(d, ROOT)
    spec = yaml.safe_load(open(os.path.join(d, "netlist.yaml"), encoding="utf-8"))
    comps = spec.get("components") or {}
    nets = spec.get("nets") or {}
    ports = spec.get("ports") or {}
    external = set(spec.get("external_endpoints") or [])

    # --- refdes and value against the BOM
    for ref, c in comps.items():
        row_ref = c.get("of", ref)        # a section names its package
        if row_ref not in bom:
            problems.append(f"{rel}: {ref} is in no bom.csv row "
                            f"(looked for {row_ref!r})")
            continue
        if "value" in c and norm(c["value"]) not in norm(bom[row_ref]["part"]):
            problems.append(f"{rel}: {ref} value {c['value']!r} does not appear "
                            f"in its BOM part field {bom[row_ref]['part']!r}")

    # --- NO CIRCUIT MAY USE MORE OF A PART THAN THE BOM BUYS.
    #
    # Several rows are qty 2 or 6 and their instances are distinguished here
    # with `of:` - R2/R3 both map to R-SER-BREATH, R4/R5 to R-BIAS-INAMP. That
    # is the right way to netlist them, and it makes over-use checkable for
    # the first time: a page that quietly drew a third instance would ship a
    # board short of a part. The op-amp half-count that three pages disagreed
    # about is this same defect in the form nobody could measure.
    from collections import Counter
    used_of = Counter(c.get("of", ref) for ref, c in comps.items())
    for row, n in used_of.items():
        if row not in bom:
            continue
        # a package supplying sections counts once per SECTION, not per package
        sections = sum(1 for c in comps.values()
                       if c.get("of") == row and c.get("section"))
        try:
            have = int(bom[row]["qty"])
        except (ValueError, KeyError):
            continue
        if sections:
            continue          # half-counting is the op-amp case, tracked in prose
        if n > have:
            problems.append(f"{rel}: uses {n} instance(s) of {row} and the BOM "
                            f"buys {have}")

    # --- nets: endpoints, and pins that exist
    declared_pins = {(r, str(p)) for r, c in comps.items()
                     for p in (c.get("pins") or [])}
    used = []
    for net, eps in nets.items():
        if net not in external and len(eps) < 2:
            problems.append(f"{rel}: net {net!r} has {len(eps)} endpoint(s); "
                            f"a net needs two or must be in external_endpoints")
        for ep in eps:
            if isinstance(ep, dict):
                pn = ep.get("port")
                if pn and pn not in ports:
                    problems.append(f"{rel}: net {net!r} uses undeclared port {pn!r}")
                continue
            if "." not in ep:
                problems.append(f"{rel}: net {net!r} endpoint {ep!r} is not REF.PIN")
                continue
            ref, pin = ep.rsplit(".", 1)
            if ref not in comps:
                problems.append(f"{rel}: net {net!r} references unknown component {ref!r}")
            elif (ref, pin) not in declared_pins:
                problems.append(f"{rel}: {ref} has no pin {pin!r} "
                                f"(declares {comps[ref].get('pins')})")
            used.append((ref, pin))

    for rp in sorted(declared_pins - set(used)):
        problems.append(f"{rel}: {rp[0]}.{rp[1]} is declared and connected to nothing")
    for rp in sorted({u for u in used if used.count(u) > 1}):
        problems.append(f"{rel}: {rp[0]}.{rp[1]} appears in more than one net")

    # IMPLICIT POWER PINS. An op-amp needs its rails whether or not the
    # drawing shows them, and drawings here mostly do not - hand-wiring V+
    # and V- into every section would add noise without adding truth. A
    # component declares `rails:` instead, and that counts as this circuit
    # receiving those nets. Without this the master's power entries look
    # unsatisfied on exactly the circuits that obviously consume them.
    for ref, c in comps.items():
        for rail in (c.get("rails") or []):
            ports.setdefault(rail, {"dir": "in", "implicit": True})

    circ_id = spec.get("circuit") or rel
    for pn, pspec in ports.items():
        seen.setdefault(pn, {})[circ_id] = (pspec or {}).get("dir")
    for pn, pspec in ports.items():
        if (pspec or {}).get("implicit"):
            continue
        if not any(isinstance(e, dict) and e.get("port") == pn
                   for eps in nets.values() for e in eps):
            problems.append(f"{rel}: port {pn!r} is declared and used by no net")

    # --- THE ONE THAT CATCHES THE RECORDED DEFECTS: drawing vs netlist
    #
    # `drawn_as` is how a drawing's local label is reconciled with the BOM
    # refdes. A drawing says [R-FB 40.2k] because the full name would push
    # every column to its right, and widening a label inside a drawing is
    # itself a recorded defect on five pages. Declaring the alias HERE - in
    # the authoritative file - is better than the prose table it replaces,
    # because the checker can enforce it.
    alias = {c["drawn_as"]: ref for ref, c in comps.items() if c.get("drawn_as")}
    # Parts drawn for context and owned by another circuit. A page whose
    # drawing deliberately spans two boards - to derive a pole or a CMRR
    # budget in one place - would otherwise report every foreign part as a
    # missing component, and the fix for THAT would be to stop drawing the
    # context, which is worse than the warning.
    foreign = spec.get("foreign") or {}
    for fr, f in foreign.items():
        row = f.get("row")
        if row and row not in bom:
            problems.append(f"{rel}: foreign {fr!r} claims BOM row {row!r}, "
                            f"which does not exist")
    page = os.path.join(d, spec.get("page") or "")
    for lineno, ref, val in drawing_labels(page):
        ref = alias.get(ref, ref)
        if ref not in comps:
            if any(c.get("of") == ref for c in comps.values()):
                continue                  # a package, not a net node
            # A PART DRAWN ON A PAGE THAT DOES NOT OWN IT WAS SKIPPED
            # ENTIRELY. power-entry.md draws the whole load switch inside one
            # drawing - that is deliberate, it is one board - but every one of
            # those labels resolved to "a BOM row, not a component here" and
            # nothing compared its value. The circuit that owns it has a
            # netlist now, so the value is checkable across the page boundary.
            # A foreign part resolves BY ROW, because its label is a local
            # name on a page that does not own it.
            index = elsewhere or {}
            other = None
            if ref in foreign and foreign[ref].get("row"):
                other = index.get("__by_row__", {}).get(foreign[ref]["row"])
            if other is None and ref not in foreign:
                other = index.get(ref)
            # ONE PAGE, SEVERAL NETLISTS. carrier.md §2 is the page of three
            # circuits at once, so without this every label on it is reported
            # three times - once by each netlist that names the page. A label
            # is this netlist's business when it declares the part `foreign:`
            # or when the part is its own; otherwise the circuit that owns it
            # reports it.
            if other and other["circuit"] != (spec.get("circuit") or rel) \
                    and ref not in foreign:
                continue
            if other:
                row = bom.get(other["row"], {})
                allowed = value_tokens(other["value"]) | value_tokens(row.get("package"))
                extra = value_tokens(val) - allowed if val else set()
                if extra:
                    problems.append(f"{rel}: drawing line {lineno} shows {ref} as "
                                    f"{val!r}, which {other['circuit']}'s netlist "
                                    f"value {other['value']!r} does not support "
                                    f"({', '.join(sorted(extra))})")
                continue
            # A FOREIGN PART WHOSE OWNER HAS NO NETLIST YET stays skipped -
            # declaring it is what keeps a deliberately cross-board drawing
            # checkable without pretending the part is ours. Once the owner is
            # converted the branch above checks it, which is the whole point:
            # `foreign:` used to be an unconditional skip, so power-entry.md's
            # seven load-switch labels were exempt from every check in this
            # file even after that circuit had a netlist.
            if ref in foreign:
                continue
            if ref in bom:
                # A BOM ROW ON ITS OWN IS NOT ENOUGH TO CHECK AGAINST. Several
                # rows carry a spec rather than a value - R-ILIM's part field
                # is "Sense resistor, value from E6", deliberately blocked on
                # a bench step - and tokenising that finds the 6 in E6. A
                # label is checked once the circuit that OWNS the part has a
                # netlist, which is the `elsewhere` branch above; until then
                # it is skipped exactly as it always was.
                continue
            problems.append(f"{rel}: drawing line {lineno} labels {ref!r}, "
                            f"which is not in this netlist")
            continue
        want = comps[ref].get("value")
        if want and val:
            # THE PACKAGE IS PART OF WHAT THE ROW SAYS. `[R-OUT-PROT 1k, 1206]`
            # states a resistance and a footprint; the resistance is in the
            # BOM's `part` field and the footprint is in its `package` field,
            # and comparing against only the first reports a correct drawing
            # as a contradiction. That is the false-positive shape CLAUDE.md 2
            # warns about - the cheapest fix for a check that fires on a
            # correct label is to make the label wrong.
            row = bom.get(comps[ref].get("of", ref), {})
            allowed = value_tokens(want) | value_tokens(row.get("package"))
            extra = value_tokens(val) - allowed
            if extra:
                problems.append(f"{rel}: drawing line {lineno} shows {ref} as {val!r}, "
                                f"which the netlist's {want!r} does not support "
                                f"({', '.join(sorted(extra))})")

    # A LABEL SPLIT ACROSS TWO LINES IS NOT A LABEL AT ALL.
    #
    # `[C-BUCK-IN` opens on one drawing line and `100 uF 25V]` closes on the
    # next, and every regex here works a line at a time, so the part was
    # invisible - not skipped with a reason, invisible. On key-register.md the
    # same thing made the WHOLE PAGE invisible: its only bracketed label was a
    # broken one, so the page reported zero labels and never appeared in the
    # rollout's list of drawings still to convert.
    for lineno, line in drawing_lines(page):
        if line.count("[") != line.count("]"):
            problems.append(f"{rel}: drawing line {lineno} has an unclosed "
                            f"bracket, so any label on it is invisible to every "
                            f"check here - a label has to fit on one line")

    # A LABEL THE PARSER CANNOT READ IS NOT A LABEL THAT PASSES.
    known = set(comps) | set(alias) | set(foreign) | set(bom)
    for lineno, text in unparsed_brackets(page):
        if any(re.fullmatch(r"[A-Z][A-Z0-9-]*", tok) and tok in known
               for tok in re.split(r"[^A-Za-z0-9-]+", text)):
            problems.append(f"{rel}: drawing line {lineno} label {text!r} names a "
                            f"known refdes but is not in [REFDES value] order, so "
                            f"nothing checks it")
    return len(comps), len(nets)


def main():
    strict = "--strict" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    dirs = sorted({os.path.dirname(p) for p in
                   glob.glob(os.path.join(ROOT, "hardware/**/netlist.yaml"),
                             recursive=True)})
    if args:
        dirs = [d for d in dirs if any(a.rstrip("/") in d for a in args)]

    # Pages that carry a drawing and have no netlist yet - the rollout's
    # denominator, printed every run so it cannot stall unnoticed.
    pending, not_a_circuit = [], []
    for page in glob.glob(os.path.join(ROOT, "hardware/**/*.md"), recursive=True):
        if os.path.basename(page) in ("README.md", "notes.md"):
            continue
        # A DRAWING PAGE IS ONE WITH A DRAWING ON IT, not one with a
        # parseable label on it. Judging by labels excluded key-register.md
        # entirely, because its single label was split across two lines.
        if not drawing_lines(page):
            continue
        # NOT EVERY DRAWING IS A CIRCUIT. cluster-boards.md draws where the
        # four boards sit inside the instrument - box characters, no nets, no
        # refdes. A netlist is the wrong artefact for it, and the page says so
        # in a marker a tool can read rather than leaving it to sit in the
        # pending list forever looking like work nobody got to.
        head = open(page, encoding="utf-8").read()
        m = re.search(r"<!--\s*netlist:\s*none\b(.*?)-->", head, re.S)
        if m:
            not_a_circuit.append((os.path.relpath(page, ROOT),
                                  " ".join(m.group(1).split()).strip(" ()")))
            continue
        if not os.path.exists(os.path.join(os.path.dirname(page), "netlist.yaml")):
            pending.append(os.path.relpath(page, ROOT))

    bom = bom_rows()
    master = master_nets()
    seen = {}

    all_specs = [yaml.safe_load(open(os.path.join(d, "netlist.yaml"),
                                     encoding="utf-8")) or {}
                 for d in sorted({os.path.dirname(p) for p in
                                  glob.glob(os.path.join(ROOT, "hardware/**/netlist.yaml"),
                                            recursive=True)})]
    # Every component anyone has netlisted, by the name a drawing might use
    # for it - its refdes and its `drawn_as`. This is what lets one page's
    # drawing be checked against another circuit's netlist.
    #
    # A GENERIC LOCAL NAME IS NOT A GLOBAL ONE. `R1` is the LT5400 element on
    # pitch-stage, the 10k input leg on mod-channels and an instrument-side
    # series resistor drawn for context on breath-receive-stage - three parts,
    # three values. A name that resolves to more than one BOM row is recorded
    # as AMBIGUOUS and never used to check anything; the by-row index below is
    # how a `foreign:` label resolves, and it does not go through the name at
    # all.
    elsewhere, by_row = {}, {}
    for spec in all_specs:
        circ = spec.get("circuit", "?")
        for ref, c in (spec.get("components") or {}).items():
            if not c.get("value"):
                continue
            entry = {"circuit": circ, "row": c.get("of", ref),
                     "value": c["value"]}
            by_row.setdefault(entry["row"], entry)
            for name in (ref, c.get("drawn_as")):
                if not name:
                    continue
                if name in elsewhere and elsewhere[name] and \
                        elsewhere[name]["row"] != entry["row"]:
                    elsewhere[name] = None        # ambiguous
                else:
                    elsewhere.setdefault(name, entry)
    elsewhere = {k: v for k, v in elsewhere.items() if v}
    elsewhere["__by_row__"] = by_row

    problems, comps, nets = [], 0, 0
    for d in dirs:
        c, n = check_one(d, bom, problems, seen, elsewhere)
        comps += c
        nets += n

    counted = check_global(all_specs, bom, problems) if not args else None

    deferred, per_board = [], []
    have_netlist = {s.get("circuit") for s in all_specs}
    if master and not args:
        check_master(master, seen, problems, have_netlist, deferred, per_board)

    for p in problems:
        print("  " + p)
    print(f"netlist: {len(dirs)} circuit(s), {comps} components, {nets} nets, "
          f"{len(master)} master net(s) | "
          f"{len(problems)} problem(s) | {len(pending)} drawing page(s) still "
          f"without a netlist | {len(deferred)} master endpoint(s) awaiting one")
    if not_a_circuit and not args:
        for pg, why in sorted(not_a_circuit):
            print(f"    not a circuit: {pg}" + (f" - {why}" if why else ""))
    if per_board:
        print(f"per-board bundles not resolved to single nets: "
              f"{', '.join(sorted(per_board))}")
    if counted:
        exact, short, sectioned = counted
        # NAMED, NOT COUNTED. A bare "5 still short" reads like five
        # unfinished conversions; every one of them so far has a reason
        # written down somewhere, and printing the rows is what lets a reader
        # check that rather than take it on trust.
        print(f"instances: {exact} row(s) placed exactly to BOM qty, "
              f"{sectioned} counted by section, {len(short)} short"
              + (": " + ", ".join(short) if short else ""))
    if pending and not args:
        for p in sorted(pending):
            print(f"    pending: {p}")
    return 1 if problems or (strict and pending) else 0


if __name__ == "__main__":
    sys.exit(main())
