#!/usr/bin/env python3
"""The commit gate: a Claude Code PreToolUse hook on Bash (.claude/settings.json).

Reads the hook's JSON on stdin. For any command that is not a `git commit` or
`git merge` it exits at once, silent - the old hook ran the whole corpus check
before EVERY Bash call (`ls` included), because its `"if"` gated nothing, and a
loop of tool calls blew its 60 s timeout (issue #9, G1).

For a commit or merge it runs, in the tree the command will commit in:
  - tools/check-staleness.py (the corpus: figures, BOM, datasheets, CAD and sim
    ledgers - everything that needs no KiCad);
  - tools/kicad.py check, at the same time, when kicad-cli is installed AND the
    commit can touch a KiCad input (something staged under hardware/ or
    mechanical/export/, a KiCad tool under tools/, or a `git add`/`-a` in the
    same command, whose staging cannot be seen yet). Otherwise it says why it
    was SKIPPED - it never just leaves it out (G3).

On a FAIL it DENIES the command (permissionDecision "deny"), unless the commit
message says why the commit is being made red anyway, with a trailer line

    Gate-Red: <which failures, and why this commit goes in with them>

anywhere in the command (a -m message) or in the file a -F names. Then the
commit goes ahead and the failures are shown, not hidden: the trailer is in the
commit message for good, `git log --grep Gate-Red` lists every red commit, and
nothing is deadlocked while a known-red state - stale renders another agent is
rebuilding, a sim waiting on a design decision - is being worked off. A checker
that crashes or times out is a FAIL too: it says nothing about the tree.

Exit 0 always; the decision is in the JSON. `--self-test` checks the command
matcher only.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

TIMEOUT = 200           # each checker; the hook entry allows 240 s for the whole gate

# git, its global options, then commit or merge (not merge-base, merge-file, --abort)
GIT_COMMIT = re.compile(
    r"(?:^|[;&|(`\s])git(?:\s+(?:-C\s+\S+|-c\s+\S+|--[\w-]+(?:=\S+)?|-[a-zA-Z]))*\s+(commit|merge)(?![\w-])")
KICAD_INPUTS = ("hardware/", "mechanical/export/", "tools/kicad.py", "tools/pcb", "tools/sch.py",
                "tools/lib-models.py")


def is_commit(cmd):
    m = GIT_COMMIT.search(cmd)
    if not m:
        return False
    tail = cmd[m.end():].split("&&")[0].split(";")[0]
    return not re.search(r"(^|\s)--(abort|quit)\b", tail)


def tree_of(cmd, cwd):
    """The work tree the command commits in: `git -C <dir>`, else a leading `cd <dir>`, else cwd."""
    m = re.search(r"\bgit\s+-C\s+(\S+)", cmd) or re.match(r"\s*cd\s+(\S+)\s*(?:&&|;)", cmd)
    d = os.path.join(cwd, os.path.expanduser(m.group(1).strip("'\""))) if m else cwd
    r = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def red_reason(cmd, cwd):
    """The Gate-Red: trailer's text, from the command or a -F file, or None."""
    m = re.search(r"Gate-Red:\s*([^\n\"']+)", cmd)
    if m and m.group(1).strip():
        return m.group(1).strip()
    try:
        words = shlex.split(cmd)
    except ValueError:
        words = cmd.split()
    for i, w in enumerate(words):
        f = words[i + 1] if w in ("-F", "--file") and i + 1 < len(words) else (
            w.split("=", 1)[1] if w.startswith("--file=") else None)
        if f:
            try:
                m = re.search(r"^Gate-Red:\s*(.+)$", open(os.path.join(cwd, f)).read(), re.M)
            except OSError:
                m = None
            if m:
                return m.group(1).strip()
    return None


def needs_kicad(cmd, tree):
    if re.search(r"\bgit\s+add\b|\scommit\b[^;&|]*\s(-a|--all|-[a-zA-Z]*a[a-zA-Z]*)\b", cmd) \
            or re.search(r"\bmerge\b", cmd):
        return "the command stages or merges files the gate cannot see yet"
    r = subprocess.run(["git", "-C", tree, "diff", "--cached", "--name-only"], capture_output=True, text=True)
    hit = [p for p in r.stdout.split() if p.startswith(KICAD_INPUTS)]
    return f"{len(hit)} staged KiCad input(s), e.g. {hit[0]}" if hit else None


def toolchain(tree):
    """Warnings for a tool that differs from tools/toolchain.yaml (G7) - shown, never fatal."""
    try:
        pins = {k: str(v) for k, v in (l.split(":", 1) for l in open(os.path.join(tree, "tools", "toolchain.yaml"))
                                       if re.match(r"\w+:", l))}
    except OSError:
        return []
    pins = {k: v.split("#")[0].strip() for k, v in pins.items()}
    out = []

    def run(*a):
        try:
            r = subprocess.run(a, capture_output=True, text=True, timeout=20)
            return r.stdout + r.stderr
        except (OSError, subprocess.TimeoutExpired):
            return ""
    kc = run("kicad-cli", "version").strip()
    key = lambda v: [int(x) for x in re.findall(r"\d+", v)]  # noqa: E731
    if kc and "kicad_min" in pins and key(kc) < key(pins["kicad_min"]):
        out.append(f"KiCad {kc} < {pins['kicad_min']}")
    m = re.search(r"ngspice-(\d+)", run("ngspice", "-v"))
    if m and "ngspice_major" in pins and m.group(1) != pins["ngspice_major"]:
        out.append(f"ngspice {m.group(1)} (results.yaml were made with {pins['ngspice_major']})")
    return [f"toolchain: WARNING {'; '.join(out)} - tools/toolchain.yaml"] if out else []


def start(args, tree):
    return subprocess.Popen([sys.executable] + args, cwd=tree, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)


def finish(p, t0, name, verdict):
    try:
        out, _ = p.communicate(timeout=max(1, TIMEOUT - (time.time() - t0)))
    except subprocess.TimeoutExpired:
        p.kill()
        return False, f"{name}: TIMED OUT after {TIMEOUT} s - it said nothing about the tree", ""
    line = verdict(out)
    if line and line.startswith(name + ":"):
        line = line[len(name) + 1:].strip()
    if p.returncode == 0:
        return True, f"{name}: {line or 'PASS'} ({time.time() - t0:.0f} s)", out
    return False, (f"{name}: {line} ({time.time() - t0:.0f} s)" if line else
                   f"{name}: CRASHED (exit {p.returncode}) - no verdict line; run it directly"), out


def gate(cmd, cwd):
    tree = tree_of(cmd, cwd)
    if not tree or not os.path.exists(os.path.join(tree, "tools", "check-staleness.py")):
        return None                              # not a Woody tree: not this gate's business
    t0 = time.time()
    procs = [("staleness", start([os.path.join(tree, "tools", "check-staleness.py")], tree),
              lambda o: next((l for l in o.splitlines() if l.startswith(("PASS", "FAIL"))), None))]
    why = needs_kicad(cmd, tree)
    if not why:
        skipped = "kicad: SKIPPED - nothing staged is a KiCad input (run `python3 tools/kicad.py check` by hand if that is wrong)"
    elif not shutil.which("kicad-cli"):
        skipped = f"kicad: SKIPPED - NO kicad-cli on PATH, so the boards were NOT checked ({why}); run tools/setup-env.sh"
    else:
        skipped = None
        procs.append(("kicad", start([os.path.join(tree, "tools", "kicad.py"), "check"], tree),
                      lambda o: next((l for l in o.splitlines() if l.startswith("kicad: ")), None)))
    results = [finish(p, t0, name, v) for name, p, v in procs]
    lines = [r[1] for r in results] + ([skipped] if skipped else []) + toolchain(tree)
    try:
        os.makedirs(os.path.join(tree, ".staleness"), exist_ok=True)
        with open(os.path.join(tree, ".staleness", "gate.txt"), "w") as fh:
            fh.write("\n".join(lines) + "\n\n" + "\n\n".join(r[2] for r in results))
        with open(os.path.join(tree, ".staleness-report.txt"), "w") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError:
        pass
    summary = " | ".join(lines)
    detail = (" Detail: .staleness/report.txt (staleness, by name) and .staleness/gate.txt "
              "(every checker's whole output) - read them, do not re-run for detail.")
    if all(r[0] for r in results):
        return {"systemMessage": "commit gate: " + summary,
                "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                       "additionalContext": "commit gate PASSED: " + summary}}
    reason = red_reason(cmd, tree)
    if reason:
        return {"systemMessage": f"commit gate: RED, committed under Gate-Red ({reason}): {summary}",
                "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                       "additionalContext": (f"commit gate FAILED and the commit carries "
                                                             f"'Gate-Red: {reason}', so it goes ahead red: {summary}."
                                                             + detail)}}
    return {"systemMessage": "commit gate: FAIL - commit refused: " + summary,
            "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": (
                                       f"Commit gate FAILED: {summary}.{detail} Fix the failures; or, if this "
                                       f"commit must go in red (a known-red state another change is working "
                                       f"off), add a trailer line 'Gate-Red: <which failures, and why>' to the "
                                       f"commit message - it stays in the log, and `git log --grep Gate-Red` "
                                       f"lists every red commit.")}}


def self_test():
    yes = ["git commit -m x", "cd /a && git commit -am 'x'", "git -C /r commit", "git merge origin/main",
           "git -c user.name=x commit --amend", "ls; git commit -F msg.txt", "(git merge --continue)"]
    no = ["ls", "git status", "git merge-base a b", "git merge --abort", "echo git commit-tree",
          "git log --grep commit", "grep -n 'git commit' CLAUDE.md | head", "git diff --cached"]
    bad = [c for c in yes if not is_commit(c)] + [c for c in no if is_commit(c)]
    print("commit-gate self-test:", "PASS" if not bad else f"FAIL {bad}")
    return 1 if bad else 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not is_commit(cmd):
        return 0
    try:
        out = gate(cmd, data.get("cwd") or os.getcwd())
    except Exception as e:      # noqa: BLE001 - a gate that crashes must not read as a pass
        import traceback
        out = {"systemMessage": f"commit gate: CRASHED ({e!r}) - commit refused",
               "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                      "permissionDecisionReason": (
                                          "tools/commit-gate.py crashed, so nothing was checked: "
                                          + traceback.format_exc(limit=3)
                                          + " Fix the gate; meanwhile a 'Gate-Red: <why>' trailer lets the "
                                            "commit through, unchecked and on the record.")}}
        if red_reason(cmd, data.get("cwd") or os.getcwd()):
            out["hookSpecificOutput"].pop("permissionDecision")
            out["hookSpecificOutput"]["additionalContext"] = out["hookSpecificOutput"].pop("permissionDecisionReason")
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
