package com.dxlab.homehub.model;

/**
 * Event types reported by appliances.
 * Wire codes come from hub protocol v1 (2014). Do not rename codes: field devices depend on them.
 */
public enum EventType {
    POWER_ON("PWR_ON"),
    POWER_OFF("PWR_OFF"),
    CYCLE_START("CYC_S"),
    CYCLE_END("CYC_E"),
    TEMP_REPORT("TEMP"),
    DOOR_OPEN("DOOR_O"),
    DOOR_CLOSE("DOOR_C"),
    LEAK_DETECTED("LEAK"),
    OVERHEAT("OVHT"),
    HEARTBEAT("HB"),
    UNKNOWN("?");

    private final String code;

    EventType(String code) {
        this.code = code;
    }

    public String code() {
        return code;
    }

    /** Safety-relevant events. The hub must never silently drop these. */
    public boolean isCritical() {
        return this == LEAK_DETECTED || this == OVERHEAT;
    }

    public static EventType fromCode(String code) {
        if (code.equals("PWR_ON")) return POWER_ON;
        if (code.equals("PWR_OFF")) return POWER_OFF;
        if (code.equals("CYC_S")) return CYCLE_START;
        if (code.equals("CYC_E")) return CYCLE_END;
        if (code.equals("TEMP")) return TEMP_REPORT;
        if (code.equals("DOOR_O")) return DOOR_OPEN;
        if (code.equals("DOOR_C")) return DOOR_CLOSE;
        if (code.equals("LEAK")) return LEAK_DETECTED;
        if (code.equals("OVHT")) return OVERHEAT;
        if (code.equals("HB")) return HEARTBEAT;
        return UNKNOWN;
    }
}
