import com.dxlab.homehub.app.HomeHub;
import com.dxlab.homehub.app.HubConfig;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;

/**
 * Runs one message through a fresh HomeHub. Input file: setup lines (messages or !drain/!step/!tick),
 * then the message to look at as the last line. Prints the state before and after.
 * With a second argument "drain", the hub also dispatches everything queued (the message and the
 * events it leads to) before the state after is taken: the whole handling of the message.
 * LineTracer records the source lines executed between mark() and unmark().
 */
public final class IngestOne {
    static void mark() {
    }

    static void unmark() {
    }

    public static void main(String[] args) throws Exception {
        List<String> lines = new ArrayList<String>();
        BufferedReader r = new BufferedReader(new FileReader(args[0]));
        for (String l; (l = r.readLine()) != null; ) {
            if (l.trim().length() > 0) lines.add(l.trim());
        }
        r.close();
        HomeHub hub = new HomeHub(new HubConfig());
        for (int i = 0; i < lines.size() - 1; i++) {
            String t = lines.get(i);
            if (t.equals("!drain")) hub.drain();
            else if (t.equals("!step")) hub.step();
            else if (t.equals("!tick")) hub.tick();
            else hub.ingest(t);
        }
        String msg = lines.get(lines.size() - 1);
        System.out.println("MESSAGE " + msg);
        System.out.println("BEFORE 0 - | " + hub.observable());
        mark();
        String result = hub.ingest(msg).name();
        if (args.length > 1 && args[1].equals("drain")) hub.drain();
        unmark();
        System.out.println("AFTER 0 " + result + " | " + hub.observable());
        System.out.println("RESULT " + result);
    }
}
