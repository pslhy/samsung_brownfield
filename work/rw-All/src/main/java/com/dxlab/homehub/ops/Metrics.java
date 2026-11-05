package com.dxlab.homehub.ops;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Named counters exported to the ops dashboard. */
public final class Metrics {
    private final Map<String, Integer> counters = new HashMap<String, Integer>();

    public void increment(String name) {
        Integer old = counters.get(name);
        if (old == null) {
            counters.put(name, new Integer(1));
        } else {
            counters.put(name, new Integer(old.intValue() + 1));
        }
    }

    public int get(String name) {
        Integer v = counters.get(name);
        return v == null ? 0 : v.intValue();
    }

    public void reset() {
        counters.clear();
    }

    public boolean isEmpty() {
        return counters.isEmpty();
    }

    /** Stable textual snapshot: keys sorted, "k=v" joined by ','. */
    public String snapshot() {
        List<String> keys = new ArrayList<String>(counters.keySet());
        Collections.sort(keys);
        StringBuffer sb = new StringBuffer();
        for (String key : keys) {
            if (sb.length() > 0) sb.append(',');
            sb.append(key).append('=').append(counters.get(key));
        }
        return sb.toString();
    }
}
