import com.sun.jdi.Bootstrap;
import com.sun.jdi.Location;
import com.sun.jdi.Method;
import com.sun.jdi.ReferenceType;
import com.sun.jdi.VirtualMachine;
import com.sun.jdi.connect.Connector;
import com.sun.jdi.connect.LaunchingConnector;
import com.sun.jdi.event.BreakpointEvent;
import com.sun.jdi.event.ClassPrepareEvent;
import com.sun.jdi.event.Event;
import com.sun.jdi.event.EventSet;
import com.sun.jdi.event.ExceptionEvent;
import com.sun.jdi.event.StepEvent;
import com.sun.jdi.event.VMDeathEvent;
import com.sun.jdi.event.VMDisconnectEvent;
import com.sun.jdi.request.BreakpointRequest;
import com.sun.jdi.request.ClassPrepareRequest;
import com.sun.jdi.request.EventRequest;
import com.sun.jdi.request.EventRequestManager;
import com.sun.jdi.request.ExceptionRequest;
import com.sun.jdi.request.StepRequest;

import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.util.Map;

/**
 * LineTracer CLASSPATH INPUTFILE [drain]: runs IngestOne under the debugger interface (JDI) and prints, as
 * JSON, the program output and every source line of com.dxlab.homehub executed while the message is
 * handled, with the exceptions thrown on the way and where they were caught.
 */
public final class LineTracer {
    public static void main(String[] a) throws Exception {
        LaunchingConnector lc = Bootstrap.virtualMachineManager().defaultConnector();
        Map<String, Connector.Argument> args = lc.defaultArguments();
        args.get("options").setValue("-cp " + a[0]);
        StringBuilder main = new StringBuilder("IngestOne");
        for (int i = 1; i < a.length; i++) main.append(' ').append(a[i]);
        args.get("main").setValue(main.toString());
        VirtualMachine vm = lc.launch(args);
        final ByteArrayOutputStream out = new ByteArrayOutputStream();
        Thread pump = pump(vm.process().getInputStream(), out);
        Thread pumpErr = pump(vm.process().getErrorStream(), new ByteArrayOutputStream());
        EventRequestManager erm = vm.eventRequestManager();
        ClassPrepareRequest cpr = erm.createClassPrepareRequest();
        cpr.addClassFilter("IngestOne");
        cpr.enable();
        StringBuilder steps = new StringBuilder();
        StringBuilder excs = new StringBuilder();
        StepRequest step = null;
        ExceptionRequest exr = null;
        int n = 0;
        loop:
        while (true) {
            EventSet es = vm.eventQueue().remove();
            for (Event e : es) {
                if (e instanceof ClassPrepareEvent) {
                    ReferenceType t = ((ClassPrepareEvent) e).referenceType();
                    for (Method m : t.methodsByName("mark")) brk(erm, m);
                    for (Method m : t.methodsByName("unmark")) brk(erm, m);
                } else if (e instanceof BreakpointEvent) {
                    BreakpointEvent b = (BreakpointEvent) e;
                    if (b.location().method().name().equals("mark")) {
                        step = erm.createStepRequest(b.thread(), StepRequest.STEP_LINE, StepRequest.STEP_INTO);
                        step.addClassFilter("com.dxlab.homehub.*");
                        step.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
                        step.enable();
                        exr = erm.createExceptionRequest(null, true, true);
                        exr.addClassFilter("com.dxlab.homehub.*");
                        exr.enable();
                    } else {
                        if (step != null) step.disable();
                        if (exr != null) exr.disable();
                    }
                } else if (e instanceof StepEvent) {
                    Location l = ((StepEvent) e).location();
                    if (n++ < 5000) {
                        if (steps.length() > 0) steps.append(',');
                        steps.append('[').append(q(l.declaringType().name())).append(',')
                             .append(q(l.method().name())).append(',').append(l.lineNumber()).append(']');
                    }
                } else if (e instanceof ExceptionEvent) {
                    ExceptionEvent x = (ExceptionEvent) e;
                    Location l = x.location();
                    Location c = x.catchLocation();
                    if (excs.length() > 0) excs.append(',');
                    excs.append("{\"type\":").append(q(x.exception().referenceType().name()))
                        .append(",\"cls\":").append(q(l.declaringType().name()))
                        .append(",\"method\":").append(q(l.method().name()))
                        .append(",\"line\":").append(l.lineNumber())
                        .append(",\"step\":").append(n)
                        .append(",\"catch_cls\":").append(c == null ? "null" : q(c.declaringType().name()))
                        .append(",\"catch_line\":").append(c == null ? -1 : c.lineNumber()).append('}');
                } else if (e instanceof VMDeathEvent || e instanceof VMDisconnectEvent) {
                    break loop;
                }
            }
            es.resume();
        }
        pump.join();
        pumpErr.join();
        System.out.println("{\"output\":" + q(out.toString("UTF-8")) + ",\"steps\":[" + steps + "],\"exceptions\":["
                           + excs + "],\"truncated\":" + (n > 5000) + "}");
    }

    static void brk(EventRequestManager erm, Method m) {
        BreakpointRequest r = erm.createBreakpointRequest(m.location());
        r.enable();
    }

    static Thread pump(final InputStream in, final ByteArrayOutputStream out) {
        Thread t = new Thread() {
            public void run() {
                byte[] b = new byte[4096];
                try {
                    for (int k; (k = in.read(b)) > 0; ) out.write(b, 0, k);
                } catch (Exception ignored) {
                }
            }
        };
        t.start();
        return t;
    }

    static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c == '\n') b.append("\\n");
            else if (c == '\r') continue;
            else if (c < 32) b.append(' ');
            else b.append(c);
        }
        return b.append('"').toString();
    }
}
