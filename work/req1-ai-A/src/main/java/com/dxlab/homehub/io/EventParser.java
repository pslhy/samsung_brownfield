package com.dxlab.homehub.io;

import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;

import java.util.HashMap;
import java.util.Map;

/**
 * Parses the hub wire format:
 *
 *   seq|deviceId|CODE|value|timestamp[|key=val;key=val]
 *
 * Lines starting with '#' and blank lines are skipped.
 * Any line that cannot be parsed is counted as malformed and dropped.
 */
public final class EventParser {
    private final ParseStats stats = new ParseStats();

    public Event parse(String line) {
        if (line == null) {
            stats.malformed++;
            return null;
        }
        String trimmed = line.trim();
        if (trimmed.length() == 0 || trimmed.startsWith("#")) {
            stats.skipped++;
            return null;
        }
        try {
            String[] f = trimmed.split("\\|");
            if (f.length < 5) {
                stats.malformed++;
                return null;
            }
            long seq = Long.parseLong(f[0].trim());
            String device = f[1].trim();
            EventType type = EventType.fromCode(f[2].trim());
            int value = Integer.parseInt(f[3].trim());
            long ts = Long.parseLong(f[4].trim());
            Map<String, String> attrs = new HashMap<String, String>();
            if (f.length > 5) {
                parseAttrs(f[5], attrs);
            }
            if (type == EventType.TEMP_REPORT) {
                // unit=F is normalized to Celsius; no unit means Celsius.
                String unit = attrs.get("unit");
                if ("F".equals(unit)) {
                    value = (value - 32) * 5 / 9;
                }
            }
            if (device.length() == 0) {
                stats.malformed++;
                return null;
            }
            stats.parsed++;
            return new Event(seq, device, type, value, ts, attrs);
        } catch (Exception ex) {
            stats.malformed++;
            return null;
        }
    }

    private static void parseAttrs(String raw, Map<String, String> out) {
        String[] pairs = raw.split(";");
        for (int i = 0; i < pairs.length; i++) {
            String p = pairs[i].trim();
            if (p.length() == 0) continue;
            int eq = p.indexOf('=');
            if (eq > 0) {
                out.put(p.substring(0, eq).trim(), p.substring(eq + 1).trim());
            }
        }
    }

    public ParseStats getStats() {
        return stats;
    }
}
