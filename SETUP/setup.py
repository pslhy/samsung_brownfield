#!/usr/bin/env python3
"""setup.py - HomeHub lab: one setup command for every OS. It looks at this computer first, in your own
account, then runs the right setup script with options decided from what it found.

    python3 SETUP/setup.py [--skip-codex | --update-codex]
        macOS   -> sudo sh SETUP/setup_mac.sh <options>   (asks for your password)
        Windows -> SETUP\\setup_windows.bat <options>    (your own account, no administrator rights)
        Linux   -> not supported: install JDK 11 and Dafny 4.11 yourself (it says what to install)
    It shows what it found before it runs anything. Parts already installed are skipped, so running it
    again with --update-codex only installs or updates Codex.

What it reads, and what it passes on:
    OS, CPU, the lab folder           which script to run (the script picks the JDK/Dafny download itself)
    jdk/, dafny/, .venv/              shown only: the scripts skip a part whose folder is already there
    java, javac, dafny on PATH        shown only (the setup changes no PATH: make and the notebooks put the
                                      lab's own jdk/, dafny/ first themselves)
    make (macOS)                      shown only: `make --version` must run (the Command Line Tools); without it
                                      it says xcode-select --install. Windows uses make.cmd -> SETUP/make_fallback.py.
    codex on PATH, codex login status,  installed, signed in and CODEX_MIN_VERSION or newer -> --skip-codex;
    codex --version                   lower than that, not signed in, or not installed -> --update-codex.
                                      Checked here because sudo does not see your account's PATH
                                      (~/.local/bin, npm). Your own option wins.

Run it from your own account, not as root / administrator: setup_mac.sh asks for the rights it needs,
and Codex is installed into the account that runs it (macOS/Linux ~/.local/bin,
Windows %LOCALAPPDATA%\\Programs\\OpenAI\\Codex\\bin).
Windows without any Python yet: double-click SETUP\\setup_windows.bat instead (it installs Python too).
Standard library only.
"""
import os
import platform
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WINDOWS, MAC = os.name == "nt", sys.platform == "darwin"
OPTIONS = ("--skip-codex", "--update-codex")
# Codex older than this is updated even when signed in. 0.147.0 has every `codex exec` option lab.codex uses
# (--ephemeral, --json, -o, -s, -C, -m, -c, --skip-git-repo-check); raise it when the lab needs a newer Codex.
CODEX_MIN_VERSION = "0.147.0"


def version_tuple(text):
    """'codex-cli 0.147.0' -> (0, 147, 0); None when there is no version number in it"""
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else None


def is_root():
    return not WINDOWS and os.geteuid() == 0


def first_line(cmd):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    out = [l for l in p.stdout.decode("utf-8", "replace").splitlines() if l.strip() and not l.startswith("Picked up")]
    return out[0].strip() if out else ""


def look():
    """everything the setup depends on, read in this account"""
    jdk_bin = os.path.join(ROOT, "jdk", "Contents", "Home", "bin") if MAC else os.path.join(ROOT, "jdk", "bin")
    exe = ".exe" if WINDOWS else ""
    venv_py = os.path.join(ROOT, ".venv", "Scripts" if WINDOWS else "bin", "python" + exe)
    codex = shutil.which("codex")
    signed_in = bool(codex) and subprocess.call([codex, "login", "status"], stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL) == 0
    return {
        "os": "Windows" if WINDOWS else "macOS" if MAC else platform.system() or "unknown",
        "cpu": platform.machine() or "?",
        "jdk": os.path.isfile(os.path.join(jdk_bin, "javac" + exe)),
        "dafny": os.path.isfile(os.path.join(ROOT, "dafny", "dafny" + exe)),
        "venv": os.path.isfile(venv_py),
        "path": {n: shutil.which(n) for n in ("java", "javac", "dafny")},
        # /usr/bin/make is there even without the Command Line Tools (it only opens their install dialog)
        "make": None if WINDOWS else first_line(["make", "--version"]) if shutil.which("make") and
                subprocess.call(["make", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0 else "",
        "codex": codex,
        "codex_version": first_line([codex, "--version"]) if codex else "",
        "signed_in": signed_in,
    }


def show(f, codex_option, reason, cmd):
    yes = lambda b: "있음 (installed, skipped)" if b else "없음 (will be installed)"
    print("==== HomeHub lab setup: what this computer has ====")
    print("  OS / CPU     : %s / %s" % (f["os"], f["cpu"]))
    print("  lab folder   : %s" % ROOT)
    print("  jdk/         : %s" % yes(f["jdk"]))
    print("  dafny/       : %s" % yes(f["dafny"]))
    print("  .venv/       : %s" % yes(f["venv"]))
    for n, p in f["path"].items():
        outside = p and not os.path.normcase(os.path.realpath(p)).startswith(os.path.normcase(os.path.realpath(ROOT)) + os.sep)
        print("  %-12s : %s%s" % (n + " (PATH)", p or "없음 (not found)",
                                  "   <- 실습 폴더 밖 (outside the lab folder)" if outside else ""))
    if WINDOWS:
        print("  make         : make.cmd -> SETUP\\make_fallback.py (in cmd, in the lab folder)")
    else:
        print("  make         : %s" % (f["make"] or "없음 -> xcode-select --install (Command Line Tools)"
                                       if MAC else f["make"] or "없음 (not found)"))
    if f["codex"]:
        print("  codex        : %s (%s), %s" % (f["codex"], f["codex_version"] or "?",
                                               "signed in" if f["signed_in"] else "not signed in"))
    else:
        print("  codex        : 없음 (not found)")
    print("  -> %s: %s" % (codex_option, reason))
    if cmd:
        print("  -> runs     : %s" % " ".join('"%s"' % c if " " in c else c for c in cmd))
    print()


def main(args):
    if any(a in ("-h", "--help", "help") for a in args):
        print(__doc__)
        return 0
    opts = args
    bad = [a for a in opts if a not in OPTIONS]
    if bad or len(set(opts)) > 1:
        print("unknown or conflicting option: %s   (python SETUP/setup.py [--skip-codex | --update-codex])"
              % " ".join(bad or opts))
        return 2
    if is_root():
        print("Run this from your own account, without sudo: it asks for administrator rights when it needs them.")
        return 1

    f = look()
    have, need = version_tuple(f["codex_version"]), version_tuple(CODEX_MIN_VERSION)
    ver = ".".join(map(str, have)) if have else "version unknown"
    if opts:
        option, reason = opts[0], "your option"
    elif f["codex"] and f["signed_in"] and have and have < need:
        option, reason = "--update-codex", "Codex %s is lower than %s: update it" % (ver, CODEX_MIN_VERSION)
    elif f["codex"] and f["signed_in"]:
        option, reason = "--skip-codex", "Codex %s is installed and signed in (%s or newer is enough)" % (
            ver, CODEX_MIN_VERSION)
    else:
        option, reason = "--update-codex", ("Codex is installed but not signed in: run the installer again"
                                            if f["codex"] else "Codex is not installed")

    if WINDOWS:
        # setup_windows.bat runs in this window as you: no administrator rights, Codex in your account
        cmd = [os.environ.get("COMSPEC", "cmd.exe"), "/c", os.path.join(HERE, "setup_windows.bat"), option]
    elif MAC:
        cmd = ["sudo", "sh", os.path.join(HERE, "setup_mac.sh"), option]
    else:
        cmd = None                       # Linux: not supported, nothing is installed
    show(f, option, reason, cmd)
    if cmd:
        if MAC:
            print("Administrator rights are needed: sudo asks for your password.")
        return subprocess.call(cmd)

    print("SETUP supports macOS and Windows only. On Linux, install these yourself:")
    print("  JDK 11 (the javac that built legacy/build): e.g. sudo apt install openjdk-11-jdk")
    print("  Dafny 4.11.0: https://github.com/dafny-lang/dafny/releases/tag/v4.11.0 (Linux zip), unpack it to")
    print("                %s" % os.path.join(ROOT, "dafny"))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
