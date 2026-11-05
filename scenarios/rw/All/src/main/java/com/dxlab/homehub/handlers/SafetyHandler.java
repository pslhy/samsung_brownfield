package com.dxlab.homehub.handlers;

import com.dxlab.homehub.device.DeviceRegistry;
import com.dxlab.homehub.dispatch.EventHandler;
import com.dxlab.homehub.model.Device;
import com.dxlab.homehub.model.DeviceStatus;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.ops.AuditLog;
import com.dxlab.homehub.ops.Metrics;
import com.dxlab.homehub.power.PowerBudget;

import java.util.List;

/** Reacts to leak and overheat alarms. */
public final class SafetyHandler implements EventHandler {
    private final DeviceRegistry devices;
    private final PowerBudget power;
    private final AuditLog audit;
    private final Metrics metrics;

    public SafetyHandler(DeviceRegistry devices, PowerBudget power, AuditLog audit, Metrics metrics) {
        this.devices = devices;
        this.power = power;
        this.audit = audit;
        this.metrics = metrics;
    }

    public String name() {
        return "safety";
    }

    public void handle(Event e) {
        if (e.getType() == EventType.LEAK_DETECTED) {
            audit.record("VALVE_CLOSE", e);
            List<Device> all = devices.all();
            for (Device d : all) {
                if (d.getKind().usesWater() && d.getStatus() == DeviceStatus.RUNNING) {
                    d.setStatus(DeviceStatus.ERROR);
                    power.stop(d.getId());
                    audit.note("SAFETY_STOP", d.getId());
                }
            }
            metrics.increment("safety.leak");
        } else if (e.getType() == EventType.OVERHEAT) {
            Device d = devices.get(e.getDeviceId());
            if (d != null) {
                d.setStatus(DeviceStatus.ERROR);
                power.stop(d.getId());
            }
            audit.record("OVERHEAT_ALARM", e);
            metrics.increment("safety.overheat");
        }
    }
}
