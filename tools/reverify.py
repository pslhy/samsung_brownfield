#!/usr/bin/env python3
"""
reverify: decide which Dafny symbols must be re-verified after a change, verify only those,
and compare the cost with full verification.

Rules (Dafny verifies each method/lemma against the CONTRACTS of what it calls):
  body change of a method/lemma/constructor      -> re-verify that symbol only
  contract change (requires/ensures/modifies/
    reads/decreases/signature)                   -> that symbol + every symbol whose body calls it
  definition change of a function/predicate      -> every symbol that mentions it, transitively
    (non-opaque functions are unfolded inside       through other functions/predicates
     proofs, so their bodies ARE part of every
     contract that mentions them)
  definition change of an OPAQUE function body   -> only symbols that `reveal` it
  added symbol                                   -> that symbol

usage:
  reverify.py --old formal/Types.dfy formal/RingQueue.dfy ... \
              --new formal/Types.dfy scenarios/req2/model/RingQueue.dfy ... \
              [--java-impact impact.json --mapping formal/mapping.tsv] [--run]

Assumption about the source layout (true for this lab): a body's opening brace is either alone
on its line or at the end of the declaration's first line, never on a requires/ensures line.
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict

DECL_RE = re.compile(
    r"^\s*((?:ghost|opaque|static|twostate|abstract)\s+)*"
    r"(method|function|predicate|lemma|constructor)\b\s*([A-Za-z_][\w']*)?")
CONTAINER_RE = re.compile(r"^\s*(?:abstract\s+)?(module|class|trait)\s+([A-Za-z_][\w]*)")
SPEC_KW = ("requires", "ensures", "reads", "modifies", "decreases", "invariant")
IDENT_RE = re.compile(r"[A-Za-z_][\w']*")
KEYWORDS = set("""method function predicate lemma constructor ghost opaque static var const if then else
while return returns requires ensures reads modifies decreases invariant forall exists old fresh
new match case assert assume reveal calc true false null this int nat bool seq set map multiset
array string char real import opened module class datatype newtype include in break label
""".split())


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return "\n".join(l.split("//", 1)[0] for l in text.splitlines())


def norm(s):
    return " ".join(s.split())


class Sym:
    def __init__(self, qname, kind, opaque, header, body, file):
        self.qname, self.kind, self.opaque = qname, kind, opaque
        self.header, self.body, self.file = header, body, file
        self.name = qname.rsplit(".", 1)[1]

    def is_fun(self):
        return self.kind in ("function", "predicate")

    def mentions(self, part="all"):
        txt = {"header": self.header, "body": self.body}.get(part, self.header + " " + self.body)
        return set(IDENT_RE.findall(txt)) - KEYWORDS

    def reveals(self):
        return set(re.findall(r"reveal\s+([\w.]+)", self.body))


FIELD_RE = re.compile(r"^\s*(?:ghost\s+)?(?:var|const)\s+([A-Za-z_]\w*)\s*:\s*([\w.]+)")
PARAM_RE = re.compile(r"([A-Za-z_]\w*)\s*:\s*([\w.]+)")
FIELD_TYPES = defaultdict(set)    # field name -> class names it may have


def parse_file(path):
    lines = strip_comments(open(path).read()).splitlines()
    for l in lines:
        fm = FIELD_RE.match(l)
        if fm:
            FIELD_TYPES[fm.group(1)].add(fm.group(2).split(".")[-1])
    syms = []
    stack = []      # (name, depth at which it closes)
    depth = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        c = CONTAINER_RE.match(line)
        if c and line.rstrip().endswith("{"):
            stack.append((c.group(2), depth))
            depth += line.count("{") - line.count("}")
            i += 1
            continue
        d = DECL_RE.match(line)
        if d:
            mods = d.group(1) or ""
            kind = d.group(2)
            name = d.group(3) if kind != "constructor" or (d.group(3) and d.group(3) != "") else None
            if kind == "constructor":
                name = d.group(3) if d.group(3) and not line.strip().startswith("constructor (") else "_ctor"
            opaque = "opaque" in line.split(kind)[0]
            header_lines = []
            j = i
            body_start = None
            while j < len(lines):
                l = lines[j]
                s = l.strip()
                first = (j == i)
                if s == "{" or (l.rstrip().endswith("{") and (first or not s.startswith(SPEC_KW))):
                    if s != "{":
                        header_lines.append(l.rstrip()[:-1])
                    body_start = j
                    break
                header_lines.append(l)
                j += 1
            if body_start is None:       # body-less declaration
                i = j + 1
                continue
            bdepth, k, body_lines = 0, body_start, []
            while k < len(lines):
                l = lines[k]
                if k == body_start:
                    l = l[l.rindex("{"):]
                body_lines.append(l)
                bdepth += l.count("{") - l.count("}")
                if bdepth == 0:
                    break
                k += 1
            qname = ".".join([n for n, _ in stack] + [name])
            syms.append(Sym(qname, kind, opaque, norm(" ".join(header_lines)), norm(" ".join(body_lines)), path))
            i = k + 1
            continue
        depth += line.count("{") - line.count("}")
        while stack and depth <= stack[-1][1]:
            stack.pop()
        i += 1
    return syms


def parse_program(files):
    out = {}
    for f in files:
        for s in parse_file(f):
            out[s.qname] = s
    return out


def classify(old, new):
    changes = {}
    for q, s in new.items():
        o = old.get(q)
        if o is None:
            changes[q] = "added"
        elif s.is_fun():
            if o.header != s.header:
                changes[q] = "definition"
            elif o.body != s.body:
                changes[q] = "opaque-body" if s.opaque else "definition"
        else:
            if o.header != s.header:
                changes[q] = "contract"
            elif o.body != s.body:
                changes[q] = "body"
    removed = sorted(set(old) - set(new))
    return changes, removed


def resolve(name, user, prog):
    """Symbols that a use of `name` inside `user` may refer to.
    - unqualified use  -> the symbol of the same class/module, if there is one
    - qualified use x.name -> the symbol in x's class when x's type is known (a parameter of
      `user` or a field), otherwise any class (over-approximation: safe, maybe too much)."""
    cands = [q for q, s in prog.items() if s.name == name]
    if len(cands) <= 1:
        return cands
    text = user.header + " " + user.body
    container = user.qname.rsplit(".", 1)[0]
    params = {}
    for pn, pt in PARAM_RE.findall(user.header):
        params[pn] = {pt.split(".")[-1]}
    out = set()
    if re.search(r"(?<![\w.])" + re.escape(name) + r"\b", text):
        local = [q for q in cands if q.rsplit(".", 1)[0] == container]
        out |= set(local) if local else set(cands)
    for recv in re.findall(r"([A-Za-z_]\w*)\s*\.\s*" + re.escape(name) + r"\b", text):
        types = params.get(recv) or FIELD_TYPES.get(recv)
        if types:
            hit = {q for q in cands if q.rsplit(".", 1)[0].split(".")[-1] in types}
            out |= hit if hit else set(cands)
        else:
            out |= {q for q in cands if q.rsplit(".", 1)[0] != container} or set(cands)
    return sorted(out)


def reverify_set(prog, changes):
    reasons = defaultdict(list)
    # 1. functions whose meaning changed, closed under "mentions"
    changed_defs = {q for q, k in changes.items() if k == "definition" or (k == "added" and prog[q].is_fun())}
    affected_funs = set(changed_defs)
    grew = True
    while grew:
        grew = False
        for q, s in prog.items():
            if s.is_fun() and q not in affected_funs:
                for n in s.mentions():
                    if any(t in affected_funs for t in resolve(n, s, prog)):
                        affected_funs.add(q)
                        reasons[q].append("mentions changed function " + n)
                        grew = True
                        break
    for q, s in prog.items():
        for n in s.mentions():
            hits = [t for t in resolve(n, s, prog) if t in affected_funs and t != q]
            if hits:
                reasons[q].append("mentions " + hits[0].split(".", 1)[1] + " (definition changed)")
                break
    for q in changed_defs:
        reasons[q].append("definition changed")
    # 2. opaque bodies: only revealers
    for q, k in changes.items():
        if k == "opaque-body":
            reasons[q].append("opaque body changed")
            for u, s in prog.items():
                if prog[q].name in {r.split(".")[-1] for r in s.reveals()}:
                    reasons[u].append("reveals " + prog[q].name)
    # 3. contracts: the symbol + callers
    for q, k in changes.items():
        if k == "contract":
            reasons[q].append("contract changed")
            for u, s in prog.items():
                if u != q and prog[q].name in s.mentions("body") and q in resolve(prog[q].name, s, prog):
                    reasons[u].append("calls " + q.split(".", 1)[1] + " (contract changed)")
        elif k in ("body", "added"):
            reasons[q].append(k)
    return {q: r for q, r in reasons.items() if q in prog}


def verify_cost_rows(csv_path):
    rows = list(csv.DictReader(open(csv_path)))
    out = defaultdict(lambda: [0.0, 0])
    for r in rows:
        name = r["TestResult.DisplayName"].split(" (")[0]
        h, m, s = r["TestResult.Duration"].split(":")
        out[name][0] += int(h) * 3600 + int(m) * 60 + float(s)
        out[name][1] += int(r["TestResult.ResourceCount"])
    return out


def run_dafny(files, filt, logdir, tag):
    dafny = shutil.which("dafny") or sys.exit("dafny not found on PATH")
    log = os.path.join(logdir, tag + ".csv")
    cmd = [dafny, "verify"] + files + ["--log-format", "csv;LogFileName=" + log]
    if filt:
        cmd += ["--filter-symbol", filt]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.time() - t0
    summary = [l for l in p.stdout.splitlines() if "verifier finished" in l]
    errors = [l for l in p.stdout.splitlines() if "Error" in l]
    return wall, (summary[0] if summary else p.stdout.strip()[-200:]), errors, log


def short(q):
    return q.replace("com.dxlab.homehub.", "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", nargs="+", required=True)
    ap.add_argument("--new", nargs="+", required=True)
    ap.add_argument("--java-impact", default=None, help="impact.json written by tools/impact.py --json")
    ap.add_argument("--mapping", default=None)
    ap.add_argument("--run", action="store_true", help="verify the selection and compare with full verification")
    ap.add_argument("--html", default=None, help="write out/html/<NAME>.html")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    R = {}

    old, new = parse_program(a.old), parse_program(a.new)
    changes, removed = classify(old, new)
    sel = reverify_set(new, changes)
    callable_syms = [q for q, s in new.items()]
    prog_names = sorted(new)

    print("# Dafny re-verification plan\n")
    print("## Changed symbols\n")
    for q, k in sorted(changes.items()):
        print("- %-55s %s" % (q, k))
    for q in removed:
        print("- %-55s removed" % q)
    if not changes and not removed:
        print("- (none)")
    print("\n## Must be re-verified: %d of %d symbols\n" % (len(sel), len(callable_syms)))
    for q in sorted(sel):
        print("- %-55s <- %s" % (q, "; ".join(sorted(set(sel[q])))))

    if a.java_impact and a.mapping:
        imp = json.load(open(a.java_impact))
        mp = {}
        for line in open(a.mapping):
            if line.strip() and not line.startswith("#"):
                p = line.rstrip("\n").split("\t")
                mp[p[0]] = p[1]
        seeds = set(imp["changed"]) | set(imp["added"]) | set(imp["removed"])
        java_side = {mp[m] for m in seeds | set(imp["impacted"]) if m in mp}
        print("\n## Java impact analysis vs. Dafny proof dependencies\n")
        print("Dafny symbols suggested by the Java impact set (changed + impacted, mapped): %d" % len(java_side))
        only_java = sorted(java_side - set(sel))
        only_dafny = sorted(set(sel) - java_side)
        print("\nIn the Java impact set but NO re-verification needed (modular proofs): %d" % len(only_java))
        for q in only_java:
            print("- " + q)
        print("\nNeeds re-verification but NOT in the Java impact set "
              "(spec-only dependencies, e.g. a function used in contracts): %d" % len(only_dafny))
        for q in only_dafny:
            print("- " + q)
        R.update(java_side=java_side, only_java=only_java, only_dafny=only_dafny)

    if a.run:
        logdir = tempfile.mkdtemp(prefix="reverify-")
        print("\n## Verification cost\n")
        wall_full, summ, errs, log = run_dafny(a.new, None, logdir, "full")
        full_cost = verify_cost_rows(log)
        print("full      : %5.1fs wall | %s" % (wall_full, summ))
        for e in errs[:10]:
            print("    " + e)
        # Dafny keeps only the last --filter-symbol, so group: one run per module when two or more
        # of its symbols are selected (verifies some extra symbols, but saves Dafny's start-up
        # time, which dominates at this model size), else one run for the single symbol.
        wall_sel, sel_errors, runs, extra = 0.0, [], [], 0
        by_mod = defaultdict(list)
        for q in prog_names:
            by_mod[q.split(".")[0]].append(q)
        for mod, members in sorted(by_mod.items()):
            chosen = [q for q in members if q in sel]
            if not chosen:
                continue
            if len(chosen) > 1:
                runs.append(mod + ".")
                extra += len(members) - len(chosen)
            else:
                runs += [q + "." for q in chosen]
        for f in runs:
            w, summ, errs, _ = run_dafny(a.new, f.rstrip(".") if f.count(".") == 1 else f, logdir,
                                         "sel-" + f.strip("."))
            wall_sel += w
            sel_errors += errs
        print("selective : %5.1fs wall | %d dafny run(s)%s" % (
            wall_sel, len(runs), (", %d extra symbol(s) verified by module runs" % extra) if extra else ""))
        for e in sel_errors[:10]:
            print("    " + e)
        tot_t = sum(v[0] for v in full_cost.values())
        tot_r = sum(v[1] for v in full_cost.values())
        sel_t = sum(v[0] for k, v in full_cost.items() if k in sel)
        sel_r = sum(v[1] for k, v in full_cost.items() if k in sel)
        print("\nprover work (from the full run's log, start-up excluded):")
        print("  all symbols     : %6.2fs solver time, %12d resource units" % (tot_t, tot_r))
        print("  selected only   : %6.2fs solver time, %12d resource units (%.0f%%)"
              % (sel_t, sel_r, 100.0 * sel_r / tot_r if tot_r else 0))
        R.update(wall_full=wall_full, wall_sel=wall_sel, runs=runs, extra=extra, tot_r=tot_r, sel_r=sel_r,
                 tot_t=tot_t, sel_t=sel_t, errors=errs + sel_errors)

    if a.html:
        html_report(a, changes, removed, sel, callable_syms, R)


KIND_KO = {"body": "본문", "contract": "계약", "definition": "함수 정의", "opaque-body": "opaque 함수 본문",
           "added": "추가", "removed": "삭제"}


def reason_ko(r):
    r = r.replace("definition changed", "정의가 바뀜").replace("contract changed", "계약이 바뀜")
    r = r.replace("opaque body changed", "opaque 본문이 바뀜")
    r = re.sub(r"^mentions changed function (\S+)", r"정의가 바뀐 \1을(를) 언급", r)
    r = re.sub(r"^mentions (\S+) \(정의가 바뀜\)", r"정의가 바뀐 \1을(를) 언급", r)
    r = re.sub(r"^calls (\S+) \(계약이 바뀜\)", r"계약이 바뀐 \1을(를) 호출", r)
    r = re.sub(r"^reveals (\S+)", r"\1을(를) reveal", r)
    return {"body": "본문이 바뀜", "added": "새로 추가됨"}.get(r, r)


def html_report(a, changes, removed, sel, callable_syms, R):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import report
    e = report.e
    n_all, n_sel = len(callable_syms), len(sel)
    body = []
    # Dafny code diff
    diffs = []
    for po, pn in zip(a.old, a.new):
        lo, ln = open(po).read().splitlines(), open(pn).read().splitlines()
        if lo != ln:
            diffs.append(report.split_diff("%s → %s" % (po, pn), lo, ln, "변경 전 모델", "변경 후 모델"))
    body.append("<section id='code'><h2>바뀐 Dafny 모델</h2><p class='sub'>Java 변경에 맞춰 고친 Dafny 모델입니다.</p>%s</section>"
                % ("".join(diffs) or "<p class='note'>바뀐 파일 없음</p>"))
    rows = [["<code>%s</code>" % e(q), report.badge(KIND_KO.get(k, k), "warn" if k != "body" else "info")]
            for q, k in sorted(changes.items())] + [["<code>%s</code>" % e(q), report.badge("삭제", "bad")] for q in removed]
    body.append("<section id='changed'><h2>바뀐 기호 (%d)</h2><p class='sub'>무엇이 바뀌었는지에 따라 다시 증명할 범위가 정해집니다. "
                "본문만 바뀌면 그 기호 하나, 계약이 바뀌면 부르는 쪽까지, 계약에 쓰인 함수의 정의가 바뀌면 그 함수를 언급하는 모든 것.</p>%s</section>"
                % (len(rows), report.table(["기호", "바뀐 것"], rows)))
    rows = [["<code>%s</code>" % e(q), e("; ".join(sorted({reason_ko(r) for r in sel[q]})))] for q in sorted(sel)]
    body.append("<section id='sel'><h2>다시 증명할 기호 (%d / %d)</h2>%s</section>" % (n_sel, n_all, report.table(["기호", "이유"], rows)))
    if "java_side" in R:
        both = sorted(set(sel) & R["java_side"])
        def chips(xs, cls=""):
            return "<div class='chips'>%s</div>" % ("".join("<span class='chip %s'>%s</span>" % (cls, e(x)) for x in xs)
                                                     or "<span class='note'>없음</span>")
        body.append("<section id='java'><h2>Java 영향 분석과 비교</h2><p class='sub'>Java 영향 분석은 코드에서 값이 흐르는 길을 따라가고, "
                    "Dafny 재증명은 계약이 무엇을 언급하는가를 따라갑니다. 그래서 둘이 다릅니다.</p>"
                    "<div class='grid3'><div class='box'><h3 style='margin-top:0'>둘 다 해당 (%d)</h3>%s</div>"
                    "<div class='box'><h3 style='margin-top:0'>Java에서는 값이 달라질 수 있지만 다시 증명할 필요 없음 (%d)</h3>"
                    "<p class='note'>이 기호들의 증명은 바뀐 코드가 아니라 그 코드의 계약만 보고 이뤄졌고, 계약은 그대로입니다.</p>%s</div>"
                    "<div class='box'><h3 style='margin-top:0'>Java 영향 분석에는 없지만 다시 증명해야 함 (%d)</h3>"
                    "<p class='note'>계약에만 쓰이는 함수와 보조정리, 또는 바뀐 함수를 계약에서 언급하는 기호입니다.</p>%s</div></div></section>"
                    % (len(both), chips(both, "on"), len(R["only_java"]), chips(R["only_java"], "off"),
                       len(R["only_dafny"]), chips(R["only_dafny"], "on")))
    fx = [("다시 증명할 기호", "%d / %d" % (n_sel, n_all)), ("바뀐 기호", len(changes) + len(removed))]
    verdict = ("전체 <span class='num'>%d</span>개 중 <span class='num'>%d</span>개만 다시 증명하면 됩니다." % (n_all, n_sel), "info")
    if "wall_full" in R:
        # the timing and solver-work numbers are kept in the console output only: at this model size the
        # selected run is not faster (Dafny's start-up time dominates), which only distracts from the point.
        ok = not R["errors"]
        body.append("<section id='cost'><h2>골라서 다시 증명한 결과 %s</h2>%s</section>" % (
            report.badge("검증 통과" if ok else "검증 오류", "ok" if ok else "bad"),
            ("<pre class='box'>%s</pre>" % e("\n".join(R["errors"][:10]))) if R["errors"] else ""))
    toc = [("code", "바뀐 모델"), ("changed", "바뀐 기호"), ("sel", "다시 증명할 기호")] + \
          ([("java", "Java와 비교")] if "java_side" in R else []) + ([("cost", "결과")] if "wall_full" in R else [])
    title = "재검증 범위: %s" % (a.label or "변경")
    html_text = report.page(title, "Dafny 모델이 바뀌었을 때 전체를 다시 증명하지 않고, 바뀐 것의 종류에 따라 필요한 것만 다시 증명합니다.",
                            "".join(body), verdict=verdict, facts_items=fx,
                            command="make reverify REQ=%s" % a.label if a.label else None, toc=toc)
    report.write(a.html, title, html_text, "ok" if not R.get("errors") else "bad",
                 "%d/%d개 다시 증명" % (n_sel, n_all))


if __name__ == "__main__":
    main()
