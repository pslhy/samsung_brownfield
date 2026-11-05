#!/usr/bin/env python3
"""
report: HTML pages for the lab results (out/html/*.html), so results are read in a browser
instead of a terminal dump. Everything is inline (no network needed).

Library use (from impact.py, reverify.py ...):
    import report
    html = report.page(title, lead, body, verdict=..., facts=..., command=...)
    report.write("impact-req2-ai", title, html, status)

CLI: one page made of several result sections
    report.py --out NAME --title T [--lead TEXT] [--command CMD]
              --sec KIND LABEL PATH EXPECT [--sec ...]
  KIND   tests | trace | difftest | hubdiff | dafny | ingest | srcdiff (PATH = a|b) | text
  EXPECT pass | fail | -     (what the lab expects: shown as "예상대로" / "예상과 다름")
"""
import argparse
import datetime
import difflib
import html as H
import json
import os
import re
import shutil
import subprocess
import sys

OUTDIR = os.environ.get("HH_HTML", "out/html")

CSS = r"""
:root{
  --paper:#FBFCFD; --sheet:#FFFFFF; --ink:#18212B; --muted:#5B6773; --rule:#D9DFE6; --rule2:#EEF1F4;
  --accent:#1F5F8B; --accent-tint:#E9F1F7;
  --same:#2D7A4C; --same-tint:#E7F3EB;
  --diff:#B83227; --diff-tint:#FCEBE9;
  --chg:#9A6512; --chg-tint:#FFF3D9;
  --code:#F4F6F8;
  --sans:"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",system-ui,sans-serif;
  --mono:"D2Coding","JetBrains Mono","SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root{
    --paper:#11161C; --sheet:#171E26; --ink:#E4E9EE; --muted:#9AA6B2; --rule:#2C3743; --rule2:#212A34;
    --accent:#7DB4DD; --accent-tint:#1B2B39;
    --same:#6CC08F; --same-tint:#17291F;
    --diff:#F08A7E; --diff-tint:#36191A;
    --chg:#E2B259; --chg-tint:#33270F;
    --code:#1C242D;
  }
}
*{box-sizing:border-box}
html{background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.6;
  -webkit-text-size-adjust:100%}
body{margin:0}
a{color:var(--accent)}
.wrap{max-width:1180px;margin:0 auto;padding:28px 24px 80px}
.top{display:flex;justify-content:space-between;gap:16px;align-items:baseline;border-bottom:2px solid var(--ink);
  padding-bottom:10px;margin-bottom:22px;font-size:13px;color:var(--muted)}
.top a{color:var(--muted);text-decoration:none}
.top a:hover{color:var(--accent)}
h1{font-size:28px;line-height:1.3;margin:0 0 6px;font-weight:700;letter-spacing:-.01em}
.lead{max-width:72ch;color:var(--muted);margin:0 0 20px}
.verdict{border-left:6px solid var(--accent);background:var(--sheet);padding:16px 20px;margin:0 0 18px;
  font-size:21px;line-height:1.45;font-weight:600;max-width:900px}
.verdict.ok{border-color:var(--same)} .verdict.bad{border-color:var(--diff)} .verdict.warn{border-color:var(--chg)}
.verdict .num{font-variant-numeric:tabular-nums}
.facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:0;margin:0 0 26px;
  border-top:1px solid var(--rule);border-left:1px solid var(--rule)}
.facts div{border-right:1px solid var(--rule);border-bottom:1px solid var(--rule);padding:10px 14px;background:var(--sheet)}
.facts b{display:block;font-size:22px;font-variant-numeric:tabular-nums;line-height:1.2}
.facts span{font-size:13px;color:var(--muted)}
.cmd{font-family:var(--mono);font-size:13px;background:var(--code);border:1px solid var(--rule);padding:6px 10px;
  display:inline-block;border-radius:3px;margin:0 0 20px;color:var(--muted)}
nav.toc{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:14px;margin:0 0 28px;padding:10px 0;
  border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
nav.toc a{text-decoration:none}
section{margin:0 0 40px}
h2{font-size:20px;margin:0 0 4px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
h3{font-size:16px;margin:22px 0 6px}
.sub{color:var(--muted);margin:0 0 14px;max-width:80ch;font-size:14px}
.badge{display:inline-block;font-size:12.5px;font-weight:600;padding:1px 8px;border-radius:999px;border:1px solid;
  white-space:nowrap}
.b-ok{color:var(--same);border-color:var(--same);background:var(--same-tint)}
.b-bad{color:var(--diff);border-color:var(--diff);background:var(--diff-tint)}
.b-warn{color:var(--chg);border-color:var(--chg);background:var(--chg-tint)}
.b-info{color:var(--accent);border-color:var(--accent);background:var(--accent-tint)}
.b-mute{color:var(--muted);border-color:var(--rule);background:transparent}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--sheet)}
th,td{text-align:left;vertical-align:top;padding:6px 10px;border-bottom:1px solid var(--rule2)}
th{font-size:13px;color:var(--muted);font-weight:600;border-bottom:1px solid var(--rule)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr.bad td{background:var(--diff-tint)}
table.state td{border-bottom:0;padding:3px 10px}
tr.chg td{background:var(--chg-tint)}
code,.mono{font-family:var(--mono);font-size:13px}
.box{background:var(--sheet);border:1px solid var(--rule);padding:14px 16px}
.scroll{overflow-x:auto}
/* source / diff */
.src{font-family:var(--mono);font-size:12.8px;line-height:1.55;border:1px solid var(--rule);background:var(--sheet);
  overflow-x:auto;margin:0 0 14px}
.src .split table{min-width:100%}
.src .fh{font-family:var(--sans);font-size:13px;color:var(--muted);padding:6px 10px;border-bottom:1px solid var(--rule);
  background:var(--code);display:flex;justify-content:space-between;gap:10px}
.src table{background:transparent;font-size:inherit}
.src td{padding:0 10px;border:0;white-space:pre}
.src td.ln{color:var(--muted);text-align:right;user-select:none;width:1%;padding-right:8px;opacity:.75}
.src tr.del td{background:var(--diff-tint)} .src tr.add td{background:var(--same-tint)}
.src tr.mark td{background:var(--chg-tint)}
.src tr.gap td{color:var(--muted);text-align:center;font-family:var(--sans);font-size:12px;background:var(--code)}
.src .split{display:grid;grid-template-columns:1fr 1fr}
.src .split>div{min-width:0;overflow-x:auto}
.src .split>div+div{border-left:1px solid var(--rule)}
.src .side{font-family:var(--sans);font-size:12px;color:var(--muted);padding:3px 10px;border-bottom:1px solid var(--rule2)}
ins.w{background:var(--same-tint);color:var(--same);text-decoration:none;font-weight:600}
del.w{background:var(--diff-tint);color:var(--diff);text-decoration:none;font-weight:600}
/* chains */
.chain{list-style:none;margin:6px 0 10px;padding:0 0 0 2px}
.chain li{position:relative;padding:3px 0 3px 22px;font-size:14px}
.chain li::before{content:"";position:absolute;left:6px;top:0;bottom:0;border-left:2px solid var(--rule)}
.chain li::after{content:"";position:absolute;left:2px;top:12px;width:10px;height:10px;border-radius:50%;
  background:var(--sheet);border:2px solid var(--accent)}
.chain li.src-line::after{background:var(--chg);border-color:var(--chg)}
.chain li:first-child::before{top:12px} .chain li:last-child::before{bottom:calc(100% - 12px)}
.chain li:last-child::after{background:var(--accent)}
.chain{background:var(--sheet);border:1px solid var(--rule2);padding:8px 12px 8px 10px;max-width:900px}
.chain .via{color:var(--muted);font-size:13px}
details{border-bottom:1px solid var(--rule2)}
details>summary{cursor:pointer;padding:6px 4px;list-style:none;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"+";font-family:var(--mono);color:var(--muted);width:12px}
details[open]>summary::before{content:"−"}
details>div{padding:4px 4px 12px 26px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-family:var(--mono);font-size:12.5px;padding:2px 8px;border:1px solid var(--rule);border-radius:3px;background:var(--sheet)}
.chip.on{border-color:var(--accent);background:var(--accent-tint)}
.chip.off{color:var(--muted);opacity:.7}
.bar{height:8px;background:var(--rule2);border-radius:4px;overflow:hidden;min-width:80px}
.bar>i{display:block;height:100%;background:var(--accent)}
.bar.alt>i{background:var(--chg)}
.filter{font:inherit;font-size:14px;padding:6px 10px;border:1px solid var(--rule);background:var(--sheet);color:var(--ink);
  width:min(360px,100%);margin:0 0 10px;border-radius:3px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.grid3 .chip{font-size:11.5px}
@media (max-width:980px){.grid3{grid-template-columns:1fr}}
@media (max-width:760px){.grid2,.src .split{grid-template-columns:1fr}.verdict{font-size:18px}h1{font-size:23px}}
.steps td.op{font-family:var(--mono);white-space:nowrap}
.note{font-size:13px;color:var(--muted)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
"""

JS = r"""
document.querySelectorAll('input.filter').forEach(function(inp){
  inp.addEventListener('input',function(){
    var q=inp.value.toLowerCase(), box=document.getElementById(inp.dataset.target);
    box.querySelectorAll('[data-k]').forEach(function(el){
      el.style.display = el.dataset.k.toLowerCase().indexOf(q)>=0 ? '' : 'none';});
  });
});
"""


def e(s):
    return H.escape(str(s), quote=True)


def badge(text, tone="info"):
    return '<span class="badge b-%s">%s</span>' % (tone, e(text))


OKWORD = {"tests": ("모두 통과", "실패 있음"), "dafny": ("검증 통과", "검증 실패"), "difftest": ("일치", "불일치"),
          "trace": ("같음", "다름"), "hubdiff": ("같음", "다름")}


def expect_badge(ok, expect, kind=""):
    """ok: result matched 'pass'; expect: 'pass'|'fail'|'-'"""
    w = OKWORD.get(kind, ("통과", "실패"))
    res = badge(w[0] if ok else w[1], "ok" if ok else "bad")
    if expect in ("pass", "fail"):
        good = (ok and expect == "pass") or (not ok and expect == "fail")
        res += " " + badge("예상대로" if good else "예상과 다름", "mute" if good else "warn")
    return res


def facts(items):
    return '<div class="facts">%s</div>' % "".join(
        "<div><b>%s</b><span>%s</span></div>" % (e(v), e(k)) for k, v in items)


def table(head, rows, cls="", numeric=()):
    th = "".join('<th class="%s">%s</th>' % ("n" if i in numeric else "", e(h)) for i, h in enumerate(head))
    out = []
    for r in rows:
        rc = ""
        if isinstance(r, tuple) and len(r) == 2 and isinstance(r[1], str) and isinstance(r[0], list):
            r, rc = r
        out.append('<tr class="%s">%s</tr>' % (rc, "".join(
            '<td class="%s">%s</td>' % ("n" if i in numeric else "", c) for i, c in enumerate(r))))
    return '<div class="scroll"><table class="%s"><tr>%s</tr>%s</table></div>' % (cls, th, "".join(out))


def word_diff(a, b):
    sa, sb = re.split(r"(\s+|[,\[\]=|{}()])", a), re.split(r"(\s+|[,\[\]=|{}()])", b)
    oa, ob = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, sa, sb, autojunk=False).get_opcodes():
        A, B = e("".join(sa[i1:i2])), e("".join(sb[j1:j2]))
        if tag == "equal":
            oa.append(A); ob.append(B)
        else:
            if A:
                oa.append('<del class="w">%s</del>' % A)
            if B:
                ob.append('<ins class="w">%s</ins>' % B)
    return "".join(oa), "".join(ob)


def source_block(title, lines, marks, context=3, right=""):
    """lines: list of str (1-based numbering); marks: {lineno: 'mark'|'add'|'del'}"""
    keep = set()
    for ln in marks:
        keep |= set(range(max(1, ln - context), min(len(lines), ln + context) + 1))
    rows, last = [], 0
    for ln in sorted(keep):
        if last and ln > last + 1:
            rows.append('<tr class="gap"><td></td><td>⋯ %d줄 생략</td></tr>' % (ln - last - 1))
        rows.append('<tr class="%s"><td class="ln">%d</td><td>%s</td></tr>' % (marks.get(ln, ""), ln, e(lines[ln - 1])))
        last = ln
    return '<div class="src"><div class="fh"><span>%s</span><span>%s</span></div><table>%s</table></div>' % (
        e(title), right, "".join(rows))


def split_diff(title, a_lines, b_lines, a_label="변경 전", b_label="변경 후", context=3):
    """side-by-side diff of two files, only hunks with context"""
    sm = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    left, right = [], []
    for grp in sm.get_grouped_opcodes(context):
        if left:
            left.append('<tr class="gap"><td></td><td>⋯</td></tr>')
            right.append('<tr class="gap"><td></td><td>⋯</td></tr>')
        for tag, i1, i2, j1, j2 in grp:
            if tag == "equal":
                for k in range(i2 - i1):
                    left.append('<tr><td class="ln">%d</td><td>%s</td></tr>' % (i1 + k + 1, e(a_lines[i1 + k])))
                    right.append('<tr><td class="ln">%d</td><td>%s</td></tr>' % (j1 + k + 1, e(b_lines[j1 + k])))
                continue
            n = max(i2 - i1, j2 - j1)
            for k in range(n):
                if i1 + k < i2:
                    left.append('<tr class="del"><td class="ln">%d</td><td>%s</td></tr>' % (i1 + k + 1, e(a_lines[i1 + k])))
                else:
                    left.append('<tr><td class="ln">&nbsp;</td><td>&nbsp;</td></tr>')
                if j1 + k < j2:
                    right.append('<tr class="add"><td class="ln">%d</td><td>%s</td></tr>' % (j1 + k + 1, e(b_lines[j1 + k])))
                else:
                    right.append('<tr><td class="ln">&nbsp;</td><td>&nbsp;</td></tr>')
    if not left:
        return ""
    return ('<div class="src"><div class="fh"><span>%s</span></div><div class="split">'
            '<div><div class="side">%s</div><table>%s</table></div>'
            '<div><div class="side">%s</div><table>%s</table></div></div></div>') % (
        e(title), e(a_label), "".join(left), e(b_label), "".join(right))


def page(title, lead, body, verdict=None, facts_items=None, command=None, toc=None):
    v = ""
    if verdict:
        text, tone = verdict
        v = '<div class="verdict %s">%s</div>' % (tone, text)
    f = facts(facts_items) if facts_items else ""
    c = '<div class="cmd">$ %s</div>' % e(command) if command else ""
    t = ""
    if toc:
        t = '<nav class="toc">%s</nav>' % "".join('<a href="#%s">%s</a>' % (a, e(b)) for a, b in toc)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'><title>%s</title><style>%s</style></head>"
            "<body><div class='wrap'><div class='top'><a href='index.html'>HomeHub 실습 결과</a><span>%s</span></div>"
            "<h1>%s</h1><p class='lead'>%s</p>%s%s%s%s%s</div><script>%s</script></body></html>") % (
        e(title), CSS, now, e(title), lead, v, f, c, t, body, JS)


def write(name, title, html_text, status="info", summary=""):
    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, name + ".html")
    with open(path, "w") as f:
        f.write(html_text)
    idx_path = os.path.join(OUTDIR, "_index.json")
    try:
        idx = json.load(open(idx_path))
    except Exception:
        idx = {}
    idx[name] = {"title": title, "status": status, "summary": summary,
                 "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    json.dump(idx, open(idx_path, "w"), ensure_ascii=False, indent=1)
    write_index(idx)
    print("→ 보고서: %s" % path + (("   (" + summary + ")") if summary else ""), file=sys.stderr)
    maybe_open(path)
    return path


GROUPS = [("준비", ("test", "verify-all")),
          ("실습 A0. 구조 파악", ("path", "state", "config-")),
          ("실습 A. 변경 영향", ("trace", "ingest", "impact-", "show-", "test-a3-")),
          ("실습 B. Dafny 모델과 차분 테스트", ("verify", "difftest")),
          ("실습 C. 변경 요청 1", ("req1", "test-req1-")),
          ("실습 D. 재검증 범위", ("reverify-",)),
          ("실습 E. 정리 규칙", ("rewrite-", "rules")),
          ("그 밖의 결과", ("",))]


def group_of(name):
    best, title_ = -1, GROUPS[-1][0]
    for title, prefixes in GROUPS:
        for p in prefixes:
            if p and (name == p or name.startswith(p if p.endswith("-") else p + "-")) and len(p) > best:
                best, title_ = len(p), title
    return title_


def write_index(idx):
    groups = {}
    for name, m in idx.items():
        groups.setdefault(group_of(name), []).append((name, m))
    body = []
    for title, _ in GROUPS:
        items = sorted(groups.get(title, []), key=lambda x: x[0])
        if not items:
            continue
        rows = []
        for name, m in items:
            tone = {"ok": "ok", "bad": "bad", "warn": "warn"}.get(m["status"], "info")
            rows.append(['<a href="%s.html">%s</a>' % (e(name), e(m["title"])), e(m.get("summary", "")),
                         badge({"ok": "통과", "bad": "문제 있음", "warn": "예상과 다름"}.get(m["status"], "보기"), tone),
                         '<span class="note" style="white-space:nowrap">%s</span>' % e(m["time"][5:])])
        body.append("<section><h2>%s</h2>%s</section>" % (e(title), table(["보고서", "요약", "상태", "만든 시각"], rows)))
    html_text = page("HomeHub 실습 결과", "make 명령을 실행할 때마다 결과 보고서가 여기에 모입니다. 실습 순서대로 묶었습니다.", "".join(body))
    with open(os.path.join(OUTDIR, "index.html"), "w") as f:
        f.write(html_text)


def maybe_open(path):
    if os.environ.get("HH_OPEN", "1") != "1":
        return
    for cmd in ("open", "xdg-open", "wslview"):
        if shutil.which(cmd):
            try:
                subprocess.Popen([cmd, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            return


# ---------------------------------------------------------------- section renderers
# each returns (html, ok, one-line summary)

def sec_tests(path):
    txt = open(path).read() if os.path.exists(path) else ""
    m = re.search(r"tests: (\d+), passed: (\d+), failed: (\d+)", txt)
    if not m:
        return '<pre class="box">%s</pre>' % e(txt), False, "실행 실패"
    total, passed, failed = map(int, m.groups())
    fails = [l[5:] for l in txt.splitlines() if l.startswith("FAIL ")]
    body = facts([("테스트", total), ("통과", passed), ("실패", failed)])
    if fails:
        body += table(["실패한 테스트", "이유"], [([e(f.split(":", 1)[0]), "<code>%s</code>" % e(f.split(":", 1)[1])], "bad")
                                            for f in fails])
    return body, failed == 0, "테스트 %d/%d 통과" % (passed, total)


STATE_RE = re.compile(r"^(\d+) (.*?) \| q=(\S+) dev=(\S*) power=(\S+) metrics=\{(.*?)\} audit=\[(.*)\]$")


def parse_state(line):
    m = STATE_RE.match(line or "")
    if not m:
        return None
    n, res, q, dev, power, metrics, audit = m.groups()
    return {"n": int(n), "결과": res, "대기열": q, "전력": power,
            "dev": dict(x.split(":", 1) for x in dev.split(",") if ":" in x),
            "dev_order": [x.split(":", 1)[0] for x in dev.split(",") if ":" in x],
            "metrics": dict(x.split("=", 1) for x in metrics.split(",") if "=" in x),
            "audit": [x.strip() for x in audit.split(", ") if x.strip()]}


def state_diff(a, b):
    """[(item, before, after)] for two trace lines; None if they cannot be parsed"""
    A, B = parse_state(a), parse_state(b)
    if A is None or B is None:
        return None
    out = []
    for k in ("결과", "대기열"):
        if A[k] != B[k]:
            out.append((k if k != "대기열" else "대기열 (개수[번호])", A[k], B[k]))
    for d in sorted(set(A["dev"]) | set(B["dev"])):
        if A["dev"].get(d) != B["dev"].get(d):
            out.append(("기기 " + d, A["dev"].get(d, "-"), B["dev"].get(d, "-")))
    if A["dev_order"] != B["dev_order"] and sorted(A["dev_order"]) == sorted(B["dev_order"]):
        out.append(("기기 목록 순서", " → ".join(A["dev_order"]), " → ".join(B["dev_order"])))
    if A["전력"] != B["전력"]:
        out.append(("전력 (사용/상한)", A["전력"], B["전력"]))
    gone = [x for x in A["audit"] if x not in B["audit"]]
    new = [x for x in B["audit"] if x not in A["audit"]]
    if gone or new:
        out.append(("감사 로그", ", ".join(gone) or "-", ", ".join(new) or "-"))
    ks = [k for k in sorted(set(A["metrics"]) | set(B["metrics"])) if A["metrics"].get(k) != B["metrics"].get(k)]
    if ks:
        out.append(("지표 %d개" % len(ks), ", ".join("%s=%s" % (k, A["metrics"].get(k, "없음")) for k in ks),
                    ", ".join("%s=%s" % (k, B["metrics"].get(k, "없음")) for k in ks)))
    return out


def state_rows(pairs, workload, a_label, b_label):
    """pairs: [(a_line, b_line)] -> table html showing only what differs, one row per item"""
    rows = []
    for a, b in pairs:
        n = parse_state(a or b)
        src = ""
        if n and workload and 0 < n["n"] <= len(workload):
            src = "<span class='via'>%d줄</span><br><code>%s</code>" % (n["n"], e(workload[n["n"] - 1]))
        d = state_diff(a, b)
        if not d:   # cannot parse, or items look equal but the lines differ: compare the whole line
            da, db = word_diff(a, b)
            d = [("(줄 전체)", None, None)]
            cells = [('<span class="mono">%s</span>' % da, '<span class="mono">%s</span>' % db)]
        else:
            cells = [('<del class="w">%s</del>' % e(x), '<ins class="w">%s</ins>' % e(y)) for _, x, y in d]
        for i, ((k, _, _), (x, y)) in enumerate(zip(d, cells)):
            first = '<td rowspan="%d" style="border-bottom:1px solid var(--rule)">%s</td>' % (len(d), src) if i == 0 else ""
            last = ' style="border-bottom:1px solid var(--rule)"' if i == len(d) - 1 else ""
            rows.append("<tr>%s<td%s>%s</td><td class='mono'%s>%s</td><td class='mono'%s>%s</td></tr>" % (
                first, last, e(k), last, x, last, y))
    return ('<div class="scroll"><table class="state"><tr><th style="width:26%%">입력 줄</th><th style="width:22%%">달라진 항목</th>'
            '<th>%s</th><th>%s</th></tr>%s</table></div>') % (e(a_label), e(b_label), "".join(rows))


def sec_trace(path):
    d = json.load(open(path))
    parts, ok_all = [], True
    for w in d["workloads"]:
        if w["same"]:
            parts.append('<h3>%s %s</h3><p class="note">%d줄, 기록과 같음</p>' % (e(w["name"]), badge("같음", "ok"), w["lines"]))
            continue
        ok_all = False
        pairs = [(a, b) for (n, a, b) in w["diffs"][:15]]
        more = len(w["diffs"]) - 15
        parts.append('<h3>%s %s</h3><p class="note">%d줄 중 %d줄 다름. 줄마다 달라진 항목만 보여 줍니다.</p>%s%s' % (
            e(w["name"]), badge("다름", "bad"), w["lines"], len(w["diffs"]),
            state_rows(pairs, w.get("workload"), "기록(golden)", "이번 실행"),
            '<p class="note">… %d줄 더 다름</p>' % more if more > 0 else ""))
    nd = sum(1 for w in d["workloads"] if not w["same"])
    return "".join(parts), ok_all, ("기록 %d개 모두 같음" % len(d["workloads"])) if ok_all else ("기록 %d개 중 %d개 다름" % (len(d["workloads"]), nd))


def sec_difftest(path):
    d = json.load(open(path))
    parts, ok_all, summ = [], True, []
    for s in d["subjects"]:
        if s["ok"]:
            parts.append('<h3>%s %s</h3><p class="note">무작위 연산열 %d개(연산 %d개)를 Java와 모델에 똑같이 넣고 매 단계 비교: 모두 같음</p>'
                         % (e(s["name"]), badge("일치", "ok"), s["runs"], s["ops"]))
            summ.append("%s 일치" % s["name"])
            continue
        ok_all = False
        summ.append("%s 불일치(%d단계)" % (s["name"], len(s["minimal"])))
        rows = []
        steps = s.get("steps", [])
        STATE = ("contents", "totalLoad")
        AUX = ("size", "isEmpty", "capacity", "dispatchedCount", "headroom", "isIdle")
        for st in steps:
            cs = st["checks"]
            ret = next((c for c in cs if c["what"] not in STATE + AUX), None)
            stt = next((c for c in cs if c["what"] in STATE), None)
            bad = [c for c in cs if not c["ok"]]

            def cell(c):
                if c is None:
                    return "", ""
                if c["ok"]:
                    return '<span class="mono">%s</span>' % e(c["java"]), '<span class="mono">%s</span>' % e(c["model"])
                a_, b_ = word_diff(c["java"], c["model"])
                return '<span class="mono">%s</span>' % a_, '<span class="mono">%s</span>' % b_
            rj, rm = cell(ret)
            sj, sm = cell(stt)
            extra = "".join('<div class="note">%s: java <code>%s</code>, 모델 <code>%s</code></div>' % (e(c["what"]), e(c["java"]), e(c["model"]))
                            for c in bad if c is not ret and c is not stt)
            rows.append(([str(st["i"] + 1), '<span class="mono">%s</span>' % e(st["op"]), rj, rm, sj, sm + extra,
                          badge("다름", "bad") if bad else ""], "bad" if bad else ""))
        what = "총부하" if any(c["what"] == "totalLoad" for st in steps for c in st["checks"]) else "대기열 내용"
        head = ["단계", "연산", "Java 결과", "모델 결과", "Java " + what, "모델 " + what, ""]
        parts.append('<h3>%s %s</h3><p class="note">처음 불일치가 난 연산열을 줄여서, 같은 불일치가 나는 가장 짧은 연산열 %d개를 남겼습니다 '
                     '(run %s, seed %s). 이 연산열을 그대로 회귀 테스트로 옮길 수 있습니다.</p>%s' % (
                         e(s["name"]), badge("불일치", "bad"), len(s["minimal"]), s["run"], s["seed"],
                         table(head, rows, cls="steps")))
    if not ok_all:
        parts.append('<p class="note">연산 읽는 법: <code>offer(7,0)</code> 번호 7인 비중요 이벤트 넣기(1이면 중요), <code>poll</code> 하나 꺼내기, '
                     '<code>submit(5,1)</code> 번호 5인 중요 이벤트 제출, <code>tryStart(1,2200)</code> 기기 1을 2200W로 켜기. '
                     '매 연산 뒤에 크기·비었는지·용량 같은 값도 비교하며, 다를 때만 따로 표시합니다.</p>')
    return "".join(parts), ok_all, ", ".join(summ)


def sec_hubdiff(path):
    d = json.load(open(path))
    if d["ok"]:
        return ('<p>무작위 입력 파일 %d개(각 %d줄)를 두 빌드에 넣었더니 상태 기록이 모두 같았습니다.</p>' % (d["runs"], d["len"]),
                True, "무작위 입력 %d개 모두 같음" % d["runs"])
    pairs = [(d["base"][i] if i < len(d["base"]) else "", d["changed"][i] if i < len(d["changed"]) else "")
             for i in range(max(len(d["base"]), len(d["changed"])))]
    wl_html = "".join("<div><span class='via'>%d</span> <code>%s</code></div>" % (i + 1, e(x)) for i, x in enumerate(d["workload"]))
    body = ('<p>무작위 입력 파일로 두 빌드를 비교하다 다른 결과가 나왔습니다. 같은 차이가 나는 가장 짧은 입력 %d줄로 줄였습니다 '
            '(<code>%s</code>에 저장). 이 입력을 기록용 입력 파일에 추가하면 회귀 테스트가 됩니다.</p>'
            '<div class="box" style="margin-bottom:12px"><b>줄인 입력</b>%s</div>%s') % (
        len(d["workload"]), e(d["keep"]), wl_html, state_rows(pairs, d["workload"], "기존 빌드", "바뀐 빌드"))
    return body, False, "무작위 비교 불일치(%d줄 입력)" % len(d["workload"])


GLOSS = [("postcondition could not be proved", "사후조건(ensures)을 증명하지 못함"),
         ("this is the postcondition that could not be proved", "증명하지 못한 사후조건"),
         ("this proposition could not be proved", "이 부분이 성립함을 보이지 못함"),
         ("precondition for this call could not be proved", "이 호출의 사전조건(requires)을 증명하지 못함"),
         ("insufficient reads clause", "읽을 수 있다고 선언하지 않은 것(reads)을 읽음"),
         ("modifies clause", "바꿀 수 있다고 선언하지 않은 것(modifies)을 바꿀 수 있음"),
         ("invariant could not be proved to be maintained", "반복 후에도 루프 불변식이 성립함을 증명하지 못함"),
         ("invariant could not be proved on entry", "루프에 들어갈 때 불변식을 증명하지 못함"),
         ("out of range", "인덱스가 범위를 벗어날 수 있음"),
         ("newtype constraint", "계산 결과가 정수 타입의 범위를 넘을 수 있음(넘침)"),
         ("timed out", "시간 초과: 증명기가 제한 시간 안에 끝내지 못함"),
         ("assertion might not hold", "assert를 증명하지 못함"),
         ("decreases", "종료를 증명하지 못함")]


def gloss(msg):
    for k, v in GLOSS:
        if k in msg:
            return '%s <span class="note">(%s)</span>' % (e(v), e(msg))
    return e(msg)


def sec_dafny(path):
    d = json.load(open(path))
    errs = d["errors"]
    ok = d["errors_count"] == 0 and d["verified"] is not None
    head = facts([("검증된 항목", d["verified"] if d["verified"] is not None else "?"),
                  ("오류", d["errors_count"])])
    if not errs:
        return head + ('<p class="note">%s</p>' % e(d["summary"]) if d["summary"] else ""), ok, d["summary"]
    groups = {}
    for er in errs:
        groups.setdefault((er["file"], er["line"]), []).append(er)
    parts = []
    for (f, ln), ers in sorted(groups.items()):
        lines = open(f).read().splitlines() if os.path.exists(f) else []
        marks = {ln: "del"}
        for er in ers:
            for r in er.get("related", []):
                if r["file"] == f:
                    marks.setdefault(r["line"], "mark")
        msgs = "".join("<li>%s</li>" % gloss(er["msg"]) for er in ers)
        rel = []
        for er in ers:
            for r in er.get("related", []):
                rel.append("%d번 줄: %s" % (r["line"], {"this is the postcondition that could not be proved": "증명하지 못한 사후조건",
                    "this proposition could not be proved": "성립함을 보이지 못한 부분"}.get(r["msg"], r["msg"])))
        parts.append('<div class="box" style="margin-bottom:12px"><b>%s:%d</b>%s<ul>%s</ul>%s%s</div>' % (
            e(os.path.basename(f)), ln, " ×%d" % len(ers) if len(ers) > 1 else "", msgs,
            source_block(f, lines, marks, context=2) if lines else "",
            ('<p class="note">관련 위치(노란 줄): %s</p>' % e("; ".join(sorted(set(rel))))) if rel else ""))
    return head + "".join(parts), ok, "오류 %d개" % d["errors_count"]


def sec_srcdiff(path):
    """PATH = 'baseRoot|changedRoot': side-by-side diff of every .java file that differs"""
    a_root, b_root = path.split("|")
    files = set()
    for root in (a_root, b_root):
        for dp, _, fs in os.walk(root):
            for f in fs:
                if f.endswith(".java"):
                    files.add(os.path.relpath(os.path.join(dp, f), root))
    parts, n = [], 0
    for rel in sorted(files):
        pa, pb = os.path.join(a_root, rel), os.path.join(b_root, rel)
        la = open(pa).read().splitlines() if os.path.exists(pa) else []
        lb = open(pb).read().splitlines() if os.path.exists(pb) else []
        if la == lb:
            continue
        n += 1
        name = rel.replace("src/main/java/com/dxlab/homehub/", "").replace("src/test/java/com/dxlab/homehub/", "테스트 ")
        parts.append(split_diff(name, la, lb, "변경 전" if la else "(없던 파일)", "변경 후" if lb else "(지운 파일)"))
    if not parts:
        return '<p class="note">바뀐 파일이 없습니다.</p>', True, "바뀐 파일 없음"
    return ('<p class="note">빨간 줄: 지운 줄, 초록 줄: 새로 쓴 줄. 바뀐 곳 앞뒤 3줄만 보여 줍니다.</p>' + "".join(parts),
            True, "파일 %d개 바뀜" % n)


def sec_text(path):
    txt = open(path).read() if os.path.exists(path) else ""
    return '<pre class="box" style="white-space:pre-wrap">%s</pre>' % e(txt), True, ""


def sec_ingest(path):
    """one message through HomeHub: the message's fields, result, what changed, the lines executed"""
    d = json.load(open(path))
    out = d["output"].splitlines()
    before = next((l[7:] for l in out if l.startswith("BEFORE ")), "")
    after = next((l[6:] for l in out if l.startswith("AFTER ")), "")
    result = next((l[7:] for l in out if l.startswith("RESULT ")), "?")
    src_root = d.get("src", "legacy/src/main/java")
    msg = next((l[8:] for l in out if l.startswith("MESSAGE ")), "")
    f = msg.split("|")
    names = ["번호(seq)", "기기", "종류 코드", "값", "시각(ms)", "속성(이름=값;...)"]
    head = names
    cells = [("<code>%s</code>" % e(f[i])) if i < len(f) else "<span class='via'>(없음)</span>" for i in range(len(head))]
    parts = ["<h3>넣은 메시지</h3><p><code>%s</code></p>%s" % (e(msg), table(head, [cells]))]
    tone = {"ACCEPTED": "ok", "INVALID": "warn"}.get(result, "info")
    parts.append("<h3>결과 %s</h3>" % badge(result, tone))
    diff = state_diff(before, after) or []
    if diff:
        parts.append(table(["달라진 항목", "넣기 전", "넣은 뒤"],
                           [["%s" % e(k), "<span class='mono'>%s</span>" % e(x), "<span class='mono'>%s</span>" % e(y)] for k, x, y in diff]))
    else:
        parts.append('<p class="note">상태 변화 없음</p>')
    # executed lines, grouped by method, with exceptions marked
    steps = d["steps"]
    exc_at = {}
    catch_at = {}
    for x in d["exceptions"]:
        exc_at[(x["cls"], x["line"])] = x["type"].split(".")[-1]
        if x["catch_cls"]:
            catch_at[(x["catch_cls"], x["catch_line"])] = x["type"].split(".")[-1]
    cache = {}

    def text(cls, ln):
        top = cls.split("$")[0]
        p = os.path.join(src_root, *top.split(".")) + ".java"
        if p not in cache:
            cache[p] = open(p).read().splitlines() if os.path.exists(p) else []
        ls = cache[p]
        return ls[ln - 1] if 0 < ln <= len(ls) else ""
    rows, prev, prev_m, shown = [], None, None, 0
    for cls, meth, ln in steps:
        if (cls, ln) == prev:
            continue
        prev = (cls, ln)
        if shown >= 120:
            rows.append('<tr class="gap"><td colspan="2">… %d줄 더</td></tr>' % (len(steps) - shown))
            break
        shown += 1
        if (cls, meth) != prev_m:
            prev_m = (cls, meth)
            rows.append('<tr class="gap"><td colspan="2" style="text-align:left">%s#%s</td></tr>' % (
                e(cls.replace("com.dxlab.homehub.", "")), e(meth)))
        note, cl = "", ""
        if (cls, ln) in exc_at:
            note, cl = "   ← 여기서 %s 발생" % exc_at[(cls, ln)], "del"
        elif (cls, ln) in catch_at:
            note, cl = "   ← 여기서 %s를 잡음" % catch_at[(cls, ln)], "mark"
        rows.append('<tr class="%s"><td class="ln">%d</td><td>%s<b>%s</b></td></tr>' % (cl, ln, e(text(cls, ln)), e(note)))
    parts.append("<h3>실행된 코드 줄 (위에서 아래로 실행 순서)</h3><div class='src'><table>%s</table></div>" % "".join(rows))
    return "".join(parts), True, "결과 %s" % result


SECTIONS = {"tests": sec_tests, "trace": sec_trace, "difftest": sec_difftest, "hubdiff": sec_hubdiff,
            "dafny": sec_dafny, "text": sec_text,
            "srcdiff": sec_srcdiff, "ingest": sec_ingest}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--lead", default="")
    ap.add_argument("--command", default=None)
    ap.add_argument("--sec", nargs=4, action="append", default=[], metavar=("KIND", "LABEL", "PATH", "EXPECT"))
    a = ap.parse_args()
    body, toc, as_expected, summary, statuses = [], [], True, [], []
    for i, (kind, label, path, expect) in enumerate(a.sec):
        try:
            h, ok, s = SECTIONS[kind](path)
        except Exception as ex:          # a missing input should not hide the other sections
            h, ok, s = '<p class="note">결과 파일을 읽지 못했습니다: %s</p>' % e(ex), False, "결과 없음"
        good = expect == "-" or (ok and expect == "pass") or (not ok and expect == "fail")
        as_expected &= good
        sid = "s%d" % i
        toc.append((sid, label))
        if kind in ("srcdiff", "text", "ingest"):
            b = ""
        else:
            b = expect_badge(ok, expect, kind)
        body.append('<section id="%s"><h2>%s %s</h2>%s</section>' % (sid, e(label), b, h))
        if kind not in ("srcdiff", "text"):
            summary.append(s)
            statuses.append(ok)
    expects = [x[3] for x in a.sec if x[3] != "-"]
    if expects:
        verdict = ("모든 결과가 예상대로 나왔습니다." if as_expected else "예상과 다른 결과가 있습니다. 노란 표시를 확인하세요.",
                   "ok" if as_expected else "warn")
        status = "ok" if as_expected else "warn"
    else:
        allok = all(statuses)
        verdict = None
        status = "ok" if allok else "bad"
    html_text = page(a.title, e(a.lead), "".join(body), verdict=verdict, command=a.command,
                     toc=toc if len(toc) > 1 else None)
    if expects:
        short_s = "모두 예상대로" if as_expected else "예상과 다른 결과 있음"
    else:
        short_s = "; ".join(summary)
    write(a.out, a.title, html_text, status, short_s[:120])


if __name__ == "__main__":
    main()
