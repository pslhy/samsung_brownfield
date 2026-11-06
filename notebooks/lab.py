"""
lab: helpers for the HomeHub lab notebooks.

    import lab
    lab.run("impact", V="scenarios/req2/ai")      # runs `make impact V=...`, shows its report below
    lab.structure()                               # HomeHub structure map (docs/homehub_구조.html); lab.structure("queue")
    lab.show("legacy/src/.../Watchdog.java", 20, 35)
    lab.diff("formal/RingQueue.dfy", "scenarios/req2/model/RingQueue.dfy")
    lab.patch(path, old, new) / lab.restore(path)
    lab.prompt("P-1")                             # print a prompt to copy into an AI tool
    lab.codex("P-1", save="mine/RingEventQueue.dfy")   # or send it to Codex and keep its code
    lab.ingest("5|fridge-2|TEMP|38|60000")       # one message: result, state change, lines executed
    lab.path("4|fridge-2|TEMP|14|180000|unit=C", setup=[...])   # call graph vs the methods that ran
    lab.trace_table("fridge_firmware")            # input file and recorded trace side by side

Every visual result is a report page (tools/report.py) shown inside the notebook.
"""
import html as _html
import os
import re
import subprocess
import sys
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import report  # noqa: E402

try:
    from IPython.display import HTML, display
except ImportError:                      # used outside Jupyter
    HTML = None

    def display(x):
        print(x)


def _p(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


HTML_DIR = os.path.join(ROOT, report.OUTDIR) if not os.path.isabs(report.OUTDIR) else report.OUTDIR
_server_port = None


SERVER_PORT = 8765                      # links saved in notebook outputs point here, so keep it fixed
_ID_FILE = "_server_id.txt"              # served file that tells our server apart from anything else on the port


def _ours(port):
    """is the web server on this port serving this lab's out/html?"""
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/%s" % (port, _ID_FILE), timeout=0.5) as r:
            return r.read().decode("utf-8", "replace").strip() == ROOT
    except Exception:
        return False


def _serve():
    """a small web server (this computer only) for out/html, so "새 탭에서 열기" works where blob: tabs don't (VS Code).

    It runs as its own process, not inside the kernel, and every notebook shares it on SERVER_PORT. So links in saved
    outputs keep working across notebooks and kernel restarts: running `import lab` once is enough."""
    global _server_port
    if _server_port and _ours(_server_port):
        return _server_port
    _server_port = None
    import time
    os.makedirs(HTML_DIR, exist_ok=True)
    with open(os.path.join(HTML_DIR, _ID_FILE), "w") as f:
        f.write(ROOT)
    for port in range(SERVER_PORT, SERVER_PORT + 10):   # the next ports only if something else holds 8765
        if _ours(port):
            _server_port = port
            return port
        p = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1",
                              "--directory", HTML_DIR], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        for _ in range(30):
            time.sleep(0.1)
            if _ours(port):
                _server_port = port
                return port
            if p.poll() is not None:     # port taken by something else
                break
        else:
            p.kill()
    return None


def _page_url(page_html, link, fid):
    """http address of a copy of the shown page (out/html/_nb/<fid>.html).
    Always a copy, not the report file itself: a later run of the same target overwrites the report file, and the
    new tab must still show what this output shows."""
    port = _serve()
    if not port:
        return None
    rel = os.path.join("_nb", fid + ".html")
    os.makedirs(os.path.join(HTML_DIR, "_nb"), exist_ok=True)
    with open(os.path.join(HTML_DIR, rel), "w") as f:
        f.write(page_html)
    return "http://localhost:%d/%s" % (port, rel.replace(os.sep, "/"))


def _link_div(fid, url, link=None):
    """the "새 탭에서 열기" line under a shown page.

    Jupyter in a browser: a blob: tab made from the page shown here (works even when the Jupyter server is elsewhere).
    VS Code (and other non-browser front ends): blob: URLs can't leave the editor, so follow the link to the
    local web server instead; the editor hands http://localhost links to the default browser."""
    return ('<div style="font-size:12.5px;color:#5b6773;margin:4px 0 0">'
            '<a href="%s" target="_blank" rel="noopener" style="color:#1f5f99;font-weight:600" onclick="return (function(){'
            'var inBrowser=/^https?:$/.test(location.protocol)&&!!document.querySelector(\'.jp-OutputArea,.output_area\');'
            'if(!inBrowser){if(%s)return true;this.textContent=\'새 탭을 열 수 없습니다. 오른쪽 파일을 브라우저로 직접 여세요\';return false;}'
            'var f=document.getElementById(\'%s\');'
            'var u=window.URL.createObjectURL(new window.Blob([f.srcdoc],{type:\'text/html\'}));var w=window.open(u,\'_blank\');'
            'if(!w){this.textContent=\'새 탭을 열 수 없습니다. 오른쪽 파일을 브라우저로 직접 여세요\';}return false;}).call(this);">새 탭에서 열기 ↗</a>'
            '%s</div>') % (_html.escape(url or "#", quote=True), "true" if url else "false", fid,
                           ('&nbsp;&nbsp;<span>파일: <code>%s</code></span>' % _html.escape(os.path.relpath(link, ROOT))) if link else "")


def _frame(page_html, height=None, link=None, est=600):
    """show a full report page inside the notebook (isolated styles), sized to its content"""
    fid = "hh" + uuid.uuid4().hex[:8]
    url = _page_url(page_html, link, fid)
    max_h = height or 1400
    doc = _html.escape(page_html, quote=True)
    out = ('<iframe id="%s" srcdoc="%s" style="width:100%%;height:%dpx;border:1px solid #d9dfe6;border-radius:4px;'
           'background:#fff"></iframe>'
           '<script>(function(){var f=document.getElementById("%s");function fit(){try{var d=f.contentDocument;'
           'if(!d||!d.body)return;var h=d.body.scrollHeight;if(h>20)f.style.height=Math.min(h+12,%d)+"px";'
           'if(!f._t){f._t=1;d.addEventListener("toggle",fit,true);}}catch(e){}}'
           'f.addEventListener("load",fit);[0,100,400,1200,3000].forEach(function(t){setTimeout(fit,t);});})();</script>'
           ) % (fid, doc, min(est, max_h), fid, max_h)
    out += _link_div(fid, url, link)
    display(HTML(out) if HTML else out)


def _embed_page(path):
    """a report file, without its top bar (the notebook is the navigation)"""
    t = open(path).read()
    t = re.sub(r"<div class='top'>.*?</div>", "", t, count=1, flags=re.S)
    return t


def run(target, height=None, show_report=True, **variables):
    """run `make <target> VAR=value ...` in the lab folder, stream its output, then show its report"""
    cmd = ["make", "-s", "--no-print-directory", target] + ["%s=%s" % (k, v) for k, v in variables.items()]
    env = dict(os.environ, HH_OPEN="0")
    env.pop("JAVA_TOOL_OPTIONS", None)
    print("$ " + " ".join(cmd[0:1] + cmd[3:]))
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, bufsize=1)
    reports = []
    for line in p.stdout:
        if line.startswith(("Picked up JAVA_TOOL_OPTIONS", "make: ***", "built variant ", "built legacy")):
            continue
        m = re.match(r"→ 보고서: (\S+)", line)
        if m:
            reports.append(os.path.join(ROOT, m.group(1)))
            continue
        print(line, end="", flush=True)
    code = p.wait()
    if code != 0 and not reports:
        print("\n(명령이 실패했습니다: 종료 코드 %d. 위 메시지를 확인하세요.)" % code)
    if show_report and reports:
        _frame(_embed_page(reports[-1]), height, link=reports[-1])
    return None


def ingest(message, setup=(), height=None):
    """put one message into a fresh hub: result, state change, and the source lines it ran through.
    setup: lines run first (messages or !drain), e.g. ["2|fridge-2|PWR_ON|0|0|fw=1.4", "!drain"]"""
    path = os.path.join(ROOT, "out", "raw", "ingest-input.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for l in list(setup) + [message]:
            f.write(l + "\n")
    run("ingest", height=height)


def path(message, setup=(), height=None):
    """one message handled to the end (the queue drained): the call graph next to the methods that ran.
    setup: lines run first (messages or !drain), e.g. ["1|fridge-2|PWR_ON|0|0", "!drain"]"""
    p = os.path.join(ROOT, "out", "raw", "path-input.txt")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        for l in list(setup) + [message]:
            f.write(l + "\n")
    run("path", height=height)


def sources(root="legacy/src/main/java"):
    """every production source file, one after another, as text for a prompt (P-6)"""
    out = []
    base = _p(root)
    for dirpath, _, names in sorted(os.walk(base)):
        for n in sorted(names):
            if n.endswith(".java"):
                full = os.path.join(dirpath, n)
                out.append("// ===== %s\n%s" % (os.path.relpath(full, base), open(full).read()))
    return "\n".join(out)


def trace_table(name, start=1, end=None, height=None):
    """input file lines and the recorded trace side by side: legacy/workloads/<name>.txt + golden/<name>.trace"""
    wl = open(_p("legacy/workloads/%s.txt" % name)).read().splitlines()
    tr = {}
    for line in open(_p("golden/%s.trace" % name)).read().splitlines():
        st = report.parse_state(line)
        if st:
            tr[st["n"]] = (line, st)
    end = min(end or len(wl), len(wl))
    rows, prev = [], None
    for n in range(1, len(wl) + 1):
        hit = tr.get(n)
        if n >= start and n <= end:
            src = wl[n - 1]
            if hit is None:
                why = "주석이라 건너뜀" if src.strip().startswith("#") else "빈 줄"
                rows.append('<tr class="dim"><td class="ln">%d</td><td class="mono">%s</td><td colspan="4" class="via">%s</td></tr>'
                            % (n, report.e(src), why))
            else:
                line, st = hit
                res = st["결과"]
                tone = "ok" if res == "ACCEPTED" else ("warn" if res in ("INVALID", "REJECTED") else "info")
                changes = []
                if prev is not None:
                    for k, x, y in report.state_diff(prev, line) or []:
                        if k.startswith("결과") or k.startswith("대기열"):
                            continue
                        if k.startswith("지표"):
                            xs = dict(i.split("=", 1) for i in x.split(", ") if "=" in i)
                            ys = dict(i.split("=", 1) for i in y.split(", ") if "=" in i)
                            for mk in sorted(ys):
                                changes.append("%s %s→%s" % (mk, xs.get(mk, "0").replace("없음", "0"), ys[mk]))
                        elif k == "감사 로그":
                            if y != "-":
                                changes.append("감사 로그에 추가: %s" % y)
                        else:
                            changes.append("%s: %s → %s" % (k, x, y))
                dropped = st["metrics"].get("ingest.dropped", "0")
                rows.append('<tr><td class="ln">%d</td><td class="mono">%s</td><td>%s</td><td class="mono">%s</td>'
                            '<td class="num">%s</td><td style="font-size:12.5px">%s</td></tr>' % (
                                n, report.e(src), report.badge(res, tone), report.e(st["대기열"]), dropped,
                                "<br>".join(report.e(c) for c in changes[:6]) + (" …" if len(changes) > 6 else "")))
        if hit is not None:
            prev = hit[0]
    body = ('<div class="scroll"><table class="state"><tr><th>줄</th><th>입력 줄 (%s.txt)</th><th>처리 결과</th>'
            '<th>대기열<br>개수[번호]</th><th>버린<br>메시지<br>(누적)</th><th>앞 줄과 비교해 바뀐 것</th></tr>%s</table></div>'
            '<style>tr.dim td{color:var(--muted)} table.state th{white-space:nowrap}</style>') % (report.e(name), "".join(rows))
    _frame(_bare(body), height, est=len(rows) * 30 + 70)


STRUCTURE_PARTS = ("outside", "inside", "hub", "parser", "disp", "queue", "reg", "handlers", "rules",
                   "devices", "power", "watch", "logs", "metrics", "config")


def structure(start=None, height=1500):
    """HomeHub 구조 지도 (docs/homehub_구조.html, tools/structure_page.py가 만듦). 상자를 누르면 확대해 들어감.
    start: 처음 보여 줄 곳, e.g. lab.structure("queue") (대기열), "watch" (점검·복구), "inside" (HomeHub 안)"""
    path = _p("docs/homehub_구조.html")
    page = open(path, encoding="utf-8").read()
    if start:
        if start not in STRUCTURE_PARTS:
            raise ValueError("start는 다음 중 하나: " + ", ".join(STRUCTURE_PARTS))
        page = page.replace("<!--HH_START-->", '<script>window.HH_START="%s";</script>' % start, 1)
    _frame(page, height, link=path, est=900)


def report_page(name, height=None):
    """show a report made earlier, e.g. lab.report_page("impact-req2-ai")"""
    path = os.path.join(ROOT, "out", "html", name + ".html")
    _frame(_embed_page(path), height, link=path)


def show(path, start=1, end=None, mark=(), title=None, height=None):
    """show lines start..end of a file; `mark` = line numbers to highlight"""
    lines = open(_p(path)).read().splitlines()
    end = end or len(lines)
    marks = {ln: "mark" for ln in mark}
    rows = "".join('<tr class="%s"><td class="ln">%d</td><td>%s</td></tr>' % (marks.get(i, ""), i, report.e(lines[i - 1]))
                   for i in range(start, min(end, len(lines)) + 1))
    body = '<div class="src"><div class="fh"><span>%s</span></div><table>%s</table></div>' % (report.e(title or path), rows)
    _frame(_bare(body), height, est=int((min(end, len(lines)) - start + 1) * 20.5 + 50))


def diff(a, b, title=None, height=None):
    """side-by-side diff of two files (paths relative to the lab folder)"""
    la, lb = open(_p(a)).read().splitlines(), open(_p(b)).read().splitlines()
    body = report.split_diff(title or "%s → %s" % (a, b), la, lb) or '<p class="note">두 파일이 같습니다.</p>'
    _frame(_bare(body), height, est=body.count("<tr") // 2 * 20 + 80)


def _bare(body):
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'><style>%s body .wrap{padding:6px}</style></head>"
            "<body><div class='wrap'>%s</div></body></html>") % (report.CSS, body)


# ---------------------------------------------------------------- reading code with notes

KINDS = {   # kind -> (label, background, bar color)
    "java": ("Java 필드", "#e9f1fb", "#3b6fb6"),
    "ghost": ("증명용 변수", "#f2ebfb", "#7a4fb5"),
    "inv": ("불변식", "#e6f5ec", "#2f8a55"),
    "pre": ("사전조건", "#fdf0e1", "#c07a1c"),
    "mod": ("바꿀 수 있는 것", "#fbe9ef", "#b5476b"),
    "post": ("사후조건", "#e2f3f3", "#1f8585"),
    "body": ("본문", "#f6f7f9", "#9aa5b1"),
    "func": ("함수", "#f6f7f9", "#9aa5b1"),
    "proof": ("증명 도우미", "#ffffff", "#d5dae0"),
}


def annotate(path, groups, start=1, end=None, title=None, height=None):
    """code with colored line groups and a note beside each group.
    groups: [(first line, last line, kind, note)], kind in KINDS ("proof" lines are dimmed)"""
    lines = open(_p(path)).read().splitlines()
    end = min(end or len(lines), len(lines))
    at = {}
    for g in groups:
        for ln in range(g[0], g[1] + 1):
            at[ln] = g
    rows = []
    for ln in range(start, end + 1):
        g = at.get(ln)
        kind = g[2] if g else None
        label, bg, bar = KINDS.get(kind, ("", "transparent", "transparent"))
        dim = "opacity:.45;" if kind == "proof" else ""
        code = ('<td class="ln">%d</td><td class="code" style="background:%s;border-left:4px solid %s;%s">%s</td>'
                % (ln, bg, bar, dim, report.e(lines[ln - 1]) or "&nbsp;"))
        if g is None:
            note = '<td class="note"></td>'
        elif ln == max(g[0], start):
            span = min(g[1], end) - ln + 1
            note = ('<td class="note" rowspan="%d" style="border-left:4px solid %s;%s"><span class="tag" style="color:%s">%s</span> %s</td>'
                    % (span, bar, dim, bar, label, g[3]))
        else:
            note = ""
        rows.append("<tr>%s%s</tr>" % (code, note))
    css = ("<style>.ann{border-collapse:collapse;width:100%;font-size:12.8px}.ann td{border:0;padding:0 8px;vertical-align:top}"
           ".ann td.code{font-family:var(--mono);white-space:pre;line-height:1.6}"
           ".ann td.ln{color:var(--muted);text-align:right;width:1%;font-family:var(--mono);line-height:1.6}"
           ".ann td.note{font-family:var(--sans);font-size:13px;line-height:1.5;width:42%;padding:3px 10px;background:#fbfcfd}"
           ".ann .tag{font-weight:700;font-size:12px;margin-right:4px}</style>")
    head = '<div class="fh" style="font-size:13px;color:var(--muted);padding:4px 0">%s</div>' % report.e(title or path)
    body = css + head + '<div class="scroll"><table class="ann">%s</table></div>' % "".join(rows)
    _frame(_bare(body), height, est=int((end - start + 1) * 21 + 60))


def side_by_side(rows, title=None, height=None, headers=("Java (legacy)", "Dafny (AI 결과 예시)", "어떻게 옮겼나")):
    """rows: [((java path, first, last), (dafny path, first, last), note)] -> Java | Dafny | note"""
    def snip(spec):
        path, a, b = spec
        ls = open(_p(path)).read().splitlines()
        return "<br>".join('<span class="ln2">%d</span> %s' % (i, report.e(ls[i - 1]).replace(" ", "&nbsp;"))
                           for i in range(a, min(b, len(ls)) + 1))
    trs = []
    for j, d, note in rows:
        trs.append('<tr><td class="c">%s</td><td class="c">%s</td><td class="n">%s</td></tr>' % (snip(j), snip(d), note))
    css = ("<style>.sbs{border-collapse:collapse;width:100%}.sbs th{text-align:left;font-size:13px;padding:6px 8px;border-bottom:1px solid var(--rule)}"
           ".sbs td{vertical-align:top;border-bottom:1px solid var(--rule2);padding:6px 8px}"
           ".sbs td.c{font-family:var(--mono);font-size:12px;line-height:1.55;white-space:nowrap}"
           ".sbs td.n{font-size:13px;line-height:1.5;min-width:220px}.sbs .ln2{color:var(--muted)}</style>")
    head = '<div style="font-size:13px;color:var(--muted);padding:4px 0">%s</div>' % report.e(title or "")
    body = css + head + ('<div class="scroll"><table class="sbs"><tr><th>%s</th><th>%s</th><th>%s</th></tr>%s</table></div>'
                         % (tuple(report.e(h) for h in headers) + ("".join(trs),)))
    n = sum(max(r[0][2] - r[0][1], r[1][2] - r[1][1]) + 1 for r in rows)
    _frame(_bare(body), height, est=n * 19 + len(rows) * 14 + 70)


def queue_picture(buf, head, count, title=None, height=None):
    """draw the array, head, and the elems sequence it stands for (Valid())"""
    n = len(buf)
    elems = [buf[(head + i) % n] for i in range(count)]
    colors = ["#3b6fb6", "#2f8a55", "#c07a1c", "#7a4fb5", "#b5476b", "#1f8585", "#5b6773", "#8a6d1f"]
    slot_of = {(head + i) % n: i for i in range(count)}
    cells = []
    for k in range(n):
        i = slot_of.get(k)
        col = colors[i % len(colors)] if i is not None else "#c9d1d9"
        txt = buf[k] if i is not None else "·"
        cells.append('<div class="slot"><div class="idx">buf[%d]</div><div class="box" style="border-color:%s;color:%s">%s</div>'
                     '<div class="hd">%s</div></div>' % (k, col, col, report.e(str(txt)), "↑ head" if k == head else ""))
    es = []
    for i, x in enumerate(elems):
        col = colors[i % len(colors)]
        es.append('<div class="slot"><div class="idx">elems[%d]</div><div class="box" style="border-color:%s;color:%s">%s</div>'
                  '<div class="hd">= buf[(%d+%d) %% %d] = buf[%d]</div></div>' % (i, col, col, report.e(str(x)), head, i, n, (head + i) % n))
    css = ("<style>.row{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 14px}.slot{text-align:center;min-width:64px}"
           ".idx{font-family:var(--mono);font-size:11.5px;color:var(--muted)}.box{border:2px solid;border-radius:4px;padding:8px 0;"
           "font-family:var(--mono);font-weight:700;font-size:15px}.hd{font-family:var(--mono);font-size:11px;color:var(--muted);height:16px}"
           ".lab{font-size:13px;font-weight:600;margin-top:4px}</style>")
    body = (css + '<div style="font-size:13px;color:var(--muted)">%s</div>' % report.e(title or "") +
            '<div class="lab">실행되는 것: 배열 buf (칸 %d개), head = %d, count = %d</div><div class="row">%s</div>' % (n, head, count, "".join(cells)) +
            '<div class="lab">증명에만 쓰는 것: elems (오래된 것부터 %d개)</div><div class="row">%s</div>' % (count, "".join(es)))
    _frame(_bare(body), height, est=230)


def patch(path, old, new):
    """replace text in a file (a backup is kept for lab.restore) and show the change"""
    full = _p(path)
    text = open(full).read()
    if old not in text:
        print("바꿀 내용을 찾지 못했습니다. 이미 바꿨다면 lab.restore(%r)로 되돌린 뒤 다시 하세요." % path)
        return
    if not os.path.exists(full + ".orig"):
        open(full + ".orig", "w").write(text)
    open(full, "w").write(text.replace(old, new, 1))
    print("바꿨습니다: %s   (되돌리기: lab.restore(%r))" % (path, path))
    diff(path + ".orig", path, title=path + " (변경 전 → 지금)")


def restore(path):
    """undo lab.patch"""
    full = _p(path)
    if os.path.exists(full + ".orig"):
        open(full, "w").write(open(full + ".orig").read())
        os.remove(full + ".orig")
        print("되돌렸습니다: " + path)
    else:
        print("되돌릴 것이 없습니다: " + path)


def _prompt_text(name, files):
    """a prompt from docs/PROMPTS.md with its {placeholders} filled.
    A placeholder is filled from files[name] (spaces in the name may be written as _): a path in the lab
    folder is replaced by that file's contents, anything else is used as text. A placeholder that is
    itself a path is replaced by that file. Returns (text, [placeholders left unfilled])."""
    text = open(os.path.join(ROOT, "docs", "PROMPTS.md")).read()
    m = re.search(r"## %s\..*?```\n(.*?)```" % re.escape(name), text, flags=re.S)
    if not m:
        return None, []
    left = []

    def fill(mt):
        key = mt.group(1).strip()
        val = files.get(key, files.get(key.replace(" ", "_")))
        if val is None:
            val = key
        elif not os.path.exists(_p(str(val))):
            return str(val)
        if os.path.exists(_p(str(val))) and os.path.isfile(_p(str(val))):
            return open(_p(str(val))).read()
        left.append(key)
        return mt.group(0)
    return re.sub(r"\{([^{}\n]+)\}", fill, m.group(1)), left


def _missing(name, files):
    """True (after saying so) when a placeholder was given None, e.g. the answer of an earlier Codex cell that
    did not run"""
    none = [k for k, v in files.items() if v is None]
    if none:
        print("프롬프트 %s에 넣을 값이 없습니다: %s. 앞 셀의 결과를 먼저 받으세요." % (name, ", ".join(k.replace("_", " ") for k in none)))
    return bool(none)


def prompt(name, **files):
    """print a prompt from docs/PROMPTS.md with its {file} placeholders filled, ready to copy"""
    if _missing(name, files):
        return
    text, left = _prompt_text(name, files)
    if text is None:
        print("프롬프트 %s를 찾지 못했습니다." % name)
        return
    print(text)


def diff_text(folder):
    """unified diff of a scenario folder (changed files only) against legacy/, as text for a prompt"""
    import difflib
    out = []
    base = _p(folder)
    for dirpath, _, names in os.walk(os.path.join(base, "src")):
        for n in sorted(names):
            new = os.path.join(dirpath, n)
            rel = os.path.relpath(new, base)
            old = os.path.join(ROOT, "legacy", rel)
            a = open(old).read().splitlines(True) if os.path.exists(old) else []
            b = open(new).read().splitlines(True)
            out += difflib.unified_diff(a, b, "legacy/" + rel, folder.rstrip("/") + "/" + rel)
    return "".join(out)


def source_text(folder="legacy/src"):
    """every .java file under a folder, each headed by its path, as text for a prompt (P-4)"""
    out = []
    for dirpath, _, names in sorted(os.walk(_p(folder))):
        for n in sorted(names):
            if n.endswith(".java"):
                f = os.path.join(dirpath, n)
                out.append("=== %s ===\n%s" % (os.path.relpath(f, ROOT), open(f).read()))
    return "\n".join(out)


def impact_tests(folder):
    """the tests the impact tool chose for a change (out/impact-<변경>.json, made by lab.run("impact", V=folder)),
    one per line, as text for a prompt (P-4)"""
    import json as _json
    vname = folder.rstrip("/").replace("scenarios/", "", 1).replace("/", "-")
    jp = os.path.join(ROOT, "out", "impact-%s.json" % vname)
    if not os.path.exists(jp):
        print("도구 결과가 없습니다. 먼저 lab.run(\"impact\", V=%r)를 실행하세요." % folder)
        return None
    return "\n".join(re.sub(r"\(.*\)$", "", t.replace("com.dxlab.homehub.", "")) for t in _json.load(open(jp))["tests"])


def dafny_errors(path):
    """`dafny verify <path>` output, as text for a prompt (P-2)"""
    p = subprocess.run(["dafny", "verify", _p(path)], cwd=ROOT, capture_output=True, text=True)
    return (p.stdout + p.stderr).strip()


# every lab.codex call uses this model and reasoning effort (the lowest this model takes), to keep calls short.
# Change them here if the model is not available to you.
CODEX_MODEL = "gpt-5.6-luna"
CODEX_EFFORT = "none"


def codex_models():
    """the models (and reasoning efforts) this computer's Codex offers, from Codex's own model list"""
    import json as _json
    path = os.path.join(os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"), "models_cache.json")
    try:
        d = _json.load(open(path))
    except (OSError, ValueError):
        print("Codex의 모델 목록을 찾지 못했습니다. 터미널에서 codex 를 한 번 실행하고 /model 로 확인하세요.")
        return
    rows = []
    for m in (d.get("models", []) if isinstance(d, dict) else d):
        if not isinstance(m, dict) or m.get("visibility") == "hide":
            continue
        levels = [x.get("effort") for x in m.get("supported_reasoning_levels") or [] if isinstance(x, dict)]
        rows.append((m.get("slug") or m.get("id"), ", ".join(l for l in levels if l)))
    print("이 컴퓨터의 Codex에서 쓸 수 있는 모델 (실습 기본값: %s, 추론 %s)" % (CODEX_MODEL, CODEX_EFFORT))
    for slug, levels in rows:
        print("  %-16s 추론: %s%s" % (slug, levels or "-", "   <- 기본값" if slug == CODEX_MODEL else ""))
    print("추론 none(생각하지 않고 바로 답)은 목록에 없지만 %s에서 쓸 수 있는 것을 확인했습니다." % CODEX_MODEL)


def _codex_ready():
    import shutil
    if not shutil.which("codex"):
        return "Codex CLI가 없습니다. 설치: npm install -g @openai/codex"
    if os.environ.get("CODEX_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        return None
    st = subprocess.run(["codex", "login", "status"], capture_output=True, text=True)
    if st.returncode != 0 or "not logged in" in (st.stdout + st.stderr).lower():
        return "Codex에 로그인되어 있지 않습니다. 터미널에서 codex login 을 실행하거나, CODEX_API_KEY 환경 변수를 설정한 뒤 Jupyter를 다시 시작하세요."
    return None


def _message_html(text):
    """the agent's answer: prose as paragraphs, fenced code as code blocks"""
    parts, pos = [], 0
    for m in re.finditer(r"```([\w+-]*)\n(.*?)```", text, flags=re.S):
        prose = text[pos:m.start()].strip()
        if prose:
            parts.append('<div style="white-space:pre-wrap;font-size:14px;line-height:1.6">%s</div>' % report.e(prose))
        parts.append('<pre class="box" style="font-size:12.5px;max-height:none">%s</pre>' % report.e(m.group(2)))
        pos = m.end()
    rest = text[pos:].strip()
    if rest:
        parts.append('<div style="white-space:pre-wrap;font-size:14px;line-height:1.6">%s</div>' % report.e(rest))
    return "".join(parts)


def _code_block(text, path):
    """the code block to save: the one in the file's language if there is one, else the longest"""
    blocks = re.findall(r"```([\w+-]*)\n(.*?)```", text, flags=re.S)
    if not blocks:
        return None
    want = {".dfy": ("dafny",), ".java": ("java",)}.get(os.path.splitext(path)[1], ())
    hit = [b for lang, b in blocks if lang.lower() in want]
    return max(hit or [b for _, b in blocks], key=len)


def codex(name, save=None, timeout=900, show_prompt=True, 깊게=False, model=None, effort=None, **files):
    """send a prompt from docs/PROMPTS.md to Codex (codex exec) and show its answer below.
    By default Codex answers from the prompt alone: it may not run commands or read files (read-only
    sandbox); model and reasoning effort are CODEX_MODEL / CODEX_EFFORT, which keeps a call short (model=, effort=
    pick others for one call; lab.codex_models() lists what this Codex offers). 깊게=True lets it work in
    out/codex/<prompt>-<time>/ (write files, run dafny) and read the lab folder. With save="mine/X.dfy" the code
    block of the answer is written there (the previous file is kept as X.dfy.before and the change shown).
    Placeholders: see _prompt_text, e.g. lab.codex("P-4", diff=lab.diff_text("scenarios/req2/ai"))"""
    if _missing(name, files):
        return None
    model = model or CODEX_MODEL
    effort = effort or CODEX_EFFORT
    text, left = _prompt_text(name, files)
    if text is None:
        print("프롬프트 %s를 찾지 못했습니다." % name)
        return None
    if left:
        files_ = [k for k in left if "/" in k]
        if files_:
            print("프롬프트 %s에 넣을 파일이 아직 없습니다: %s (앞 단계 셀을 먼저 실행하세요)" % (name, ", ".join(files_)))
        others = [k for k in left if "/" not in k]
        if others:
            print("프롬프트 %s에 채우지 않은 자리가 있습니다: %s" % (name, ", ".join("{%s}" % k for k in others)))
            print("예: lab.codex(%r, %s=...)" % (name, others[0].replace(" ", "_")))
        return None
    if show_prompt:
        n = text.count("\n") + 1
        display(HTML('<details style="font-size:13px"><summary>Codex에 보내는 프롬프트 %s (%d줄, 눌러서 보기)</summary>'
                     '<pre style="white-space:pre-wrap;font-size:12px">%s</pre></details>' % (name, n, report.e(text)))
                if HTML else text)
    why = _codex_ready()
    if why:
        print(why)
        print("Codex를 쓸 수 없으면 lab.prompt(%r)로 프롬프트를 출력해 사내 AI 도구에 붙여 넣으세요." % name)
        return None
    import time
    # Codex works in its own scratch folder (it may write files and run dafny there); the lab folder is
    # only read. What we keep is taken from its final answer.
    work = os.path.join(ROOT, "out", "codex", "%s-%s" % (name, time.strftime("%H%M%S")))
    os.makedirs(work, exist_ok=True)
    out = os.path.join(work, "answer.md")
    if 깊게:
        cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "--color", "never",
               "-s", "workspace-write", "-C", work, "-m", model, "-c", 'model_reasoning_effort="%s"' % effort,
               "--json", "-o", out, "-"]
        text = text + "\n\n(작업 폴더는 지금 폴더다. 실습 폴더 %s 는 읽기만 하라. 최종 답에 결과 코드 전체를 코드 블록 하나로 넣어라.)" % ROOT
    else:
        cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "--color", "never",
               "-s", "read-only", "-C", work, "-m", model, "-c", 'model_reasoning_effort="%s"' % effort,
               "--json", "-o", out, "-"]
        text = text + ("\n\n(필요한 것은 위에 다 있다. 명령을 실행하거나 파일을 찾아 읽지 말고 바로 답하라. "
                       "코드를 만들면 최종 답에 결과 코드 전체를 코드 블록 하나로 넣어라.)")
    print("Codex 실행 중… (모델 %s, 추론 %s)%s" % (model, effort, " (깊게: 직접 파일을 쓰고 명령을 돌리므로 몇 분 걸릴 수 있음)" if 깊게 else ""))
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    p.stdin.write(text)
    p.stdin.close()
    import json as _json
    for line in p.stdout:
        line = line.strip()
        try:
            ev = _json.loads(line)
        except ValueError:
            continue                     # log lines; errors also come as JSON events
        typ = ev.get("type", "")
        item = ev.get("item") or {}
        kind = item.get("type") or item.get("item_type") or ""
        if typ == "item.started" and kind == "command_execution":
            print("  명령 실행: %s" % str(item.get("command", ""))[:160])
        elif typ == "item.completed" and kind == "file_change":
            ch = item.get("changes") or []
            print("  파일 작성(작업 폴더): %s" % ", ".join(os.path.basename(str(c.get("path", ""))) for c in ch if isinstance(c, dict)))
        elif typ in ("error", "turn.failed"):
            msg = ev.get("message") or (ev.get("error") or {}).get("message") or line
            print("  %s: %s" % ("연결 재시도" if "Reconnecting" in str(msg) else "오류", str(msg)[:240]))
        if time.time() - t0 > timeout:
            p.kill()
            print("  시간 초과(%d초)로 멈췄습니다." % timeout)
            break
    code = p.wait()
    answer = open(out).read().strip() if os.path.exists(out) else ""
    print("끝났습니다 (%.0f초)." % (time.time() - t0))
    if not answer:
        print("Codex의 답이 없습니다(종료 코드 %d). 위 오류를 확인하세요." % code)
        return None
    body = '<div style="font-size:13px;color:var(--muted)">Codex의 답 (%s)</div>%s' % (name, _message_html(answer))
    _frame(_bare(body), est=answer.count("\n") * 20 + 80)
    if save:
        blk = _code_block(answer, save)
        if blk is None:
            print("답에 코드 블록이 없어 %s에 저장하지 않았습니다." % save)
        else:
            full = _p(save)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            before = None
            if os.path.exists(full):
                before = full + ".before"
                open(before, "w").write(open(full).read())
            open(full, "w").write(blk)
            print("저장했습니다: %s" % save)
            if before:
                diff(os.path.relpath(before, ROOT), save, title="%s: 이전 → Codex가 고친 것 (계약 줄이 바뀌었는지 확인)" % save)
    return answer


try:                                     # start the page server now, so "새 탭에서 열기" in saved outputs works
    _serve()                             # as soon as `import lab` has run
except Exception:
    pass
