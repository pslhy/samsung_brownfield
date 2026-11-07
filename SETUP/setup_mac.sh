#!/bin/sh
# ============================================================================
#  setup_mac.sh - HomeHub lab: install JDK 11, Dafny 4.11.0, Python 3.13 and the Codex CLI on macOS
#  (Windows: setup_windows.bat). Run the setup with:  python3 SETUP/setup.py   (it runs this script with sudo)
#
#  Lives in <lab folder>/SETUP/ and sets up <lab folder> (the folder above it).
#  Downloads are kept here in SETUP/.
#
#  Official downloads only (adoptium, dafny-lang, python.org), no package manager.
#  setup.py runs it as administrator:   sudo sh SETUP/setup_mac.sh [--skip-codex | --update-codex]
#    (setup.py checks Codex in your own account first and passes one of the two)
#    1. JDK 11     Eclipse Temurin 11.0.32.1+1 tar.gz (Apple or Intel chip) -> <lab folder>/jdk/
#                  (the javac that built the committed legacy/build: the same bytecode, see A-1)
#    2. Dafny      4.11.0 zip                                             -> <lab folder>/dafny/
#    3. Python     uses a python3 that is 3.8 or newer (Homebrew, python.org, /usr/local/bin, or the
#                  Command Line Tools one; no install); only otherwise installs 3.13.17 with python.org's
#                  .pkg (only the interpreter, pip and /usr/local/bin/python3: no IDLE app, no docs, no
#                  shell profile change). Then makes <lab folder>/.venv with that Python
#                  and installs jupyterlab into it (pip, from PyPI; brings ipykernel, nbconvert)
#    4. For all users (made again when run again):
#         /etc/paths.d/homehub    PATH += jdk/Contents/Home/bin, dafny   (new Terminal windows)
#         /Library/Java/JavaVirtualMachines/homehub-temurin-11.jdk -> jdk  (/usr/bin/java, javac find it)
#    5. Prints the versions
#    6. Codex CLI (optional): OpenAI's installer (https://chatgpt.com/codex/install.sh), run as the one
#       who ran sudo, not as root: it installs into that account (~/.local/bin, ~/.codex) and adds
#       ~/.local/bin to that account's shell profile. Skipped when Codex is already installed and
#       signed in (codex login status); otherwise installs, or updates an install that is not signed in.
#       --skip-codex: skip step 6.  --update-codex: run the installer even when Codex is already there.
#       A failure here does not stop the setup. Later, or to update: python3 SETUP/setup.py --update-codex
#  A download is skipped when its file is already in SETUP/ next to this script (e.g. copied
#  from a USB stick); every file is checked against its SHA-256 before use.
#  A part that is already installed is skipped; delete its folder to reinstall.
#  Undo step 4: sudo rm /etc/paths.d/homehub /Library/Java/JavaVirtualMachines/homehub-temurin-11.jdk
# ============================================================================

HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 1
ROOT=$(cd "$HERE/.." && pwd -P) || exit 1           # the lab folder (project root) is the folder above SETUP/
cd "$ROOT" || exit 1
OWNER=${SUDO_USER:-root}                            # what this script makes belongs to the one who ran sudo

fail() { echo; echo "ERROR: $*"; exit 1; }
CODEX_MODE=auto                                     # auto: look for Codex here; skip / update: setup.py decided
for a in "$@"; do
  case "$a" in
    --skip-codex) CODEX_MODE=skip ;;
    --update-codex) CODEX_MODE=update ;;
    *) fail "unknown option: $a   (sudo sh SETUP/setup_mac.sh [--skip-codex | --update-codex]; usually: python3 SETUP/setup.py)" ;;
  esac
done
[ "$(id -u)" = 0 ] || fail "administrator rights are needed. Run the setup with:  python3 SETUP/setup.py"

if [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = 1 ]; then         # Apple chip (also under Rosetta)
  JDK_NAME=OpenJDK11U-jdk_aarch64_mac_hotspot_11.0.32.1_1.tar.gz
  JDK_SHA=c487a1c3a56588b3a32d0d07cdd526bf3d401c4b8422be772ca178bfcd647f3f
  DAFNY_NAME=dafny-4.11.0-arm64-macos-13.zip
  DAFNY_SHA=c90c75e7d5db9c6ccbb7127840dfe43f0ac938b039a7ebed146d8ead383a572f
else                                                                  # Intel
  JDK_NAME=OpenJDK11U-jdk_x64_mac_hotspot_11.0.32.1_1.tar.gz
  JDK_SHA=03de26f0d11ec3e6365e0352d9fcfaff447be35a2b2f36ee1ffb6063980343f5
  DAFNY_NAME=dafny-4.11.0-x64-macos-13.zip
  DAFNY_SHA=5fc0de946c5b2fad33f16bd22a5b06f4fd0dfa7f6d770284237e3f1f3ca9f73d
fi
JDK_URL=https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.32.1%2B1/$JDK_NAME
DAFNY_URL=https://github.com/dafny-lang/dafny/releases/download/v4.11.0/$DAFNY_NAME
PY_NAME=python-3.13.17-macos11.pkg
PY_URL=https://www.python.org/ftp/python/3.13.17/$PY_NAME
PY_SHA=3053592af66128269efab37fe7851a4894920b27c442aeec99ce4d34d17c07e3
PY_HOME=/Library/Frameworks/Python.framework/Versions/3.13

# fetch NAME URL SHA256 SIZE_TEXT   -> SETUP/NAME, checked against SHA256
fetch() {
  f="$HERE/$1"
  if [ ! -f "$f" ]; then
    echo "      downloading $2 ($4)"
    if ! curl -L --fail --retry 3 --progress-bar -o "$f" "$2"; then
      rm -f "$f"
      echo; echo "ERROR: download failed (internet/proxy). Put $1 in SETUP/ and run python3 SETUP/setup.py again:"; echo "       $2"
      return 1
    fi
    chown "$OWNER" "$f"
  fi
  h=$(shasum -a 256 "$f" | cut -d' ' -f1)
  if [ "$h" != "$3" ]; then
    echo "      SHA-256 mismatch: $h"; rm -f "$f"
    echo; echo "ERROR: $1 is damaged or not the expected file (deleted it). Run python3 SETUP/setup.py again."
    return 1
  fi
  xattr -d com.apple.quarantine "$f" 2>/dev/null
  echo "      file OK: $1 (SHA-256 checked)"
}

# unpack ARCHIVE TARGET_DIR FILE_INSIDE   -> <lab folder>/TARGET_DIR (FILE_INSIDE must exist there)
unpack() {
  d="$ROOT/$2"; t="$ROOT/_unpack_tmp"; src=""
  echo "      unpacking to $d ..."
  rm -rf "$t" && mkdir "$t" && tar -xf "$HERE/$1" -C "$t" 2>/dev/null \
    || { rm -rf "$t"; echo; echo "ERROR: could not unpack $1. Delete it and run python3 SETUP/setup.py again."; return 1; }
  if [ -f "$t/$3" ]; then src=$t; else
    for s in "$t"/*/; do [ -f "$s$3" ] && { src=${s%/}; break; }; done
  fi
  [ -n "$src" ] || { rm -rf "$t"; echo; echo "ERROR: no $3 in $1. Delete it and run python3 SETUP/setup.py again."; return 1; }
  rm -rf "$d" && mv "$src" "$d" && rm -rf "$t" || return 1
  xattr -dr com.apple.quarantine "$d" 2>/dev/null                   # Gatekeeper: as dafny's allow_on_mac.sh
  chown -R "$OWNER" "$d"
  echo "      done: $d/$3"
}

echo "==== HomeHub lab setup (macOS, administrator) ===="
echo "Lab folder: $ROOT"
echo

# ---------------------------------------------------------------- 1. JDK
echo "[1/6] JDK 11 (Eclipse Temurin 11.0.32.1+1)"
if [ -x "$ROOT/jdk/Contents/Home/bin/javac" ]; then
  echo "      skipped: already installed ($ROOT/jdk)"
else
  fetch "$JDK_NAME" "$JDK_URL" "$JDK_SHA" "about 180 MB" && unpack "$JDK_NAME" jdk Contents/Home/bin/javac || exit 1
fi

# ---------------------------------------------------------------- 2. Dafny
echo "[2/6] Dafny 4.11.0"
if [ -x "$ROOT/dafny/dafny" ]; then
  echo "      skipped: already installed ($ROOT/dafny)"
else
  fetch "$DAFNY_NAME" "$DAFNY_URL" "$DAFNY_SHA" "about 55 MB" && unpack "$DAFNY_NAME" dafny dafny || exit 1
fi

# ---------------------------------------------------------------- 3. Python
echo "[3/6] Python 3.8 or newer, .venv and Jupyter"
# sudo's PATH has no user folders, so these are looked at by name; /usr/bin/python3 only with the
# Command Line Tools (without them it opens an install dialog instead of running)
PY_EXE=""
for p in /opt/homebrew/bin/python3 /usr/local/bin/python3 /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 /usr/bin/python3; do
  [ -x "$p" ] || continue
  [ "$p" = /usr/bin/python3 ] && ! xcode-select -p >/dev/null 2>&1 && continue
  v=$("$p" --version 2>&1)
  if "$p" -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
    echo "      found: $p ($v), no install needed"; PY_EXE=$p; break
  fi
  echo "      too old: $p ($v)"
done
if [ -z "$PY_EXE" ]; then
  echo "      no Python 3.8 or newer: installing Python 3.13.17 (python.org)"
  fetch "$PY_NAME" "$PY_URL" "$PY_SHA" "about 71 MB" || exit 1
  xml="$HERE/_python_choices.xml"                                    # leave out: IDLE app, docs, shell profile change
  { echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
    echo '<plist version="1.0"><array>'
    for c in PythonApplications PythonDocumentation PythonProfileChanges; do
      echo "<dict><key>attributeSetting</key><integer>0</integer><key>choiceAttribute</key><string>selected</string><key>choiceIdentifier</key><string>org.python.Python.$c-3.13</string></dict>"
    done
    echo '</array></plist>'; } > "$xml"
  installer -pkg "$HERE/$PY_NAME" -target / -applyChoiceChangesXML "$xml"; rc=$?
  rm -f "$xml"
  [ $rc = 0 ] && [ -x "$PY_HOME/bin/python3" ] || fail "the Python installer failed."
  PY_EXE=$PY_HOME/bin/python3
fi

VPY="$ROOT/.venv/bin/python"
if [ -x "$VPY" ] && "$VPY" -c "import sys" >/dev/null 2>&1; then
  echo "      skipped: .venv already exists ($("$VPY" --version 2>&1))"
else
  [ -e "$ROOT/.venv" ] && { echo "      .venv does not run (its Python was removed?): making it again"; rm -rf "$ROOT/.venv"; }
  echo "      making $ROOT/.venv ..."
  "$PY_EXE" -m venv "$ROOT/.venv" || fail "could not make .venv with $PY_EXE."
  chown -R "$OWNER" "$ROOT/.venv"                                    # made as root: let its user install packages
  echo "      done: $VPY"
fi
echo "      installing jupyterlab into .venv (pip, from PyPI) ..."
as_owner() { if [ "$OWNER" = "$(id -un)" ]; then "$@"; else sudo -H -u "$OWNER" "$@"; fi; }   # not as root: no root-owned files in .venv
as_owner "$VPY" -m pip install --disable-pip-version-check -q jupyterlab \
  || fail "pip could not install jupyterlab into .venv (internet/proxy, or PyPI blocked?). Run python3 SETUP/setup.py again."
echo "      done: jupyterlab"

# ---------------------------------------------------------------- 4. environment
echo "[4/6] PATH and Java for all users"
printf '%s\n%s\n' "$ROOT/jdk/Contents/Home/bin" "$ROOT/dafny" > /etc/paths.d/homehub || fail "could not write /etc/paths.d/homehub."
echo "      PATH      : $ROOT/jdk/Contents/Home/bin"
echo "      PATH      : $ROOT/dafny"
mkdir -p /Library/Java/JavaVirtualMachines && ln -sfn "$ROOT/jdk" /Library/Java/JavaVirtualMachines/homehub-temurin-11.jdk \
  || fail "could not link the JDK into /Library/Java/JavaVirtualMachines."
echo "      JDK       : /Library/Java/JavaVirtualMachines/homehub-temurin-11.jdk -> $ROOT/jdk"

# ---------------------------------------------------------------- 5. versions
echo "[5/6] Versions"
"$ROOT/jdk/Contents/Home/bin/java" -version || fail "java did not run."
"$ROOT/jdk/Contents/Home/bin/javac" -version || fail "javac did not run."
"$ROOT/dafny/dafny" --version || fail "dafny did not run."
"$VPY" --version || fail ".venv/bin/python did not run."

# ---------------------------------------------------------------- 6. Codex CLI (optional)
echo "[6/6] Codex CLI (optional: skipped when already installed and signed in)"
CODEX_SH=https://chatgpt.com/codex/install.sh
OHOME=$(eval echo "~$OWNER")                                        # sudo's PATH has no ~/.local/bin: look by name
CODEX_BIN=""
for c in "$OHOME/.local/bin/codex" /opt/homebrew/bin/codex /usr/local/bin/codex; do [ -x "$c" ] && { CODEX_BIN=$c; break; }; done
if [ "$CODEX_MODE" = skip ]; then
  echo "      skipped (--skip-codex): already installed and signed in. To update:  python3 SETUP/setup.py --update-codex"
elif [ "$OWNER" = root ]; then
  echo "      skipped: run python3 SETUP/setup.py from your own account, so Codex goes into your home folder"
  elif [ "$CODEX_MODE" = auto ] && [ -n "$CODEX_BIN" ] && as_owner "$CODEX_BIN" login status >/dev/null 2>&1; then
  echo "      skipped: already installed and signed in ($CODEX_BIN, $(as_owner "$CODEX_BIN" --version 2>/dev/null))"
  echo "               to update:  python3 SETUP/setup.py --update-codex"
# downloaded to a file first: with `curl ... | sh` a failed download still ends as success
elif as_owner env CODEX_NON_INTERACTIVE=1 sh -c 'f=$(mktemp) && curl -fsSL -o "$f" "$1" && sh "$f"; rc=$?; rm -f "$f"; exit $rc' sh "$CODEX_SH"; then
  echo "      done. In a NEW Terminal window, sign in once:  codex login"
else
  echo "      WARNING: Codex was not installed or updated (internet/proxy, or chatgpt.com blocked?)."
  echo "               The lab works without it. Later:  python3 SETUP/setup.py --update-codex"
fi
echo
echo "OK. Open a NEW Terminal window (and restart VS Code / Jupyter) to use java, javac and dafny."
echo "    Next:  make check-env   (make comes with the Command Line Tools: xcode-select --install)"
exit 0
