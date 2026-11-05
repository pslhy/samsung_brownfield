package difftest;

import com.dxlab.homehub.dispatch.Dispatcher;
import com.dxlab.homehub.dispatch.EventHandler;
import com.dxlab.homehub.dispatch.HandlerRegistry;
import com.dxlab.homehub.dispatch.SubmitResult;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.ops.AuditLog;
import com.dxlab.homehub.ops.Metrics;
import com.dxlab.homehub.power.PowerBudget;
import com.dxlab.homehub.queue.EventQueue;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Differential testing: legacy Java class vs. the Dafny shadow model compiled to Java.
 *
 *   DiffTest queue|dispatcher|power|all [--runs N] [--len N] [--seed N] [--cap N]
 *            [--no-capacity]
 *
 * System properties select the implementations:
 *   -Djava.queue=com.dxlab.homehub.queue.RingEventQueue   Java queue class, needs (int) ctor
 *   -Dqueue.adapter=difftest.RingQueueAdapter              QueueModel adapter of the Dafny queue
 *                                                          (see QueueModel.java)
 *   -Dmodel.queue=RingQueueModel.RingQueue                 Dafny queue used by the dispatcher test
 *
 * Every step compares return values and the full observable state (queue contents, size,
 * dispatched count, load ...). On the first mismatch the operation sequence is shrunk
 * (greedy delta debugging) and printed: paste it into a regression test.
 *
 * Agreement on sampled inputs is evidence, not proof: it checks that the model you verified
 * describes the Java code you ship, on the inputs you tried.
 */
public final class DiffTest {

    static int runs = 300;
    static int len = 60;
    static long seed = 42;
    static int cap = 4;
    static boolean compareCapacity = true;
    static String jsonOut = null;
    static final StringBuilder json = new StringBuilder();
    /** when non-null, every comparison of a replay is recorded here (used for the HTML report) */
    static List<String[]> recorder = null;

    public static void main(String[] args) throws Exception {
        String target = args.length > 0 ? args[0] : "all";
        for (int i = 1; i < args.length; i++) {
            if (args[i].equals("--runs")) runs = Integer.parseInt(args[++i]);
            else if (args[i].equals("--len")) len = Integer.parseInt(args[++i]);
            else if (args[i].equals("--seed")) seed = Long.parseLong(args[++i]);
            else if (args[i].equals("--cap")) cap = Integer.parseInt(args[++i]);
            else if (args[i].equals("--no-capacity")) compareCapacity = false;
            else if (args[i].equals("--json")) jsonOut = args[++i];
        }
        boolean ok = true;
        if (target.equals("queue") || target.equals("all")) ok &= run(new QueueSubject());
        if (target.equals("dispatcher") || target.equals("all")) ok &= run(new DispatcherSubject());
        if (target.equals("power") || target.equals("all")) ok &= run(new PowerSubject());
        if (jsonOut != null) {
            java.io.FileWriter w = new java.io.FileWriter(jsonOut);
            w.write("{\"subjects\":[" + json + "]}");
            w.close();
        }
        System.exit(ok ? 0 : 1);
    }

    // ------------------------------------------------------------------ framework

    static final class Op {
        final String kind;
        final int a;
        final int b;

        Op(String kind, int a, int b) {
            this.kind = kind;
            this.a = a;
            this.b = b;
        }

        public String toString() {
            return kind + "(" + a + (b == Integer.MIN_VALUE ? "" : "," + b) + ")";
        }
    }

    interface Subject {
        String name();

        List<Op> generate(Random r);

        /** Replays ops on fresh Java and model objects; returns null or a mismatch description. */
        String replay(List<Op> ops) throws Exception;
    }

    static boolean run(Subject s) throws Exception {
        Random rnd = new Random(seed);
        long steps = 0;
        for (int i = 0; i < runs; i++) {
            List<Op> ops = s.generate(rnd);
            steps += ops.size();
            String bad = safeReplay(s, ops);
            if (bad != null) {
                List<Op> small = shrink(s, ops);
                recorder = new ArrayList<String[]>();
                String why = safeReplay(s, small);
                List<String[]> rec = recorder;
                recorder = null;
                System.out.println("[" + s.name() + "] MISMATCH (run " + i + ", seed " + seed + ")");
                System.out.println("  minimal sequence (" + small.size() + " ops): " + small);
                System.out.println("  " + why);
                addJson(s.name(), false, runs, steps, i, small, rec);
                return false;
            }
        }
        System.out.println("[" + s.name() + "] " + runs + " runs, " + steps + " ops: Java and model agree");
        addJson(s.name(), true, runs, steps, -1, null, null);
        return true;
    }

    static List<Op> shrink(Subject s, List<Op> ops) throws Exception {
        List<Op> cur = new ArrayList<Op>(ops);
        boolean progress = true;
        while (progress) {
            progress = false;
            for (int i = cur.size() - 1; i >= 0; i--) {
                List<Op> cand = new ArrayList<Op>(cur);
                cand.remove(i);
                if (safeReplay(s, cand) != null) {
                    cur = cand;
                    progress = true;
                }
            }
        }
        return cur;
    }

    /** A crash on either side counts as a mismatch. */
    static String safeReplay(Subject s, List<Op> ops) {
        try {
            return s.replay(ops);
        } catch (Throwable t) {
            Throwable c = t;
            while (c.getCause() != null) c = c.getCause();
            return "exception: " + c;
        }
    }

    static String q(String x) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : x.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 32) b.append(' ');
            else b.append(c);
        }
        return b.append('"').toString();
    }

    static void addJson(String name, boolean ok, int runs, long ops, int run, List<Op> small, List<String[]> rec) {
        if (json.length() > 0) json.append(',');
        json.append("{\"name\":").append(q(name)).append(",\"ok\":").append(ok)
            .append(",\"runs\":").append(runs).append(",\"ops\":").append(ops)
            .append(",\"seed\":").append(seed).append(",\"run\":").append(run);
        if (small != null) {
            json.append(",\"minimal\":[");
            for (int i = 0; i < small.size(); i++) json.append(i > 0 ? "," : "").append(q(small.get(i).toString()));
            json.append("],\"steps\":[");
            int cur = -1;
            boolean firstStep = true;
            for (String[] r : rec) {
                int st = Integer.parseInt(r[0]);
                if (st != cur) {
                    if (cur >= 0) json.append("]}");
                    json.append(firstStep ? "" : ",").append("{\"i\":").append(st).append(",\"op\":").append(q(r[1]))
                        .append(",\"checks\":[");
                    firstStep = false;
                    cur = st;
                } else {
                    json.append(",");
                }
                json.append("{\"what\":").append(q(r[2])).append(",\"java\":").append(q(r[3]))
                    .append(",\"model\":").append(q(r[4])).append(",\"ok\":").append(r[3].equals(r[4])).append("}");
            }
            if (cur >= 0) json.append("]}");
            json.append("]");
        }
        json.append("}");
    }

    static String check(int step, Op op, String what, Object javaV, Object modelV) {
        if (recorder != null) {
            recorder.add(new String[] {String.valueOf(step), op.toString(), what, String.valueOf(javaV), String.valueOf(modelV)});
        }
        if (String.valueOf(javaV).equals(String.valueOf(modelV))) return null;
        return "step " + step + " " + op + ": " + what + " java=" + javaV + " model=" + modelV;
    }

    // ------------------------------------------------------------------ helpers

    static Event javaEvent(int id, boolean critical) {
        return critical
                ? new Event(id, "leak-1", EventType.LEAK_DETECTED, 1, id)
                : new Event(id, "tv-1", EventType.HEARTBEAT, 0, id);
    }

    static Types.Ev modelEvent(int id, boolean critical) {
        return Types.Ev.create(id, critical);
    }

    static String javaIds(List<Event> evs) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < evs.size(); i++) {
            if (i > 0) sb.append(',');
            sb.append(evs.get(i) == null ? "null" : String.valueOf(evs.get(i).getSeq()));
        }
        return sb.append(']').toString();
    }

    static String modelIds(Object dafnySeq) {
        dafny.DafnySequence<?> s = (dafny.DafnySequence<?>) dafnySeq;
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < s.length(); i++) {
            if (i > 0) sb.append(',');
            sb.append(((Types.Ev) s.select(i)).dtor_id());
        }
        return sb.append(']').toString();
    }

    static Object call(Object target, String method, Object... args) throws Exception {
        for (Method m : target.getClass().getMethods()) {
            if (m.getName().equals(method) && m.getParameterTypes().length == args.length) {
                return m.invoke(target, args);
            }
        }
        throw new NoSuchMethodException(target.getClass().getName() + "." + method);
    }

    static EventQueue newJavaQueue(int capacity) throws Exception {
        String cls = System.getProperty("java.queue", "com.dxlab.homehub.queue.RingEventQueue");
        return (EventQueue) Class.forName(cls).getConstructor(int.class).newInstance(capacity);
    }

    static QueueModel newQueueAdapter(int capacity) throws Exception {
        String cls = System.getProperty("queue.adapter", "difftest.RingQueueAdapter");
        QueueModel m = (QueueModel) Class.forName(cls).getConstructor().newInstance();
        m.init(capacity);
        return m;
    }

    static Object newModelQueue(int capacity) throws Exception {
        String cls = System.getProperty("model.queue", "RingQueueModel.RingQueue");
        Object q = Class.forName(cls).getConstructor().newInstance();
        call(q, "__ctor", capacity);
        return q;
    }

    /** Uses the (…, maxPending) constructor when the Java class has one (REQ-1), with maxPending = cap. */
    static Dispatcher newJavaDispatcher(EventQueue q, HandlerRegistry reg, boolean autoDrain) throws Exception {
        try {
            return Dispatcher.class.getConstructor(EventQueue.class, HandlerRegistry.class, Metrics.class,
                    AuditLog.class, boolean.class, int.class)
                    .newInstance(q, reg, new Metrics(), new AuditLog(), autoDrain, cap);
        } catch (NoSuchMethodException legacy) {
            return new Dispatcher(q, reg, new Metrics(), new AuditLog(), autoDrain);
        }
    }

    static Object newModelDispatcher(Object q, boolean autoDrain) throws Exception {
        Object d = Class.forName("DispatcherModel.Dispatcher").getConstructor().newInstance();
        for (Method m : d.getClass().getMethods()) {
            if (m.getName().equals("__ctor") && m.getParameterTypes().length == 3) {
                m.invoke(d, q, autoDrain, cap);
                return d;
            }
        }
        call(d, "__ctor", q, autoDrain);
        return d;
    }

    // ------------------------------------------------------------------ queue

    static final class QueueSubject implements Subject {
        public String name() {
            return "queue";
        }

        public List<Op> generate(Random r) {
            List<Op> ops = new ArrayList<Op>();
            int id = 1;
            for (int i = 0; i < len; i++) {
                int p = r.nextInt(100);
                if (p < 55) ops.add(new Op("offer", id++, r.nextInt(5) == 0 ? 1 : 0));
                else if (p < 90) ops.add(new Op("poll", 0, Integer.MIN_VALUE));
                else if (p < 96) ops.add(new Op("peek", 0, Integer.MIN_VALUE));
                else ops.add(new Op("clear", 0, Integer.MIN_VALUE));
            }
            return ops;
        }

        public String replay(List<Op> ops) throws Exception {
            EventQueue j = newJavaQueue(cap);
            QueueModel m = newQueueAdapter(cap);
            for (int i = 0; i < ops.size(); i++) {
                Op op = ops.get(i);
                String bad = null;
                if (op.kind.equals("offer")) {
                    bad = check(i, op, "offer", j.offer(javaEvent(op.a, op.b == 1)), m.offer(op.a, op.b == 1));
                } else if (op.kind.equals("poll")) {
                    Event e = j.poll();
                    Integer mv = m.poll();
                    bad = check(i, op, "poll", e == null ? "none" : String.valueOf(e.getSeq()), mv == null ? "none" : mv);
                } else if (op.kind.equals("peek")) {
                    Event e = j.peek();
                    Integer mv = m.peek();
                    bad = check(i, op, "peek", e == null ? "none" : String.valueOf(e.getSeq()), mv == null ? "none" : mv);
                } else {
                    j.clear();
                    m.clear();
                }
                if (bad == null) bad = check(i, op, "size", j.size(), m.size());
                if (bad == null) bad = check(i, op, "isEmpty", j.isEmpty(), m.isEmpty());
                if (bad == null) bad = check(i, op, "contents", javaIds(j.snapshot()), m.snapshot().toString().replace(" ", ""));
                if (bad == null && compareCapacity) bad = check(i, op, "capacity", j.capacity(), m.capacity());
                if (bad != null) return bad;
            }
            return null;
        }
    }

    // ------------------------------------------------------------------ dispatcher

    static final class DispatcherSubject implements Subject {
        public String name() {
            return "dispatcher";
        }

        public List<Op> generate(Random r) {
            List<Op> ops = new ArrayList<Op>();
            ops.add(new Op("config", r.nextBoolean() ? 1 : 0, Integer.MIN_VALUE));
            int id = 1;
            for (int i = 0; i < len; i++) {
                int p = r.nextInt(100);
                if (p < 70) ops.add(new Op("submit", id++, r.nextInt(3) == 0 ? 1 : 0));
                else if (p < 95) ops.add(new Op("dispatchOne", 0, Integer.MIN_VALUE));
                else ops.add(new Op("drain", 0, Integer.MIN_VALUE));
            }
            return ops;
        }

        public String replay(List<Op> ops) throws Exception {
            boolean autoDrain = !ops.isEmpty() && ops.get(0).kind.equals("config") && ops.get(0).a == 1;
            EventQueue jq = newJavaQueue(cap);
            final List<Event> handled = new ArrayList<Event>();
            HandlerRegistry reg = new HandlerRegistry();
            reg.setFallback(new EventHandler() {
                public void handle(Event e) {
                    handled.add(e);
                }

                public String name() {
                    return "record";
                }
            });
            Dispatcher j = newJavaDispatcher(jq, reg, autoDrain);
            Object mq = newModelQueue(cap);
            Object m = newModelDispatcher(mq, autoDrain);
            for (int i = 0; i < ops.size(); i++) {
                Op op = ops.get(i);
                String bad = null;
                if (op.kind.equals("submit")) {
                    SubmitResult jr = j.submit(javaEvent(op.a, op.b == 1));
                    Object mr = call(m, "Submit", modelEvent(op.a, op.b == 1));
                    String ms = (Boolean) call(mr, "is_ACCEPTED") ? "ACCEPTED"
                            : (Boolean) call(mr, "is_ACCEPTED__EVICTED") ? "ACCEPTED_EVICTED"
                            : (Boolean) call(mr, "is_ACCEPTED__DRAINED") ? "ACCEPTED_DRAINED" : "REJECTED_FULL";
                    bad = check(i, op, "submit", jr.name(), ms);
                } else if (op.kind.equals("dispatchOne")) {
                    Event e = j.dispatchOne();
                    dafny.Tuple2<?, ?> t = (dafny.Tuple2<?, ?>) call(m, "DispatchOne");
                    String mv = (Boolean) t.dtor__0() ? String.valueOf(((Types.Ev) t.dtor__1()).dtor_id()) : "none";
                    bad = check(i, op, "dispatchOne", e == null ? "none" : String.valueOf(e.getSeq()), mv);
                } else if (op.kind.equals("drain")) {
                    bad = check(i, op, "drain", j.drain(), call(m, "Drain"));
                }
                if (bad == null) bad = check(i, op, "contents", javaIds(jq.snapshot()), modelIds(call(mq, "Snapshot")));
                if (bad == null) bad = check(i, op, "dispatchedCount", j.getDispatchedCount(),
                        m.getClass().getField("dispatchedCount").get(m));
                if (bad != null) return bad;
            }
            return null;
        }
    }

    // ------------------------------------------------------------------ power budget

    static final class PowerSubject implements Subject {
        static final int CAP = 4000;
        static final int[] WATTS = {-5, 0, 1, 120, 150, 1800, 2000, 2200, 2500, 3637, CAP, CAP + 1, Integer.MAX_VALUE};

        public String name() {
            return "power";
        }

        public List<Op> generate(Random r) {
            List<Op> ops = new ArrayList<Op>();
            for (int i = 0; i < len; i++) {
                int p = r.nextInt(100);
                int dev = r.nextInt(5);
                if (p < 55) ops.add(new Op("tryStart", dev, WATTS[r.nextInt(WATTS.length)]));
                else if (p < 90) ops.add(new Op("stop", dev, Integer.MIN_VALUE));
                else if (p < 97) ops.add(new Op("isRunning", dev, Integer.MIN_VALUE));
                else ops.add(new Op("stopAll", 0, Integer.MIN_VALUE));
            }
            return ops;
        }

        public String replay(List<Op> ops) throws Exception {
            PowerBudget j = new PowerBudget(CAP);
            PowerBudgetModel.PowerBudget m = new PowerBudgetModel.PowerBudget();
            m.__ctor(CAP);
            for (int i = 0; i < ops.size(); i++) {
                Op op = ops.get(i);
                String id = "dev-" + op.a;
                String bad = null;
                if (op.kind.equals("tryStart")) {
                    bad = check(i, op, "tryStart", j.tryStart(id, op.b), m.TryStart(op.a, op.b));
                } else if (op.kind.equals("stop")) {
                    j.stop(id);
                    m.Stop(op.a);
                } else if (op.kind.equals("isRunning")) {
                    bad = check(i, op, "isRunning", j.isRunning(id), m.IsRunning(op.a));
                } else {
                    j.stopAll();
                    m.StopAll();
                }
                if (bad == null) bad = check(i, op, "totalLoad", j.totalLoad(), m.TotalLoad());
                if (bad == null) bad = check(i, op, "headroom", j.headroom(), m.Headroom());
                if (bad == null) bad = check(i, op, "isIdle", j.isIdle(), m.IsIdle());
                if (bad != null) return bad;
            }
            return null;
        }
    }
}
