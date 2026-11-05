#!/usr/bin/env python3
"""trace_check: replay the workload files on a build and compare with the recorded (golden) traces.

  trace_check.py --cp CLASSES --json OUT [--golden golden] [--workloads legacy/workloads] name ...
"""
import argparse
import json
import os
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cp", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--golden", default="golden")
    ap.add_argument("--workloads", default="legacy/workloads")
    ap.add_argument("--save", default="build", help="where to save this run's traces")
    ap.add_argument("names", nargs="+")
    a = ap.parse_args()
    env = dict(os.environ)
    env.pop("JAVA_TOOL_OPTIONS", None)
    res, ok = [], True
    os.makedirs(a.save, exist_ok=True)
    for n in a.names:
        p = subprocess.run(["java", "-cp", a.cp, "com.dxlab.homehub.app.HubMain",
                            os.path.join(a.workloads, n + ".txt")], capture_output=True, text=True, env=env)
        got = p.stdout.splitlines()
        open(os.path.join(a.save, n + ".trace"), "w").write(p.stdout)
        exp = open(os.path.join(a.golden, n + ".trace")).read().splitlines()
        diffs = []
        for i in range(max(len(got), len(exp))):
            g = got[i] if i < len(got) else ""
            x = exp[i] if i < len(exp) else ""
            if g != x:
                diffs.append([i + 1, x, g])
        if p.returncode != 0:
            diffs.insert(0, [0, "(정상 종료)", "실행 오류: " + p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "실행 오류"])
        same = not diffs
        ok &= same
        wl = open(os.path.join(a.workloads, n + ".txt")).read().splitlines()
        res.append({"name": n, "same": same, "lines": len(exp), "diffs": diffs, "workload": wl})
        print("기록 %-16s %s" % (n, "같음" if same else "다름 (%d줄)" % len(diffs)))
    os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
    json.dump({"workloads": res}, open(a.json, "w"), ensure_ascii=False)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
