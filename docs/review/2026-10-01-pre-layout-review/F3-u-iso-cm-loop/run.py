import subprocess, re, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
tpl = open('cm.cir.tpl').read()
THRU = "RCA vinp fp 1m\nRCB vinn fn 1m"
def choke(l):
    return f"LCA vinp fa {l}\nRCHA fa fp 0.05\nLCB vinn fb {l}\nRCHB fb fn 0.05\nK1 LCA LCB 0.995"
base = dict(YR="0.001", CY="1n", CYN="1f", CHOKE=THRU, LRIB="0.3u", RPTC="1.0")
cases = [
    ("as netlisted: C-ISO-Y 1n", {}),
    ("as netlisted, ribbon 1 uH/conductor", dict(LRIB="1u")),
    ("as netlisted, ribbon 0.1 uH/conductor", dict(LRIB="0.1u")),
    ("as netlisted, PTCs 0.4 ohm", dict(RPTC="0.4")),
    ("C-ISO-Y 10n", dict(CY="10n")),
    ("C-ISO-Y 47n", dict(CY="47n")),
    ("C-ISO-Y 100n + 100n VIN_NEG-PWR_GND", dict(CY="100n", CYN="100n")),
    ("47n + 2.2 ohm series (damped)", dict(CY="47n", CHOKE=THRU, YR="2.2")),
    ("100n + 1 ohm series (damped)", dict(CY="100n", YR="1.0")),
    ("220n + 1 ohm series (damped)", dict(CY="220n", YR="1.0")),
    ("1n + CM choke 1 mH", dict(CHOKE=choke("1m"))),
    ("10n + CM choke 1 mH", dict(CY="10n", CHOKE=choke("1m"))),
]
for name, c in cases:
    v = dict(base, **c)
    d = tpl
    for k, x in v.items():
        d = d.replace("{%s}" % k, x)
    open('cm.cir', 'w').write(d)
    out = subprocess.run(['ngspice', '-b', 'cm.cir'], capture_output=True, text=True).stdout
    m = dict(re.findall(r'^(\w+)\s+=\s+([-\d.eE+]+)', out, re.M))
    if 't550' not in m:
        print(out[-3000:]); sys.exit(1)
    f = lambda k: float(m[k])
    row = [f"{name:40s}"]
    for fr in ("550", "1650", "5500"):
        t = f('t' + fr)
        row.append(f"{fr}k: Y {f('y'+fr)/t*100:5.1f}% AGND {f('a'+fr)/t*100:5.1f}% star {f('s'+fr)/t*100:5.1f}%")
    print(" | ".join(row))
