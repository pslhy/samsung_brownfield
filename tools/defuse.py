#!/usr/bin/env python3
"""
defuse: the dependence graph of one compiled Java method (JDK only, via javap).

For one method it builds a program dependence graph (PDG) whose nodes are the method's
bytecode instructions, plus the nodes that connect it to other methods:

  ("i", k)          instruction k (its source line is known from the LineNumberTable)
  ("ie", k)         instruction k storing an object's contents into a field (putfield of a fresh array)
  ("E",)            method entry: "this method runs"
  ("x", k)          "library call k throws"
  ("FI", j)         formal-in: parameter j (j = 0 is the receiver)
  ("AI", k, j)      actual-in: argument j passed at the call instruction k
  ("AO", k, "ret")  actual-out: the value returned to the call instruction k
  ("AO", k, "exc")  actual-out: an exception thrown out of the callee at call k
  ("V", g)          every value the global g may hold inside this method

Globals are the heap abstraction: ("field", "C.f") is the value of field f (any object of class C),
("elem", "C.f") is the contents of the array or collection held in field f.

Edges (dependences, "src -> dst" means dst may change when src changes):

  data      a value defined at src is used at dst (through locals, the operand stack,
            or an object's contents)
  control   dst runs or not depending on the branch src (post-dominator based); side effects
            (field and array writes, calls) also depend on the method entry, values do not: what
            a method returns when it runs does not depend on whether it runs. Code in a catch
            block depends on the instructions in the try block that may throw

Global reads and writes are reported per method (reads, defs), so that sdg.py can connect the
methods: a field written in one method and read in another, the arguments of a call and the
callee's parameters, the callee's return value and the caller's use of it.

Library code (java.*) is not analyzed: a library call's result depends on its receiver, its
arguments and the receiver's contents; a call that is not known to be read-only writes the
receiver's contents. Calls a library makes back into application code (a Comparator passed to
Collections.sort, a lambda) are not followed.
"""
import re
from collections import defaultdict

import bytecode

INSN_RE = re.compile(r"^\s*(\d+):\s+([a-z_0-9]+)\s*(.*)$")
SWITCH_CASE_RE = re.compile(r"^\s*(-?\d+|default):\s+(\d+)\s*$")
EXC_ROW_RE = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\S.*)$")
LINE_RE = re.compile(r"^\s+line (\d+): (\d+)$")

# library methods that only read their receiver
PURE = {"get", "size", "isEmpty", "contains", "containsKey", "containsValue", "iterator", "hasNext",
        "next", "keySet", "entrySet", "values", "getKey", "getValue", "equals", "hashCode",
        "toString", "length", "charAt", "intValue", "longValue", "booleanValue", "compareTo",
        "startsWith", "endsWith", "trim", "split", "substring", "indexOf", "name", "ordinal",
        "getClass", "peek", "peekFirst", "peekLast", "subList", "toArray", "isPresent",
        "equalsIgnoreCase", "toLowerCase", "toUpperCase", "getOrDefault", "first", "last",
        "getFirst", "getLast", "stream", "listIterator", "hasPrevious", "previous", "clone",
        "close", "flush"}

BRANCH1 = {"ifeq", "ifne", "iflt", "ifge", "ifgt", "ifle", "ifnull", "ifnonnull"}
BRANCH2 = {"if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpge", "if_icmpgt", "if_icmple",
           "if_acmpeq", "if_acmpne"}
RETURNS = {"ireturn", "lreturn", "freturn", "dreturn", "areturn", "return"}
CAT2_PUSH = {"lconst_0", "lconst_1", "dconst_0", "dconst_1", "ldc2_w", "lload", "dload",
             "lload_0", "lload_1", "lload_2", "lload_3", "dload_0", "dload_1", "dload_2", "dload_3",
             "i2l", "f2l", "d2l", "i2d", "f2d", "l2d", "ladd", "lsub", "lmul", "ldiv", "lrem", "land",
             "lor", "lxor", "lshl", "lshr", "lushr", "lneg", "dadd", "dsub", "dmul", "ddiv", "drem",
             "dneg", "laload", "daload"}
BIN = {"iadd", "isub", "imul", "idiv", "irem", "iand", "ior", "ixor", "ishl", "ishr", "iushr",
       "ladd", "lsub", "lmul", "ldiv", "lrem", "land", "lor", "lxor", "lshl", "lshr", "lushr",
       "fadd", "fsub", "fmul", "fdiv", "frem", "dadd", "dsub", "dmul", "ddiv", "drem",
       "lcmp", "fcmpl", "fcmpg", "dcmpl", "dcmpg"}
UN = {"ineg", "lneg", "fneg", "dneg", "i2l", "i2f", "i2d", "l2i", "l2f", "l2d", "f2i", "f2l", "f2d",
      "d2i", "d2l", "d2f", "i2b", "i2c", "i2s", "checkcast", "instanceof"}
CONST = {"aconst_null", "iconst_m1", "iconst_0", "iconst_1", "iconst_2", "iconst_3", "iconst_4",
         "iconst_5", "lconst_0", "lconst_1", "fconst_0", "fconst_1", "fconst_2", "dconst_0",
         "dconst_1", "bipush", "sipush", "ldc", "ldc_w", "ldc2_w"}
ALOAD = {"iaload", "laload", "faload", "daload", "aaload", "baload", "caload", "saload"}
ASTORE = {"iastore", "lastore", "fastore", "dastore", "aastore", "bastore", "castore", "sastore"}
# exception types after which a catch block catches everything a call may throw
CATCH_ALL = {"any", "java/lang/Throwable", "java/lang/Exception", "java/lang/RuntimeException"}

DATA, CTL = "data", "ctl"
EMPTY = frozenset()


class Val:
    """an abstract operand: t = nodes that define it, o = where its contents live"""
    __slots__ = ("t", "cat", "o")

    def __init__(self, t=EMPTY, cat=1, o=EMPTY):
        self.t, self.cat, self.o = frozenset(t), cat, frozenset(o)

    def join(self, other):
        return Val(self.t | other.t, max(self.cat, other.cat), self.o | other.o)

    def key(self):
        return (self.t, self.cat, self.o)


def join_states(a, b):
    if a is None:
        return b
    la, sa, pa = a
    lb, sb, pb = b
    locs = dict(la)
    for k, v in lb.items():
        locs[k] = locs[k].join(v) if k in locs else v
    n = min(len(sa), len(sb))
    st = [sa[i].join(sb[i]) for i in range(n)]
    return (locs, st, pa | pb)


def state_key(s):
    locs, st, p = s
    return (tuple(sorted((k, v.key()) for k, v in locs.items())), tuple(v.key() for v in st), p)


def parse_methods(text):
    """javap -c -p -l output -> {canon: {cls, name, desc, static, insns, lines, handlers}}"""
    out = {}
    cur_cls = None
    cur = None
    pending = None
    mode = None
    last_switch = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.startswith(" ") and line.endswith("{"):
            hdr = bytecode.CLASS_HDR_RE.match(bytecode.strip_generics(line))
            if hdr:
                cur_cls = hdr.group(2)
            cur = None
            continue
        if cur_cls is None:
            continue
        if line.startswith("  ") and not line.startswith("   ") and line.endswith(";"):
            pending = line.strip()
            cur, mode = None, None
            continue
        if line.startswith("    descriptor:") and pending is not None:
            desc = line.split(":", 1)[1].strip()
            hdr, pending = pending, None
            if "(" not in desc:
                continue
            before = bytecode.strip_generics(hdr.split("(")[0])
            if hdr.startswith("static {}"):
                name = "<clinit>"
            else:
                last = before.split()[-1]
                name = "<init>" if last == cur_cls else last
            c = bytecode.canon(cur_cls, name, desc)
            cur = {"cls": cur_cls, "name": name, "desc": desc, "canon": c,
                   "static": " static " in " " + hdr.split("(")[0] + " ",
                   "insns": [], "lines": [], "handlers": []}
            out[c] = cur
            continue
        if cur is None:
            continue
        s = line.strip()
        if s == "Code:":
            mode = "code"
            continue
        if s == "LineNumberTable:":
            mode = "lines"
            continue
        if s.startswith("Exception table:"):
            mode = "exc"
            continue
        if s.endswith("Table:") or s.startswith("Exceptions:") or s.startswith("Signature:"):
            mode = None
            continue
        if mode == "code":
            m = INSN_RE.match(line)
            if m and not SWITCH_CASE_RE.match(line):
                pc, op, rest = int(m.group(1)), m.group(2), m.group(3)
                cur["insns"].append([pc, op, rest, []])
                last_switch = cur["insns"][-1] if op in ("tableswitch", "lookupswitch") else None
                continue
            sm = SWITCH_CASE_RE.match(line)
            if sm and last_switch is not None:
                last_switch[3].append(int(sm.group(2)))
        elif mode == "lines":
            lm = LINE_RE.match(line)
            if lm:
                cur["lines"].append((int(lm.group(2)), int(lm.group(1))))
        elif mode == "exc":
            em = EXC_ROW_RE.match(line)
            if em:
                typ = em.group(4).split()[-1]
                cur["handlers"].append((int(em.group(1)), int(em.group(2)), int(em.group(3)), typ))
    return out


def ref_member(rest):
    """'#7  // Field queue:Lx;' -> (kind, owner, name, desc); owner None means the current class"""
    c = rest.split("//", 1)[1].strip() if "//" in rest else ""
    kind, _, target = c.partition(" ")
    name_part, _, desc = target.partition(":")
    if "." in name_part:
        owner, name = name_part.rsplit(".", 1)
        owner = owner.replace("/", ".")
    else:
        owner, name = None, name_part
    return kind, owner, name.strip('"'), desc.strip()


def nargs(desc):
    return len(bytecode.parse_desc_params(desc))


def ret_cat(desc):
    r = desc[desc.index(")") + 1:]
    return 0 if r == "V" else (2 if r in ("J", "D") else 1)


def line_of(meth, pc):
    best = None
    for start, ln in meth["lines"]:
        if start <= pc and (best is None or start >= best[0]):
            best = (start, ln)
    return best[1] if best else -1


def cfg(meth):
    insns = meth["insns"]
    idx = {ins[0]: i for i, ins in enumerate(insns)}
    succ = defaultdict(list)
    for i, (pc, op, rest, cases) in enumerate(insns):
        nxt = i + 1 if i + 1 < len(insns) else None
        if op in RETURNS or op == "athrow":
            continue
        if op in ("goto", "goto_w"):
            succ[i].append(idx[int(rest.split()[0])])
            continue
        if op in ("tableswitch", "lookupswitch"):
            succ[i].extend(idx[t] for t in cases)
            continue
        if op in BRANCH1 or op in BRANCH2:
            succ[i].append(idx[int(rest.split()[0])])
        if nxt is not None:
            succ[i].append(nxt)
    return idx, succ


def control_deps(n, succ):
    """i -> set of branch instruction indices that i is directly control-dependent on"""
    EXIT = n
    nodes = list(range(n + 1))
    s2 = {i: (list(succ[i]) or [EXIT]) for i in range(n)}
    s2[EXIT] = []
    pdom = {v: set(nodes) for v in nodes}
    pdom[EXIT] = {EXIT}
    changed = True
    while changed:
        changed = False
        for v in reversed(range(n)):
            new = set.intersection(*(pdom[s] for s in s2[v])) | {v}
            if new != pdom[v]:
                pdom[v], changed = new, True
    ipdom = {}
    for v in range(n):
        strict = pdom[v] - {v}
        for c in strict:
            if pdom[c] == strict:      # post-dominators form a chain
                ipdom[v] = c
                break
    cd = defaultdict(set)
    for b in range(n):
        if len(set(s2[b])) < 2:
            continue
        stop = ipdom.get(b)
        for s in set(s2[b]):
            y = s
            while y is not None and y != stop and y != EXIT:
                if y != b:
                    cd[y].add(b)
                y = ipdom.get(y)
    return cd


class PDG:
    """dependence graph of one method; see the module docstring for the node keys"""

    def __init__(self, meth):
        self.meth = meth
        self.deps = defaultdict(set)       # node -> {(src node, DATA|CTL)}
        self.line = {}                     # node -> source line
        self.reads = set()                 # globals read directly
        self.defs = defaultdict(set)       # global -> nodes that write it directly
        self.calls = {}                    # call instruction k -> (targets, method name)
        self.ret_srcs = set()              # nodes whose value is returned
        self.exc_srcs = set()              # nodes whose exception leaves the method
        self.nparams = 0


def build_pdg(meth, targets):
    """meth: one entry of parse_methods; targets(kind, owner, name, desc) -> [application methods]"""
    g = PDG(meth)
    insns = meth["insns"]
    if not insns:
        return g
    n = len(insns)
    idx, succ = cfg(meth)
    cd = control_deps(n, succ)
    is_init = meth["name"] == "<init>"
    deps = g.deps
    for i, ins in enumerate(insns):
        ln = line_of(meth, ins[0])
        g.line[("i", i)] = ln
    covers = defaultdict(list)             # instruction -> [(handler index, catches everything)]
    for (fr, to, tgt, typ) in meth["handlers"]:
        for i, ins in enumerate(insns):
            if fr <= ins[0] < to:
                covers[i].append((idx[tgt], typ in CATCH_ALL))

    locs = {}
    slot, j = 0, 0
    if not meth["static"]:
        locs[0] = Val({("FI", 0)}, 1, {("param", 0)})
        slot = 1
    for p in bytecode.parse_desc_params(meth["desc"]):
        j += 1
        cat = 2 if p in ("long", "double") else 1
        locs[slot] = Val({("FI", j)}, cat, {("param", j)})
        slot += cat
    g.nparams = j

    alloc = defaultdict(frozenset)         # allocation site -> nodes that wrote its contents
    PASS = re.compile(r"^[ilfda]load(_\d)?$")

    def size():
        return sum(len(v) for v in deps.values()) + sum(len(v) for v in alloc.values()) + \
            sum(len(v) for v in g.defs.values()) + len(g.ret_srcs) + len(g.exc_srcs)

    for _round in range(10):
        before = size()
        states = [None] * n
        states[0] = (locs, [], EMPTY)
        work = [0]
        seen_keys = {}
        while work:
            i = work.pop()
            st = states[i]
            k = state_key(st)
            if seen_keys.get(i) == k:
                continue
            seen_keys[i] = k
            L, S, P = dict(st[0]), list(st[1]), st[2]
            pc, op, rest, cases = insns[i]
            K = ("i", i)
            ctl_src = {("i", b) for b in cd.get(i, ())} | set(P)
            thrower = None

            def control(node, effect=False, no_entry=False):
                # values depend on the branches above them; side effects (writes, calls) also
                # depend on whether the method runs at all
                srcs = set(ctl_src)
                if effect and not no_entry:
                    srcs.add(("E",))
                for s in srcs:
                    deps[node].add((s, CTL))

            def data(node, srcs):
                for s in srcs:
                    if s != node:
                        deps[node].add((s, DATA))

            def contents(origins):
                t = set()
                for o in origins:
                    if o[0] == "field":
                        gl = ("elem", o[1])
                        g.reads.add(gl)
                        t.add(("V", gl))
                    elif o[0] == "alloc":
                        t |= alloc[o[1]]
                    elif o[0] == "param":
                        t.add(("FI", o[1]))
                    elif o[0] == "node":
                        t.add(o[1])
                return t

            def push(t=EMPTY, cat=1, o=EMPTY):
                S.append(Val(t, cat, o))

            def pop():
                return S.pop() if S else Val()

            if PASS.match(op):
                slotn = int(op.split("_")[1]) if "_" in op else int(rest.split()[0])
                v = L.get(slotn, Val())
                push(v.t, 2 if op[0] in "ld" else 1, v.o)
            elif op in CONST:
                control(K)
                push({K}, 2 if op in CAT2_PUSH else 1)
            elif re.match(r"^[ilfda]store(_\d)?$", op):
                slotn = int(op.split("_")[1]) if "_" in op else int(rest.split()[0])
                v = pop()
                control(K)
                data(K, v.t)
                L[slotn] = Val({K}, v.cat, v.o)
            elif op == "iinc":
                slotn = int(rest.split()[0].rstrip(","))
                v = L.get(slotn, Val())
                control(K)
                data(K, v.t)
                L[slotn] = Val({K}, 1, v.o)
            elif op in BIN:
                b, a = pop(), pop()
                control(K)
                data(K, a.t | b.t)
                push({K}, 2 if op in CAT2_PUSH else 1)
            elif op in UN:
                a = pop()
                control(K)
                data(K, a.t)
                push({K}, 2 if op in CAT2_PUSH else 1, a.o if op == "checkcast" else EMPTY)
            elif op == "pop":
                pop()
            elif op == "pop2":
                a = pop()
                if a.cat == 1:
                    pop()
            elif op == "dup":
                a = pop(); S += [a, a]
            elif op == "dup_x1":
                a, b = pop(), pop(); S += [a, b, a]
            elif op == "dup_x2":
                a, b = pop(), pop()
                if b.cat == 2:
                    S += [a, b, a]
                else:
                    c = pop(); S += [a, c, b, a]
            elif op == "dup2":
                a = pop()
                if a.cat == 2:
                    S += [a, a]
                else:
                    b = pop(); S += [b, a, b, a]
            elif op == "dup2_x1":
                a = pop()
                if a.cat == 2:
                    b = pop(); S += [a, b, a]
                else:
                    b, c = pop(), pop(); S += [b, a, c, b, a]
            elif op == "swap":
                a, b = pop(), pop(); S += [a, b]
            elif op in ("getfield", "getstatic"):
                _, owner, name, desc = ref_member(rest)
                f = (owner or meth["cls"]) + "." + name
                if op == "getfield":
                    pop()                          # which object: not tracked (field-based heap)
                gl = ("field", f)
                g.reads.add(gl)
                control(K)
                data(K, {("V", gl)})
                push({K}, 2 if desc in ("J", "D") else 1, {("field", f)})
            elif op in ("putfield", "putstatic"):
                _, owner, name, desc = ref_member(rest)
                f = (owner or meth["cls"]) + "." + name
                v = pop()
                obj = pop() if op == "putfield" else Val()
                # a constructor initializing its own object: the stored value does not depend on
                # whether the constructor runs (that only decides whether the object exists)
                own = is_init and ("param", 0) in obj.o
                control(K, effect=True, no_entry=own)
                data(K, v.t)
                g.defs[("field", f)].add(K)
                if any(o[0] == "alloc" for o in v.o):
                    KE = ("ie", i)
                    g.line[KE] = g.line[K]
                    control(KE, effect=True, no_entry=own)
                    data(KE, contents(v.o))
                    g.defs[("elem", f)].add(KE)
            elif op in ALOAD:
                ix, arr = pop(), pop()
                control(K)
                data(K, ix.t | arr.t | contents(arr.o))
                push({K}, 2 if op in CAT2_PUSH else 1)
            elif op in ASTORE:
                v, ix, arr = pop(), pop(), pop()
                control(K, effect=any(o[0] == "field" for o in arr.o))
                data(K, v.t | ix.t | contents(v.o))
                for o in arr.o:
                    if o[0] == "field":
                        g.defs[("elem", o[1])].add(K)
                    elif o[0] == "alloc":
                        alloc[o[1]] = alloc[o[1]] | {K}
            elif op == "arraylength":
                a = pop()
                control(K)
                data(K, a.t)
                push({K})
            elif op == "new":
                push(EMPTY, 1, {("alloc", i)})
            elif op in ("newarray", "anewarray"):
                c = pop()
                control(K)
                data(K, c.t)
                push({K}, 1, {("alloc", i)})
            elif op == "multianewarray":
                dims = int(rest.split(",")[-1].split()[0])
                t = set()
                for _ in range(dims):
                    t |= pop().t
                control(K)
                data(K, t)
                push({K}, 1, {("alloc", i)})
            elif op.startswith("invoke") and op != "invokedynamic":
                kind, owner, name, desc = ref_member(rest)
                owner = owner or meth["cls"]
                args = [pop() for _ in range(nargs(desc))][::-1]
                recv = pop() if op != "invokestatic" else None
                allargs = ([recv] if recv is not None else []) + args
                tg = targets(op[6:], owner, name, desc)
                rc = ret_cat(desc)
                if tg:
                    control(K, effect=True)
                    g.calls[i] = (tg, name, owner)
                    base_j = 0 if recv is not None else 1
                    for jj, a in enumerate(allargs):
                        jx = base_j + jj
                        if jx == 0:
                            continue           # the receiver: which object is not tracked
                        AI = ("AI", i, jx)
                        g.line[AI] = g.line[K]
                        data(AI, a.t | contents(a.o))
                    AOX = ("AO", i, "exc")
                    g.line[AOX] = g.line[K]
                    control(AOX)
                    thrower = AOX
                    if rc:
                        AOR = ("AO", i, "ret")
                        g.line[AOR] = g.line[K]
                        control(AOR)
                        push({AOR}, rc, {("node", AOR)})
                else:
                    t = set()
                    for a in allargs:
                        t |= a.t | contents(a.o)
                    mut = recv is not None and (name not in PURE and name != "<init>" or (name == "<init>" and args))
                    control(K, effect=mut and any(o[0] == "field" for o in recv.o))
                    data(K, t)
                    # whether the library call throws depends on the values it is given (not on what
                    # is stored inside them, and not on whether this method runs)
                    KX = ("x", i)
                    g.line[KX] = g.line[K]
                    control(KX)
                    data(KX, set().union(*(a.t for a in allargs)) if allargs else set())
                    thrower = KX
                    if mut:
                        for o in recv.o:
                            if o[0] == "field":
                                g.defs[("elem", o[1])].add(K)
                            elif o[0] == "alloc":
                                alloc[o[1]] = alloc[o[1]] | {K}
                    if rc:
                        push({K}, rc, recv.o if recv is not None else EMPTY)
            elif op == "invokedynamic":
                _, _, name, desc = ref_member(rest)
                t = set()
                for _ in range(nargs(desc)):
                    a = pop()
                    t |= a.t | contents(a.o)
                control(K)
                data(K, t)
                rc = ret_cat(desc)
                if rc:
                    push({K}, rc)
            elif op in RETURNS:
                if op != "return":
                    v = pop()
                    control(K)
                    data(K, v.t | contents(v.o))
                    g.ret_srcs.add(K)
            elif op == "athrow":
                v = pop()
                control(K)
                data(K, v.t)
                thrower = K
            elif op in BRANCH1 or op in ("tableswitch", "lookupswitch"):
                a = pop()
                control(K)
                data(K, a.t)
            elif op in BRANCH2:
                b, a = pop(), pop()
                control(K)
                data(K, a.t | b.t)
            elif op in ("monitorenter", "monitorexit"):
                pop()
            elif op in ("goto", "goto_w", "nop"):
                pass
            else:
                raise RuntimeError("defuse: unsupported opcode %s in %s" % (op, meth["canon"]))

            # exceptions leaving the method: throw statements and what callees throw; a JDK call's
            # runtime exceptions (NullPointerException, ...) only matter for catch blocks here
            if thrower is not None and thrower[0] != "x" and not any(all_ for _, all_ in covers.get(i, ())):
                g.exc_srcs.add(thrower)
            new_state = (L, S, P)
            for s in succ[i]:
                old = states[s]
                states[s] = join_states(old, new_state)
                if old is None or state_key(old) != state_key(states[s]):
                    work.append(s)
            # catch blocks covering this instruction: they run only if it throws
            for hi, _ in covers.get(i, ()):
                extra = frozenset({thrower}) if thrower is not None else EMPTY
                hs = (dict(st[0]), [Val(extra)], P | extra)
                old = states[hi]
                states[hi] = join_states(old, hs)
                if old is None or state_key(old) != state_key(states[hi]):
                    work.append(hi)
        if size() == before:
            break
    return g


def make_resolver(model):
    """target resolution for one program: every override in the class hierarchy that may run"""
    subtypes = defaultdict(set)

    def all_supers(c):
        names, todo = set(), [c]
        while todo:
            x = todo.pop()
            if x in names:
                continue
            names.add(x)
            if x in model.classes:
                todo.append(model.classes[x]["super"])
                todo.extend(model.classes[x]["ifaces"])
        return names

    for c in model.classes:
        for s in all_supers(c):
            subtypes[s].add(c)

    def resolve(cls, name, desc):
        c = cls
        while c in model.classes:
            hit = model.declared[c].get((name, desc))
            if hit and not model.methods[hit]["abstract"]:
                return hit
            c = model.classes[c]["super"]
        return None

    def targets(kind, owner, name, desc):
        if owner not in model.classes:
            return []
        if kind in ("static", "special"):
            t = resolve(owner, name, desc)
            return [t] if t else []
        out = set()
        for s in subtypes.get(owner, ()):
            info = model.classes[s]
            if "interface" in info["flags"] or "abstract" in info["flags"]:
                continue
            t = resolve(s, name, desc)
            if t:
                out.add(t)
        return sorted(out)

    return targets
