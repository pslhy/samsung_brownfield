package com.dxlab.homehub.handlers;

import com.dxlab.homehub.device.DeviceRegistry;
import com.dxlab.homehub.device.DeviceStateMachine;
import com.dxlab.homehub.dispatch.EventHandler;
import com.dxlab.homehub.model.Device;
import com.dxlab.homehub.model.DeviceStatus;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.ops.AuditLog;
import com.dxlab.homehub.ops.Metrics;
import com.dxlab.homehub.power.PowerBudget;

/** Tracks appliance lifecycle and requests power grants for heavy loads. */
public final class DeviceStatusHandler implements EventHandler {
    private final DeviceRegistry devices;
    private final PowerBudget power;
    private final AuditLog audit;
    private final Metrics metrics;

    public DeviceStatusHandler(DeviceRegistry devices, PowerBudget power, AuditLog audit, Metrics metrics) {
        this.devices = devices;
        this.power = power;
        this.audit = audit;
        this.metrics = metrics;
    }

    public String name() {
        return "device-status";
    }

    public void handle(Event e) {
        Device d = devices.get(e.getDeviceId());
        if (d == null) {
            audit.record("UNKNOWN_DEVICE", e);
            metrics.increment("device.unknown");
            return;
        }
        d.setLastSeen(e.getTimestamp());
        String fw = e.attr("fw");
        if (fw != null) {
            d.setFirmware(fw);
        }
        if (e.getType() == EventType.DOOR_OPEN) {
            d.setDoorOpen(true, e.getTimestamp());
            return;
        }
        if (e.getType() == EventType.DOOR_CLOSE) {
            d.setDoorOpen(false, e.getTimestamp());
            return;
        }
        DeviceStatus before = d.getStatus();
        if (e.getType() == EventType.CYCLE_START && before == DeviceStatus.IDLE && d.getKind().isHeavyLoad()) {
            if (!power.tryStart(d.getId(), d.getKind().getRatedWatts())) {
                audit.record("POWER_DENIED", e);
                metrics.increment("power.denied");
                return;
            }
        }
        DeviceStatus after = DeviceStateMachine.next(before, e.getType());
        d.setStatus(after);
        if (before == DeviceStatus.RUNNING && after != DeviceStatus.RUNNING) {
            power.stop(d.getId());
        }
        if (before != after) {
            audit.note("STATE", d.getId() + ":" + before + "->" + after);
        }
    }
}
