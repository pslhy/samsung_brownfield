#!/usr/bin/env python3
"""
impact: change-impact analysis by def-use (data and control dependence), for the HomeHub lab.

  1. Changed lines     Source lines that differ between the base and the changed version, kept
                       only inside methods whose compiled code actually differs (so comment or
                       formatting edits do not count). Deleted lines are taken from the base
                       version, inserted lines from the changed version.
  2. Forward slice     On the system dependence graph of each version (tools/sdg.py), from the
                       nodes on those lines: every def-use and control dependence, across
                       methods, following only paths where a call returns to its own caller.
                       Both versions are sliced and the results are joined.
  3. Report            the data that may now hold different values (fields, collection
                       contents), the methods whose outputs (return value, exception, writes)
                       may differ, the tests whose result may differ. For every one of them the
                       chain of source lines from a changed line to it.

Changes in test code only decide which tests to rerun; they do not make production code impacted.

usage:
  impact.py --base legacy/build/classes legacy/build/test-classes \\
            --base-src legacy/src/main/java legacy/src/test/java \\
            --changed work/x/build/classes work/x/build/test-classes \\
            --changed-src work/x/src/main/java work/x/src/test/java \\
            [--mapping formal/mapping.tsv] [--json out.json] [--why Class#method ...]
"""
import argparse
import difflib
import json
import os
import sys
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bytecode  # noqa: E402
import defuse  # noqa: E402
import report  # noqa: E402
import sdg  # noqa: E402

PFX = "com.dxlab.homehub."


def short(m):
    if "#" not in m:
        return m.replace(PFX, "")
    cls, rest = m.split("#", 1)
    return cls.replace(PFX, "") + "#" + rest.replace(PFX, "").replace("java.lang.", "")


def is_test(m):
    cls = m.split("#")[0]
    return cls.endswith("Test") or ".testkit." in cls


def is_test_method(m):
    return is_test(m) and m.split("#")[1].startswith("test")


def load_mapping(path):
    mp = {}
    if not path or not os.path.exists(path):
        return mp
    for line in open(path):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        mp[parts[0]] = {"dafny": parts[1], "kind": parts[2] if len(parts) > 2 else "?",
                        "note": parts[3] if len(parts) > 3 else ""}
    return mp


class Program:
    def __init__(self, dirs, srcs):
        names = []
        for d in dirs:
            names += bytecode.list_classes(d)
        text = bytecode.run_javap(os.pathsep.join(dirs), names)
        self.model = bytecode.parse(text)
        self.methods = defuse.parse_methods(text)
        self.hashes = {c: h for c, _, _, _, _, h in bytecode.method_rows(self.model)}
        self.srcs = srcs
        self.targets = defuse.make_resolver(self.model)

    def source_path(self, cls):
        info = self.model.classes.get(cls)
        if not info or not info["source"]:
            return None
        rel = os.path.join(*cls.split(".")[:-1], info["source"])
        for r in self.srcs:
            p = os.path.join(r, rel)
            if os.path.exists(p):
                return p
        return None

    def method_lines(self, m):
        return {ln for _, ln in self.methods[m]["lines"]} if m in self.methods else set()


def line_diff(a_path, b_path):
    a = open(a_path).read().splitlines() if a_path else []
    b = open(b_path).read().splitlines() if b_path else []
    a = [x.rstrip() for x in a]
    b = [x.rstrip() for x in b]
    da, db = set(), set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            da |= set(range(i1 + 1, i2 + 1))
            if tag == "delete":
                db |= {j1, j1 + 1}            # the statement next to a deletion
        if tag in ("replace", "insert"):
            db |= set(range(j1 + 1, j2 + 1))
            if tag == "insert":
                da |= {i1, i1 + 1}
    return da, db


GLOBAL_KINDS = ("field", "elem")


def g_txt(gl):
    return ("필드 %s" % short(gl[1])) if gl[0] == "field" else ("%s의 내용" % short(gl[1]))


def out_txt(out):
    return {"ret": "반환값", "exc": "예외"}.get(out[0]) or ("%s에 쓰는 값" % g_txt(out))


class Analysis:
    """one version: its SDG, the slices from the changed lines, and the reason chains"""

    def __init__(self, prog, seeds):
        self.P = prog
        self.G = sdg.SDG(prog.methods, prog.targets, is_test)
        prod = {m: ls for m, ls in seeds.items() if not is_test(m)}
        test = {m: ls for m, ls in seeds.items() if is_test(m)}
        self.par_prod = self.G.slice(self.G.criterion(prod))
        self.par_test = self.G.slice(self.G.criterion(test))
        self.prod_seeds = prod
        self._per_seed = None

    def per_seed(self):
        """one slice per changed production method: {method: parents}"""
        if self._per_seed is None:
            self._per_seed = {m: self.G.slice(self.G.criterion({m: ls})) for m, ls in sorted(self.prod_seeds.items())}
        return self._per_seed

    def outputs(self, m, test_slice=False):
        """{out: node} for the outputs of m reached by the slice"""
        G, par = self.G, (self.par_test if test_slice else self.par_prod)
        r = {}
        for x in ("ret", "exc"):
            n = G.ids.get((m, ("FO", x)))
            if n is not None and n in par:
                r[(x,)] = n
        p = G.pdg.get(m)
        if p is not None:
            for gl, ws in sorted(p.defs.items()):
                hits = [G.ids[(m, w)] for w in ws if G.ids.get((m, w)) in par]
                if hits:
                    r[gl] = min(hits)
            # a changed condition decides whether a call happens: what the callee writes is an
            # output of this method too
            for k in sorted(p.calls):
                C = G.ids.get((m, ("i", k)))
                if C is None or C not in par or not any(
                        kd == sdg.CTL and G.nodes[s][1][0] == "i" and s in par for s, kd in G.pred[C]):
                    continue
                for gl in sorted(set().union(*(G.gmod.get(t, set()) for t in p.calls[k][0]))):
                    ao = G.ids.get((m, ("AO", k, gl)))
                    if ao is not None and ao in par and gl not in r:
                        r[gl] = C            # the reason shown: why the call now may or may not happen
        return r

    def chain(self, n, test_slice=False, par=None):
        """[{m, line, via}] from a changed line to node n, and the label of the last hop"""
        G = self.G
        if par is None:
            par = self.par_test if test_slice else self.par_prod
        path = G.path_to(par, n)
        items, via, kind_in = [], [], None
        for idx, v in enumerate(path):
            m, key = G.nodes[v]
            ln = G.lines[v]
            if idx > 0:
                kind_in = next((k for d, k in G.succ[path[idx - 1]] if d == v), kind_in)
            is_line = ln > 0 and (key[0] in ("i", "ie", "x") or idx == 0)
            if not is_line:
                via.append(v)
                continue
            if items and items[-1]["m"] == m and items[-1]["line"] == ln:
                via = []
                continue
            items.append({"m": m, "line": ln, "via": self.via_txt(via, kind_in, items[-1]["m"] if items else m, m)})
            via = []
        if via and via[-1] == n and G.nodes[n][1][0] == "FO":
            via = via[:-1]               # the target itself is named below the chain
        # end on the target's own line (e.g. the call in this method that leads to the write)
        tm, tln = G.nodes[n][0], G.lines[n]
        if tln > 0 and via and not (items and items[-1]["m"] == tm and items[-1]["line"] == tln):
            items.append({"m": tm, "line": tln, "via": self.via_txt(via[:-1], kind_in, None, None)})
            via = []
        return items, (self.via_txt(via, kind_in, None, None) if via else "")

    def via_txt(self, via, kind_in, m_from, m_to):
        """how a value got from one shown line to the next, in order: fields, returns, arguments"""
        G = self.G
        hops = []

        def add(h):
            if h and (not hops or hops[-1] != h):
                hops.append(h)
        for v in via:
            m, key = G.nodes[v]
            x = key[-1] if key[0] in ("FI", "FO", "V", "G", "AI", "AO") else None
            if isinstance(x, tuple) and x[0] in GLOBAL_KINDS:
                add("%s에 저장했다가 읽음" % g_txt(x))
            elif key[0] == "FO" and key[1] == "ret":
                add("%s의 반환값으로" % short(m))
            elif key[0] == "FO" and key[1] == "exc":
                add("%s에서 나온 예외로" % short(m))
            elif key[0] == "FI" and isinstance(key[1], int):
                add("%s의 %d번째 인자로" % (short(m), key[1]))
            elif key[0] == "E":
                add("%s 호출 여부가 달라짐" % short(m))
        if hops:
            if len(hops) > 3:
                hops = hops[:1] + ["…"] + hops[-2:]
            return " → ".join(hops)
        if kind_in == sdg.CTL:
            return "위 줄의 조건에 따라 실행 여부가 달라짐"
        return ""


def scope_arg(a):
    return (" SCOPE=" + " ".join(a.scope)) if a.scope else ""


def restrict(a):
    """--scope: copy only the given source files and their class files (with inner classes) into a temporary
    folder, for both versions, and analyze that instead"""
    import glob
    import shutil
    import tempfile
    import atexit
    tmp = tempfile.mkdtemp(prefix="impact-scope-")
    atexit.register(shutil.rmtree, tmp, True)
    a.scope_names = []
    for v, cls_dirs, src_dirs in (("base", "base", "base_src"), ("new", "changed", "changed_src")):
        cdir, sdir = os.path.join(tmp, v, "classes"), os.path.join(tmp, v, "src", "main", "java")   # same tail as the real tree
        for f in a.scope:
            rel = f.split("/java/", 1)[-1]                      # com/dxlab/.../X.java
            stem = rel[:-len(".java")]
            for root in getattr(a, src_dirs):
                if os.path.exists(os.path.join(root, rel)):
                    os.makedirs(os.path.dirname(os.path.join(sdir, rel)), exist_ok=True)
                    shutil.copy(os.path.join(root, rel), os.path.join(sdir, rel))
            for root in getattr(a, cls_dirs):
                for c in glob.glob(os.path.join(root, stem + ".class")) + glob.glob(os.path.join(root, stem + "$*.class")):
                    dst = os.path.join(cdir, os.path.relpath(c, root))
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy(c, dst)
            if v == "base":
                a.scope_names.append(os.path.basename(rel))
        os.makedirs(cdir, exist_ok=True)
        os.makedirs(sdir, exist_ok=True)
        setattr(a, cls_dirs, [cdir])
        setattr(a, src_dirs, [sdir])
    a.json = None                       # the whole-program result (used by reverify) stays as it is


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", nargs="+", required=True)
    ap.add_argument("--changed", nargs="+", required=True)
    ap.add_argument("--base-src", nargs="+", required=True)
    ap.add_argument("--changed-src", nargs="+", required=True)
    ap.add_argument("--mapping", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--why", nargs="*", default=[])
    ap.add_argument("--html", default=None, help="write out/html/<NAME>.html")
    ap.add_argument("--title-v", default="", help="name of the change shown in the HTML title")
    ap.add_argument("--scope", nargs="*", default=[],
                    help="analyze only these source files (as if the program had nothing else; other classes are "
                         "treated like library code and there are no tests), e.g. legacy/src/main/java/.../X.java")
    a = ap.parse_args()
    if a.scope:
        restrict(a)

    P = {"base": Program(a.base, a.base_src), "new": Program(a.changed, a.changed_src)}
    hb, hn = P["base"].hashes, P["new"].hashes
    changed = sorted(m for m in hb.keys() & hn.keys() if hb[m] != hn[m])
    added = sorted(hn.keys() - hb.keys())
    removed = sorted(hb.keys() - hn.keys())

    # 1. changed lines, per version and method
    seeds = {"base": defaultdict(set), "new": defaultdict(set)}
    diffs = {}
    for m in changed + added + removed:
        cls = m.split("#")[0]
        if cls not in diffs:
            diffs[cls] = line_diff(P["base"].source_path(cls), P["new"].source_path(cls))
        da, db = diffs[cls]
        if m in P["base"].methods and m not in added:
            seeds["base"][m] = P["base"].method_lines(m) & da
        if m in P["new"].methods and m not in removed:
            seeds["new"][m] = P["new"].method_lines(m) & db
        if not seeds["base"].get(m) and not seeds["new"].get(m):      # e.g. inlined constant
            if m in P["new"].methods:
                seeds["new"][m] = P["new"].method_lines(m)
            else:
                seeds["base"][m] = P["base"].method_lines(m)

    # 2. system dependence graphs and slices
    A = {v: Analysis(P[v], seeds[v]) for v in ("new", "base")}

    # 3. results, joined over both versions (the changed version first)
    all_methods = set(P["base"].methods) | set(P["new"].methods)

    def outs_of(m):
        r = {}
        for v in ("new", "base"):
            for out, n in A[v].outputs(m).items():
                r.setdefault(out, (v, n, False))
        return r

    def test_outs(m):
        r = outs_of(m)
        for v in ("new", "base"):
            for out, n in A[v].outputs(m, test_slice=True).items():
                if out[0] in ("ret", "exc"):
                    r.setdefault(out, (v, n, True))
        return {o: x for o, x in r.items() if o[0] in ("ret", "exc")}

    impacted = sorted(m for m in all_methods if not is_test(m) and outs_of(m))
    tests = sorted(m for m in all_methods if is_test_method(m) and test_outs(m))
    n_tests = sum(1 for m in all_methods if is_test_method(m))
    data_w = {}
    writers = {}                        # every method whose written value may differ, per data item
    for m in sorted(all_methods):
        if is_test(m):
            continue
        for out, x in outs_of(m).items():
            if out[0] in GLOBAL_KINDS and out[1].startswith(PFX) and not is_test(out[1].rsplit(".", 1)[0] + "#"):
                data_w.setdefault(out, (m,) + x)
                writers.setdefault(out, []).append(m)
    data = sorted(data_w)
    mapping = load_mapping(a.mapping)

    def chain(v, n, ts=False):
        return A[v].chain(n, ts)

    def chains(v, n, ts, limit=3):
        """up to `limit` reasons for node n, starting from different changed methods, shortest first"""
        out = [chain(v, n, ts)]
        if ts:
            return out
        seen = {(out[0][0][0]["m"], out[0][0][0]["line"])} if out[0][0] else set()
        cands = []
        for sm, par in A[v].per_seed().items():
            if n in par:
                items, last = A[v].chain(n, par=par)
                if items and (items[0]["m"], items[0]["line"]) not in seen:
                    cands.append((len(items), sm, (items, last)))
        for _, sm, c in sorted(cands, key=lambda x: (x[0], x[1])):
            if len(out) >= limit:
                break
            if sm in {x[0][0]["m"] for x in out if x[0]}:
                continue
            out.append(c)
        return out

    def chain_txt(v, n, ts=False, ind="    ", chain_=None):
        items, last = chain_ or chain(v, n, ts)
        out = []
        for k, it in enumerate(items):
            src = P[v].source_path(it["m"].split("#")[0])
            code = ""
            if src:
                ls = open(src).read().splitlines()
                code = ls[it["line"] - 1].strip() if 0 < it["line"] <= len(ls) else ""
            if it["via"]:
                out.append("%s  ↓ %s" % (ind, it["via"]))
            out.append("%s%s %s:%d  %s%s" % (ind, "바뀐 줄" if k == 0 else "→", short(it["m"]), it["line"], code,
                                             "  (변경 전 코드)" if v == "base" else ""))
        if last:
            out.append("%s  ↓ %s" % (ind, last))
        return out

    print("# 변경 영향 보고서 (def-use 기반, 시스템 의존 그래프)\n")
    if a.scope:
        print("분석 범위: %s 만 (다른 클래스의 코드와 테스트 코드는 없는 것으로 보고 분석함)\n" % ", ".join(a.scope_names))
    print("## 1. 바뀐 줄\n")
    for m in sorted(set(seeds["base"]) | set(seeds["new"])):
        tag = "추가" if m in added else ("삭제" if m in removed else "변경")
        cls = m.split("#")[0]
        parts = []
        for v in ("base", "new"):
            ls = sorted(seeds[v].get(m, ()))
            if ls:
                parts.append("%s %s:%s" % ("변경 전" if v == "base" else "변경 후",
                                           os.path.basename(P[v].source_path(cls) or "?"), ",".join(map(str, ls))))
        print("- [%s] %s  (%s)" % (tag, short(m), "; ".join(parts)))
    if not seeds["base"] and not seeds["new"]:
        print("- (없음: 컴파일된 코드가 같음)")

    print("\n## 2. 값이 달라질 수 있는 데이터 (%d)\n" % len(data))
    for gl in data:
        print("- %s  <- 쓰는 메서드: %s" % (g_txt(gl), ", ".join(short(m) for m in writers[gl])))

    print("\n## 3. 출력이 달라질 수 있는 메서드 (%d)\n" % len(impacted))
    for m in impacted:
        print("- %s: %s" % (short(m), ", ".join(sorted({out_txt(o) for o in outs_of(m)}))[:160]))

    if a.scope:
        print("\n## 4. 다시 돌릴 테스트\n\n- (범위 안에 테스트 코드가 없어 고르지 않음)")
    else:
        print("\n## 4. 다시 돌릴 테스트 (%d / %d)\n" % (len(tests), n_tests))
    for m in tests:
        print("- " + short(m))

    for w in a.why:
        cands = [m for m in all_methods if short(m).startswith(w) or m.startswith(w)]
        print("\n## 왜 영향받는가: %s\n" % w)
        if not cands:
            print("- 그런 메서드가 없음")
        for m in sorted(cands):
            outs = test_outs(m) if is_test(m) else outs_of(m)
            if not outs:
                print("- %s: 영향받지 않음" % short(m))
                continue
            for o, (v, n, ts) in sorted(outs.items()):
                print("- %s의 %s" % (short(m), out_txt(o)))
                for k, c in enumerate(chains(v, n, ts)):
                    if k:
                        print("    (다른 이유)")
                    for l in chain_txt(v, n, ts, chain_=c):
                        print(l)

    if a.html:
        html_report(a, P, seeds, changed, added, removed, data, data_w, impacted, tests, n_tests, all_methods,
                    mapping, outs_of, test_outs, chain, diffs, A, chains)

    if a.json:
        with open(a.json, "w") as f:
            json.dump({"changed": changed, "added": added, "removed": removed,
                       "impacted": impacted, "tests": tests,
                       "data": [list(n) for n in data],
                       "dafny": {m: mapping[m] for m in set(changed) | set(added) | set(removed) if m in mapping}},
                      f, indent=2)


def html_report(a, P, seeds, changed, added, removed, data, data_w, impacted, tests, n_tests, all_methods,
                mapping, outs_of, test_outs, chain, diffs, A, chains):
    e = report.e
    srccache = {}

    def src_line(v, m, ln):
        path = P[v].source_path(m.split("#")[0])
        if path not in srccache:
            srccache[path] = open(path).read().splitlines() if path else []
        lines = srccache[path]
        return os.path.basename(path or "?"), (lines[ln - 1].strip() if 0 < ln <= len(lines) else "")

    def chain_html(v, n, ts, target, chain_=None):
        items, last = chain_ or chain(v, n, ts)
        lis = []
        for k, it in enumerate(items):
            fname, code = src_line(v, it["m"], it["line"])
            via = "<div class='via'>↓ %s</div>" % e(it["via"]) if it["via"] and k > 0 else ""
            head = "<span class='via'>바뀐 줄%s</span>" % (" (변경 전 코드)" if v == "base" else "") if k == 0 else ""
            lis.append("<li%s>%s%s<div><b class='mono'>%s</b> <span class='via'>%s:%d</span></div>"
                       "<div class='mono'>%s</div></li>" % (
                           " class='src-line'" if k == 0 else "", via, head, e(short(it["m"])), e(fname), it["line"], e(code)))
        lis.append("<li>%s<b>%s</b></li>" % ("<div class='via'>↓ %s</div>" % e(last) if last else "", e(target)))
        return "<ol class='chain'>%s</ol>" % "".join(lis)

    def method_detail(m, outs, many=False):
        parts = []
        for o, (v, n, ts) in sorted(outs.items()):
            t = out_txt(o)
            last = t[-1]
            josa = "이" if "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28 else "가"
            cs = chains(v, n, ts) if many else [None]
            body = "".join(("<p class='via' style='margin:8px 0 0'>다른 이유 %d</p>" % k if k else "") +
                           chain_html(v, n, ts, "%s의 %s" % (short(m), t), c) for k, c in enumerate(cs))
            parts.append("<h3 style='margin:10px 0 2px;font-size:14px'>%s%s 달라질 수 있는 이유%s</h3>%s" % (
                e(t), josa, (" %d가지" % len(cs)) if len(cs) > 1 else "", body))
        return "".join(parts)

    prod_all = sorted(m for m in all_methods if not is_test(m) and "<clinit>" not in m)
    seeds_m = set(changed) | set(added) | set(removed)
    n_lines = sum(len(v) for vv in seeds.values() for v in vv.values())

    verdict = ("바뀐 줄에서 나온 값이 <span class='num'>%d</span>개 메서드와 <span class='num'>%d</span>개 데이터에 닿을 수 있습니다. "
               "다시 돌릴 테스트는 <span class='num'>%d</span> / %d개입니다." % (len(impacted), len(data), len(tests), n_tests))
    if a.scope:
        verdict = verdict.split("다시 돌릴")[0].strip()
    fx = [("바뀐 메서드", len(seeds_m)), ("바뀐 줄", n_lines), ("값이 달라질 수 있는 데이터", len(data)),
          ("출력이 달라질 수 있는 메서드", "%d / %d" % (len(impacted), len(prod_all))),
          ("다시 돌릴 테스트", "%d / %d" % (len(tests), n_tests))]
    if a.scope:
        fx = fx[:-1]

    body = []
    if a.why:
        rows, n_hit = [], 0
        for w in a.why:
            cands = [m for m in all_methods if short(m).startswith(w) or m.startswith(w)]
            if not cands:
                rows.append("<p><b class='mono'>%s</b>: 그런 메서드가 없습니다</p>" % e(w))
            for m in sorted(cands):
                outs = test_outs(m) if is_test(m) else outs_of(m)
                if outs:
                    n_hit += 1
                    rows.append("<details open><summary><b class='mono'>%s</b></summary><div>%s</div></details>" % (
                        e(short(m)), method_detail(m, outs, many=True)))
                else:
                    rows.append("<p><b class='mono'>%s</b>: 영향받지 않음</p>" % e(short(m)))
        # WHY= asks only for the reasons: a short page of its own, not the whole report again
        title = "변경 영향의 이유: %s" % (a.title_v or "변경")
        lead = ("물어본 메서드가 왜 영향받는지만 보여 줍니다. 위에서 아래로 읽습니다. "
                "노란 점의 바뀐 줄에서 나온 값이 어느 줄들을 거쳐 이 메서드의 출력까지 오는지, 실제 코드 줄로 보여 줍니다. "
                "줄 사이의 회색 글은 값이 어떻게 넘어갔는지(필드에 저장, 반환값, 인자, if 조건)입니다. "
                "바뀐 메서드가 여럿이면, 서로 다른 바뀐 메서드에서 출발하는 이유를 3가지까지 보여 줍니다. "
                "전체 영향 분석 결과는 WHY 없이 실행하면 나옵니다.")
        html_text = report.page(title, e(lead), "<section id='why'>%s</section>" % "".join(rows),
                                command="make impact V=%s WHY=%s" % (a.title_v, " ".join(a.why)) + scope_arg(a))
        report.write(a.html, title, html_text, "info", "물어본 %d개 중 영향받음 %d" % (len(a.why), n_hit))
        return

    code = []
    for cls in sorted(diffs, key=lambda c: (is_test(c + "#"), c)):
        pa, pb = P["base"].source_path(cls), P["new"].source_path(cls)
        la = open(pa).read().splitlines() if pa else []
        lb = open(pb).read().splitlines() if pb else []
        name = (pb or pa or cls).split("/java/")[-1]
        if la != lb and not any(name == c[0] for c in code):
            code.append((name, report.split_diff(name, la, lb)))
    body.append("<section id='code'><h2>바뀐 코드</h2><p class='sub'>분석은 이 줄들에서 출발합니다. 지운 줄(빨강)은 변경 전 코드에서, "
                "새로 쓴 줄(초록)은 변경 후 코드에서 출발합니다. 주석이나 줄바꿈만 바뀐 메서드는 출발점에서 뺍니다. "
                "테스트 코드의 변경은 어느 테스트를 다시 돌릴지만 정하고, 제품 코드의 영향으로 세지 않습니다.</p>%s</section>"
                % "".join(h for _, h in code))

    pk = {}
    for m in prod_all:
        p_ = short(m).split(".")[0] if "." in short(m).split("#")[0] else "-"
        pk.setdefault(p_, [0, 0])[1] += 1
        if m in impacted:
            pk[p_][0] += 1
    dk = {}
    for gl in data:
        p_ = short(gl[1]).split(".")[0]
        dk[p_] = dk.get(p_, 0) + 1
    rows = []
    for p_, (hit_, tot) in sorted(pk.items(), key=lambda x: -x[1][0] / max(1, x[1][1])):
        rows.append([e(p_), "%d / %d" % (hit_, tot), '<div class="bar"><i style="width:%.0f%%"></i></div>' % (100.0 * hit_ / tot),
                     str(dk.get(p_, 0))])
    body.append("<section id='pkg'><h2>패키지별로 얼마나 퍼졌나</h2><p class='sub'>패키지마다 출력이 달라질 수 있는 메서드의 비율입니다.</p>%s</section>"
                % report.table(["패키지", "메서드", "", "데이터"], rows, numeric=(1, 3)))

    wr = {}
    dset = set(data)
    for m in sorted(all_methods):
        if not is_test(m):
            for o in outs_of(m):
                if o in dset:
                    wr.setdefault(o, []).append(m)
    drows = []
    for gl in data:
        m, v, n, ts = data_w[gl]
        ws = wr.get(gl, [m])
        drows.append("<details data-k='%s'><summary><span class='mono'>%s</span> <span class='via'>쓰는 메서드: %s</span></summary>"
                     "<div>%s%s</div></details>" % (
                         e(g_txt(gl)), e(g_txt(gl)), e(", ".join(short(x) for x in ws[:4]) + (" 외 %d개" % (len(ws) - 4) if len(ws) > 4 else "")),
                         "<p class='via' style='margin:6px 0 0'>%s에서 쓰는 경우:</p>" % e(short(m)) if len(ws) > 1 else "",
                         chain_html(v, n, ts, g_txt(gl))))
    body.append("<section id='data'><h2>값이 달라질 수 있는 데이터 (%d)</h2><p class='sub'>필드, 그리고 필드에 담긴 배열·컬렉션의 내용입니다. "
                "펼치면 어느 바뀐 줄에서 어떤 줄들을 거쳐 왔는지 보입니다.</p>"
                "<input class='filter' data-target='dlist' placeholder='이름으로 찾기'><div id='dlist'>%s</div></section>"
                % (len(data), "".join(drows)))

    mrows = []
    for m in impacted:
        outs = outs_of(m)
        tags = " ".join(report.badge(t, "info") for t in sorted({out_txt(o) if o[0] in ("ret", "exc") else
                                                                 ("필드 씀" if o[0] == "field" else "내용 씀") for o in outs}))
        mark = report.badge("바뀐 메서드", "warn") if m in seeds_m else ""
        mrows.append("<details data-k='%s'><summary><span class='mono'>%s</span> %s %s</summary><div>%s</div></details>" % (
            e(short(m)), e(short(m)), tags, mark, method_detail(m, outs)))
    body.append("<section id='methods'><h2>출력이 달라질 수 있는 메서드 (%d)</h2><p class='sub'>반환값, 예외, 필드나 컬렉션에 쓰는 값 중 하나라도 "
                "달라질 수 있는 메서드입니다. \"달라질 수 있다\"이지 \"달라졌다\"가 아닙니다. 실제로 달라졌는지는 테스트와 동작 기록 비교로 판단합니다.</p>"
                "<input class='filter' data-target='mlist' placeholder='클래스나 메서드 이름으로 찾기'><div id='mlist'>%s</div></section>"
                % (len(impacted), "".join(mrows)))

    if a.scope:
        body.append("<section id='tests'><h2>다시 돌릴 테스트</h2><p class='note'>범위 안에 테스트 코드가 없으므로 "
                    "테스트는 고르지 않았습니다.</p></section>")
    all_tests = sorted(m for m in all_methods if is_test_method(m))
    chips = "".join('<span class="chip %s">%s</span>' % ("on" if t in tests else "off", e(short(t))) for t in all_tests)
    body.append("" if a.scope else "<section id='tests'><h2>다시 돌릴 테스트 (%d / %d)</h2><p class='sub'>파란 테두리가 결과가 달라질 수 있는 테스트, "
                "흐린 것은 영향이 없는 테스트입니다.%s</p><div class='chips'>%s</div></section>"
                % (len(tests), n_tests, (" 테스트가 왜 들어갔는지 보려면 명령 끝에 <code>WHY=테스트 이름</code>을 붙여 다시 실행합니다"
                                         "(예: <code>%s</code>). 바뀐 줄에서 그 테스트까지 값이 지나간 코드 줄만 따로 보여 줍니다."
                                         % e("make impact V=%s WHY=%s" % (a.title_v, short(tests[0]).split("(")[0]))) if tests else "",
                   chips))

    toc = [("code", "바뀐 코드"), ("pkg", "패키지별 범위"), ("data", "데이터"), ("methods", "메서드"),
           ("tests", "테스트")]
    cmd = "make impact V=%s" % a.title_v + scope_arg(a)
    title = "변경 영향: %s%s" % (a.title_v or "변경", (" (%s만)" % ", ".join(a.scope_names)) if a.scope else "")
    lead = ("바뀐 줄에서 계산된 값이 어디까지 흘러가는지 따라갑니다(def-use 분석). 값을 저장한 필드와 컬렉션, 그것을 읽는 줄, "
            "그 값으로 판단하는 if 안의 일까지 메서드를 넘나들며 끝까지 따라갑니다. 메서드를 부르고 돌아올 때는 "
            "부른 곳으로만 돌아가도록 짝을 맞춥니다.")
    if a.scope:
        lead += (" 이번에는 %s 하나만 분석합니다. 프로그램에 이 파일만 있는 것처럼, 다른 클래스는 코드를 모르는 "
                 "라이브러리로 보고 테스트 코드도 없는 것으로 봅니다." % ", ".join(a.scope_names))
        toc = [t for t in toc if t[0] not in ("pkg",)]
        body = [b for b in body if not b.startswith("<section id='pkg'>")]
    html_text = report.page(title, e(lead), "".join(body), verdict=(verdict, "info"), facts_items=fx,
                            command=cmd, toc=toc)
    report.write(a.html, title, html_text, "info",
                 ("%s만: 메서드 %d, 데이터 %d" % (", ".join(a.scope_names), len(impacted), len(data))) if a.scope else
                 "메서드 %d, 데이터 %d, 테스트 %d/%d" % (len(impacted), len(data), len(tests), n_tests))


if __name__ == "__main__":
    main()
