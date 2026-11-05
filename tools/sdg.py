#!/usr/bin/env python3
"""
sdg: system dependence graph of a compiled Java program, and forward slicing on it.

  1. Every method gets its dependence graph (defuse.build_pdg): instruction nodes with data and
     control dependences.
  2. Globals (fields, and the contents of arrays and collections held in fields) are treated as
     extra parameters: a method gets a formal-in node for every global it may read (itself or in
     a method it calls) and a formal-out node for every global it may write. Every call gets the
     matching actual-in / actual-out nodes.
  3. Methods are connected: call -> callee entry, actual-in -> formal-in (parameter-in),
     formal-out -> actual-out (parameter-out).
  4. Summary edges: at a call, actual-in x -> actual-out y when, inside the callee, formal-in x
     reaches formal-out y on a path that returns where it entered (computed by the worklist
     algorithm of Horwitz, Reps and Binkley, extended to the summary edges of nested calls).
  5. Methods nobody in the program calls (tests, main, API entry points) may be called in any
     order from outside: a global they write may be read by any of them afterwards.
  6. Forward slice in two phases, so that only paths that return to the caller they came from
     are followed: phase 1 follows data, control, summary and parameter-out edges (into callers);
     phase 2, from everything phase 1 reached, follows data, control, summary, call and
     parameter-in edges (into callees).
"""
from collections import defaultdict, deque

import defuse

DATA, CTL = defuse.DATA, defuse.CTL
CALL, PIN, POUT, SUM, GLOB = "call", "param-in", "param-out", "summary", "global"
PHASE1 = {DATA, CTL, SUM, POUT, GLOB}
PHASE2 = {DATA, CTL, SUM, CALL, PIN, GLOB}
INTRA = {DATA, CTL, SUM}


class SDG:
    def __init__(self, methods, targets, is_test):
        """methods: defuse.parse_methods result; targets: defuse.make_resolver; is_test(m) -> bool"""
        self.is_test = is_test
        self.pdg = {m: defuse.build_pdg(meth, targets) for m, meth in methods.items() if meth["insns"]}
        self.ids = {}            # (method or None, key) -> id
        self.nodes = []          # id -> (method, key)
        self.lines = []          # id -> source line or -1
        self.succ = defaultdict(list)    # id -> [(dst, kind)]
        self.pred = defaultdict(list)    # id -> [(src, kind)]  intra-method kinds only
        self._globals()
        self._build()
        self._summaries()

    # ------------------------------------------------------------------ construction
    def node(self, m, key, line=-1):
        k = (m, key)
        i = self.ids.get(k)
        if i is None:
            i = len(self.nodes)
            self.ids[k] = i
            self.nodes.append(k)
            self.lines.append(line)
        return i

    def edge(self, a, b, kind):
        self.succ[a].append((b, kind))
        if kind in INTRA:
            self.pred[b].append((a, kind))

    def _globals(self):
        """GREF/GMOD: globals each method may read/write, itself or in what it calls"""
        self.gref = {m: set(p.reads) for m, p in self.pdg.items()}
        self.gmod = {m: set(p.defs) for m, p in self.pdg.items()}
        changed = True
        while changed:
            changed = False
            for m, p in self.pdg.items():
                for tg, _, _ in p.calls.values():
                    for t in tg:
                        if t not in self.pdg:
                            continue
                        r = self.gref[t] - self.gref[m]
                        w = self.gmod[t] - self.gmod[m]
                        if r or w:
                            self.gref[m] |= r
                            self.gmod[m] |= w
                            changed = True
        # methods that may throw: a throw statement, or a call to such a method, not caught
        self.throws = {m for m, p in self.pdg.items() if any(x[0] == "i" for x in p.exc_srcs)}
        changed = True
        while changed:
            changed = False
            for m, p in self.pdg.items():
                if m in self.throws:
                    continue
                for x in p.exc_srcs:
                    if x[0] == "AO" and any(t in self.throws for t in p.calls[x[1]][0]):
                        self.throws.add(m)
                        changed = True
                        break
        self.callers = defaultdict(list)          # callee -> [(caller, call instruction)]
        for m, p in self.pdg.items():
            for k, (tg, _, _) in p.calls.items():
                for t in tg:
                    if t in self.pdg:
                        self.callers[t].append((m, k))

    def _build(self):
        N = self.node
        for m, p in self.pdg.items():
            N(m, ("E",))
            for j in range(p.nparams + 1):
                N(m, ("FI", j))
            for gl in sorted(self.gref[m]):
                self.edge(N(m, ("FI", gl)), N(m, ("V", gl)), DATA)
            fo_ret, fo_exc = N(m, ("FO", "ret")), N(m, ("FO", "exc"))
            for gl in sorted(self.gmod[m]):
                N(m, ("FO", gl))
            # nodes and dependences inside the method
            def silent(x):         # the exception of a call whose callees never throw
                return x[0] == "AO" and x[2] == "exc" and not any(t in self.throws for t in p.calls[x[1]][0])
            for key, srcs in sorted(p.deps.items(), key=lambda kv: repr(kv[0])):
                if silent(key):
                    continue
                d = N(m, key, p.line.get(key, -1))
                for s, kind in sorted(srcs, key=repr):
                    if not silent(s):
                        self.edge(N(m, s, p.line.get(s, -1)), d, kind)
            for s in sorted(p.ret_srcs, key=repr):
                self.edge(N(m, s, p.line.get(s, -1)), fo_ret, DATA)
            for s in sorted(p.exc_srcs, key=repr):
                if not silent(s):
                    self.edge(N(m, s, p.line.get(s, -1)), fo_exc, DATA)
            for gl, ws in sorted(p.defs.items()):
                for w in sorted(ws, key=repr):
                    wid = N(m, w, p.line.get(w, -1))
                    self.edge(wid, N(m, ("FO", gl)), DATA)
                    if gl in self.gref[m]:
                        self.edge(wid, N(m, ("V", gl)), DATA)
            # calls
            for k, (tg, name, owner) in sorted(p.calls.items()):
                tg = [t for t in tg if t in self.pdg]
                ln = p.line.get(("i", k), -1)
                C = N(m, ("i", k), ln)
                if not tg:
                    continue
                refs = set().union(*(self.gref[t] for t in tg))
                mods = set().union(*(self.gmod[t] for t in tg))
                for t in tg:
                    self.edge(C, self.node(t, ("E",)), CALL)
                # parameters
                for key in sorted((x for x in p.deps if x[0] == "AI"), key=repr):
                    if key[1] == k:
                        ai = N(m, key, ln)
                        for t in tg:
                            if key[2] <= self.pdg[t].nparams:
                                self.edge(ai, N(t, ("FI", key[2])), PIN)
                # globals passed in
                for gl in sorted(refs):
                    ai = N(m, ("AI", k, gl), ln)
                    self.edge(N(m, ("V", gl)), ai, DATA)
                    for t in tg:
                        if gl in self.gref[t]:
                            self.edge(ai, N(t, ("FI", gl)), PIN)
                # results: return value, exception, globals written
                init = name == "<init>"
                outs = [("ret",)] + ([("exc",)] if any(t in self.throws for t in tg) else []) + [(gl,) for gl in sorted(mods)]
                for (x,) in outs:
                    if x == "ret" and ("AO", k, "ret") not in p.line:
                        continue
                    ao = N(m, ("AO", k, x), ln)
                    # a constructor writing its own object's fields: the values do not depend on
                    # whether the object is made here
                    own = init and isinstance(x, tuple) and x[1].startswith(owner + ".")
                    if isinstance(x, tuple) and not own:
                        self.edge(C, ao, CTL)        # the callee writes it only if the call happens
                    for t in tg:
                        if x in ("ret", "exc") or x in self.gmod[t]:
                            self.edge(N(t, ("FO", x)), ao, POUT)
                    if isinstance(x, tuple):
                        self.edge(ao, N(m, ("FO", x)), DATA)
                        if x in self.gref[m]:
                            self.edge(ao, N(m, ("V", x)), DATA)
        # entry points: called from outside in any order
        roots = [m for m in self.pdg if not self.callers.get(m)]
        self.roots = roots
        for m in roots:
            for gl in sorted(self.gmod[m]):
                if not self.is_test(m):
                    self.edge(N(m, ("FO", gl)), N(None, ("G", gl)), GLOB)
            for gl in sorted(self.gref[m]):
                self.edge(N(None, ("G", gl)), N(m, ("FI", gl)), GLOB)

    def _summaries(self):
        """summary edges actual-in -> actual-out, Horwitz-Reps-Binkley style"""
        nodes, ids = self.nodes, self.ids
        path = defaultdict(set)          # node -> {formal-out it reaches inside its method}
        work = deque()

        def prop(u, w):
            if w not in path[u]:
                path[u].add(w)
                work.append((u, w))
        for i, (m, key) in enumerate(nodes):
            if m is not None and key[0] == "FO":
                prop(i, i)
        self.sums = set()
        while work:
            v, w = work.popleft()
            m, key = nodes[v]
            if key[0] == "FI":
                x, y = key[1], nodes[w][1][1]
                for (cm, k) in self.callers.get(m, ()):
                    ai = ids.get((cm, ("AI", k, x)))
                    ao = ids.get((cm, ("AO", k, y)))
                    if ai is None or ao is None:
                        continue
                    if (ai, ao) in self.sums:
                        continue
                    self.sums.add((ai, ao))
                    self.edge(ai, ao, SUM)
                    for a in list(path[ao]):
                        prop(ai, a)
            else:
                for u, _ in self.pred[v]:
                    prop(u, w)

    # ------------------------------------------------------------------ slicing
    def criterion(self, seeds):
        """seeds: {method: {lines}} -> nodes on those lines"""
        out = []
        for i, (m, key) in enumerate(self.nodes):
            if m not in seeds or self.lines[i] not in seeds[m]:
                continue
            # instructions, arguments computed and results received on the line; not the globals a
            # call merely passes through, nor whether a call on the line throws (the callee decides)
            if key[0] in ("i", "ie") or (key[0] == "AI" and isinstance(key[2], int)) or key[:1] + key[2:] == ("AO", "ret"):
                out.append(i)
        return out

    # cost of an edge when choosing the reason path shown to people: a hop through "the program is
    # called again from outside" is a last resort; every other step counts 1
    COST = {GLOB: 12}

    def slice(self, crit, block_test_args=True):
        """two-phase forward slice -> {node: (parent node or None, edge kind)}

        Phase 1 follows PHASE1 edges, phase 2 PHASE2 edges, and a path may switch from phase 1 to
        phase 2 once. The parent of each node is on a cheapest such path (see COST)."""
        import heapq
        dist, par_s = {}, {}
        heap = []
        for c in crit:
            st = (c, 1)
            if st not in dist:
                dist[st] = 0
                par_s[st] = (None, None)
                heapq.heappush(heap, (0, c, 1))
        done = set()
        while heap:
            dv, v, ph = heapq.heappop(heap)
            st = (v, ph)
            if st in done:
                continue
            done.add(st)
            if ph == 1 and (v, 2) not in dist:        # switch to phase 2 at no cost
                dist[(v, 2)] = dv
                par_s[(v, 2)] = (st, None)
                heapq.heappush(heap, (dv, v, 2))
            kinds = PHASE1 if ph == 1 else PHASE2
            mv = self.nodes[v][0]
            for d, kind in self.succ[v]:
                if kind not in kinds:
                    continue
                if block_test_args and kind in (CALL, PIN) and mv is not None and self.is_test(mv):
                    md, kd = self.nodes[d]
                    # test code is a client: what it computes does not change the production code it calls
                    if not self.is_test(md) and not (kind == PIN and isinstance(kd[1], tuple)):
                        continue
                nd = dv + self.COST.get(kind, 1)
                if nd < dist.get((d, ph), 1 << 60):
                    dist[(d, ph)] = nd
                    par_s[(d, ph)] = (st, kind)
                    heapq.heappush(heap, (nd, d, ph))
        best = {}
        for (v, ph) in done:
            if v not in best or dist[(v, ph)] < dist[best[v]]:
                best[v] = (v, ph)
        parent = {}
        for v, st in best.items():
            parent[v] = (st, par_s)
        return parent

    def path_to(self, parent, n):
        """node path criterion .. n, summary edges expanded into the callee's lines"""
        st, par_s = parent[n]
        p = []
        while st is not None:
            if not p or p[-1] != st[0]:
                p.append(st[0])
            st = par_s[st][0]
        p.reverse()
        return self.expand(p, 0)

    def expand(self, p, depth):
        out = [p[0]]
        for a, b in zip(p, p[1:]):
            if depth < 4 and (a, b) in self.sums and not any(
                    d == b and k in (DATA, CTL) for d, k in self.succ[a]):
                inner = self.inner_path(a, b)
                if inner:
                    out += self.expand(inner, depth + 1)
            out.append(b)
        return out

    def inner_path(self, ai, ao):
        """inside a callee: formal-in matching ai -> formal-out matching ao (BFS on intra edges)"""
        cm, (_, k, x) = self.nodes[ai]
        _, (_, _, y) = self.nodes[ao]
        tg = self.pdg[cm].calls[k][0]
        for t in tg:
            s, e = self.ids.get((t, ("FI", x))), self.ids.get((t, ("FO", y)))
            if s is None or e is None:
                continue
            par = {s: None}
            q = deque([s])
            while q:
                v = q.popleft()
                if v == e:
                    break
                for d, kind in self.succ[v]:
                    if kind in INTRA and d not in par:
                        par[d] = v
                        q.append(d)
            if e in par:
                path = []
                v = e
                while v is not None:
                    path.append(v)
                    v = par[v]
                return path[::-1]
        return None
