package com.dxlab.homehub.io;

/** Counters kept by the parser (read by ops dashboards through Metrics). */
public class ParseStats {
    public int parsed;
    public int malformed;
    public int skipped;

    public String toString() {
        return "parsed=" + parsed + ",malformed=" + malformed + ",skipped=" + skipped;
    }
}
