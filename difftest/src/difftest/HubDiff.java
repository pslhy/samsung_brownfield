package difftest;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintStream;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Whole-system differential testing between two builds of the hub (e.g. legacy vs. rewritten).
 *
 *   HubDiff <baseClassesDir> <changedClassesDir> [--runs N] [--len N] [--seed N] [--keep FILE]
 *
 * Each run generates a random workload (wire-format events + !step/!drain/!tick commands),
 * replays it on both builds through HubMain.run, and compares the observable traces line by
 * line. The first mismatching workload is shrunk (line removal) and written to --keep
 * (default: hubdiff-minimal.txt) so it can be added to the golden workloads.
 *
 * The generator deliberately produces the inputs a field hub sees: Fahrenheit reports
 * without a unit, repeated identical readings, unknown devices and codes.
 */
public final class HubDiff {
    static final String[] DEVICES = {"washer-1", "dryer-1", "fridge-1", "fridge-2", "aircon-1", "oven-1",
        "leak-1", "tv-1", "ghost-9"};
    static final String[] CODES = {"PWR_ON", "PWR_OFF", "CYC_S", "CYC_E", "TEMP", "TEMP", "TEMP", "DOOR_O",
        "DOOR_C", "LEAK", "HB", "ZZZ"};
    static final int[] TEMPS = {3, 4, 9, 11, 12, 12, 38, 39, 50};
    static final String[] UNITS = {"", "unit=C", "unit=C", "unit=F"};

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: HubDiff <baseClassesDir> <changedClassesDir> [--runs N] [--len N] [--seed N]");
            System.exit(2);
        }
        int runs = 200;
        int len = 40;
        long seed = 7;
        String keep = "hubdiff-minimal.txt";
        String json = null;
        for (int i = 2; i < args.length; i++) {
            if (args[i].equals("--runs")) runs = Integer.parseInt(args[++i]);
            else if (args[i].equals("--len")) len = Integer.parseInt(args[++i]);
            else if (args[i].equals("--seed")) seed = Long.parseLong(args[++i]);
            else if (args[i].equals("--keep")) keep = args[++i];
            else if (args[i].equals("--json")) json = args[++i];
        }
        Build base = new Build(args[0]);
        Build changed = new Build(args[1]);
        Random r = new Random(seed);
        for (int run = 0; run < runs; run++) {
            List<String> w = generate(r, len);
            if (firstDiff(base, changed, w) != null) {
                List<String> small = shrink(base, changed, w);
                FileWriter out = new FileWriter(keep);
                for (String l : small) out.write(l + "\n");
                out.close();
                String[] d = firstDiff(base, changed, small);
                System.out.println("MISMATCH (run " + run + ", seed " + seed + "): minimal workload with "
                        + small.size() + " lines written to " + keep);
                for (String l : small) System.out.println("    " + l);
                System.out.println("  base   : " + d[0]);
                System.out.println("  changed: " + d[1]);
                if (json != null) {
                    File f = new File(keep);
                    writeJson(json, "{\"ok\":false,\"runs\":" + runs + ",\"len\":" + len + ",\"keep\":" + q(keep)
                        + ",\"workload\":" + arr(small.toArray(new String[0]))
                        + ",\"base\":" + arr(base.trace(f.getPath()).split("\n"))
                        + ",\"changed\":" + arr(changed.trace(f.getPath()).split("\n")) + "}");
                }
                System.exit(1);
            }
        }
        System.out.println(runs + " random workloads (" + len + " lines each): identical traces");
        if (json != null) {
            writeJson(json, "{\"ok\":true,\"runs\":" + runs + ",\"len\":" + len + "}");
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

    static String arr(String[] xs) {
        StringBuilder b = new StringBuilder("[");
        for (int i = 0; i < xs.length; i++) b.append(i > 0 ? "," : "").append(q(xs[i]));
        return b.append("]").toString();
    }

    static void writeJson(String path, String text) throws IOException {
        FileWriter w = new FileWriter(path);
        w.write(text);
        w.close();
    }

    static List<String> generate(Random r, int len) {
        List<String> w = new ArrayList<String>();
        long seq = 1;
        for (int i = 0; i < len; i++) {
            int p = r.nextInt(100);
            if (p < 15) {
                w.add("!step");
            } else if (p < 22) {
                w.add("!drain");
            } else if (p < 26) {
                w.add("!tick");
            } else if (p < 27) {
                w.add("!dump");
            } else {
                String dev = DEVICES[r.nextInt(DEVICES.length)];
                String code = CODES[r.nextInt(CODES.length)];
                int value = code.equals("TEMP") ? TEMPS[r.nextInt(TEMPS.length)] : r.nextInt(2);
                String attrs = code.equals("TEMP") ? UNITS[r.nextInt(UNITS.length)] : (r.nextInt(8) == 0 ? "fw=2.1" : "");
                w.add(seq + "|" + dev + "|" + code + "|" + value + "|" + (seq * 60000) + (attrs.length() > 0 ? "|" + attrs : ""));
                seq++;
            }
        }
        return w;
    }

    static List<String> shrink(Build a, Build b, List<String> w) throws Exception {
        List<String> cur = new ArrayList<String>(w);
        boolean progress = true;
        while (progress) {
            progress = false;
            for (int i = cur.size() - 1; i >= 0; i--) {
                List<String> cand = new ArrayList<String>(cur);
                cand.remove(i);
                if (firstDiff(a, b, cand) != null) {
                    cur = cand;
                    progress = true;
                }
            }
        }
        return cur;
    }

    /** Returns {baseLine, changedLine} of the first difference, or null. */
    static String[] firstDiff(Build a, Build b, List<String> workload) throws Exception {
        File f = File.createTempFile("hubdiff", ".txt");
        f.deleteOnExit();
        FileWriter out = new FileWriter(f);
        for (String l : workload) out.write(l + "\n");
        out.close();
        String[] ta = a.trace(f.getPath()).split("\n", -1);
        String[] tb = b.trace(f.getPath()).split("\n", -1);
        for (int i = 0; i < Math.max(ta.length, tb.length); i++) {
            String x = i < ta.length ? ta[i] : "<end>";
            String y = i < tb.length ? tb[i] : "<end>";
            if (!x.equals(y)) return new String[] {x, y};
        }
        return null;
    }

    /** One build of the hub, loaded in its own class loader. */
    static final class Build {
        final URLClassLoader loader;

        Build(String classesDir) throws IOException {
            loader = new URLClassLoader(new URL[] {new File(classesDir).toURI().toURL()}, null);
        }

        String trace(String workload) throws Exception {
            Class<?> cfgC = loader.loadClass("com.dxlab.homehub.app.HubConfig");
            Class<?> hubC = loader.loadClass("com.dxlab.homehub.app.HomeHub");
            Class<?> mainC = loader.loadClass("com.dxlab.homehub.app.HubMain");
            Object hub = hubC.getConstructor(cfgC).newInstance(cfgC.getConstructor().newInstance());
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            PrintStream ps = new PrintStream(bytes, true, "UTF-8");
            Method run = mainC.getMethod("run", hubC, String.class, PrintStream.class);
            try {
                run.invoke(null, hub, workload, ps);
            } catch (java.lang.reflect.InvocationTargetException ex) {
                ps.println("EXCEPTION " + ex.getCause());
            }
            ps.flush();
            return bytes.toString("UTF-8");
        }
    }
}
