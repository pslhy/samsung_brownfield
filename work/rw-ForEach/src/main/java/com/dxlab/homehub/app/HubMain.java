package com.dxlab.homehub.app;

import com.dxlab.homehub.dispatch.SubmitResult;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintStream;

/**
 * Replays a workload file and prints an observable trace.
 *
 * Workload lines are wire-format events, or commands:
 *   !step   dispatch one event        !drain  dispatch all pending events
 *   !tick   run watchdog/recovery     !dump   print the audit log
 */
public final class HubMain {
    private HubMain() {
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: HubMain <workload.txt> [hub.properties]");
            System.exit(2);
        }
        HubConfig config = args.length > 1 ? HubConfig.load(args[1]) : new HubConfig();
        run(new HomeHub(config), args[0], System.out);
    }

    public static void run(HomeHub hub, String workload, PrintStream out) throws IOException {
        BufferedReader r = new BufferedReader(new FileReader(workload));
        try {
            String line;
            int lineNo = 0;
            while ((line = r.readLine()) != null) {
                lineNo++;
                String t = line.trim();
                if (t.length() == 0 || t.startsWith("#")) continue;
                String result;
                if (t.equals("!step")) {
                    result = hub.step() ? "stepped" : "idle";
                } else if (t.equals("!drain")) {
                    result = "drained " + hub.drain();
                } else if (t.equals("!tick")) {
                    hub.tick();
                    result = "ticked";
                } else if (t.equals("!dump")) {
                    out.print(hub.getAudit().dump());
                    continue;
                } else {
                    SubmitResult s = hub.ingest(t);
                    result = s.name();
                }
                out.println(lineNo + " " + result + " | " + hub.observable());
            }
        } finally {
            r.close();
        }
    }
}
