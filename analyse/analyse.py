#!/usr/bin/env python3
"""
Static analysis: will `release/data/openknx-release.json` (written by the
`release-json` branch of OGM-Common) be complete for every OpenKNX application
(OAM) release product?

What the release JSON needs per product (see OGM-Common
scripts/setup/reusable/Build-ReleaseJson.ps1):

  * the product is added by Build-Step.ps1 (reusable script in
    lib/OGM-Common/scripts/setup/reusable) -> needs scripts/Build-Release.ps1
    to call the reusable Build-Release-Preprocess/Build-Step/Postprocess scripts
  * deviceId/deviceName come from .pio/build/<env>/openknx-build.json, which
    scripts/pio/prepare.py writes by running the toolchain preprocessor
    (`-E -dM`) over `#include <hardware.h>` with the env's defines/include paths
    and grepping `#define DEVICE_ID "..."` / `#define DEVICE_NAME "..."`
  * appId comes from include/knxprod.h (MAIN_OpenKnxId/MAIN_ApplicationNumber),
    which OpenKNXproducer writes; for kaenxcreator this is only known when a
    knxprod.h with those defines exists in the repo

This script re-creates that chain statically for every OAM:

  1. repo list from openknx.github.io/docs/releases.json + inclusion rule of
     scripts/app_config.py (prefix OAM-, special names, exclusion list)
  2. `git clone --depth 1` of every OAM into repos/<name> (cloned content is
     untrusted: it is parsed only, never executed)
  3. dependencies.txt -> pinned commits; OGM-HardwareConfig / OGM-Common are
     exported at the pinned commit from full-history cache clones; OFM-* libs
     are cloned (tip of the pinned branch) because hardware.h may include their
     headers; lib/ of the OAM is populated with symlinks to those
  4. scripts/Build-Release.ps1 is parsed (comments stripped) for Build-Step
     calls (env, firmwareName, featureSet, productName, -DebugBuild) and the
     `if ($releaseIndication -eq "...")` block they sit in
  5. scripts/OpenKNX-Build-Settings.ps1 -> compileWith
  6. platformio.ini resolved with `pio project config --json-output` (fallback:
     own extends/interpolation parser); -D / -I flags extracted
  7. host g++ `-x c++ -E -dM` over `#include <hardware.h>` (plus `-dD` to find
     the file that defined DEVICE_ID); missing headers (Arduino.h, ...) are
     stubbed and recorded; a textual #ifdef scan is the fallback
  8. classification per product and per OAM, result.json + report.md

Usage:  python3 -I analyse.py [--only NAME,NAME] [--no-clone] [--skip-pio]
Re-runnable: existing clones and caches are reused; delete repos/ or cache/ to
start fresh. Python 3 stdlib only; `pio` (PlatformIO Core) is optional.
"""

import argparse
import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import Counter, OrderedDict

# ---------------------------------------------------------------- settings --
BASE = os.path.dirname(os.path.abspath(__file__))
REPOS = os.path.join(BASE, "repos")
CACHE = os.path.join(BASE, "cache")
TREES = os.path.join(CACHE, "trees")
LIBS = os.path.join(CACHE, "libs")
STUBS = os.path.join(CACHE, "stubs")
RELEASES_JSON = "/home/user/openknx/openknx.github.io/docs/releases.json"
GITHUB = "https://github.com/OpenKNX/"
PIO = os.path.expanduser("~/.local/bin/pio")
GXX = shutil.which("g++") or shutil.which("gcc")

# inclusion rule from openknx.github.io/scripts/app_config.py
APP_PREFIX = "OAM-"
APP_SPECIAL = ["SOM-UP", "GW-REG1-Dali", "SEN-UP1-8xTH", "BEM-GardenControl"]
APP_EXCLUSION = ["OAM-TestApp"]

# full-history caches (short SHAs from dependencies.txt must be resolvable)
FULL_CACHES = {"OGM-Common": "v1", "OGM-HardwareConfig": "v1"}

REUSABLE_DIR = "scripts/setup/reusable"
STEP_SCRIPTS = {"Build-Release-Preprocess.ps1": "pre", "Build-Step.ps1": "step",
                "Build-Release-Postprocess.ps1": "post"}
VALID_FEATURESETS = {"bin", "uf2", "esp32", "esp32-ip", "esp32-tp", "esp32-tpip", "esp32-iptp",
                     "rp2040-ip", "rp2040-tp", "rp2040-tpip", "rp2040-iptp",
                     "rp2350-ip", "rp2350-tp", "rp2350-tpip", "rp2350-iptp"}
CLONE_TIMEOUT = 300

LOG = []


def log(msg):
    print(msg, flush=True)
    LOG.append(msg)


def run(cmd, cwd=None, timeout=120, input_text=None, env=None):
    try:
        return subprocess.run(cmd, cwd=cwd, timeout=timeout, capture_output=True,
                              text=True, input=input_text, env=env, errors="replace")
    except subprocess.TimeoutExpired as e:
        r = subprocess.CompletedProcess(cmd, 124, stdout=e.stdout or "", stderr="timeout")
        return r


# ------------------------------------------------------------------ helpers --
def read_text_any(path):
    """dependencies.txt etc. may be UTF-16 (PowerShell default) or UTF-8 with BOM."""
    raw = open(path, "rb").read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    if len(raw) > 1 and raw[1:2] == b"\x00" and raw[0:1] != b"\x00":
        return raw.decode("utf-16-le", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def git_head(path):
    r = run(["git", "rev-parse", "HEAD"], cwd=path)
    sha = r.stdout.strip() if r.returncode == 0 else None
    r = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    br = r.stdout.strip() if r.returncode == 0 else None
    return br, sha


def git_tracked(path, rel):
    r = run(["git", "ls-files", "--error-unmatch", rel], cwd=path)
    return r.returncode == 0


# ---------------------------------------------------------------- cloning ----
def ensure_clone(name, allow_clone=True):
    dest = os.path.join(REPOS, name)
    if os.path.isdir(os.path.join(dest, ".git")):
        return dest, None
    if not allow_clone:
        return None, "not cloned (--no-clone)"
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    log(f"  cloning {name} ...")
    r = run(["git", "clone", "--depth", "1", "-q", GITHUB + name, dest], timeout=CLONE_TIMEOUT)
    if r.returncode != 0:
        if os.path.isdir(dest):
            shutil.rmtree(dest, ignore_errors=True)
        return None, "clone failed: " + (r.stderr.strip().splitlines() or ["?"])[-1][:200]
    return dest, None


def ensure_full_cache(name, branch):
    dest = os.path.join(CACHE, name.lower() + "-git")
    if not os.path.isdir(os.path.join(dest, ".git")):
        log(f"  cloning full history of {name} ...")
        r = run(["git", "clone", "-q", "--branch", branch, GITHUB + name, dest], timeout=CLONE_TIMEOUT)
        if r.returncode != 0:
            log(f"  WARNING: full clone of {name} failed: {r.stderr.strip()[:200]}")
            return None
        run(["git", "remote", "set-branches", "origin", "*"], cwd=dest)
        run(["git", "fetch", "-q", "origin"], cwd=dest, timeout=CLONE_TIMEOUT)
        if run(["git", "rev-parse", "--is-shallow-repository"], cwd=dest).stdout.strip() == "true":
            run(["git", "fetch", "-q", "--unshallow", "origin"], cwd=dest, timeout=CLONE_TIMEOUT)
    return dest


def resolve_sha(cache, short):
    if not cache or not short:
        return None
    r = run(["git", "rev-parse", "--verify", "-q", short + "^{commit}"], cwd=cache)
    return r.stdout.strip() if r.returncode == 0 else None


def tip_sha(cache, branch):
    r = run(["git", "rev-parse", "--verify", "-q", "origin/" + branch + "^{commit}"], cwd=cache)
    return r.stdout.strip() if r.returncode == 0 else None


def export_tree(name, cache, sha):
    """Export <name> at <sha> into cache/trees/<name>/<sha> (cached)."""
    dest = os.path.join(TREES, name, sha)
    if os.path.isdir(dest) and os.listdir(dest):
        return dest
    os.makedirs(dest, exist_ok=True)
    r = subprocess.run(f"git archive --format=tar {sha} | tar -x -C {shlex.quote(dest)}",
                       shell=True, cwd=cache, capture_output=True, text=True)
    if r.returncode != 0:
        shutil.rmtree(dest, ignore_errors=True)
        return None
    return dest


def ensure_lib_clone(name, branch):
    """Tip clone of an OFM-*/other lib (one per name, first branch wins)."""
    dest = os.path.join(LIBS, name)
    if os.path.isdir(os.path.join(dest, ".git")):
        return dest
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    cmd = ["git", "clone", "--depth", "1", "-q"]
    if branch:
        cmd += ["--branch", branch]
    r = run(cmd + [GITHUB + name, dest], timeout=CLONE_TIMEOUT)
    if r.returncode != 0 and branch:
        shutil.rmtree(dest, ignore_errors=True)
        r = run(["git", "clone", "--depth", "1", "-q", GITHUB + name, dest], timeout=CLONE_TIMEOUT)
    if r.returncode != 0:
        shutil.rmtree(dest, ignore_errors=True)
        return None
    return dest


# ------------------------------------------------------ dependencies.txt -----
DEP_RE = re.compile(r"^\s*([0-9a-fA-F]{6,40})\s+(\S+)\s+(\S+)\s+(\S+)\s*$")


def parse_dependencies(repo):
    path = os.path.join(repo, "dependencies.txt")
    deps = []
    if not os.path.isfile(path):
        return None
    for line in read_text_any(path).splitlines():
        m = DEP_RE.match(line.strip("\ufeff"))
        if not m:
            continue
        sha, branch, libdir, url = m.groups()
        libdir = libdir.replace("\\", "/")
        name = libdir.rstrip("/").split("/")[-1]
        deps.append({"sha": sha, "branch": branch, "libdir": libdir, "name": name, "url": url})
    return deps


# ------------------------------------------------------- PowerShell parsing --
def strip_ps_comments(text):
    out = []
    i, n = 0, len(text)
    quote = None
    while i < n:
        c = text[i]
        if quote:
            out.append(c)
            if c == quote:
                if i + 1 < n and text[i + 1] == quote:  # doubled quote
                    out.append(text[i + 1]); i += 1
                else:
                    quote = None
            i += 1
            continue
        if c in ("'", '"'):
            quote = c; out.append(c); i += 1; continue
        if c == "<" and text.startswith("<#", i):
            j = text.find("#>", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c == "#":
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(c); i += 1
    return "".join(out)


def ps_tokens(line):
    """Split a PowerShell command line into tokens (quotes removed)."""
    toks, cur, quote = [], "", None
    i = 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == quote:
                if i + 1 < len(line) and line[i + 1] == quote:
                    cur += c; i += 1
                else:
                    quote = None
            else:
                cur += c
        elif c in ("'", '"'):
            quote = c
        elif c.isspace():
            if cur:
                toks.append(cur); cur = ""
        else:
            cur += c
        i += 1
    if cur:
        toks.append(cur)
    return toks


REL_VAR_RE = re.compile(r"releaseIndication|appRelease|\$args\[0\]|\$release", re.I)
STR_RE = re.compile(r"""["']([^"']*)["']""")


def block_label(cond):
    """Label for an if(...) condition: the release indications it compares with."""
    if not REL_VAR_RE.search(cond):
        return None
    strs = STR_RE.findall(cond)
    if not strs:
        return "?" + cond.strip()[:40]
    neg = "-ne" in cond or "-notin" in cond or "!" in cond.split("-eq")[0]
    lab = "|".join(strs)
    return ("not " + lab) if neg and "-eq" not in cond else lab


def parse_build_release(text):
    """Collect script calls from Build-Release.ps1 with the if-block they sit in."""
    text = strip_ps_comments(text)
    calls, other_ps1 = [], []
    stack = []          # labels of open braces
    # target tables:  $xyzTargets = @( @{ Env = "..."; Name = "..."; Ext = "..." } ... )
    tables, cur_table = OrderedDict(), None
    for raw in text.splitlines():
        s = raw.strip()
        m = re.match(r"\$(\w+)\s*=\s*@\(\s*$", s)
        if m:
            cur_table = m.group(1); tables[cur_table] = []; continue
        if cur_table:
            if s.startswith(")"):
                cur_table = None; continue
            m = re.match(r"@\{(.*)\}\s*$", s)
            if m:
                entry = {}
                for kv in m.group(1).split(";"):
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        entry[k.strip()] = v.strip().strip('"\'')
                tables[cur_table].append(entry)
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # detect if / elseif / else with releaseIndication
        m = re.search(r"\b(if|elseif)\s*\((.*)\)\s*\{?", line, re.I)
        lab = None
        if m:
            lab = block_label(m.group(2))
        elif re.search(r"^\}?\s*else\s*\{", line, re.I):
            lab = "else"
        # calls (one per line is the convention)
        for tok in ps_tokens(line):
            if tok.lower().endswith(".ps1"):
                t = tok.replace("\\", "/")
                base = os.path.basename(t)
                if base in STEP_SCRIPTS or base == "OpenKNX-Build-Settings.ps1":
                    pass
                elif base not in other_ps1:
                    other_ps1.append(t)
        toks = ps_tokens(line)
        for idx, tok in enumerate(toks):
            t = tok.replace("\\", "/")
            base = os.path.basename(t)
            if base in STEP_SCRIPTS:
                kind = STEP_SCRIPTS[base]
                if t.startswith("lib/OGM-Common/" + REUSABLE_DIR):
                    pkind = "reusable"
                elif t.startswith("../OGM-Common/" + REUSABLE_DIR):
                    pkind = "reusable-sibling"
                elif REUSABLE_DIR in t:
                    pkind = "reusable-other-path"
                else:
                    pkind = "local"
                args = toks[idx + 1:]
                if "|" in args:
                    args = args[:args.index("|")]
                call = {"script": t, "kind": kind, "pathKind": pkind, "args": args,
                        "block": next((l for l in reversed(stack) if l), "always")}
                if kind == "step":
                    call.update(parse_step_args(args))
                calls.append(call)
                break
        # brace bookkeeping (outside strings)
        for c in strip_strings(line):
            if c == "{":
                stack.append(lab if lab is not None else (stack[-1] if stack else None))
                lab = None
            elif c == "}":
                if stack:
                    stack.pop()
    # expand Build-Step calls inside `foreach ($t in $xyzTargets)` loops from the hashtable tables
    expanded = []
    for c in calls:
        if c["kind"] == "step" and c.get("dynamicArgs") and tables:
            fields = [re.sub(r"^\$\w+\.", "", a) for a in (c["env"], c["firmwareName"], c["featureSet"])]
            if all(f and not f.startswith("$") for f in fields):
                for tname, entries in tables.items():
                    for e in entries:
                        if fields[0] not in e:
                            continue
                        nc = dict(c)
                        nc.update(parse_step_args([e.get(fields[0], "?"), e.get(fields[1], "?"), e.get(fields[2], "?")]))
                        nc["debugBuild"] = c["debugBuild"]
                        nc["block"] = "table:" + tname + (" (default)" if re.search(r"standard|default", tname, re.I) else "")
                        nc["dynamicArgs"] = False
                        nc["expandedFrom"] = c["args"]
                        expanded.append(nc)
                continue
        expanded.append(c)
    return expanded, other_ps1


def strip_strings(line):
    return re.sub(r"""(["'])(?:(?!\1).)*\1""", "", line)


def parse_step_args(args):
    d = {"debugBuild": False, "env": None, "firmwareName": None, "featureSet": None,
         "productName": None, "dynamicArgs": False}
    pos = []
    i = 0
    while i < len(args):
        a = args[i]
        la = a.lower()
        if la == "-debugbuild":
            d["debugBuild"] = True
        elif la in ("-pioenv", "-firmwarename", "-featureset", "-productname", "-binaryformat", "-projectdir"):
            key = {"-pioenv": "env", "-firmwarename": "firmwareName", "-featureset": "featureSet",
                   "-binaryformat": "featureSet", "-productname": "productName", "-projectdir": None}[la]
            if i + 1 < len(args):
                if key:
                    d[key] = args[i + 1]
                i += 1
        elif a.startswith("-") and not a[1:2].isdigit():
            pass
        else:
            pos.append(a)
        i += 1
    for key, val in zip(["env", "firmwareName", "featureSet", "productName"], pos):
        if d[key] is None:
            d[key] = val
    if any("$" in str(v) for v in (d["env"], d["firmwareName"], d["featureSet"], d["productName"]) if v):
        d["dynamicArgs"] = True
    if d["productName"] is None and d["firmwareName"]:
        d["productName"] = d["firmwareName"].replace("firmware-", "")
    return d


def parse_settings(repo):
    """compileWith from scripts/OpenKNX-Build-Settings.ps1."""
    path = os.path.join(repo, "scripts", "OpenKNX-Build-Settings.ps1")
    info = {"exists": os.path.isfile(path), "compileWith": None, "source": None,
            "sourceName": None, "targetName": None}
    if not info["exists"]:
        return info
    text = strip_ps_comments(read_text_any(path))
    m = re.search(r"OpenKNX-Build-Settings\.ps1\s+\$\w+(?:\[\d+\])?\s*(.*)", text)
    if m:
        toks = ps_tokens(m.group(1))
        info["source"] = "common-settings-script"
        if len(toks) >= 1:
            info["sourceName"] = toks[0]
        if len(toks) >= 2:
            info["targetName"] = toks[1]
        info["compileWith"] = toks[2] if len(toks) >= 3 else "openknxproducer"
    for key in ("compileWith",):
        m2 = re.search(r"""(?:\$settings\.|\$settings\[\s*["']|^\s*)compileWith["']?\s*\]?\s*=\s*["']?([\w-]+)""",
                       text, re.M)
        if m2:
            info["compileWith"] = m2.group(1)
            info["source"] = (info["source"] or "local") + "+override" if info["source"] == "common-settings-script" else "local"
    for key in ("sourceName", "targetName"):
        m3 = re.search(r"""\$settings\.%s\s*=\s*["']([^"']+)["']""" % key, text)
        if m3:
            info[key] = m3.group(1)
    if info["compileWith"] is None:
        info["compileWith"] = "none(no compileWith)"
        info["source"] = info["source"] or "local"
    if not info["targetName"]:
        info["targetName"] = info["sourceName"]
    return info


# ----------------------------------------------------------- ini resolving --
def pio_project_config(repo):
    if not os.path.isfile(PIO):
        return None, "pio not installed"
    env = dict(os.environ, PLATFORMIO_DISABLE_PROGRESSBAR="true", PLATFORMIO_NO_ANSI="true")
    r = run([PIO, "project", "config", "--json-output"], cwd=repo, timeout=120, env=env)
    if r.returncode != 0:
        return None, "pio failed: " + r.stderr.strip()[-300:]
    try:
        data = json.loads(r.stdout)
    except ValueError as e:
        return None, f"pio output not json: {e}"
    cfg = OrderedDict()
    for section, opts in data:
        cfg[section] = OrderedDict((k, v) for k, v in opts)
    return cfg, None


class IniResolver:
    """Minimal PlatformIO-ini resolver: extra_configs, extends, ${sec.opt}."""

    def __init__(self, repo):
        self.repo = repo
        self.raw = OrderedDict()
        self.problems = []
        self.load(os.path.join(repo, "platformio.ini"))
        for extra in self.raw.get("platformio", {}).get("extra_configs", "").split("\n"):
            extra = extra.strip()
            if not extra:
                continue
            p = os.path.join(repo, extra)
            if os.path.isfile(p):
                self.load(p)
            else:
                self.problems.append(f"extra_configs missing: {extra}")

    def load(self, path):
        if not os.path.isfile(path):
            self.problems.append(f"missing ini: {os.path.relpath(path, self.repo)}")
            return
        cur = None
        for raw in read_text_any(path).splitlines():
            line = raw.rstrip()
            s = line.strip()
            if not s or s[0] in ";#":
                continue
            if s.startswith("[") and s.endswith("]"):
                cur = s[1:-1].strip()
                self.raw.setdefault(cur, OrderedDict())
                continue
            if cur is None:
                continue
            if line[0] in " \t" and self.raw[cur]:
                last = next(reversed(self.raw[cur]))
                self.raw[cur][last] += "\n" + s.split(" ;")[0].strip()
            elif "=" in s:
                k, v = s.split("=", 1)
                self.raw[cur][k.strip()] = v.split(" ;")[0].strip()
        return

    def resolved_section(self, name, seen=None):
        seen = seen or set()
        if name in seen:
            self.problems.append(f"extends cycle at {name}")
            return OrderedDict()
        seen = seen | {name}
        if name not in self.raw:
            self.problems.append(f"unknown section: {name}")
            return OrderedDict()
        out = OrderedDict()
        if name.startswith("env:") and "env" in self.raw:
            out.update(self.resolved_section("env", seen))
        for parent in [p.strip() for p in self.raw[name].get("extends", "").replace("\n", ",").split(",") if p.strip()]:
            out.update(self.resolved_section(parent, seen))
        for k, v in self.raw[name].items():
            if k != "extends":
                out[k] = v
        return out

    def interpolate(self, value, depth=0):
        if depth > 20:
            return value

        def rep(m):
            sec, opt = m.group(1), m.group(2)
            if sec == "sysenv":
                return os.environ.get(opt, "")
            if sec == "this":
                return ""
            s = self.raw.get(sec)
            if s is None:
                self.problems.append(f"interpolation of unknown section: ${{{sec}.{opt}}}")
                return ""
            rs = self.resolved_section(sec)
            if opt not in rs:
                self.problems.append(f"interpolation of unknown option: ${{{sec}.{opt}}}")
                return ""
            return self.interpolate(rs[opt], depth + 1)
        return re.sub(r"\$\{([\w:\-\.]+)\.([\w\-\.]+)\}", rep, value)

    def envs(self):
        return [s[4:] for s in self.raw if s.startswith("env:")]

    def env(self, name):
        sec = self.resolved_section("env:" + name)
        return OrderedDict((k, self.interpolate(v)) for k, v in sec.items())


def flags_from_value(val):
    if val is None:
        return []
    lines = val if isinstance(val, list) else str(val).split("\n")
    toks = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        try:
            toks.extend(shlex.split(line, posix=True))
        except ValueError:
            toks.extend(line.split())
    return toks


def defines_includes(tokens):
    defines, includes, undefs = OrderedDict(), [], []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "-D" and i + 1 < len(tokens):
            name, _, val = tokens[i + 1].partition("=")
            defines[name] = val if _ else "1"; i += 2; continue
        if t.startswith("-D") and len(t) > 2:
            name, _, val = t[2:].partition("=")
            defines[name] = val if _ else "1"; i += 1; continue
        if t == "-U" and i + 1 < len(tokens):
            undefs.append(tokens[i + 1]); defines.pop(tokens[i + 1], None); i += 2; continue
        if t.startswith("-U") and len(t) > 2:
            undefs.append(t[2:]); defines.pop(t[2:], None); i += 1; continue
        if t == "-I" and i + 1 < len(tokens):
            includes.append(tokens[i + 1]); i += 2; continue
        if t.startswith("-I") and len(t) > 2:
            includes.append(t[2:]); i += 1; continue
        i += 1
    return defines, includes, undefs


HW_PREFIXES = ("DEVICE_", "BOARD_", "OKNXHW_", "SOM_", "HARDWARE_", "HW_")


def arch_defines(envopts):
    plat = str(envopts.get("platform", "")).lower()
    board = str(envopts.get("board", "")).lower()
    fw = str(envopts.get("framework", "")).lower()
    d = {"ARDUINO": "10812"}
    if "raspberrypi" in plat or "rp2040" in plat or "pico" in board:
        d["ARDUINO_ARCH_RP2040"] = "1"
        d["PICO_RP2350" if ("2350" in board or "pico2" in board) else "PICO_RP2040"] = "1"
        arch = "rp2040"
    elif "espressif32" in plat or "esp32" in plat or "esp32" in board:
        d.update({"ESP32": "1", "ARDUINO_ARCH_ESP32": "1", "ESP_PLATFORM": "1"})
        arch = "esp32"
    elif "atmelsam" in plat or "samd" in plat:
        d.update({"ARDUINO_ARCH_SAMD": "1", "__SAMD21G18A__": "1"})
        arch = "samd"
    else:
        arch = "unknown"
    if "arduino" not in fw and fw:
        d.pop("ARDUINO", None)
    return arch, d


# ----------------------------------------------------------- preprocessing --
MISSING_RE = re.compile(r"fatal error: ([^:\n]+): No such file or directory")


def preprocess(repo, defines, includes, extra_defines, stubdir, source_roots):
    """Mimic prepare.py: `$CXX -x c++ ... -E -dM -` with `#include <hardware.h>`."""
    os.makedirs(stubdir, exist_ok=True)
    inc = []
    for p in includes:
        ap = os.path.normpath(os.path.join(repo, p))
        if os.path.isdir(ap) and ap not in inc:
            inc.append(ap)
    for p in ["include", "src"]:
        ap = os.path.join(repo, p)
        if os.path.isdir(ap) and ap not in inc:
            inc.append(ap)
    libdir = os.path.join(repo, "lib")
    if os.path.isdir(libdir):
        for lib in sorted(os.listdir(libdir)):
            for sub in ("include", "src", ""):
                ap = os.path.normpath(os.path.join(libdir, lib, sub))
                if os.path.isdir(ap) and ap not in inc:
                    inc.append(ap)
    base = [GXX, "-x", "c++", "-E", "-w"]
    for k, v in extra_defines.items():
        base += [f"-D{k}={v}"]
    for k, v in defines.items():
        base += [f"-D{k}={v}" if v != "1" else f"-D{k}"]
    for p in inc:
        base += ["-I", p]
    base += ["-idirafter", stubdir]
    stubs, result = [], {}
    for attempt in range(40):
        r = run(base + ["-dM", "-"], cwd=repo, input_text="#include <hardware.h>\n", timeout=60)
        missing = MISSING_RE.findall(r.stderr)
        if r.returncode != 0 and missing:
            created = False
            for miss in missing:
                stub = os.path.join(stubdir, miss.replace("\\", "/"))
                if not os.path.exists(stub):
                    os.makedirs(os.path.dirname(stub), exist_ok=True)
                    open(stub, "w").write("/* stub created by analyse.py */\n")
                    stubs.append(miss); created = True
            if created:
                continue
        break
    result["stubs"] = stubs
    result["returncode"] = r.returncode
    errs = [l for l in r.stderr.splitlines() if "error" in l.lower()]
    result["errors"] = errs[:8]
    for key, define in (("deviceId", "DEVICE_ID"), ("deviceName", "DEVICE_NAME")):
        m = re.search(r'^#define %s "(.*)"$' % define, r.stdout, re.M)
        result[key] = m.group(1) if m else None
    # non-string DEVICE_ID / DEVICE_NAME (would not match prepare.py's regex):
    # record the raw macro body and what it expands to (what the firmware sees)
    for key, define in (("deviceId", "DEVICE_ID"), ("deviceName", "DEVICE_NAME")):
        m = re.search(r'^#define %s (.*)$' % define, r.stdout, re.M)
        if m and result[key] is None:
            result[key + "Raw"] = m.group(1).strip()
            probe = run(base + ["-P", "-"], cwd=repo, timeout=60,
                        input_text="#include <hardware.h>\n@@PROBE@@ %s @@END@@\n" % define)
            mm = re.search(r"@@PROBE@@\s*(.*?)\s*@@END@@", probe.stdout, re.S)
            if mm:
                exp = mm.group(1).strip()
                parts = re.findall(r'"((?:[^"\\]|\\.)*)"', exp)
                result[key + "Expanded"] = "".join(parts) if parts and re.fullmatch(r'(\s*"(?:[^"\\]|\\.)*"\s*)+', exp) else exp
    # where was it defined? (-dD keeps #define lines with line markers)
    r2 = run(base + ["-dD", "-"], cwd=repo, input_text="#include <hardware.h>\n", timeout=60)
    cur, defs = "<stdin>", []
    for line in r2.stdout.splitlines():
        mm = re.match(r'^# \d+ "([^"]*)"', line)
        if mm:
            cur = mm.group(1); continue
        mm = re.match(r'^#(define|undef) (DEVICE_ID|DEVICE_NAME)\b\s*(.*)$', line)
        if mm:
            defs.append({"op": mm.group(1), "macro": mm.group(2), "value": mm.group(3).strip(),
                         "file": cur, "origin": classify_origin(cur, repo, source_roots)})
    result["definitions"] = defs
    last_id = [d for d in defs if d["macro"] == "DEVICE_ID" and d["op"] == "define"]
    result["deviceIdOrigin"] = last_id[-1]["origin"] if last_id else None
    result["deviceIdFile"] = last_id[-1]["file"] if last_id else None
    result["includePaths"] = [os.path.relpath(p, repo) if p.startswith(repo) else p for p in inc]
    return result


def classify_origin(path, repo, roots):
    if path in ("<command-line>", "<stdin>", "<built-in>"):
        return "build-flags"
    ap = os.path.normpath(os.path.join(repo, path)) if not os.path.isabs(path) else os.path.normpath(path)
    rp = os.path.realpath(ap)
    for label, root in roots:
        if root and (rp.startswith(os.path.realpath(root) + os.sep) or ap.startswith(root + os.sep)):
            return label
    if rp.startswith(os.path.realpath(STUBS)):
        return "stub"
    if rp.startswith(os.path.realpath(repo) + os.sep):
        return "oam:" + os.path.relpath(rp, os.path.realpath(repo))
    return "other:" + path


# ---------------------------------------------------------- textual scan -----
def header_files(root):
    out = []
    for dp, dn, fn in os.walk(root, followlinks=True):
        dn[:] = [d for d in dn if d not in (".git", ".pio", "doc", "docs")]
        for f in fn:
            if f.endswith((".h", ".hpp")):
                out.append(os.path.join(dp, f))
    return out


def textual_scan(files, define_names):
    """Which #ifdef <define> blocks in the given headers define DEVICE_ID?"""
    hits = []
    names = set(define_names)
    for f in files:
        try:
            lines = read_text_any(f).splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            m = re.match(r"\s*#\s*(?:ifdef\s+(\w+)|if\s+defined\s*\(?\s*(\w+)\s*\)?)\s*$", line)
            if not m:
                continue
            name = m.group(1) or m.group(2)
            if name not in names:
                continue
            depth, did, dname = 0, None, None
            for l in lines[i:]:
                s = l.strip()
                if re.match(r"#\s*if", s):
                    depth += 1
                elif re.match(r"#\s*endif", s):
                    depth -= 1
                    if depth == 0:
                        break
                mm = re.match(r'#\s*define\s+DEVICE_ID\s+"(.*)"', s)
                if mm:
                    did = mm.group(1)
                mm = re.match(r'#\s*define\s+DEVICE_NAME\s+"(.*)"', s)
                if mm:
                    dname = mm.group(1)
            if did or dname:
                hits.append({"define": name, "file": f, "deviceId": did, "deviceName": dname})
    return hits


# ------------------------------------------------------------- analysis -----
def analyse_oam(name, meta, args, caches):
    res = OrderedDict(repo=name, repoUrl=meta.get("repo_url", GITHUB + name),
                      archived=bool(meta.get("archived")), inReleasesJson=meta.get("_listed", True))
    repo, err = ensure_clone(name, allow_clone=not args.no_clone)
    if err:
        res["analysed"] = False
        res["notAnalysedReason"] = err
        return res
    res["analysed"] = True
    res["defaultBranch"], res["headSha"] = git_head(repo)
    res["warnings"] = []

    # ---- dependencies / lib population
    deps = parse_dependencies(repo)
    res["dependenciesTxt"] = deps is not None
    res["libs"] = OrderedDict()
    pins = {d["name"]: d for d in (deps or [])}
    roots = []
    for libname, default_branch in FULL_CACHES.items():
        cache = caches[libname]
        pin = pins.get(libname)
        entry = OrderedDict(pinned=pin["sha"] if pin else None, branch=pin["branch"] if pin else None)
        sha = resolve_sha(cache, pin["sha"]) if pin else None
        if pin and sha:
            entry["resolved"] = True; entry["sha"] = sha; entry["used"] = "pinned"
        else:
            entry["resolved"] = False if pin else None
            sha = tip_sha(cache, (pin["branch"] if pin else default_branch)) or tip_sha(cache, default_branch)
            entry["sha"] = sha; entry["used"] = "tip"
            if pin:
                res["warnings"].append(f"{libname}: pinned commit {pin['sha']} not found, using tip of {default_branch}")
        tree = export_tree(libname, cache, sha) if sha else None
        entry["path"] = tree
        res["libs"][libname] = entry
        roots.append(({"OGM-HardwareConfig": "hwconfig", "OGM-Common": "common"}[libname], tree))
    hw = res["libs"]["OGM-HardwareConfig"]
    res["hwconfig"] = OrderedDict(pin=hw["pinned"], resolved=hw["resolved"], used=hw["used"], sha=hw["sha"])

    libdir = os.path.join(repo, "lib")
    os.makedirs(libdir, exist_ok=True)
    wanted = OrderedDict()
    for libname, entry in res["libs"].items():
        if entry["path"]:
            wanted[libname] = entry["path"]
    for d in (deps or []):
        if d["name"] in wanted or d["name"] in FULL_CACHES:
            continue
        if d["name"].startswith(("OFM-", "OGM-")) or d["name"] in ("knx",):
            if d["name"] == "knx":
                continue
            p = ensure_lib_clone(d["name"], d["branch"])
            if p:
                wanted[d["name"]] = p
            else:
                res["warnings"].append(f"lib {d['name']} could not be cloned")
    # libs referenced by extra_configs but not in dependencies.txt
    pio_ini = os.path.join(repo, "platformio.ini")
    if os.path.isfile(pio_ini):
        for m in re.finditer(r"lib/([\w\-\.]+)/", read_text_any(pio_ini)):
            ln = m.group(1)
            if ln not in wanted and ln.startswith(("OFM-", "OGM-")):
                p = ensure_lib_clone(ln, None)
                if p:
                    wanted[ln] = p
                    res["warnings"].append(f"lib {ln} referenced by platformio.ini but not in dependencies.txt (tip used)")
    for ln, target in wanted.items():
        dst = os.path.join(libdir, ln)
        if os.path.isdir(dst) and not os.path.islink(dst) and not os.listdir(dst):
            os.rmdir(dst)  # empty dir: git submodule (gitlink) or placeholder
            res["warnings"].append(f"lib/{ln} is an empty directory (submodule?) in the repo, replaced")
        if os.path.islink(dst) or not os.path.exists(dst):
            if os.path.islink(dst):
                os.unlink(dst)
            os.symlink(target, dst)
        else:
            res["warnings"].append(f"lib/{ln} is a committed directory in the repo, kept as is")
    res["libsPopulated"] = list(wanted)
    # extra_configs with wrong case (works on Windows, not here): add a symlink in the lib tree
    if os.path.isfile(pio_ini):
        txt = read_text_any(pio_ini)
        m = re.search(r"^extra_configs\s*=\s*(.*?)(?=^\S|\Z)", txt, re.M | re.S)
        for extra in (m.group(1).split("\n") if m else []):
            extra = extra.strip()
            if not extra or extra.startswith(";"):
                continue
            ap = os.path.join(repo, extra)
            if os.path.isfile(ap):
                continue
            d, b = os.path.split(ap)
            if os.path.isdir(d):
                cands = [f for f in os.listdir(d) if f.lower() == b.lower()]
                if cands:
                    os.symlink(cands[0], ap)
                    res["warnings"].append(f"extra_configs {extra}: wrong case (found {cands[0]}), linked for the analysis")

    # ---- build scripts
    br_path = os.path.join(repo, "scripts", "Build-Release.ps1")
    bs = OrderedDict()
    bs["buildReleaseExists"] = os.path.isfile(br_path)
    bs["localScripts"] = sorted(f for f in os.listdir(os.path.join(repo, "scripts")) if f.endswith(".ps1")) \
        if os.path.isdir(os.path.join(repo, "scripts")) else []
    calls, other = [], []
    if bs["buildReleaseExists"]:
        calls, other = parse_build_release(read_text_any(br_path))
    bs["preprocess"] = [c["pathKind"] for c in calls if c["kind"] == "pre"]
    bs["postprocess"] = [c["pathKind"] for c in calls if c["kind"] == "post"]
    bs["otherScriptsCalled"] = other
    steps = [c for c in calls if c["kind"] == "step"]
    bs["buildStepCalls"] = len(steps)
    bs["buildStepPathKinds"] = sorted(set(c["pathKind"] for c in steps))
    local_step = os.path.isfile(os.path.join(repo, "scripts", "Build-Step.ps1"))
    bs["localBuildStepExists"] = local_step
    if not bs["buildReleaseExists"]:
        bs["status"] = "missing-build-release"
    elif not steps and not bs["preprocess"]:
        bs["status"] = "custom-build-scripts"
    elif not steps:
        bs["status"] = "template-no-build-step"
    elif all(k in ("reusable", "reusable-sibling") for k in bs["buildStepPathKinds"]) \
            and all(k in ("reusable", "reusable-sibling") for k in bs["preprocess"] + bs["postprocess"]) \
            and bs["preprocess"] and bs["postprocess"]:
        bs["status"] = "reusable"
        if "reusable-sibling" in bs["buildStepPathKinds"] + bs["preprocess"]:
            bs["status"] = "reusable-sibling-path"
    else:
        bs["status"] = "custom-build-scripts"
    res["buildScripts"] = bs

    # ---- knxprod tool / appId
    st = parse_settings(repo)
    res["settings"] = st
    knxprod = os.path.join(repo, "include", "knxprod.h")
    app = OrderedDict(compileWith=st["compileWith"])
    app["knxprodHeaderCommitted"] = os.path.isfile(knxprod) and git_tracked(repo, "include/knxprod.h")
    app["appIdInCommittedHeader"] = None
    if os.path.isfile(knxprod):
        t = read_text_any(knxprod)
        m1 = re.search(r"#define MAIN_OpenKnxId\s+(\S+)", t)
        m2 = re.search(r"#define MAIN_ApplicationNumber\s+(\S+)", t)
        if m1 and m2:
            try:
                app["appIdInCommittedHeader"] = "0x%04X" % ((int(m1.group(1), 0) << 8) | int(m2.group(1), 0))
            except ValueError:
                app["appIdInCommittedHeader"] = f"{m1.group(1)}/{m2.group(1)}"
    ae = [f for f in os.listdir(repo) if f.endswith(".ae-manu")]
    app["kaenxProject"] = ae
    cw = (st["compileWith"] or "").lower()
    if cw == "openknxproducer":
        app["appIdExpected"] = "yes (OpenKNXproducer writes include/knxprod.h)"
        app["appIdStatus"] = "expected"
    elif cw == "kaenxcreator":
        if app["appIdInCommittedHeader"]:
            app["appIdExpected"] = f"probably ({app['appIdInCommittedHeader']} in committed include/knxprod.h, must be kept current)"
            app["appIdStatus"] = "committed-header"
        else:
            app["appIdExpected"] = "unknown (kaenx)"
            app["appIdStatus"] = "unknown"
    else:
        app["appIdExpected"] = f"no tool ({st['compileWith']}): knxprod.h not generated by the release build"
        app["appIdStatus"] = "unknown"
    res["appId"] = app

    # ---- platformio config
    cfg_src, cfg, envs, problems = None, None, [], []
    has_ini = os.path.isfile(pio_ini)
    own = None
    if has_ini:
        own = IniResolver(repo)
        problems = list(dict.fromkeys(own.problems))
        if not args.skip_pio:
            cfg, perr = pio_project_config(repo)
            if cfg is not None:
                cfg_src = "pio"
                envs = [s[4:] for s in cfg if s.startswith("env:")]
            else:
                problems.append(perr)
        if cfg is None:
            cfg_src = "own-parser"
            envs = own.envs()
    res["platformio"] = OrderedDict(iniExists=has_ini, resolver=cfg_src, envs=envs, problems=problems)

    # ---- per product
    products = []
    hw_tree = res["libs"]["OGM-HardwareConfig"]["path"]
    hw_headers = header_files(hw_tree) if hw_tree else []
    oam_headers = header_files(os.path.join(repo, "include")) if os.path.isdir(os.path.join(repo, "include")) else []
    oam_headers += header_files(os.path.join(repo, "src")) if os.path.isdir(os.path.join(repo, "src")) else []
    lib_headers = []
    for ln, target in wanted.items():
        if ln in FULL_CACHES:
            continue
        lib_headers += [(ln, f) for f in header_files(target)]
    stubdir = os.path.join(STUBS, name)
    env_cache = {}
    for c in steps:
        p = OrderedDict()
        p["env"] = c["env"]; p["firmwareName"] = c["firmwareName"]; p["featureSet"] = c["featureSet"]
        p["productName"] = c["productName"]; p["debugBuild"] = c["debugBuild"]; p["block"] = c["block"]
        p["scriptPath"] = c["pathKind"]
        reasons, warns = [], []
        if bs["status"] == "custom-build-scripts" or c["pathKind"] == "local":
            reasons.append("custom-build-scripts")
        if c["dynamicArgs"]:
            warns.append("dynamic arguments in Build-Step call")
        if c["featureSet"] not in VALID_FEATURESETS:
            reasons.append("invalid-featureset")
        if app["appIdStatus"] == "unknown":
            reasons.append("kaenx-appid-unknown" if cw == "kaenxcreator" else "appid-unknown")
        if res["hwconfig"]["resolved"] is False:
            reasons.append("hwconfig-pin-unresolved")
        # env
        if not has_ini:
            reasons.append("env-missing"); p["envExists"] = False
        elif c["env"] not in envs:
            reasons.append("env-missing"); p["envExists"] = False
        else:
            p["envExists"] = True
            if c["env"] not in env_cache:
                if cfg_src == "pio":
                    opts = cfg["env:" + c["env"]]
                else:
                    opts = own.env(c["env"])
                toks = flags_from_value(opts.get("build_flags"))
                if c["debugBuild"]:
                    toks += flags_from_value(opts.get("debug_build_flags"))
                raw_flags = "\n".join(opts.get("build_flags") or []) if isinstance(opts.get("build_flags"), list) else str(opts.get("build_flags") or "")
                flag_warn = [m.group(0) for m in re.finditer(r"-D\s*DEVICE_(?:ID|NAME)=\S*\\\S*", raw_flags)]
                defines, includes, undefs = defines_includes(toks)
                arch, extra = arch_defines(opts)
                pre = preprocess(repo, defines, includes, extra, stubdir, roots)
                hw_defs = [d for d in defines if d.startswith(HW_PREFIXES)]
                scan_names = hw_defs or list(defines)
                tx = textual_scan(hw_headers, scan_names)
                for h in tx:
                    h["where"] = "hwconfig"; h["file"] = os.path.relpath(h["file"], hw_tree)
                tx2 = textual_scan(oam_headers, scan_names)
                for h in tx2:
                    h["where"] = "oam"; h["file"] = os.path.relpath(h["file"], repo)
                tx3 = []
                for ln, f in lib_headers:
                    pass
                lib_hits = textual_scan([f for _, f in lib_headers], scan_names)
                for h in lib_hits:
                    owner = next((ln for ln, f in lib_headers if f == h["file"]), "lib")
                    h["where"] = "lib:" + owner; h["file"] = os.path.relpath(h["file"], LIBS)
                env_cache[c["env"]] = dict(opts=opts, defines=defines, includes=includes, arch=arch,
                                           extra=extra, pre=pre, hw_defs=hw_defs, textual=tx + tx2 + lib_hits,
                                           extends=opts.get("extends"), flag_warn=flag_warn)
            ec = env_cache[c["env"]]
            for fw in ec["flag_warn"]:
                warns.append(f"backslash escapes in build flag `{fw}`: the value depends on shell/SCons quoting")
            p["extends"] = ec["extends"]
            p["arch"] = ec["arch"]
            p["defines"] = ec["defines"]
            p["hardwareDefines"] = ec["hw_defs"]
            p["deviceDefines"] = [d for d in ec["hw_defs"] if d.startswith("DEVICE_")]
            p["includeFlags"] = ec["includes"]
            pre = ec["pre"]
            p["preprocessor"] = OrderedDict(returncode=pre["returncode"], errors=pre["errors"],
                                            stubs=pre["stubs"], definitions=pre["definitions"])
            p["deviceId"] = pre["deviceId"]; p["deviceName"] = pre["deviceName"]
            p["deviceIdOrigin"] = pre["deviceIdOrigin"]; p["deviceIdFile"] = pre["deviceIdFile"]
            non_string = False
            for key, define in (("deviceId", "DEVICE_ID"), ("deviceName", "DEVICE_NAME")):
                if pre.get(key + "Raw"):
                    non_string = True
                    p[key + "Raw"] = pre[key + "Raw"]; p[key + "Expanded"] = pre.get(key + "Expanded")
                    warns.append(f"{define} is not a string literal: `{pre[key + 'Raw']}` (expands to \"{pre.get(key + 'Expanded')}\")")
            if non_string:
                reasons.append("device-id-not-string-literal")
            if "hardware.h" in pre["stubs"]:
                warns.append("no hardware.h found in include/ or src/ (stubbed)")
            p["textualMatches"] = ec["textual"]
            # trigger define: textual block that yields the resolved id
            trig = [h for h in ec["textual"] if h["deviceId"] == pre["deviceId"]] if pre["deviceId"] else []
            if not trig and pre["deviceIdFile"]:
                trig = [h for h in ec["textual"] if os.path.basename(h["file"]) == os.path.basename(pre["deviceIdFile"])]
            p["triggerDefine"] = trig[0]["define"] if trig else None
            p["resolution"] = "preprocessor"
            if pre["returncode"] != 0:
                if pre["deviceId"] is None and not non_string:
                    # textual fallback
                    tx_hw = [h for h in ec["textual"] if h["where"] == "hwconfig" and h["deviceId"]]
                    tx_any = [h for h in ec["textual"] if h["deviceId"]]
                    if tx_any:
                        p["deviceId"] = tx_any[-1]["deviceId"]; p["deviceName"] = tx_any[-1]["deviceName"]
                        p["deviceIdOrigin"] = tx_any[-1]["where"]; p["deviceIdFile"] = tx_any[-1]["file"]
                        p["triggerDefine"] = tx_any[-1]["define"]
                        p["resolution"] = "textual"
                        warns.append("preprocessor failed, textual fallback used")
                    else:
                        reasons.append("preprocess-failed")
                else:
                    warns.append("preprocessor returned errors but DEVICE_ID was still resolved")
            if pre["stubs"]:
                warns.append("stubbed headers: " + ", ".join(pre["stubs"]))
            any_id = p["deviceId"] is not None or non_string
            if not p["deviceDefines"] and not any_id:
                reasons.append("no-device-define")
                if p["hardwareDefines"]:
                    warns.append("non-DEVICE_ hardware defines: " + ", ".join(p["hardwareDefines"]))
            if any_id:
                origin = str(p["deviceIdOrigin"])
                if origin != "hwconfig":
                    reasons.append({"build-flags": "device-in-build-flags", "common": "device-in-legacy-common-header"}.get(
                        origin, "device-in-oam-header" if origin.startswith("oam") else "device-in-lib-header"))
                if p["deviceDefines"] == [] and p["triggerDefine"]:
                    warns.append(f"DEVICE_ID set via non-DEVICE_ define {p['triggerDefine']}")
                if p["deviceName"] is None and not pre.get("deviceNameRaw"):
                    reasons.append("no-device-name")
            elif p["deviceDefines"]:
                reasons.append("device-not-in-hwconfig")
                p["searched"] = ["OGM-HardwareConfig@" + (res["hwconfig"]["sha"] or "?")[:7],
                                 "include/, src/ of " + name] + [f"lib:{ln}" for ln in wanted if ln not in FULL_CACHES]
            dup = [d for d in pre["definitions"] if d["macro"] == "DEVICE_ID" and d["op"] == "define"]
            if len(dup) > 1:
                warns.append("DEVICE_ID defined %d times (%s)" % (len(dup), "; ".join(f"{d['origin']}={d['value']}" for d in dup)))
        p["reasons"] = list(dict.fromkeys(reasons))
        p["warnings"] = warns
        # jsonComplete: all fields of openknx-release.json would be filled (deviceId/deviceName
        # resolvable by prepare.py, reusable scripts, appId) regardless of where the id comes from
        registry_only = {"device-in-oam-header", "device-in-lib-header", "device-in-build-flags",
                         "device-in-legacy-common-header", "hwconfig-pin-unresolved"}
        p["jsonComplete"] = bool(p.get("deviceId")) and bool(p.get("deviceName")) and not (set(p["reasons"]) - registry_only)
        p["classification"] = "ok" if not reasons else ("complete-not-registry" if p["jsonComplete"] else "incomplete")
        products.append(p)
    res["products"] = products
    res["summary"] = OrderedDict(total=len(products), ok=sum(1 for p in products if p["classification"] == "ok"),
                                 jsonComplete=sum(1 for p in products if p["jsonComplete"]),
                                 incomplete=sum(1 for p in products if not p["jsonComplete"]),
                                 reasons=dict(Counter(r for p in products for r in p["reasons"])))
    if not products:
        res["summary"]["oamReason"] = bs["status"]
    return res


# -------------------------------------------------------------- reporting ---
def main_reason(r):
    if not r.get("analysed"):
        return "nicht analysiert"
    if not r["products"]:
        return {"missing-build-release": "kein Build-Release.ps1",
                "template-no-build-step": "Build-Release.ps1 ohne Build-Step (Template)",
                "custom-build-scripts": "eigene Build-Skripte"}.get(r["buildScripts"]["status"], r["buildScripts"]["status"])
    c = Counter(r for p in r["products"] for r in p["reasons"])
    if not c:
        return "-"
    return c.most_common(1)[0][0]


def write_report(results, archived, totals, path):
    L = []
    L.append("# Statische Analyse: Vollständigkeit von `openknx-release.json` je OAM\n")
    L.append(f"Stand: {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC. "
             f"Analysiert mit `analyse.py` (OGM-Common Branch `release-json`, Build-ReleaseJson.ps1 / prepare.py).\n")
    L.append("Die Analyse bildet statisch nach, was ein Release-Build tun würde: Build-Step-Aufrufe aus "
             "`scripts/Build-Release.ps1`, Build-Flags des jeweiligen `[env:...]` (aufgelöst mit `pio project config`), "
             "Präprozessorlauf des Host-g++ über `#include <hardware.h>` mit diesen Defines (OGM-HardwareConfig am in "
             "`dependencies.txt` gepinnten Commit), Auswertung von `DEVICE_ID`/`DEVICE_NAME`, sowie `compileWith` für die appId.\n")
    L.append("## Übersicht\n")
    L.append(f"- OAM-Repos laut Regel: {totals['repos']} (analysiert: {totals['analysed']}, nicht analysiert: {totals['notAnalysed']}, archiviert: {len(archived)})")
    L.append(f"- Release-Produkte (Build-Step-Aufrufe) gesamt: {totals['products']}, davon `ok` (vollständig und Gerät aus OGM-HardwareConfig): {totals['ok']}, "
             f"JSON vollständig, aber Gerät nicht aus dem Register: {totals['jsonComplete'] - totals['ok']}, unvollständig: {totals['incomplete']}")
    no_hw = [r["repo"] for r in results if r.get("analysed") and r["hwconfig"]["pin"] is None]
    L.append(f"- OAMs ohne OGM-HardwareConfig in dependencies.txt (Analyse mit v1-Spitze): {len(no_hw)} ({', '.join(no_hw)})")
    sib = [r["repo"] for r in results if r.get("analysed") and r["buildScripts"]["status"] == "reusable-sibling-path"]
    L.append(f"- OAMs mit `../OGM-Common/...`-Aufrufen in Build-Release.ps1: {len(sib)}")
    L.append("- Gründe (Mehrfachnennung je Produkt möglich):")
    for k, v in sorted(totals["reasons"].items(), key=lambda kv: -kv[1]):
        L.append(f"  - `{k}`: {v}")
    L.append("")
    L.append("| OAM | Build-Skripte | compileWith | HWConfig-Pin | Produkte | ok | JSON vollst. | fehlend | Hauptgrund |")
    L.append("|---|---|---|---|---:|---:|---:|---:|---|")
    for r in results:
        if not r.get("analysed"):
            L.append(f"| {r['repo']} | – | – | – | – | – | – | – | nicht analysiert: {r['notAnalysedReason']} |")
            continue
        hw = r["hwconfig"]
        hwtxt = (hw["pin"] or "–") + (" ✓" if hw["resolved"] else (" ✗ (tip)" if hw["resolved"] is False else " (tip)"))
        s = r["summary"]
        L.append(f"| {r['repo']} | {r['buildScripts']['status']} | {r['settings']['compileWith'] or '–'} | {hwtxt} | "
                 f"{s['total']} | {s['ok']} | {s['jsonComplete']} | {s['incomplete']} | {main_reason(r)} |")
    L.append("")
    if archived:
        L.append("### Archivierte Repos (nicht analysiert)\n")
        for a in archived:
            L.append(f"- {a}")
        L.append("")

    L.append("Spalte `Build-Skripte`: `reusable` = alle Aufrufe gehen an `lib/OGM-Common/scripts/setup/reusable/`; "
             "`reusable-sibling-path` = mindestens ein Aufruf geht an `../OGM-Common/scripts/setup/reusable/` (Schwesterverzeichnis). "
             "Das funktioniert nur, wenn `lib/OGM-Common` und `../OGM-Common` derselbe Stand sind: Build-Release-Preprocess.ps1 ruft "
             "`lib/OGM-Common/scripts/setup/reusable/Build-ReleaseJson.ps1 Init` mit festem Pfad auf, Build-Step.ps1 dagegen `$PSScriptRoot/Build-ReleaseJson.ps1`. "
             "`template-no-build-step` = Build-Release.ps1 entspricht dem Template ohne Build-Step; `missing-build-release` = Datei fehlt.\n")
    L.append("## Bedeutung der Gründe\n")
    L.append("- `ok`: deviceId und deviceName werden aus OGM-HardwareConfig aufgelöst, die wiederverwendbaren Skripte aus "
             "`lib/OGM-Common/scripts/setup/reusable` werden benutzt, Feature-Set ist gültig, appId ist zu erwarten.")
    L.append("- `no-device-define`: das env setzt kein `-D DEVICE_*`; prepare.py findet keine DEVICE_ID -> Produkt ohne deviceId/deviceName.")
    L.append("- `device-not-in-hwconfig`: ein `DEVICE_*`-Define ist gesetzt, aber kein Header im durchsuchten Satz (OGM-HardwareConfig am Pin, include/ und src/ des OAM, OFM-Libs) definiert dafür eine DEVICE_ID.")
    L.append("- `device-in-oam-header`: DEVICE_ID wird aufgelöst, stammt aber aus `include/hardware.h` des OAM (bzw. einem anderen OAM-Header) und nicht aus OGM-HardwareConfig -> nicht im Hardware-Register.")
    L.append("- `device-in-lib-header`: DEVICE_ID stammt aus einem OFM-Modul-Header.")
    L.append("- `device-in-legacy-common-header`: DEVICE_ID stammt aus `include/OpenKNXHardware.h` des alten, gepinnten OGM-Common (dort ohne DEVICE_NAME).")
    L.append("- `device-in-build-flags`: DEVICE_ID/DEVICE_NAME werden direkt als `-D` in platformio.ini gesetzt (JSON wird gefüllt, Gerät steht aber in keinem Header-Register).")
    L.append("- `device-id-not-string-literal`: DEVICE_ID ist in OGM-HardwareConfig als Makro-Ausdruck definiert (z. B. `PREFIX_ID \"-DD-Meter\"`). "
             "prepare.py greift mit `^#define DEVICE_ID \"(.*)\"$` auf die `-dM`-Ausgabe zu, in der der Ausdruck unexpandiert steht -> keine deviceId, obwohl die Firmware einen gültigen String sieht (Spalte `deviceIdExpanded` in result.json). Fix gehört nach prepare.py (Makro expandieren) oder in die Header.")
    L.append("- Spalte `JSON vollst.`: Produkte, bei denen alle Felder gefüllt würden, unabhängig davon, ob das Gerät aus OGM-HardwareConfig stammt (`ok` + `device-in-*`-Fälle mit DEVICE_NAME).")
    L.append("- `no-device-name`: DEVICE_ID vorhanden, aber kein DEVICE_NAME.")
    L.append("- `custom-build-scripts`: Build-Release.ps1 nutzt projektlokale Kopien / andere Skripte statt der wiederverwendbaren aus OGM-Common (Build-ReleaseJson.ps1 wird nicht aufgerufen).")
    L.append("- `missing-build-release` / `template-no-build-step`: kein `scripts/Build-Release.ps1` bzw. nur das Template ohne Build-Step-Aufrufe (keine Produkte).")
    L.append("- `env-missing`: Build-Step referenziert ein env, das es in platformio.ini (inkl. extra_configs) nicht gibt.")
    L.append("- `invalid-featureset`: Feature-Set wird von Build-Step.ps1 nicht akzeptiert (Build bricht ab).")
    L.append("- `kaenx-appid-unknown` / `appid-unknown`: compileWith = kaenxcreator ohne eingechecktes include/knxprod.h mit MAIN_OpenKnxId/MAIN_ApplicationNumber bzw. kein KNX-Tool -> appId fehlt voraussichtlich.")
    L.append("- `preprocess-failed`: Host-Präprozessor scheiterte und auch die textuelle Suche fand keine DEVICE_ID.")
    L.append("- `hwconfig-pin-unresolved`: der in dependencies.txt gepinnte OGM-HardwareConfig-Commit ist nicht auffindbar; es wurde die Spitze von v1 verwendet.")
    L.append("")

    L.append("## Was wo angepasst werden muss\n")
    by_reason = OrderedDict()
    for r in results:
        if not r.get("analysed"):
            continue
        if not r["products"]:
            by_reason.setdefault(r["buildScripts"]["status"], []).append(
                f"- **{r['repo']}**: scripts/Build-Release.ps1 "
                + ("fehlt" if r["buildScripts"]["status"] == "missing-build-release" else
                   f"enthält keine Build-Step-Aufrufe (Pre/Post: {r['buildScripts']['preprocess']}/{r['buildScripts']['postprocess']}; "
                   f"weitere Skripte: {', '.join(r['buildScripts']['otherScriptsCalled']) or '–'}; lokale Skripte: {', '.join(r['buildScripts']['localScripts'])})"))
        for p in r["products"]:
            for reason in p["reasons"]:
                det = ""
                if reason == "no-device-define":
                    det = f"Defines im env: {', '.join(p['hardwareDefines']) or 'keine Hardware-Defines'}"
                elif reason == "device-not-in-hwconfig":
                    det = f"Define {', '.join(p['deviceDefines'])}; durchsucht: {', '.join(p.get('searched', []))}"
                    if p.get("textualMatches"):
                        det += "; textuelle Treffer: " + "; ".join(f"{h['where']}:{h['file']} ({h['define']} -> {h['deviceId']})" for h in p["textualMatches"])
                elif reason in ("device-in-oam-header", "device-in-lib-header", "device-in-legacy-common-header"):
                    det = f"DEVICE_ID \"{p['deviceId']}\" aus {os.path.relpath(p['deviceIdFile'], REPOS) if p['deviceIdFile'] and p['deviceIdFile'].startswith(REPOS) else p['deviceIdFile']} (Define: {p.get('triggerDefine') or ', '.join(p['hardwareDefines'])})"
                elif reason == "device-in-build-flags":
                    det = f"-D DEVICE_ID=\"{p['deviceId']}\", DEVICE_NAME=\"{p['deviceName']}\" in platformio.ini"
                elif reason == "device-id-not-string-literal":
                    det = f"`#define DEVICE_ID {p.get('deviceIdRaw')}` -> \"{p.get('deviceIdExpanded')}\" in {os.path.relpath(p['deviceIdFile'], REPOS) if p.get('deviceIdFile') and p['deviceIdFile'].startswith(REPOS) else p.get('deviceIdFile')} (Define: {p.get('triggerDefine') or ', '.join(p['hardwareDefines'])})"
                elif reason == "env-missing":
                    det = "env nicht in platformio.ini" + ("" if r["platformio"]["iniExists"] else " (keine platformio.ini)")
                elif reason == "invalid-featureset":
                    det = f"featureSet `{p['featureSet']}`"
                elif reason == "custom-build-scripts":
                    det = f"Skript: {p['scriptPath']}; Build-Release-Status: {r['buildScripts']['status']}"
                elif reason in ("kaenx-appid-unknown", "appid-unknown"):
                    det = r["appId"]["appIdExpected"]
                elif reason == "preprocess-failed":
                    det = "; ".join(p["preprocessor"]["errors"][:2])
                elif reason == "hwconfig-pin-unresolved":
                    det = f"Pin {r['hwconfig']['pin']} ({r['libs']['OGM-HardwareConfig']['branch']})"
                elif reason == "no-device-name":
                    det = f"DEVICE_ID \"{p['deviceId']}\" aus {os.path.relpath(p['deviceIdFile'], REPOS) if p.get('deviceIdFile') and p['deviceIdFile'].startswith(REPOS) else p.get('deviceIdFile')}"
                by_reason.setdefault(reason, []).append(
                    f"- {r['repo']} / env `{p['env']}` / Produkt `{p['productName']}` [{p['block']}]: {det}")
    order = ["no-device-define", "device-not-in-hwconfig", "device-id-not-string-literal", "device-in-oam-header",
             "device-in-build-flags", "device-in-legacy-common-header", "device-in-lib-header", "no-device-name",
             "env-missing", "invalid-featureset", "custom-build-scripts", "missing-build-release", "template-no-build-step",
             "kaenx-appid-unknown", "appid-unknown", "preprocess-failed", "hwconfig-pin-unresolved"]
    for reason in order + [k for k in by_reason if k not in order]:
        if reason not in by_reason:
            continue
        L.append(f"### `{reason}` ({len(by_reason[reason])})\n")
        L.extend(by_reason[reason])
        L.append("")

    L.append("## Vollständige Produkte (`ok`)\n")
    for r in results:
        if not r.get("analysed"):
            continue
        oks = [p for p in r["products"] if p["classification"] == "ok"]
        if oks:
            L.append(f"- **{r['repo']}**: " + ", ".join(f"`{p['productName']}` ({p['deviceId']})" for p in oks))
    L.append("")

    L.append("## Auffälligkeiten bei den aufgelösten DEVICE_IDs\n")
    ids = OrderedDict()
    for r in results:
        if not r.get("analysed"):
            continue
        for p in r["products"]:
            did = p.get("deviceId") or p.get("deviceIdExpanded")
            if did:
                use = (r["repo"], p["env"], p.get("deviceName") or p.get("deviceNameExpanded"), str(p.get("deviceIdOrigin")))
                if use not in ids.setdefault(did, []):
                    ids[did].append(use)
    found = False
    for did, uses in ids.items():
        names = sorted(set(u[2] for u in uses if u[2]))
        origins = sorted(set(u[3] for u in uses))
        local_repos = sorted(set(u[0] for u in uses if u[3] != "hwconfig"))
        if len(names) > 1 or (len(origins) > 1 and any(o != "hwconfig" for o in origins)) or len(local_repos) > 1:
            found = True
            L.append(f"- DEVICE_ID \"{did}\": " + "; ".join(f"{u[0]}/{u[1]} -> \"{u[2]}\" ({u[3]})" for u in uses))
    if not found:
        L.append("- keine Konflikte (gleiche DEVICE_ID mit unterschiedlichem DEVICE_NAME oder unterschiedlicher Quelle)")
    L.append("")

    L.append("## Hinweise je OAM (Warnungen)\n")
    for r in results:
        if not r.get("analysed"):
            continue
        ws = list(r["warnings"])
        for p in r["products"]:
            for w in p["warnings"]:
                if "stubbed headers" in w:
                    continue
                ws.append(f"{p['env']}: {w}")
        if r["platformio"]["problems"]:
            ws.append("platformio.ini: " + "; ".join(r["platformio"]["problems"]))
        if ws:
            L.append(f"- **{r['repo']}**:")
            for w in dict.fromkeys(ws):
                L.append(f"  - {w}")
    L.append("")

    L.append("## Grenzen der statischen Analyse\n")
    L.append("- Der Präprozessor ist der Host-g++, nicht die Ziel-Toolchain. Toolchain-Makros wurden nachgestellt "
             "(`ARDUINO`, `ARDUINO_ARCH_RP2040`/`PICO_RP2040`/`PICO_RP2350`, `ESP32`/`ARDUINO_ARCH_ESP32`); Header, die auf "
             "andere Toolchain-/Board-Makros reagieren, könnten im echten Build anders auflösen.")
    L.append("- Nicht auffindbare Header (Arduino.h u. ä.) wurden durch leere Stubs ersetzt. Definiert ein solcher Header im "
             "echten Build DEVICE_ID, fehlt das hier. Die Stubs sind je Produkt in result.json (`preprocessor.stubs`) vermerkt.")
    L.append("- Include-Pfade: `-I` aus den Build-Flags, `include/`, `src/`, sowie `include/`/`src/` aller Libs aus dependencies.txt. "
             "Die echte LDF-Reihenfolge kann abweichen; Build-Flags aus `platformio.ini` wurden mit `pio project config` aufgelöst "
             "(bei `-DebugBuild` zusätzlich `debug_build_flags`).")
    L.append("- OFM-Module liegen als Spitze des in dependencies.txt genannten Branches vor (nicht am gepinnten Commit); nur "
             "OGM-Common und OGM-HardwareConfig wurden am gepinnten Commit ausgewertet. Beim echten Release-Build entscheidet der "
             "tatsächliche Stand im lib/-Verzeichnis des Entwicklers.")
    L.append("- Der Release-Build läuft lokal beim Entwickler; ob dessen OGM-Common bereits Build-ReleaseJson.ps1 enthält, ist nicht Teil der Analyse.")
    L.append("- Build-Release.ps1 wurde regulär geparst (Kommentare entfernt, `if ($releaseIndication -eq ...)`-Blöcke verfolgt). "
             "Build-Step-Aufrufe in Schleifen über Hashtable-Tabellen (`@{ Env = ...; Name = ...; Ext = ... }`, OAM-NeoPixel) wurden "
             "je Tabelle expandiert (`table:<name>`); andere dynamische Aufrufe werden nur markiert.")
    L.append("- appId: für `openknxproducer` wird angenommen, dass der Producer `include/knxprod.h` mit MAIN_OpenKnxId/MAIN_ApplicationNumber schreibt (ProcessInclude.cs). "
             "Für `kaenxcreator` ist nur ein eingechecktes knxprod.h als Hinweis verfügbar.")
    L.append("- GitHub-API war nicht verfügbar: Default-Branch/HEAD stammen aus dem Clone, der Archiv-Status aus releases.json.")
    L.append("")
    na = [r for r in results if not r.get("analysed")]
    L.append("## Nicht analysierte OAMs\n")
    if na:
        for r in na:
            L.append(f"- {r['repo']}: {r['notAnalysedReason']}")
    else:
        L.append("- keine")
    L.append("")
    open(path, "w", encoding="utf-8").write("\n".join(L))


# -------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma separated repo names")
    ap.add_argument("--no-clone", action="store_true")
    ap.add_argument("--skip-pio", action="store_true")
    args = ap.parse_args()
    for d in (REPOS, CACHE, TREES, LIBS, STUBS):
        os.makedirs(d, exist_ok=True)

    data = json.load(open(RELEASES_JSON))["data"]
    names = sorted(data)
    for s in APP_SPECIAL:
        if s not in names:
            names.append(s)
            data[s] = {"repo_url": GITHUB + s, "archived": False, "_listed": False}
    selected = [n for n in names if (n.startswith(APP_PREFIX) or n in APP_SPECIAL) and n not in APP_EXCLUSION]
    archived = [n for n in selected if data[n].get("archived")]
    todo = [n for n in selected if n not in archived]
    if args.only:
        todo = [n for n in todo if n in args.only.split(",")]

    caches = {n: ensure_full_cache(n, b) for n, b in FULL_CACHES.items()}
    results = []
    for n in todo:
        log(f"== {n}")
        try:
            results.append(analyse_oam(n, data[n], args, caches))
        except Exception as e:  # keep going, record
            import traceback
            results.append(OrderedDict(repo=n, analysed=False, notAnalysedReason=f"exception: {e!r}",
                                       traceback=traceback.format_exc()))
            log(f"  EXCEPTION: {e!r}")
    analysed = [r for r in results if r.get("analysed")]
    totals = OrderedDict(repos=len(selected), analysed=len(analysed), notAnalysed=len(results) - len(analysed),
                         archived=archived,
                         products=sum(r["summary"]["total"] for r in analysed),
                         ok=sum(r["summary"]["ok"] for r in analysed),
                         jsonComplete=sum(r["summary"]["jsonComplete"] for r in analysed),
                         incomplete=sum(r["summary"]["incomplete"] for r in analysed),
                         reasons=dict(Counter(k for r in analysed for p in r["products"] for k in p["reasons"])),
                         oamsWithoutProducts={r["repo"]: r["buildScripts"]["status"] for r in analysed if not r["products"]})
    out = OrderedDict(generated=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                      ogmCommonBranch="release-json", inclusionRule=dict(prefix=APP_PREFIX, special=APP_SPECIAL, exclusion=APP_EXCLUSION),
                      hwconfigTip=tip_sha(caches["OGM-HardwareConfig"], "v1"),
                      totals=totals, archived=archived, oams=results)
    json.dump(out, open(os.path.join(BASE, "result.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    write_report(results, archived, totals, os.path.join(BASE, "report.md"))
    log(f"done: {totals['analysed']} OAMs, {totals['products']} products, {totals['ok']} ok")


if __name__ == "__main__":
    main()
