package com.dxlab.homehub.model;

/** Appliance kinds supported by the hub, with rated power draw while running. */
public enum DeviceKind {
    WASHER(2000),
    DRYER(2500),
    FRIDGE(150),
    AIRCON(1800),
    OVEN(2200),
    LEAK_SENSOR(1),
    TV(120);

    private final int ratedWatts;

    DeviceKind(int ratedWatts) {
        this.ratedWatts = ratedWatts;
    }

    public int getRatedWatts() {
        return ratedWatts;
    }

    /** Heavy loads must obtain a power grant before starting a cycle. */
    public boolean isHeavyLoad() {
        return ratedWatts >= 1000;
    }

    public boolean usesWater() {
        return this == WASHER || this == DRYER;
    }
}
