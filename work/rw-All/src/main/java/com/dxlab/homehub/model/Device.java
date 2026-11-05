package com.dxlab.homehub.model;

/** Mutable runtime view of one appliance. */
public class Device {
    private final String id;
    private final DeviceKind kind;
    private DeviceStatus status = DeviceStatus.OFF;
    private long lastSeen = -1;
    private Integer lastTemp;          // last reported temperature (Celsius), null if none
    private int consecutiveHighTemp;   // consecutive reports at or above the high threshold
    private boolean doorOpen;
    private long doorOpenedAt = -1;
    private String firmware = "1.0";

    public Device(String id, DeviceKind kind) {
        this.id = id;
        this.kind = kind;
    }

    public String getId() {
        return id;
    }

    public DeviceKind getKind() {
        return kind;
    }

    public DeviceStatus getStatus() {
        return status;
    }

    public void setStatus(DeviceStatus status) {
        this.status = status;
    }

    public long getLastSeen() {
        return lastSeen;
    }

    public void setLastSeen(long lastSeen) {
        this.lastSeen = lastSeen;
    }

    public Integer getLastTemp() {
        return lastTemp;
    }

    public void setLastTemp(Integer lastTemp) {
        this.lastTemp = lastTemp;
    }

    public int getConsecutiveHighTemp() {
        return consecutiveHighTemp;
    }

    public void setConsecutiveHighTemp(int n) {
        this.consecutiveHighTemp = n;
    }

    public boolean isDoorOpen() {
        return doorOpen;
    }

    public void setDoorOpen(boolean doorOpen, long at) {
        this.doorOpen = doorOpen;
        this.doorOpenedAt = doorOpen ? at : -1;
    }

    public long getDoorOpenedAt() {
        return doorOpenedAt;
    }

    public String getFirmware() {
        return firmware;
    }

    public void setFirmware(String firmware) {
        this.firmware = firmware;
    }

    public String toString() {
        return id + "[" + kind + "," + status + "]";
    }
}
