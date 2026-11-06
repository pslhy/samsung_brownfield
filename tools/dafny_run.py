#!/usr/bin/env python3
"""dafny_run: run `dafny verify` and save the result as JSON (errors with file, line, message,
related locations) for tools/report.py. Prints a one-line summary.

  dafny_run.py --json OUT file.dfy|dfyconfig.toml ...  [-- extra dafny options]
"""
import json
import os
import re
import shutil
import subprocess
import sys

ERR = re.compile(r"^(.+?)\((\d+),(\d+)\): (Error|Related location): ?(.*)$")


def main():
    args = sys.argv[1:]
    out = args[args.index("--json") + 1]
    files = [x for i, x in enumerate(args) if args[i - 1] != "--json" and x != "--json"]
    dafny = os.environ.get("DAFNY") or shutil.which("dafny") or "dafny"
    p = subprocess.run([dafny, "verify"] + files, capture_output=True, text=True)
    text = p.stdout + p.stderr
    errors, cur = [], None
    for line in text.splitlines():
        m = ERR.match(line.strip())
        if m:
            f, ln, col, kind, msg = m.groups()
            if kind == "Error":
                cur = {"file": f, "line": int(ln), "col": int(col), "msg": msg, "related": []}
                errors.append(cur)
            elif cur is not None:
                cur["related"].append({"file": f, "line": int(ln), "col": int(col), "msg": msg})
    m = re.search(r"finished with (\d+) verified, (\d+) errors?", text)
    verified = int(m.group(1)) if m else None
    n_err = int(m.group(2)) if m else len(errors) or (0 if p.returncode == 0 else 1)
    summary = m.group(0) if m else (text.strip().splitlines()[-1] if text.strip() else "")
    if m is None and not errors and p.returncode != 0:
        errors.append({"file": "", "line": 0, "col": 0, "msg": text.strip()[-600:], "related": []})
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    json.dump({"files": files, "verified": verified, "errors_count": n_err, "errors": errors,
               "summary": summary, "output": text[-20000:]}, open(out, "w"), ensure_ascii=False)
    print("Dafny %-40s %s" % (" ".join(os.path.basename(f) for f in files)[:40],
                              "검증 %s개, 오류 %s개" % (verified if verified is not None else "?", n_err)))
    sys.exit(0 if n_err == 0 and p.returncode == 0 else 1)


if __name__ == "__main__":
    main()
