#!/usr/bin/env python3
"""make_fallback.py - Windows용 HomeHub 실습 명령. Windows에는 make가 없고 Makefile은 bash가 필요하므로,
Makefile과 대상·변수·동작이 같은 일을 Python(표준 라이브러리만)으로 합니다. macOS·Linux는 Makefile을 씁니다.

    make <대상> [변수=값 ...]       Windows cmd, 실습 폴더에서: make.cmd가 이 파일을 부릅니다   (목록: make help)
                                    노트북의 lab.run도 Windows에서는 이 파일을 부릅니다

그래서 문서·보고서·노트북의 명령은 모두 `make ...` 하나로 적습니다.
macOS에서 `python3 SETUP/make_fallback.py ...`로 직접 돌리는 것은 Makefile과 결과가 같은지 확인할 때뿐입니다.
고칠 때: Makefile이 기준입니다. 대상을 바꾸면 Makefile을 먼저 고치고 이 파일을 맞춘 뒤, `make smoke`와
`python3 SETUP/make_fallback.py smoke`의 결과가 같은지 확인합니다.
변수는 명령줄 > 환경변수 > 기본값 순입니다(make와 같음).
각 대상 위의 주석은 Makefile의 해당 줄이 어떻게 옮겨졌는지입니다: `;` = 실패해도 계속, `-` = 실패 무시(ok=True).
"""
import glob, json, os, re, shlex, shutil, stat, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the lab folder: this file is in <lab>/SETUP/
os.chdir(ROOT)
os.environ["PYTHONUTF8"] = "1"                      # tools/*.py: UTF-8 files and pipes on every OS (Windows default: cp949)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):
        pass

# Makefile 맨 위와 같음: 실습 폴더의 JDK·Dafny(SETUP)를 PATH 맨 앞에. SETUP은 PC의 PATH를 바꾸지 않습니다
os.environ["PATH"] = os.pathsep.join([os.path.join(ROOT, "jdk", "bin"), os.path.join(ROOT, "dafny"),
                                      os.environ.get("PATH", "")])

LEGACY, OUT, BUILD, WORK = "legacy", "out", "build", "work"
RAW = OUT + "/raw"
JFLAGS = ["-nowarn", "-Xlint:-options", "-encoding", "UTF-8"]
LEGACY_CP, LEGACY_TCP = LEGACY + "/build/classes", LEGACY + "/build/test-classes"
FORMAL = ["formal/Types.dfy", "formal/RingQueue.dfy", "formal/Dispatcher.dfy", "formal/PowerBudget.dfy"]
WORKLOADS = ["normal_day", "burst", "fridge_firmware"]
TESTRUNNER = "com.dxlab.homehub.testkit.TestRunner"
MODEL_JAR = BUILD + "/model/homehub_model.jar"
REQ1 = "scenarios/req1"
REQ1_MODEL_JAR = BUILD + "/model-req1/homehub_model.jar"
NEWFORMAL = {"req2": ["formal/Types.dfy", "scenarios/req2/model/RingQueue.dfy", "formal/Dispatcher.dfy", "formal/PowerBudget.dfy"],
             "req1": ["formal/Types.dfy", REQ1 + "/model/RingQueue.dfy", REQ1 + "/model/Dispatcher.dfy", "formal/PowerBudget.dfy"]}
JAVAV = {"req2": "scenarios/req2/ai", "req1": REQ1 + "/ai-B"}

# ---------------------------------------------------------------- variables, running things (what make and bash give for free)

CLI, GOALS = {}, []                                 # command-line variables, targets ($(MAKECMDGOALS))


def var(name, default=""):
    return CLI.get(name, os.environ.get(name, default))


class Stop(Exception):
    """stop with exit code args[0], as make does when a recipe line fails"""


def sh(cmd, out=None, append=False, merge=False, ok=False, cwd=None, env=None):
    """one recipe line: stdout to the terminal or to file `out` (os.devnull = > /dev/null), merge = 2>&1"""
    cmd = [str(c) for c in cmd]
    f = open(out, "ab" if append else "wb") if out else None
    try:
        rc = subprocess.call([shutil.which(cmd[0]) or cmd[0]] + cmd[1:], stdout=f,
                             stderr=subprocess.STDOUT if merge else None, cwd=cwd, env=env)
    except OSError as e:
        print("%s: %s" % (cmd[0], e.strerror or e), file=sys.stderr)
        rc = 127
    finally:
        if f:
            f.close()
    if rc and not ok:
        raise Stop(rc)
    return rc


def lines(cmd, err=subprocess.STDOUT):
    """output lines of cmd (err=None: stderr to the terminal, DEVNULL: dropped)"""
    cmd = [str(c) for c in cmd]
    try:
        p = subprocess.run([shutil.which(cmd[0]) or cmd[0]] + cmd[1:], stdout=subprocess.PIPE, stderr=err)
    except OSError:
        return []
    return p.stdout.decode("utf-8", "replace").splitlines()


def head1(cmd):
    """cmd | head -1"""
    print("\n".join(lines(cmd, err=None)[:1]))


def me(*args):
    """$(MAKE) -s <대상> 변수=값: this script again; the command-line variables pass on, as with MAKEFLAGS"""
    return [sys.executable, os.path.abspath(__file__)] + ["%s=%s" % kv for kv in CLI.items()] + list(args)


def each(cmds):
    """for ...; do $(MAKE) ...; done: every command runs, the loop's status is the last one's"""
    rc = 0
    for c in cmds:
        rc = sh(c, ok=True)
    finish(rc)


def finish(rc):
    if rc:
        raise Stop(rc)


def cp(*parts):
    return os.pathsep.join(parts)                   # Java classpath: ':' (macOS/Linux) or ';' (Windows)


def javac(dest, files, classpath=None, release="8", **kw):
    return sh([JAVAC] + JFLAGS + (["--release", release] if release else []) + (["-cp", classpath] if classpath else [])
              + ["-d", dest] + list(files), **kw)


def tool(name, *args, **kw):
    return sh([PY, "tools/%s.py" % name] + list(args), **kw)


def drun(json_out, *files):
    return tool("dafny_run", "--json", json_out, *files, ok=True)


def report(out, title, lead, command, *secs, **kw):
    return tool("report", "--out", out, "--title", title, "--lead", lead, "--command", command,
                *[a for s in secs for a in ("--sec",) + tuple(s)], **kw)


def mkdir(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def _force(func, path, *_):
    os.chmod(path, stat.S_IWRITE)                   # Windows: read-only files
    func(path)


def rm(*paths):
    """rm -rf"""
    for p in paths:
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p, **({"onexc": _force} if sys.version_info >= (3, 12) else {"onerror": _force}))
        elif os.path.lexists(p):
            os.remove(p)


def touch(path):
    open(path, "ab").close()
    os.utime(path, None)


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def tail(path):
    """tail -1"""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return (f.read().splitlines() or [""])[-1]
    except OSError:
        return ""


def tail1(path):
    if tail(path):
        print(tail(path))


def javas(d):
    return sorted(glob.glob(d + "/**/*.java", recursive=True))


def stale(target, sources):
    """make's rule: target missing or older than a source"""
    return not os.path.exists(target) or any(os.path.getmtime(s) > os.path.getmtime(target) for s in sources)


def venv(prog):
    """a program in .venv (made by the setup), whether or not .venv is activated"""
    for p in (".venv/bin/" + prog, ".venv/Scripts/%s.exe" % prog):
        if os.path.isfile(p):
            return os.path.abspath(p)


def find_dafny():
    """DAFNY, else dafny on PATH, else the release unpacked in ./dafny/ (SETUP/)"""
    if var("DAFNY") or shutil.which("dafny"):
        return var("DAFNY") or "dafny"
    for d in ("dafny/dafny.exe", "dafny/dafny"):
        if os.path.isfile(d):
            os.environ["PATH"] = os.path.abspath("dafny") + os.pathsep + os.environ.get("PATH", "")   # for tools/
            return os.path.abspath(d)
    return "dafny"


# a "variant" is a copy of legacy/ with a directory copied on top of it: an overlay from scenarios/..., or your own
# edited copy of the project (e.g. V=mywork after copying legacy to mywork)
def V():
    return var("V").replace("\\", "/").rstrip("/")


def vname():
    return re.sub(r"^scenarios/", "", V()).replace("/", "-")


def vdir():
    return WORK + "/" + vname()


# ---------------------------------------------------------------- targets

TARGETS, DONE = {}, set()


def target(name, *deps):
    def deco(fn):
        TARGETS[name] = (deps, fn)
        return fn
    return deco


def make(name):
    if name not in DONE:
        DONE.add(name)
        deps, fn = TARGETS[name]
        for d in deps:
            make(d)
        fn()


HELP = """\
처음    : python SETUP\\setup.py (macOS: python3 SETUP/setup.py): JDK·Dafny·Python·.venv·Jupyter → make check-env
준비    : make check-env | build | test | trace
구조    : make path MSG='4|fridge-2|TEMP|14|180000|unit=C' | state | config KEY=temp.highCelsius (참고용)
실습 A  : make trace | ingest MSG='5|fridge-2|TEMP|38|60000' | impact V=scenarios/req2/ai [WHY=클래스#메서드]
          make impact V=scenarios/req1/ai-A WHY=ops.Watchdog#check | impact V=scenarios/a3-sort
          make impact V=scenarios/req2/ai SCOPE=legacy/src/main/java/com/dxlab/homehub/queue/RingEventQueue.java
실습 B  : make verify | model | difftest
          make difftest-mine DFY=mine/RingEventQueue.dfy ADAPTER=mine/MyQueueAdapter.java
          make difftest-sample   (AI 결과 예시로 같은 과정)
          make dispatcher-sample (예시 대기열 위의 Dispatcher 모델 검증)
실습 C  : make req1   (= req1-tests, req1-verify, req1-difftest)
실습 D  : make reverify REQ=req2|req1
실습 E  : make rewrite-check R=IsEmpty|ForEach|InlineVariable|All | make rules
노트북  : make notebook (Jupyter로 실습 노트북 열기, notebooks/0_시작하기.ipynb부터)
보고서  : make report (목록 열기) | make show V=<폴더> (바뀐 코드) | HH_OPEN=0 이면 자동으로 열지 않음
강사    : make verify-all (통과해야 하는 Dafny 증명 전부) | smoke (전체) | smoke-notebooks (노트북 6개) | clean"""


@target("help")
def t_help():
    print(HELP)


@target("check-env")
def t_check_env():
    # ENV_OS / ENV_APT: an install hint under each tool that does not run (Windows: SETUP\setup.py, which make never sees)
    mac, apt, win = sys.platform == "darwin", shutil.which("apt-get"), os.name == "nt"
    setup = r"  python SETUP\setup.py 실행 (JDK·Dafny·Python 설치)"
    by_os = lambda m, a, other: setup if win else "  " + (m if mac else a if apt else other)
    def show(label, cmd, *fix):
        try:
            p = subprocess.run([shutil.which(cmd[0]) or cmd[0]] + cmd[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, rc = p.stdout.decode("utf-8", "replace").splitlines(), p.returncode
        except OSError:
            out, rc = ["(없음)"], 127
        print(label + (out[0] if out else ""))
        if rc:
            print("\n".join(fix))
    jdk = by_os("brew install --cask temurin@21", "sudo apt install openjdk-21-jdk", "배포판의 패키지 관리자로 JDK 11 이상 설치")
    show("java : ", [JAVA, "-version"], jdk)
    show("javac: ", [JAVAC, "-version"], jdk)
    show("py   : ", [PY, "--version"], by_os("brew install python3", "sudo apt install python3 python3-pip python3-venv",
                                            "배포판의 패키지 관리자로 Python 3·pip·venv 설치"))
    show("dafny: ", [DAFNY, "--version"], *([setup] if win else [
        "  https://github.com/dafny-lang/dafny/releases/tag/v4.11.0 에서 " + ("Mac용 ZIP 설치 후 해당 폴더에서 ./allow_on_mac.sh 실행" if mac else "Linux용 ZIP 설치"),
        "  압축을 푼 뒤 dafny 실행 파일이 있는 디렉터리로 이동해서 실행하세요:", '    export PATH="$PWD:$PATH"',
        "  새 터미널에서도 유지하려면 현재 디렉터리의 절대경로(pwd 출력)를 %s에 export PATH=\"절대경로:$PATH\" 형태로 추가하세요."
        % ("~/.zshrc" if mac else "Bash는 ~/.bashrc · Zsh는 ~/.zshrc"), "  확인: dafny --version"]))
    jup = [l for l in lines([venv("jupyter") or "jupyter", "--version"], subprocess.DEVNULL) if re.search("jupyterlab|notebook", l, re.I)]
    print("jupyter: " + (jup[0] if jup else "없음 (%s, 또는 VS Code의 Python·Jupyter 확장)" % (r"python SETUP\setup.py" if win else "python3 SETUP/setup.py")))
    cx = lines(["codex", "--version"], subprocess.DEVNULL)
    st = lines(["codex", "login", "status"]) if cx else []
    print("codex: %s %s" % (cx[0] if cx else "없음 (선택: %s, 이후 새 창에서 codex login)" % (
                                "PowerShell에서 irm https://chatgpt.com/codex/install.ps1 | iex" if win else
                                "curl -fsSL https://chatgpt.com/codex/install.sh | sh"),
                            "· " + st[0] if st else ""))


# ---------------------------------------------------------------- build / test

@target("build")
def t_build():
    stamp = LEGACY_CP + "/.stamp"
    # REBUILD_LEGACY: A-1 compares bytecode, so a direct req2/ai impact run builds both sides with the same javac
    force = var("REBUILD_LEGACY", "1" if "impact" in GOALS and var("V") == "scenarios/req2/ai" else "0") == "1"
    if force or stale(stamp, javas(LEGACY + "/src")):
        rm(LEGACY + "/build")
        mkdir(LEGACY_CP, LEGACY_TCP)
        javac(LEGACY_CP, javas(LEGACY + "/src/main/java"))
        javac(LEGACY_TCP, javas(LEGACY + "/src/test/java"), LEGACY_CP)
        touch(stamp)
        print("built " + LEGACY)


@target("test", "build")
def t_test():
    mkdir(RAW)
    st = sh([JAVA, "-cp", cp(LEGACY_CP, LEGACY_TCP), TESTRUNNER], out=RAW + "/test.txt", ok=True)
    tail1(RAW + "/test.txt")
    report("test", "기존 테스트", "레거시 코드의 테스트 38개를 실행한 결과입니다.", "make test",
           ("tests", "테스트", RAW + "/test.txt", "pass"), ok=True)
    finish(st)


# characterization tests: compare observable traces with the golden files (TRACE_CP = another build)
@target("trace", "build")
def t_trace():
    mkdir(RAW)
    tcp = var("TRACE_CP")
    st = tool("trace_check", "--cp", tcp or LEGACY_CP, "--json", RAW + "/trace.json", *WORKLOADS, ok=True)
    report(var("TRACE_NAME") or "trace", "동작 기록 비교",
           "입력 파일(legacy/workloads)을 넣고 한 줄마다 나온 상태를, 미리 저장해 둔 기록(golden)과 비교합니다. 다른 줄은 다른 낱말에 표시합니다.",
           "make trace" + (" TRACE_CP=" + tcp if tcp else ""),
           ("trace", "기록 비교 (%s)" % (tcp or "legacy"), RAW + "/trace.json", "-"), ok=True)
    finish(st)


@target("golden", "build")
def t_golden():
    mkdir("golden")
    rc = 0
    for w in WORKLOADS:
        p = subprocess.run([JAVA, "-cp", LEGACY_CP, "com.dxlab.homehub.app.HubMain", "%s/workloads/%s.txt" % (LEGACY, w)],
                           stdout=subprocess.PIPE)
        with open("golden/%s.trace" % w, "wb") as f:
            f.write(p.stdout.replace(b"\r\n", b"\n"))   # Windows: the same file as on macOS
        rc = p.returncode
    finish(rc)
    print("golden traces regenerated from legacy")


# ---------------------------------------------------------------- session 2: change impact (def-use)

@target("variant")
def t_variant():
    v, d = V(), vdir()
    if not v:
        print("usage: make variant V=scenarios/<...>")
        raise Stop(2)
    rm(d)
    mkdir(WORK)
    try:
        shutil.copytree(LEGACY, d)
        shutil.copytree(v, d, dirs_exist_ok=True)
    except OSError as e:
        print("cp: %s" % e, file=sys.stderr)
        raise Stop(1)
    rm(d + "/build", d + "/target")
    mkdir(d + "/build/classes", d + "/build/test-classes")
    javac(d + "/build/classes", javas(d + "/src/main/java"))
    javac(d + "/build/test-classes", javas(d + "/src/test/java"), d + "/build/classes")
    print("built variant %s  (바뀐 코드: make show V=%s)" % (d, v))


@target("variant-test", "variant")
def t_variant_test():
    v, d, n = V(), vdir(), vname()
    out = "%s/test-%s.txt" % (RAW, n)
    mkdir(RAW)
    st = sh([JAVA, "-cp", cp(d + "/build/classes", d + "/build/test-classes"), TESTRUNNER], out=out, ok=True)
    tail1(out)
    if var("NOREPORT") != "1":
        report("test-" + n, "테스트: " + v, "%s를 레거시에 덮어쓴 빌드의 테스트 결과입니다." % v, "make variant-test V=" + v,
               ("srcdiff", "바뀐 코드", "%s/src|%s/src" % (LEGACY, d), "-"), ("tests", "테스트", out, "-"), ok=True)
    finish(st)


def trace_one(kind, inp, *extra):
    """one message through a fresh hub (JDK debugger interface): MSG='...', or a file of setup lines + the message"""
    mkdir(RAW, BUILD + "/tools")
    javac(BUILD + "/tools", ["tools/java/IngestOne.java", "tools/java/LineTracer.java"], LEGACY_CP, release=None)
    if var("MSG"):
        write(inp, var("MSG") + "\n")
    sh([JAVA, "-cp", BUILD + "/tools", "LineTracer", cp(LEGACY_CP, BUILD + "/tools"), inp] + list(extra),
       out="%s/%s.json" % (RAW, kind))


# make ingest MSG='5|fridge-2|TEMP|38|60000'   (or a file of setup lines + the message: INGEST_IN=...)
@target("ingest", "build")
def t_ingest():
    inp = var("INGEST_IN", RAW + "/ingest-input.txt")
    trace_one("ingest", inp)
    report("ingest", "메시지 하나 넣어 보기", "새로 시작한 허브에 메시지 한 줄을 넣고, 결과와 바뀐 상태, 실제로 실행된 코드 줄을 보여 줍니다.",
           "make ingest MSG='%s'" % tail(inp), ("ingest", "처리 결과", RAW + "/ingest.json", "-"))


# the structure of the legacy code (reference; the lab uses docs/homehub_구조.html)
# path MSG='...': one message handled to the end (the queue drained): call graph vs the methods that ran (or PATH_IN=...)
@target("path", "build")
def t_path():
    inp = var("PATH_IN", RAW + "/path-input.txt")
    trace_one("path", inp, "drain")
    tool("structure", "path", "--classes", LEGACY_CP, "--src", LEGACY + "/src/main/java", "--trace", RAW + "/path.json",
         "--html", "path", "--command", "make path MSG='%s'" % tail(inp))


# who changes and who reads each piece of shared state
@target("state", "build")
def t_state():
    tool("structure", "state", "--classes", LEGACY_CP, "--src", LEGACY + "/src/main/java", "--html", "state",
         "--command", "make state")


# config KEY=temp.highCelsius: where a configuration value may flow
@target("config", "build")
def t_config():
    key = var("KEY")
    if not key:
        print("usage: make config KEY=temp.highCelsius")
        raise Stop(2)
    tool("structure", "config", "--classes", LEGACY_CP, "--src", LEGACY + "/src/main/java", "--key", key,
         "--html", "config-" + key, "--command", "make config KEY=" + key)


# what a scenario folder changes, as a side-by-side diff page
@target("show", "variant")
def t_show():
    report("show-" + vname(), "바뀐 코드: " + V(), "%s가 레거시에서 바꾼 파일입니다." % V(), "make show V=" + V(),
           ("srcdiff", "바뀐 코드", "%s/src|%s/src" % (LEGACY, vdir()), "-"))


# WHY=클래스#메서드 : only the reasons for that method (impact-<V>-why.html)
# SCOPE=소스 파일    : analyze only that file, as if nothing else existed (impact-<V>-scope.html)
@target("impact", "build", "variant")
def t_impact():
    d, n, why, scope = vdir(), vname(), var("WHY"), var("SCOPE")
    suf = ("-scope" if scope else "") + ("-why" if why else "")
    mkdir(OUT)
    tool("impact", "--base", LEGACY_CP, LEGACY_TCP, "--base-src", LEGACY + "/src/main/java", LEGACY + "/src/test/java",
         "--changed", d + "/build/classes", d + "/build/test-classes", "--changed-src", d + "/src/main/java", d + "/src/test/java",
         "--mapping", "formal/mapping.tsv", "--json", "%s/impact-%s.json" % (OUT, n), "--html", "impact-" + n + suf, "--title-v", V(),
         *((["--why", why] if why else []) + (["--scope", scope] if scope else [])), out="%s/impact-%s%s.md" % (OUT, n, suf))


# ---------------------------------------------------------------- session 3: formalization, difftest

@target("verify")
def t_verify():
    mkdir(RAW)
    st = drun(RAW + "/verify.json", "formal/dfyconfig.toml")
    report("verify", "Dafny 기준 모델 검증", "formal/의 대기열, Dispatcher, 전력 모델을 검증합니다.", "make verify",
           ("dafny", "formal/ 전체", RAW + "/verify.json", "pass"), ok=True)
    finish(st)


@target("model")
def t_model():
    if stale(MODEL_JAR, FORMAL):
        mkdir(BUILD + "/model")
        sh([DAFNY, "build", "-t", "java", "formal/dfyconfig.toml", "-o", BUILD + "/model/homehub_model"], out=os.devnull)
        print("Dafny 모델을 Java로 컴파일: " + MODEL_JAR)


# Makefile's $(BUILD)/difftest/.stamp: it depends on the phony `build`, so make recompiles it every time
@target("difftest-classes", "build", "model")
def t_difftest_classes():
    mkdir(BUILD + "/difftest")
    javac(BUILD + "/difftest", sorted(glob.glob("difftest/src/difftest/*.java")), cp(LEGACY_CP, MODEL_JAR), release="11")
    touch(BUILD + "/difftest/.stamp")


def dt_args():
    return shlex.split(var("DT_ARGS"))


@target("difftest", "difftest-classes")
def t_difftest():
    mkdir(RAW)
    jcp, what = var("JAVA_CP"), var("WHAT")
    st = sh([JAVA, "-cp", cp(jcp or LEGACY_CP, var("MODEL_JAR") or MODEL_JAR, BUILD + "/difftest"), "difftest.DiffTest", what or "all",
             "--json", RAW + "/difftest.json"] + dt_args(), ok=True)
    report("difftest", "차분 테스트: Java와 Dafny 모델",
           "같은 무작위 연산을 Java 클래스와 Java로 컴파일한 Dafny 모델에 넣고, 매 연산 뒤의 결과와 상태를 비교합니다. "
           "다르면 같은 차이가 나는 가장 짧은 연산열을 보여 줍니다.",
           "make difftest" + (" JAVA_CP=" + jcp if jcp else "") + (" WHAT=" + what if what else ""),
           ("difftest", "%s vs 모델" % (jcp or "legacy"), RAW + "/difftest.json", "-"), ok=True)
    finish(st)


# Your own (AI-written) Dafny model of RingEventQueue + its adapter (docs/PROMPTS.md P-1, P-1b).
# DFY may list several files. The adapter must be class difftest.MyQueueAdapter.
@target("difftest-mine", "difftest-classes")
def t_difftest_mine():
    dfy_s, ad_s = var("DFY", "mine/RingEventQueue.dfy"), var("ADAPTER", "mine/MyQueueAdapter.java")
    dfy, adapter = shlex.split(dfy_s), shlex.split(ad_s)
    for f in dfy + adapter:
        if not os.path.isfile(f):
            print("아직 없습니다: %s  (노트북의 lab.codex 셀을 실행하거나 AI 결과를 붙여 넣으세요)" % f)
            raise Stop(2)
        with open(f, encoding="utf-8", errors="replace") as fh:
            if "여기에 붙여 넣기" in fh.read():
                print("아직 AI 결과를 붙여 넣지 않았습니다: " + f)
                raise Stop(2)
    rm(BUILD + "/mine", *glob.glob(RAW + "/mine-*"))
    mkdir(BUILD + "/mine/classes", RAW)
    drun(RAW + "/mine-verify.json", *dfy)
    log, jar = RAW + "/mine-build.txt", BUILD + "/mine/mymodel.jar"
    if (sh([DAFNY, "build", "-t", "java", "--no-verify", "--allow-warnings"] + dfy + ["-o", BUILD + "/mine/mymodel"],
           out=log, merge=True, ok=True) == 0 and
            javac(BUILD + "/mine/classes", adapter, cp(jar, BUILD + "/difftest"), "11", out=log, append=True, merge=True, ok=True) == 0):
        print("연결 코드 컴파일: 성공")
        sh([JAVA, "-Dqueue.adapter=difftest.MyQueueAdapter", "-cp", cp(jar, BUILD + "/mine/classes", LEGACY_CP, BUILD + "/difftest"),
            "difftest.DiffTest", "queue", "--json", RAW + "/mine-difftest.json"] + dt_args(), ok=True)
    else:
        print("Java 컴파일 또는 연결 코드 컴파일 실패: 보고서를 보세요")
    report("difftest-mine", "내 Dafny 모델 확인",
           "AI가 만든 Dafny 모델(%s)을 검증하고, 연결 코드(%s)로 레거시 RingEventQueue와 차분 테스트합니다. "
           "계약은 실습 안내서 B-1의 확인 목록으로 직접 읽어 판단합니다." % (dfy_s, ad_s),
           "make difftest-mine DFY=%s ADAPTER=%s" % (dfy_s, ad_s),
           ("dafny", "1. Dafny 검증", RAW + "/mine-verify.json", "pass"),
           ("text", "2. Java로 컴파일, 연결 코드 컴파일 (메시지)", log, "-"),
           ("difftest", "3. 차분 테스트: 레거시 RingEventQueue vs 내 모델", RAW + "/mine-difftest.json", var("DT_EXPECT", "pass")))


# the same with the example AI output in scenarios/b1-ai-sample/
@target("difftest-sample")
def t_difftest_sample():
    sh(me("difftest-mine", "DFY=scenarios/b1-ai-sample/RingEventQueue.dfy", "ADAPTER=scenarios/b1-ai-sample/MyQueueAdapter.java"))


# B-2: the Dispatcher model written on top of the example queue model (same names: elems, Event, buf.Length)
@target("dispatcher-sample")
def t_dispatcher_sample():
    mkdir(RAW)
    st = drun(RAW + "/dispatcher-sample.json", "scenarios/b1-ai-sample/RingEventQueue.dfy", "scenarios/b1-ai-sample/Dispatcher.dfy")
    report("dispatcher-sample", "Dispatcher 모델 검증",
           "예시 대기열 모델(RingEventQueue.dfy)을 가져다 쓰는 Dispatcher 모델(Dispatcher.dfy)을 함께 검증합니다.",
           "make dispatcher-sample", ("dafny", "scenarios/b1-ai-sample/", RAW + "/dispatcher-sample.json", "pass"), ok=True)
    finish(st)


# ---------------------------------------------------------------- session 4: REQ-1 verified evolution

@target("req1-model")
def t_req1_model():
    if stale(REQ1_MODEL_JAR, [REQ1 + "/model/RingQueue.dfy", REQ1 + "/model/Dispatcher.dfy"]):
        mkdir(BUILD + "/model-req1")
        sh([DAFNY, "build", "-t", "java"] + NEWFORMAL["req1"] + ["-o", BUILD + "/model-req1/homehub_model"], out=os.devnull)


REQ1_CODE = [("srcdiff", "패치 A가 바꾼 코드", "%s/src|%s/req1-ai-A/src" % (LEGACY, WORK), "-"),
             ("srcdiff", "패치 B가 바꾼 코드", "%s/src|%s/req1-ai-B/src" % (LEGACY, WORK), "-")]
REQ1_TESTS = [("tests", "테스트: 패치 A", RAW + "/test-req1-ai-A.txt", "pass"),
              ("tests", "테스트: 패치 B", RAW + "/test-req1-ai-B.txt", "pass")]
REQ1_VERIFY = [("dafny", "Dafny: 패치 A의 대기열 모델", RAW + "/req1-v1.json", "fail"),
               ("dafny", "Dafny: 패치 B의 대기열 + Dispatcher 모델", RAW + "/req1-v3.json", "pass")]
REQ1_DIFF = [("difftest", "차분 테스트: 패치 A vs 변경 요청 1 모델", RAW + "/req1-dt-A.json", "fail"),
             ("difftest", "차분 테스트: 패치 B vs 변경 요청 1 모델", RAW + "/req1-dt-B.json", "pass"),
             ("difftest", "차분 테스트: 레거시 vs 변경 요청 1 모델 (승인된 동작 변화)", RAW + "/req1-dt-legacy.json", "fail")]
REQ1_LEAD = ("변경 요청 1(대기열 늘리기)에 대한 AI 패치 A·B를 테스트, Dafny, 차분 테스트로 차례로 판단합니다. "
             "각 결과 옆의 표시는 실습이 예상한 결과와 같은지입니다.")


@target("req1-tests-run")
def t_req1_tests_run():
    for v in ("ai-A", "ai-B"):
        print("%-6s " % v, end="", flush=True)
        print("\n".join(lines(me("variant-test", "V=%s/%s" % (REQ1, v), "NOREPORT=1"), subprocess.DEVNULL)[-1:]))


@target("req1-verify-run")
def t_req1_verify_run():
    mkdir(RAW)
    drun(RAW + "/req1-v1.json", "formal/Types.dfy", REQ1 + "/model/RingQueue_A.dfy")
    drun(RAW + "/req1-v3.json", *NEWFORMAL["req1"])


@target("req1-difftest-run", "difftest-classes", "req1-model")
def t_req1_difftest_run():
    mkdir(RAW)
    rc = 0
    for v in ("ai-A", "ai-B"):
        rc = sh(me("variant", "V=%s/%s" % (REQ1, v)), out=os.devnull, ok=True)
    finish(rc)
    dt = BUILD + "/difftest"
    head1([JAVA, "-cp", cp(WORK + "/req1-ai-A/build/classes", REQ1_MODEL_JAR, dt), "difftest.DiffTest", "queue", "--json", RAW + "/req1-dt-A.json"])
    sh([JAVA, "-cp", cp(WORK + "/req1-ai-B/build/classes", REQ1_MODEL_JAR, dt), "difftest.DiffTest", "all", "--json", RAW + "/req1-dt-B.json"], ok=True)
    head1([JAVA, "-cp", cp(LEGACY_CP, REQ1_MODEL_JAR, dt), "difftest.DiffTest", "queue", "--json", RAW + "/req1-dt-legacy.json"])


@target("req1-tests", "req1-tests-run")
def t_req1_tests():
    report("req1-tests", "변경 요청 1: 테스트", REQ1_LEAD, "make req1-tests", *(REQ1_CODE + REQ1_TESTS))


@target("req1-verify", "req1-verify-run")
def t_req1_verify():
    report("req1-verify", "변경 요청 1: Dafny", REQ1_LEAD, "make req1-verify", *REQ1_VERIFY)


@target("req1-difftest", "req1-difftest-run")
def t_req1_difftest():
    report("req1-difftest", "변경 요청 1: 차분 테스트", REQ1_LEAD, "make req1-difftest", *REQ1_DIFF)


@target("req1", "req1-tests-run", "req1-verify-run", "req1-difftest-run")
def t_req1():
    report("req1", "변경 요청 1: 대기열 늘리기", REQ1_LEAD, "make req1", *(REQ1_CODE + REQ1_TESTS + REQ1_VERIFY + REQ1_DIFF))


# every Dafny check that is expected to PASS, with full output (run this first on a new machine)
@target("verify-all")
def t_verify_all():
    mkdir(RAW)
    drun(RAW + "/va-1.json", "formal/dfyconfig.toml")
    drun(RAW + "/va-2.json", *NEWFORMAL["req1"])
    drun(RAW + "/va-3.json", *NEWFORMAL["req2"])
    drun(RAW + "/va-5.json", "rewrite/RewriteRules.dfy")
    report("verify-all", "Dafny 증명 전체 점검",
           "이 실습에서 통과해야 하는 Dafny 증명을 모두 돌립니다. 새 PC에서 먼저 실행하세요. 시간 초과(timed out)가 나면 강사에게 알려 주세요.",
           "make verify-all", ("dafny", "기준 모델 (formal/)", RAW + "/va-1.json", "pass"),
           ("dafny", "변경 요청 1 모델", RAW + "/va-2.json", "pass"), ("dafny", "변경 요청 2 모델", RAW + "/va-3.json", "pass"),
           ("dafny", "정리 규칙의 조건", RAW + "/va-5.json", "pass"))


# ---------------------------------------------------------------- session 5: impact-guided re-verification

@target("reverify", "build")
def t_reverify():
    req = var("REQ", "req2")
    sh(me("impact", "V=" + JAVAV.get(req, ""), "REBUILD_LEGACY=0"), out=os.devnull, env=dict(os.environ, HH_OPEN="0"))
    tool("reverify", "--old", *FORMAL, "--new", *NEWFORMAL[req],
         "--java-impact", "%s/impact-%s.json" % (OUT, JAVAV[req][len("scenarios/"):].replace("/", "-")),
         "--mapping", "formal/mapping.tsv", "--run", "--html", "reverify-" + req, "--label", req, out="%s/reverify-%s.md" % (OUT, req))


# ---------------------------------------------------------------- session 5: semantics-preserving rewriting

# R = rule name: scenarios/rw/<R> holds the code after applying that cleanup rule everywhere
#     (IsEmpty, ForEach, InlineVariable, or All = all three)
@target("rewrite-check", "difftest-classes")
def t_rewrite_check():
    r = var("R", "All")
    d, t = "%s/rw-%s" % (WORK, r), "%s/rw-%s" % (RAW, r)
    mkdir(RAW)
    sh(me("variant", "V=scenarios/rw/" + r), out=os.devnull, ok=True)
    sh([JAVA, "-cp", cp(d + "/build/classes", d + "/build/test-classes"), TESTRUNNER], out=t + "-test.txt", ok=True)
    tail1(t + "-test.txt")
    tool("trace_check", "--cp", d + "/build/classes", "--json", t + "-trace.json", "--save", "%s/rw-%s" % (BUILD, r), *WORKLOADS, ok=True)
    head1([JAVA, "-cp", BUILD + "/difftest", "difftest.HubDiff", LEGACY_CP, d + "/build/classes",
           "--keep", "%s/hubdiff-%s.txt" % (OUT, r), "--json", t + "-hub.json"])
    report("rewrite-check-" + r, "정리 규칙 적용 확인: " + r,
           "정리 규칙을 코드 전체에 적용한 결과가 동작을 바꾸지 않았는지 세 가지로 확인합니다: 기존 테스트, 기록해 둔 동작, 무작위 입력으로 레거시와 비교.",
           "make rewrite-check R=" + r, ("srcdiff", "바뀐 코드", "%s/src|%s/src" % (LEGACY, d), "-"),
           ("tests", "1. 기존 테스트", t + "-test.txt", "-"), ("trace", "2. 기록해 둔 동작", t + "-trace.json", "-"),
           ("hubdiff", "3. 무작위 입력으로 레거시와 비교", t + "-hub.json", "-"))


@target("rules")
def t_rules():
    mkdir(RAW)
    st = drun(RAW + "/rules.json", "rewrite/RewriteRules.dfy")
    report("rules", "정리 규칙의 조건 증명",
           "rewrite/RewriteRules.dfy: 규칙마다 같음 보조정리(조건은 requires)와, 조건부 규칙은 조건이 없을 때의 반례 보조정리.",
           "make rules", ("dafny", "RewriteRules.dfy", RAW + "/rules.json", "pass"), ok=True)
    finish(st)


# ---------------------------------------------------------------- everything (instructor smoke test)

@target("smoke")
def t_smoke():
    os.environ["HH_OPEN"] = CLI.get("HH_OPEN", "0")              # smoke: export HH_OPEN = 0
    for t in ("check-env", "test", "trace", "verify-all", "difftest", "difftest-sample", "req1", "rules"):
        make(t)
    sh(me("ingest", "MSG=5|fridge-2|TEMP|38|60000"))
    write(RAW + "/path-input.txt", "1|fridge-2|PWR_ON|0|0\n2|fridge-2|TEMP|12|60000|unit=C\n3|fridge-2|TEMP|13|120000|unit=C\n"
                                   "!drain\n4|fridge-2|TEMP|14|180000|unit=C\n")
    sh(me("path"))
    sh(me("state"), ok=True)
    each(me("config", "KEY=" + k) for k in ("temp.highCelsius", "rules.doorOpenAlertMillis"))
    each(me("impact", "V=scenarios/" + v) for v in ("req2/ai", "req1/ai-A", "a3-sort"))
    if sh(me("variant-test", "V=scenarios/req1/ai-A-oldtests", "NOREPORT=1"), ok=True):
        print("  (예상대로 5개 실패: AI가 테스트를 고치기 전)")
    each(me("reverify", "REQ=" + c) for c in ("req2", "req1"))
    each(me("rewrite-check", "R=" + r) for r in ("IsEmpty", "ForEach", "InlineVariable", "All"))
    print("\n모든 보고서: %s/html/index.html" % OUT)


@target("smoke-notebooks")
def t_smoke_notebooks():
    """(not in the Makefile) run the 6 notebooks top to bottom without Codex; the executed copies go to out/notebooks/"""
    env, bad = dict(os.environ, HH_OPEN="0", HH_NO_CODEX="1"), 0
    for nb in sorted(glob.glob("notebooks/*.ipynb")):
        print("%-34s " % os.path.basename(nb), end="", flush=True)
        p = subprocess.run([venv("python") or sys.executable, "-m", "nbconvert", "--to", "notebook", "--execute",
                            "--ExecutePreprocessor.timeout=900", "--output-dir", OUT + "/notebooks", nb],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        print("ok" if p.returncode == 0 else "실패")
        if p.returncode:
            bad += 1
            print("\n".join("    " + l for l in p.stdout.decode("utf-8", "replace").strip().splitlines()[-8:]))
    finish(1 if bad else 0)


# the lab notebooks (notebooks/0_시작하기.ipynb first)
@target("notebook")
def t_notebook():
    jup = venv("jupyter") or shutil.which("jupyter")
    if not jup:
        print("Jupyter가 없습니다. python SETUP\\setup.py 로 설치하거나, VS Code에서 notebooks/ 의 .ipynb 파일을 여세요.")
        raise Stop(2)
    sh([jup, "lab"], cwd="notebooks", env=dict(os.environ, HH_OPEN="0"))


# open the list of all reports
@target("report")
def t_report():
    sys.path.insert(0, "tools")
    import report as rep
    with open(OUT + "/html/_index.json", encoding="utf-8") as f:
        rep.write_index(json.load(f))
    rep.maybe_open(OUT + "/html/index.html")


@target("clean")
def t_clean():
    gone = [LEGACY + "/build", BUILD, OUT, WORK, "notebooks/__pycache__", "notebooks/.ipynb_checkpoints"]
    print("rm -rf " + " ".join(gone))
    rm(*gone)


# ---------------------------------------------------------------- main

def main(argv):
    global JAVA, JAVAC, PY, DAFNY
    targets = GOALS
    for a in argv:
        m = re.match(r"([A-Za-z_]\w*)=(.*)\Z", a, re.S)
        if m:
            CLI[m.group(1)] = m.group(2)
        elif not a.startswith("-"):                  # -s, --no-print-directory: make's flags, nothing to do here
            targets.append(a)
    JAVA, JAVAC, PY, DAFNY = var("JAVA", "java"), var("JAVAC", "javac"), var("PY") or sys.executable, find_dafny()
    os.environ["DAFNY"] = DAFNY                      # DRUN = DAFNY=$(DAFNY) $(PY) tools/dafny_run.py
    os.environ["HH_OPEN"] = var("HH_OPEN", "1")      # export HH_OPEN ?= 1: tools/report.py opens each report
    for t in targets or ["help"]:
        if t not in TARGETS:
            print("make: *** No rule to make target '%s'.  (목록: make help)" % t, file=sys.stderr)
            return 2
    try:
        for t in targets or ["help"]:
            make(t)
    except Stop as e:
        return e.args[0]
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
