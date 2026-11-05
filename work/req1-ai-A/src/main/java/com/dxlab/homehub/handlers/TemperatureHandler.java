package com.dxlab.homehub.handlers;

import com.dxlab.homehub.device.DeviceRegistry;
import com.dxlab.homehub.dispatch.EventHandler;
import com.dxlab.homehub.model.Device;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.ops.AuditLog;
import com.dxlab.homehub.ops.Metrics;

/** Keeps the latest temperature per device and counts consecutive high readings. */
public final class TemperatureHandler implements EventHandler {
    private final DeviceRegistry devices;
    private final Metrics metrics;
    private final AuditLog audit;
    private final int highThresholdCelsius;

    public TemperatureHandler(DeviceRegistry devices, Metrics metrics, AuditLog audit, int highThresholdCelsius) {
        this.devices = devices;
        this.metrics = metrics;
        this.audit = audit;
        this.highThresholdCelsius = highThresholdCelsius;
    }

    public String name() {
        return "temperature";
    }

    public void handle(Event e) {
        Device d = devices.get(e.getDeviceId());
        if (d == null) {
            audit.record("UNKNOWN_DEVICE", e);
            return;
        }
        d.setLastSeen(e.getTimestamp());
        Integer t = new Integer(e.getValue());
        d.setLastTemp(t);
        if (t.intValue() >= highThresholdCelsius) {
            d.setConsecutiveHighTemp(d.getConsecutiveHighTemp() + 1);
        } else {
            d.setConsecutiveHighTemp(0);
        }
        metrics.increment("temp.reports");
    }
}
