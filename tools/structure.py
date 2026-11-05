#!/usr/bin/env python3
"""
structure: three views of the legacy code for lab A0 (understanding the code before changing it).

  path    One message handled by the hub. The methods the call graph says may run (calls resolved
          to every implementation of an interface method) next to the methods that really ran
          (out/raw/path.json from tools/java/LineTracer). Methods only one side has, and why.
  state   Shared state map. For every field (or the contents of a collection held in a field)
          that changes after start-up: the methods of other classes that change it and that read
          it, through the methods of the class that owns it. Pairs of classes that never call
          each other but are connected through such state.
  config  One configuration key. Where the key appears in the code, and where the value read
          with it may flow (forward slice on the system dependence graph, tools/sdg.py): the
          methods it reaches, the conditions decided with it, and the chain for each.

usage:
  structure.py path   --classes legacy/build/classes --src legacy/src/main/java --trace out/raw/path.json --html path
  structure.py state  --classes legacy/build/classes --src legacy/src/main/java --html state
  structure.py config --classes legacy/build/classes --src legacy/src/main/java --key temp.highCelsius --html config-...
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import defuse  # noqa: E402
import impact  # noqa: E402
import report  # noqa: E402
import sdg  # noqa: E402

e = report.e
short = impact.short
INVOKES = ("invokevirtual", "invokeinterface", "invokestatic", "invokespecial")
BRANCHES = defuse.BRANCH2 | {"ifeq", "ifne", "iflt", "ifge", "ifgt", "ifle", "ifnull", "ifnonnull",
                             "tableswitch", "lookupswitch"}
ENTRIES = ("com.dxlab.homehub.app.HomeHub#ingest(java.lang.String)", "com.dxlab.homehub.app.HomeHub#drain()")


def cls_of(m):
    return m.split("#")[0]


def cshort(c):
    return c.rsplit(".", 1)[-1]


def mshort(m):
    """Class.method (parameters dropped unless overloaded names matter)"""
    return cshort(cls_of(m)) + "." + m.split("#")[1].split("(")[0]


class Code:
    def __init__(self, classes, src):
        self.P = impact.Program([classes], [src])
        self.srccache = {}

    def line(self, m, ln):
        path = self.P.source_path(cls_of(m))
        if path not in self.srccache:
            self.srccache[path] = open(path).read().splitlines() if path else []
        ls = self.srccache[path]
        return os.path.basename(path or "?"), (ls[ln - 1].strip() if 0 < ln <= len(ls) else "")

    def call_sites(self, m):
        """[(line, kind, owner, name, desc, [targets])] in code order"""
        meth = self.P.methods.get(m)
        if not meth:
            return []
        out = []
        for pc, op, rest, _ in meth["insns"]:
            if op not in INVOKES:
                continue
            kind, owner, name, desc = defuse.ref_member(rest)
            owner = owner or meth["cls"]
            tg = [t for t in self.P.targets(op[6:], owner, name, desc) if t in self.P.methods]
            out.append((defuse.line_of(meth, pc), op[6:], owner, name, desc, tg))
        return out


# --------------------------------------------------------------------------------------------- path

def is_bridge(P, m):
    """compiler-made bridge (compare(Object,Object) next to compare(Device,Device)): shown once"""
    cls, rest = m.split("#")
    name, params = rest.split("(")[0], rest.split("(")[1].rstrip(")").split(",")
    if not params or params == [""] or any(p != "java.lang.Object" for p in params):
        return False
    return any(o != m and o.startswith(cls + "#" + name + "(") and len(o.split("(")[1].split(",")) == len(params)
               for o in P.methods)


def cmd_path(a):
    C = Code(a.classes, a.src)
    P = C.P
    tr = json.load(open(a.trace))

    # static: methods reachable from the entries
    reach, order, todo = set(), [], list(ENTRIES)
    while todo:
        m = todo.pop(0)
        if m in reach or m not in P.methods:
            continue
        reach.add(m)
        order.append(m)
        for _, _, _, _, _, tg in C.call_sites(m):
            todo += [t for t in tg if t not in reach]

    # dynamic: methods that ran, in order of first execution, and the lines that ran
    by_name = defaultdict(list)
    for m in P.methods:
        by_name[(cls_of(m), m.split("#")[1].split("(")[0])].append(m)
    ran, ran_order, ran_lines = set(), [], defaultdict(set)
    for c, name, ln in tr["steps"]:
        cands = by_name.get((c, name), [])
        hit = [m for m in cands if ln in P.method_lines(m)] or cands[:1]
        if not hit:
            continue
        m = hit[0]
        ran_lines[m].add(ln)
        if m not in ran:
            ran.add(m)
            ran_order.append((m, ln))

    reach = {m for m in reach if not is_bridge(P, m)}
    ran = {m for m in ran if not is_bridge(P, m)}
    ran_order = [x for x in ran_order if x[0] in ran]
    both = reach & ran
    static_only = sorted(reach - ran)
    dyn_only = sorted(ran - reach)

    # why a method of the call graph did not run: was a line that may call it executed?
    callers = defaultdict(list)            # callee -> [(caller, line, n candidates)]
    for m in reach:
        for ln, kind, owner, name, desc, tg in C.call_sites(m):
            for t in tg:
                callers[t].append((m, ln, len(tg)))

    def why_not(m):
        hits = [(c, ln, n) for c, ln, n in callers[m] if ln in ran_lines.get(c, ())]
        multi = [h for h in hits if h[2] > 1]
        if multi:
            c, ln, n = multi[0]
            return "부르는 줄은 실행됐지만 다른 구현이 불림 (%s:%d, 후보 %d개)" % (mshort(c), ln, n), "warn"
        if hits:
            c, ln, n = hits[0]
            return "부르는 줄은 실행됐지만 호출까지 가지 않음: 같은 줄의 앞 조건에서 끝남 (%s:%d)" % (mshort(c), ln), "mute"
        c, ln, _ = sorted(callers[m])[0] if callers[m] else (None, 0, 0)
        if c is None:
            return "", "mute"
        return "부르는 줄이 이번에는 실행되지 않음 (%s:%d)" % (mshort(c), ln), "mute"

    out = tr.get("output", "")
    msg = next((l[8:] for l in out.splitlines() if l.startswith("MESSAGE ")), "?")
    before = next((l[7:] for l in out.splitlines() if l.startswith("BEFORE ")), "")
    after = next((l[6:] for l in out.splitlines() if l.startswith("AFTER ")), "")

    body = []
    # 1. what happened
    rows = []
    for k, x, y in report.state_diff(before, after) or []:
        rows.append([e(k), "<span class='mono'>%s</span>" % e(x), "<span class='mono'>%s</span>" % e(y)])
    body.append("<section id='s1'><h2>메시지와 결과</h2><p class='sub'>메시지 <code>%s</code>를 넣고 허브가 대기열을 "
                "다 비울 때까지 처리했습니다(그 사이 만들어진 이벤트까지).</p>%s</section>" % (
                    e(msg), report.table(["항목", "처리 전", "처리 후"], rows) if rows else ""))

    # 2. what really ran, in order
    rows = []
    for i, (m, ln) in enumerate(ran_order, 1):
        f, code = C.line(m, ln)
        rows.append(([str(i), "<b class='mono'>%s</b>" % e(mshort(m)), "<span class='mono'>%s</span>" % e(code),
                      "" if m in reach else report.badge("호출 그래프에 없음", "bad")], "" if m in reach else "bad"))
    body.append("<section id='s2'><h2>실제로 실행된 메서드 %d개 (처음 실행된 순서)</h2>"
                "<p class='sub'>디버거로 실행된 줄을 기록한 결과입니다. 둘째 칸은 그 메서드에서 처음 실행된 줄입니다.</p>%s</section>"
                % (len(ran_order), report.table(["#", "메서드", "처음 실행된 줄", ""], rows, numeric=(0,))))

    # 3. the call graph, as a tree from the entries
    lines_out, shown = [], set()

    def walk(m, depth, via):
        mark = "✓" if m in ran else "·"
        tone = "" if m in ran else "color:var(--muted)"
        again = m in shown
        lines_out.append("<div style='padding-left:%dpx;%s' class='mono'>%s %s%s%s</div>" % (
            depth * 18, tone, mark, e(mshort(m)), " <span class='via'>%s</span>" % e(via) if via else "",
            " <span class='via'>(위에 나옴)</span>" if again else ""))
        if again:
            return
        shown.add(m)
        seen_t = set()
        for ln, kind, owner, name, desc, tg in C.call_sites(m):
            for t in tg:
                if t in seen_t:
                    continue
                seen_t.add(t)
                v = ("%s 호출의 후보 %d개 중 하나" % (cshort(owner) + "." + name, len(tg))) if len(tg) > 1 else ""
                walk(t, depth + 1, v)
    for en in ENTRIES:
        walk(en, 0, "")
    body.append("<section id='s3'><h2>호출 그래프 (%d개 메서드)</h2>"
                "<p class='sub'>클래스 파일의 호출문에서 만든 그래프입니다. 인터페이스 메서드 호출은 그 인터페이스를 구현한 "
                "모든 클래스의 메서드로 이어 줍니다. ✓는 이번 실행에서 실제로 실행된 메서드, ·는 실행되지 않은 메서드입니다. "
                "같은 메서드는 처음 나올 때만 펼칩니다.</p>"
                "<details><summary>호출 그래프 펼치기</summary><div class='box' style='font-size:12.5px;line-height:1.7'>%s</div></details></section>"
                % (len(reach), "".join(lines_out)))

    # 4. differences
    rows = []
    for m in static_only:
        w, tone = why_not(m)
        rows.append(([e(mshort(m)), e(w)], "chg" if tone == "warn" else ""))
    body.append("<section id='s4'><h2>호출 그래프에만 있는 메서드 %d개</h2>"
                "<p class='sub'>부를 수는 있지만 이번 메시지에서는 실행되지 않은 메서드입니다. 노란 줄은 부르는 줄이 실행됐지만 "
                "인터페이스 뒤의 다른 구현이 불린 경우입니다.</p>%s</section>"
                % (len(static_only), report.table(["메서드", "이번에 실행되지 않은 이유"], rows)))
    if dyn_only:
        rows = [[e(mshort(m)), "프로그램 코드에 이 메서드를 부르는 호출문이 없음: 라이브러리(문자열 연결, HashMap, 정렬 등)가 불렀음"]
                for m in dyn_only]
        dtxt = report.table(["메서드", "이유"], rows)
    else:
        dtxt = ("<p>없습니다. 이번 메시지에서 실행된 메서드는 모두 호출 그래프에 있습니다. 라이브러리가 대신 부르는 메서드"
                "(정렬의 비교 함수, HashMap이 부르는 equals·hashCode, 문자열 연결이 부르는 toString)가 실행됐다면 여기에 나옵니다.</p>")
    body.append("<section id='s5'><h2>실행됐지만 호출 그래프에 없는 메서드 %d개</h2>%s</section>" % (len(dyn_only), dtxt))

    verdict = ("호출 그래프는 <span class='num'>%d</span>개 메서드가 실행될 수 있다고 하고, 실제로는 "
               "<span class='num'>%d</span>개가 실행됐습니다." % (len(reach), len(ran)))
    fx = [("호출 그래프의 메서드", len(reach)), ("실제로 실행된 메서드", len(ran)), ("둘 다", len(both)),
          ("호출 그래프에만", len(static_only)), ("실행에만", len(dyn_only))]
    toc = [("s1", "메시지와 결과"), ("s2", "실제로 실행된 메서드"), ("s3", "호출 그래프"), ("s4", "그래프에만 있는 것"),
           ("s5", "실행에만 있는 것")]
    page = report.page("메시지 하나의 처리 경로", e("메시지 하나가 처리될 때 실행될 수 있는 메서드(호출 그래프)와 실제로 "
                                                 "실행된 메서드(실행 기록)를 비교합니다."),
                       "".join(body), verdict=(verdict, "info"), facts_items=fx, command=a.command, toc=toc)
    report.write(a.html, "메시지 하나의 처리 경로", page, "info",
                 "호출 그래프 %d개, 실행 %d개" % (len(reach), len(ran)))
    print("호출 그래프 %d개 메서드, 실제로 실행 %d개 (둘 다 %d, 그래프에만 %d, 실행에만 %d)"
          % (len(reach), len(ran), len(both), len(static_only), len(dyn_only)))


# -------------------------------------------------------------------------------------------- state

def g_owner(gl):
    return gl[1].rsplit(".", 1)[0]


def g_name(gl):
    c, f = gl[1].rsplit(".", 1)
    return ("%s.%s" % (cshort(c), f)) + (" 의 내용" if gl[0] == "elem" else "")


def state_access(C):
    """{global: {"w": {outside method: [owner method called]}, "r": {...}}} for globals of program classes"""
    P = C.P
    pdg = {m: defuse.build_pdg(meth, P.targets) for m, meth in P.methods.items() if meth["insns"]}
    reads = {m: set(p.reads) for m, p in pdg.items()}
    writes = {m: set(p.defs) for m, p in pdg.items()}
    sites = {m: C.call_sites(m) for m in pdg}
    # effects of a method of class O counting only calls inside O
    eff_r, eff_w = {m: set(v) for m, v in reads.items()}, {m: set(v) for m, v in writes.items()}
    changed = True
    while changed:
        changed = False
        for m in pdg:
            for _, _, _, _, _, tg in sites[m]:
                for t in tg:
                    if t in pdg and cls_of(t) == cls_of(m):
                        r, w = eff_r[t] - eff_r[m], eff_w[t] - eff_w[m]
                        if r or w:
                            eff_r[m] |= r
                            eff_w[m] |= w
                            changed = True
    acc = defaultdict(lambda: {"w": defaultdict(set), "r": defaultdict(set)})
    for m in pdg:
        cm = cls_of(m)
        if impact.is_test(m):
            continue
        for gl in reads[m]:
            if g_owner(gl) != cm:
                acc[gl]["r"][m].add("직접")
        for gl in writes[m]:
            if g_owner(gl) != cm:
                acc[gl]["w"][m].add("직접")
        for _, _, _, _, _, tg in sites[m]:
            for t in tg:
                if t not in pdg or cls_of(t) == cm:
                    continue
                for gl in ([] if is_ctor(t) else eff_w[t]):     # a new object's own fields: not a change
                    if g_owner(gl) == cls_of(t):
                        acc[gl]["w"][m].add(mshort(t))
                for gl in eff_r[t]:
                    if g_owner(gl) == cls_of(t):
                        acc[gl]["r"][m].add(mshort(t))
    return acc, sites


def is_ctor(m):
    return "#<init>" in m or "#<clinit>" in m


def cmd_state(a):
    C = Code(a.classes, a.src)
    acc, sites = state_access(C)
    PFX = impact.PFX
    # class-level calls, to find classes connected only through state
    calls = defaultdict(set)
    for m, ss in sites.items():
        for _, _, _, _, _, tg in ss:
            for t in tg:
                if cls_of(t) != cls_of(m):
                    calls[cls_of(m)].add(cls_of(t))

    def related(x, y):
        return y in calls[x] or x in calls[y]

    rows_by_owner = defaultdict(list)
    hidden = []
    n_states = 0
    for gl in sorted(acc, key=lambda g: (g_owner(g), g[1], g[0])):
        if not gl[1].startswith(PFX) or impact.is_test(g_owner(gl) + "#"):
            continue
        ws = {m: v for m, v in acc[gl]["w"].items() if not is_ctor(m)}
        rs = {m: v for m, v in acc[gl]["r"].items() if not is_ctor(m)}
        if not ws:
            continue                       # set only while the hub starts: not shared state
        wc = sorted({cls_of(m) for m in ws})
        rc = sorted({cls_of(m) for m in rs} - set(wc))
        if not rc and len(wc) < 2:
            continue                       # one class changes it and nobody else reads it
        n_states += 1

        def cell(d):
            return "<br>".join("<span class='mono'>%s</span> <span class='via'>(%s)</span>" % (
                e(mshort(m)), e(", ".join(sorted(v)))) for m, v in sorted(d.items()))
        rows_by_owner[g_owner(gl)].append([("<b class='mono'>%s</b>" % e(g_name(gl))), cell(ws), cell(rs)])
        for w in wc:
            for r in rc:
                if not related(w, r):
                    hidden.append((w, gl, r))

    body = []
    if hidden:
        grp = defaultdict(set)
        for w, gl, r in hidden:
            grp[(gl, r)].add(w)
        rows = []
        for (gl, r), ws_ in sorted(grp.items(), key=lambda x: (g_owner(x[0][0]), x[0][0][1], x[0][1])):
            rows.append([", ".join("<b class='mono'>%s</b>" % e(cshort(w)) for w in sorted(ws_)),
                         "<span class='mono'>%s</span>" % e(g_name(gl)), "<b class='mono'>%s</b>" % e(cshort(r))])
        body.append("<section id='s1'><h2>서로 부르지 않는데 상태로 이어진 곳 %d곳</h2>"
                    "<p class='sub'>왼쪽 클래스가 바꾼 값을 오른쪽 클래스가 읽습니다. 두 클래스 사이에는 어느 쪽으로도 호출이 없어서 "
                    "호출 그래프로는 이 연결이 보이지 않습니다.</p>%s</section>" % (
                        len({(gl, r) for _, gl, r in hidden}), report.table(["바꾸는 클래스", "상태", "읽는 클래스"], rows)))
    secs = []
    for owner in sorted(rows_by_owner):
        secs.append("<h3>%s</h3>%s" % (e(cshort(owner)), report.table(
            ["상태", "바꾸는 메서드 (거쳐 가는 메서드)", "읽는 메서드 (거쳐 가는 메서드)"], rows_by_owner[owner])))
    body.append("<section id='s2'><h2>공유 상태 %d개</h2><p class='sub'>허브가 시작된 뒤에 바뀌고, 둘 이상의 클래스가 쓰는 "
                "필드(또는 필드에 든 컬렉션의 내용)입니다. 다른 클래스의 메서드가 그 필드를 가진 클래스의 메서드를 거쳐 바꾸거나 "
                "읽는 경우를 모았습니다. 괄호 안은 거쳐 가는 메서드입니다. 생성자에서만 하는 일은 뺐습니다.</p>%s</section>"
                % (n_states, "".join(secs)))
    verdict = ("허브가 돌아가는 동안 여러 클래스가 함께 쓰는 상태가 <span class='num'>%d</span>개 있고, 서로 부르지 않는 클래스끼리 "
               "상태로 이어진 곳이 <span class='num'>%d</span>곳 있습니다." % (n_states, len({(gl, r) for _, gl, r in hidden})))
    page = report.page("공유 상태 지도", e("누가 어떤 상태를 바꾸고 누가 읽는지 모은 표입니다."), "".join(body),
                       verdict=(verdict, "info"), command=a.command,
                       toc=[("s1", "상태로만 이어진 클래스"), ("s2", "공유 상태")] if hidden else None)
    report.write(a.html, "공유 상태 지도", page, "info", "공유 상태 %d개, 상태로만 이어진 곳 %d곳"
                 % (n_states, len({(gl, r) for _, gl, r in hidden})))
    print("공유 상태 %d개, 서로 부르지 않는데 상태로 이어진 곳 %d곳" % (n_states, len({(gl, r) for _, gl, r in hidden})))


# ------------------------------------------------------------------------------------------- config

def cmd_config(a):
    C = Code(a.classes, a.src)
    P = C.P
    key = a.key
    # 1. where the key appears: string constants in the code
    uses = []                                   # (method, line, insn index of the call that takes it or None)
    for m, meth in sorted(P.methods.items()):
        ins = meth["insns"]
        for i, (pc, op, rest, _) in enumerate(ins):
            if op in ("ldc", "ldc_w") and rest.rstrip().endswith("String " + key):
                call = None
                for j in range(i + 1, min(i + 4, len(ins))):
                    if ins[j][1] in INVOKES:
                        _, _, name, desc = defuse.ref_member(ins[j][2])
                        if name.startswith("get") and name != "getProperty":
                            call = j
                        break
                at = ins[call][0] if call is not None else pc       # the line of the call that reads it
                uses.append((m, defuse.line_of(meth, at), call))
    rows = []
    for m, ln, call in uses:
        f, code = C.line(m, ln)
        what = "값을 읽음" if call is not None else ("기본값을 정함" if cls_of(m).endswith("HubConfig") else "")
        rows.append(["<b class='mono'>%s</b>" % e(mshort(m)), "%s:%d" % (e(f), ln), "<span class='mono'>%s</span>" % e(code), e(what)])
    body = ["<section id='s1'><h2>키가 나오는 곳 %d곳</h2><p class='sub'>코드에서 문자열 <code>%s</code>를 찾은 결과입니다"
            "(검색으로 찾을 수 있는 범위). 실제 값은 기본값이거나, 허브를 시작할 때 읽는 설정 파일(<code>hub.properties</code>)의 값입니다.</p>%s</section>"
            % (len(uses), e(key), report.table(["메서드", "파일:줄", "코드", ""], rows))]

    # 2. forward slice from the values read with the key
    G = sdg.SDG(P.methods, P.targets, impact.is_test)
    crit = []
    for m, ln, call in uses:
        if call is not None:
            n = G.ids.get((m, ("AO", call, "ret")))
            if n is not None:
                crit.append(n)
    A = impact.Analysis.__new__(impact.Analysis)
    A.P, A.G = P, G
    A.par_prod = G.slice(crit)
    A.par_test = {}
    A.prod_seeds = {}
    A._per_seed = None
    reached = sorted(m for m in P.methods if not impact.is_test(m) and A.outputs(m))
    data = set()
    for m in reached:
        for o in A.outputs(m):
            if o[0] in impact.GLOBAL_KINDS:
                data.add(o)

    def chain_html(n, target):
        items, last = A.chain(n)
        lis = []
        for k, it in enumerate(items):
            f, code = C.line(it["m"], it["line"])
            via = "<div class='via'>↓ %s</div>" % e(it["via"]) if it["via"] and k > 0 else ""
            head = "<span class='via'>설정값을 읽는 줄</span>" if k == 0 else ""
            lis.append("<li%s>%s%s<div><b class='mono'>%s</b> <span class='via'>%s:%d</span></div><div class='mono'>%s</div></li>"
                       % (" class='src-line'" if k == 0 else "", via, head, e(mshort(it["m"])), e(f), it["line"], e(code)))
        lis.append("<li>%s<b>%s</b></li>" % ("<div class='via'>↓ %s</div>" % e(last) if last else "", e(target)))
        return "<ol class='chain'>%s</ol>" % "".join(lis)

    # conditions decided with the value: branch instructions in the slice, nearest first
    conds = []
    for n, _ in A.par_prod.items():
        m, k = G.nodes[n]
        if m is None or k[0] != "i" or impact.is_test(m):
            continue
        op = P.methods[m]["insns"][k[1]][1]
        if op in BRANCHES:
            items, _ = A.chain(n)
            conds.append((len(items), m, G.lines[n], n))
    conds.sort(key=lambda x: (x[0], x[1], x[2]))
    seen, crows = set(), []
    for d, m, ln, n in conds:
        if (m, ln) in seen:
            continue
        seen.add((m, ln))
        f, code = C.line(m, ln)
        crows.append("<details><summary><b class='mono'>%s</b> <span class='via'>%s:%d</span> <span class='mono'>%s</span>"
                     " <span class='via'>(%d단계)</span></summary><div>%s</div></details>"
                     % (e(mshort(m)), e(f), ln, e(code), d, chain_html(n, "이 조건의 결과가 달라질 수 있음")))
    body.append("<section id='s2'><h2>이 값으로 판단하는 조건 %d곳</h2><p class='sub'>설정값이 흘러 들어가 결과가 달라질 수 있는 "
                "if·switch입니다. 가까운 것부터 보여 줍니다. 눌러서 값이 거기까지 가는 길을 봅니다.</p>%s</section>"
                % (len(crows), "".join(crows)))

    mrows = []
    for m in reached:
        outs = A.outputs(m)
        o, n = sorted(outs.items())[0]
        mrows.append("<details><summary><b class='mono'>%s</b> <span class='via'>%s</span></summary><div>%s</div></details>"
                     % (e(mshort(m)), e(", ".join(sorted({impact.out_txt(x) for x in outs}))[:140]),
                        chain_html(n, "%s의 %s" % (mshort(m), impact.out_txt(o)))))
    body.append("<section id='s3'><h2>값이 닿는 메서드 %d개</h2><p class='sub'>설정값에 따라 결과(반환값, 예외, 필드에 쓰는 값)가 "
                "달라질 수 있는 메서드입니다.</p><input class='filter' placeholder='메서드 이름으로 찾기' "
                "oninput=\"var q=this.value.toLowerCase();this.parentNode.querySelectorAll('details').forEach(function(d){"
                "d.style.display=d.textContent.toLowerCase().indexOf(q)<0?'none':''})\">%s</section>" % (len(reached), "".join(mrows)))
    files_n = len({cls_of(m) for m, _, _ in uses})
    verdict = ("키 <code>%s</code>는 코드 %d곳(%d개 클래스)에 나오지만, 그 값은 <span class='num'>%d</span>개 메서드와 "
               "<span class='num'>%d</span>개 조건에 닿을 수 있습니다." % (e(key), len(uses), files_n, len(reached), len(crows)))
    fx = [("키가 나오는 곳", len(uses)), ("값이 닿는 메서드", len(reached)), ("값으로 판단하는 조건", len(crows)),
          ("값이 달라질 수 있는 데이터", len(data))]
    page = report.page("설정값 따라가기: %s" % key, e("설정 키 하나를 코드에서 찾고, 그 값이 어디까지 흘러가는지 따라갑니다."),
                       "".join(body), verdict=(verdict, "info"), facts_items=fx, command=a.command,
                       toc=[("s1", "키가 나오는 곳"), ("s2", "값으로 판단하는 조건"), ("s3", "값이 닿는 메서드")])
    report.write(a.html, "설정값 따라가기: %s" % key, page, "info",
                 "키 %d곳, 닿는 메서드 %d개, 조건 %d곳" % (len(uses), len(reached), len(crows)))
    print("키 %s: 코드에 %d곳, 값이 닿는 메서드 %d개, 값으로 판단하는 조건 %d곳" % (key, len(uses), len(reached), len(crows)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=("path", "state", "config"))
    ap.add_argument("--classes", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--trace", default=None)
    ap.add_argument("--key", default=None)
    ap.add_argument("--html", required=True)
    ap.add_argument("--command", default=None)
    a = ap.parse_args()
    {"path": cmd_path, "state": cmd_state, "config": cmd_config}[a.what](a)


if __name__ == "__main__":
    main()
