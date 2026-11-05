"""
structure_page: writes docs/homehub_구조.html, the zoomable HomeHub structure map shown by lab.structure().

    python3 tools/structure_page.py            # regenerate the page after editing this file

Levels (C4 style, like zooming a map): outside (context) -> inside (components) -> one component -> its code.
Every box with a ⊕ opens the level below it. The "inside" level also has a step-by-step tour of one message.
The page is static HTML + inline SVG + a little JavaScript; no network, no libraries.
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "homehub_구조.html")
E = html.escape


# ------------------------------------------------------------------ svg helpers
def T(x, y, s, cls="", anchor="start"):
    a = ' text-anchor="%s"' % anchor if anchor != "start" else ""
    return '<text x="%s" y="%s" class="%s"%s>%s</text>' % (x, y, cls, a, s)


def node(nid, go, x, y, w, h, title, sub=None, lines=(), cls="", sub_inline=False):
    """a box; go = level id it opens (None: not clickable)"""
    attrs = ' data-go="%s"' % go if go else ""
    out = ['<g class="node %s" id="n-%s"%s>' % (cls, nid, attrs),
           '<rect x="%d" y="%d" width="%d" height="%d" rx="6"/>' % (x, y, w, h)]
    if sub and sub_inline:
        out.append(T(x + 12, y + 24, '%s <tspan class="sub">%s</tspan>' % (E(title), E(sub)), "tt"))
        yy = y + 24
    else:
        out.append(T(x + 12, y + 21, E(title), "tt"))
        yy = y + 21
        if sub:
            yy += 16
            out.append(T(x + 12, yy, E(sub), "sub"))
    for ln in lines:
        yy += 17
        out.append(T(x + 12, yy, ln, "ln"))
    if go:
        out.append(T(x + w - 10, y + 19, "⊕", "zoom", "end"))
    out.append("</g>")
    return "".join(out)


def edge(eid, d, label=None, lx=0, ly=0, anchor="start", dashed=False):
    out = ['<g class="edge%s" id="e-%s"><path d="%s"/>' % (" dash" if dashed else "", eid, d)]
    if label:
        for i, part in enumerate(label.split("\n")):
            out.append(T(lx, ly + i * 14, part, "el", anchor))
    out.append("</g>")
    return "".join(out)


def group(x, y, w, h, label):
    return '<rect x="%d" y="%d" width="%d" height="%d" rx="10" class="grp"/>' % (x, y, w, h) + T(x + 12, y + 19, label, "gl")


def diamond(cx, cy, w, h, lines):
    pts = "%d,%d %d,%d %d,%d %d,%d" % (cx, cy - h / 2, cx + w / 2, cy, cx, cy + h / 2, cx - w / 2, cy)
    out = ['<g class="node dia"><polygon points="%s"/>' % pts]
    y0 = cy - (len(lines) - 1) * 8 + 4
    for i, ln in enumerate(lines):
        out.append(T(cx, y0 + i * 16, ln, "ln dk", "middle"))
    out.append("</g>")
    return "".join(out)


def card(x, y, w, h, title, lines, cls="", title_cls="tt"):
    out = ['<g class="node static %s"><rect x="%d" y="%d" width="%d" height="%d" rx="6"/>' % (cls, x, y, w, h),
           T(x + 12, y + 22, title, title_cls)]
    for i, ln in enumerate(lines):
        out.append(T(x + 12, y + 44 + i * 18, ln, "ln"))
    out.append("</g>")
    return "".join(out)


# ------------------------------------------------------------------ level 1: outside (context)
def lv_outside():
    s = []
    s.append(node("devs", "devices", 20, 110, 230, 230, "가전 8대", None, [
        "세탁기 <tspan class='m'>washer-1</tspan>", "건조기 <tspan class='m'>dryer-1</tspan>",
        "냉장고 <tspan class='m'>fridge-1, fridge-2</tspan>", "에어컨 <tspan class='m'>aircon-1</tspan>",
        "오븐 <tspan class='m'>oven-1</tspan>", "누수센서 <tspan class='m'>leak-1</tspan>", "TV <tspan class='m'>tv-1</tspan>",
        "<tspan class='mu'>무슨 일이 생기면 메시지를 보냄</tspan>"], cls="ext"))
    s.append(edge("msg", "M250,200 H408", "메시지 한 줄", 329, 190, "middle"))
    s.append(T(329, 222, "10|fridge-1|TEMP|12|…", "el m", "middle"))
    s.append(node("hh", "inside", 410, 100, 230, 200, "HomeHub", None, [
        "가전 메시지를 받아", "차례대로 처리하는 프로그램", "", "<tspan class='hint'>⊕ 눌러서 안으로 들어가기</tspan>"], cls="main big"))
    s.append(node("cfg", "config", 410, 350, 230, 64, "설정 파일", "hub.properties", [], cls="ext"))
    s.append(edge("cfg", "M525,350 V302", "읽음", 531, 330))
    outs = [("o1", "hub", 20, "상태 한 줄", "지금 허브 상태를 글자 한 줄로"),
            ("o2", "logs", 160, "로그", "무슨 일이 있었는지 적은 기록"),
            ("o3", "metrics", 300, "개수", "일마다 몇 번 일어났는지 센 숫자")]
    for oid, go, y, t, sub in outs:
        s.append(node(oid, go, 740, y, 240, 80, t, None, [sub], cls="ext"))
        s.append(edge(oid, "M640,200 C690,200 690,%d 738,%d" % (y + 40, y + 40)))
    return "0 0 1000 430", "".join(s)


DESC_OUTSIDE = """
<h3>HomeHub는 무엇인가</h3>
<p>HomeHub는 집 안 가전을 한곳에서 관리하는 프로그램입니다(이 실습을 위해 만든 가상의 프로그램, Java 8, 약 1,600줄).</p>
<p>가전은 무슨 일이 생길 때마다 HomeHub에 <b>메시지</b> 한 줄을 보냅니다. "전원이 켜졌다", "온도를 재 보니 12°C다", "물이 샌다" 같은 것입니다.
HomeHub는 메시지를 받은 순서대로 처리하고, 필요하면 가전을 멈춥니다. 예를 들어 냉장고 온도가 계속 높으면 냉장고를 고장 상태로 돌리고, 물이 새면 돌고 있는 세탁기와 건조기를 멈춥니다.</p>
<p>처리한 결과는 오른쪽 세 가지로 남습니다.</p>
<table>
<tr><th>상태 한 줄</th><td>지금 허브 상태(대기 중인 일, 기기마다 상태, 전력, 개수, 최근 로그)를 글자 한 줄로 적은 것. 이 한 줄을 만드는 함수가 <code>HomeHub.observable()</code>입니다. 실습의 <b>동작 기록</b>(<code>golden/*.trace</code>)은 메시지를 하나 처리할 때마다 이 한 줄을 적어 둔 파일입니다.</td></tr>
<tr><th>로그</th><td>무슨 일이 있었는지 한 줄씩 적은 기록. 예: <code>OVERHEAT_ALARM:1000000@fridge-1</code> = fridge-1에 과열 경보.</td></tr>
<tr><th>개수</th><td>일마다 몇 번 일어났는지 센 숫자. 예: <code>submit.accepted=12</code> = 지금까지 받아들인 이벤트가 12개.</td></tr>
</table>

<h3>메시지 한 줄은 이렇게 생겼습니다</h3>
<p><code>10|fridge-1|TEMP|12|240000|unit=C</code> = 10번 메시지, 냉장고 1이(<code>fridge-1</code>) 온도를 보고(<code>TEMP</code>), 값은 12, 보낸 시각은 240,000ms(4분), 단위는 섭씨.
칸마다 뜻은 HomeHub 안의 <a href="#" data-go="parser">입구</a>에서 자세히 봅니다.</p>

<h3>실습에서는: 입력 파일과 동작 기록</h3>
<p>실습에는 진짜 가전이 없습니다. 대신 가전이 보냈을 메시지를 시간 순서대로 적은 <b>입력 파일</b>(<code>legacy/workloads/*.txt</code>)을 HomeHub에 한 줄씩 넣습니다.</p>
<pre>1|fridge-1|PWR_ON|0|0|fw=2.1        ← 메시지: 냉장고 1 전원 켜짐
4|fridge-1|TEMP|9|60000|unit=C      ← 메시지: 냉장고 1 온도 9°C
!drain                              ← 명령: 쌓인 일을 모두 처리하라</pre>
<p><code>!</code>로 시작하는 줄은 메시지가 아니라 <b>명령</b>입니다. 진짜 허브는 쌓인 일을 쉬지 않고 처리하지만, 실습에서는 언제 처리할지를 입력 파일이 정합니다.
<code>!drain</code>은 "쌓인 일을 모두 처리", <code>!step</code>은 "하나만 처리", <code>!tick</code>은 "점검 한 번"입니다.</p>

<p class="next">다음: 가운데 <b>HomeHub</b> 상자를 누르세요. 안에 어떤 부품이 있는지 보입니다.</p>
"""


# ------------------------------------------------------------------ level 2: inside (components)
def lv_inside():
    s = []
    s.append(node("hub", "hub", 20, 12, 960, 64, "HomeHub", "app.HomeHub", [
        "모든 부품을 만들어 서로 연결하고, 바깥에서 부르는 ingest · step · drain · tick 으로 일을 진행시킵니다"],
        cls="main", sub_inline=True))
    s.append(node("parser", "parser", 70, 112, 140, 70, "입구", "EventParser", ["한 줄 → 이벤트"]))
    s.append(node("disp", "disp", 250, 112, 180, 100, "접수·꺼내기", "Dispatcher", ["대기열에 넣을지 정함", "하나 꺼내 처리기로"]))
    q = [node("queue", "queue", 490, 112, 180, 100, "대기열", "RingEventQueue", ["처리 차례를 기다리는 줄"])]
    for i in range(8):
        q.append('<rect class="qc" id="qc%d" x="%d" y="182" width="18" height="18" rx="2"/>' % (i, 502 + i * 20))
    s.append("".join(q))
    s.append(node("watch", "watch", 740, 112, 240, 64, "점검", "Watchdog", ["대기열이 계속 꽉 차 있나 보기"]))
    s.append(node("recov", "watch", 740, 188, 240, 64, "복구", "RecoveryManager", ["막힌 대기열 정리"]))
    s.append(node("rules", "rules", 30, 290, 180, 96, "규칙 검사", "RuleEngine", ["처리 뒤 규칙 확인", "필요하면 새 이벤트"]))
    s.append(node("reg", "reg", 250, 290, 180, 74, "처리기 고르기", "HandlerRegistry", ["종류에 맞는 처리기로"]))
    s.append(group(480, 268, 200, 300, "처리기 (종류별로 일을 함)"))
    for i, (nid, t, c, ln) in enumerate([("hStatus", "기기 상태 처리기", "DeviceStatusHandler", "전원·작동·문"),
                                         ("hTemp", "온도 처리기", "TemperatureHandler", "온도 기록, 고온 횟수"),
                                         ("hSafety", "안전 처리기", "SafetyHandler", "누수·과열 때 멈춤"),
                                         ("hCount", "개수 처리기", "CountingHandler", "모든 이벤트 개수 세기")]):
        s.append(node(nid, "handlers", 490, 296 + i * 66, 180, 58, t, c, [ln]))
    s.append(group(740, 268, 240, 300, "처리기들이 바꾸는 것"))
    for i, (nid, go, t, c, ln) in enumerate([("logs", "logs", "로그", "AuditLog", "무슨 일이 있었나 적기"),
                                             ("metrics", "metrics", "개수 세기", "Metrics", "이름별로 횟수 세기"),
                                             ("power", "power", "전력 관리", "PowerBudget", "동시 전력 4,000W 이하로"),
                                             ("devices", "devices", "기기 목록", "DeviceRegistry", "기기 8대와 각 상태")]):
        s.append(node(nid, go, 750, 296 + i * 66, 220, 58, t, c, [ln]))
    # edges
    s.append(edge("parse", "M140,76 V110", "① 바꾸기", 146, 98))
    s.append(edge("submit", "M300,76 V110", "② 넣기", 306, 98))
    s.append(edge("step", "M390,76 V110", "꺼내 처리 (step · drain)", 396, 98))
    s.append(edge("offer", "M430,145 H488", "넣기", 459, 138, "middle"))
    s.append(edge("poll", "M488,180 H432", "꺼내기", 459, 197, "middle"))
    s.append(edge("reg", "M340,212 V288", "넘김", 346, 254))
    s.append(edge("notify", "M250,195 H120 V288", "처리 끝 알림", 126, 254))
    s.append(edge("back", "M40,288 V78", "새 이벤트\n다시 넣기", 46, 226))
    s.append(edge("choose", "M430,327 H488", "종류로", 459, 319, "middle"))
    s.append(edge("change", "M680,420 H738", "바꿈", 709, 412, "middle"))
    s.append(edge("tick", "M860,76 V110", "tick: 1초마다 점검", 866, 98))
    s.append(edge("wq", "M740,140 H672", "개수 보기", 706, 132, "middle"))
    s.append(edge("rq", "M740,222 H672", "정리", 706, 214, "middle"))
    s.append(edge("read", "M120,386 V600 H860 V556", "기기 정보 읽기 (예: 연속 고온 횟수)", 140, 594))
    return "0 0 1000 620", "".join(s)


DESC_INSIDE = """
<p class="tourcall"><button class="big" data-act="tour">▶ 메시지 하나 따라가기</button>
냉장고가 높은 온도를 보고한 메시지 하나가 어느 부품을 거쳐 어떻게 처리되는지, 위 그림에서 한 단계씩 보여 줍니다.</p>
<h3>HomeHub 안의 부품</h3>
<p>HomeHub 안에는 일을 나눠 맡은 부품(Java 객체)이 있습니다. 큰 흐름은 <b>왼쪽 위에서 오른쪽 아래로</b> 갑니다.
메시지가 <b>입구</b>에서 이벤트로 바뀌고 → <b>접수</b>가 <b>대기열</b>에 넣고 → 차례가 오면 꺼내서 → <b>처리기</b>가 일을 하고 → 오른쪽 아래(기기 상태, 전력, 로그, 개수)를 바꿉니다.
⊕ 표시가 있는 상자를 누르면 그 부품 안으로 들어갑니다.</p>
<h3>먼저 알아 둘 말</h3>
<table>
<tr><th>메시지와 이벤트</th><td>메시지는 가전이 보낸 <b>글자 한 줄</b>, 이벤트는 그 한 줄을 프로그램이 다루기 좋게 바꾼 <b>객체</b>(<code>Event</code>)입니다. 이벤트에는 번호, 기기, 종류, 값, 시각이 들어 있습니다.</td></tr>
<tr><th>대기열</th><td>들어온 이벤트가 처리 차례를 기다리는 줄입니다. 먼저 들어온 것이 먼저 처리됩니다. 칸은 8개뿐입니다.</td></tr>
<tr><th>중요 이벤트</th><td>누수(<code>LEAK</code>)와 과열(<code>OVHT</code>) 두 종류. 대기열이 가득 차도 절대 버리지 않습니다.</td></tr>
<tr><th>처리기</th><td>이벤트 종류마다 실제 일을 하는 부품입니다. 온도 보고는 온도 처리기, 누수는 안전 처리기가 맡는 식입니다.</td></tr>
</table>
"""

TOUR = [
    dict(on=[], mv=[], q=[], fr="IDLE", hot=2, box=[], log="STATE:fridge-1:OFF->IDLE",
         t="준비. 냉장고 1(<code>fridge-1</code>)은 켜져서 쉬는 중(IDLE)이고, 12°C를 이미 두 번 보고해서 <b>연속 고온 횟수</b>가 2입니다. 대기열은 비어 있습니다. 이제 세 번째 12°C 보고가 들어옵니다."),
    dict(on=["n-hub"], mv=[], t="가전이 보낸 메시지 한 줄 <code>10|fridge-1|TEMP|12|240000|unit=C</code>가 HomeHub에 들어옵니다(<code>ingest</code>)."),
    dict(on=["n-hub", "e-parse", "n-parser"], mv=["e-parse"],
         t="<b>입구</b>(EventParser)가 글자 한 줄을 이벤트 객체로 바꿉니다. 10번 · fridge-1 · 온도 보고 · 값 12."),
    dict(on=["n-hub", "e-submit", "n-disp", "e-offer", "n-queue"], mv=["e-submit", "e-offer"], q=["10"],
         t="<b>접수</b>(Dispatcher)가 대기열에 빈 칸이 있는지 보고, 있으니 넣습니다. 메시지를 받는 일(<code>ingest</code>)은 여기서 끝납니다. <b>아직 아무것도 처리하지 않았습니다.</b> 처리는 대기열에서 꺼낼 차례가 와야 시작됩니다."),
    dict(on=["n-hub", "e-step", "n-disp", "e-poll", "n-queue"], mv=["e-step", "e-poll"], q=[],
         t="입력 파일의 <code>!drain</code> 줄: HomeHub가 '대기열이 빌 때까지 하나씩 꺼내 처리하기'(<code>drain</code>)를 시작합니다. 맨 앞의 10번을 꺼냅니다."),
    dict(on=["n-disp", "e-reg", "n-reg", "e-choose", "n-hTemp"], mv=["e-reg", "e-choose"],
         t="<b>처리기 고르기</b>(HandlerRegistry)가 이벤트 종류를 봅니다. 온도 보고이니 <b>온도 처리기</b>에 넘깁니다."),
    dict(on=["n-hTemp", "n-hCount", "e-change", "n-devices", "n-metrics"], mv=["e-change"], hot=3,
         t="<b>온도 처리기</b>: 12°C는 기준(10°C) 이상이므로 fridge-1의 연속 고온 횟수를 2 → <b>3</b>으로 올려 기기 목록에 적어 둡니다. 이어서 <b>개수 처리기</b>가 <code>evt.temp_report</code>를 1 늘립니다. 온도 처리기가 하는 일은 여기까지입니다."),
    dict(on=["n-disp", "e-notify", "n-rules", "e-read", "n-devices"], mv=["e-notify", "e-read"], box=["1000000"],
         log="RULE_OVERHEAT:10@fridge-1",
         t="처리가 끝나면 접수가 <b>규칙 검사</b>(RuleEngine)에 알립니다. 규칙 검사가 기기 목록에서 fridge-1의 연속 고온 횟수를 읽어 보니 3입니다. '3번 연속 고온이면 과열' 규칙에 걸리므로 <b>과열 이벤트</b>(번호 1000000)를 새로 만들어 보관함에 넣고, 로그에 <code>RULE_OVERHEAT</code>를 적습니다."),
    dict(on=["n-rules", "e-back", "n-hub", "e-submit", "n-disp", "e-offer", "n-queue"], mv=["e-back", "e-submit", "e-offer"],
         q=["!1000000"], box=[],
         t="HomeHub가 보관함에 새 이벤트가 있는지 보고 꺼내서 접수에 넣습니다(<code>flushDerived</code>). 빈 칸이 있으니 과열 이벤트가 대기열 맨 뒤에 들어갑니다."),
    dict(on=["n-hub", "e-step", "n-disp", "e-poll", "n-queue", "e-reg", "n-reg", "e-choose", "n-hSafety"],
         mv=["e-poll", "e-reg", "e-choose"], q=[],
         t="대기열이 아직 비지 않았으니 drain이 계속됩니다. 과열 이벤트를 꺼내고, 종류가 과열이니 처리기 고르기가 <b>안전 처리기</b>로 보냅니다."),
    dict(on=["n-hSafety", "e-change", "n-devices", "n-power", "n-logs"], mv=["e-change"], fr="ERROR",
         log="OVERHEAT_ALARM:1000000@fridge-1",
         t="<b>안전 처리기</b>가 fridge-1을 고장 상태(ERROR)로 바꾸고, 전력 관리에서 빼고, 로그에 <code>OVERHEAT_ALARM</code>을 적습니다. 그 뒤 개수 처리기와 규칙 검사도 거치지만 더 할 일은 없습니다."),
    dict(on=["n-hub"], mv=[],
         t="대기열이 비어서 drain이 끝납니다. 메시지 한 줄이 이벤트 두 개(온도 보고, 과열)의 처리로 이어졌습니다. 실습의 동작 기록에는 이때의 상태 한 줄이 남습니다: <code>… fridge-1:ERROR … audit=[…, RULE_OVERHEAT:10@fridge-1, OVERHEAT_ALARM:1000000@fridge-1]</code>"),
]


# ------------------------------------------------------------------ level 3: components
def lv_hub():
    s = []
    rows = [("ingest(한 줄)", "parser", "메시지 줄", ["입구에서 이벤트로", "바꾸고 접수에 넣음", "새 이벤트도 넣음"]),
            ("step()", "disp", "!step", ["대기열에서 하나", "꺼내 처리", "새 이벤트도 넣음"]),
            ("drain()", "disp", "!drain", ["대기열이 빌 때까지", "step()을 반복"]),
            ("tick()", "watch", "!tick", ["점검을 한 번 하고", "막혔다고 하면 복구"]),
            ("observable()", None, "모든 줄 뒤", ["지금 상태를", "글자 한 줄로 만듦"])]
    for i, (m, go, inp, lines) in enumerate(rows):
        x = 20 + i * 196
        s.append('<g class="node static ext"><rect x="%d" y="20" width="176" height="40" rx="20"/>%s</g>'
                 % (x, T(x + 88, 45, E(inp), "ln dk", "middle")))
        s.append(edge("h%d" % i, "M%d,60 V98" % (x + 88)))
        s.append(node("m%d" % i, go, x, 100, 176, 120, m, None, lines, cls="mono-title"))
    s.append(T(20, 250, "위: 입력 파일의 줄  →  아래: HubMain이 부르는 HomeHub 메서드", "el"))
    s.append(card(20, 280, 960, 120, "생성자: new HomeHub(설정)", [
        "설정을 읽어 부품을 모두 만들고 서로 연결합니다(조립). 대기열 8칸, 전력 상한 4,000W, 기기 8대 등록이 여기서 정해집니다.",
        "어떤 종류의 이벤트를 어느 처리기가 맡을지도 여기서 등록합니다(처리기 고르기 참고).",
        "그래서 HomeHub 코드를 읽으면 부품이 어떻게 이어져 있는지 한곳에서 볼 수 있습니다."], cls="wide"))
    return "0 0 1000 420", "".join(s)


DESC_HUB = """
<h3>HomeHub: 조립하고 진행시키는 곳</h3>
<p>HomeHub 객체는 직접 계산을 거의 하지 않습니다. 하는 일은 두 가지입니다. ① 처음에 부품을 모두 만들어 연결하고(생성자), ② 바깥에서 부르는 메서드로 일을 진행시킵니다.</p>
<table>
<tr><th><code>ingest(한 줄)</code></th><td>메시지 한 줄을 받습니다. 입구에서 이벤트로 바꾸고 접수에 넣습니다. <b>처리는 하지 않습니다.</b> 형식이 틀린 줄이면 <code>INVALID</code>를 돌려줍니다.</td></tr>
<tr><th><code>step()</code></th><td>대기열에서 하나를 꺼내 처리합니다. 처리 중에 규칙 검사가 새 이벤트를 만들었으면 그것을 대기열에 넣습니다(<code>flushDerived</code>).</td></tr>
<tr><th><code>drain()</code></th><td>대기열이 빌 때까지 <code>step()</code>을 반복합니다. 처리 중에 새로 생긴 이벤트도 끝까지 처리됩니다.</td></tr>
<tr><th><code>tick()</code></th><td>정기 점검. 진짜 허브에서는 1초마다 불립니다. 점검(Watchdog)이 "대기열이 막혔다"고 하면 복구(RecoveryManager)를 부릅니다.</td></tr>
<tr><th><code>observable()</code></th><td>지금 상태를 글자 한 줄로 만듭니다. 아래 "상태 한 줄 읽기" 참고.</td></tr>
</table>
<h3>상태 한 줄 읽기</h3>
<p>실습 프로그램(<code>HubMain</code>)은 입력 파일을 한 줄 처리할 때마다 <code>줄번호 결과 | observable()</code>를 출력합니다. 이것을 저장해 둔 것이 동작 기록(<code>golden/*.trace</code>)입니다.</p>
<pre>19 drained 3 | q=0[] dev=aircon-1:OFF,…,fridge-1:ERROR,… power=0/4000 metrics={dispatch.count=12,…} audit=[…, OVERHEAT_ALARM:1000000@fridge-1]</pre>
<table>
<tr><th><code>19 drained 3</code></th><td>입력 파일 19번째 줄(<code>!drain</code>)을 처리했고, 이벤트 3개를 꺼내 처리했다. 메시지 줄이었다면 <code>ACCEPTED</code>(받음) 같은 접수 결과가 나옵니다.</td></tr>
<tr><th><code>q=0[]</code></th><td>대기열에 남은 개수와 그 번호들(오래된 것부터)</td></tr>
<tr><th><code>dev=…</code></th><td>기기마다 상태. OFF(꺼짐), IDLE(켜져서 쉼), RUNNING(작동 중), ERROR(고장으로 멈춤). 기기 이름의 알파벳순.</td></tr>
<tr><th><code>power=0/4000</code></th><td>지금 작동 중인 무거운 가전의 전력 합 / 상한(W)</td></tr>
<tr><th><code>metrics={…}</code></th><td>개수 세기의 숫자들</td></tr>
<tr><th><code>audit=[…]</code></th><td>로그의 마지막 3줄</td></tr>
</table>
"""


def lv_parser():
    s = []
    fields = [("10", "번호"), ("fridge-1", "기기"), ("TEMP", "종류 코드"), ("12", "값"), ("240000", "시각 (ms)"), ("unit=C", "속성")]
    x = 90
    for i, (f, lab) in enumerate(fields):
        w = max(70, len(f) * 13 + 24)
        s.append('<g class="node static"><rect x="%d" y="40" width="%d" height="44" rx="4"/>%s</g>'
                 % (x, w, T(x + w / 2, 68, E(f), "big m", "middle")))
        s.append(T(x + w / 2, 104, lab, "el", "middle"))
        x += w
        if i < len(fields) - 1:
            s.append(T(x + 9, 70, "|", "big m mu", "middle"))
            x += 18
    s.append(T(20, 30, "메시지 (글자 한 줄)", "gl"))
    s.append(edge("p", "M480,120 V170", "EventParser.parse()", 490, 150))
    s.append(card(250, 175, 500, 200, "이벤트 (Event 객체)", [
        "<tspan class='m'>seq       = 10</tspan>            번호",
        "<tspan class='m'>deviceId  = \"fridge-1\"</tspan>    기기",
        "<tspan class='m'>type      = TEMP_REPORT</tspan>   종류 (코드 TEMP)",
        "<tspan class='m'>value     = 12</tspan>            값",
        "<tspan class='m'>timestamp = 240000</tspan>        시각",
        "<tspan class='m'>attrs     = {unit=C}</tspan>      속성"], cls="wide"))
    return "0 0 1000 400", "".join(s)


DESC_PARSER = """
<h3>입구: 글자 한 줄을 이벤트로 바꾸기</h3>
<p>메시지는 <code>|</code>로 나뉜 칸들입니다. 앞의 다섯 칸은 꼭 있어야 하고, 여섯째 칸(속성)은 있을 수도 없을 수도 있습니다. 속성은 <code>이름=값</code>을 <code>;</code>로 이어 씁니다(예: <code>unit=F;fw=1.4</code>).</p>
<table>
<tr><th>종류 코드</th><th>뜻</th><th>맡는 처리기</th></tr>
<tr><td><code>PWR_ON</code> <code>PWR_OFF</code></td><td>전원 켜짐 / 꺼짐</td><td rowspan="4">기기 상태 처리기</td></tr>
<tr><td><code>CYC_S</code> <code>CYC_E</code></td><td>작동 시작 / 끝 (세탁 한 번, 건조 한 번 같은 것)</td></tr>
<tr><td><code>DOOR_O</code> <code>DOOR_C</code></td><td>문 열림 / 닫힘</td></tr>
<tr><td><code>HB</code></td><td>"살아 있음" 신호 (heartbeat). 가전이 주기적으로 보냄</td></tr>
<tr><td><code>TEMP</code></td><td>온도 보고</td><td>온도 처리기</td></tr>
<tr><td><code>LEAK</code></td><td>누수 감지 · <b>중요</b></td><td rowspan="2">안전 처리기</td></tr>
<tr><td><code>OVHT</code></td><td>과열 · <b>중요</b>. 가전이 보내기도 하고, HomeHub가 스스로 만들기도 함</td></tr>
</table>
<p>알아 둘 것</p>
<ul>
<li>온도가 화씨(<code>unit=F</code>)로 오면 여기서 섭씨로 바꿉니다. 그래서 <code>38</code>°F는 이벤트 안에서 <code>3</code>(°C)이 됩니다.</li>
<li>칸이 모자라거나 숫자 자리에 글자가 있으면 이벤트를 만들지 않습니다. HomeHub는 이 줄을 버리고 <code>INVALID</code>를 돌려줍니다.</li>
<li>모르는 종류 코드는 오류가 아니라 <code>UNKNOWN</code> 종류의 이벤트가 됩니다. 개수만 세고 아무 일도 하지 않습니다.</li>
</ul>
"""


def lv_disp():
    s = []
    s.append('<g class="node static start"><rect x="380" y="16" width="240" height="40" rx="20"/>%s</g>'
             % T(500, 41, "새 이벤트가 들어옴 <tspan class='m'>submit(e)</tspan>", "ln dk", "middle"))
    s.append(edge("a", "M500,56 V78"))
    s.append(diamond(500, 112, 220, 64, ["대기열에", "빈 칸이 있나?"]))
    s.append(edge("y1", "M610,112 H698", "있음", 654, 104, "middle"))
    s.append(card(700, 86, 280, 56, "넣음", ["<tspan class='m'>ACCEPTED</tspan>"], cls="ok"))
    s.append(edge("n1", "M500,144 V178", "가득 참 (8개)", 508, 166))
    s.append(diamond(500, 212, 240, 64, ["중요 이벤트인가?", "(누수 · 과열)"]))
    s.append(edge("y2", "M380,212 H260 V266", "예", 320, 204, "middle"))
    s.append(edge("n2", "M620,212 H740 V266", "아니오", 680, 204, "middle"))
    s.append(diamond(260, 300, 260, 64, ["대기열에", "비중요 이벤트가 있나?"]))
    s.append(diamond(740, 300, 260, 64, ["autoDrainOnFull", "설정이 켜져 있나?"]))
    s.append(edge("y3", "M130,300 H135 V388", "있음", 120, 330, "end"))
    s.append(edge("n3", "M390,300 H385 V388", "없음", 400, 330))
    s.append(edge("y4", "M610,300 H625 V388", "켜짐", 600, 330, "end"))
    s.append(edge("n4", "M870,300 H865 V388", "꺼짐 (기본)", 880, 330))
    outs = [(20, "가장 오래된 비중요 이벤트를", "빼고 넣음", "ACCEPTED_EVICTED", "R2 · R3", "ok"),
            (270, "하나를 지금 처리해", "자리를 만든 뒤 넣음", "ACCEPTED_DRAINED", "R2", "ok"),
            (510, "하나를 지금 처리해", "자리를 만든 뒤 넣음", "ACCEPTED_DRAINED", "R4", "ok"),
            (750, "받지 않음 (거부)", "로그에 REJECT", "REJECTED_FULL", "R4", "bad")]
    for x, l1, l2, r, rule, c in outs:
        s.append('<g class="node static %s"><rect x="%d" y="390" width="230" height="92" rx="6"/>%s%s%s%s</g>'
                 % (c, x, T(x + 12, 412, l1, "ln dk"), T(x + 12, 430, l2, "ln dk"), T(x + 12, 452, r, "ln m"),
                    T(x + 218, 474, "규칙 " + rule, "el", "end")))
    s.append(T(20, 522, "꺼내 처리 <tspan class='m'>dispatchOne()</tspan>:", "ln dk"))
    for i, t in enumerate(["대기열에서 맨 앞 하나 꺼냄", "처리기 고르기에 넘김", "규칙 검사에 '끝났다' 알림"]):
        x = 210 + i * 200
        s.append('<g class="node static"><rect x="%d" y="502" width="180" height="32" rx="4"/>%s</g>' % (x, T(x + 90, 523, t, "ln dk", "middle")))
        if i < 2:
            s.append(edge("d%d" % i, "M%d,518 H%d" % (x + 180, x + 198)))
    s.append(node("code", "disp_code", 820, 496, 160, 44, "코드로 보기", None, [], cls="codebtn"))
    return "0 0 1000 550", "".join(s)


DESC_DISP = """
<h3>접수·꺼내기: 받을지 정하고, 꺼내서 넘기기</h3>
<p>접수(Dispatcher)는 두 가지 일을 합니다.</p>
<ul>
<li><b>받기</b>(<code>submit</code>): 새 이벤트를 대기열에 넣습니다. 빈 칸이 있으면 그냥 넣고, <b>가득 찼을 때</b>만 위 그림의 규칙대로 정합니다.</li>
<li><b>꺼내 처리</b>(<code>dispatchOne</code>): 대기열 맨 앞 이벤트를 꺼내 처리기 고르기에 넘기고, 처리가 끝나면 규칙 검사에 알립니다.</li>
</ul>
<h3>바꾸면 안 되는 규칙 R1~R4</h3>
<p>대기열이 가득 찼을 때 어떻게 할지는 안전 검토에서 정한 규칙입니다. 실습 B~D에서 AI가 고친 코드가 이 규칙을 지키는지 확인합니다.</p>
<table>
<tr><th>R1</th><td>대기열에는 정해진 개수(8개)보다 많이 넣지 않는다.</td></tr>
<tr><th>R2</th><td>중요 이벤트(누수, 과열)는 절대 거부하지 않는다. 자리가 없으면 만든다.</td></tr>
<tr><th>R3</th><td>대기열에 남는 이벤트의 순서는 바꾸지 않는다. 자리를 만들어야 하면 <b>가장 오래된 비중요 이벤트</b>를 뺀다.</td></tr>
<tr><th>R4</th><td>비중요 이벤트는 대기열이 가득 차 있고 <code>autoDrainOnFull</code> 설정이 꺼져 있을 때만 거부한다(기본은 꺼짐).</td></tr>
</table>
<p>"하나를 지금 처리해 자리를 만든다"는, 맨 앞 이벤트를 차례보다 조금 일찍 처리해서 한 칸을 비운다는 뜻입니다. 결과 이름(<code>ACCEPTED</code> 등)은 실습 기록의 각 메시지 줄 맨 앞에 나옵니다.</p>
"""


def lv_queue():
    s = []
    cw, x0, y0 = 84, 150, 110
    for i in range(8):
        x = x0 + i * cw
        s.append('<rect class="cell" id="rc%d" x="%d" y="%d" width="%d" height="54"/>' % (i, x, y0, cw))
        s.append('<text class="big m" id="rt%d" x="%d" y="%d" text-anchor="middle"></text>' % (i, x + cw / 2, y0 + 34))
        s.append(T(x + cw / 2, y0 + 74, "buf[%d]" % i, "el m", "middle"))
    s.append(T(20, y0 + 33, "buf (8칸 배열)", "ln dk"))
    s.append('<g id="qdyn"></g>')
    s.append('<path class="wrapline" d="M%d,%d H%d V300 H%d V%d H%d" marker-end="url(#ah)"/>'
             % (x0 + 8 * cw, y0 + 27, x0 + 8 * cw + 30, x0 - 30, y0 + 27, x0 - 2))
    s.append(T(500, 294, "끝(7) 다음은 다시 처음(0)으로. 이 '돌아가기'를 % 연산으로 계산합니다", "el", "middle"))
    s.append(node("code", "queue_code", 820, 10, 160, 44, "코드로 보기", None, [], cls="codebtn"))
    return "0 0 1000 320", "".join(s)


DESC_QUEUE = """
<div class="qctl"><button data-act="offer">＋ 넣기 (offer)</button> <button data-act="poll">− 꺼내기 (poll)</button>
<button data-act="qreset">처음으로</button><span id="qmsg"></span></div>
<h3>대기열: 8칸짜리 원형 줄</h3>
<p>대기열은 칸이 8개인 배열(<code>buf</code>) 하나와 숫자 두 개로 되어 있습니다.</p>
<table>
<tr><th><code>head</code></th><td>가장 오래된 이벤트가 있는 칸 번호. 꺼낼 때(<code>poll</code>) 여기서 꺼내고 한 칸 앞으로 갑니다.</td></tr>
<tr><th><code>count</code></th><td>지금 기다리는 이벤트 개수. 새 이벤트는 <code>head</code>에서 <code>count</code>칸 뒤에 넣습니다(<code>offer</code>).</td></tr>
</table>
<p>이벤트를 꺼낼 때 배열 전체를 앞으로 당기지 않고 <code>head</code>만 옮깁니다. 그래서 칸 7 다음에는 다시 칸 0을 씁니다. 칸이 고리처럼 이어진 셈이라 <b>원형 대기열</b>이라고 부릅니다.
위 그림처럼 기다리는 이벤트가 배열 끝(6, 7)과 처음(0, 1)에 걸쳐 있을 수 있습니다. 위 단추로 넣고 꺼내 보면서 <code>head</code>가 7에서 0으로 넘어가는 순간을 보세요.</p>
<p>가득 찼을 때(<code>count = 8</code>) 넣으면 대기열은 아무것도 바꾸지 않고 <code>FULL</code>을 돌려줍니다. 그다음은 <a href="#" data-go="disp">접수</a>가 규칙대로 정합니다.</p>
<h3>변경 요청 두 건이 모두 이 클래스를 고칩니다</h3>
<table>
<tr><th>변경 요청 1 (실습 C)</th><td>"최대 32개까지 받게 해 달라." 가득 차면 더 큰 배열로 바꿉니다. 이때 고리 모양으로 걸쳐 있던 이벤트를 새 배열에 <b>순서대로</b> 옮기는지가 핵심입니다.</td></tr>
<tr><th>변경 요청 2 (실습 A, D)</th><td>"<code>%</code> 연산을 없애 달라." 위의 '7 다음은 0' 계산을 <code>%</code> 없이 해야 합니다.</td></tr>
</table>
"""


def lv_reg():
    s = []
    types = [("PWR_ON", "POWER_ON", 0), ("PWR_OFF", "POWER_OFF", 0), ("CYC_S", "CYCLE_START", 0), ("CYC_E", "CYCLE_END", 0),
             ("DOOR_O", "DOOR_OPEN", 0), ("DOOR_C", "DOOR_CLOSE", 0), ("HB", "HEARTBEAT", 0), ("TEMP", "TEMP_REPORT", 1),
             ("LEAK", "LEAK_DETECTED", 2), ("OVHT", "OVERHEAT", 2), ("그 밖", "UNKNOWN", 3)]
    hs = [(110, 70, "기기 상태 처리기", "DeviceStatusHandler"), (280, 50, "온도 처리기", "TemperatureHandler"),
          (336, 56, "안전 처리기", "SafetyHandler"), (400, 50, "개수 처리기", "CountingHandler")]
    s.append(T(40, 14, "이벤트 종류", "gl"))
    s.append(T(640, 14, "처리기", "gl"))
    for i, (code, name, h) in enumerate(types):
        y = 22 + i * 38
        s.append('<g class="node static"><rect x="40" y="%d" width="240" height="30" rx="15"/>%s%s</g>'
                 % (y, T(56, y + 20, code, "ln m"), T(270, y + 20, name, "el", "end")))
        hy, hh = hs[h][0], hs[h][1]
        ty = hy + hh / 2
        s.append('<path class="lnk" d="M280,%d C460,%d 460,%d 638,%d" marker-end="url(#ah)"/>' % (y + 15, y + 15, ty, ty))
    for y, h, t, c in hs:
        s.append(node("h" + c, "handlers", 640, y, 280, h, t, c, [], cls=""))
    s.append('<path class="lnk dash" d="M950,40 V420 H922" marker-end="url(#ah)"/>')
    s.append(T(956, 230, "모든 종류가", "el"))
    s.append(T(956, 244, "마지막에", "el"))
    s.append(T(956, 258, "여기도 거침", "el"))
    return "0 0 1040 460", "".join(s)


DESC_REG = """
<h3>처리기 고르기: 종류를 보고 처리기에 넘기기</h3>
<p>꺼낸 이벤트의 <b>종류</b>를 보고, 그 종류를 맡은 처리기에 넘깁니다. 그다음 종류와 상관없이 <b>개수 처리기</b>에도 넘깁니다.</p>
<p>어느 종류를 어느 처리기가 맡을지는 처리기 고르기 안에 적혀 있지 않습니다. HomeHub가 처음에 조립할 때(생성자) <code>register(종류, 처리기)</code>로 하나씩 등록합니다.
그래서 처리기 고르기의 코드에는 <code>handle(e)</code> 한 줄만 있고, 실제로 어느 처리기가 불리는지는 HomeHub 생성자를 봐야 알 수 있습니다.</p>
"""


def lv_handlers():
    s = []
    cards = [("기기 상태 처리기", "DeviceStatusHandler", ["맡는 종류: 전원 · 작동 · 문 · HB", "기기 상태를 아래 그림대로 바꿈", "무거운 가전은 작동 시작 전에", "전력 관리의 허락을 받음", "문 열림·닫힘과 그 시각을 적음"]),
             ("온도 처리기", "TemperatureHandler", ["맡는 종류: TEMP", "기기의 마지막 온도를 적음", "10°C 이상이면", "연속 고온 횟수 +1", "아니면 0으로 되돌림"]),
             ("안전 처리기", "SafetyHandler", ["맡는 종류: LEAK, OVHT", "누수: 작동 중인 세탁기·건조기를", "멈춤(ERROR)", "과열: 그 기기를 멈춤(ERROR)", "멈춘 기기는 전력 관리에서 뺌"]),
             ("개수 처리기", "CountingHandler", ["맡는 종류: 모든 종류", "다른 처리기 다음에 항상 불림", "evt.종류 개수를 1 셈", "(예: evt.temp_report)"])]
    for i, (t, c, lines) in enumerate(cards):
        x = 20 + i * 245
        s.append('<g class="node static"><rect x="%d" y="16" width="230" height="160" rx="6"/>%s%s%s</g>'
                 % (x, T(x + 12, 38, t, "tt"), T(x + 12, 54, c, "sub"),
                    "".join(T(x + 12, 78 + j * 18, ln, "ln") for j, ln in enumerate(lines))))
    s.append(T(20, 222, "기기 상태가 바뀌는 길 (DeviceStateMachine)", "gl"))
    st = [("OFF", "꺼짐", 110), ("IDLE", "켜져서 쉼", 370), ("RUNNING", "작동 중", 630), ("ERROR", "고장으로 멈춤", 890)]
    for code, ko, cx in st:
        s.append('<g class="node static state"><rect x="%d" y="300" width="160" height="56" rx="28"/>%s%s</g>'
                 % (cx - 80, T(cx, 324, code, "tt m", "middle"), T(cx, 343, ko, "el", "middle")))
    s.append(edge("s1", "M190,320 H288", "PWR_ON", 239, 312, "middle"))
    s.append(edge("s2", "M450,320 H548", "CYC_S", 499, 312, "middle"))
    s.append(edge("s3", "M550,342 H452", "CYC_E", 501, 360, "middle"))
    s.append(edge("s4", "M630,356 C630,400 890,400 890,358"))
    s.append(edge("s5", "M370,356 C370,474 890,474 890,358", "안전 처리기 (누수·과열)", 630, 470, "middle"))
    s.append(edge("s6", "M890,300 C890,250 110,250 110,298", "PWR_OFF (어느 상태에서든 꺼짐으로)", 500, 262, "middle"))
    return "0 0 1000 486", "".join(s)


DESC_HANDLERS = """
<h3>처리기 4개</h3>
<p>처리기는 이벤트 종류마다 실제 일을 하는 부품입니다. 처리기들은 서로 부르지 않습니다. 대신 오른쪽 아래의 같은 대상(기기 목록, 전력 관리, 로그, 개수)을 각자 읽고 바꿉니다.</p>
<h3>기기 상태가 바뀌는 길</h3>
<p>기기는 처음에 모두 꺼짐(OFF)입니다. 전원이 켜지면 쉼(IDLE), 작동을 시작하면 작동 중(RUNNING), 작동이 끝나면 다시 쉼으로 돌아옵니다.
누수나 과열이 생기면 안전 처리기가 고장으로 멈춤(ERROR)으로 바꿉니다. 고장 상태에서는 전원을 끄는 것(<code>PWR_OFF</code>)으로만 벗어납니다.</p>
<p><b>무거운 가전</b>(1,000W 이상: 세탁기, 건조기, 에어컨, 오븐)이 작동을 시작하려면 <a href="#" data-go="power">전력 관리</a>의 허락이 필요합니다. 허락을 못 받으면 상태가 그대로이고 로그에 <code>POWER_DENIED</code>가 남습니다.</p>
"""


def lv_rules():
    s = []
    s.append(T(20, 130, "이벤트 하나의 처리가", "el"))
    s.append(T(20, 144, "끝날 때마다 접수가 부름", "el"))
    s.append(edge("in", "M40,152 V178 H88"))
    s.append(card(90, 150, 180, 90, "규칙 검사", ["<tspan class='m'>afterDispatch(e)</tspan>", "규칙 세 개를 확인"]))
    rules = [(20, 100, "① 냉장고 과열", ["냉장고가 10°C 이상을 3번 연속 보고하면 과열 이벤트(OVHT)를 새로 만듦",
                                       "같은 냉장고는 온도가 내려가기 전까지 다시 만들지 않음 · 로그 RULE_OVERHEAT"]),
             (135, 80, "② 문 오래 열림", ["문이 열린 지 5분이 지났는데 HB가 오면 로그에 DOOR_LEFT_OPEN"]),
             (230, 80, "③ 건조기 추천", ["세탁기 작동이 끝났고 건조기가 쉬고 있으면 로그에 SUGGEST_DRYER"])]
    for y, h, t, lines in rules:
        s.append(card(320, y, 660, h, t, lines))
        s.append('<path class="lnk" d="M270,195 C295,195 295,%d 318,%d" marker-end="url(#ah)"/>' % (y + h / 2, y + h / 2))
    s.append(card(90, 340, 300, 70, "보관함 (outbox)", ["새로 만든 이벤트가 잠시 머무는 곳"]))
    s.append(edge("ob", "M180,240 V338", "규칙 ①이 만든 새 이벤트", 188, 292))
    s.append(edge("fl", "M390,375 H698", "HomeHub가 꺼내 다시 넣음 (flushDerived)", 544, 366, "middle"))
    s.append(node("d", "disp", 700, 340, 280, 70, "접수", "Dispatcher.submit", []))
    return "0 0 1000 430", "".join(s)


DESC_RULES = """
<h3>규칙 검사: 처리가 끝난 뒤 한 번 더 보기</h3>
<p>규칙 검사는 처리기와 따로 있습니다. 접수가 이벤트 하나를 처리기에 넘기고 나면 규칙 검사에 "방금 이 이벤트를 처리했다"고 알리고(<code>afterDispatch</code>), 규칙 검사는 <a href="#" data-go="devices">기기 목록</a>에서 그 기기의 상태를 읽어 규칙 세 개를 확인합니다.</p>
<p>규칙 ②, ③은 로그에 한 줄 적는 것으로 끝납니다. 규칙 ①은 <b>새 이벤트</b>를 만듭니다. 새 이벤트는 바로 처리되지 않고 보관함에 들어갔다가, HomeHub가 꺼내서(<code>flushDerived</code>) 접수에 넣습니다. 그러면 다른 이벤트처럼 대기열 맨 뒤에서 차례를 기다립니다.
HomeHub가 만든 이벤트는 가전이 보낸 것과 구별하려고 번호가 1000000부터 붙습니다.</p>
<p>규칙 ①이 보는 '연속 고온 횟수'는 <a href="#" data-go="handlers">온도 처리기</a>가 기기 목록에 적어 둔 값입니다.</p>
"""


DEVICES = [("washer-1", "세탁기", "WASHER", 2000, True, True), ("dryer-1", "건조기", "DRYER", 2500, True, True),
           ("fridge-1", "냉장고", "FRIDGE", 150, False, False), ("fridge-2", "냉장고", "FRIDGE", 150, False, False),
           ("aircon-1", "에어컨", "AIRCON", 1800, True, False), ("oven-1", "오븐", "OVEN", 2200, True, False),
           ("leak-1", "누수센서", "LEAK_SENSOR", 1, False, False), ("tv-1", "TV", "TV", 120, False, False)]


def lv_devices():
    s = []
    for i, (did, ko, kind, w, heavy, water) in enumerate(DEVICES):
        x, y = 20 + (i % 4) * 245, 16 + (i // 4) * 116
        tags = []
        if heavy:
            tags.append("무거운 가전")
        if water:
            tags.append("물 사용")
        s.append(card(x, y, 230, 104, did, ["%s · %s" % (ko, kind), "%sW" % format(w, ","), " · ".join(tags) or " "],
                      title_cls="tt m"))
    s.append(T(20, 266, "기기 하나(Device 객체)가 기억하는 것", "gl"))
    f = [("status", "상태: OFF / IDLE / RUNNING / ERROR (처음엔 OFF)"), ("lastSeen", "마지막으로 메시지를 받은 시각"),
         ("lastTemp", "마지막으로 보고된 온도(°C)"), ("consecutiveHighTemp", "연속 고온 횟수 (온도 처리기가 셈)"),
         ("doorOpen", "문이 열려 있나"), ("doorOpenedAt", "문을 연 시각"), ("firmware", "펌웨어 버전 (처음엔 1.0)")]
    s.append('<g class="node static wide"><rect x="20" y="276" width="960" height="150" rx="6"/></g>')
    for i, (k, v) in enumerate(f):
        x, y = 36 + (i % 2) * 480, 302 + (i // 2) * 30
        s.append(T(x, y, k, "ln m dk"))
        s.append(T(x + 190, y, v, "ln"))
    return "0 0 1000 440", "".join(s)


DESC_DEVICES = """
<h3>기기 목록: 기기 8대와 각 기기의 상태</h3>
<p>등록된 기기는 설정 파일의 <code>devices</code>에 적힌 8대입니다. 기기 목록(DeviceRegistry)은 이름(<code>fridge-1</code> 등)으로 기기 객체를 찾아 줍니다.
처리기와 규칙 검사가 여기서 기기를 찾아 상태를 읽고 바꿉니다.</p>
<ul>
<li><b>무거운 가전</b>(1,000W 이상)은 작동을 시작할 때 <a href="#" data-go="power">전력 관리</a>의 허락을 받아야 합니다.</li>
<li><b>물 사용</b> 가전(세탁기, 건조기)은 누수가 감지되면 안전 처리기가 멈춥니다.</li>
<li>모든 기기를 달라고 하면(<code>all()</code>) 이름의 알파벳순으로 정렬해서 줍니다(aircon-1, dryer-1, fridge-1, …). 상태 한 줄에 기기가 나오는 순서, 누수 때 안전 처리기가 기기를 멈추는 순서가 이 순서입니다.</li>
</ul>
"""


def lv_power():
    s = []
    k, x0 = 0.15, 60
    cap = x0 + 4000 * k

    def bar(y, segs, label):
        out = [T(20, y - 12, label, "gl")]
        x = x0
        out.append('<rect class="track" x="%d" y="%d" width="%d" height="40"/>' % (x0, y, 4000 * k))
        for name, w, cls in segs:
            out.append('<rect class="seg %s" x="%d" y="%d" width="%d" height="40"/>' % (cls, x, y, w * k))
            out.append(T(x + w * k / 2, y + 25, "%s %sW" % (name, format(w, ",")), "ln dk", "middle"))
            x += w * k
        return "".join(out)

    s.append(bar(50, [("세탁기", 2000, ""), ("에어컨", 1800, "")], "지금 작동 중인 무거운 가전 (running)"))
    s.append(bar(160, [("세탁기", 2000, ""), ("에어컨", 1800, ""), ("오븐", 2200, "over")], "오븐(2,200W)이 작동을 시작하려 함"))
    s.append('<line class="cap" x1="%d" y1="30" x2="%d" y2="215"/>' % (cap, cap))
    s.append(T(cap + 6, 40, "상한 4,000W", "el"))
    s.append(T(20, 240, "3,800 + 2,200 = 6,000W → 상한을 넘으므로 거부. 오븐은 쉼(IDLE) 상태 그대로, 로그에 POWER_DENIED", "ln dk"))
    s.append(T(20, 280, "가벼운 가전(냉장고 150W, TV 120W, 누수센서 1W)은 허락 없이 작동하고, 이 합계에도 넣지 않습니다.", "ln"))
    return "0 0 1000 300", "".join(s)


DESC_POWER = """
<h3>전력 관리: 동시에 쓰는 전력을 4,000W 이하로</h3>
<p>집의 차단기가 내려가지 않도록, 동시에 작동하는 무거운 가전의 전력 합을 4,000W 이하로 지킵니다.
지금 작동 중인 무거운 가전과 그 전력은 <code>running</code>이라는 표에 적어 둡니다.</p>
<table>
<tr><th><code>tryStart(기기, W)</code></th><td>"이 기기를 작동시켜도 되나?" 합이 4,000W를 넘지 않으면 <code>running</code>에 적고 허락합니다. 넘으면 거부합니다. 기기 상태 처리기가 무거운 가전의 작동 시작(<code>CYC_S</code>) 때 부릅니다.</td></tr>
<tr><th><code>stop(기기)</code></th><td><code>running</code>에서 뺍니다. 작동이 끝나거나 안전 처리기가 기기를 멈출 때 부릅니다.</td></tr>
</table>
<p>예를 들어 세탁기(2,000W)와 건조기(2,500W)는 합이 4,500W라 동시에 돌 수 없습니다.</p>
"""


def lv_watch():
    s = []
    seq = [7, 6, 3, 6, 8, 7]
    cnt = [1, 2, 0, 1, 2, 3]
    for i, (n, c) in enumerate(zip(seq, cnt)):
        x = 60 + i * 150
        s.append(T(x + 30, 24, "점검 %d" % (i + 1), "tt", "middle"))
        for j in range(8):
            on = j < n
            s.append('<rect class="cell%s" x="%d" y="%d" width="60" height="14"/>' % (" on" if on else "", x, 160 - j * 16))
        s.append('<line class="cap" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (x - 6, 160 - 5 * 16 - 1, x + 66, 160 - 5 * 16 - 1))
        s.append(T(x + 30, 196, "%d개" % n, "ln dk", "middle"))
        s.append(T(x + 30, 216, "6개 이상 ✓" if n >= 6 else "6개 미만", "el" + ("" if n >= 6 else " mu"), "middle"))
        s.append(T(x + 30, 244, "연속 %d번" % c, "tt" + (" alarm" if c >= 3 else ""), "middle"))
    s.append(T(36, 82, "75%", "el", "end"))
    s.append(T(36, 96, "(6칸)", "el", "end"))
    s.append('<g class="node static alarmbox"><rect x="740" y="262" width="240" height="44" rx="6"/>%s</g>'
             % T(860, 289, "3번 연속 → '막혔다' → 복구", "ln dk", "middle"))
    s.append(T(20, 340, "복구 (RecoveryManager): 중요 이벤트만 남기고 나머지는 버림", "gl"))
    before = ["5", "6", "누수", "8", "과열", "10", "11"]
    for i, b in enumerate(before):
        crit = not b.isdigit()
        s.append('<rect class="cell%s" x="%d" y="356" width="64" height="34"/>' % (" crit" if crit else " on", 20 + i * 66, ))
        s.append(T(52 + i * 66, 378, b, "ln dk", "middle"))
    s.append(edge("rc", "M490,373 H560"))
    for i, b in enumerate(["누수", "과열"]):
        s.append('<rect class="cell crit" x="%d" y="356" width="64" height="34"/>' % (570 + i * 66))
        s.append(T(602 + i * 66, 378, b, "ln dk", "middle"))
    s.append(T(20, 414, "버린 이벤트마다 로그에 RECOVERY_DROP, 끝나면 RECOVER:kept=2,dropped=5", "el"))
    return "0 0 1000 430", "".join(s)


DESC_WATCH = """
<h3>점검과 복구: 대기열이 막혔을 때</h3>
<p>처리가 어딘가에서 멈추면 대기열이 줄지 않고 계속 꽉 차 있게 됩니다. <b>점검</b>(Watchdog, '감시견')은 이것을 알아채는 부품입니다.</p>
<ol>
<li>HomeHub는 1초마다 <code>tick()</code>을 부르고, 그때마다 점검이 대기열을 한 번 봅니다.</li>
<li>대기열이 <b>75% 이상</b>(8칸 중 <b>6개 이상</b>) 차 있으면 '꽉 찬 점검' 횟수를 1 늘립니다. 6개 미만이면 0으로 되돌립니다. (위 그림의 점검 3처럼)</li>
<li>이 횟수가 <b>3</b>이 되면, 즉 <b>점검 3번 연속으로 대기열이 6개 이상 차 있으면</b> "처리가 멈췄다"고 판단합니다. 로그에 <code>WATCHDOG</code>를 적고 횟수를 0으로 되돌립니다.</li>
<li>HomeHub가 <b>복구</b>(RecoveryManager)를 부릅니다. 복구는 대기열에서 중요 이벤트(누수, 과열)만 남기고 나머지를 버립니다.</li>
</ol>
<p>'75%'는 대기열 칸 수(<code>capacity()</code>, 지금은 8)에 대한 비율입니다. 계산식은 <code>size() * 4 &gt;= capacity() * 3</code>입니다. 3번이라는 기준은 설정 <code>watchdog.threshold</code>입니다.</p>
"""


def lv_logs():
    s = []
    rows = [("STATE:fridge-1:OFF->IDLE", "기기 상태 처리기", "fridge-1이 꺼짐 → 쉼으로 바뀜"),
            ("RULE_OVERHEAT:10@fridge-1", "규칙 검사", "10번 이벤트를 보고 과열 규칙이 걸림"),
            ("OVERHEAT_ALARM:1000000@fridge-1", "안전 처리기", "1000000번(과열) 이벤트로 fridge-1을 멈춤"),
            ("REJECT:42@tv-1", "접수", "대기열이 가득 차서 42번 메시지를 거부"),
            ("WATCHDOG:stuck size=7", "점검", "대기열이 막혔다고 판단 (7개 대기 중)")]
    s.append('<rect class="term" x="20" y="16" width="960" height="%d" rx="6"/>' % (len(rows) * 40 + 20))
    for i, (line, who, what) in enumerate(rows):
        y = 46 + i * 40
        s.append(T(40, y, E(line), "ln m dk"))
        s.append(T(440, y, who, "tt"))
        s.append(T(580, y, what, "ln"))
    return "0 0 1000 240", "".join(s)


DESC_LOGS = """
<h3>로그: 무슨 일이 있었는지 적은 기록</h3>
<p>부품들이 중요한 일을 할 때마다 로그(AuditLog)에 한 줄씩 적습니다. 줄 모양은 두 가지입니다.</p>
<ul>
<li><code>태그:이벤트번호@기기</code> — 어떤 이벤트 때문에 생긴 일. 예: <code>REJECT:42@tv-1</code></li>
<li><code>태그:내용</code> — 그 밖의 일. 예: <code>STATE:fridge-1:OFF->IDLE</code></li>
</ul>
<p>최근 500줄만 남기고 오래된 것부터 지웁니다. 상태 한 줄에는 마지막 3줄이 나옵니다.</p>
<table>
<tr><th>누가 적나</th><th>태그</th></tr>
<tr><td>접수</td><td><code>EVICT</code>(자리를 만들려고 뺌), <code>REJECT</code>(거부)</td></tr>
<tr><td>기기 상태 처리기</td><td><code>STATE</code>(상태 바뀜), <code>POWER_DENIED</code>(전력 허락 못 받음), <code>UNKNOWN_DEVICE</code>(모르는 기기)</td></tr>
<tr><td>안전 처리기</td><td><code>VALVE_CLOSE</code>(누수: 물 잠금), <code>SAFETY_STOP</code>(기기 멈춤), <code>OVERHEAT_ALARM</code>(과열 경보)</td></tr>
<tr><td>규칙 검사</td><td><code>RULE_OVERHEAT</code>, <code>DOOR_LEFT_OPEN</code>, <code>SUGGEST_DRYER</code></td></tr>
<tr><td>점검 · 복구</td><td><code>WATCHDOG</code>, <code>RECOVERY_DROP</code>(버린 이벤트), <code>RECOVER</code>(복구 끝)</td></tr>
</table>
"""


def lv_metrics():
    s = []
    rows = [("submit.accepted = 12", "대기열에 받아들인 이벤트 수"), ("dispatch.count = 12", "꺼내서 처리한 이벤트 수"),
            ("evt.temp_report = 8", "온도 보고 이벤트 수 (개수 처리기가 종류마다 셈)"), ("temp.reports = 8", "온도 처리기가 처리한 수"),
            ("safety.overheat = 1", "안전 처리기가 처리한 과열 수")]
    s.append('<rect class="term" x="20" y="16" width="960" height="%d" rx="6"/>' % (len(rows) * 40 + 20))
    for i, (a, b) in enumerate(rows):
        y = 46 + i * 40
        s.append(T(40, y, a, "ln m dk"))
        s.append(T(440, y, b, "ln"))
    return "0 0 1000 240", "".join(s)


DESC_METRICS = """
<h3>개수 세기: 이름별로 몇 번 일어났나</h3>
<p>개수 세기(Metrics)는 이름표가 붙은 카운터 모음입니다. 부품들이 어떤 일을 할 때 그 이름의 숫자를 1씩 늘립니다(<code>increment("submit.accepted")</code>).
"지금까지 몇 개를 받았고, 몇 개를 거부했고, 경보가 몇 번 났나"를 숫자로 보려는 것입니다. 상태 한 줄의 <code>metrics={…}</code>에 이름순으로 모두 나옵니다.</p>
<table>
<tr><th>이름</th><th>언제 1 늘어나나</th></tr>
<tr><td><code>submit.accepted</code> · <code>submit.rejected</code> · <code>submit.evicted</code> · <code>submit.drained</code></td><td>접수가 받음 · 거부 · 하나 빼고 받음 · 하나 처리하고 받음</td></tr>
<tr><td><code>queue.full</code></td><td>대기열이 가득 찬 상태에서 이벤트가 들어옴</td></tr>
<tr><td><code>dispatch.count</code></td><td>이벤트 하나를 꺼내 처리함</td></tr>
<tr><td><code>evt.종류</code></td><td>그 종류의 이벤트를 처리함 (개수 처리기)</td></tr>
<tr><td><code>temp.reports</code> · <code>safety.leak</code> · <code>safety.overheat</code> · <code>power.denied</code></td><td>각 처리기가 해당 일을 함</td></tr>
<tr><td><code>recovery.count</code> · <code>ingest.dropped</code></td><td>복구함 · 형식이 틀린 메시지를 버림</td></tr>
</table>
"""


def lv_config():
    s = []
    rows = [("queue.capacity=8", "대기열 칸 수"), ("dispatch.autoDrainOnFull=false", "가득 찼을 때 비중요 이벤트를 거부 (R4)"),
            ("power.capWatts=4000", "동시 전력 상한 (W)"), ("watchdog.threshold=3", "점검 몇 번 연속 꽉 차면 '막힘'인가"),
            ("temp.highCelsius=10", "이 온도 이상이면 고온"), ("rules.overheatAfterReports=3", "고온 몇 번 연속이면 과열 이벤트"),
            ("rules.doorOpenAlertMillis=300000", "문이 이만큼(5분) 열려 있으면 로그"), ("devices=washer-1:WASHER,…", "등록할 기기 8대")]
    s.append('<rect class="term" x="20" y="16" width="960" height="%d" rx="6"/>' % (len(rows) * 36 + 20))
    for i, (a, b) in enumerate(rows):
        y = 44 + i * 36
        s.append(T(40, y, E(a), "ln m dk"))
        s.append(T(480, y, b, "ln"))
    return "0 0 1000 330", "".join(s)


DESC_CONFIG = """
<h3>설정: hub.properties</h3>
<p>HomeHub가 시작할 때 읽는 설정입니다. 파일이 없으면 위의 기본값을 씁니다(<code>HubConfig</code>). 실습은 모두 기본값으로 돌립니다.</p>
<p>실습 C의 패치 B는 여기에 없던 <code>dispatch.maxPending</code>이라는 키를 새로 만듭니다.</p>
"""


# ------------------------------------------------------------------ level 4: code
CODE_QUEUE = """<div class="code"><pre><span class="c">// 넣기: head에서 count칸 뒤에 넣는다. 끝을 넘으면 % 로 처음부터 센다</span>
public OfferResult offer(Event e) {
    if (e == null) return OfferResult.REJECTED;
    if (count == buf.length) return OfferResult.FULL;     <span class="c">// 가득 참: 아무것도 바꾸지 않음</span>
    buf[<b>(head + count) % buf.length</b>] = e;
    count++;
    return OfferResult.OK;
}

<span class="c">// 꺼내기: head 칸에서 꺼내고 head를 한 칸 앞으로. 7 다음은 0</span>
public Event poll() {
    if (count == 0) return null;
    Event e = buf[head];
    buf[head] = null;
    head = <b>(head + 1) % buf.length</b>;
    count--;
    return e;
}

public int size()     { return count; }        <span class="c">// 점검이 쓰는 값</span>
public int capacity() { return buf.length; }   <span class="c">// 점검이 쓰는 값 (지금은 항상 8)</span></pre></div>"""

DESC_QUEUE_CODE = """
<h3>대기열 코드 (legacy/…/queue/RingEventQueue.java)</h3>
<p>굵게 표시한 두 곳이 '7 다음은 0' 계산입니다. 변경 요청 2는 이 <code>%</code>를 없애 달라는 것이고, 변경 요청 1은 <code>buf</code>를 더 큰 배열로 바꾸게 됩니다.
<code>size()</code>와 <code>capacity()</code>는 <a href="#" data-go="watch">점검</a>이 '75% 이상 찼나'를 계산할 때 씁니다.</p>
"""

CODE_DISP = """<div class="code"><pre>public SubmitResult submit(Event e) {
    OfferResult r = queue.offer(e);
    if (r == OfferResult.OK) return ACCEPTED;                 <span class="c">// 빈 칸이 있었음</span>
    <span class="c">// 여기부터는 대기열이 가득 찬 경우</span>
    if (e.isCritical()) {                                     <span class="c">// 중요 이벤트 (R2)</span>
        Event victim = evictOldestNonCritical();              <span class="c">// 가장 오래된 비중요를 뺌 (R3)</span>
        if (victim != null) { audit.record("EVICT", victim); queue.offer(e); return ACCEPTED_EVICTED; }
        dispatchOne(); queue.offer(e); return ACCEPTED_DRAINED;  <span class="c">// 모두 중요: 하나 처리해 자리 만듦</span>
    }
    if (autoDrainOnFull) { dispatchOne(); queue.offer(e); return ACCEPTED_DRAINED; }   <span class="c">// R4</span>
    audit.record("REJECT", e); return REJECTED_FULL;           <span class="c">// R4: 기본은 거부</span>
}

<span class="c">// 대기열을 한 바퀴 돌리면서(꺼내서 다시 넣기) 처음 만난 비중요 하나만 다시 넣지 않는다.</span>
<span class="c">// 나머지의 순서는 그대로 (R3)</span>
Event evictOldestNonCritical() { … }

public Event dispatchOne() {
    Event e = queue.poll();
    if (e == null) return null;
    handlers.dispatch(e);                <span class="c">// 처리기 고르기 → 처리기</span>
    listener.afterDispatch(e);           <span class="c">// 규칙 검사에 알림</span>
    return e;
}</pre></div>"""

DESC_DISP_CODE = """
<h3>접수 코드 (legacy/…/dispatch/Dispatcher.java, 줄였음)</h3>
<p>개수 세기(<code>metrics.increment</code>) 줄은 빼고 흐름만 남겼습니다. 위의 결정 그림과 한 줄씩 대응합니다.</p>
"""


# ------------------------------------------------------------------ assemble
LEVELS = {}


def add(lid, title, crumb, parent, view, desc):
    if isinstance(view, tuple):
        LEVELS[lid] = dict(title=title, crumb=crumb, parent=parent, vb=view[0], svg=view[1], desc=desc)
    else:
        LEVELS[lid] = dict(title=title, crumb=crumb, parent=parent, html=view, desc=desc)


add("outside", "바깥에서 본 HomeHub", "HomeHub 바깥", None, lv_outside(), DESC_OUTSIDE)
add("inside", "HomeHub 안의 부품", "HomeHub 안", "outside", lv_inside(), DESC_INSIDE)
add("config", "설정", "설정", "outside", lv_config(), DESC_CONFIG)
add("hub", "HomeHub: 조립과 진행", "HomeHub 객체", "inside", lv_hub(), DESC_HUB)
add("parser", "입구 (EventParser)", "입구", "inside", lv_parser(), DESC_PARSER)
add("disp", "접수·꺼내기 (Dispatcher)", "접수·꺼내기", "inside", lv_disp(), DESC_DISP)
add("disp_code", "접수 코드", "코드", "disp", CODE_DISP, DESC_DISP_CODE)
add("queue", "대기열 (RingEventQueue)", "대기열", "inside", lv_queue(), DESC_QUEUE)
add("queue_code", "대기열 코드", "코드", "queue", CODE_QUEUE, DESC_QUEUE_CODE)
add("reg", "처리기 고르기 (HandlerRegistry)", "처리기 고르기", "inside", lv_reg(), DESC_REG)
add("handlers", "처리기 4개", "처리기", "inside", lv_handlers(), DESC_HANDLERS)
add("rules", "규칙 검사 (RuleEngine)", "규칙 검사", "inside", lv_rules(), DESC_RULES)
add("devices", "기기 목록 (DeviceRegistry)", "기기 목록", "inside", lv_devices(), DESC_DEVICES)
add("power", "전력 관리 (PowerBudget)", "전력 관리", "inside", lv_power(), DESC_POWER)
add("watch", "점검과 복구 (Watchdog, RecoveryManager)", "점검·복구", "inside", lv_watch(), DESC_WATCH)
add("logs", "로그 (AuditLog)", "로그", "inside", lv_logs(), DESC_LOGS)
add("metrics", "개수 세기 (Metrics)", "개수 세기", "inside", lv_metrics(), DESC_METRICS)

# fill tour defaults: each step inherits the previous step's state
state = {}
for st in TOUR:
    for k in ("q", "fr", "hot", "box", "log"):
        if k in st:
            state[k] = st[k]
        else:
            st[k] = state[k]

CSS = r"""
:root{--paper:#FBFCFD;--sheet:#FFFFFF;--ink:#18212B;--muted:#5B6773;--rule:#D9DFE6;--rule2:#EEF1F4;
  --accent:#1F5F8B;--accent-tint:#E9F1F7;--ok:#2D7A4C;--ok-tint:#E7F3EB;--bad:#B83227;--bad-tint:#FCEBE9;
  --chg:#9A6512;--chg-tint:#FFF3D9;--code:#F4F6F8;--ext:#F3F5F7;
  --sans:"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",system-ui,sans-serif;
  --mono:"D2Coding","JetBrains Mono","SF Mono",Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root{--paper:#11161C;--sheet:#171E26;--ink:#E4E9EE;--muted:#9AA6B2;--rule:#2C3743;
  --rule2:#212A34;--accent:#7DB4DD;--accent-tint:#1B2B39;--ok:#6CC08F;--ok-tint:#17291F;--bad:#F08A7E;--bad-tint:#36191A;
  --chg:#E2B259;--chg-tint:#33270F;--code:#1C242D;--ext:#1C242D}}
*{box-sizing:border-box}
html{background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.65}
body{margin:0}
a{color:var(--accent)}
.wrap{max-width:1100px;margin:0 auto;padding:22px 22px 60px}
h1{font-size:25px;margin:0 0 4px}
.lead{color:var(--muted);margin:0 0 14px;max-width:80ch}
.bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 0;border-top:1px solid var(--rule);
  border-bottom:1px solid var(--rule);margin:0 0 10px;font-size:14px}
.bar #crumbs a{text-decoration:none}
.bar #crumbs b{color:var(--ink)}
.bar .sp{flex:1}
button{font:inherit;font-size:13.5px;padding:4px 12px;border:1px solid var(--rule);background:var(--sheet);color:var(--ink);
  border-radius:4px;cursor:pointer}
button:hover{border-color:var(--accent);color:var(--accent)}
button:disabled{opacity:.4;cursor:default;border-color:var(--rule);color:var(--ink)}
button.big{font-size:15px;font-weight:700;padding:7px 16px;background:var(--accent);color:#fff;border-color:var(--accent)}
button.big:hover{color:#fff;opacity:.9}
h2#ltitle{font-size:19px;margin:6px 0 6px}
.stagewrap{overflow:hidden;background:var(--sheet);border:1px solid var(--rule);border-radius:6px}
#stage{padding:8px}
#stage svg{width:100%;height:auto;display:block}
#desc{margin-top:14px}
#desc h3{font-size:16px;margin:20px 0 6px}
#desc p,#desc li{max-width:84ch}
.next{color:var(--accent);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--sheet);margin:6px 0 12px}
th,td{text-align:left;vertical-align:top;padding:6px 10px;border-bottom:1px solid var(--rule2)}
th{font-weight:600;white-space:nowrap;color:var(--ink)}
code{font-family:var(--mono);font-size:13px}
pre{font-family:var(--mono);font-size:13px;line-height:1.55;background:var(--code);border:1px solid var(--rule);padding:10px 14px;
  overflow-x:auto;margin:6px 0 12px}
.code pre{margin:0;background:transparent;border:0;font-size:13.5px}
.code pre b{background:var(--chg-tint);color:var(--chg)}
.code .c{color:var(--muted)}
.hint2{font-size:13px;color:var(--muted);margin:0 0 8px}
/* tour panel */
.tour{border:2px solid var(--accent);border-radius:6px;padding:12px 16px;background:var(--accent-tint)}
.tour .hd{display:flex;gap:10px;align-items:center;margin:0 0 6px;font-weight:700}
.tour .txt{font-size:15px;margin:0 0 10px;min-height:3.2em}
.tour .st{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13.5px;margin:0 0 10px}
.tour .st span b{font-family:var(--mono);font-size:13px}
.chip{display:inline-block;font-family:var(--mono);font-size:12.5px;padding:0 6px;border:1px solid var(--rule);border-radius:3px;
  background:var(--sheet);margin-right:3px}
.chip.crit{border-color:var(--chg);color:var(--chg)}
.qctl{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 8px}
#qmsg{font-size:13.5px;color:var(--muted);margin-left:6px}
#qmsg code{color:var(--ink)}
/* svg */
svg text{font-family:var(--sans);fill:var(--ink)}
svg .tt{font-size:14px;font-weight:700}
svg .sub{font-family:var(--mono);font-size:11.5px;fill:var(--muted);font-weight:400}
svg .ln{font-size:12.5px;fill:var(--muted)}
svg .dk{fill:var(--ink)}
svg .m{font-family:var(--mono)}
svg .mu{fill:var(--muted)}
svg .big{font-size:16px}
svg .el{font-size:11.5px;fill:var(--muted)}
svg .gl{font-size:13px;font-weight:700;fill:var(--muted)}
svg .zoom{font-size:16px;fill:var(--accent)}
svg .hint{fill:var(--accent);font-weight:600}
svg .alarm{fill:var(--bad)}
.node rect,.node polygon{fill:var(--sheet);stroke:var(--ink);stroke-width:1.2}
.node.ext rect{fill:var(--ext);stroke:var(--muted)}
.node.main rect{fill:var(--accent-tint);stroke:var(--accent);stroke-width:1.6}
.node.big .tt{font-size:20px}
.node.mono-title .tt{font-family:var(--mono);font-size:13.5px}
.node.ok rect{fill:var(--ok-tint);stroke:var(--ok)}
.node.bad rect{fill:var(--bad-tint);stroke:var(--bad)}
.node.start rect{fill:var(--accent-tint);stroke:var(--accent)}
.node.dia polygon{fill:var(--sheet);stroke:var(--accent)}
.node.state rect{fill:var(--accent-tint);stroke:var(--accent)}
.node.alarmbox rect{fill:var(--bad-tint);stroke:var(--bad)}
.node.codebtn rect{fill:var(--chg-tint);stroke:var(--chg)}
.node.codebtn .tt{fill:var(--chg)}
.node.codebtn .zoom{fill:var(--chg)}
.node[data-go]{cursor:pointer}
.node[data-go]:hover rect{stroke:var(--accent);stroke-width:2.6}
.grp{fill:none;stroke:var(--muted);stroke-dasharray:5 4}
.edge path,.lnk,.wrapline{fill:none;stroke:var(--muted);stroke-width:1.5;marker-end:url(#ah)}
.edge.dash path,.lnk.dash{stroke-dasharray:6 4}
.ahd{fill:var(--muted)} .ahd2{fill:var(--accent)}
.cell{fill:var(--sheet);stroke:var(--ink);stroke-width:1.1}
.cell.on{fill:var(--accent-tint)}
.cell.crit{fill:var(--chg-tint);stroke:var(--chg)}
.cell.hi{stroke:var(--accent);stroke-width:3}
.qc{fill:var(--sheet);stroke:var(--muted)}
.qc.on{fill:var(--accent)} .qc.crit{fill:var(--chg)}
.term{fill:var(--code);stroke:var(--rule)}
.track{fill:var(--rule2);stroke:var(--rule)}
.seg{fill:var(--accent-tint);stroke:var(--accent)}
.seg.over{fill:var(--bad-tint);stroke:var(--bad);stroke-dasharray:5 3}
.cap{stroke:var(--bad);stroke-width:2;stroke-dasharray:4 3}
.mk{stroke:var(--accent);stroke-width:2;marker-end:url(#ah2)}
.mkt{fill:var(--accent);font-size:13px;font-weight:700}
/* tour highlighting */
svg.touring .node,svg.touring .edge,svg.touring .grp,svg.touring .gl{opacity:.22;transition:opacity .25s}
svg.touring .on{opacity:1}
svg.touring .edge.on path{stroke:var(--accent);stroke-width:2.6;marker-end:url(#ah2)}
svg.touring .node.on rect{stroke:var(--accent);stroke-width:2.6}
.token{fill:var(--chg);stroke:var(--sheet);stroke-width:2}
"""

JS = r"""
const NS='http://www.w3.org/2000/svg';
const DEFS='<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ahd"/></marker><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ahd2"/></marker></defs>';
const stage=document.getElementById('stage'), desc=document.getElementById('desc');
let cur=null, tourAt=-1, gen=0;
function chain(id){const p=[];while(id){p.unshift(id);id=L[id].parent;}return p;}
function notify(){try{document.dispatchEvent(new Event('toggle'));}catch(e){}}
function render(id){
  const lv=L[id]; cur=id; tourAt=-1; gen++;
  stage.innerHTML = lv.svg ? '<svg viewBox="'+lv.vb+'">'+DEFS+lv.svg+'</svg>' : lv.html;
  desc.innerHTML = lv.desc;
  document.getElementById('ltitle').textContent = lv.title;
  document.getElementById('crumbs').innerHTML = chain(id).map((p,i,a)=> i<a.length-1 ?
     '<a href="#" data-go="'+p+'">'+L[p].crumb+'</a>' : '<b>'+L[p].crumb+'</b>').join(' › ');
  document.getElementById('out').disabled = !lv.parent;
  if (INIT[id]) INIT[id]();
  notify();
}
function centerOf(el){const r=el.getBoundingClientRect(),s=stage.getBoundingClientRect();
  return (r.left+r.width/2-s.left)+'px '+(r.top+r.height/2-s.top)+'px';}
function go(id, from){
  if(!L[id]||id===cur) return;
  const inward = chain(id).indexOf(cur)>=0 || (from && from.closest && from.closest('svg'));
  stage.style.transformOrigin = from && from.closest && from.closest('#stage') ? centerOf(from) : '50% 50%';
  const prev=cur, still=!stage.animate||matchMedia('(prefers-reduced-motion: reduce)').matches;
  let done=false, leave=null;
  const swap=()=>{
    if(done) return; done=true;
    if(leave) leave.cancel();
    render(id);
    if(still) return;
    let o='50% 50%';
    if(!inward){const n=stage.querySelector('[data-go="'+prev+'"]'); if(n) o=centerOf(n);}
    stage.style.transformOrigin=o;
    const enter=stage.animate([{transform:inward?'scale(.45)':'scale(2.4)',opacity:0},{transform:'scale(1)',opacity:1}],
                              {duration:320,easing:'ease-out'});
    setTimeout(()=>{ if(enter.playState!=='finished') enter.cancel(); },700);   // never leave the map invisible
  };
  if(still){swap();return;}
  leave=stage.animate([{transform:'scale(1)',opacity:1},{transform:inward?'scale(2.4)':'scale(.55)',opacity:0}],
                      {duration:260,easing:'ease-in',fill:'forwards'});
  leave.onfinish=swap;
  setTimeout(swap,400);   // in case animations do not run (hidden tab, some webviews)
}
/* ---------- tour ---------- */
function tourShow(i){
  const svg=stage.querySelector('svg'); if(!svg) return;
  tourAt=i; const s=TOUR[i]; const my=++gen;
  svg.classList.add('touring');
  svg.querySelectorAll('.on').forEach(e=>e.classList.remove('on'));
  s.on.forEach(id=>{const e=svg.getElementById(id); if(e) e.classList.add('on');});
  for(let k=0;k<8;k++){const c=svg.getElementById('qc'+k); if(!c) continue; const v=s.q[k];
    c.setAttribute('class','qc'+(v===undefined?'':(v[0]==='!'?' crit':' on')));}
  const chips=a=>a.length?a.map(v=>'<span class="chip'+(v[0]==='!'?' crit':'')+'">#'+v.replace('!','')+'</span>').join(''):'<span class="chip">비어 있음</span>';
  desc.innerHTML='<div class="tour"><div class="hd">메시지 하나 따라가기 <span style="font-weight:400;color:var(--muted)">'+(i+1)+' / '+TOUR.length+'</span></div>'+
    '<p class="txt">'+s.t+'</p><div class="st"><span>대기열 '+chips(s.q)+'</span><span>보관함 '+chips(s.box)+'</span>'+
    '<span>fridge-1 상태 <b>'+s.fr+'</b></span><span>연속 고온 횟수 <b>'+s.hot+'</b></span><span>로그 마지막 줄 <b>'+s.log+'</b></span></div>'+
    '<button data-act="prev"'+(i===0?' disabled':'')+'>◀ 이전</button> '+
    (i<TOUR.length-1?'<button class="big" data-act="next">다음 ▶</button> ':'<button class="big" data-act="tour">처음부터 다시</button> ')+
    '<button data-act="stop">그만 보기</button></div>';
  moveTokens(svg,s.mv,my); notify();
}
function moveTokens(svg,ids,my){
  svg.querySelectorAll('.token').forEach(t=>t.remove());
  if(!ids.length) return;
  const dot=document.createElementNS(NS,'circle'); dot.setAttribute('r',7); dot.setAttribute('class','token'); svg.appendChild(dot);
  let i=0;
  (function nextEdge(){
    if(my!==gen||i>=ids.length){ if(my===gen) setTimeout(()=>dot.remove(),250); return; }
    const p=svg.querySelector('#'+ids[i++]+' path'); if(!p){nextEdge();return;}
    const len=p.getTotalLength(), dur=Math.max(380,len*3.2), t0=performance.now();
    (function f(t){ if(my!==gen){dot.remove();return;}
      const k=Math.min(1,(t-t0)/dur), pt=p.getPointAtLength(len*k);
      dot.setAttribute('cx',pt.x); dot.setAttribute('cy',pt.y);
      if(k<1) requestAnimationFrame(f); else nextEdge(); })(performance.now());
  })();
}
function tourStop(){render(cur);}
/* ---------- queue playground ---------- */
const Q={};
function qreset(){Q.buf=new Array(8).fill(null);Q.buf[6]=21;Q.buf[7]=22;Q.buf[0]=23;Q.buf[1]=24;Q.head=6;Q.count=4;Q.seq=25;
  qdraw(null,'처음 상태: head = 6, count = 4. 기다리는 이벤트가 6, 7, 0, 1칸에 걸쳐 있습니다.');}
function qdraw(hit,msg){
  const svg=stage.querySelector('svg'); if(!svg) return;
  for(let i=0;i<8;i++){svg.getElementById('rt'+i).textContent=Q.buf[i]===null?'':'#'+Q.buf[i];
    svg.getElementById('rc'+i).setAttribute('class','cell'+(Q.buf[i]===null?'':' on')+(i===hit?' hi':''));}
  const cw=84,x0=150,hx=x0+Q.head*cw+cw/2, nx=x0+((Q.head+Q.count)%8)*cw+cw/2;
  let g='<line class="mk" x1="'+hx+'" y1="62" x2="'+hx+'" y2="104"/><text class="mkt" x="'+hx+'" y="54" text-anchor="middle">head = '+Q.head+' (가장 오래된 것)</text>';
  if(Q.count<8) g+='<line class="mk" x1="'+nx+'" y1="232" x2="'+nx+'" y2="192"/><text class="mkt" x="'+nx+'" y="250" text-anchor="middle">다음 넣을 칸 = (head + count) % 8 = '+((Q.head+Q.count)%8)+'</text>';
  else g+='<text class="mkt" x="500" y="250" text-anchor="middle">가득 참 (count = 8)</text>';
  g+='<text class="el" x="'+(x0+8*cw+40)+'" y="137">count = '+Q.count+'</text>';
  svg.getElementById('qdyn').innerHTML=g;
  const m=document.getElementById('qmsg'); if(m) m.innerHTML=msg||'';
  notify();
}
function qoffer(){ if(Q.count===8){qdraw(null,'가득 찼습니다. <code>offer</code>는 아무것도 바꾸지 않고 <code>FULL</code>을 돌려줍니다.');return;}
  const k=(Q.head+Q.count)%8; Q.buf[k]=Q.seq++; Q.count++;
  qdraw(k,'넣기: <code>buf[('+Q.head+' + '+(Q.count-1)+') % 8] = buf['+k+']</code>에 넣고 count를 '+Q.count+'로');}
function qpoll(){ if(Q.count===0){qdraw(null,'비어 있습니다. <code>poll</code>은 <code>null</code>을 돌려줍니다.');return;}
  const h=Q.head, v=Q.buf[h]; Q.buf[h]=null; Q.head=(h+1)%8; Q.count--;
  qdraw(null,'꺼내기: <code>buf['+h+']</code>의 #'+v+'을 꺼내고 <code>head = ('+h+' + 1) % 8 = '+Q.head+'</code>'+(h===7?' ← 7 다음은 0':''));}
const INIT={queue:qreset};
/* ---------- events ---------- */
document.addEventListener('click',e=>{
  const g=e.target.closest('[data-go]'); if(g){e.preventDefault();go(g.getAttribute('data-go'),g);return;}
  const b=e.target.closest('[data-act]'); if(!b) return;
  const a=b.getAttribute('data-act');
  if(a==='tour') tourShow(0); else if(a==='next') tourShow(tourAt+1); else if(a==='prev') tourShow(tourAt-1);
  else if(a==='stop') tourStop(); else if(a==='offer') qoffer(); else if(a==='poll') qpoll(); else if(a==='qreset') qreset();
});
document.getElementById('out').addEventListener('click',()=>{if(L[cur].parent) go(L[cur].parent,null);});
document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&L[cur].parent) go(L[cur].parent,null);
  if(tourAt>=0&&e.key==='ArrowRight'&&tourAt<TOUR.length-1) tourShow(tourAt+1);
  if(tourAt>=0&&e.key==='ArrowLeft'&&tourAt>0) tourShow(tourAt-1);});
const hash=location.hash.slice(1), tm=/^tour(\d+)$/.exec(hash);
const start=(window.HH_START&&L[window.HH_START])?window.HH_START:(tm?'inside':(L[hash]?hash:'outside'));
render(start);
if(tm) tourShow(Math.min(+tm[1],TOUR.length-1));
"""

PAGE = """<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HomeHub 구조 지도</title><style>%(css)s</style></head><body><div class="wrap">
<h1>HomeHub 구조 지도</h1>
<p class="lead">지도를 확대하듯 바깥에서 안으로 들어가며 봅니다. <b>⊕ 표시가 있는 상자를 누르면</b> 그 안의 자세한 그림이 나옵니다.
위 경로를 누르거나 <b>← 밖으로</b>(또는 Esc)를 누르면 한 단계 밖으로 나옵니다.</p>
<div class="bar"><button id="out">← 밖으로</button><span id="crumbs"></span><span class="sp"></span></div>
<h2 id="ltitle"></h2>
<div class="stagewrap"><div id="stage"></div></div>
<div id="desc"></div>
</div>
<!--HH_START-->
<script>const L=%(levels)s;const TOUR=%(tour)s;%(js)s</script></body></html>
"""


def main():
    levels = json.dumps(LEVELS, ensure_ascii=False).replace("</", "<\\/")
    tour = json.dumps(TOUR, ensure_ascii=False).replace("</", "<\\/")
    page = PAGE % dict(css=CSS, levels=levels, tour=tour, js=JS)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", os.path.relpath(OUT, ROOT), len(page), "bytes,", len(LEVELS), "levels,", len(TOUR), "tour steps")


if __name__ == "__main__":
    main()
