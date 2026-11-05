#!/usr/bin/env python3
"""
bytecode: reads compiled Java classes with javap (JDK only) for the analysis tools.

Gives the class hierarchy, every method with its line table and normalized bytecode (used
to tell whether a method really changed), and the resolution of a call to the methods it may
run (every override in the class hierarchy). tools/defuse.py builds the def-use analysis on it.

Method names use one canonical form shared by every tool in this lab:
  com.dxlab.homehub.queue.RingEventQueue#offer(com.dxlab.homehub.model.Event)
Constructors are "<init>", static initializers "<clinit>".
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

INVOKE_RE = re.compile(
    r"^\s*\d+:\s+(invokevirtual|invokeinterface|invokestatic|invokespecial)\s+#\d+(?:,\s*\d+)?\s+"
    r"//\s+(?:Interface)?Method\s+(.+)$")
CLASS_HDR_RE = re.compile(
    r"^(?:(?:public|protected|private|abstract|final|static|strictfp|synchronized)\s+)*"
    r"(class|interface|enum)\s+([\w.$]+)(?:<.*?>)?(?:\s+extends\s+([\w.$<>, ?]+?))?"
    r"(?:\s+implements\s+([\w.$<>, ?]+?))?\s*\{\s*$")
LINE_RE = re.compile(r"^\s+line (\d+): \d+$")
CP_INDEX_RE = re.compile(r"#\d+")
OFFSET_RE = re.compile(r"^\s*\d+:")

PRIMS = {"B": "byte", "C": "char", "D": "double", "F": "float", "I": "int", "J": "long",
         "S": "short", "Z": "boolean", "V": "void"}


def find_javap():
    j = shutil.which("javap")
    if j:
        return j
    home = os.environ.get("JAVA_HOME")
    if home and os.path.exists(os.path.join(home, "bin", "javap")):
        return os.path.join(home, "bin", "javap")
    sys.exit("javap not found: install a JDK (11+) and put it on PATH")


def parse_desc_params(desc):
    """'(ILjava/lang/String;[J)V' -> ['int', 'java.lang.String', 'long[]']"""
    inner = desc[desc.index("(") + 1:desc.index(")")]
    out, i = [], 0
    while i < len(inner):
        dims = 0
        while inner[i] == "[":
            dims += 1
            i += 1
        c = inner[i]
        if c == "L":
            j = inner.index(";", i)
            name = inner[i + 1:j].replace("/", ".")
            i = j + 1
        else:
            name = PRIMS[c]
            i += 1
        out.append(name + "[]" * dims)
    return out


def canon(cls, name, desc):
    return "%s#%s(%s)" % (cls, name, ",".join(parse_desc_params(desc)))


def strip_generics(s):
    depth, out = 0, []
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def list_classes(root):
    names = []
    for dp, _, files in os.walk(root):
        for f in files:
            if f.endswith(".class") and f != "module-info.class":
                rel = os.path.relpath(os.path.join(dp, f), root)
                names.append(rel[:-6].replace(os.sep, "."))
    return sorted(names)


def run_javap(classpath, classes):
    javap = find_javap()
    env = dict(os.environ)
    env.pop("JAVA_TOOL_OPTIONS", None)
    out = []
    for i in range(0, len(classes), 200):
        chunk = classes[i:i + 200]
        p = subprocess.run([javap, "-c", "-p", "-s", "-l", "-cp", classpath] + chunk,
                           capture_output=True, text=True, env=env)
        if p.returncode != 0:
            sys.exit("javap failed:\n" + p.stderr)
        out.append(p.stdout)
    return "\n".join(out)


class Model:
    def __init__(self):
        self.classes = {}            # name -> dict(super, ifaces, flags, source)
        self.methods = {}            # canon -> dict(cls, name, desc, abstract, lines, code)
        self.declared = defaultdict(dict)   # cls -> {(name, desc): canon}
        self.calls = []              # (caller canon, kind, owner, name, desc)


def parse(text):
    m = Model()
    cur_cls = None
    source = None
    cur = None          # current method dict
    pending_hdr = None  # header line waiting for descriptor
    in_code = in_lines = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("Compiled from"):
            source = line.split('"')[1]
            continue
        if not line.startswith(" ") and line.endswith("{"):
            hdr = CLASS_HDR_RE.match(strip_generics(line))
            if hdr:
                kind, name, sup, ifs = hdr.groups()
                flags = set(line.split()[:line.split().index(kind)])
                if kind == "interface":
                    flags.add("interface")
                ifaces = [x.strip() for x in (ifs or "").split(",") if x.strip()]
                if kind == "interface":
                    ifaces = [x.strip() for x in (sup or "").split(",") if x.strip()]
                    sup = None
                if kind == "enum":
                    sup = "java.lang.Enum"
                m.classes[name] = {"super": (sup or "java.lang.Object").strip(), "ifaces": ifaces,
                                   "flags": flags, "source": source}
                cur_cls = name
            continue
        if cur_cls is None:
            continue
        if line.startswith("  ") and not line.startswith("   ") and line.endswith(";"):
            pending_hdr = line.strip()
            in_code = in_lines = False
            cur = None
            continue
        if line.startswith("    descriptor:") and pending_hdr is not None:
            desc = line.split(":", 1)[1].strip()
            hdr = pending_hdr
            pending_hdr = None
            if "(" not in desc:
                continue   # field
            before = strip_generics(hdr.split("(")[0])
            if hdr.startswith("static {}"):
                name = "<clinit>"
            else:
                last = before.split()[-1]
                name = "<init>" if last == cur_cls else last
            c = canon(cur_cls, name, desc)
            cur = {"cls": cur_cls, "name": name, "desc": desc, "abstract": " abstract " in " " + hdr,
                   "lines": [], "code": []}
            m.methods[c] = cur
            m.declared[cur_cls][(name, desc)] = c
            cur["canon"] = c
            continue
        if cur is None:
            continue
        s = line.strip()
        if s == "Code:":
            in_code, in_lines = True, False
            continue
        if s == "LineNumberTable:":
            in_code, in_lines = False, True
            continue
        if s.endswith("Table:") or s.startswith("Exceptions:") or s.startswith("Signature:"):
            in_code = in_lines = False
            continue
        if in_code:
            if OFFSET_RE.match(line):
                cur["code"].append(CP_INDEX_RE.sub("#", s))
                inv = INVOKE_RE.match(line)
                if inv:
                    kind, target = inv.groups()
                    owner_name, desc = target.split(":", 1)
                    if "." in owner_name:
                        owner, name = owner_name.rsplit(".", 1)
                        owner = owner.replace("/", ".")
                    else:
                        owner, name = cur["cls"], owner_name
                    name = name.strip('"')
                    m.calls.append((cur["canon"], kind[6:], owner, name, desc.strip()))
        elif in_lines:
            lm = LINE_RE.match(line)
            if lm:
                cur["lines"].append(int(lm.group(1)))
    return m


def method_rows(m):
    rows = []
    for c, info in sorted(m.methods.items()):
        lines = info["lines"]
        h = hashlib.sha1("\n".join(info["code"]).encode()).hexdigest()[:12] if info["code"] else "-"
        rows.append((c, info["cls"], m.classes[info["cls"]]["source"] or "-",
                     min(lines) if lines else -1, max(lines) if lines else -1, h))
    return rows
