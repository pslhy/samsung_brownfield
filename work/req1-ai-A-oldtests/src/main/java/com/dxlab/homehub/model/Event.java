package com.dxlab.homehub.model;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/** Immutable device event. Identity is (seq, deviceId). */
public final class Event {
    private final long seq;
    private final String deviceId;
    private final EventType type;
    private final int value;
    private final long timestamp;
    private final Map<String, String> attrs;

    public Event(long seq, String deviceId, EventType type, int value, long timestamp) {
        this(seq, deviceId, type, value, timestamp, new HashMap<String, String>());
    }

    public Event(long seq, String deviceId, EventType type, int value, long timestamp,
                 Map<String, String> attrs) {
        this.seq = seq;
        this.deviceId = deviceId;
        this.type = type;
        this.value = value;
        this.timestamp = timestamp;
        this.attrs = Collections.unmodifiableMap(new HashMap<String, String>(attrs));
    }

    public long getSeq() {
        return seq;
    }

    public String getDeviceId() {
        return deviceId;
    }

    public EventType getType() {
        return type;
    }

    public int getValue() {
        return value;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public String attr(String key) {
        return attrs.get(key);
    }

    public Map<String, String> getAttrs() {
        return attrs;
    }

    public boolean isCritical() {
        return type.isCritical();
    }

    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Event)) return false;
        Event other = (Event) o;
        return seq == other.seq && deviceId.equals(other.deviceId);
    }

    public int hashCode() {
        return (int) (seq ^ (seq >>> 32)) * 31 + deviceId.hashCode();
    }

    public String toString() {
        return "#" + seq + " " + deviceId + " " + type + "(" + value + ")";
    }
}
