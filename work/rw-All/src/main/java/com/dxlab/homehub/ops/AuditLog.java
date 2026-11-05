package com.dxlab.homehub.ops;

import com.dxlab.homehub.model.Event;

import java.util.ArrayList;
import java.util.List;

/** Bounded in-memory audit trail. Oldest entries are discarded first. */
public final class AuditLog {
    public static final int DEFAULT_MAX = 500;

    private final List<String> entries = new ArrayList<String>();
    private final int maxEntries;

    public AuditLog() {
        this(DEFAULT_MAX);
    }

    public AuditLog(int maxEntries) {
        this.maxEntries = maxEntries;
    }

    public void record(String tag, Event e) {
        entries.add(tag + (e == null ? "" : ":" + e.getSeq() + "@" + e.getDeviceId()));
        if (entries.size() > maxEntries) {
            entries.remove(0);
        }
    }

    public void note(String tag, String detail) {
        entries.add(tag + ":" + detail);
        if (entries.size() > maxEntries) {
            entries.remove(0);
        }
    }

    public int size() {
        return entries.size();
    }

    public boolean contains(String prefix) {
        for (String entry : entries) {
            if (entry.startsWith(prefix)) return true;
        }
        return false;
    }

    public int count(String prefix) {
        int n = 0;
        for (String entry : entries) {
            if (entry.startsWith(prefix)) n++;
        }
        return n;
    }

    public List<String> tail(int n) {
        return new ArrayList<String>(entries.subList(Math.max(0, entries.size() - n), entries.size()));
    }

    /** Full dump, one entry per line (used by the support tool). */
    public String dump() {
        String s = "";
        for (String entry : entries) {
            s = s + entry + "\n";
        }
        return s;
    }
}
